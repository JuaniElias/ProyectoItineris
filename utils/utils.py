from django.core.mail import EmailMessage
from django.conf import settings

import googlemaps
import pandas as pd
from urllib.parse import quote

from django.shortcuts import get_object_or_404

from itineris.models import Traveler, Travel


def send_email(to_email, subject, message, file):
    email = EmailMessage(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [to_email],
    )
    if file:
        email.attach(file.name, file.read(), file.content_type)

    email.send()


def get_next_destination(origin: str, distance_matrix: pd.DataFrame):
    """
    This function returns the best consequent given an starting point. It selects the destination with the minimum distance/time
    and then remove that location so the value is not duplicated.

    :param origin: is the starting point from where we are going to look for the next destination.

    :param distance_matrix:  is a squared matrix with the distance/time between different locations. Column names have the Origin,
    while rows have the destinations. This parameter is then returned without the destination selected.
    """
    # distance_matrix['Poyredon 1020']
    #
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


def get_url_route(best_route: list, gmaps):
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
        address_ori = f'{traveler.addr_ori} {traveler.addr_ori_num}, {travel.city_origin}'
        pickup_addresses.append(address_ori)
        address_dest = f'{traveler.addr_dest} {traveler.addr_dest_num}, {travel.city_destination}'
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

    # Remove the start point as a posible destination because it is, indeed, the start point
    distance_matrix_drop_off = distance_matrix_drop_off[distance_matrix_drop_off['destination'] != drop_off_start]

    best_route_drop_off = get_best_route(drop_off_start, distance_matrix_drop_off)

    final_route = best_route_pickup[:-1] + best_route_drop_off
    url = get_url_route(final_route)

    travel.url = url
    travel.save()
