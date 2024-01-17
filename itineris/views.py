from django.shortcuts import render
from django.http import HttpResponse


# Create your views here.
def index(request):
    return render(request, "itineris/index.html")


def work_with_us(request):
    return render(request, "itineris/work-with-us.html")


def login(request):
    return render(request, "itineris/login.html")


def sign_in(request):
    return render(request, "itineris/sign-in.html")
