from django.db import connection
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .serializers import (
    HealthSerializer,
    RecommendationQuerySerializer,
    RecommendationResponseSerializer,
    SimilarQuerySerializer,
)


class HealthView(APIView):
    """Public, unauthenticated. Reveals no secrets or configuration."""

    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(summary="Health check", responses={200: HealthSerializer, 503: HealthSerializer}, auth=[])
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return Response({"status": "ok", "database": "ok"})
        except Exception:
            return Response(
                {"status": "degraded", "database": "unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


class PersonalizedRecommendationView(APIView):
    @extend_schema(
        summary="Personalized recommendations for a user (Lesson 6 algorithm)",
        description=(
            "Uses the Lesson 6 algorithm when the user has interaction history. "
            "Users with no history get `strategy: popular_fallback` (separate rule, not Lesson 6). "
            "An empty catalogue returns `strategy: empty`."
        ),
        parameters=[
            OpenApiParameter("user_id", str, required=True),
            OpenApiParameter("top_k", int, description="1-50, default 8"),
        ],
        responses=RecommendationResponseSerializer,
    )
    def get(self, request):
        query = RecommendationQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        user_id, top_k = query.validated_data["user_id"], query.validated_data["top_k"]

        strategy, results = services.personalized_recommendations(request.auth, user_id, top_k)
        return Response(
            {"user_id": user_id, "strategy": strategy, "count": len(results), "results": results}
        )


class SimilarContentView(APIView):
    @extend_schema(
        summary="Content similar to a given item (TF-IDF + cosine similarity)",
        parameters=[
            OpenApiParameter("content_id", str, required=True),
            OpenApiParameter("top_k", int, description="1-50, default 6"),
        ],
        responses=RecommendationResponseSerializer,
    )
    def get(self, request):
        query = SimilarQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        content_id, top_k = query.validated_data["content_id"], query.validated_data["top_k"]

        outcome = services.similar_recommendations(request.auth, content_id, top_k)
        if outcome is None:
            return Response(
                {"detail": "Content not found for your account."}, status=status.HTTP_404_NOT_FOUND
            )
        strategy, results = outcome
        return Response(
            {"content_id": content_id, "strategy": strategy, "count": len(results), "results": results}
        )
