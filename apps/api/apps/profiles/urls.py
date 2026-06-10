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
]
