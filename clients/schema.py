from drf_spectacular.extensions import OpenApiAuthenticationExtension


class ClientApiKeyScheme(OpenApiAuthenticationExtension):
    target_class = "clients.authentication.ClientApiKeyAuthentication"
    name = "ApiKeyAuth"

    def get_security_definition(self, auto_schema):
        return {"type": "apiKey", "in": "header", "name": "X-API-Key"}
