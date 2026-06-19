from django.urls import path

from . import views

app_name = "bulletins"

urlpatterns = [
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
