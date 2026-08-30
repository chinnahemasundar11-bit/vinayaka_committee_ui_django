from django.test import TestCase
from workflows.models import WorkflowDefinition, WorkflowStepDefinition


class WorkflowsTestCase(TestCase):
    def test_workflow_definition_and_step(self):
        wf = WorkflowDefinition.objects.create(
            name="High Expense Verification",
            module_code="EXPENSE",
            description="Auto approval workflow for large vouchers",
            is_active=True
        )
        step = WorkflowStepDefinition.objects.create(
            workflow=wf,
            step_name="Treasurer Review",
            step_order=1,
            assigned_role="Treasurer",
            approval_threshold=5000.00
        )
        self.assertIsNotNone(wf.id)
        self.assertEqual(step.approval_threshold, 5000.00)
