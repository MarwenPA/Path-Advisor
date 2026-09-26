from django.urls import path

from .views import (
    AdminModelVersionActivateView,
    AdminModelVersionsView,
    RecommendationReviewAdminListView,
    RecommendationReviewCreateView,
    RecommendationsView,
)

urlpatterns = [
    # Story 9.5 — gouvernance des versions de modèle (art. 22).
    path(
        "admin/model-versions/",
        AdminModelVersionsView.as_view(),
        name="admin-model-versions",
    ),
    path(
        "admin/model-versions/<str:version_id>/activate/",
        AdminModelVersionActivateView.as_view(),
        name="admin-model-version-activate",
    ),
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
