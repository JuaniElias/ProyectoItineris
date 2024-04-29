from datetime import datetime

from django.http import HttpResponseBadRequest, JsonResponse
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

    if request.user.is_authenticated:
        return render(request, "itineris/your_travels.html")
    else:
        return render(request, "itineris/index.html", {'form': form})


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


def get_available_drivers(request):
    vehicle_departure = datetime.strptime(request.GET.get("salida"), '%Y-%m-%dT%H:%M').astimezone()
    vehicle_arrival = datetime.strptime(request.GET.get("llegada"), '%Y-%m-%dT%H:%M').astimezone()

    vehicle_exclude = []
    driver_exclude = []

    scheduled_travels = Travel.objects.filter(company_id=request.user.id, status='Agendado')

    for travel in scheduled_travels:
        if (vehicle_departure <= travel.estimated_datetime_arrival.astimezone()
                and travel.datetime_departure.astimezone() <= vehicle_arrival):
            vehicle_exclude.append(travel.vehicle_id)
            driver_exclude.append(travel.driver_id)

    # vehicles logic
    available_vehicles = Vehicle.objects.filter(company_id=request.user.id, status='Disponible')
    available_vehicles = available_vehicles.exclude(plate_number__in=vehicle_exclude)

    # drivers logic
    available_drivers = Driver.objects.filter(company_id=request.user.id)
    available_drivers = available_drivers.exclude(driver_id__in=driver_exclude)

    data_vehicles = [{'vehicle_id': vehicle.plate_number} for vehicle in available_vehicles]
    data_drivers = [{'driver_id': driver.driver_id} for driver in available_drivers]

    data = {'drivers': data_drivers, 'vehicles': data_vehicles}

    return JsonResponse(data, safe=False)


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


def travel_detail(request, travel_id):
    travel = get_object_or_404(Travel, travel_id=travel_id)
    travelers = Traveler.objects.filter(travel_id=travel_id)
    return render(request, "itineris/travel_detail.html", {'travel': travel, 'travelers': travelers})


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
    travels = Travel.objects.filter(company_id=request.user.id, status='Agendado')
    return render(request, "itineris/your_travels.html", {'travels': travels, })


def delete_travel(request, travel_id):
    travel = get_object_or_404(Travel, travel_id=travel_id)
    travel.status = 'Cancelado'
    travel.save()
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
