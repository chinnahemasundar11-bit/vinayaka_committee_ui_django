import os
import sys
import random
import string
import pytest

sys.path.insert(0, os.path.abspath("."))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from django.contrib.auth.models import User
from administration.models import FinancialYear, FundSource, PaymentMethod, ExpenseCategory


@pytest.fixture
def dynamic_phone():
    """Generates dynamic non-static 10-digit mobile number."""
    return "9" + "".join(random.choices(string.digits, k=9))


@pytest.fixture
def dynamic_name():
    """Generates dynamic non-static donor/user name."""
    first = random.choice(["Ramesh", "Suresh", "Priya", "Anitha", "Karthik", "Vikram", "Lakshmi", "Rajesh"])
    last = random.choice(["Kumar", "Rao", "Reddy", "Verma", "Sharma", "Nair", "Patel"])
    return f"{first} {last}"


@pytest.fixture
def dynamic_amount():
    """Generates dynamic non-static financial amount."""
    return round(random.uniform(500.0, 25000.0), 2)


@pytest.fixture
def admin_user():
    """Provides superuser fixture."""
    user = User.objects.filter(username="test_super_admin").first()
    if not user:
        user = User.objects.create_superuser("test_super_admin", "admin@qa.com", "pass123")
    return user


@pytest.fixture
def master_data():
    """Ensures master lookup records exist."""
    fs, _ = FundSource.objects.get_or_create(code="SRC_QA_GEN", defaults={"name": "QA General Fund"})
    pm, _ = PaymentMethod.objects.get_or_create(code="PAY_QA_CASH", defaults={"name": "QA Cash"})
    ec, _ = ExpenseCategory.objects.get_or_create(code="EXP_QA_POOJA", defaults={"name": "QA Pooja Expense"})
    return {"fund_source": fs, "payment_method": pm, "expense_category": ec}
