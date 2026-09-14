from django.test import TestCase, Client
from django.contrib.auth.models import User
from administration.models import AppModule, RolePermission, LookupType, LookupValue
from accounts.permissions import has_module_action_right

class RBACDynamicModulesTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create Super Admin User
        self.admin_user = User.objects.create_superuser(username="admin", password="password123")
        
        # Create Regular Member User
        self.member_user = User.objects.create_user(username="member1", password="password123")
        
        # Roles LookupType
        self.role_type, _ = LookupType.objects.get_or_create(code="SYSTEM_ROLE", defaults={"name": "System Roles"})
        self.admin_role, _ = LookupValue.objects.get_or_create(lookup_type=self.role_type, code="SUPER_ADMIN", defaults={"value": "Super Admin"})
        self.treasurer_role, _ = LookupValue.objects.get_or_create(lookup_type=self.role_type, code="TREASURER", defaults={"value": "Chief Treasurer"})
        
        # Parent Module
        self.parent_mod = AppModule.objects.create(
            code="FINANCE_MGMT", name="Finance Management", url="#",
            icon_class="bi-wallet2", display_order=10, is_active=True,
            available_rights=["add", "edit", "delete_single", "delete_bulk", "print_single", "print_bulk"]
        )
        
        # Child Module
        self.child_mod = AppModule.objects.create(
            code="FUNDS_RECEIVED", name="Funds Received", url="/funds/",
            parent=self.parent_mod, icon_class="bi-cash-coin", display_order=11, is_active=True,
            available_rights=["add", "edit", "delete_single", "delete_bulk", "print_single", "print_bulk"]
        )

    def test_module_creation(self):
        """Test creating parent and child sidebar modules."""
        self.assertEqual(AppModule.objects.count(), 2)
        self.assertEqual(self.child_mod.parent, self.parent_mod)
        self.assertIn("add", self.child_mod.available_rights)

    def test_role_permission_assignment(self):
        """Test assigning rights in RolePermission tree matrix."""
        perm = RolePermission.objects.create(
            role=self.treasurer_role,
            module=self.child_mod,
            assigned_rights=["add", "edit", "print_single"]
        )
        self.assertEqual(perm.assigned_rights, ["add", "edit", "print_single"])

    def test_action_right_enforcement(self):
        """Test has_module_action_right for superuser and regular users."""
        # Superuser has full rights
        self.assertTrue(has_module_action_right(self.admin_user, "FUNDS_RECEIVED", "delete_bulk"))
        
        # Unassigned user returns False
        self.assertFalse(has_module_action_right(self.member_user, "FUNDS_RECEIVED", "delete_bulk"))

    def test_modules_view_access(self):
        """Test module management view accessibility for admin."""
        self.client.login(username="admin", password="password123")
        response = self.client.get("/administration/modules/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Finance Management")
        self.assertContains(response, "Funds Received")

    def test_roles_tree_view_access(self):
        """Test roles permission tree view rendering."""
        self.client.login(username="admin", password="password123")
        response = self.client.get("/administration/roles/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Permission Tree Matrix")

    def test_direct_url_route_blocking_and_access(self):
        """Test that unassigned users cannot access module GET route, and assigned users can."""
        from members.models import Member

        # Link member_user to a Member profile with Chief Treasurer role
        member_profile = Member.objects.create(
            member_id="MBR-T01",
            full_name="Treasurer User",
            mobile_number=self.member_user.username,
            committee_position="Treasurer",
            system_role="Chief Treasurer",
            joining_date="2026-01-01",
            status="Active"
        )

        self.client.login(username="member1", password="password123")

        # 1. No rights assigned yet -> GET /funds/ should redirect to /dashboard/
        res = self.client.get("/funds/")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/dashboard/", res.url)

        # 2. Assign rights for FUNDS_RECEIVED -> GET /funds/ should return 200
        RolePermission.objects.create(
            role=self.treasurer_role,
            module=self.child_mod,
            assigned_rights=["add", "edit", "print_single"]
        )
        res_allowed = self.client.get("/funds/")
        self.assertEqual(res_allowed.status_code, 200)

        # 3. Add page access with 'add' right
        res_add = self.client.get("/funds/add/")
        self.assertEqual(res_add.status_code, 200)

        # 4. Remove all rights -> direct access should be blocked again
        perm = RolePermission.objects.get(role=self.treasurer_role, module=self.child_mod)
        perm.assigned_rights = []
        perm.save()

        res_blocked_again = self.client.get("/funds/")
        self.assertEqual(res_blocked_again.status_code, 302)
        self.assertIn("/dashboard/", res_blocked_again.url)

    def test_cascading_folder_sidebar_removal(self):
        """Test that parent folder disappears from sidebar when all child submodules are unassigned."""
        from accounts.context_processors import user_permissions
        from django.test import RequestFactory
        from members.models import Member

        Member.objects.create(
            member_id="MBR-T02",
            full_name="Treasurer User 2",
            mobile_number=self.member_user.username,
            committee_position="Treasurer",
            system_role="Chief Treasurer",
            joining_date="2026-01-01",
            status="Active"
        )

        rf = RequestFactory()
        req = rf.get("/dashboard/")
        req.user = self.member_user

        # 1. Initially no permissions -> sidebar has 0 module categories
        ctx = user_permissions(req)
        self.assertEqual(len(ctx["sidebar_modules_tree"]), 0)

        # 2. Assign FUNDS_RECEIVED rights -> Finance Management parent and Funds Received child appear
        perm, _ = RolePermission.objects.get_or_create(
            role=self.treasurer_role,
            module=self.child_mod,
            defaults={"assigned_rights": ["add"]}
        )
        perm.assigned_rights = ["add"]
        perm.save()

        ctx = user_permissions(req)
        self.assertEqual(len(ctx["sidebar_modules_tree"]), 1)
        self.assertEqual(ctx["sidebar_modules_tree"][0]["module"].name, "Finance Management")
        self.assertEqual(len(ctx["sidebar_modules_tree"][0]["children"]), 1)

        # 3. Remove rights -> Finance Management disappears completely
        perm.assigned_rights = []
        perm.save()

        ctx = user_permissions(req)
        self.assertEqual(len(ctx["sidebar_modules_tree"]), 0)

