from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext as _
from members.models import Member


def get_user_role(user):
    """
    Evaluates the system access role for a given User object.
    Returns string role name.
    """
    if not user or not user.is_authenticated:
        return "Guest"

    if user.is_superuser:
        return "Super Admin"

    # Search for matching Member profile by mobile number or username
    try:
        member = Member.objects.filter(mobile_number=user.username, is_deleted=False).first()
        if member and member.system_role:
            return member.system_role
    except Exception:
        pass

    if user.is_staff:
        return "Super Admin"

    return "Committee Member"


def login_required_custom(view_func):
    """Decorator ensuring user is authenticated before accessing the view."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, _("Please sign in to access this page."))
            return redirect("/accounts/login/?next=" + request.path)
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def role_required(allowed_roles):
    """
    Decorator requiring the user to have one of the specified allowed system roles.
    allowed_roles can be a list or tuple of role strings.
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, _("Please sign in to access this page."))
                return redirect("/accounts/login/?next=" + request.path)

            current_role = get_user_role(request.user)

            # Super Admin bypasses all role restrictions
            if request.user.is_superuser or current_role == "Super Admin":
                return view_func(request, *args, **kwargs)

            if current_role in allowed_roles:
                return view_func(request, *args, **kwargs)

            messages.error(
                request,
                _("Access Denied: You do not have permission to perform this action (Role Required: %(roles)s).")
                % {"roles": ", ".join(allowed_roles)}
            )
            return redirect("/dashboard/")
        return _wrapped_view
    return decorator


# Convenient shortcut decorators
admin_required = role_required(["Super Admin"])
treasurer_required = role_required(["Super Admin", "Chief Treasurer", "Treasurer", "Joint Treasurer"])
leader_required = role_required(["Super Admin", "President", "Vice President", "Secretary", "Joint Secretary"])


def has_module_action_right(user, module_code, right_code):
    """
    Evaluates whether the given user has the specified action right (add, edit, delete_single, delete_bulk, print_single, print_bulk)
    for a given module code. Super Admin users always return True.
    """
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    role_name = get_user_role(user)
    if role_name == "Super Admin":
        return True

    from administration.models import RolePermission, LookupValue
    role_obj = LookupValue.objects.filter(lookup_type__code="SYSTEM_ROLE", value=role_name).first()
    if not role_obj:
        return False

    perm = RolePermission.objects.filter(role=role_obj, module__code=module_code).first()
    if not perm:
        return False

    return right_code in (perm.assigned_rights or [])


def module_right_required(module_code, right_code):
    """
    Decorator requiring the user to have the specific module action right.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, _("Please sign in to access this page."))
                return redirect("/accounts/login/?next=" + request.path)

            if has_module_action_right(request.user, module_code, right_code):
                return view_func(request, *args, **kwargs)

            messages.error(
                request,
                _("Access Denied: You do not have right '%(right)s' for module '%(mod)s'.")
                % {"right": right_code, "mod": module_code}
            )
            return redirect("/dashboard/")
        return _wrapped_view
    return decorator

