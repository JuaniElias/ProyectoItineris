from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from itineris.forms import AddVehicle, AddDriver
from itineris.models import CompanyProfile, Vehicle


# Create your views here.
def index(request):
    return render(request, "itineris/index.html")


def work_with_us(request):
    return render(request, "itineris/work-with-us.html")


def about(request):
    return render(request, "itineris/about_us.html")


def create_travel(request):
    return render(request, "itineris/create_travel.html")


def pre_checkout(request):
    return render(request, "itineris/pre-checkout.html")


def travel_result(request):
    return render(request, "itineris/travel_result.html")


def your_drivers(request):
    user_id = request.user.id
    company = get_object_or_404(CompanyProfile, user_id=user_id)

    if request.method == "POST":
        form = AddDriver(request.POST)
        if form.is_valid():
            new_driver = form.save(commit=False)
            new_driver.company_id = company.id
            new_driver.save()
            return redirect('your_drivers')
    else:
        form = AddDriver()

    return render(request, "itineris/your_drivers.html", {
        'form': form,
    })


def your_payments(request):
    return render(request, "itineris/your_payments.html")


def your_travels(request):
    return render(request, "itineris/your_travels.html")


def your_vehicles(request):
    user_id = request.user.id
    company = get_object_or_404(CompanyProfile, user_id=user_id)

    if request.method == "POST":
        form = AddVehicle(request.POST)
        if form.is_valid():
            new_vehicle = form.save(commit=False)
            new_vehicle.company_id = company.id
            new_vehicle.save()
            return redirect('your_vehicles')
    else:
        form = AddVehicle()

    return render(request, "itineris/your_vehicles.html", {
        'form': form,
    })


def delete_vehicle(request, plate_number):
    vehicle = get_object_or_404(Vehicle, plate_number=plate_number)
    vehicle.delete()
    return redirect('your_vehicles')  # Redirect to the view displaying the table


def navbar(request):
    return render(request, "itineris/navbar.html")
