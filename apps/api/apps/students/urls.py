from django.urls import path

from . import views
from .views_maturity import ProfileMaturityView

app_name = "students"

urlpatterns = [
    path(
        "me/onboarding/passions",
        views.OnboardingPassionsView.as_view(),
        name="me-onboarding-passions",
    ),
    path(
        "me/onboarding/level",
        views.OnboardingLevelView.as_view(),
        name="me-onboarding-level",
    ),
    path(
        "me/profile/maturity",
        ProfileMaturityView.as_view(),
        name="me-profile-maturity",
    ),
]
