from django.test import TestCase, Client
from django.contrib.auth.models import User
from accounts.views import generate_otp, send_otp_notification


class AccountsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("test_super_admin", "admin@qa.com", "pass123")

    def test_user_authentication_flow(self):
        client = Client()
        login_success = client.login(username=self.user.username, password="pass123")
        self.assertTrue(login_success)

    def test_otp_generation(self):
        user = User.objects.create_user(username="9988776655", password="password123")
        otp_code = generate_otp()
        self.assertEqual(len(otp_code), 6)
        send_otp_notification(user, otp_code, purpose="Testing")

    def test_mfa_toggle_behavior(self):
        from administration.models import SiteSetting
        SiteSetting.objects.update_or_create(key="MFA_ENABLED", defaults={"value": "True"})
        setting = SiteSetting.objects.get(key="MFA_ENABLED")
        self.assertEqual(setting.value, "True")

    def test_forgot_password_otp_full_flow(self):
        client = Client()
        target_mobile = "7032524939"
        
        # 1. Initiate Forgot Password OTP
        resp = client.post("/accounts/forgot-password/", {"mobile": target_mobile}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("reset_otp", client.session)
        otp_code = client.session["reset_otp"]
        self.assertEqual(len(otp_code), 6)

        # 2. Check NotificationLog creation
        from audit.models import NotificationLog
        notif = NotificationLog.objects.filter(recipient_phone=target_mobile).last()
        self.assertIsNotNone(notif)
        self.assertIn("OTP", notif.channel)

        # 3. Test OTP Resend
        resend_resp = client.post("/accounts/verify-forgot-otp/", {"action": "resend"})
        self.assertEqual(resend_resp.status_code, 200)
        new_otp_code = client.session["reset_otp"]
        self.assertEqual(len(new_otp_code), 6)

        # 4. Verify OTP & Reset Password
        verify_resp = client.post("/accounts/verify-forgot-otp/", {
            "action": "verify",
            "otp_code": new_otp_code,
            "new_password": "newsecretpassword123",
            "confirm_password": "newsecretpassword123"
        }, follow=True)
        self.assertEqual(verify_resp.status_code, 200)

        # 5. Login with new password
        login_resp = client.post("/accounts/login/", {
            "username": target_mobile,
            "password": "newsecretpassword123"
        }, follow=True)
        self.assertEqual(login_resp.status_code, 200)
