from django.urls import path

from . import views

app_name = "profiles"

urlpatterns = [
    path("access-list/", views.access_list, name="profile-access-list"),
    # Story 1.10 — `<str:entry_id>` accepts the composite `<source_name>:<source_pk>`
    # form (colons are allowed by the `str` converter — only `/` is excluded).
    path(
        "access-list/<str:entry_id>/revoke/",
        views.revoke_access_list_entry,
        name="profile-access-revoke",
    ),
    # Story 6.11 — access history modal + CSV export
    path(
        "access-list/<str:entry_id>/history/",
        views.access_list_entry_history,
        name="profile-access-history",
    ),
    path(
        "access-list/<str:entry_id>/history.csv/",
        views.access_list_entry_history_export,
        name="profile-access-history-export",
    ),
]
