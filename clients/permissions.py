from rest_framework.permissions import BasePermission

from .models import Client


class IsAuthenticatedClient(BasePermission):
    message = "A valid X-API-Key header is required."

    def has_permission(self, request, view):
        return isinstance(request.auth, Client) and request.auth.is_active
