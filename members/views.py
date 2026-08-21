from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from .models import Member
from administration.models import LookupType, LookupValue
from audit.models import AuditLog
import datetime


def member_list(request):
    """List, search, create, update, and delete committee members."""
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create":
            m_id = request.POST.get("member_id", "").strip() or f"MBR-2026-{Member.objects.count() + 1:03d}"
            name = request.POST.get("full_name", "").strip()
            mobile = request.POST.get("mobile_number", "").strip()
            position = request.POST.get("committee_position", "").strip()
            sys_role = request.POST.get("system_role", "Committee Member").strip()
            joining = request.POST.get("joining_date") or datetime.date.today().isoformat()
            status = request.POST.get("status", "Active")
            address = request.POST.get("address", "").strip()

            if name and mobile and position:
                member = Member.objects.create(
                    member_id=m_id,
                    full_name=name,
                    mobile_number=mobile,
                    committee_position=position,
                    system_role=sys_role,
                    joining_date=joining,
                    status=status,
                    address=address
                )
                user = request.user if request.user.is_authenticated else None
                AuditLog.objects.create(user=user, action="CREATE", model_name="Member", object_id=str(member.id), details=f"Registered committee member {name} ({m_id})")
                messages.success(request, f"Member {name} ({m_id}) registered successfully!")
            else:
                messages.error(request, "* Please fill all mandatory fields.")

        elif action == "update":
            m_db_id = request.POST.get("member_db_id")
            member = get_object_or_404(Member, id=m_db_id)
            member.full_name = request.POST.get("full_name", member.full_name)
            member.mobile_number = request.POST.get("mobile_number", member.mobile_number)
            member.committee_position = request.POST.get("committee_position", member.committee_position)
            member.system_role = request.POST.get("system_role", member.system_role)
            member.joining_date = request.POST.get("joining_date", member.joining_date)
            member.status = request.POST.get("status", member.status)
            member.address = request.POST.get("address", member.address)
            member.save()

            user = request.user if request.user.is_authenticated else None
            AuditLog.objects.create(user=user, action="UPDATE", model_name="Member", object_id=str(member.id), details=f"Updated member record {member.full_name}")
            messages.success(request, f"Member record for {member.full_name} updated successfully!")

        elif action == "delete":
            m_db_id = request.POST.get("member_db_id")
            member = get_object_or_404(Member, id=m_db_id)
            name = member.full_name
            member.delete()
            user = request.user if request.user.is_authenticated else None
            AuditLog.objects.create(user=user, action="DELETE", model_name="Member", object_id=str(m_db_id), details=f"Deleted member {name}")
            messages.success(request, f"Member {name} deleted successfully.")

        elif action == "bulk_delete":
            selected_ids = request.POST.getlist("selected_ids[]") or request.POST.getlist("selected_ids")
            if selected_ids:
                members_qs = Member.objects.filter(id__in=selected_ids)
                count = members_qs.count()
                for m in members_qs:
                    m.delete()
                user = request.user if request.user.is_authenticated else None
                AuditLog.objects.create(user=user, action="BULK_DELETE", model_name="Member", object_id=str(selected_ids), details=f"Bulk deleted {count} members")
                messages.success(request, f"Successfully deleted {count} selected member records.")

        return redirect("/members/")

    search_query = request.GET.get("q", "").strip()
    members_qs = Member.objects.all()
    if search_query:
        members_qs = members_qs.filter(
            Q(member_id__icontains=search_query) |
            Q(full_name__icontains=search_query) |
            Q(mobile_number__icontains=search_query) |
            Q(committee_position__icontains=search_query)
        )

    # Dynamic Lookup options for Position & Role dropdowns
    pos_type = LookupType.objects.filter(code="MEMBER_POSITION").first()
    positions = LookupValue.objects.filter(lookup_type=pos_type, is_active=True) if pos_type else []

    role_type = LookupType.objects.filter(code="SYSTEM_ROLE").first()
    roles = LookupValue.objects.filter(lookup_type=role_type, is_active=True) if role_type else []

    context = {
        "members": members_qs,
        "positions": positions,
        "roles": roles,
        "search_query": search_query,
    }
    return render(request, "members/member_list.html", context)


def member_add(request):
    """Dedicated Add Committee Member View."""
    if request.method == "POST":
        return member_list(request)

    pos_type = LookupType.objects.filter(code="MEMBER_POSITION").first()
    positions = LookupValue.objects.filter(lookup_type=pos_type, is_active=True) if pos_type else []

    role_type = LookupType.objects.filter(code="SYSTEM_ROLE").first()
    roles = LookupValue.objects.filter(lookup_type=role_type, is_active=True) if role_type else []

    next_member_id = f"MBR-2026-{Member.objects.count() + 1:03d}"
    today_date = datetime.date.today().isoformat()

    context = {
        "positions": positions,
        "roles": roles,
        "next_member_id": next_member_id,
        "today_date": today_date,
    }
    return render(request, "members/member_form.html", context)
