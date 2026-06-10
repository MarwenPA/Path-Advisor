from django.urls import path

from . import views

app_name = "profiles"

urlpatterns = [
    path("access-list/", views.access_list, name="profile-access-list"),
]
