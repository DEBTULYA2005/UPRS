from rest_framework import authentication, exceptions

from .models import Client

API_KEY_HEADER = "X-API-Key"


class ClientPrincipal:
    """Minimal 'user' object so DRF treats a valid API key as authenticated."""

    is_authenticated = True
    is_anonymous = False

    def __init__(self, client):
        self.client = client
        self.pk = client.pk

    def __str__(self):
        return f"client:{self.client.name}"


class ClientApiKeyAuthentication(authentication.BaseAuthentication):
    """Authenticate via the `X-API-Key` header. request.auth is the Client."""

    def authenticate(self, request):
        raw_key = request.headers.get(API_KEY_HEADER)
        if not raw_key:
            return None  # -> NotAuthenticated (401) if the view requires auth
        client = Client.authenticate_key(raw_key.strip())
        if client is None:
            # Deliberately vague: don't reveal whether the key exists or is disabled.
            raise exceptions.AuthenticationFailed("Invalid or inactive API key.")
        return ClientPrincipal(client), client

    def authenticate_header(self, request):
        return API_KEY_HEADER
