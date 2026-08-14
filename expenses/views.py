from django.shortcuts import render

def index(request):
    return render(request, "expenses/expense_list.html")

def add(request):
    return render(request, "expenses/expense_form.html")
