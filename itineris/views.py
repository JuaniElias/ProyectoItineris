from datetime import datetime

import mercadopago
from django.contrib import messages
from django.db.models import Model
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from ProyectoItineris import settings
from itineris.forms import CreateVehicle, CreateDriver, CreateTravel, SearchTravel, PreCheckout
from itineris.models import Company, Vehicle, Driver, Travel, Traveler
from utils.utils import send_email


def index(request):
    request.session['travelers'] = []
    if request.method == "POST":
        form = SearchTravel(request.POST)
        if form.is_valid():
            city_origin = form.cleaned_data['city_origin']
            city_destination = form.cleaned_data['city_destination']
            date_departure = form.cleaned_data['datetime_departure']
            passengers = form.cleaned_data['passengers']

            request.session['passengers'] = passengers

            # Buscar viajes que coincidan con los criterios
            travels = Travel.objects.all().filter(city_origin=city_origin,
                                                  city_destination=city_destination,
                                                  datetime_departure__date=date_departure,
                                                  seats_left__gte=passengers,
                                                  status="Agendado"
                                                  )

            return render(request, 'itineris/travel_result.html', {'travels': travels, 'passengers': passengers})
    else:
        form = SearchTravel()

    if request.user.is_authenticated:
        return render(request, "itineris/your_travels.html")
    else:
        return render(request, "itineris/index.html", {'form': form})


def work_with_us(request):
    return render(request, "itineris/work_with_us.html")


def about(request):
    return render(request, "itineris/about_us.html")


def create_travel(request):
    company_id = request.user.id
    company = get_object_or_404(Company, id=company_id)

    if request.method == "POST":
        form = CreateTravel(company.id, request.POST)
        if form.is_valid():
            if company.is_verified:
                new_travel = form.save(commit=False)
                new_travel.company_id = company.id
                new_travel.duration = new_travel.estimated_datetime_arrival - new_travel.datetime_departure
                new_travel.save()
                return redirect('create_travel')
            else:
                messages.success(request, 'No se puede crear el viaje, la compañía no está verificada.')

    else:
        form = CreateTravel(company.id)

    return render(request, "itineris/create_travel.html", {
        'form': form,
    })


def get_available_options(request):
    if request.GET.get("salida") and request.GET.get("llegada"):
        vehicle_departure = datetime.strptime(request.GET.get("salida"), '%Y-%m-%dT%H:%M').astimezone()
        vehicle_arrival = datetime.strptime(request.GET.get("llegada"), '%Y-%m-%dT%H:%M').astimezone()

        vehicle_exclude = []
        driver_exclude = []

        scheduled_travels = Travel.objects.filter(company_id=request.user.id, status='Agendado')

        available_vehicles = Vehicle.objects.filter(company_id=request.user.id, status='Disponible')
        available_drivers = Driver.objects.filter(company_id=request.user.id)

        for travel in scheduled_travels:
            if (vehicle_departure <= travel.estimated_datetime_arrival.astimezone() and
                    travel.datetime_departure.astimezone() <= vehicle_arrival):
                vehicle_exclude.append(travel.vehicle.plate_number)
                driver_exclude.append(travel.driver.driver_id)

        available_vehicles = available_vehicles.exclude(plate_number__in=vehicle_exclude)
        available_drivers = available_drivers.exclude(pk__in=driver_exclude)
        data = {
            'drivers': list(available_drivers.values('driver_id', 'first_name', 'last_name', 'license_number')),
            'vehicles': list(available_vehicles.values('plate_number', 'brand', 'car_model', ))
        }
        return JsonResponse(data)
    return JsonResponse({'message': 'Not found'})


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
    drivers = Driver.objects.filter(company_id=request.user.id, active=True)

    if request.method == "POST":
        form = CreateDriver(request.POST)
        if form.is_valid():
            if company.is_verified:
                new_driver = form.save(commit=False)
                new_driver.company_id = request.user.id
                new_driver.save()
                return redirect('your_drivers')
            else:
                messages.success(request, 'No se puede cargar el conductor, la compañía no está verificada.')
    else:
        form = CreateDriver()

    return render(request, "itineris/your_drivers.html", {
        'form': form,
        'drivers': drivers
    })


def delete_driver(request, driver_id):
    driver = get_object_or_404(Driver, driver_id=driver_id)
    driver.active = False
    driver.save()
    return redirect('your_drivers')


def your_travels(request):
    travels = Travel.objects.filter(company_id=request.user.id, status='Agendado')
    return render(request, "itineris/your_travels.html", {'travels': travels, })


def travel_history(request):
    travels = Travel.objects.filter(company_id=request.user.id)
    vehicles = Vehicle.objects.filter(company_id=request.user.id)
    drivers = Driver.objects.filter(company_id=request.user.id)
    return render(request, "itineris/travel_history.html",
                  {'travels': travels, 'vehicles': vehicles, 'drivers': drivers})


def delete_travel(request, travel_id):
    travel = get_object_or_404(Travel, travel_id=travel_id)
    travel.status = 'Cancelado'
    travel.save()
    return redirect('your_travels')


def your_vehicles(request):
    company_id = request.user.id
    company = get_object_or_404(Company, id=company_id)
    vehicles = Vehicle.objects.filter(company_id=request.user.id, active=True)

    if request.method == "POST":
        form = CreateVehicle(request.POST)
        if form.is_valid():
            if company.is_verified:
                new_vehicle = form.save(commit=False)
                new_vehicle.company_id = request.user.id
                new_vehicle.save()
                return redirect('your_vehicles')
            else:
                messages.error(request, "No se puede cargar el vehículo, la compañía no está verificada.")
    else:
        form = CreateVehicle()

    return render(request, "itineris/your_vehicles.html", {
        'form': form,
        'vehicles': vehicles
    })


def delete_vehicle(request, plate_number):
    vehicle = get_object_or_404(Vehicle, plate_number=plate_number)
    vehicle.active = False
    vehicle.save()
    return redirect('your_vehicles')


def pre_checkout(request):
    travel = get_object_or_404(Travel, travel_id=request.session.get('travel_id'))
    passenger_count = int(request.session.get('passengers'))

    # Inicializa la lista con los ID de los pasajeros
    travelers = request.session.get('travelers', [])

    if len(travelers) < passenger_count:
        if request.method == "POST":
            form = PreCheckout(request.POST)
            if form.is_valid():
                new_traveler = form.save(commit=False)
                new_traveler.travel = travel
                new_traveler.save()
                travelers.append(new_traveler.id)
                request.session['travelers'] = travelers  # This ain't the way

                return redirect('pre_checkout')
        else:
            form = PreCheckout()
    else:
        return redirect('checkout')
    return render(request, "itineris/pre_checkout.html",
                  {'travel': travel, 'passengers': passenger_count, 'form': form})


def save_travel_id(request, travel_id):
    request.session['travel_id'] = travel_id

    return redirect('pre_checkout')


def checkout(request):
    travelers = request.session.get('travelers')
    request.session['travelers'] = []
    if not travelers:
        return HttpResponseBadRequest("No se han creado viajeros.")
    travelers_obj = Traveler.objects.filter(id__in=travelers)

    checkout_url = request.build_absolute_uri(reverse('checkout'))
    payment_success_url = request.build_absolute_uri(reverse('payment_success'))

    travel = get_object_or_404(Travel, travel_id=request.session.get('travel_id'))
    sdk = mercadopago.SDK('APP_USR-4911057100331416-060418-a5d1090130a913b3533f686a2c7f5c20-1831872037')
    preference_data = {
        "items": [
            {
                "title": "Pasaje: Itineris",
                "unit_price": travel.fee,
                "quantity": travelers_obj.count()
            }
        ],
        "purpose": "onboarding_credits",
        "statement_descriptor": "Itineris",
        "back_urls": {
            "success": payment_success_url,
            "failure": checkout_url,
        },
    }

    preference_response = sdk.preference().create(preference_data)
    preference_id = preference_response["response"]["id"]

    return render(request, "itineris/checkout.html",
                  {'travelers': travelers_obj, 'preference_id': preference_id})


@csrf_exempt
def payment_success(request):
    payment_status = request.GET.get("status", None)
    print(payment_status)
    if payment_status == 'approved':
        payment_id = request.GET.get("payment_id", None)

        sdk = mercadopago.SDK("APP_USR-4911057100331416-060418-a5d1090130a913b3533f686a2c7f5c20-1831872037")
        payment_info = sdk.payment().get(payment_id)

        status = payment_info["response"]["status"]

        # Por las dudas chequeamos que el pago fue aprobado nuevamente
        if status == 'approved':
            traveler_ids = request.session.get('travelers')
            travelers = Traveler.objects.filter(id__in=traveler_ids)
            for traveler in travelers:
                traveler.status = 'Confirmado'

                to_email = traveler.email
                subject = f'Pasaje Itineris - {traveler.travel.city_origin} a {traveler.travel.city_destination}'
                message = (f'¡Te brindamos los datos de tu pasaje!\n'
                           f'Información de tu pasaje:\n'
                           f'Origen: {traveler.address_origin}, {traveler.travel.city_origin}\n'
                           f'Destino: {traveler.address_destination}, {traveler.travel.city_destination}\n'
                           f'Fecha de salida: {traveler.travel.datetime_departure}\n'
                           f'Fecha estimada de llegada: {traveler.travel.estimated_datetime_arrival}\n'
                           f'Tarifa: {traveler.travel.fee}\n')

                try:
                    send_email(to_email, subject, message, file=None)
                    messages.success(request,
                                     'Email enviado correctamente.')
                except Exception as e:
                    messages.error(request, f'Error al enviar el correo de verificación: {str(e)}')
                traveler.save()

            travel = get_object_or_404(Travel, travel_id=request.session.get('travel_id'))
            travel.seats_left -= travelers.count()
            travel.save()

            return redirect('payment_success')
        else:
            return redirect('checkout')

    return render(request, "itineris/payment_success.html")
