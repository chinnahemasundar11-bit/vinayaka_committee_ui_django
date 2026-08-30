from django.core.management.base import BaseCommand
from administration.models import AppModule, RolePermission, LookupType, LookupValue

class Command(BaseCommand):
    help = "Seeds default dynamic system modules and role permissions"

    def handle(self, *args, **options):
        self.stdout.write("Seeding system modules...")
        
        ALL_RIGHTS = ["add", "edit", "delete_single", "delete_bulk", "print_single", "print_bulk"]
        
        # Modules Definition
        modules_data = [
            # Top-level standalone
            {
                "code": "DASHBOARD", "name": "Dashboard", "url": "/dashboard/",
                "parent_code": None, "icon_class": "bi-grid-1x2-fill", "order": 10
            },
            # Category 1: Finance Management
            {
                "code": "FINANCE_MGMT", "name": "Finance Management", "url": "#",
                "parent_code": None, "icon_class": "bi-wallet2", "order": 20
            },
            {
                "code": "FUNDS_RECEIVED", "name": "Funds Received", "url": "/funds/",
                "parent_code": "FINANCE_MGMT", "icon_class": "bi-cash-coin", "order": 21
            },
            {
                "code": "EXPENSES", "name": "Expenses", "url": "/expenses/",
                "parent_code": "FINANCE_MGMT", "icon_class": "bi-receipt", "order": 22
            },
            {
                "code": "REPORTS", "name": "Reports & Analytics", "url": "/reports/",
                "parent_code": "FINANCE_MGMT", "icon_class": "bi-bar-chart-fill", "order": 23
            },
            # Category 2: Committee & Events
            {
                "code": "COMMITTEE_MGMT", "name": "Committee & Events", "url": "#",
                "parent_code": None, "icon_class": "bi-people-fill", "order": 30
            },
            {
                "code": "MEMBERS", "name": "Committee Members", "url": "/members/",
                "parent_code": "COMMITTEE_MGMT", "icon_class": "bi-person-badge", "order": 31
            },
            {
                "code": "EVENTS", "name": "Festival Events", "url": "/events/",
                "parent_code": "COMMITTEE_MGMT", "icon_class": "bi-calendar-event", "order": 32
            },
            # Category 3: Administration
            {
                "code": "ADMINISTRATION", "name": "Administration", "url": "#",
                "parent_code": None, "icon_class": "bi-gear-fill", "order": 40
            },
            {
                "code": "ADMIN_HOME", "name": "Master Overview", "url": "/administration/",
                "parent_code": "ADMINISTRATION", "icon_class": "bi-speedometer2", "order": 41
            },
            {
                "code": "ADMIN_USERS", "name": "Users & Access", "url": "/administration/users/",
                "parent_code": "ADMINISTRATION", "icon_class": "bi-people", "order": 42
            },
            {
                "code": "ADMIN_MODULES", "name": "Sidebar Modules", "url": "/administration/modules/",
                "parent_code": "ADMINISTRATION", "icon_class": "bi-layout-sidebar-inset", "order": 43
            },
            {
                "code": "ADMIN_ROLES", "name": "Roles & Permissions", "url": "/administration/roles/",
                "parent_code": "ADMINISTRATION", "icon_class": "bi-shield-lock", "order": 44
            },
            {
                "code": "ADMIN_PAYMENT_METHODS", "name": "Payment Methods", "url": "/administration/payment-methods/",
                "parent_code": "ADMINISTRATION", "icon_class": "bi-credit-card", "order": 45
            },
            {
                "code": "ADMIN_FUND_SOURCES", "name": "Fund Sources", "url": "/administration/fund-sources/",
                "parent_code": "ADMINISTRATION", "icon_class": "bi-piggy-bank", "order": 46
            },
            {
                "code": "ADMIN_EXPENSE_CATEGORIES", "name": "Expense Categories", "url": "/administration/expense-categories/",
                "parent_code": "ADMINISTRATION", "icon_class": "bi-tags", "order": 47
            },
            {
                "code": "ADMIN_FINANCIAL_YEARS", "name": "Financial Years", "url": "/administration/financial-years/",
                "parent_code": "ADMINISTRATION", "icon_class": "bi-calendar-range", "order": 48
            },
            {
                "code": "WORKFLOW_ENGINE", "name": "Workflow Engine", "url": "/workflows/",
                "parent_code": "ADMINISTRATION", "icon_class": "bi-diagram-3", "order": 49
            },
            {
                "code": "WORKFLOW_EMAIL", "name": "Email Configurations", "url": "/workflows/email-configs/",
                "parent_code": "ADMINISTRATION", "icon_class": "bi-envelope-paper", "order": 50
            },
            {
                "code": "AI_PREDICTOR", "name": "AI Budget Predictor", "url": "/administration/analytics/expense-predictor/",
                "parent_code": "ADMINISTRATION", "icon_class": "bi-magic", "order": 51
            },
            {
                "code": "SITE_SETTINGS", "name": "Site Settings UI", "url": "/administration/site-settings/",
                "parent_code": "ADMINISTRATION", "icon_class": "bi-sliders", "order": 52
            },
            {
                "code": "BACKUPS", "name": "Database Backup Vault", "url": "/administration/backups/",
                "parent_code": "ADMINISTRATION", "icon_class": "bi-database-down", "order": 53
            },
            {
                "code": "NOTIF_LOGS", "name": "Notification Dispatch Logs", "url": "/audit/notifications/",
                "parent_code": "ADMINISTRATION", "icon_class": "bi-bell", "order": 54
            },
            # Top-level standalone items
            {
                "code": "MY_TASKS", "name": "My Tasks Inbox", "url": "/workflows/my-tasks/",
                "parent_code": None, "icon_class": "bi-inbox-fill", "order": 60
            },
            {
                "code": "QA_DASHBOARD", "name": "QA Test Dashboard", "url": "/qa-dashboard/",
                "parent_code": None, "icon_class": "bi-robot", "order": 70
            },
            {
                "code": "AUDIT_LOGS", "name": "Audit Logs", "url": "/audit/",
                "parent_code": None, "icon_class": "bi-clock-history", "order": 80
            },
        ]

        modules_by_code = {}
        for m in modules_data:
            parent_obj = modules_by_code.get(m["parent_code"]) if m["parent_code"] else None
            mod, _created = AppModule.objects.update_or_create(
                code=m["code"],
                defaults={
                    "name": m["name"],
                    "url": m["url"],
                    "parent": parent_obj,
                    "icon_class": m["icon_class"],
                    "display_order": m["order"],
                    "is_active": True,
                    "available_rights": ALL_RIGHTS
                }
            )
            modules_by_code[m["code"]] = mod

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {len(modules_data)} system modules."))

        # Populate permissions for default roles
        role_type, _ = LookupType.objects.get_or_create(code="SYSTEM_ROLE", defaults={"name": "System Roles"})
        
        default_roles = [
            ("SUPER_ADMIN", "Super Admin"),
            ("PRESIDENT", "President"),
            ("TREASURER", "Chief Treasurer"),
            ("SECRETARY", "Secretary"),
            ("MEMBER", "Committee Member"),
        ]

        for rcode, rval in default_roles:
            role_obj, _ = LookupValue.objects.get_or_create(lookup_type=role_type, code=rcode, defaults={"value": rval})
            for mod in AppModule.objects.all():
                if rcode == "SUPER_ADMIN":
                    rights = ALL_RIGHTS
                elif rcode in ["PRESIDENT", "TREASURER", "SECRETARY"]:
                    if mod.code in ["ADMIN_ROLES", "ADMIN_MODULES", "BACKUPS"]:
                        rights = []
                    else:
                        rights = ["add", "edit", "delete_single", "print_single", "print_bulk"]
                else:
                    if mod.parent and mod.parent.code == "ADMINISTRATION":
                        rights = []
                    else:
                        rights = ["add", "print_single"]

                RolePermission.objects.update_or_create(
                    role=role_obj,
                    module=mod,
                    defaults={"assigned_rights": rights}
                )

        self.stdout.write(self.style.SUCCESS("Successfully seeded role permissions!"))
