# Baseado em: https://medium.com/@keagileageek/putting-a-django-site-in-maintenance-mode-creating-a-django-maintenance-mode-middleware-7c5474f62491

from django.shortcuts import reverse, redirect
from django.conf import settings

# Rotinas para exibir página de manutenção em alguma emergência
class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.META.get('PATH_INFO', "")
        if (request.user.is_authenticated and request.user.tipo_de_usuario!=4) and settings.MAINTENANCE_MODE and path!=reverse("manutencao"):
            response = redirect(reverse("manutencao"))
        elif (request.user.is_authenticated and request.user.tipo_de_usuario!=4) and (not settings.MAINTENANCE_MODE) and path==reverse("manutencao"):
            response = redirect(reverse("index"))
        else:
            response = self.get_response(request)
        return response
    