"""Tests for POST /v1/score-metiers."""

from __future__ import annotations

from fastapi.testclient import TestClient

VALID_BODY = {
    "student_id": "stu_01HXJ123",
    "profile": {
        "passions": ["biologie", "bénévolat"],
        "valeurs": ["utilité_sociale", "autonomie"],
        "niveau": "terminale_generale",
        "specialites": ["SVT", "Maths"],
        "has_bulletins": True,
        "bulletin_summary": {"average": 14.2, "appreciation_keywords": ["engagée"]},
    },
    "occupation_ids": ["occ_01", "occ_02", "occ_03"],
}

NO_BULLETINS_BODY = {
    "student_id": "stu_01HXJ456",
    "profile": {
        "passions": ["sport"],
        "valeurs": ["liberté"],
        "niveau": "troisieme",
        "specialites": [],
        "has_bulletins": False,
        "bulletin_summary": None,
    },
    "occupation_ids": ["occ_10", "occ_11"],
}


def test_score_metiers_requires_jwt(client: TestClient) -> None:
    response = client.post("/v1/score-metiers", json=VALID_BODY)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing JWT token"


def test_score_metiers_rejects_invalid_token(client: TestClient) -> None:
    response = client.post(
        "/v1/score-metiers",
        json=VALID_BODY,
        headers={"Authorization": "Bearer not-a-valid-jwt"},
    )
    assert response.status_code == 401


def test_score_metiers_rejects_expired_token(client: TestClient, expired_token: str) -> None:
    response = client.post(
        "/v1/score-metiers",
        json=VALID_BODY,
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401


def test_score_metiers_with_valid_jwt(auth_client: TestClient) -> None:
    response = auth_client.post("/v1/score-metiers", json=VALID_BODY)
    assert response.status_code == 200
    body = response.json()
    assert body["student_id"] == "stu_01HXJ123"
    assert body["model_version"] == "0.1.0-statistical"
    assert len(body["scored_occupations"]) == 3
    assert "computation_time_ms" in body


def test_score_metiers_response_schema(auth_client: TestClient) -> None:
    response = auth_client.post("/v1/score-metiers", json=VALID_BODY)
    assert response.status_code == 200
    occ = response.json()["scored_occupations"][0]
    assert "occupation_id" in occ
    assert "score" in occ
    assert "signals_contributifs" in occ
    assert "confidence_level" in occ
    assert 0 <= occ["score"] <= 100
    assert occ["confidence_level"] in ("low", "medium", "high")


def test_score_metiers_empty_occupations(auth_client: TestClient) -> None:
    body = dict(VALID_BODY)
    body["occupation_ids"] = []
    response = auth_client.post("/v1/score-metiers", json=body)
    assert response.status_code == 200
    assert response.json()["scored_occupations"] == []


def test_score_metiers_low_confidence_without_bulletins(auth_client: TestClient) -> None:
    response = auth_client.post("/v1/score-metiers", json=NO_BULLETINS_BODY)
    assert response.status_code == 200
    for occ in response.json()["scored_occupations"]:
        assert occ["confidence_level"] == "low"


def test_score_metiers_medium_confidence_with_bulletins(auth_client: TestClient) -> None:
    response = auth_client.post("/v1/score-metiers", json=VALID_BODY)
    assert response.status_code == 200
    for occ in response.json()["scored_occupations"]:
        assert occ["confidence_level"] == "medium"
