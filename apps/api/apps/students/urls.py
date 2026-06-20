from django.urls import path

from . import views
from .views_bulletins_status import BulletinsBannerDismissView, BulletinsPostponeView
from .views_maturity import ProfileMaturityView
from .views_profile import (
    ProfileAggregatedView,
    ProfileHistorySnapshotView,
    ProfileHistoryView,
    ProfileRecomputeView,
)

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
    path(
        "me/bulletins/postpone",
        BulletinsPostponeView.as_view(),
        name="me-bulletins-postpone",
    ),
    path(
        "me/bulletins/banner/dismiss",
        BulletinsBannerDismissView.as_view(),
        name="me-bulletins-banner-dismiss",
    ),
    path(
        "me/profile",
        ProfileAggregatedView.as_view(),
        name="me-profile",
    ),
    path(
        "me/profile/recompute",
        ProfileRecomputeView.as_view(),
        name="me-profile-recompute",
    ),
    path(
        "me/profile/history",
        ProfileHistoryView.as_view(),
        name="me-profile-history",
    ),
    path(
        "me/profile/history/snapshot",
        ProfileHistorySnapshotView.as_view(),
        name="me-profile-history-snapshot",
    ),
]
