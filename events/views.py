from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Q
from .models import Event
from administration.models import LookupType, LookupValue
from audit.models import AuditLog
import datetime


from accounts.permissions import (
    login_required_custom, get_user_role, has_module_action_right,
    module_access_required, module_right_required
)


@module_access_required("EVENTS")
def event_list(request):
    """List, search, create, update, and delete festival events."""
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create" and not has_module_action_right(request.user, "EVENTS", "add"):
            messages.error(request, "Access Denied: You do not have permission to add festival events.")
            return redirect("/events/")
        elif action in ["update", "edit"] and not has_module_action_right(request.user, "EVENTS", "edit"):
            messages.error(request, "Access Denied: You do not have permission to edit festival events.")
            return redirect("/events/")
        elif action == "delete" and not has_module_action_right(request.user, "EVENTS", "delete_single"):
            messages.error(request, "Access Denied: You do not have permission to delete festival events.")
            return redirect("/events/")
        elif action == "bulk_delete" and not has_module_action_right(request.user, "EVENTS", "delete_bulk"):
            messages.error(request, "Access Denied: You do not have permission to bulk delete festival events.")
            return redirect("/events/")


        if action == "create":
            e_id = request.POST.get("event_id", "").strip() or f"EVT-2026-{Event.objects.count() + 1:03d}"
            title = request.POST.get("title", "").strip()
            venue = request.POST.get("venue_location", "").strip()
            date = request.POST.get("event_date") or datetime.date.today().isoformat()
            budget = request.POST.get("allocated_budget", 0)
            spend = request.POST.get("actual_spend", 0)
            status = request.POST.get("status", "Planned")
            description = request.POST.get("description", "").strip()

            if title and venue and date and budget:
                event = Event.objects.create(
                    event_id=e_id,
                    title=title,
                    venue_location=venue,
                    event_date=date,
                    allocated_budget=budget,
                    actual_spend=spend,
                    status=status,
                    description=description
                )
                user = request.user if request.user.is_authenticated else None
                AuditLog.objects.create(user=user, action="CREATE", model_name="Event", object_id=str(event.id), details=f"Created event {title} ({e_id})")
                messages.success(request, f"Event '{title}' scheduled successfully!")
            else:
                messages.error(request, "* Please fill all mandatory fields.")

        elif action == "update":
            e_db_id = request.POST.get("event_db_id")
            event = get_object_or_404(Event, id=e_db_id)
            event.title = request.POST.get("title", event.title)
            event.venue_location = request.POST.get("venue_location", event.venue_location)
            event.event_date = request.POST.get("event_date", event.event_date)
            event.allocated_budget = request.POST.get("allocated_budget", event.allocated_budget)
            event.actual_spend = request.POST.get("actual_spend", event.actual_spend)
            event.status = request.POST.get("status", event.status)
            event.description = request.POST.get("description", event.description)
            event.save()

            user = request.user if request.user.is_authenticated else None
            AuditLog.objects.create(user=user, action="UPDATE", model_name="Event", object_id=str(event.id), details=f"Updated event {event.title}")
            messages.success(request, f"Event '{event.title}' updated successfully!")

        elif action == "delete":
            e_db_id = request.POST.get("event_db_id")
            event = get_object_or_404(Event, id=e_db_id)
            title = event.title
            event.delete()
            user = request.user if request.user.is_authenticated else None
            AuditLog.objects.create(user=user, action="DELETE", model_name="Event", object_id=str(e_db_id), details=f"Deleted event {title}")
            messages.success(request, f"Event '{title}' deleted successfully.")

        elif action == "bulk_delete":
            selected_ids = request.POST.getlist("selected_ids[]") or request.POST.getlist("selected_ids")
            if selected_ids:
                events_qs = Event.objects.filter(id__in=selected_ids)
                count = events_qs.count()
                for e in events_qs:
                    e.delete()
                user = request.user if request.user.is_authenticated else None
                AuditLog.objects.create(user=user, action="BULK_DELETE", model_name="Event", object_id=str(selected_ids), details=f"Bulk deleted {count} events")
                messages.success(request, f"Successfully deleted {count} selected events.")

        return redirect("/events/")

    search_query = request.GET.get("q", "").strip()
    events_qs = Event.objects.all()
    if search_query:
        events_qs = events_qs.filter(
            Q(event_id__icontains=search_query) |
            Q(title__icontains=search_query) |
            Q(venue_location__icontains=search_query)
        )

    total_budget = events_qs.aggregate(Sum("allocated_budget"))["allocated_budget__sum"] or 0
    total_spend = events_qs.aggregate(Sum("actual_spend"))["actual_spend__sum"] or 0

    try:
        per_page = int(request.GET.get("per_page", 10))
        if per_page not in [10, 50, 100, 500]: per_page = 10
    except (ValueError, TypeError):
        per_page = 10

    from django.core.paginator import Paginator
    paginator = Paginator(events_qs, per_page)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "events": page_obj,
        "page_obj": page_obj,
        "per_page": per_page,
        "total_budget": total_budget,
        "total_spend": total_spend,
        "search_query": search_query,
    }
    return render(request, "events/event_list.html", context)


@module_right_required("EVENTS", "add")
def event_add(request):
    """Dedicated Add Event View."""
    if request.method == "POST":
        return event_list(request)

    next_event_id = f"EVT-2026-{Event.objects.count() + 1:03d}"
    today_date = datetime.date.today().isoformat()

    context = {
        "next_event_id": next_event_id,
        "today_date": today_date,
    }
    return render(request, "events/event_form.html", context)
