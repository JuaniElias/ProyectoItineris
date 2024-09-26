import csv
import io
from datetime import datetime

import mercadopago
import pandas as pd
import pytz
from django.contrib import messages
from django.db.models import Sum
from django.forms import modelformset_factory
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from itineris.forms import (CreateVehicle, CreateDriver, CreateTravel, SearchTravel, CreateTraveler, PeriodTravel,
                            UpdateTraveler, UpdateTravel, CreateWaypoint, EditSegmentFormSet)
from itineris.models import Company, Vehicle, Driver, Travel, Traveler, Segment, Waypoint
from utils.utils import (send_email, decrypt_number, encryptedkey, encrypt_number, create_segments, search_segments,
                         cancel_travel)
from utils.maps import calculate_full_route

def index(request):
    request.session.clear()
    # request.session['travelers'] = []
    if request.method == "POST":
        form = SearchTravel(request.POST)
        if form.is_valid():
            city_origin = form.cleaned_data['city_origin']
            city_destination = form.cleaned_data['city_destination']
            date_departure = form.cleaned_data['datetime_departure']
            passengers_count = int(form.cleaned_data['passengers'])

            request.session['passengers_count'] = passengers_count

            segments = search_segments(city_origin, passengers_count)

            results = [segment for segment in segments
                       if ((segment.waypoint_destination.city == city_destination) and
                           (segment.waypoint_origin.estimated_datetime_arrival.date() == date_departure.date()))
                       ]

            if not results:
                msg_text = (f'No hemos encontrado viajes para la fecha ingresada, te dejamos una lista de viajes'
                            f' para otras fechas de salida.')

                results = [segment for segment in segments if segment.waypoint_destination.city == city_destination]

                if len(results) > 10:
                    results = results[:10]

                if not results:
                    msg_text = (f'No hemos encontrado viajes para la ciudad ingresada, te dejamos una lista de viajes '
                                f'a otras ciudades.')

                    results = [segment for segment in segments
                               if segment.waypoint_origin.estimated_datetime_arrival.date() == date_departure.date()
                               ]

                    if not results:
                        return redirect('travel_result_failed')

                messages.success(request, message=msg_text)

            return render(request, 'itineris/travel_result.html', {'segments': results})
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
    current_company_id = request.user.id
    company = get_object_or_404(Company, id=current_company_id)

    if request.method == "POST":
        form = CreateTravel(company.id, request.POST)
        period_form = PeriodTravel(request.POST)
        toggle_checkbox = request.POST.get('period_checkbox')

        if form.is_valid():
            if company.is_verified:
                new_travel = Travel.objects.create(company=company,
                                                   driver=form.cleaned_data['driver'],
                                                   vehicle=form.cleaned_data['vehicle'],
                                                   address=form.cleaned_data['address'],
                                                   geocode=form.cleaned_data['geocode'])

                if toggle_checkbox and period_form.is_valid():
                    period = period_form.save()

                    if period.end_date is None:
                        start_date = (pd.to_datetime(form.cleaned_data['datetime_departure']) + pd.Timedelta(
                            days=1)).date()
                        end_date = start_date + pd.Timedelta(days=365)
                        period.end_date = end_date
                        period.save()

                    new_travel.period = period
                    new_travel.save()

                Waypoint.objects.create(
                    travel=new_travel,
                    city=form.cleaned_data['city_origin'],
                    estimated_datetime_arrival=form.cleaned_data['datetime_departure'],
                    node_number=0
                )

                Waypoint.objects.create(
                    travel=new_travel,
                    city=form.cleaned_data['city_destination'],
                    estimated_datetime_arrival=form.cleaned_data['datetime_arrival'],
                    node_number=1
                )
                request.session['travel_id'] = new_travel.travel_id
                request.session['max_node_number'] = 1
                return redirect("show_waypoints")
            else:
                messages.success(request, 'No se puede crear el viaje, la compañía no está verificada.')
    else:
        form = CreateTravel(company.id)
        period_form = PeriodTravel()

    return render(request, "itineris/create_travel.html", {
        'form': form,
        'period_form': period_form,
    })


def show_waypoints(request):
    travel_id = request.session.get('travel_id')
    waypoints = Waypoint.objects.all().filter(travel_id=travel_id).order_by("estimated_datetime_arrival")
    all_but_last_waypoints = waypoints[:waypoints.count() - 1]
    last_waypoint = waypoints.last()

    form = CreateWaypoint()

    return render(request, "itineris/create_waypoints.html", {
        "all_but_last_waypoints": all_but_last_waypoints,
        "last_waypoint": last_waypoint,
        "form": form,
    })


def add_waypoint(request):
    travel_id = request.session.get('travel_id')

    if request.method == 'POST':
        form = CreateWaypoint(request.POST)
        if form.is_valid():
            new_waypoint = form.save(commit=False)
            new_waypoint.travel_id = travel_id
            new_waypoint.node_number = 0
            new_waypoint.save()

            return redirect('show_waypoints')
    else:
        form = CreateWaypoint()

    return render(request, "itineris/create_waypoints.html", {
        'form': form,
    })


def delete_waypoint(request, waypoint_id):
    waypoint = get_object_or_404(Waypoint, id=waypoint_id)
    waypoint.delete()
    return redirect('show_waypoints')


def generate_segments(request):
    travel_id = request.session.get('travel_id')
    travel = get_object_or_404(Travel, travel_id=travel_id)
    waypoints = Waypoint.objects.all().filter(travel_id=travel_id).order_by("estimated_datetime_arrival")

    if waypoints.none() or waypoints.count() < 2:
        messages.success(request, 'Debes ingresar al menos 2 ciudades.')
        return redirect('show_waypoints')

    i = 0
    for waypoint in waypoints:
        waypoint.node_number = i
        i += 1
        waypoint.save()

    create_segments(travel, waypoints)
    return redirect('show_segments')


def show_segments(request):
    if request.method == 'POST':
        formset = EditSegmentFormSet(request.POST)
        if formset.is_valid():
            formset.save()
            return redirect('end_travel_creation')
        else:
            print("Formset is not valid: ", formset.errors)
            print("Formset data:", request.POST)
    else:
        travel_id = request.session.get('travel_id')
        formset = EditSegmentFormSet(queryset=Segment.objects.all().filter(travel_id=travel_id))

    return render(request, 'itineris/show_segments.html', {"formset": formset})


def end_travel_creation(request):
    travel_id = request.session.get('travel_id')
    request.session['travel_id'] = ''
    travel = get_object_or_404(Travel, travel_id=travel_id)
    travel.status = 'Agendado'
    travel.save()

    if travel.period:
        waypoints = Waypoint.objects.all().filter(travel_id=travel_id).order_by("estimated_datetime_arrival")
        original_segments = Segment.objects.all().filter(travel_id=travel_id)

        start_date = pd.to_datetime(waypoints.first().estimated_datetime_arrival)
        end_date = timezone.make_aware(pd.to_datetime(travel.period.end_date), timezone.get_current_timezone())

        departure_time = waypoints.first().estimated_datetime_arrival.time()

        period_weekdays = [weekday.weekday_id for weekday in travel.period.weekdays.all()]
        date_range = pd.date_range(start=start_date + pd.Timedelta(days=1), end=end_date)
        date_to_use = [d for d in date_range if d.weekday() + 1 in period_weekdays]

        durations = []
        for waypoint in waypoints[1:]:
            durations.append(waypoint.estimated_datetime_arrival - start_date)
        durations = [pd.Timedelta(days=0)] + durations

        for d in date_to_use:
            travel_copy = Travel.objects.create(
                company=travel.company,
                driver=travel.driver,
                vehicle=travel.vehicle,
                address=travel.address,
                geocode=travel.geocode,
                period=travel.period,
                status=travel.status,
            )
            start_date = pd.to_datetime(datetime.combine(d, departure_time))

            for waypoint, duration in zip(waypoints, durations):
                datetime_dep = start_date + duration

                Waypoint.objects.create(
                    travel=travel_copy,
                    city=waypoint.city,
                    estimated_datetime_arrival=timezone.make_aware(datetime_dep, timezone.get_current_timezone()),
                    node_number=waypoint.node_number
                )
            new_waypoints = Waypoint.objects.all().filter(travel_id=travel_copy.travel_id)
            create_segments(travel_copy, new_waypoints, original_segments)

    return redirect('your_travels')


def get_available_options(request):
    if request.GET.get("salida") and request.GET.get("llegada"):
        vehicle_departure = datetime.strptime(request.GET.get("salida"), '%Y-%m-%dT%H:%M').astimezone()
        vehicle_arrival = datetime.strptime(request.GET.get("llegada"), '%Y-%m-%dT%H:%M').astimezone()

        vehicle_exclude = []
        driver_exclude = []

        scheduled_travels = Travel.objects.filter(company_id=request.user.id, status='Agendado')

        available_vehicles = Vehicle.objects.filter(company_id=request.user.id, status='Disponible')
        available_drivers = Driver.objects.filter(company_id=request.user.id, active=True)

        for travel in scheduled_travels:
            if (vehicle_departure <= travel.destination.estimated_datetime_arrival.astimezone() and
                    travel.origin.estimated_datetime_arrival.astimezone() <= vehicle_arrival):
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
    segments = Segment.objects.all()
    return render(request, "itineris/travel_result.html", {'segments': segments})


def travel_result_failed(request):
    return render(request, "itineris/travel_result_failed.html")


def travel_detail(request, travel_id):
    travel = get_object_or_404(Travel, travel_id=travel_id)
    travelers = Traveler.objects.filter(segment__travel=travel_id, payment_status='Confirmado')

    total_passengers = travel.segment_set.aggregate(total=Sum('seats_occupied'))['total'] or 0
    gross_revenue = travelers.aggregate(total=Sum('paid_amount'))['total'] or 0

    segments = Segment.objects.all().filter(travel_id=travel_id)
    waypoints = (travel.origin, travel.destination, total_passengers, gross_revenue)
    return render(request, "itineris/travel_detail.html",
                  {'travelers': travelers, 'waypoints': waypoints, 'travel': travel, 'segments': segments})


def your_drivers(request):
    company_id = request.user.id
    company = get_object_or_404(Company, id=company_id)
    drivers = Driver.objects.filter(company_id=request.user.id, active=True)

    if request.method == "POST":
        # If driver_id is passed, handle edit
        driver_id = request.POST.get("driver_id")
        if driver_id:
            driver = get_object_or_404(Driver, pk=driver_id)
            form = CreateDriver(request.POST, instance=driver)
            if form.is_valid():
                form.save()
                return redirect('your_drivers')
        else:
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

def update_driver(request, driver_id):
    driver = get_object_or_404(Driver, driver_id=driver_id)

    if request.method == 'POST':
        form = CreateDriver(request.POST, instance=driver)
        if form.is_valid():
            form.save()
            messages.success(request, "El conductor se editó correctamente.")
            return redirect('your_drivers')
    else:
        form = CreateDriver(instance=driver)

    return render(request, "itineris/update_driver.html", {'form': form, 'driver': driver})

def your_travels(request):
    travels = Travel.objects.all().filter(company=request.user.id, status='Agendado')
    wp = []
    for travel in travels:
        total_passengers = travel.segment_set.aggregate(total=Sum('seats_occupied'))['total'] or 0

        fee = Segment.objects.all().filter(waypoint_origin=travel.origin,
                                           waypoint_destination=travel.destination).values('fee')[0]['fee']

        wp.append((travel.origin, travel.destination, total_passengers, fee))

    wp.sort(key=lambda x: x[0].estimated_datetime_arrival)

    return render(request, "itineris/your_travels.html", {'travels': wp, })


def travel_history(request):
    travels = Travel.objects.all().filter(company=request.user.id).exclude(status='Borrador')

    vehicles = Vehicle.objects.filter(company_id=request.user.id)
    drivers = Driver.objects.filter(company_id=request.user.id)

    wp = []
    for travel in travels:
        total_passengers = travel.segment_set.aggregate(total=Sum('seats_occupied'))['total'] or 0

        segments = travel.segment_set.all()
        total_paid_amount = (Traveler.objects.all()
                             .filter(segment__in=segments, payment_status='Confirmado')
                             .aggregate(total=Sum('paid_amount'))
                             )['total'] or 0

        wp.append((travel.origin, travel.destination, total_passengers, total_paid_amount))

    wp.sort(key=lambda x: x[0].estimated_datetime_arrival)

    return render(request, "itineris/travel_history.html",
                  {'travels': wp, 'vehicles': vehicles, 'drivers': drivers})


def mark_travel_ended(request, travel_id):
    travel = get_object_or_404(Travel, travel_id=travel_id)
    travel.real_datetime_arrival = datetime.now()
    travel.status = 'Finalizado'
    travel.save()
    travelers = Traveler.objects.filter(segment_id=travel_id, payment_status='Confirmado')

    for traveler in travelers:
        to_email = traveler.email
        subject = f'Itineris | Viaje finalizado!'
        message = (f'¡Gracias por elegirnos!<br>'
                   f'Se ha completado el viaje de '
                   f'{traveler.address_origin}, {traveler.segment.waypoint_origin.city} a '
                   f'{traveler.address_destination}, {traveler.segment.waypoint_destination.city}<br>'
                   f'Día de salida: {traveler.segment.waypoint_origin.estimated_datetime_arrival}<br>'
                   f'Finalizado el: {traveler.segment.waypoint_destination.estimated_datetime_arrival}<br>'
                   f'Empresa: {traveler.segment.travel.company.company_name}<br>'
                   f'Vehículo: {traveler.segment.travel.vehicle}<br>'
                   f'Chofer: {traveler.segment.travel.driver}<br> <br> <br>'
                   f'Si quieres dejar una reseña de viaje puedes hacerlo <a href="localhost:8000">aquí</a>.'
                   )
        try:
            send_email(to_email, subject, message, file=None, html=True)
        except Exception as e:
            messages.error(request, f'Error al enviar el correo de verificación: {str(e)}')

    return travel_detail(request, travel_id)


def start_trip(request, travel_id):
    calculate_full_route(travel_id)

    travel = get_object_or_404(Travel, travel_id=travel_id)
    travel.status = 'En proceso'
    travel.save()
    travelers = Traveler.objects.filter(segment__travel=travel_id, payment_status='Confirmado')

    driver_message = (f"<h2>Ingrese al siguiente <a href={travel.url}>LINK</a> para ver la ruta de viaje.</h2><br>"
                      f"<h3>Lista de pasajeros para el viaje: <br>"
                      f"<table><thead>"
                      f"<tr><th>Trayecto</th>"
                      f"<th>Nombre</th>"
                      f"<th>Apellido</th>"
                      f"<th>DNI</th>"
                      f"<th>Teléfono</th>"
                      f"<th>Dirección Origen</th>"
                      f"<th>Dirección Destino</th></tr></h3>")

    for traveler in travelers:
        to_email = traveler.email
        subject = f'Itineris | El chofer {travel.driver} inició tu viaje!'
        message = (
            f'Se ha iniciado el viaje de {traveler.segment.waypoint_origin.city} a {traveler.segment.waypoint_destination.city}<br>'
            f'El chofer se estará comunicando contigo por teléfono.<br>'
            f'Este es su número de teléfono en caso de que lo necesites! {travel.driver.phone_number} <br>'
            f'Empresa: {travel.company.company_name}<br>'
            f'Vehículo: {travel.vehicle}<br>'
            f'Recuerda chequear que el vehículo sea el correcto. Te brindamos la ruta que el conductor estará '
            f'siguiendo <a href="{travel.url}">aquí</a>'
            )
        driver_message += (f"<tr><td>{traveler.first_name}</td>"
                           f"<td>{traveler.last_name}</td>"
                           f"<td>{traveler.dni}</td>"
                           f"<td>{traveler.phone}</td>"
                           f"<td>{traveler.address_origin}</td>"
                           f"<td>{traveler.address_destination}</td>"
                           f"<td>{traveler.segment.waypoint_origin.city.city_name
                           } - {traveler.segment.waypoint_destination.city.city_name}</td></tr>")
        try:
            send_email(to_email, subject, message, file=None, html=True)
        except Exception as e:
            messages.error(request, f'Error al enviar el correo de verificación: {str(e)}')

    # Envía mail al driver
    driver_email = travel.driver.email
    driver_subject = f'Itineris | Viaje confirmado!'
    driver_message += f"</tbody></table>"

    try:
        send_email(driver_email, driver_subject, driver_message, file=None, html=True)
    except Exception as e:
        messages.error(request, f'Error al enviar el correo de verificación al driver: {str(e)}')

    return travel_detail(request, travel_id)


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

def update_vehicle(request, plate_number):
    vehicle = get_object_or_404(Vehicle, plate_number=plate_number)

    if request.method == 'POST':
        form = CreateVehicle(request.POST, instance=vehicle, disable_plate=True)
        form.fields['plate_number'].widget.attrs['disabled'] = 'disabled'
        if form.is_valid():
            form.save()
            messages.success(request, "El vehículo se editó correctamente.")
            return redirect('your_vehicles')
    else:
        form = CreateVehicle(instance=vehicle, disable_plate=True)

    return render(request, "itineris/update_vehicle.html", {'form': form, 'vehicle': vehicle})


def pre_checkout(request, segment_id):
    request.session['segment_id'] = segment_id
    return redirect('show_travelers')


def show_travelers(request):
    create_traveler_formset = modelformset_factory(Traveler, form=CreateTraveler,
                                                   extra=int(request.session.get("passengers_count")))
    segment = get_object_or_404(Segment, id=request.session.get("segment_id"))

    if request.method == 'POST':
        formset = create_traveler_formset(request.POST)
        if formset.is_valid():
            travelers = formset.save(commit=False)
            t = []
            for traveler in travelers:
                traveler.segment = segment
                traveler.save()
                t.append(traveler.id)
            request.session['travelers'] = t
            segment.seats_occupied += len(t)
            segment.save()
            return redirect('checkout')
        else:
            print("Formset is not valid: ", formset.errors)
            print("Formset data:", request.POST)
    else:
        formset = create_traveler_formset(queryset=Traveler.objects.none())

    return render(request, 'itineris/pre_checkout.html', {"formset": formset, "segment": segment})


def checkout(request):
    session_travelers = request.session.get('travelers')
    # request.session['travelers'] = []  # Limpia los travelers de la session cuando entra a checkout y no está muy bien
    if not session_travelers:
        return HttpResponseBadRequest("No se han creado viajeros.")
    travelers = Traveler.objects.filter(id__in=session_travelers)

    checkout_url = request.build_absolute_uri(reverse('checkout'))
    payment_success_url = request.build_absolute_uri(reverse('payment_success'))

    segment = get_object_or_404(Segment, id=request.session.get('segment_id'))
    sdk = mercadopago.SDK('APP_USR-4911057100331416-060418-a5d1090130a913b3533f686a2c7f5c20-1831872037')
    preference_data = {
        "items": [
            {
                "title": "Pasaje: Itineris",
                "unit_price": segment.fee,
                "quantity": travelers.count()
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
    preference = preference_response["response"]

    return render(request, "itineris/checkout.html",
                  {'travelers': travelers, 'preference': preference})


@csrf_exempt
def payment_success(request):
    payment_status = request.GET.get("status", None)
    print(payment_status)
    if payment_status == 'approved':
        payment_id = request.GET.get("payment_id", None)
        print(payment_id)
        sdk = mercadopago.SDK("APP_USR-4911057100331416-060418-a5d1090130a913b3533f686a2c7f5c20-1831872037")
        payment_info = sdk.payment().get(payment_id)
        print(payment_info)
        status = payment_info["response"]["status"]
        print(status)
        # Por las dudas chequeamos que el pago fue aprobado nuevamente
        if status == 'approved':
            traveler_ids = request.session.get('travelers')
            travelers = Traveler.objects.filter(id__in=traveler_ids)
            for traveler in travelers:
                traveler.payment_status = 'Confirmado'
                encrypted_traveler_id = encrypt_number(traveler.id, key=encryptedkey)

                # test = request.build_absolute_uri(reverse('update_traveler')) + encrypted_traveler_id + "/"

                relative_url = reverse('update_traveler', kwargs={'encrypted_traveler_id': encrypted_traveler_id})
                # Generar la URL absoluta utilizando 'request.build_absolute_uri'
                absolute_url = request.build_absolute_uri(relative_url)

                to_email = traveler.email
                subject = f'Pasaje Itineris - {traveler.segment.waypoint_origin.city} a {traveler.segment.waypoint_destination.city}'
                message = (f'<h1>¡Te brindamos los datos de tu pasaje!</h1><br>'
                           f'<h3>Información de tu pasaje:<br>'
                           f'Origen: {traveler.address_origin}<br>'
                           f'Destino: {traveler.address_destination}<br>'
                           f'Fecha y hora de salida: {traveler.segment.waypoint_origin.estimated_datetime_arrival}<br>'
                           f'Fecha y hora estimada de llegada: {traveler.segment.waypoint_destination.estimated_datetime_arrival}<br>'
                           f'Empresa: {traveler.segment.travel.company.company_name}<br><br>'
                           
                           f'Vehículo: {traveler.segment.travel.vehicle}<br>'
                           f'Chofer: {traveler.segment.travel.driver}<br>'
                           f'Tarifa: ${traveler.segment.fee}<br><br>'

                           f'Si querés editar tus datos antes de viajar podés ingresar al siguiente '
                           f'<a href="{absolute_url}">link</a>.</h3>'
                           )
                try:
                    send_email(to_email, subject, message, file=None, html=True)
                except Exception as e:
                    messages.error(request, f'Error al enviar el correo de verificación: {str(e)}')
                traveler.save()
            return redirect('payment_success')
        else:
            return redirect('checkout')

    return render(request, "itineris/payment_success.html")


def feedback(request, encrypted_traveler_id):
    traveler_id = decrypt_number(encrypted_traveler_id, key=encryptedkey)
    traveler = Traveler.objects.get(id=traveler_id)

    return render(request, "itineris/feedback.html", {'traveler': traveler})


def update_feedback(request):
    if request.method == 'POST':
        traveler_feedback = request.POST.get('feedback')
        traveler = Traveler.objects.get(id=request.POST.get('traveler_id'))
        traveler.feedback = traveler_feedback
        traveler.save()
    return redirect("index")


def update_traveler(request, encrypted_traveler_id):
    traveler_id = decrypt_number(encrypted_traveler_id, key=encryptedkey)
    traveler = Traveler.objects.get(id=traveler_id)
    # Chequea si puede cancelar el viaje el pasajero antes de 48 horas
    can_cancel = True
    # Dos días antes se puede cancelar el viaje
    date_to_check = traveler.segment.waypoint_origin.estimated_datetime_arrival - pd.Timedelta(days=2)

    if datetime.now(pytz.utc) <= date_to_check:
        can_cancel = False
    # Solo permitir editar los datos antes de que haya comenzado el viaje.
    if traveler.segment.travel.status == "Agendado":
        if request.method == 'POST':
            form = UpdateTraveler(request.POST, instance=traveler)
            if form.is_valid():
                form.save()
                messages.success(request, "Tus datos se modificaron exitosamente.")
                return redirect('index')
        else:
            form = UpdateTraveler(instance=traveler)
    # Viajes ya finalizados, en proceso o cancelados.
    else:
        messages.success(request, "No se pueden editar los datos en este momento.")
        return redirect('index')

    return render(request, "itineris/update_traveler.html", {'form': form, 'traveler': traveler,
                                                             'encrypted_traveler_id': encrypted_traveler_id,
                                                             'can_cancel': can_cancel})


def cancel_traveler_ticket(request, encrypted_traveler_id):
    traveler_id = decrypt_number(encrypted_traveler_id, key=encryptedkey)
    traveler = get_object_or_404(Traveler, id=traveler_id)
    traveler.payment_status = 'Cancelado'
    traveler.save()
    messages.success(request, "Tu viaje fue cancelado exitosamente.")

    return redirect('index')



def update_travel(request, travel_id):
    travel = Travel.objects.get(travel_id=travel_id)

    original_travel = Travel.objects.get(travel_id=travel_id)

    can_cancel = True
    # Dos días antes se puede cancelar el viaje
    date_to_check = travel.origin.estimated_datetime_arrival - pd.Timedelta(days=2)

    if datetime.now(pytz.timezone('America/Argentina/Buenos_Aires')) >= date_to_check:
        can_cancel = False
    action = request.POST.get('action')
    if action == 'cancel':
        if travel.company.id == request.user.id:
            if request.POST.get('radio_period') == 'following':
                travels = Travel.objects.filter(period=travel.period)

                future_travels = [
                    t for t in travels
                    if
                    t.origin.estimated_datetime_arrival >= travel.origin.estimated_datetime_arrival
                ]
                print(future_travels)
                for t in future_travels:
                    cancel_travel(t)

            else:
                cancel_travel(travel)

            messages.success(request, "Tu viaje fue cancelado exitosamente.")
        else:
            return "No tienes acceso para borrar este viaje"

        return redirect('your_travels')

    if travel.status == "Agendado":
        if request.method == 'POST':
            formset = EditSegmentFormSet(request.POST)
            form = UpdateTravel(travel_id, request.POST, instance=travel)
            if form.is_valid() and formset.is_valid():
                updated_travel = form.save(commit=False)
                changed_fields = []
                for field in form.changed_data:
                    original_value = getattr(original_travel, field)
                    updated_value = getattr(updated_travel, field)
                    if original_value != updated_value:
                        changed_fields.append(field)
                updated_travel.save()
                formset.save()

                if updated_travel.period:
                    if request.POST.get('radio_period') == 'following':
                        travels = Travel.objects.filter(period=updated_travel.period)
                        # Filtrar los viajes en Python, no en la base de datos
                        future_travels = [
                            travel for travel in travels
                            if
                            travel.origin.estimated_datetime_arrival > updated_travel.origin.estimated_datetime_arrival
                        ]
                        for travel in future_travels:
                            travel.driver = updated_travel.driver
                            travel.vehicle = updated_travel.vehicle
                            travel.address = updated_travel.address
                            travel.geocode = updated_travel.geocode
                            travel.save()

                            # TODO: try this instead
                            # travel = form.save()

                            segments = updated_travel.segment_set.all()
                            for segment in segments:
                                updated_segment = get_object_or_404(Segment,
                                                                    waypoint_origin__city=segment.waypoint_origin.city,
                                                                    waypoint_destination__city=segment.waypoint_destination.city,
                                                                    travel_id=travel.travel_id)
                                updated_segment.fee = segment.fee
                                updated_segment.save()

                messages.success(request, "El viaje fue modificado exitosamente.")

                if 'driver' in changed_fields or 'vehicle' in changed_fields:
                    travelers = Traveler.objects.filter(segment__travel=travel_id, status='Confirmado')
                    if travelers:
                        for traveler in travelers:
                            to_email = traveler.email
                            subject = f'Itineris | Hubo un cambio en tu viaje.'
                            message = (
                                f'Se han actualizado los datos del viaje de {traveler.segment.waypoint_origin.city
                                } a {traveler.segment.waypoint_destination.city} '
                                f'para la fecha {traveler.segment.waypoint_origin.estimated_datetime_arrival}<br>'
                                f'Empresa: {travel.company.company_name}<br>'
                                f'Chofer: ({travel.driver}) se estará comunicando contigo por teléfono.<br>'
                                f'Este es su número de teléfono en caso de que lo necesites! {travel.driver.phone_number}<br>'
                                f'Vehículo: {travel.vehicle}<br>'
                                f'Saludos!'
                            )
                            try:
                                send_email(to_email, subject, message, file=None, html=True)
                            except Exception as e:
                                messages.error(request, f'Error al enviar el correo de verificación: {str(e)}')

                return redirect('your_travels')
        else:
            form = UpdateTravel(travel_id=travel_id, instance=travel)
            formset = EditSegmentFormSet(queryset=Segment.objects.all().filter(travel_id=travel_id))
    else:
        messages.success(request, "No se pueden editar los datos en este momento.")
        return redirect('your_travels')

    return render(request, "itineris/update_travel.html", {
        'form': form,
        'formset': formset,
        'travel': travel,
        'can_cancel': can_cancel,
        'waypoints': (travel.origin, travel.destination)})




def cancel_travel_handler(request, travel_id):
    travel = get_object_or_404(Travel, travel_id=travel_id)




def export_travelers_to_csv(request, travel_id):
    travel = get_object_or_404(Travel, travel_id=travel_id)
    date_ = travel.origin.estimated_datetime_arrival.strftime("%Y-%m-%d")
    city_origin = travel.origin.city.city_name
    city_destination = travel.destination.city.city_name
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{city_origin}_a_{city_destination}_{date_}.csv"'

    # Crear un escritor de CSV con encoding utf-8
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer, quoting=csv.QUOTE_MINIMAL, lineterminator='\n')

    # Escribir el encabezado del CSV
    writer.writerow(
        ['apellido', 'nombre', 'tipo_documento', 'descripcion_documento', 'numero_documento', 'sexo', 'menor'
            , 'nacionalidad', 'tripulante', 'ocupa_butaca'])

    # Obtener los datos de la base de datos y escribirlos en el archivo CSV
    segments = Segment.objects.filter(travel=travel)
    travelers = Traveler.objects.all().filter(segment__in=segments)
    for traveler in travelers:
        writer.writerow([
            traveler.last_name,
            traveler.first_name,
            traveler.dni_type,
            traveler.dni_description,
            traveler.dni,
            traveler.sex,
            traveler.minor,
            traveler.nationality.iso_code,
            0,
            1,
        ])

    response.write('\ufeff')  # Agregar BOM
    response.write(csv_buffer.getvalue())
    csv_buffer.close()

    return response

def export_travel_history(request):
    print(request.POST.get("min"))
    return redirect(travel_history)