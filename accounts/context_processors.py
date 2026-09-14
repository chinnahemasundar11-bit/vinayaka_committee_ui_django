from .permissions import get_user_role
from administration.models import AppModule, RolePermission, LookupValue


def user_permissions(request):
    """
    Context processor making active user role, permissions, dynamic sidebar menu, and profile details available globally across templates.
    """
    user = request.user
    if not user.is_authenticated:
        return {
            "user_role": "Guest",
            "user_display_name": "Guest User",
            "user_avatar_initials": "GU",
            "is_admin_user": False,
            "is_treasurer": False,
            "is_president_or_sec": False,
            "can_manage_finance": False,
            "can_manage_admin": False,
            "can_manage_members": False,
            "can_manage_events": False,
            "can_approve_expense": False,
            "sidebar_modules_tree": [],
        }

    role = get_user_role(user)
    is_admin = user.is_superuser or (role == "Super Admin")

    treasurer_roles = ["Super Admin", "Chief Treasurer", "Treasurer", "Joint Treasurer"]
    leader_roles = ["Super Admin", "President", "Vice President", "Secretary", "Joint Secretary"]
    event_roles = ["Super Admin", "President", "Secretary", "Event Coordinator"]

    is_treasurer = is_admin or (role in treasurer_roles)
    is_leader = is_admin or (role in leader_roles)
    is_event_mgr = is_admin or (role in event_roles)

    display_name = user.get_full_name().strip() or user.username
    parts = display_name.split()
    if len(parts) >= 2:
        initials = (parts[0][0] + parts[1][0]).upper()
    elif parts:
        initials = parts[0][:2].upper()
    else:
        initials = "VC"

    # Build Dynamic Sidebar Modules Navigation Tree
    all_modules = AppModule.objects.filter(is_active=True).order_by("display_order", "name")
    accessible_module_ids = set()

    if is_admin:
        accessible_module_ids = set(all_modules.values_list("id", flat=True))
    else:
        role_obj = LookupValue.objects.filter(lookup_type__code="SYSTEM_ROLE", value=role).first()
        if role_obj:
            allowed_perms = RolePermission.objects.filter(role=role_obj).exclude(assigned_rights=[])
            accessible_module_ids = set(allowed_perms.values_list("module_id", flat=True))

    parent_modules = [m for m in all_modules if m.parent_id is None]
    sidebar_modules_tree = []

    for parent in parent_modules:
        children = [m for m in all_modules if m.parent_id == parent.id and m.id in accessible_module_ids]
        
        # Parent is included if parent itself is directly accessible (non-# url) or has accessible children
        if (parent.url != "#" and parent.id in accessible_module_ids) or children:
            sidebar_modules_tree.append({
                "module": parent,
                "is_accessible": parent.id in accessible_module_ids,
                "children": children,
            })

    return {
        "user_role": role,
        "user_display_name": display_name,
        "user_avatar_initials": initials,
        "is_admin_user": is_admin,
        "is_treasurer": is_treasurer,
        "is_president_or_sec": is_leader,
        "can_manage_finance": is_admin or is_treasurer,
        "can_manage_admin": is_admin,
        "can_manage_members": is_admin or is_leader,
        "can_manage_events": is_admin or is_event_mgr,
        "can_approve_expense": is_admin or is_leader or is_treasurer,
        "sidebar_modules_tree": sidebar_modules_tree,
    }

