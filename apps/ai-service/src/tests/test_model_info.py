"""Tests for GET /v1/model-version."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_model_version_no_auth_required(client: TestClient) -> None:
    response = client.get("/v1/model-version")
    assert response.status_code == 200


def test_model_version_response_shape(client: TestClient) -> None:
    response = client.get("/v1/model-version")
    body = response.json()
    assert body["model_version"] == "0.1.0-statistical"
    assert body["model_type"] == "statistical_content_based"
    assert "deployed_at" in body
    assert isinstance(body["features"], list)
    assert len(body["features"]) > 0


def test_model_version_features_match_scorer(client: TestClient) -> None:
    from src.domain.recommendation.statistical_scorer import FEATURES

    response = client.get("/v1/model-version")
    assert response.json()["features"] == FEATURES
