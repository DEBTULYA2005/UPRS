from django.urls import path

from .views import ContentDetailView, ContentListCreateView

urlpatterns = [
    path("", ContentListCreateView.as_view(), name="content-list"),
    path("<str:content_id>/", ContentDetailView.as_view(), name="content-detail"),
]
