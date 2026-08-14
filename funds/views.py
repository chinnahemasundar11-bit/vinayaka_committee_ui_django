from django.shortcuts import render

def index(request):
    return render(request, "funds/fund_list.html")

def add(request):
    return render(request, "funds/fund_form.html")
