"""Story 10.3 — tableau qualité référentiel : KPIs, fraîcheur, seuils, accès.

Contrats : les comptes suivent `status` (source de vérité 9.1/9.2), la
fraîcheur se mesure sur la dernière révision (repli création) des seules
fiches publiées, les seuils de l'AC arment `alert`, et l'endpoint est
réservé path_admin.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.db.models import Max
from django.utils import timezone
from rest_framework.test import APIClient

from apps.core.rls_testing import as_path_admin
from apps.professions.models import (
    Profession,
    ProfessionReport,
    ProfessionRevision,
    ProfessionStatus,
)
from apps.professions.referential_quality import build_quality_report

pytestmark = pytest.mark.django_db

QUALITY_URL = "/api/v1/admin/referential-quality/"


def _profession(slug: str, *, status: str = ProfessionStatus.PUBLISHED, created_days_ago=0):
    with as_path_admin():
        p = Profession.objects.create(
            slug=slug,
            name=slug,
            sector="test",
            description="d",
            status=status,
        )
        if created_days_ago:
            Profession.objects.filter(pk=p.pk).update(
                created_at=timezone.now() - timedelta(days=created_days_ago)
            )
            p.refresh_from_db()
    return p


def _revision(profession, *, days_ago: int):
    with as_path_admin():
        r = ProfessionRevision.objects.create(
            profession=profession,
            action=ProfessionRevision.Action.UPDATED,
            snapshot={},
        )
        ProfessionRevision.objects.filter(pk=r.pk).update(
            created_at=timezone.now() - timedelta(days=days_ago)
        )


def test_counts_follow_editorial_status():
    _profession("q-pub-1")
    _profession("q-pub-2")
    _profession("q-draft", status=ProfessionStatus.DRAFT)
    _profession("q-arch", status=ProfessionStatus.ARCHIVED)

    report = build_quality_report()
    professions = report["professions"]
    assert professions["published"] >= 2
    assert professions["draft"] >= 1
    assert professions["archived"] >= 1
    assert professions["targets"] == {"mvp": 50, "growth": 500}


def test_freshness_counts_only_published_and_uses_last_revision():
    fresh = _profession("q-fresh", created_days_ago=700)
    _revision(fresh, days_ago=30)  # éditée récemment malgré une création vieille
    _profession("q-stale", created_days_ago=700)  # jamais éditée → repli création, stale
    _profession("q-stale-draft", status=ProfessionStatus.DRAFT, created_days_ago=700)

    report = build_quality_report()
    pct = report["freshness"]["professions_pct"]
    # Publiées : q-fresh (fraîche) + q-stale (périmée) + le seed éventuel.
    # On vérifie la mécanique plutôt qu'un chiffre absolu dépendant du seed :
    total_published = Profession.objects.filter(status="published").count()
    cutoff = timezone.now() - timedelta(days=365)
    expected_fresh = sum(
        1
        for last, created in Profession.objects.filter(status="published")
        .annotate(last_edit=Max("revisions__created_at"))
        .values_list("last_edit", "created_at")
        if (last or created) >= cutoff
    )
    assert pct == round(100 * expected_fresh / total_published, 1)


def test_reports_threshold_arms_alert():
    prof = _profession("q-reports")
    with as_path_admin():
        for i in range(21):
            ProfessionReport.objects.create(
                profession=prof,
                error_type="debouches_perimes",
                comment=f"signalement {i}",
            )
    report = build_quality_report()
    assert report["reports"]["open"] >= 21
    assert report["reports"]["alert"] is True


def test_trends_bucket_by_month():
    prof = _profession("q-trend")
    _revision(prof, days_ago=5)
    _revision(prof, days_ago=40)

    report = build_quality_report()
    trends = report["trends"]
    assert len(trends["months"]) == 6
    assert trends["months"][-1] == timezone.now().strftime("%Y-%m")
    assert trends["profession_edits"][-1] >= 1
    assert sum(trends["profession_edits"]) >= 2


def test_endpoint_requires_path_admin(django_user_model):
    from apps.accounts.models import UserRole, UserStatus

    with as_path_admin():
        student = django_user_model.objects.create_user(
            email="q-student@test.local",
            password="Strong1!pass",
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
        )
        admin = django_user_model.objects.create_user(
            email="q-admin@test.local",
            password="Strong1!pass",
            role=UserRole.PATH_ADMIN,
            status=UserStatus.ACTIVE,
            email_verified_at=timezone.now(),
            is_superuser=True,  # bypass MFA (patron des tests admin 9.x)
        )
    client = APIClient()
    client.force_authenticate(user=student)
    assert client.get(QUALITY_URL).status_code == 403

    client.force_authenticate(user=admin)
    response = client.get(QUALITY_URL)
    assert response.status_code == 200
    body = response.json()
    assert {"professions", "schools", "freshness", "reports", "moderation", "trends"} <= set(body)
