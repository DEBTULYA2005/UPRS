from django.urls import path

from .views import PersonalizedRecommendationView, SimilarContentView

urlpatterns = [
    path("", PersonalizedRecommendationView.as_view(), name="recommendations"),
    path("similar/", SimilarContentView.as_view(), name="recommendations-similar"),
]
