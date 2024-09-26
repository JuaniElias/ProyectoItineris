import itertools

from django.core.mail import EmailMessage
from django.conf import settings

import pandas as pd
from datetime import date

from itineris.models import Segment, Traveler

import base64

encryptedkey = 'itinerisencryptedkey'


def send_email(to_email, subject, message, file, html=False):
    email = EmailMessage(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [to_email],
    )
    if html:
        email.content_subtype = "html"
    if file:
        email.attach(file.name, file.read(), file.content_type)

    email.send()


def xor_encrypt_decrypt(input_string, key):
    return ''.join(chr(ord(c) ^ ord(k)) for c, k in zip(input_string, key))


def encrypt_number(number, key):
    number_str = str(number)
    key = (key * (len(number_str) // len(key) + 1))[:len(number_str)]
    encrypted_str = xor_encrypt_decrypt(number_str, key)
    return base64.urlsafe_b64encode(encrypted_str.encode()).decode()


def decrypt_number(encoded_str, key):
    encrypted_str = base64.urlsafe_b64decode(encoded_str).decode()
    key = (key * (len(encrypted_str) // len(key) + 1))[:len(encrypted_str)]
    decrypted_str = xor_encrypt_decrypt(encrypted_str, key)

    return int(decrypted_str)


# Segments
def create_segments(travel, waypoints, segments=None):
    list_of_segments = list(itertools.combinations(waypoints, 2))

    travel.segment_set.all().delete()

    for segment in list_of_segments:
        origin, destination = segment
        duration = destination.estimated_datetime_arrival - origin.estimated_datetime_arrival

        if segments:
            fee = segments.filter(waypoint_origin__city=origin.city,
                                  waypoint_destination__city=destination.city
                                  ).values('fee')[0]['fee']
        else:
            fee = 0

        Segment.objects.create(travel=travel,
                               waypoint_origin=origin,
                               waypoint_destination=destination,
                               duration=duration,
                               fee=fee
                               )


def search_segments(city_origin, passengers):
    maximum_date = date.today() + pd.Timedelta(days=60)
    segments = Segment.objects.filter(
        waypoint_origin__city=city_origin,
        waypoint_origin__estimated_datetime_arrival__date__gte=date.today(),
        waypoint_origin__estimated_datetime_arrival__date__lte=maximum_date,
        travel__status='Agendado'
    ).order_by('waypoint_origin__estimated_datetime_arrival')

    return [segment for segment in segments if segment.seats_available >= passengers]


def cancel_travel(travel):
    travel.status = 'Cancelado'
    travel.save()

    travelers = Traveler.objects.filter(segment__travel=travel, payment_status='Confirmado')

    for traveler in travelers:
        to_email = traveler.email
        subject = f'Itineris | Viaje cancelado.'
        message = (f'La empresa {travel.company.company_name} ha cancelado su viaje de '
                   f'{traveler.segment.waypoint_origin.city} a {traveler.segment.waypoint_destination.city}<br>'
                   f'Día de salida: {traveler.segment.waypoint_origin.estimated_datetime_arrival}<br>'
                   f'En los próximos días verás reflejado la devolución de tu dinero.<br>'
                   f'Lamentamos las molestias.<br>'
                   f'Podes contactarte con nosotros con el siguiente mail: <a>itineris.pf@gmail.com</a>'
                   )
        try:
            send_email(to_email, subject, message, file=None, html=True)
        except Exception as e:
            raise f'Error al enviar el correo de verificación: {str(e)}'