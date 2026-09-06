"""Cohort reporting export tests — Story 6.9.

Covers:
- GET /api/v1/establishments/cohort-dashboard/export.csv/ — AC (CSV, no
  nominative data, k-anonymity threshold, audit trace with content hash)
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole, UserStatus
from apps.audit.models import AuditLog
from apps.core.rls import bypass_rls
from apps.establishments.services.cohort_reporting_export import (
    K_ANONYMITY_THRESHOLD,
    export_cohort_reporting_csv,
)

pytestmark = pytest.mark.django_db


def _uf(**kwargs) -> User:
    with bypass_rls(reason="test_setup.create_reporting_user"):
        return User.objects.create_user(
            password="Strong1!pass",
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
            **kwargs,
        )


def _counselor() -> User:
    counselor = _uf(
        email="counselor-reporting@test.local",
        role=UserRole.COUNSELOR,
        tenant_id="00000000-0000-0000-0000-0000000000f9",
    )
    counselor.is_verified = lambda: True
    return counselor


DASHBOARD_FIXTURE = {
    "kpis": {"nb_eleves": 12, "taux_completion_profil": 75.0, "nb_eleves_mode_degrade": 3},
    "top_metiers": [
        {"name": "Infirmier·ère", "count": 6},
        {"name": "Agent·e logistique", "count": 2},
    ],
    "distribution_filiere": [
        {"filiere": "Générale", "count": 8},
        {"filiere": "Non renseigné", "count": 4},
    ],
    "activite_recente": [{"student_id": "usr_should_not_leak", "derniere_connexion": None}],
    "eleves": [{"student_id": "usr_should_not_leak_either", "cohort_name": "Terminale"}],
}


class TestCohortReportingExport:
    @patch("apps.establishments.services.cohort_reporting_export.get_cohort_dashboard")
    def test_export_folds_categories_below_k_anonymity_threshold(self, mock_dashboard):
        mock_dashboard.return_value = DASHBOARD_FIXTURE
        counselor = _counselor()

        content = export_cohort_reporting_csv(counselor=counselor).decode("utf-8")

        assert "Infirmier·ère" in content
        assert "Agent·e logistique" not in content  # count=2 < 5, folded
        assert "Autres (<5)" in content

    @patch("apps.establishments.services.cohort_reporting_export.get_cohort_dashboard")
    def test_export_contains_no_nominative_data(self, mock_dashboard):
        mock_dashboard.return_value = DASHBOARD_FIXTURE
        counselor = _counselor()

        content = export_cohort_reporting_csv(counselor=counselor).decode("utf-8")

        assert "usr_should_not_leak" not in content
        assert "usr_should_not_leak_either" not in content

    @patch("apps.establishments.services.cohort_reporting_export.get_cohort_dashboard")
    def test_export_writes_audit_log_with_content_hash(self, mock_dashboard):
        mock_dashboard.return_value = DASHBOARD_FIXTURE
        counselor = _counselor()

        export_cohort_reporting_csv(counselor=counselor)

        with bypass_rls(reason="test_assert.read_audit_log"):
            log = AuditLog.objects.filter(action="establishments.cohort_reporting_exported").latest(
                "created_at"
            )
        assert "content_hash" in log.metadata
        assert len(log.metadata["content_hash"]) == 64  # sha256 hex digest

    def test_endpoint_returns_csv_with_attachment_header(self):
        counselor = _counselor()
        client = APIClient()
        client.force_authenticate(user=counselor)

        response = client.get(reverse("establishments_cohort:counselor-cohort-reporting-export"))

        assert response.status_code == 200, response.content
        assert response["Content-Type"] == "text/csv"
        assert 'filename="reporting-cohorte.csv"' in response["Content-Disposition"]

    def test_endpoint_requires_counselor_role(self):
        student = _uf(email="intruder-reporting@test.local", role=UserRole.STUDENT)
        client = APIClient()
        client.force_authenticate(user=student)

        response = client.get(reverse("establishments_cohort:counselor-cohort-reporting-export"))

        assert response.status_code == 403

    def test_threshold_constant_is_5(self):
        assert K_ANONYMITY_THRESHOLD == 5
