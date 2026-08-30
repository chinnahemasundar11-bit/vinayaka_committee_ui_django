import re
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from members.models import Member
from audit.models import AuditLog
from .models import (
    WorkflowDefinition, WorkflowStepDefinition,
    WorkflowInstance, WorkflowTaskAction, WorkflowEmailConfig
)


def render_template_placeholders(template_str, context):
    """
    Replaces dynamic placeholders in subject/body templates.
    Example: "{item_number}" -> "EXP-2026-001"
    """
    if not template_str:
        return ""
    result = str(template_str)
    for key, value in context.items():
        placeholder = f"{{{key}}}"
        val_str = str(value) if value is not None else ""
        result = result.replace(placeholder, val_str)
    return result


def get_users_by_role_or_type(recipient_type, step=None, submitter=None):
    """
    Resolves recipient user email addresses dynamically based on recipient_type.
    """
    users_qs = User.objects.none()

    if recipient_type == "SUBMITTER" and submitter:
        return [submitter] if submitter.email else []

    elif recipient_type == "SUPER_ADMIN":
        users_qs = User.objects.filter(is_superuser=True)

    elif recipient_type == "ALL_LEADERS":
        leader_mobiles = Member.objects.filter(
            committee_position__in=["President", "Secretary", "Chief Treasurer", "Vice President"],
            is_deleted=False
        ).values_list("mobile_number", flat=True)
        users_qs = User.objects.filter(username__in=leader_mobiles)

    elif recipient_type == "ASSIGNED_ROLE" and step and step.assigned_role:
        assigned_mobiles = Member.objects.filter(
            system_role__icontains=step.assigned_role,
            is_deleted=False
        ).values_list("mobile_number", flat=True)
        users_qs = User.objects.filter(username__in=assigned_mobiles)

    recipient_users = list(users_qs)
    # Include superuser if list is empty
    if not recipient_users and recipient_type == "ASSIGNED_ROLE":
        recipient_users = list(User.objects.filter(is_superuser=True))

    return recipient_users


def send_workflow_email_notifications(instance, step, trigger_event, extra_context=None):
    """
    Evaluates WorkflowEmailConfig rules for trigger_event and dispatches emails with dynamic placeholders.
    """
    configs = WorkflowEmailConfig.objects.filter(
        trigger_event=trigger_event,
        is_active=True
    )
    # Filter by specific workflow if set
    configs_specific = configs.filter(workflow=instance.workflow)
    if configs_specific.exists():
        configs = configs_specific

    context = {
        "workflow_name": instance.workflow.name,
        "module_code": instance.module_code,
        "item_number": instance.object_id,
        "status": instance.status,
        "submitted_by": instance.submitted_by.get_full_name() if instance.submitted_by else "System",
        "step_name": step.step_name if step else "Workflow Execution",
        "assigned_role": step.assigned_role if step else "General Role",
    }
    if extra_context:
        context.update(extra_context)

    for cfg in configs:
        recipients = get_users_by_role_or_type(cfg.recipient_type, step=step, submitter=instance.submitted_by)
        recipient_emails = [u.email for u in recipients if u.email]

        subject = render_template_placeholders(cfg.email_subject_template, context)
        body = render_template_placeholders(cfg.email_body_template, context)

        if recipient_emails and subject and body:
            try:
                send_mail(
                    subject=subject,
                    message=body,
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@vinayaka.org"),
                    recipient_list=recipient_emails,
                    fail_silently=True
                )
            except Exception:
                pass

        # Audit log email trigger
        try:
            from django.db import transaction
            with transaction.atomic():
                AuditLog.objects.create(
                    user=instance.submitted_by if (instance.submitted_by and instance.submitted_by.pk) else None,
                    action="EMAIL_TRIGGER",
                    model_name="WorkflowEmailConfig",
                    object_id=str(cfg.id),
                    details=f"Sent workflow email [{trigger_event}] to {len(recipient_emails)} recipients for {instance.object_id}"
                )
        except Exception:
            pass


def start_workflow_for_object(module_code, object_id, submitter, amount=0):
    """
    Starts an active workflow for a newly created or submitted item.
    """
    workflow_def = WorkflowDefinition.objects.filter(module_code=module_code, is_active=True).first()
    if not workflow_def:
        return None

    # Get first step that satisfies threshold
    first_step = workflow_def.steps.filter(approval_threshold__lte=amount).order_by("step_order").first()
    if not first_step:
        first_step = workflow_def.steps.order_by("step_order").first()

    if not first_step:
        return None

    instance = WorkflowInstance.objects.create(
        workflow=workflow_def,
        module_code=module_code,
        object_id=str(object_id),
        current_step=first_step,
        status="PENDING",
        submitted_by=submitter
    )

    send_workflow_email_notifications(
        instance=instance,
        step=first_step,
        trigger_event="ON_SUBMIT",
        extra_context={"amount": f"{amount:.2f}"}
    )
    send_workflow_email_notifications(
        instance=instance,
        step=first_step,
        trigger_event="ON_ASSIGNMENT",
        extra_context={"amount": f"{amount:.2f}"}
    )

    return instance


def process_task_action(instance_id, user, action_taken, comments=""):
    """
    Processes user approval/rejection task action and advances the workflow.
    """
    instance = WorkflowInstance.objects.select_related("workflow", "current_step").get(id=instance_id)
    current_step = instance.current_step

    if not current_step:
        return instance

    # Create task action record
    TaskAction = WorkflowTaskAction.objects.create(
        instance=instance,
        step=current_step,
        assigned_role=current_step.assigned_role,
        performed_by=user,
        action_taken=action_taken,
        comments=comments
    )

    extra = {
        "performed_by": user.get_full_name() or user.username,
        "action_taken": action_taken,
        "comments": comments,
    }

    if action_taken == "APPROVED":
        # Find next step
        next_step = instance.workflow.steps.filter(step_order__gt=current_step.step_order).order_by("step_order").first()
        if next_step:
            instance.current_step = next_step
            instance.status = "IN_REVIEW"
            instance.save()

            send_workflow_email_notifications(instance, current_step, "ON_APPROVE", extra)
            send_workflow_email_notifications(instance, next_step, "ON_ASSIGNMENT", extra)
        else:
            # Workflow completed and fully approved
            instance.current_step = None
            instance.status = "APPROVED"
            instance.save()

            send_workflow_email_notifications(instance, current_step, "ON_APPROVE", extra)

    elif action_taken in ["REJECTED", "CHANGES_REQUESTED"]:
        instance.status = "REJECTED"
        instance.save()

        send_workflow_email_notifications(instance, current_step, "ON_REJECT", extra)

    return instance
