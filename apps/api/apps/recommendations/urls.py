from django.urls import path

from .views import (
    RecommendationReviewAdminListView,
    RecommendationReviewCreateView,
    RecommendationsView,
)

urlpatterns = [
    # Story 3.4
    path(
        "students/me/recommendations/",
        RecommendationsView.as_view(),
        name="recommendations-me",
    ),
    # Story 3.7 — RGPD art. 22 human review request
    path(
        "students/me/recommendation-reviews/",
        RecommendationReviewCreateView.as_view(),
        name="recommendation-review-create",
    ),
    path(
        "admin/recommendation-reviews/",
        RecommendationReviewAdminListView.as_view(),
        name="admin-recommendation-review-list",
    ),
]
