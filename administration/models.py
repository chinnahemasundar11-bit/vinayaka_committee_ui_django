from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from config.middleware import get_current_user


class ActiveManager(models.Manager):
    """Default QuerySet manager filtering out soft-deleted records."""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class AllObjectsManager(models.Manager):
    """QuerySet manager returning all records including soft-deleted ones."""
    def get_queryset(self):
        return super().get_queryset()


class AuditModel(models.Model):
    """
    Abstract Base Model with standard 6 audit metadata fields and soft-delete capabilities.
    """
    created_by = models.ForeignKey(
        User, on_delete=models.PROTECT,
        related_name="%(class)s_created",
        null=True, blank=True,
        help_text="User who created the record"
    )
    updated_by = models.ForeignKey(
        User, on_delete=models.PROTECT,
        related_name="%(class)s_updated",
        null=True, blank=True,
        help_text="User who last updated the record"
    )
    deleted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        related_name="%(class)s_deleted",
        null=True, blank=True,
        help_text="User who soft-deleted the record"
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when created")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when updated")
    deleted_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when soft-deleted")
    is_deleted = models.BooleanField(default=False, db_index=True, help_text="Soft delete status flag")

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and user.is_authenticated:
            if not self.pk and not self.created_by:
                self.created_by = user
            self.updated_by = user
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        """Soft delete record by toggling is_deleted=True and populating audit timestamps."""
        user = get_current_user()
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if user and user.is_authenticated:
            self.deleted_by = user
        self.save()


class LookupType(AuditModel):
    """Central categories for dynamic dropdown options."""
    code = models.CharField(max_length=50, unique=True, help_text="Unique category identifier (e.g. PAYMENT_MODE)")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "administration_lookup_type"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class LookupValue(AuditModel):
    """Individual dynamic choice options linked to a LookupType."""
    lookup_type = models.ForeignKey(LookupType, on_delete=models.CASCADE, related_name="values")
    code = models.CharField(max_length=50)
    value = models.CharField(max_length=150, help_text="Display text in UI select dropdown")
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "administration_lookup_value"
        ordering = ["display_order", "value"]
        unique_together = ["lookup_type", "code"]

    def __str__(self):
        return self.value


class SiteSetting(AuditModel):
    """Global system configuration key-value settings."""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    category = models.CharField(max_length=50, default="GENERAL")
    description = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "administration_site_setting"
        ordering = ["key"]

    def __str__(self):
        return f"{self.key}: {self.value}"


class FinancialYear(AuditModel):
    """Accounting financial period master."""
    name = models.CharField(max_length=100, help_text="e.g. FY 2026 - 2027")
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)

    class Meta:
        db_table = "administration_financial_year"
        ordering = ["-start_date"]

    def __str__(self):
        return self.name


class FundSource(AuditModel):
    """Contribution categories master."""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    receipt_prefix = models.CharField(max_length=20, default="RCPT-")
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "administration_fund_source"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ExpenseCategory(AuditModel):
    """Expense spending heads master."""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    requires_approval = models.BooleanField(default=False)
    approval_threshold = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "administration_expense_category"
        ordering = ["name"]

    def __str__(self):
        return self.name


class PaymentMethod(AuditModel):
    """Payment channels master."""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    requires_ref_no = models.BooleanField(default=False)
    icon_name = models.CharField(max_length=50, default="bi-credit-card")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "administration_payment_method"
        ordering = ["name"]

    def __str__(self):
        return self.name


DEFAULT_MODULE_RIGHTS = [
    ("add", "Add Record"),
    ("edit", "Edit Record"),
    ("delete_single", "Single Delete"),
    ("delete_bulk", "Bulk Delete"),
    ("print_single", "Single Print"),
    ("print_bulk", "Bulk Print"),
]


class AppModule(AuditModel):
    """Dynamic Sidebar Navigation & System Module Registry."""
    code = models.CharField(max_length=50, unique=True, help_text="Unique module code e.g. FUND_RECEIPTS")
    name = models.CharField(max_length=100, help_text="Menu display name e.g. Funds Received")
    url = models.CharField(max_length=200, help_text="Navigation URL matching config URLs e.g. /funds/")
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children",
        help_text="Parent module for multi-level navigation tree"
    )
    icon_class = models.CharField(max_length=50, default="bi-folder", help_text="Bootstrap icon class")
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    available_rights = models.JSONField(
        default=list,
        help_text="List of right codes supported by module (add, edit, delete_single, delete_bulk, print_single, print_bulk)"
    )

    class Meta:
        db_table = "administration_app_module"
        ordering = ["display_order", "name"]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} -> {self.name} [{self.code}]"
        return f"{self.name} [{self.code}]"


class RolePermission(AuditModel):
    """Matrix mapping system roles to module rights."""
    role = models.ForeignKey(LookupValue, on_delete=models.CASCADE, related_name="role_permissions")
    module = models.ForeignKey(AppModule, on_delete=models.CASCADE, related_name="role_permissions")
    assigned_rights = models.JSONField(
        default=list,
        help_text="List of assigned right codes for this role and module"
    )

    class Meta:
        db_table = "administration_role_permission"
        unique_together = ["role", "module"]

    def __str__(self):
        return f"{self.role.value} - {self.module.name} ({len(self.assigned_rights)} rights)"

