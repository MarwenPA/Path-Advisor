"""Tests for Story 3.4 — GET /api/v1/students/me/recommendations/."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from rest_framework import status
from rest_framework.test import APIClient

AI_SERVICE_RESPONSE = {
    "student_id": "stu_01",
    "model_version": "0.2.0-statistical",
    "scored_occupations": [
        {
            "occupation_id": "prof_01",
            "score": 90,
            "signals_contributifs": [
                {"signal": "passion_overlap", "weight": 0.35, "contribution": 32}
            ],
            "confidence_level": "high",
        },
        {
            "occupation_id": "prof_02",
            "score": 75,
            "signals_contributifs": [
                {"signal": "passion_overlap", "weight": 0.35, "contribution": 20}
            ],
            "confidence_level": "medium",
        },
        {
            "occupation_id": "prof_03",
            "score": 60,
            "signals_contributifs": [],
            "confidence_level": "low",
        },
        {
            "occupation_id": "prof_04",
            "score": 55,
            "signals_contributifs": [],
            "confidence_level": "low",
        },
        {
            "occupation_id": "prof_05",
            "score": 50,
            "signals_contributifs": [],
            "confidence_level": "low",
        },
        {
            "occupation_id": "prof_06",
            "score": 40,
            "signals_contributifs": [],
            "confidence_level": "low",
        },
        {
            "occupation_id": "prof_07",
            "score": 30,
            "signals_contributifs": [],
            "confidence_level": "low",
        },
        {
            "occupation_id": "prof_08",
            "score": 20,
            "signals_contributifs": [],
            "confidence_level": "low",
        },
        {
            "occupation_id": "prof_09",
            "score": 10,
            "signals_contributifs": [],
            "confidence_level": "low",
        },
    ],
    "computation_time_ms": 42,
}


# ---------------------------------------------------------------------------
# RecommendationService unit tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.postgresql_only
class TestComputeRecommendations:
    def _make_professions(self, db_factory, count: int = 9):
        from apps.professions.models import Profession

        profs = []
        for i in range(1, count + 1):
            p = Profession.objects.create(
                id=f"prof_0{i}" if i < 10 else f"prof_{i}",
                slug=f"metier-{i}",
                name=f"Métier {i}",
                description="desc",
                daily_routine="routine",
                prospects_text="prospects",
                signals_json={"passions": [], "valeurs": []},
                level_compatibility=["terminale_generale"],
                sector="santé",
            )
            profs.append(p)
        return profs

    def test_returns_top_8_sorted_by_score(self, db):
        from apps.accounts.models import User
        from apps.recommendations.services.recommendation_service import compute_recommendations

        user = User.objects.create_user(email="student@test.com", password="pass", role="student")
        self._make_professions(db)

        with patch(
            "apps.recommendations.services.recommendation_service.ai_client.score_metiers",
            return_value=AI_SERVICE_RESPONSE,
        ):
            results = compute_recommendations(user)

        assert len(results) == 8
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_graceful_no_profile(self, db):
        """Student with no profile gets scored with empty profile dict."""
        from apps.accounts.models import User
        from apps.recommendations.services.recommendation_service import compute_recommendations

        user = User.objects.create_user(email="noProfile@test.com", password="pass", role="student")
        self._make_professions(db)

        captured = {}

        def mock_score(student_id, profile, occupation_ids, professions_data=None):
            captured["profile"] = profile
            return AI_SERVICE_RESPONSE

        with patch(
            "apps.recommendations.services.recommendation_service.ai_client.score_metiers",
            side_effect=mock_score,
        ):
            results = compute_recommendations(user)

        assert captured["profile"]["passions"] == []
        assert captured["profile"]["valeurs"] == []
        assert captured["profile"]["has_bulletins"] is False
        assert len(results) == 8

    def test_skips_professions_not_in_db(self, db):
        """If ai-service returns an occupation_id not in DB, it is silently skipped."""
        from apps.accounts.models import User
        from apps.recommendations.services.recommendation_service import compute_recommendations

        user = User.objects.create_user(email="skip@test.com", password="pass", role="student")
        # Only create prof_01 — prof_02 through prof_09 are unknown
        from apps.professions.models import Profession

        Profession.objects.create(
            id="prof_01",
            slug="metier-1",
            name="Métier 1",
            description="desc",
            daily_routine="routine",
            prospects_text="prospects",
            signals_json={},
            level_compatibility=[],
            sector="santé",
        )

        with patch(
            "apps.recommendations.services.recommendation_service.ai_client.score_metiers",
            return_value=AI_SERVICE_RESPONSE,
        ):
            results = compute_recommendations(user)

        assert len(results) == 1
        assert results[0]["id"] == "prof_01"


# ---------------------------------------------------------------------------
# BulletinSummary computation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.postgresql_only
class TestComputeBulletinSummary:
    def test_returns_none_when_no_bulletins(self, db):
        from apps.accounts.models import User
        from apps.recommendations.services.recommendation_service import _compute_bulletin_summary
        from apps.students.models import StudentProfile

        user = User.objects.create_user(
            email="nobulletin@test.com", password="pass", role="student"
        )
        profile = StudentProfile.objects.create(user=user)
        result = _compute_bulletin_summary(profile)
        assert result is None

    def test_computes_average_from_matieres(self, db):
        from apps.accounts.models import User
        from apps.bulletins.models import BulletinManual
        from apps.recommendations.services.recommendation_service import _compute_bulletin_summary
        from apps.students.models import StudentProfile

        user = User.objects.create_user(
            email="withbulletin@test.com", password="pass", role="student"
        )
        profile = StudentProfile.objects.create(user=user)
        BulletinManual.objects.create(
            student=profile,
            trimestre_label="T1",
            year="2025",
            matieres=[
                {"subject_id": "math", "note": 14.0, "appreciation": "bien"},
                {"subject_id": "svt", "note": 16.0, "appreciation": "très bien"},
            ],
        )
        result = _compute_bulletin_summary(profile)
        assert result is not None
        assert result["average"] == pytest.approx(15.0, abs=0.01)

    def test_ignores_zero_notes(self, db):
        from apps.accounts.models import User
        from apps.bulletins.models import BulletinManual
        from apps.recommendations.services.recommendation_service import _compute_bulletin_summary
        from apps.students.models import StudentProfile

        user = User.objects.create_user(email="zeronote@test.com", password="pass", role="student")
        profile = StudentProfile.objects.create(user=user)
        BulletinManual.objects.create(
            student=profile,
            trimestre_label="T1",
            year="2025",
            matieres=[
                {"subject_id": "math", "note": 0, "appreciation": ""},
                {"subject_id": "svt", "note": None, "appreciation": ""},
            ],
        )
        result = _compute_bulletin_summary(profile)
        assert result is None


# ---------------------------------------------------------------------------
# RecommendationsView integration tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.postgresql_only
class TestRecommendationsView:
    def test_requires_auth(self, db):
        client = APIClient()
        response = client.get("/api/v1/students/me/recommendations/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_requires_student_role(self, db):
        from apps.accounts.models import User

        admin = User.objects.create_user(email="admin@test.com", password="pass", role="path_admin")
        client = APIClient()
        client.force_authenticate(user=admin)
        response = client.get("/api/v1/students/me/recommendations/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_success_returns_8_results(self, db):
        from apps.accounts.models import User
        from apps.professions.models import Profession

        student = User.objects.create_user(
            email="student2@test.com", password="pass", role="student"
        )
        for i in range(1, 10):
            Profession.objects.create(
                id=f"prof_0{i}" if i < 10 else f"prof_{i}",
                slug=f"metier-view-{i}",
                name=f"Métier View {i}",
                description="desc",
                daily_routine="routine",
                prospects_text="prospects",
                signals_json={},
                level_compatibility=[],
                sector="santé",
            )

        client = APIClient()
        client.force_authenticate(user=student)

        with patch(
            "apps.recommendations.services.recommendation_service.ai_client.score_metiers",
            return_value=AI_SERVICE_RESPONSE,
        ):
            response = client.get("/api/v1/students/me/recommendations/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "results" in data
        assert "computed_at" in data
        assert len(data["results"]) == 8

    def test_result_schema(self, db):
        from apps.accounts.models import User
        from apps.professions.models import Profession

        student = User.objects.create_user(email="schema@test.com", password="pass", role="student")
        for i in range(1, 10):
            Profession.objects.create(
                id=f"prof_0{i}" if i < 10 else f"prof_{i}",
                slug=f"metier-schema-{i}",
                name=f"Métier Schema {i}",
                description="desc",
                daily_routine="routine",
                prospects_text="prospects",
                signals_json={},
                level_compatibility=[],
                sector="santé",
            )

        client = APIClient()
        client.force_authenticate(user=student)

        with patch(
            "apps.recommendations.services.recommendation_service.ai_client.score_metiers",
            return_value=AI_SERVICE_RESPONSE,
        ):
            response = client.get("/api/v1/students/me/recommendations/")

        item = response.json()["results"][0]
        for field in [
            "id",
            "slug",
            "name",
            "sector",
            "score",
            "confidence_level",
            "signals_contributifs",
            "phrase_recopiable",
        ]:
            assert field in item, f"Missing field: {field}"
        assert 0 <= item["score"] <= 100
        assert item["confidence_level"] in ("low", "medium", "high")

    def test_ai_service_error_returns_503(self, db):
        from apps.accounts.models import User
        from apps.recommendations.services.ai_client import AIServiceUnavailableError

        student = User.objects.create_user(email="error@test.com", password="pass", role="student")
        client = APIClient()
        client.force_authenticate(user=student)

        with patch(
            "apps.recommendations.services.recommendation_service.ai_client.score_metiers",
            side_effect=AIServiceUnavailableError(
                detail="Le service IA n'a pas répondu dans les délais."
            ),
        ):
            response = client.get("/api/v1/students/me/recommendations/")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()
        assert "detail" in data or "title" in data
