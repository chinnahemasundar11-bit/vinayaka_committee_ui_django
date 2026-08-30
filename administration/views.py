from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from .models import (
    SiteSetting, LookupType, LookupValue, FinancialYear,
    FundSource, ExpenseCategory, PaymentMethod,
    AppModule, RolePermission, DEFAULT_MODULE_RIGHTS
)
from audit.models import AuditLog


from accounts.permissions import admin_required


def paginate_queryset(request, queryset, default_per_page=10):
    try:
        per_page = int(request.GET.get("per_page", default_per_page))
        if per_page not in [10, 50, 100, 500]: per_page = default_per_page
    except (ValueError, TypeError):
        per_page = default_per_page
    from django.core.paginator import Paginator
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return page_obj, per_page


@admin_required
def index(request):
    """Administration Central Overview Dashboard."""
    return render(request, "administration/admin_home.html")


@admin_required
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

    page_obj, per_page = paginate_queryset(request, User.objects.all())
    return render(request, "administration/users.html", {"users_list": page_obj, "page_obj": page_obj, "per_page": per_page})


@admin_required
def modules(request):
    """Dynamic Sidebar Modules Management View."""
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            code = request.POST.get("code", "").upper().strip()
            name = request.POST.get("name", "").strip()
            url = request.POST.get("url", "").strip()
            parent_id = request.POST.get("parent_id")
            icon_class = request.POST.get("icon_class", "bi-folder").strip()
            order = int(request.POST.get("display_order", 0))
            rights = request.POST.getlist("rights")
            
            parent = AppModule.objects.filter(id=parent_id).first() if parent_id else None
            if code and name:
                mod = AppModule.objects.create(
                    code=code, name=name, url=url or "#", parent=parent,
                    icon_class=icon_class, display_order=order,
                    available_rights=rights or ["add", "edit", "delete_single", "delete_bulk", "print_single", "print_bulk"]
                )
                AuditLog.objects.create(user=request.user, action="CREATE", model_name="AppModule", object_id=str(mod.id), details=f"Created module {name} [{code}]")
                messages.success(request, f"Module '{name}' created successfully!")
        elif action == "edit":
            mod_id = request.POST.get("module_id")
            mod = get_object_or_404(AppModule, id=mod_id)
            mod.name = request.POST.get("name", "").strip() or mod.name
            mod.url = request.POST.get("url", "").strip() or mod.url
            parent_id = request.POST.get("parent_id")
            mod.parent = AppModule.objects.filter(id=parent_id).first() if parent_id else None
            mod.icon_class = request.POST.get("icon_class", "bi-folder").strip()
            mod.display_order = int(request.POST.get("display_order", mod.display_order))
            mod.available_rights = request.POST.getlist("rights")
            mod.save()
            AuditLog.objects.create(user=request.user, action="UPDATE", model_name="AppModule", object_id=str(mod.id), details=f"Updated module {mod.name}")
            messages.success(request, f"Module '{mod.name}' updated successfully.")
        elif action == "delete":
            mod_id = request.POST.get("module_id")
            mod = get_object_or_404(AppModule, id=mod_id)
            mname = mod.name
            mod.delete()
            AuditLog.objects.create(user=request.user, action="DELETE", model_name="AppModule", object_id=str(mod_id), details=f"Deleted module {mname}")
            messages.success(request, f"Module '{mname}' deleted successfully.")
        elif action == "bulk_delete":
            selected_ids = request.POST.getlist("selected_ids")
            if selected_ids:
                count = AppModule.objects.filter(id__in=selected_ids).delete()[0]
                AuditLog.objects.create(user=request.user, action="BULK_DELETE", model_name="AppModule", object_id="MULTIPLE", details=f"Bulk deleted {count} modules")
                messages.success(request, f"Successfully deleted {count} selected module(s).")
        return redirect("/administration/modules/")

    modules_qs = AppModule.objects.all().select_related("parent").order_by("display_order", "name")
    parent_modules = AppModule.objects.filter(parent__isnull=True).order_by("display_order", "name")
    page_obj, per_page = paginate_queryset(request, modules_qs)
    
    return render(request, "administration/modules.html", {
        "modules_list": page_obj,
        "page_obj": page_obj,
        "per_page": per_page,
        "parent_modules": parent_modules,
        "default_rights": DEFAULT_MODULE_RIGHTS,
    })


@admin_required
def roles(request):
    """System roles management & interactive Permission Tree View."""
    role_type, _ = LookupType.objects.get_or_create(code="SYSTEM_ROLE", defaults={"name": "System Roles"})
    
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            code = request.POST.get("code", "").upper().strip()
            value = request.POST.get("value", "").strip()
            if code and value:
                role_obj, created = LookupValue.objects.get_or_create(lookup_type=role_type, code=code, defaults={"value": value})
                if not created:
                    role_obj.value = value
                    role_obj.save()
                messages.success(request, f"Role '{value}' saved successfully!")
        elif action == "delete":
            v_id = request.POST.get("role_id")
            val = get_object_or_404(LookupValue, id=v_id)
            val.delete()
            messages.success(request, "Role deleted successfully.")
        elif action == "save_permissions":
            role_id = request.POST.get("role_id")
            role_obj = get_object_or_404(LookupValue, id=role_id, lookup_type=role_type)
            
            # Map of module_id -> list of assigned right strings
            module_rights_map = {}
            for key, val_list in request.POST.lists():
                if key.startswith("rights_mod_"):
                    mod_id = key.replace("rights_mod_", "")
                    module_rights_map[mod_id] = val_list
            
            # Update RolePermission records for all modules
            for mod in AppModule.objects.all():
                assigned = module_rights_map.get(str(mod.id), [])
                RolePermission.objects.update_or_create(
                    role=role_obj,
                    module=mod,
                    defaults={"assigned_rights": assigned}
                )
            
            AuditLog.objects.create(
                user=request.user,
                action="UPDATE_PERMISSIONS",
                model_name="RolePermission",
                object_id=str(role_id),
                details=f"Updated permission matrix for role {role_obj.value}"
            )
            messages.success(request, f"Permissions updated successfully for role '{role_obj.value}'!")
            return redirect(f"/administration/roles/?selected_role_id={role_id}")
            
        return redirect("/administration/roles/")

    roles_list = LookupValue.objects.filter(lookup_type=role_type)
    selected_role_id = request.GET.get("selected_role_id") or (roles_list.first().id if roles_list.exists() else None)
    
    selected_role = None
    role_perms_dict = {}
    if selected_role_id:
        selected_role = LookupValue.objects.filter(id=selected_role_id).first()
        if selected_role:
            perms = RolePermission.objects.filter(role=selected_role)
            for p in perms:
                role_perms_dict[p.module_id] = p.assigned_rights

    # Tree View Structure: Parent modules with pre-fetched children
    all_modules = AppModule.objects.all().order_by("display_order", "name")
    parent_modules = [m for m in all_modules if m.parent_id is None]
    
    module_tree = []
    for parent in parent_modules:
        children = [m for m in all_modules if m.parent_id == parent.id]
        module_tree.append({
            "parent": parent,
            "parent_rights": role_perms_dict.get(parent.id, []),
            "children": [
                {
                    "module": child,
                    "assigned_rights": role_perms_dict.get(child.id, [])
                }
                for child in children
            ]
        })

    page_obj, per_page = paginate_queryset(request, roles_list)
    return render(request, "administration/roles.html", {
        "roles_list": page_obj,
        "page_obj": page_obj,
        "per_page": per_page,
        "all_roles": roles_list,
        "selected_role": selected_role,
        "module_tree": module_tree,
        "default_rights": DEFAULT_MODULE_RIGHTS,
    })



@admin_required
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
        elif action == "bulk_delete":
            selected_ids = request.POST.getlist("selected_ids")
            if selected_ids:
                count = PaymentMethod.objects.filter(id__in=selected_ids).delete()[0]
                messages.success(request, f"Deleted {count} payment method(s).")
        return redirect("/administration/payment-methods/")

    page_obj, per_page = paginate_queryset(request, PaymentMethod.objects.all())
    return render(request, "administration/payment_methods.html", {"pm_list": page_obj, "page_obj": page_obj, "per_page": per_page})


@admin_required
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
        elif action == "bulk_delete":
            selected_ids = request.POST.getlist("selected_ids")
            if selected_ids:
                count = FundSource.objects.filter(id__in=selected_ids).delete()[0]
                messages.success(request, f"Deleted {count} fund source(s).")
        return redirect("/administration/fund-sources/")

    page_obj, per_page = paginate_queryset(request, FundSource.objects.all())
    return render(request, "administration/fund_sources.html", {"fs_list": page_obj, "page_obj": page_obj, "per_page": per_page})


@admin_required
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
        elif action == "bulk_delete":
            selected_ids = request.POST.getlist("selected_ids")
            if selected_ids:
                count = ExpenseCategory.objects.filter(id__in=selected_ids).delete()[0]
                messages.success(request, f"Deleted {count} expense category/categories.")
        return redirect("/administration/expense-categories/")

    page_obj, per_page = paginate_queryset(request, ExpenseCategory.objects.all())
    return render(request, "administration/expense_categories.html", {"cat_list": page_obj, "page_obj": page_obj, "per_page": per_page})


@admin_required
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
        elif action == "bulk_delete":
            selected_ids = request.POST.getlist("selected_ids")
            if selected_ids:
                count = FinancialYear.objects.filter(id__in=selected_ids).delete()[0]
                messages.success(request, f"Deleted {count} financial year(s).")
        return redirect("/administration/financial-years/")

    page_obj, per_page = paginate_queryset(request, FinancialYear.objects.all())
    return render(request, "administration/financial_years.html", {"fy_list": page_obj, "page_obj": page_obj, "per_page": per_page})



import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
from django.utils.translation import gettext as _

@admin_required
def site_settings(request):
    """Global Site Settings & Customization management view with Image File Upload support."""
    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "clear_logo":
            for k in ["SITE_LOGO_URL", "SITE_LOGO_FILE_NAME", "SITE_LOGO_FILE_SIZE", "SITE_LOGO_TYPE", "SITE_LOGO_UPLOADED_AT"]:
                SiteSetting.objects.filter(key=k).delete()
            messages.success(request, _("Custom logo image removed. Reverted to default icon."))
            return redirect("/administration/site-settings/")

        if action == "clear_qr_image":
            for k in ["UPI_QR_IMAGE_URL", "UPI_QR_FILE_NAME", "UPI_QR_FILE_SIZE", "UPI_QR_UPLOADED_AT"]:
                SiteSetting.objects.filter(key=k).delete()
            messages.success(request, _("Custom QR Code image removed. Reverted to dynamic generated QR code."))
            return redirect("/administration/site-settings/")

        updated_count = 0
        for key, value in request.POST.items():
            if key not in ["csrfmiddlewaretoken", "action"]:
                setting, _obj = SiteSetting.objects.get_or_create(key=key)
                setting.value = str(value).strip()
                setting.save()
                updated_count += 1
                if key == "DEFAULT_LANGUAGE" and value in ["en", "te", "hi"]:
                    request.session["_language"] = value

        # Process uploaded logo image file
        if request.FILES.get("SITE_LOGO_FILE"):
            logo_file = request.FILES["SITE_LOGO_FILE"]
            upload_dir = os.path.join(settings.MEDIA_ROOT, "site_logos")
            os.makedirs(upload_dir, exist_ok=True)
            
            fs = FileSystemStorage(location=upload_dir, base_url="/media/site_logos/")
            filename = fs.save(logo_file.name, logo_file)
            file_url = fs.url(filename)

            # Format file size (KB / MB)
            bytes_size = logo_file.size
            size_str = f"{bytes_size / 1048576:.2f} MB" if bytes_size >= 1048576 else f"{bytes_size / 1024:.1f} KB"

            # Save logo image URL & metadata fields in SiteSetting
            SiteSetting.objects.update_or_create(key="SITE_LOGO_URL", defaults={"value": file_url, "category": "BRANDING"})
            SiteSetting.objects.update_or_create(key="SITE_LOGO_FILE_NAME", defaults={"value": logo_file.name, "category": "BRANDING"})
            SiteSetting.objects.update_or_create(key="SITE_LOGO_FILE_SIZE", defaults={"value": size_str, "category": "BRANDING"})
            SiteSetting.objects.update_or_create(key="SITE_LOGO_TYPE", defaults={"value": logo_file.content_type, "category": "BRANDING"})
            SiteSetting.objects.update_or_create(key="SITE_LOGO_UPLOADED_AT", defaults={"value": timezone.now().strftime("%Y-%m-%d %H:%M:%S"), "category": "BRANDING"})
            updated_count += 1

        # Process uploaded custom UPI QR code image file
        if request.FILES.get("UPI_QR_IMAGE_FILE"):
            qr_file = request.FILES["UPI_QR_IMAGE_FILE"]
            upload_dir = os.path.join(settings.MEDIA_ROOT, "qr_codes")
            os.makedirs(upload_dir, exist_ok=True)

            fs = FileSystemStorage(location=upload_dir, base_url="/media/qr_codes/")
            filename = fs.save(qr_file.name, qr_file)
            file_url = fs.url(filename)

            bytes_size = qr_file.size
            size_str = f"{bytes_size / 1048576:.2f} MB" if bytes_size >= 1048576 else f"{bytes_size / 1024:.1f} KB"

            SiteSetting.objects.update_or_create(key="UPI_QR_IMAGE_URL", defaults={"value": file_url, "category": "PAYMENT"})
            SiteSetting.objects.update_or_create(key="UPI_QR_FILE_NAME", defaults={"value": qr_file.name, "category": "PAYMENT"})
            SiteSetting.objects.update_or_create(key="UPI_QR_FILE_SIZE", defaults={"value": size_str, "category": "PAYMENT"})
            SiteSetting.objects.update_or_create(key="UPI_QR_UPLOADED_AT", defaults={"value": timezone.now().strftime("%Y-%m-%d %H:%M:%S"), "category": "PAYMENT"})
            updated_count += 1

        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action="UPDATE",
            model_name="SiteSetting",
            object_id="GLOBAL",
            details=f"Updated {updated_count} site configuration setting(s)"
        )
        messages.success(request, _("Site settings updated successfully!"))
        return redirect("/administration/site-settings/")

    return render(request, "administration/site_settings.html")


from django.utils.http import url_has_allowed_host_and_scheme

def switch_year_view(request, year_id=0):
    """Switch active/viewing financial year term for current session."""
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/dashboard/"
    if not url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={request.get_host()}):
        next_url = "/dashboard/"
    
    if year_id == 0:
        request.session.pop("active_year_id", None)
        messages.info(request, _("Switched back to active financial term."))
    else:
        fy = FinancialYear.objects.filter(id=year_id).first()
        if fy:
            request.session["active_year_id"] = fy.id
            if fy.is_locked:
                messages.warning(request, _("Switched to archived festival term '%(name)s' (READ-ONLY MODE).") % {"name": fy.name})
            else:
                messages.success(request, _("Active festival term set to '%(name)s'.") % {"name": fy.name})
    return redirect(next_url)

