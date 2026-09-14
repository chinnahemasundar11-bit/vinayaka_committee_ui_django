from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext as _
from accounts.permissions import login_required_custom, admin_required, get_user_role, module_access_required
from administration.models import LookupType, LookupValue
from audit.models import AuditLog
from .models import (
    WorkflowDefinition, WorkflowStepDefinition,
    WorkflowInstance, WorkflowTaskAction, WorkflowEmailConfig
)
from .services import process_task_action


@admin_required
def workflow_list(request):
    """Workflow Definitions & Step Builder UI."""
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create_workflow":
            name = request.POST.get("name", "").strip()
            module_code = request.POST.get("module_code", "EXPENSE")
            description = request.POST.get("description", "").strip()
            if name and module_code:
                wf = WorkflowDefinition.objects.create(name=name, module_code=module_code, description=description)
                # Create default 2 steps for workflow
                WorkflowStepDefinition.objects.create(workflow=wf, step_name="Treasurer Review", step_order=1, assigned_role="Treasurer")
                WorkflowStepDefinition.objects.create(workflow=wf, step_name="President Approval", step_order=2, assigned_role="President", approval_threshold=5000)

                messages.success(request, f"Workflow '{name}' created successfully!")
        
        elif action == "add_step":
            wf_id = request.POST.get("workflow_id")
            wf = get_object_or_404(WorkflowDefinition, id=wf_id)
            step_name = request.POST.get("step_name", "").strip()
            role = request.POST.get("assigned_role", "Treasurer")
            order = request.POST.get("step_order", wf.steps.count() + 1)
            thresh = request.POST.get("approval_threshold", 0)

            if step_name:
                WorkflowStepDefinition.objects.create(
                    workflow=wf, step_name=step_name, assigned_role=role,
                    step_order=order, approval_threshold=thresh
                )
                messages.success(request, f"Step '{step_name}' added to workflow '{wf.name}'.")

        elif action == "delete_workflow":
            wf_id = request.POST.get("workflow_id")
            wf = get_object_or_404(WorkflowDefinition, id=wf_id)
            wf_name = wf.name
            wf.delete()
            messages.success(request, f"Workflow '{wf_name}' deleted.")

        return redirect("/workflows/")

    workflows_qs = WorkflowDefinition.objects.prefetch_related("steps").all()
    
    role_type = LookupType.objects.filter(code="SYSTEM_ROLE").first()
    roles = LookupValue.objects.filter(lookup_type=role_type, is_active=True) if role_type else []

    try:
        per_page = int(request.GET.get("per_page", 10))
        if per_page not in [10, 50, 100, 500]: per_page = 10
    except (ValueError, TypeError):
        per_page = 10

    from django.core.paginator import Paginator
    paginator = Paginator(workflows_qs, per_page)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "workflows": page_obj,
        "page_obj": page_obj,
        "per_page": per_page,
        "roles": roles,
    }
    return render(request, "workflows/workflow_list.html", context)


@admin_required
def email_config_list(request):
    """Status-wise Dynamic Email Configuration Module for Workflows and Tasks."""
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "save_email_config":
            cfg_id = request.POST.get("config_id")
            trigger = request.POST.get("trigger_event")
            recipient = request.POST.get("recipient_type")
            subject = request.POST.get("email_subject_template", "").strip()
            body = request.POST.get("email_body_template", "").strip()
            wf_id = request.POST.get("workflow_id")

            wf = WorkflowDefinition.objects.filter(id=wf_id).first() if wf_id else None

            if cfg_id:
                cfg = get_object_or_404(WorkflowEmailConfig, id=cfg_id)
                cfg.trigger_event = trigger
                cfg.recipient_type = recipient
                cfg.email_subject_template = subject
                cfg.email_body_template = body
                cfg.workflow = wf
                cfg.save()
                messages.success(request, "Email configuration template updated successfully!")
            else:
                WorkflowEmailConfig.objects.create(
                    workflow=wf,
                    trigger_event=trigger,
                    recipient_type=recipient,
                    email_subject_template=subject,
                    email_body_template=body
                )
                messages.success(request, "New status-wise email template configuration saved!")

        elif action == "delete_config":
            cfg_id = request.POST.get("config_id")
            cfg = get_object_or_404(WorkflowEmailConfig, id=cfg_id)
            cfg.delete()
            messages.success(request, "Email configuration deleted.")

        return redirect("/workflows/email-configs/")

    configs_qs = WorkflowEmailConfig.objects.select_related("workflow", "step").all()
    workflows_qs = WorkflowDefinition.objects.filter(is_active=True)

    try:
        per_page = int(request.GET.get("per_page", 10))
        if per_page not in [10, 50, 100, 500]: per_page = 10
    except (ValueError, TypeError):
        per_page = 10

    from django.core.paginator import Paginator
    paginator = Paginator(configs_qs, per_page)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "email_configs": page_obj,
        "page_obj": page_obj,
        "per_page": per_page,
        "workflows": workflows_qs,
    }
    return render(request, "workflows/email_config_list.html", context)


@login_required_custom
def my_tasks(request):
    """Task Inbox / Pending Workflow Approvals Queue."""
    user_role = get_user_role(request.user)

    # SuperAdmin sees all pending instances; role users see instances matching their role
    if request.user.is_superuser or user_role == "Super Admin":
        instances_qs = WorkflowInstance.objects.filter(status__in=["PENDING", "IN_REVIEW"]).select_related("workflow", "current_step", "submitted_by")
    else:
        instances_qs = WorkflowInstance.objects.filter(
            status__in=["PENDING", "IN_REVIEW"],
            current_step__assigned_role__icontains=user_role
        ).select_related("workflow", "current_step", "submitted_by")

    # History of tasks performed
    history_qs = WorkflowTaskAction.objects.filter(performed_by=request.user).select_related("instance", "step")[:20]

    try:
        per_page = int(request.GET.get("per_page", 10))
        if per_page not in [10, 50, 100, 500]: per_page = 10
    except (ValueError, TypeError):
        per_page = 10

    from django.core.paginator import Paginator
    paginator = Paginator(instances_qs, per_page)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "pending_tasks": page_obj,
        "page_obj": page_obj,
        "per_page": per_page,
        "task_history": history_qs,
        "user_role": user_role,
    }
    return render(request, "workflows/my_tasks.html", context)


@login_required_custom
def task_perform_action(request):
    """Submit approval, rejection, or changes requested task action."""
    if request.method == "POST":
        instance_id = request.POST.get("instance_id")
        action_taken = request.POST.get("action_taken")
        comments = request.POST.get("comments", "").strip()

        if instance_id and action_taken in ["APPROVED", "REJECTED", "CHANGES_REQUESTED"]:
            instance = process_task_action(instance_id, request.user, action_taken, comments)
            messages.success(
                request,
                f"Action '{action_taken}' processed successfully for workflow item {instance.object_id}!"
            )

    return redirect("/workflows/my-tasks/")
