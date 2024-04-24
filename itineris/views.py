from django.http import HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404, redirect
from itineris.forms import AddVehicle, AddDriver, AddTravel, SearchTravel, PreCheckout
from itineris.models import Company, Vehicle, Driver, Travel, Traveler


# Create your views here.
def index(request):
    if request.method == "POST":
        form = SearchTravel(request.POST)
        if form.is_valid():
            city_origin = form.cleaned_data['city_origin']
            city_destination = form.cleaned_data['city_destination']
            date_departure = form.cleaned_data['datetime_departure']
            passengers = form.cleaned_data['passengers']

            # Buscar vuelos que coincidan con los criterios
            travels = Travel.objects.all().filter(city_origin=city_origin,
                                                  city_destination=city_destination,
                                                  datetime_departure__date=date_departure,
                                                  seats_left__gte=passengers,
                                                  )

            return render(request, 'itineris/travel_result.html', {'travels': travels, 'passengers': passengers})
    else:
        form = SearchTravel()
    return render(request, 'itineris/index.html', {'form': form})


def work_with_us(request):
    return render(request, "itineris/work-with-us.html")


def about(request):
    return render(request, "itineris/about_us.html")


def create_travel(request):
    company_id = request.user.id
    company = get_object_or_404(Company, id=company_id)

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


def pre_checkout(request, travel_id, passengers):
    travel = get_object_or_404(Travel, travel_id=travel_id)
    passenger_count = int(passengers)

    travelers = request.session.get('travelers', [])

    if request.method == "POST":
        form = PreCheckout(request.POST)
        if form.is_valid():
            new_traveler = form.save(commit=False)
            new_traveler.travel = travel
            new_traveler.save()
            travelers.append(new_traveler.id)
            request.session['travelers'] = travelers
            passenger_count -= 1
            if passenger_count > 0:
                return redirect('pre_checkout', travel_id=travel_id, passengers=passenger_count)
            else:
                return redirect('checkout')
    else:
        form = PreCheckout()
    return render(request, "itineris/pre-checkout.html",
                  {'travel': travel, 'passengers': passenger_count, 'form': form})


def travel_result(request):
    travels = Travel.objects.all()

    return render(request, "itineris/travel_result.html", {'travels': travels})


def your_drivers(request):
    company_id = request.user.id
    company = get_object_or_404(Company, id=company_id)

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
    company_id = request.user.id
    company = get_object_or_404(Company, id=company_id)

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


def checkout(request):
    travelers = request.session.get('travelers')
    if not travelers:
        return HttpResponseBadRequest("No se han creado viajeros.")
    travelers_obj = Traveler.objects.filter(id__in=travelers)
    return render(request, "itineris/checkout.html", {'travelers': travelers_obj})
