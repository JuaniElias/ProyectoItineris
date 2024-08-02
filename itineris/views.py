from datetime import datetime, date

import mercadopago
import pandas as pd
from django.contrib import messages
from django.db.models import Model
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from ProyectoItineris import settings
from itineris.forms import CreateVehicle, CreateDriver, CreateTravel, SearchTravel, PreCheckout, PeriodTravel
from itineris.models import Company, Vehicle, Driver, Travel, Traveler
from utils.utils import send_email, calculate_full_route
from django.utils import timezone


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
            travels.order_by('datetime_departure')

            if not travels:
                maximum_date = date.today() + pd.Timedelta(days=60)
                travels = Travel.objects.all().filter(city_origin=city_origin,
                                                      city_destination=city_destination,
                                                      seats_left__gte=passengers,
                                                      datetime_departure__date__lte=maximum_date,
                                                      status="Agendado"
                                                      )
                travels.order_by('datetime_departure')
                if travels.count() > 10:
                    travels = travels[:10]
                messages.success(request, "No tenemos para el mismo dia que ingresaste")

            if not travels:
                travels = Travel.objects.all().filter(city_origin=city_origin,
                                                      seats_left__gte=passengers,
                                                      datetime_departure__date=date_departure,
                                                      status="Agendado"
                                                      )
                travels.order_by('datetime_departure')
                messages.success(request, "No tenemos para la ciudad que ingresaste")

            if not travels:
                redirect()

            return render(request, 'itineris/travel_result.html', {'travels': travels,
                                                                   'passengers': passengers})
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
        period_form = PeriodTravel(request.POST)

        toggle_checkbox = request.POST.get('period_checkbox')
        if form.is_valid():
            if company.is_verified:
                new_travel = form.save(commit=False)
                new_travel.company_id = company.id
                duration = new_travel.estimated_datetime_arrival - new_travel.datetime_departure
                new_travel.duration = new_travel.estimated_datetime_arrival - new_travel.datetime_departure

                if toggle_checkbox and period_form.is_valid():
                    start_date = (new_travel.datetime_departure + pd.Timedelta(days=1)).date()

                    period_ = period_form.save()

                    end_date = period_.end_date
                    if end_date is None:
                        end_date = start_date + pd.Timedelta(days=365)
                    period_.end_date = end_date

                    period_.save()

                    new_travel.period = period_

                    period_weekdays = [weekday.weekday_id for weekday in period_.weekdays.all()]

                    print(period_weekdays)

                    date_range = pd.date_range(start=start_date, end=end_date)

                    date_to_use = [date for date in date_range if date.weekday() + 1 in period_weekdays]

                    departure_time = new_travel.datetime_departure.time()
                    arrival_time = new_travel.estimated_datetime_arrival.time()

                    for date in date_to_use:
                        date_dep = pd.to_datetime(datetime.combine(date, departure_time))
                        date_arr = date_dep + duration

                        travel = Travel.objects.create(
                            company=company,
                            driver=new_travel.driver,
                            vehicle=new_travel.vehicle,
                            addr_origin=new_travel.addr_origin,
                            addr_origin_num=new_travel.addr_origin_num,
                            city_origin=new_travel.city_origin,
                            city_destination=new_travel.city_destination,
                            datetime_departure=timezone.make_aware(
                                date_dep,
                                timezone.get_current_timezone()
                            ),
                            estimated_datetime_arrival=timezone.make_aware(
                                date_arr,
                                timezone.get_current_timezone()
                            ),
                            duration=new_travel.duration,
                            fee=new_travel.fee,
                            payment_status="Pendiente",
                            status="Agendado",
                            period=period_,
                        )
                        travel.save()

                    new_travel.period = period_
                    new_travel.save()
                # TODO: Crear los viajes periódicos
                else:
                    messages.success(request,
                                     'Seleccione días de la semana a repetir el viaje.')

                return redirect('create_travel')
            else:
                messages.success(request, 'No se puede crear el viaje, la compañía no está verificada.')
    else:
        form = CreateTravel(company.id)
        period_form = PeriodTravel()

    return render(request, "itineris/create_travel.html", {
        'form': form,
        'period_form': period_form
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
    if driver.travel_set.filter(status='Agendado'):
        messages.success(request, "El chofer tiene viajes asignados. Edite los viajes antes de borrar el conductor.")
    else:
        driver.active = False
        driver.save()
    return redirect('your_drivers')


def your_travels(request):
    travels = Travel.objects.filter(company_id=request.user.id, status='Agendado')
    return render(request, "itineris/your_travels.html", {'travels': travels, })


def travel_history(request):
    travels = Travel.objects.filter(company_id=request.user.id)
    travels = travels.order_by('datetime_departure')
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
    if vehicle.travel_set.filter(status='Agendado'):
        messages.success(request, "El vehículo tiene viajes asignados. Edite los viajes antes de borrar el vehículo.")
    else:
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
    # request.session['travelers'] = []  # Limpia los travelers de la session cuando entra a checkout y no está muy bien
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
                           f'Origen: {traveler.addr_ori}, {traveler.addr_ori_num}, {traveler.travel.city_origin}\n'
                           f'Destino: {traveler.addr_dest}, {traveler.addr_dest_num}, {traveler.travel.city_destination}\n'
                           f'Fecha y hora de salida: {traveler.travel.datetime_departure}\n'
                           f'Fecha y hora estimada de llegada: {traveler.travel.estimated_datetime_arrival}\n'
                           f'Empresa: {traveler.travel.company.company_name}\n'
                           f'El vehículo que te pasa a buscar: {traveler.travel.vehicle}\n'
                           f'Chofer: {traveler.travel.driver}\n'
                           f'Tarifa: {traveler.travel.fee}\n')
                try:
                    send_email(to_email, subject, message, file=None)
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


def generate_route(request, travel_id):
    calculate_full_route(travel_id)
    return travel_detail(request, travel_id)
