class SessionCleanupMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Lista de vistas para limpiar la sesión
        views_to_clear_session = [
            'index',
            'about_us',
            'work_with_us',
            'login',
            'sign_up_business',
        ]

        # Limpia la sesión si la vista actual está en la lista
        if hasattr(request, 'resolver_match') and request.resolver_match:
            current_view_name = request.resolver_match.view_name
            if current_view_name in views_to_clear_session:
                request.session.clear()

        return response
    