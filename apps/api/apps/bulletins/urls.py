from django.urls import path

from . import views
from .views_manual import BulletinManualDetailView, BulletinManualListView

app_name = "bulletins"

urlpatterns = [
    path(
        "me/bulletins/manual",
        BulletinManualListView.as_view(),
        name="me-bulletins-manual",
    ),
    path(
        "me/bulletins/manual/<str:pk>",
        BulletinManualDetailView.as_view(),
        name="me-bulletins-manual-detail",
    ),
    path(
        "me/bulletins/upload",
        views.BulletinUploadView.as_view(),
        name="me-bulletins-upload",
    ),
    path(
        "me/bulletins/ocr/start",
        views.OCRStartView.as_view(),
        name="me-bulletins-ocr-start",
    ),
    path(
        "me/bulletins/ocr/status",
        views.OCRStatusView.as_view(),
        name="me-bulletins-ocr-status",
    ),
    path(
        "me/bulletins/<str:bulletin_id>/finalize",
        views.BulletinFinalizeView.as_view(),
        name="me-bulletins-finalize",
    ),
    path(
        "me/bulletins/onboarding/status",
        views.OnboardingStatusView.as_view(),
        name="me-bulletins-onboarding-status",
    ),
]
