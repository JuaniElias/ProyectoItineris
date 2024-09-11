import itertools
import os

from django.core.mail import EmailMessage
from django.conf import settings

import googlemaps
import pandas as pd
from urllib.parse import quote
from datetime import date
from django.shortcuts import get_object_or_404
from dotenv import load_dotenv

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


def get_distance_matrix(start, end, traveler_to_pickup, traveler_to_drop, gmaps):
    """

    """
    rows_matrix = []
    ids_to_pickup = [traveler.id for traveler in traveler_to_pickup]
    ids_to_drop = [traveler.id for traveler in traveler_to_drop]
    start_id = 'start'
    end_id = 'end' if end is not None else None
    ids_list = ids_to_pickup + ids_to_drop + [start_id] + [end_id] if end is not None else []
    
    locations = ([traveler.geocode_origin for traveler in traveler_to_pickup] 
                 + [traveler.geocode_destination for traveler in traveler_to_drop] 
                 + [start] 
                 + [end] if end is not None else []
                 )
    
    for traveler in traveler_to_pickup:
        # se hacen llamados individuales para no sobrepasar el límite de la API
        result = gmaps.distance_matrix(mode='driving', origins=traveler.geocode_origin, destinations=locations, region='AR',
                                       units='metric')
        rows_matrix.append((traveler.id, result))
    
    for traveler in traveler_to_drop:
        # se hacen llamados individuales para no sobrepasar el límite de la API
        result = gmaps.distance_matrix(mode='driving', origins=traveler.geocode_destination, destinations=locations, region='AR',
                                       units='metric')
        rows_matrix.append((traveler.id, result))
    
    first_place = gmaps.distance_matrix(mode='driving', origins=start, destinations=locations, region='AR',
                                       units='metric')
    rows_matrix.append((start_id, first_place))
    
    if end is not None:
        last_place = gmaps.distance_matrix(mode='driving', origins=end, destinations=locations, region='AR',
                                       units='metric')
        rows_matrix.append((end_id, last_place))

    raw_data = []
    for row in rows_matrix:
        result = row[1]
        id_origin = row[0]
        id_dest = 0
        for i, origin in enumerate(result['origin_addresses']):
            for j, destination in enumerate(result['destination_addresses']):
                data = {
                    'origin': origin,
                    'id_origin': id_origin,
                    'destination': destination,
                    'id_destination': ids_list[id_dest],
                    'distance': result['rows'][i]['elements'][j]['distance']['value'],
                    'duration': result['rows'][i]['elements'][j]['duration']['value'],
                    'status': result['rows'][i]['elements'][j]['status']
                }
                # Agregar el diccionario a la lista
                raw_data.append(data)
                id_dest += 1

    df = pd.json_normalize(raw_data)
    # ACA DEBERÍAMOS CHEQUEAR QUE TODOS LOS VALORES DEL DF TENGAN EL STATUS = 'OK'

    return df.pivot_table(index='id_destination', columns='id_origin', values='duration').reset_index()


def get_url_route(best_route: list):
    """
    This function returns the URL to the route generated.
    :param best_route: is a list with all the locations in order to generate the route.
    """
    url_waypoints = "/".join(quote(wp, safe='') for wp in best_route)

    return f'https://www.google.com/maps/dir/{url_waypoints}'


# Función para calcular la distancia total de una ruta
def calculate_distance(route, distance_matrix):
    distancia_total = 0
    for i in range(len(route) - 1):
        distancia_total += distance_matrix.iloc[route[i], route[i + 1]]
    return distancia_total

# Función para realizar el algoritmo de Branch and Bound
def branch_and_bound(current_route, travelers, pending_nodes, max_capacity, nodes_to_pickup, nodes_to_drop, distance_matrix):
    # Si no quedan nodos por visitar, calculamos la distancia total y retornamos la ruta
    if not pending_nodes:
        complete_route = current_route + [0]  # Volvemos al nodo inicial
        total_distance = calculate_distance(complete_route, distance_matrix)
        return complete_route, total_distance
    
    best_route = None
    best_distance = float('inf')

    # Exploramos las ramas posibles (visitando los nodos pendientes)
    for next_node in pending_nodes:
        if next_node in nodes_to_pickup and travelers < max_capacity:  # Recoger pasajero
            new_route = current_route + [next_node]
            new_pending_nodes = pending_nodes.copy()
            new_pending_nodes.remove(next_node)
            route, distance = branch_and_bound(new_route, travelers + 1, new_pending_nodes,
                                               max_capacity, nodes_to_pickup, nodes_to_drop, distance_matrix)
            if distance < best_distance:
                best_route = route
                best_distance = distance
        elif next_node in nodes_to_drop and travelers > 0:  # Dejar pasajero
            new_route = current_route + [next_node]
            new_pending_nodes = pending_nodes.copy()
            new_pending_nodes.remove(next_node)
            route, distance = branch_and_bound(new_route, travelers - 1, new_pending_nodes, 
                                               max_capacity, nodes_to_pickup, nodes_to_drop, distance_matrix)
            if distance < best_distance:
                best_route = route
                best_distance = distance

    return best_route, best_distance

def calculate_waypoint_route(travel, segments, waypoint):
    gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
    
    traveler_to_pickup = segments.traveler_set.filter(waypoint_origin=waypoint, payment_status='Confirmado')
    traveler_to_drop = segments.traveler_set.filter(waypoint_destination=waypoint, payment_status='Confirmado')
    
    previous_destination = segments.traveler_set.filter(waypoint_destination__node_number=waypoint.node_number - 1).first()
    start = travel.geocode if not previous_destination else previous_destination.geocode_destination
    next_destination = segments.traveler_set.filter(waypoint_destination__node_number=waypoint.node_number + 1).first()
    end = None if not next_destination else next_destination.geocode_destination

    distance_matrix = get_distance_matrix(start, end, traveler_to_pickup, traveler_to_drop, gmaps)
    
    # Inicialización
    start_point = 'start'
    first_route = [start_point]

    nodes_to_pickup = [traveler.id for traveler in traveler_to_pickup]
    nodes_to_drop = [traveler.id for traveler in traveler_to_drop]
    max_capacity = travel.vehicle.capacity
    travelers_on_board = 0 if not previous_destination else previous_destination.seats_occupied

    # Nodos que deben ser visitados
    pending_nodes = nodes_to_pickup + nodes_to_drop

    # Llamada al algoritmo
    best_route, best_distance = branch_and_bound(
        first_route, travelers_on_board, pending_nodes, max_capacity, nodes_to_pickup, nodes_to_drop, distance_matrix
    )
    
    best_route = best_route if end is None else best_route[:-1]
    best_route = best_route if not previous_destination else best_route[1:]
    
    geocode_route = []
    for node in best_route:
        if node in nodes_to_pickup:
            geocode_route.append(traveler_to_pickup.get(id=node).geocode_origin)
        elif node in nodes_to_drop:
            geocode_route.append(traveler_to_drop.get(id=node).geocode_destination)
        elif node == 'start':
            geocode_route.append(start)
    
    return geocode_route

def calculate_full_route(travel_id):
    # el start point debería estar indicado por la empresa, sería el punto de acceso a la ciudad final.
    travel = get_object_or_404(Travel, travel_id=travel_id)
    segments = travel.segment_set.all()
    waypoints = travel.waypoint_set.all().order_by('node_number')
    
    complete_route = []
    for waypoint in waypoints:
        best_route = calculate_waypoint_route(travel, segments, waypoint)
        complete_route += best_route
        # waypoint.url = get_url_route(best_route)
        # waypoint.save()
    
    travel.url = get_url_route(complete_route)
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