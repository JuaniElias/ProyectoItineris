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
    result = gmaps.distance_matrix(mode='driving', origins=locations, destinations=locations, region='AR',
                                   units='metric')

    raw_data = []
    for i, origin in enumerate(locations):
        for j, destination in enumerate(locations):
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

    # ACA DEBERÍAMOS CHEQUEAR QUE TODOS LOS VALORES DEL DF TENGAN EL STATUS = 'OK'

    return df.pivot_table(index='destination', columns='origin', values='duration').reset_index()


def get_url_route(best_route: list, gmaps):
    """
    This function returns the URL to the route generated.

    :param best_route: is a list with all the locations in order to generate the route.

    :param gmaps: is the google maps client. A ESTO DEBERÍAMOS HACERLO TIPO VARIABLE GLOBAL DESPUES
    """
    start = best_route[0]
    end = best_route[-1]
    waypoints = best_route[1:len(best_route) - 1]

    route = gmaps.directions(origin=start, destination=end, waypoints=waypoints, mode="driving", alternatives=False,
                             units="metric", region="AR", optimize_waypoints=False)

    overview_polyline = route[0]['overview_polyline']['points']

    # fix locations to create the route URL
    url_start = quote(start, safe='')
    url_end = quote(end, safe='')
    url_waypoints = "|".join(quote(wp, safe='') for wp in waypoints)

    return f"https://www.google.com/maps/dir/?api=1&origin={url_start}&destination={url_end}&waypoints={url_waypoints
    }&travelmode=driving&dir_action=navigate&waypoints={overview_polyline}"


def calculate_full_route(travel_id):
    gmaps = googlemaps.Client(key='')
    # el start point debería estar indicado por la empresa, sería el punto de acceso a la ciudad final.
    start_point = 'Pablo Stampa 2510, Chajari'
    # esta lista debería venir de una query a la base de datos trayendo todos los destinos para un viaje
    pickup_addresses = [start_point]
    drop_off_addresses = []
    travel = get_object_or_404(Travel, id=travel_id)
    travelers = Traveler.objects.filter(travel_id=travel_id)

    for traveler in travelers:
        address_ori = f'{traveler.addr_ori} {traveler.addr_ori_num}, {Travel.city_origin}'
        pickup_addresses.append(address_ori)
        address_dest = f'{traveler.addr_dest} {traveler.addr_dest_num}, {Travel.city_destination}'
        drop_off_addresses.append(address_dest)

    # esto puede ir como no, dependiendo de la solución que tomemos.

    distance_matrix_pickup = get_distance_matrix(pickup_addresses, gmaps)

    # Remove the start point as a posible destination because it is, indeed, the start point
    distance_matrix_pickup = distance_matrix_pickup[distance_matrix_pickup['destination'] != start_point]

    best_route_pickup = get_best_route(start_point, distance_matrix_pickup)

    drop_off_start = best_route_pickup[-1]
    drop_off_addresses.append(drop_off_start)
    distance_matrix_drop_off = get_distance_matrix(drop_off_addresses, gmaps)
    distance_matrix_drop_off = distance_matrix_drop_off[distance_matrix_drop_off['destination'] != start_point]
    best_route_drop_off = get_best_route(drop_off_start, distance_matrix_drop_off)

    final_route = best_route_pickup[:-1] + best_route_drop_off
    url = get_url_route(final_route, gmaps)

    return url
