from django.shortcuts import render

def index(request):
    return render(request, "administration/admin_home.html")

def users(request):
    return render(request, "administration/users.html")

def roles(request):
    return render(request, "administration/roles.html")

def payment_methods(request):
    return render(request, "administration/payment_methods.html")

def fund_sources(request):
    return render(request, "administration/fund_sources.html")

def expense_categories(request):
    return render(request, "administration/expense_categories.html")

def financial_years(request):
    return render(request, "administration/financial_years.html")
