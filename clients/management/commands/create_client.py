from django.core.management.base import BaseCommand

from clients.models import Client


class Command(BaseCommand):
    help = "Create an API client and print its API key ONCE."

    def add_arguments(self, parser):
        parser.add_argument("name", help="Client name, e.g. 'My E-commerce Shop'")

    def handle(self, *args, **options):
        client, raw_key = Client.create_with_key(options["name"])
        self.stdout.write(self.style.SUCCESS(f"Created client '{client.name}' (id={client.pk})"))
        self.stdout.write("API key (store it securely - it cannot be shown again):")
        self.stdout.write(raw_key)
