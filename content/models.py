from django.core.validators import RegexValidator
from django.db import models

from clients.models import Client

content_id_validator = RegexValidator(
    r"^[A-Za-z0-9_.:-]+$",
    "content_id may only contain letters, digits, and the characters _ . : -",
)


class Content(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="contents")
    # External ID chosen by the client (e.g. a product ID). Unique PER CLIENT.
    content_id = models.CharField(max_length=100, validators=[content_id_validator])
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True, default="")
    description = models.TextField(blank=True, default="")
    image_url = models.URLField(max_length=1000, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["client", "content_id"], name="unique_content_id_per_client"),
        ]
        ordering = ["id"]

    def __str__(self):
        return f"{self.content_id}: {self.title}"
