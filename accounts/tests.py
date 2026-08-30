from django.test import TestCase, Client
from django.contrib.auth.models import User
from members.models import Member
from accounts.permissions import get_user_role


class RBACTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Super Admin
        self.superuser = User.objects.create_superuser("admin_user", "admin@test.com", "pass123")

        # Treasurer Member
        self.treasurer_user = User.objects.create_user("9876501234", "treasurer@test.com", "pass123")
        Member.objects.create(
            member_id="MBR-T01",
            full_name="Suresh Treasurer",
            mobile_number="9876501234",
            committee_position="Chief Treasurer",
            system_role="Treasurer",
            joining_date="2026-01-01"
        )

        # General Member
        self.general_user = User.objects.create_user("9876511111", "member@test.com", "pass123")
        Member.objects.create(
            member_id="MBR-M01",
            full_name="Ravi Member",
            mobile_number="9876511111",
            committee_position="Member",
            system_role="Committee Member",
            joining_date="2026-01-01"
        )

    def test_role_evaluation(self):
        self.assertEqual(get_user_role(self.superuser), "Super Admin")
        self.assertEqual(get_user_role(self.treasurer_user), "Treasurer")
        self.assertEqual(get_user_role(self.general_user), "Committee Member")

    def test_unauthenticated_access_redirects_login(self):
        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_admin_route_restricted_for_general_member(self):
        self.client.login(username="9876511111", password="pass123")
        response = self.client.get("/administration/site-settings/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/dashboard/", response.url)

    def test_admin_route_accessible_by_superuser(self):
        self.client.login(username="admin_user", password="pass123")
        response = self.client.get("/administration/site-settings/")
        self.assertEqual(response.status_code, 200)

    def test_treasurer_can_access_fund_add(self):
        self.client.login(username="9876501234", password="pass123")
        response = self.client.get("/funds/add/")
        self.assertEqual(response.status_code, 200)

    def test_general_member_restricted_from_fund_add(self):
        self.client.login(username="9876511111", password="pass123")
        response = self.client.get("/funds/add/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/dashboard/", response.url)


class MFAAndOTPOptionTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="9998887776", email="testotp@vinayaka.org", password="Password@123")

    def test_login_mfa_disabled(self):
        from administration.models import SiteSetting
        SiteSetting.objects.update_or_create(key="MFA_ENABLED", defaults={"value": "false"})
        response = self.client.post("/accounts/login/", {"username": "9998887776", "password": "Password@123"})
        self.assertRedirects(response, "/dashboard/")

    def test_login_mfa_enabled_redirects_to_otp_verify(self):
        from administration.models import SiteSetting
        SiteSetting.objects.update_or_create(key="MFA_ENABLED", defaults={"value": "true"})
        response = self.client.post("/accounts/login/", {"username": "9998887776", "password": "Password@123"})
        self.assertRedirects(response, "/accounts/verify-mfa-otp/")
        self.assertIn("mfa_otp", self.client.session)

    def test_mfa_otp_verification_success(self):
        from administration.models import SiteSetting
        SiteSetting.objects.update_or_create(key="MFA_ENABLED", defaults={"value": "true"})
        self.client.post("/accounts/login/", {"username": "9998887776", "password": "Password@123"})
        otp_code = self.client.session["mfa_otp"]
        
        # Verify valid OTP
        response = self.client.post("/accounts/verify-mfa-otp/", {"action": "verify", "otp_code": otp_code})
        self.assertRedirects(response, "/dashboard/")

    def test_mfa_otp_verification_invalid_code(self):
        from administration.models import SiteSetting
        SiteSetting.objects.update_or_create(key="MFA_ENABLED", defaults={"value": "true"})
        self.client.post("/accounts/login/", {"username": "9998887776", "password": "Password@123"})
        
        # Post invalid OTP
        response = self.client.post("/accounts/verify-mfa-otp/", {"action": "verify", "otp_code": "000000"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid OTP code")

    def test_forgot_password_otp_and_reset_flow(self):
        # Step 1: Request OTP
        response = self.client.post("/accounts/forgot-password/", {"mobile": "9998887776"})
        self.assertRedirects(response, "/accounts/verify-forgot-otp/")
        self.assertIn("reset_otp", self.client.session)
        otp_code = self.client.session["reset_otp"]

        # Step 2: Verify OTP and reset password
        reset_resp = self.client.post("/accounts/verify-forgot-otp/", {
            "action": "verify",
            "otp_code": otp_code,
            "new_password": "NewSecretPassword@123",
            "confirm_password": "NewSecretPassword@123"
        })
        self.assertRedirects(reset_resp, "/accounts/login/")

        # Step 3: Login with new password
        login_resp = self.client.post("/accounts/login/", {"username": "9998887776", "password": "NewSecretPassword@123"})
        self.assertRedirects(login_resp, "/dashboard/")

