from django.shortcuts import render, get_object_or_404, redirect
from itineris.forms import AddVehicle, AddDriver, AddTravel
from itineris.models import CompanyProfile, Vehicle, Driver, Travel


# Create your views here.
def index(request):
    return render(request, "itineris/index.html")


def work_with_us(request):
    return render(request, "itineris/work-with-us.html")


def about(request):
    return render(request, "itineris/about_us.html")


def create_travel(request):
    user_id = request.user.id
    company = get_object_or_404(CompanyProfile, user_id=user_id)

    if request.method == "POST":
        form = AddTravel(company.id, request.POST)
        if form.is_valid():
            new_travel = form.save(commit=False)
            new_travel.company_id = company.id
            new_travel.duration = new_travel.estimated_datetime_arrival - new_travel.datetime_departure
            new_travel.save()
            return redirect('create_travel')
    else:
        form = AddTravel(company.id)

    return render(request, "itineris/create_travel.html", {
        'form': form,
    })


def pre_checkout(request):
    return render(request, "itineris/pre-checkout.html")


def travel_result(request):
    travels = Travel.objects.all()

    return render(request, "itineris/travel_result.html", {'travels': travels})


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


def delete_driver(request, driver_id):
    driver = get_object_or_404(Driver, driver_id=driver_id)
    driver.delete()
    return redirect('your_drivers')  # Redirect to the view displaying the table


def your_payments(request):
    return render(request, "itineris/your_payments.html")


def your_travels(request):
    return render(request, "itineris/your_travels.html")


def delete_travel(request, travel_id):
    travel = get_object_or_404(Travel, travel_id=travel_id)
    travel.delete()
    return redirect('your_travels')  # Redirect to the view displaying the table


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
