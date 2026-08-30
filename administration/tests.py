from django.test import TestCase
from django.contrib.auth.models import User
from django.core.management import call_command
from administration.models import (
    LookupType, LookupValue, SiteSetting, FinancialYear,
    FundSource, ExpenseCategory, PaymentMethod
)


class AdministrationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("testuser", "test@example.com", "password123")

    def test_lookup_type_and_value_creation(self):
        ltype = LookupType.objects.create(code="TEST_TYPE", name="Test Category")
        lval = LookupValue.objects.create(lookup_type=ltype, code="TEST_VAL", value="Test Value", display_order=1)

        self.assertEqual(LookupType.objects.count(), 1)
        self.assertEqual(LookupValue.objects.count(), 1)
        self.assertEqual(str(lval), "Test Value")

    def test_soft_delete_and_audit(self):
        fs = FundSource.objects.create(name="Donation", code="SRC_DONATION")
        self.assertFalse(fs.is_deleted)
        self.assertEqual(FundSource.objects.count(), 1)

        # Perform soft delete
        fs.delete()

        self.assertTrue(fs.is_deleted)
        self.assertEqual(FundSource.objects.count(), 0)
        self.assertEqual(FundSource.all_objects.count(), 1)

    def test_seed_data_command(self):
        call_command("seed_data")
        self.assertTrue(SiteSetting.objects.filter(key="SITE_NAME").exists())
        self.assertTrue(FinancialYear.objects.filter(is_active=True).exists())
        self.assertTrue(FundSource.objects.exists())
        self.assertTrue(ExpenseCategory.objects.exists())
        self.assertTrue(PaymentMethod.objects.exists())

    def test_financial_year_term_switcher(self):
        import datetime
        from django.test import Client
        fy_active = FinancialYear.objects.create(name="FY 2026 - 2027", start_date=datetime.date(2026, 4, 1), end_date=datetime.date(2027, 3, 31), is_active=True, is_locked=False)
        fy_archived = FinancialYear.objects.create(name="FY 2024 - 2025 (Archived)", start_date=datetime.date(2024, 4, 1), end_date=datetime.date(2025, 3, 31), is_active=False, is_locked=True)

        client = Client()
        admin_user = User.objects.create_superuser("admin_term", "term@test.com", "pass123")
        client.force_login(admin_user)

        # Switch to archived year
        response = client.post(f"/administration/switch-year/{fy_archived.id}/", follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Historical Festival Term:")
        self.assertContains(response, "FY 2024 - 2025 (Archived)")

        # Reset back to active year
        response = client.post("/administration/switch-year/0/", follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Historical Festival Term:")

    def test_part_1_high_value_features(self):
        from funds.models import FundReceipt
        fs = FundSource.objects.create(name="Youth Fund", code="SRC_YOUTH_P1")
        pm = PaymentMethod.objects.create(name="Cash", code="PAY_CASH_P1")
        receipt = FundReceipt.objects.create(
            receipt_number="RCPT-P1-001",
            donor_name="Part 1 Donor",
            donor_phone="9988776655",
            fund_source=fs,
            payment_method=pm,
            amount=5000.00,
            date_received="2026-08-25"
        )
        from django.test import Client
        c = Client()

        # 1. Test LED TV Wall of Honor (Unauthenticated public view)
        res1 = c.get("/public/wall-of-honor/")
        self.assertEqual(res1.status_code, 200)
        self.assertContains(res1, "Part 1 Donor")
        self.assertContains(res1, "LIVE FESTIVAL LED DISPLAY")

        # 2. Test Donor QR Verification Portal (Unauthenticated public view)
        res2 = c.get(f"/public/verify-receipt/{receipt.receipt_number}/")
        self.assertEqual(res2.status_code, 200)
        self.assertContains(res2, "OFFICIALLY VERIFIED RECORD")
        self.assertContains(res2, "Part 1 Donor")

        # 3. Test AI Expense Predictor (Authenticated)
        admin_u = User.objects.create_superuser("p1_admin", "p1@test.com", "pass123")
        c.force_login(admin_u)
        res3 = c.get("/administration/analytics/expense-predictor/")
        self.assertEqual(res3.status_code, 200)
        self.assertContains(res3, "Expense Velocity Predictor")

        # 4. Test PWA Offline Receipt Bulk Sync API
        payload = {
            "receipts": [
                {
                    "receipt_number": "RCPT-OFF-999",
                    "donor_name": "Offline Donor",
                    "donor_phone": "9876543210",
                    "amount": 3500.00,
                    "date_received": "2026-08-25"
                }
            ]
        }
        res4 = c.post("/funds/api/sync-offline-receipts/", data=payload, content_type="application/json")
        self.assertEqual(res4.status_code, 200)
        self.assertTrue(FundReceipt.objects.filter(receipt_number="RCPT-OFF-999").exists())

    def test_steps_11a_to_11d_features(self):
        from django.test import Client
        from administration.webhooks import dispatch_high_value_event
        from administration.models import SiteSetting

        c = Client()
        admin_u = User.objects.create_superuser("admin_11", "admin11@test.com", "pass123")
        c.force_login(admin_u)

        # 1. Test Excel & Audit PDF Report endpoints
        res_excel = c.get("/reports/export/excel/")
        self.assertEqual(res_excel.status_code, 200)

        res_audit = c.get("/reports/export/audit-pdf/")
        self.assertEqual(res_audit.status_code, 200)
        self.assertContains(res_audit, "OFFICIAL EXECUTIVE FINANCIAL AUDIT STATEMENT")

        # 2. Test Real-Time Webhook Alert Dispatcher
        payload = dispatch_high_value_event("HIGH_VALUE_DONATION", "RCPT-100k", 100000.00, user=admin_u, details="Major donor contribution")
        self.assertEqual(payload["event_type"], "HIGH_VALUE_DONATION")
        self.assertEqual(payload["amount"], 100000.00)

        # 3. Test MFA Setting toggle
        SiteSetting.objects.update_or_create(key="MFA_ENABLED", defaults={"value": "true"})
        self.assertEqual(SiteSetting.objects.get(key="MFA_ENABLED").value, "true")

    def test_backup_vault_creation_and_listing(self):
        from django.test import Client

        c = Client()
        admin_u = User.objects.create_superuser("bk_admin", "bk@test.com", "pass123")
        c.force_login(admin_u)

        # 1. Test Backup Vault UI page
        res = c.get("/administration/backups/")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Database Backup & Restore Vault")

        # 2. Test Backup Snapshot Creation
        res_create = c.post("/administration/backups/", data={"action": "create"})
        self.assertEqual(res_create.status_code, 302)

        # 3. Verify Backup Vault listing shows created snapshot
        res_after = c.get("/administration/backups/")
        self.assertEqual(res_after.status_code, 200)
        self.assertContains(res_after, "festival_db_backup_")
