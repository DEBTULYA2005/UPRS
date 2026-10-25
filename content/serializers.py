from rest_framework import serializers

from .models import Content, content_id_validator


class ContentSerializer(serializers.ModelSerializer):
    content_id = serializers.CharField(max_length=100, validators=[content_id_validator])

    class Meta:
        model = Content
        fields = [
            "content_id", "title", "category", "description",
            "image_url", "is_active", "created_at",
        ]
        read_only_fields = ["created_at"]

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Title cannot be blank.")
        return value

    def validate_content_id(self, value):
        # The client always comes from the authenticated API key, never from the body.
        client = self.context["request"].auth
        if Content.objects.filter(client=client, content_id=value).exists():
            raise serializers.ValidationError("Content with this content_id already exists for your account.")
        return value
