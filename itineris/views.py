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


def about(request):
    return render(request, "itineris/about_us.html")


def create_travel(request):
    return render(request, "itineris/create_travel.html")


def pre_checkout(request):
    return render(request, "itineris/pre-checkout.html")


def sign_in_business(request):
    return render(request, "itineris/sign-in-business.html")


def travel_result(request):
    return render(request, "itineris/travel_result.html")


def your_drivers(request):
    return render(request, "itineris/your_drivers.html")


def your_payments(request):
    return render(request, "itineris/your_payments.html")


def your_travels(request):
    return render(request, "itineris/your_travels.html")


def your_vehicles(request):
    return render(request, "itineris/your_vehicles.html")
