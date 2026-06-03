from django.urls import path

from . import views

app_name = "students"

urlpatterns = [
    path(
        "me/onboarding/passions",
        views.OnboardingPassionsView.as_view(),
        name="me-onboarding-passions",
    ),
]
