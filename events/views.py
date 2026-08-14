from django.shortcuts import render

def index(request):
    return render(request, "events/event_list.html")

def add(request):
    return render(request, "events/event_form.html")
