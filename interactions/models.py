from django.core.exceptions import ValidationError
from django.db import models

from clients.models import Client
from content.models import Content
from recommendation_engine.weights import EVENT_TYPE_CHOICES, INTERACTION_WEIGHTS


class UserProfile(models.Model):
    """An end user of a client's app. IDs are isolated per client."""

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="users")
    external_user_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["client", "external_user_id"], name="unique_user_per_client"),
        ]

    def __str__(self):
        return f"{self.external_user_id} ({self.client_id})"


class Interaction(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="interactions")
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="interactions")
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name="interactions")
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    weight = models.PositiveSmallIntegerField(editable=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["client", "user"]),
            models.Index(fields=["client", "content"]),
        ]
        ordering = ["id"]

    def clean(self):
        if self.event_type not in INTERACTION_WEIGHTS:
            raise ValidationError({"event_type": "Unknown event type."})
        if self.user.client_id != self.client_id or self.content.client_id != self.client_id:
            raise ValidationError("User and content must both belong to the interaction's client.")

    def save(self, *args, **kwargs):
        # The weight is ALWAYS derived on the server, never taken from input.
        self.weight = INTERACTION_WEIGHTS[self.event_type] if self.event_type in INTERACTION_WEIGHTS else 0
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user_id} {self.event_type} {self.content_id}"
