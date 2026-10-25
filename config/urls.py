from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from recommendations.views import HealthView


def json_not_found(request, exception=None):
    return JsonResponse({"detail": "Not found."}, status=404)


def json_server_error(request):
    return JsonResponse({"detail": "Internal server error."}, status=500)


handler404 = json_not_found
handler500 = json_server_error

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", HealthView.as_view(), name="health"),
    path("api/content/", include("content.urls")),
    path("api/events/", include("interactions.urls")),
    path("api/recommendations/", include("recommendations.urls")),
    # Interactive documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
