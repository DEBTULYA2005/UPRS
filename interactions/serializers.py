import re

from rest_framework import serializers

from content.models import Content
from recommendation_engine.weights import INTERACTION_WEIGHTS

from .models import Interaction, UserProfile

USER_ID_RE = re.compile(r"^[A-Za-z0-9_.:@-]+$")


def validate_external_user_id(value):
    if not USER_ID_RE.match(value):
        raise serializers.ValidationError(
            "user_id may only contain letters, digits, and the characters _ . : @ -"
        )
    return value


class EventCreateSerializer(serializers.Serializer):
    """Input for POST /api/events/. Any `weight` or `client` sent is ignored."""

    user_id = serializers.CharField(max_length=100)
    content_id = serializers.CharField(max_length=100)
    event_type = serializers.ChoiceField(choices=list(INTERACTION_WEIGHTS))

    def validate_user_id(self, value):
        return validate_external_user_id(value)

    def validate(self, attrs):
        client = self.context["request"].auth
        try:
            attrs["content"] = Content.objects.get(
                client=client, content_id=attrs["content_id"], is_active=True
            )
        except Content.DoesNotExist:
            raise serializers.ValidationError(
                {"content_id": "No active content with this content_id exists for your account."}
            )
        return attrs

    def create(self, validated_data):
        client = self.context["request"].auth
        user, _ = UserProfile.objects.get_or_create(
            client=client, external_user_id=validated_data["user_id"]
        )
        return Interaction.objects.create(
            client=client,
            user=user,
            content=validated_data["content"],
            event_type=validated_data["event_type"],
        )


class EventSerializer(serializers.ModelSerializer):
    """Output for POST /api/events/."""

    user_id = serializers.CharField(source="user.external_user_id", read_only=True)
    content_id = serializers.CharField(source="content.content_id", read_only=True)

    class Meta:
        model = Interaction
        fields = ["id", "user_id", "content_id", "event_type", "weight", "timestamp"]
        read_only_fields = fields
