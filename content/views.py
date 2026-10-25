from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics

from .models import Content
from .serializers import ContentSerializer


class ContentListCreateView(generics.ListCreateAPIView):
    serializer_class = ContentSerializer

    def get_queryset(self):
        qs = Content.objects.filter(client=self.request.auth)
        category = self.request.query_params.get("category")
        search = self.request.query_params.get("q")
        if self.request.query_params.get("include_inactive", "").lower() not in {"1", "true"}:
            qs = qs.filter(is_active=True)
        if category:
            qs = qs.filter(category__iexact=category)
        if search:
            qs = qs.filter(title__icontains=search)
        return qs

    @extend_schema(
        summary="List your content (paginated)",
        parameters=[
            OpenApiParameter("category", str, description="Exact category (case-insensitive)"),
            OpenApiParameter("q", str, description="Title contains"),
            OpenApiParameter("include_inactive", bool, description="Include inactive content"),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="Create a content item for your account")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(client=self.request.auth)


class ContentDetailView(generics.RetrieveAPIView):
    serializer_class = ContentSerializer

    def get_object(self):
        # Scoped to the authenticated client: other clients' IDs give 404.
        return get_object_or_404(
            Content, client=self.request.auth, content_id=self.kwargs["content_id"]
        )

    @extend_schema(summary="Retrieve one content item by your content_id")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
