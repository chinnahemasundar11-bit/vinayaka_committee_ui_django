import datetime
from django.shortcuts import render
from django.db.models import Sum, Count, Avg
from funds.models import FundReceipt
from expenses.models import ExpenseVoucher
from events.models import Event
from administration.models import SiteSetting, FinancialYear
from accounts.permissions import login_required_custom


def get_site_setting(key, default=""):
    obj = SiteSetting.objects.filter(key=key).first()
    return obj.value if obj else default


@login_required_custom
def expense_predictor_view(request):
    """
    AI-Powered Festival Expense Predictor & Budget Velocity Analytics Engine.
    Analyses donation trend velocity, forecasts final revenue, and compares against projected event costs.
    """
    total_income = float(FundReceipt.objects.aggregate(Sum("amount"))["amount__sum"] or 0)
    total_expenses = float(ExpenseVoucher.objects.filter(status="APPROVED").aggregate(Sum("amount_spent"))["amount_spent__sum"] or 0)
    pending_expenses = float(ExpenseVoucher.objects.filter(status="PENDING").aggregate(Sum("amount_spent"))["amount_spent__sum"] or 0)

    total_event_budget = float(Event.objects.aggregate(Sum("allocated_budget"))["allocated_budget__sum"] or 0)
    total_receipts_count = FundReceipt.objects.count()

    # Calculate average daily collection velocity over recent active days
    receipt_dates = FundReceipt.objects.values("date_received").annotate(daily_total=Sum("amount")).order_by("date_received")
    active_days_count = max(receipt_dates.count(), 1)
    
    avg_daily_collection = total_income / active_days_count if active_days_count > 0 else 0
    
    # AI Forecast: Assuming 10 festival celebration days
    projected_final_income = total_income + (avg_daily_collection * 3) # Project next 3 peak festival days
    projected_total_outflow = total_expenses + pending_expenses + (total_event_budget * 0.2) # Add 20% contingency
    projected_net_surplus = projected_final_income - projected_total_outflow

    # AI Recommendation rules
    if projected_net_surplus >= 0:
        ai_health_status = "HEALTHY_SURPLUS"
        ai_recommendation = f"Festival fund trajectory is strong! Projected surplus of {get_site_setting('CURRENCY_SYMBOL', '₹')} {projected_net_surplus:,.2f}. Safe to proceed with scheduled cultural events."
    else:
        ai_health_status = "DEFICIT_WARNING"
        ai_recommendation = f"Budget deficit warning detected! Projected shortfall of {get_site_setting('CURRENCY_SYMBOL', '₹')} {abs(projected_net_surplus):,.2f}. Recommend capping un-approved vendor expenses or launching a special youth donor drive."

    currency = get_site_setting("CURRENCY_SYMBOL", "₹")

    context = {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "pending_expenses": pending_expenses,
        "total_event_budget": total_event_budget,
        "total_receipts_count": total_receipts_count,
        "active_days_count": active_days_count,
        "avg_daily_collection": avg_daily_collection,
        "projected_final_income": projected_final_income,
        "projected_total_outflow": projected_total_outflow,
        "projected_net_surplus": projected_net_surplus,
        "ai_health_status": ai_health_status,
        "ai_recommendation": ai_recommendation,
        "currency": currency,
    }
    return render(request, "administration/expense_predictor.html", context)
