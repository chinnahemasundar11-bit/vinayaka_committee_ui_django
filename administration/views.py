from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from .models import (
    SiteSetting, LookupType, LookupValue, FinancialYear,
    FundSource, ExpenseCategory, PaymentMethod
)
from audit.models import AuditLog


def index(request):
    """Administration Central Overview Dashboard."""
    return render(request, "administration/admin_home.html")


def users(request):
    """System users management view."""
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            username = request.POST.get("username", "").strip()
            name = request.POST.get("full_name", "").strip()
            password = request.POST.get("password", "admin123").strip()
            if username:
                first_name = name.split()[0] if name else ""
                last_name = " ".join(name.split()[1:]) if len(name.split()) > 1 else ""
                user = User.objects.create_user(username=username, password=password, first_name=first_name, last_name=last_name)
                AuditLog.objects.create(user=request.user if request.user.is_authenticated else None, action="CREATE", model_name="User", object_id=str(user.id), details=f"Created user {username}")
                messages.success(request, f"User '{username}' created successfully!")
        elif action == "delete":
            u_id = request.POST.get("user_id")
            user_obj = get_object_or_404(User, id=u_id)
            uname = user_obj.username
            user_obj.delete()
            AuditLog.objects.create(user=request.user if request.user.is_authenticated else None, action="DELETE", model_name="User", object_id=str(u_id), details=f"Deleted user {uname}")
            messages.success(request, f"User '{uname}' deleted successfully.")
        return redirect("/administration/users/")

    users_qs = User.objects.all()
    return render(request, "administration/users.html", {"users_list": users_qs})


def roles(request):
    """System roles management view (LookupValue for SYSTEM_ROLE)."""
    role_type, _ = LookupType.objects.get_or_create(code="SYSTEM_ROLE", defaults={"name": "System Roles"})
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            code = request.POST.get("code", "").upper().strip()
            value = request.POST.get("value", "").strip()
            if code and value:
                LookupValue.objects.create(lookup_type=role_type, code=code, value=value)
                messages.success(request, f"Role '{value}' created successfully!")
        elif action == "delete":
            v_id = request.POST.get("role_id")
            val = get_object_or_404(LookupValue, id=v_id)
            val.delete()
            messages.success(request, "Role deleted successfully.")
        return redirect("/administration/roles/")

    roles_qs = LookupValue.objects.filter(lookup_type=role_type)
    return render(request, "administration/roles.html", {"roles_list": roles_qs})


def payment_methods(request):
    """Payment methods master view."""
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            name = request.POST.get("name", "").strip()
            code = request.POST.get("code", "").upper().strip()
            icon = request.POST.get("icon_name", "bi-credit-card").strip()
            if name and code:
                PaymentMethod.objects.create(name=name, code=code, icon_name=icon)
                messages.success(request, f"Payment method '{name}' added successfully!")
        elif action == "delete":
            pm_id = request.POST.get("pm_id")
            pm = get_object_or_404(PaymentMethod, id=pm_id)
            pm.delete()
            messages.success(request, "Payment method deleted.")
        return redirect("/administration/payment-methods/")

    pm_qs = PaymentMethod.objects.all()
    return render(request, "administration/payment_methods.html", {"pm_list": pm_qs})


def fund_sources(request):
    """Fund sources master view."""
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            name = request.POST.get("name", "").strip()
            code = request.POST.get("code", "").upper().strip()
            prefix = request.POST.get("receipt_prefix", "RCPT-").strip()
            if name and code:
                FundSource.objects.create(name=name, code=code, receipt_prefix=prefix)
                messages.success(request, f"Fund source '{name}' added successfully!")
        elif action == "delete":
            fs_id = request.POST.get("fs_id")
            fs = get_object_or_404(FundSource, id=fs_id)
            fs.delete()
            messages.success(request, "Fund source deleted.")
        return redirect("/administration/fund-sources/")

    fs_qs = FundSource.objects.all()
    return render(request, "administration/fund_sources.html", {"fs_list": fs_qs})


def expense_categories(request):
    """Expense categories master view."""
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            name = request.POST.get("name", "").strip()
            code = request.POST.get("code", "").upper().strip()
            if name and code:
                ExpenseCategory.objects.create(name=name, code=code)
                messages.success(request, f"Expense category '{name}' created successfully!")
        elif action == "delete":
            cat_id = request.POST.get("cat_id")
            cat = get_object_or_404(ExpenseCategory, id=cat_id)
            cat.delete()
            messages.success(request, "Expense category deleted.")
        return redirect("/administration/expense-categories/")

    cat_qs = ExpenseCategory.objects.all()
    return render(request, "administration/expense_categories.html", {"cat_list": cat_qs})


def financial_years(request):
    """Financial years master view."""
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            name = request.POST.get("name", "").strip()
            start = request.POST.get("start_date")
            end = request.POST.get("end_date")
            if name and start and end:
                FinancialYear.objects.create(name=name, start_date=start, end_date=end, is_active=True)
                messages.success(request, f"Financial year '{name}' added!")
        elif action == "delete":
            fy_id = request.POST.get("fy_id")
            fy = get_object_or_404(FinancialYear, id=fy_id)
            fy.delete()
            messages.success(request, "Financial year deleted.")
        return redirect("/administration/financial-years/")

    fy_qs = FinancialYear.objects.all()
    return render(request, "administration/financial_years.html", {"fy_list": fy_qs})


def site_settings(request):
    """Global Site Settings & Customization management view."""
    if request.method == "POST":
        updated_count = 0
        for key, value in request.POST.items():
            if key not in ["csrfmiddlewaretoken", "action"]:
                setting, _ = SiteSetting.objects.get_or_create(key=key)
                setting.value = str(value).strip()
                setting.save()
                updated_count += 1
        
        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action="UPDATE",
            model_name="SiteSetting",
            object_id="GLOBAL",
            details=f"Updated {updated_count} site configuration setting(s)"
        )
        messages.success(request, "Site settings updated successfully!")
        return redirect("/administration/site-settings/")

    return render(request, "administration/site_settings.html")
