import itertools

from django.core.mail import EmailMessage
from django.conf import settings

import googlemaps
import pandas as pd
from urllib.parse import quote
from datetime import date
from django.shortcuts import get_object_or_404

from itineris.models import Traveler, Travel, Segment

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


def get_next_destination(origin: str, distance_matrix: pd.DataFrame):
    """
    This function returns the best consequent given an starting point. It selects the destination with the minimum distance/time
    and then remove that location so the value is not duplicated.

    :param origin: is the starting point from where we are going to look for the next destination.

    :param distance_matrix:  is a squared matrix with the distance/time between different locations. Column names have the Origin,
    while rows have the destinations. This parameter is then returned without the destination selected.
    """
    id_min = distance_matrix[distance_matrix[origin] > 0][origin].idxmin()
    destination = distance_matrix.loc[id_min, 'destination']
    distance_matrix = distance_matrix[distance_matrix['destination'] != destination]

    return destination, distance_matrix


def get_best_route(start_point: str, distance_matrix: pd.DataFrame):
    """
    This function returns the best route based on a starting point, which is on the distance matrix provided.
    In order to return a route it uses a heuristic method.

    :param start_point: is the starting point of the travel, where the travel begin

    :param distance_matrix: is a squared matrix with the distance/time between different locations. Column names have the Origin,
    while rows have the destinations.
    """
    best_consequent = [start_point]
    locations = distance_matrix.iloc[:, 1:].columns.to_list()
    locations = [x for x in locations if x != start_point]

    for i in range(1, len(locations) + 1):
        origin = best_consequent[i - 1]
        destination, distance_matrix = get_next_destination(origin, distance_matrix)
        best_consequent.append(destination)

    return best_consequent


def get_distance_matrix(locations: list, gmaps):
    """

    """
    rows_matrix = []

    for item in locations:
        # se hacen llamados individuales para no sobrepasar el límite de la API
        result = gmaps.distance_matrix(mode='driving', origins=item, destinations=locations, region='AR',
                                       units='metric')
        rows_matrix.append(result)

    raw_data = []
    for result in rows_matrix:
        for i, origin in enumerate(result['origin_addresses']):
            for j, destination in enumerate(result['destination_addresses']):
                data = {
                    'origin': origin,
                    'destination': destination,
                    'distance': result['rows'][i]['elements'][j]['distance']['value'],
                    'duration': result['rows'][i]['elements'][j]['duration']['value'],
                    'status': result['rows'][i]['elements'][j]['status']
                }
                # Agregar el diccionario a la lista
                raw_data.append(data)

    df = pd.json_normalize(raw_data)
    df.origin = pd.Categorical(df.origin, categories=df.origin.unique(), ordered=True)
    # ACA DEBERÍAMOS CHEQUEAR QUE TODOS LOS VALORES DEL DF TENGAN EL STATUS = 'OK'

    return df.pivot_table(index='destination', columns='origin', values='duration').reset_index()


def get_url_route(best_route: list):
    """
    This function returns the URL to the route generated.
    :param best_route: is a list with all the locations in order to generate the route.
    """
    url_waypoints = "/".join(quote(wp, safe='') for wp in best_route)

    return f'https://www.google.com/maps/dir/{url_waypoints}'


def calculate_full_route(travel_id):
    gmaps = googlemaps.Client(key='')
    # el start point debería estar indicado por la empresa, sería el punto de acceso a la ciudad final.
    travel = get_object_or_404(Travel, travel_id=travel_id)
    start_point = travel.addr_origin + ' ' + travel.addr_origin_num + ', ' + str(travel.city_origin)
    # esta lista debería venir de una query a la base de datos trayendo todos los destinos para un viaje
    pickup_addresses = [start_point]
    drop_off_addresses = []

    travelers = Traveler.objects.filter(travel_id=travel_id)

    for traveler in travelers:
        address_ori = f'{traveler.addr_ori} {traveler.addr_ori_num}, {traveler.segment.waypoint_origin.city}'
        pickup_addresses.append(address_ori)
        address_dest = f'{traveler.addr_dest} {traveler.addr_dest_num}, {traveler.segment.waypoint_destination.city}'
        drop_off_addresses.append(address_dest)

    distance_matrix_pickup = get_distance_matrix(pickup_addresses, gmaps)
    start_point = distance_matrix_pickup.columns.to_list()[1]

    # Remove the start point as a posible destination because it is, indeed, the start point
    distance_matrix_pickup = distance_matrix_pickup[distance_matrix_pickup['destination'] != start_point]

    best_route_pickup = get_best_route(start_point, distance_matrix_pickup)

    drop_off_start = best_route_pickup[-1]
    drop_off_addresses = [drop_off_start] + drop_off_addresses

    distance_matrix_drop_off = get_distance_matrix(drop_off_addresses, gmaps)
    drop_off_start = distance_matrix_drop_off.columns.to_list()[1]

    # Remove the start point as a possible destination because it is, indeed, the start point
    distance_matrix_drop_off = distance_matrix_drop_off[distance_matrix_drop_off['destination'] != drop_off_start]

    best_route_drop_off = get_best_route(drop_off_start, distance_matrix_drop_off)

    final_route = best_route_pickup[:-1] + best_route_drop_off
    url = get_url_route(final_route)

    travel.url = url
    travel.save()


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

    return [segment for segment in segments if segment.seats_available() >= passengers]