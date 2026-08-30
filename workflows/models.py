from django.db import models
from django.contrib.auth.models import User
from administration.models import AuditModel


class WorkflowDefinition(AuditModel):
    """Master Enterprise Workflow Process Definition."""
    MODULE_CHOICES = [
        ("EXPENSE", "Expenses & Vouchers"),
        ("FUND", "Fund Contributions & Receipts"),
        ("EVENT", "Festival Events & Programs"),
        ("MEMBER", "Youth Committee Members"),
    ]

    name = models.CharField(max_length=150, help_text="e.g. High Value Expense Approval Process")
    module_code = models.CharField(max_length=50, choices=MODULE_CHOICES, help_text="Target module for workflow execution")
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True, help_text="Active workflows will automatically run on item creation")

    class Meta:
        db_table = "workflows_definition"
        ordering = ["module_code", "name"]

    def __str__(self):
        return f"{self.name} [{self.module_code}]"


class WorkflowStepDefinition(AuditModel):
    """Step & Task Configuration for a Workflow Definition."""
    workflow = models.ForeignKey(WorkflowDefinition, on_delete=models.CASCADE, related_name="steps")
    step_name = models.CharField(max_length=150, help_text="e.g. Treasurer Verification")
    step_order = models.PositiveIntegerField(default=1, help_text="Sequence order of step (1, 2, 3...)")
    assigned_role = models.CharField(max_length=100, help_text="System Role authorized to perform task (e.g. Treasurer, President)")
    approval_threshold = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Minimum item amount required to trigger step")

    class Meta:
        db_table = "workflows_step_definition"
        ordering = ["workflow", "step_order"]

    def __str__(self):
        return f"Step {self.step_order}: {self.step_name} ({self.assigned_role})"


class WorkflowInstance(AuditModel):
    """Lifecycle Tracker for a specific item undergoing Workflow approval."""
    STATUS_CHOICES = [
        ("PENDING", "Pending Action"),
        ("IN_REVIEW", "In Review"),
        ("APPROVED", "Fully Approved"),
        ("REJECTED", "Rejected"),
    ]

    workflow = models.ForeignKey(WorkflowDefinition, on_delete=models.CASCADE, related_name="instances")
    module_code = models.CharField(max_length=50)
    object_id = models.CharField(max_length=100, help_text="Primary Key or Voucher/Receipt Number of target item")
    current_step = models.ForeignKey(WorkflowStepDefinition, on_delete=models.SET_NULL, null=True, blank=True, related_name="active_instances")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="PENDING")
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="workflow_submissions")

    class Meta:
        db_table = "workflows_instance"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.workflow.name} - {self.object_id} [{self.status}]"


class WorkflowTaskAction(models.Model):
    """Audit Log of Task Actions performed by authorized role users."""
    ACTION_CHOICES = [
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("CHANGES_REQUESTED", "Changes Requested"),
    ]

    instance = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE, related_name="task_actions")
    step = models.ForeignKey(WorkflowStepDefinition, on_delete=models.CASCADE, related_name="task_history")
    assigned_role = models.CharField(max_length=100)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="performed_tasks")
    action_taken = models.CharField(max_length=30, choices=ACTION_CHOICES)
    comments = models.TextField(blank=True, null=True)
    performed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "workflows_task_action"
        ordering = ["-performed_at"]

    def __str__(self):
        user_str = self.performed_by.username if self.performed_by else "System"
        return f"[{self.performed_at.strftime('%Y-%m-%d %H:%M')}] {user_str} - {self.action_taken} for {self.step.step_name}"


class WorkflowEmailConfig(AuditModel):
    """Status-wise Dynamic Email Configuration Module for Workflows and Tasks."""
    TRIGGER_CHOICES = [
        ("ON_SUBMIT", "On Item Submission"),
        ("ON_ASSIGNMENT", "On Task Assignment to Role"),
        ("ON_APPROVE", "On Task Approval"),
        ("ON_REJECT", "On Task Rejection"),
    ]

    RECIPIENT_CHOICES = [
        ("ASSIGNED_ROLE", "Users with Assigned Step Role"),
        ("SUBMITTER", "Item Submitter"),
        ("SUPER_ADMIN", "System Super Admins"),
        ("ALL_LEADERS", "All Committee Leaders"),
    ]

    workflow = models.ForeignKey(WorkflowDefinition, on_delete=models.CASCADE, null=True, blank=True, related_name="email_configs")
    step = models.ForeignKey(WorkflowStepDefinition, on_delete=models.CASCADE, null=True, blank=True, related_name="email_configs")
    trigger_event = models.CharField(max_length=50, choices=TRIGGER_CHOICES)
    recipient_type = models.CharField(max_length=50, choices=RECIPIENT_CHOICES, default="ASSIGNED_ROLE")
    email_subject_template = models.TextField(help_text="Email subject with dynamic placeholders e.g. {item_number}")
    email_body_template = models.TextField(help_text="HTML/Text body template with placeholders e.g. {amount}, {performed_by}")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "workflows_email_config"
        ordering = ["trigger_event", "id"]

    def __str__(self):
        wf_name = self.workflow.name if self.workflow else "Global"
        return f"Email Config [{self.trigger_event}] - {wf_name}"
