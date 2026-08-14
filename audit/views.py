from django.shortcuts import render

def index(request):
    return render(request, "audit/audit_logs.html")
