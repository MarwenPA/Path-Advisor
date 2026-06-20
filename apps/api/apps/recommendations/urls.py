from django.urls import path

from .views import RecommendationsView

urlpatterns = [
    path(
        "students/me/recommendations/",
        RecommendationsView.as_view(),
        name="recommendations-me",
    ),
]
