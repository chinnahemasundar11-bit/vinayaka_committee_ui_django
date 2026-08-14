from django.shortcuts import render

def index(request):
    return render(request, "members/member_list.html")

def add(request):
    return render(request, "members/member_form.html")
