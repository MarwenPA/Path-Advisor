from django.urls import path

from . import views

app_name = "audit"

urlpatterns = [
    path("logs/", views.AuditLogListView.as_view(), name="log-list"),
    path("logs/export.csv", views.audit_log_export_csv, name="log-export-csv"),
]
