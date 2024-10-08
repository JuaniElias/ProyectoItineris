from django.conf import settings

import googlemaps
import pandas as pd
from urllib.parse import quote
from django.shortcuts import get_object_or_404

from itineris.models import Travel, Segment, Traveler, Waypoint

def calculate_full_route(travel_id):
    # el start point debería estar indicado por la empresa, sería el punto de acceso a la ciudad final.
    travel = get_object_or_404(Travel, travel_id=travel_id)
    segments = Segment.objects.filter(travel=travel, seats_occupied__gt=0)

    waypoint_origin_ids = [s.waypoint_origin.id for s in segments]
    waypoint_destination_ids = [s.waypoint_destination.id for s in segments]

    waypoint_ids = set(waypoint_origin_ids + waypoint_destination_ids)

    waypoints = list(Waypoint.objects.filter(id__in=waypoint_ids).order_by('node_number'))

    complete_route = []
    waypoint_codes = []
    for i, waypoint in enumerate(waypoints):
        start = travel.geocode if len(complete_route) == 0 else complete_route[-1]
        travelers_on_board = waypoint.seats_available

        if i + 1 < len(waypoints):
            next_segment = segments.filter(waypoint_destination=waypoints[i + 1])
            t = Traveler.objects.filter(segment__in=next_segment, payment_status='Confirmado').first()
            end = t.geocode_destination
        else:
            end = None

        best_route = calculate_waypoint_route(travel, segments, waypoint, start, end, travelers_on_board)
        complete_route += best_route
        waypoint_codes.append(best_route)

    fixed_orders = []
    for j, waypoint in enumerate(waypoint_codes):
        if j + 1 < len(waypoint_codes):
            waypoint += [waypoint_codes[j+1][0]]

        fixed_orders.append(waypoint)

    for i, waypoint in enumerate(waypoints):
        waypoint.url = get_url_route(fixed_orders[i])
        waypoint.save()


    travel.url = get_url_route(complete_route)
    travel.save()


def calculate_waypoint_route(travel, segments, waypoint, start, end, travelers_on_board):
    gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)

    # Traer todos los travelers de cada segmento cuyo origen es waypoint
    segments_waypoint_origin = segments.filter(waypoint_origin=waypoint)
    traveler_to_pickup = Traveler.objects.filter(segment__in=segments_waypoint_origin, payment_status='Confirmado')

    # Traer todos los travelers de cada segmento cuyo destino es waypoint
    segments_waypoint_destination = segments.filter(waypoint_destination=waypoint)
    traveler_to_drop = Traveler.objects.filter(segment__in=segments_waypoint_destination, payment_status='Confirmado')

    distance_matrix = get_distance_matrix(start, end, traveler_to_pickup, traveler_to_drop, gmaps)

    # Inicialización
    first_route = ['start']

    nodes_to_pickup = [traveler.id for traveler in traveler_to_pickup]
    nodes_to_drop = [traveler.id for traveler in traveler_to_drop]
    max_capacity = travel.vehicle.capacity

    # Nodos que deben ser visitados
    pending_nodes = nodes_to_pickup + nodes_to_drop

    # Llamada al algoritmo
    best_route, best_distance = branch_and_bound(
        first_route, travelers_on_board, pending_nodes, max_capacity, nodes_to_pickup, nodes_to_drop, distance_matrix
    )

    best_route = best_route if end is None else best_route[:-1]
    best_route = best_route if waypoint.node_number == 0 else best_route[1:]

    geocode_route = []
    for node in best_route:
        if node in nodes_to_pickup:
            geocode_route.append(traveler_to_pickup.get(id=node).geocode_origin)
        elif node in nodes_to_drop:
            geocode_route.append(traveler_to_drop.get(id=node).geocode_destination)
        elif node == 'start':
            geocode_route.append(start)

    return geocode_route


def get_distance_matrix(start, end, traveler_to_pickup, traveler_to_drop, gmaps):
    rows_matrix = []

    # Creo listas con los ID de los travelers para buscar y para dejar
    ids_to_pickup = [traveler.id for traveler in traveler_to_pickup]
    ids_to_drop = [traveler.id for traveler in traveler_to_drop]

    start_id = 'start'
    end_id = 'end' if end is not None else None

    ids_list = ids_to_pickup + ids_to_drop + [start_id] + ([end_id] if end is not None else [])

    locations = ([traveler.geocode_origin for traveler in traveler_to_pickup]
                 + [traveler.geocode_destination for traveler in traveler_to_drop]
                 + [start]
                 + ([end] if end is not None else [])
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

    return df.pivot_table(index='id_destination', columns='id_origin', values='duration')


def branch_and_bound(current_route, travelers, pending_nodes, max_capacity, nodes_to_pickup, nodes_to_drop, distance_matrix):
    # Si no quedan nodos por visitar, calculamos la distancia total y retornamos la ruta
    if not pending_nodes:
        complete_route = current_route + (['end'] if 'end' in distance_matrix.columns else []) # Ponemos el final
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


def calculate_distance(route, distance_matrix):
    distancia_total = 0
    for i in range(len(route) - 1):
        distancia_total += distance_matrix.loc[route[i], route[i + 1]]
    return distancia_total


def get_url_route(best_route: list):
    url_waypoints = "/".join(quote(wp, safe='') for wp in best_route)

    return f'https://www.google.com/maps/dir/{url_waypoints}'
