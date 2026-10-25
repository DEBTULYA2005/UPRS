import re

from rest_framework import serializers

from interactions.serializers import validate_external_user_id

MAX_TOP_K = 50


class RecommendationQuerySerializer(serializers.Serializer):
    user_id = serializers.CharField(max_length=100)
    top_k = serializers.IntegerField(min_value=1, max_value=MAX_TOP_K, default=8)

    def validate_user_id(self, value):
        return validate_external_user_id(value)


class SimilarQuerySerializer(serializers.Serializer):
    content_id = serializers.CharField(max_length=100)
    top_k = serializers.IntegerField(min_value=1, max_value=MAX_TOP_K, default=6)

    def validate_content_id(self, value):
        if not re.match(r"^[A-Za-z0-9_.:-]+$", value):
            raise serializers.ValidationError("Invalid content_id.")
        return value


class RecommendationItemSerializer(serializers.Serializer):
    content_id = serializers.CharField()
    title = serializers.CharField()
    category = serializers.CharField()
    image_url = serializers.CharField(allow_blank=True)
    score = serializers.FloatField()


class RecommendationResponseSerializer(serializers.Serializer):
    strategy = serializers.ChoiceField(
        choices=["personalized", "popular_fallback", "content_similarity", "empty"]
    )
    count = serializers.IntegerField()
    results = RecommendationItemSerializer(many=True)
    user_id = serializers.CharField(required=False)
    content_id = serializers.CharField(required=False)


class HealthSerializer(serializers.Serializer):
    status = serializers.CharField()
    database = serializers.CharField()
