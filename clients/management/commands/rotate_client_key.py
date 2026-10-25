from django.core.management.base import BaseCommand, CommandError

from clients.models import Client


class Command(BaseCommand):
    help = "Issue a new API key for an existing client (the old key stops working)."

    def add_arguments(self, parser):
        parser.add_argument("client_id", type=int)

    def handle(self, *args, **options):
        try:
            client = Client.objects.get(pk=options["client_id"])
        except Client.DoesNotExist:
            raise CommandError("No client with that id.")
        raw_key = client.set_new_api_key()
        client.save()
        self.stdout.write(self.style.SUCCESS(f"New key for '{client.name}' (shown once):"))
        self.stdout.write(raw_key)
