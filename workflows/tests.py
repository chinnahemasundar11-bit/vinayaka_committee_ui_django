from django.test import TestCase, Client
from django.contrib.auth.models import User
from members.models import Member
from workflows.models import (
    WorkflowDefinition, WorkflowStepDefinition,
    WorkflowInstance, WorkflowTaskAction, WorkflowEmailConfig
)
from workflows.services import (
    render_template_placeholders, start_workflow_for_object, process_task_action
)


class WorkflowModuleTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser("admin_wf", "admin@test.com", "pass123")
        self.treasurer_user = User.objects.create_user("9876501234", "treasurer@test.com", "pass123")

        Member.objects.create(
            member_id="MBR-W01",
            full_name="Treasurer User",
            mobile_number="9876501234",
            committee_position="Chief Treasurer",
            system_role="Treasurer",
            joining_date="2026-01-01"
        )

        self.wf = WorkflowDefinition.objects.create(
            name="Expense Approval Workflow",
            module_code="EXPENSE",
            description="Testing enterprise workflows"
        )
        self.step1 = WorkflowStepDefinition.objects.create(
            workflow=self.wf,
            step_name="Treasurer Review",
            step_order=1,
            assigned_role="Treasurer",
            approval_threshold=0
        )
        self.step2 = WorkflowStepDefinition.objects.create(
            workflow=self.wf,
            step_name="President Final Review",
            step_order=2,
            assigned_role="President",
            approval_threshold=5000
        )

        self.email_config = WorkflowEmailConfig.objects.create(
            workflow=self.wf,
            trigger_event="ON_SUBMIT",
            recipient_type="SUBMITTER",
            email_subject_template="Item Submission #{item_number}",
            email_body_template="Item #{item_number} submitted by {submitted_by} for amount ₹{amount}"
        )

    def test_placeholder_renderer(self):
        ctx = {"item_number": "EXP-100", "submitted_by": "John", "amount": "500.00"}
        res = render_template_placeholders(self.email_config.email_body_template, ctx)
        self.assertIn("EXP-100", res)
        self.assertIn("John", res)
        self.assertIn("500.00", res)

    def test_start_workflow_engine(self):
        instance = start_workflow_for_object(
            module_code="EXPENSE",
            object_id="EXP-2026-001",
            submitter=self.admin_user,
            amount=8000
        )
        self.assertIsNotNone(instance)
        self.assertEqual(instance.status, "PENDING")
        self.assertEqual(instance.current_step, self.step1)

    def test_process_task_action_advancement(self):
        instance = start_workflow_for_object("EXPENSE", "EXP-2026-002", self.admin_user, amount=8000)
        
        # Treasurer approves step 1
        instance = process_task_action(instance.id, self.treasurer_user, "APPROVED", "Checked receipts")
        self.assertEqual(instance.status, "IN_REVIEW")
        self.assertEqual(instance.current_step, self.step2)

        # President approves step 2 (final step)
        instance = process_task_action(instance.id, self.admin_user, "APPROVED", "Final OK")
        self.assertEqual(instance.status, "APPROVED")
        self.assertIsNone(instance.current_step)

    def test_workflow_list_view_admin_access(self):
        self.client.login(username="admin_wf", password="pass123")
        response = self.client.get("/workflows/")
        self.assertEqual(response.status_code, 200)

    def test_email_configs_view_admin_access(self):
        self.client.login(username="admin_wf", password="pass123")
        response = self.client.get("/workflows/email-configs/")
        self.assertEqual(response.status_code, 200)

    def test_my_tasks_inbox_view(self):
        self.client.login(username="9876501234", password="pass123")
        response = self.client.get("/workflows/my-tasks/")
        self.assertEqual(response.status_code, 200)
