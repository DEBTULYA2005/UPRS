from django.apps import AppConfig


class ClientsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "clients"

    def ready(self):
        from . import schema  # noqa: F401  (registers the X-API-Key scheme for the docs)
