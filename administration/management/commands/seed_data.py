import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from administration.models import (
    SiteSetting, LookupType, LookupValue, FinancialYear,
    FundSource, ExpenseCategory, PaymentMethod
)
from members.models import Member
from events.models import Event
from funds.models import FundReceipt
from expenses.models import ExpenseVoucher


class Command(BaseCommand):
    help = "Seeds initial lookup types, values, site settings, and master data."

    def handle(self, *args, **options):
        self.stdout.write("Seeding master data...")

        # Reset Postgres primary key sequences if on PostgreSQL
        from django.db import connection
        if connection.vendor == "postgresql":
            existing_tables = connection.introspection.table_names()
            tables = [
                "auth_user", "administration_lookup_type", "administration_lookup_value",
                "administration_site_setting", "administration_financial_year",
                "administration_fund_source", "administration_expense_category",
                "administration_payment_method", "audit_auditlog", "events_event",
                "expenses_expense_voucher", "funds_fund_receipt", "members_member"
            ]
            with connection.cursor() as cursor:
                for table in tables:
                    if table in existing_tables:
                        try:
                            cursor.execute(
                                f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM \"{table}\";"
                            )
                        except Exception:
                            pass

        # 1. Superuser
        if not User.objects.filter(username="9876543210").exists():
            User.objects.create_superuser("9876543210", "admin@vinayaka.org", "admin123")
            self.stdout.write(self.style.SUCCESS("Superuser created (9876543210 / admin123)"))

        # 2. Site Settings
        SiteSetting.objects.get_or_create(key="SITE_NAME", defaults={"value": "Vinayaka Youth Committee", "category": "GENERAL"})
        SiteSetting.objects.get_or_create(key="SITE_SLOGAN", defaults={"value": "Ganesh Utsav Finance Portal", "category": "GENERAL"})
        SiteSetting.objects.get_or_create(key="CURRENCY_SYMBOL", defaults={"value": "₹", "category": "FINANCIAL"})

        # 3. Lookup Types & Values
        pos_type, _ = LookupType.objects.get_or_create(code="COMMITTEE_POSITION", defaults={"name": "Committee Positions"})
        positions = [
            ("POS_PRESIDENT", "President", 1),
            ("POS_VICE_PRESIDENT", "Vice President", 2),
            ("POS_SECRETARY", "Secretary", 3),
            ("POS_JOINT_SECRETARY", "Joint Secretary", 4),
            ("POS_TREASURER", "Chief Treasurer", 5),
            ("POS_JOINT_TREASURER", "Joint Treasurer", 6),
            ("POS_EVENT_COORD", "Event Coordinator", 7),
            ("POS_VOLUNTEER_LEAD", "Volunteer Leader", 8),
            ("POS_MEMBER", "Youth Committee Member", 9),
        ]
        for code, val, order in positions:
            LookupValue.objects.get_or_create(lookup_type=pos_type, code=code, defaults={"value": val, "display_order": order})

        role_type, _ = LookupType.objects.get_or_create(code="SYSTEM_ROLE", defaults={"name": "System Access Roles"})
        roles = [
            ("ROLE_SUPER_ADMIN", "Super Admin", 1),
            ("ROLE_TREASURER", "Treasurer", 2),
            ("ROLE_MEMBER", "Committee Member", 3),
            ("ROLE_AUDITOR", "Viewer / Public Auditor", 4),
        ]
        for code, val, order in roles:
            LookupValue.objects.get_or_create(lookup_type=role_type, code=code, defaults={"value": val, "display_order": order})

        # 4. Financial Year
        FinancialYear.objects.get_or_create(
            name="FY 2026 - 2027",
            defaults={"start_date": datetime.date(2026, 4, 1), "end_date": datetime.date(2027, 3, 31), "is_active": True}
        )

        # 5. Masters
        fs_youth, _ = FundSource.objects.get_or_create(code="SRC_YOUTH", defaults={"name": "Youth Contribution", "receipt_prefix": "RCPT-YTH-"})
        fs_village, _ = FundSource.objects.get_or_create(code="SRC_VILLAGE", defaults={"name": "Village Household Contribution", "receipt_prefix": "RCPT-VLG-"})
        fs_donor, _ = FundSource.objects.get_or_create(code="SRC_DONOR", defaults={"name": "Outside Donors & Well Wishers", "receipt_prefix": "RCPT-DNR-"})
        fs_laddu, _ = FundSource.objects.get_or_create(code="SRC_AUCTION", defaults={"name": "Laddu Auction & Prasadam", "receipt_prefix": "RCPT-AUC-"})

        cat_idol, _ = ExpenseCategory.objects.get_or_create(code="EXP_IDOL", defaults={"name": "Idol & Sthapana Pooja", "requires_approval": True, "approval_threshold": 10000})
        cat_dec, _ = ExpenseCategory.objects.get_or_create(code="EXP_DECOR", defaults={"name": "Decorations & Mandapam Set", "requires_approval": True, "approval_threshold": 5000})
        cat_food, _ = ExpenseCategory.objects.get_or_create(code="EXP_FOOD", defaults={"name": "Annasantharpana / Prasadam Food", "requires_approval": True, "approval_threshold": 15000})
        cat_lgt, _ = ExpenseCategory.objects.get_or_create(code="EXP_LIGHTING", defaults={"name": "Lighting & Sound Systems"})
        cat_nim, _ = ExpenseCategory.objects.get_or_create(code="EXP_NIMAJJANAM", defaults={"name": "Nimajjanam Procession & Band", "requires_approval": True, "approval_threshold": 10000})

        pay_cash, _ = PaymentMethod.objects.get_or_create(code="PAY_CASH", defaults={"name": "Cash Payment", "icon_name": "bi-cash-stack"})
        pay_upi, _ = PaymentMethod.objects.get_or_create(code="PAY_UPI", defaults={"name": "UPI / PhonePe / GooglePay", "requires_ref_no": True, "icon_name": "bi-qr-code"})
        pay_bank, _ = PaymentMethod.objects.get_or_create(code="PAY_BANK", defaults={"name": "Bank Transfer (NEFT/IMPS)", "requires_ref_no": True, "icon_name": "bi-bank"})

        # 6. Members
        Member.objects.get_or_create(member_id="MBR-2026-001", defaults={"full_name": "K. V. Ramesh", "mobile_number": "9876543210", "committee_position": "President", "system_role": "Super Admin", "joining_date": datetime.date(2026, 1, 1), "status": "Active"})
        Member.objects.get_or_create(member_id="MBR-2026-002", defaults={"full_name": "M. Suresh Kumar", "mobile_number": "9876501234", "committee_position": "Chief Treasurer", "system_role": "Treasurer", "joining_date": datetime.date(2026, 1, 1), "status": "Active"})
        Member.objects.get_or_create(member_id="MBR-2026-003", defaults={"full_name": "P. Anjaneyulu", "mobile_number": "9876512345", "committee_position": "Secretary", "system_role": "Committee Member", "joining_date": datetime.date(2026, 1, 15), "status": "Active"})

        # 7. Events
        Event.objects.get_or_create(event_id="EVT-2026-001", defaults={"title": "Ganesh Idol Installation & Sthapana", "venue_location": "Main Mandapam Temple", "event_date": datetime.date(2026, 8, 20), "allocated_budget": 25000, "actual_spend": 22500, "status": "Planned", "description": "Grand installation of Lord Ganesha idol with Veda chanting."})
        Event.objects.get_or_create(event_id="EVT-2026-002", defaults={"title": "Grand Annasantharpana (Mahaprasadam)", "venue_location": "Community Dining Hall", "event_date": datetime.date(2026, 8, 24), "allocated_budget": 45000, "actual_spend": 42000, "status": "Planned", "description": "Free community feast for over 2,500 devotees."})

        # 8. Fund Receipts
        FundReceipt.objects.get_or_create(receipt_number="RCPT-2026-001", defaults={"donor_name": "Ramesh Kumar", "donor_phone": "9876543210", "fund_source": fs_youth, "payment_method": pay_upi, "amount": 10000, "date_received": datetime.date(2026, 8, 13), "reference_number": "UPI-88776655"})
        FundReceipt.objects.get_or_create(receipt_number="RCPT-2026-002", defaults={"donor_name": "Village Elders", "donor_phone": "9876599999", "fund_source": fs_village, "payment_method": pay_cash, "amount": 25000, "date_received": datetime.date(2026, 8, 12)})
        FundReceipt.objects.get_or_create(receipt_number="RCPT-2026-003", defaults={"donor_name": "Suresh Rao", "donor_phone": "9876501234", "fund_source": fs_donor, "payment_method": pay_bank, "amount": 15000, "date_received": datetime.date(2026, 8, 10), "reference_number": "TXN-998877"})

        # 9. Expense Vouchers
        ExpenseVoucher.objects.get_or_create(voucher_number="EXP-2026-001", defaults={"category": cat_dec, "vendor_name": "Royal Decorators", "description": "Stage & Mandapam Decoration Flowers & Cloth", "amount_spent": 8500, "expense_date": datetime.date(2026, 8, 12), "payment_method": pay_cash, "status": "Approved"})
        ExpenseVoucher.objects.get_or_create(voucher_number="EXP-2026-002", defaults={"category": cat_lgt, "vendor_name": "ABC Electricals", "description": "500W Sound System & Festival LED Lights", "amount_spent": 12000, "expense_date": datetime.date(2026, 8, 11), "payment_method": pay_upi, "status": "Approved"})
        ExpenseVoucher.objects.get_or_create(voucher_number="EXP-2026-003", defaults={"category": cat_food, "vendor_name": "Sri Laxmi Mart", "description": "Grocery Purchase for Mahaprasadam Cooking", "amount_spent": 35000, "expense_date": datetime.date(2026, 8, 9), "payment_method": pay_cash, "status": "Approved"})

        # 10. Enterprise Workflow Definitions & Email Configuration Module
        from workflows.models import WorkflowDefinition, WorkflowStepDefinition, WorkflowEmailConfig

        wf_exp, _ = WorkflowDefinition.objects.get_or_create(
            name="Expense Voucher Approval Workflow",
            module_code="EXPENSE",
            defaults={"description": "Multi-step approval process for festival expenditures with threshold limits."}
        )
        s1, _ = WorkflowStepDefinition.objects.get_or_create(
            workflow=wf_exp, step_order=1,
            defaults={"step_name": "Treasurer Financial Audit", "assigned_role": "Treasurer", "approval_threshold": 0}
        )
        s2, _ = WorkflowStepDefinition.objects.get_or_create(
            workflow=wf_exp, step_order=2,
            defaults={"step_name": "President Final Approval", "assigned_role": "President", "approval_threshold": 5000}
        )

        # Status-wise Email Templates Configuration
        WorkflowEmailConfig.objects.get_or_create(
            trigger_event="ON_SUBMIT",
            recipient_type="SUBMITTER",
            defaults={
                "email_subject_template": "[Vinayaka Portal] Submission Confirmation: {module_code} #{item_number}",
                "email_body_template": "Hello {submitted_by},\n\nYour submission for {module_code} item #{item_number} of amount ₹{amount} has been received and initiated into workflow '{workflow_name}'.\n\nCurrent Step: {step_name} ({assigned_role}).\n\nThank you,\nVinayaka Youth Committee"
            }
        )
        WorkflowEmailConfig.objects.get_or_create(
            trigger_event="ON_ASSIGNMENT",
            recipient_type="ASSIGNED_ROLE",
            defaults={
                "email_subject_template": "[Vinayaka Portal] Action Required: Task Assigned for #{item_number}",
                "email_body_template": "Hello,\n\nA new task step '{step_name}' has been assigned to your role ({assigned_role}) for item #{item_number}.\n\nWorkflow: {workflow_name}\nModule: {module_code}\nSubmitted By: {submitted_by}\n\nPlease sign in to open your Task Inbox (/workflows/my-tasks/) and perform your review.\n\nThank you,\nVinayaka Youth Committee"
            }
        )
        WorkflowEmailConfig.objects.get_or_create(
            trigger_event="ON_APPROVE",
            recipient_type="SUBMITTER",
            defaults={
                "email_subject_template": "[Vinayaka Portal] Approved: Item #{item_number} Action Passed",
                "email_body_template": "Hello {submitted_by},\n\nGreat news! Step '{step_name}' for item #{item_number} has been APPROVED by {performed_by}.\n\nComments: {comments}\nOverall Status: {status}\n\nThank you,\nVinayaka Youth Committee"
            }
        )
        WorkflowEmailConfig.objects.get_or_create(
            trigger_event="ON_REJECT",
            recipient_type="SUBMITTER",
            defaults={
                "email_subject_template": "[Vinayaka Portal] Update Required / Rejected: Item #{item_number}",
                "email_body_template": "Hello {submitted_by},\n\nYour submission for item #{item_number} was marked as {action_taken} by {performed_by} at step '{step_name}'.\n\nComments: {comments}\n\nPlease review your submission details.\n\nThank you,\nVinayaka Youth Committee"
            }
        )

        self.stdout.write(self.style.SUCCESS("Master data and sample records successfully seeded!"))
