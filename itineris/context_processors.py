# my_app/context_processors.py
from django.conf import settings

def google_maps_api_key(request):
    """
    Agrega la API Key de Google Maps al contexto de todos los templates.
    """
    return {
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY
    }