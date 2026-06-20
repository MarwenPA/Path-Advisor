"""Unit tests for AIClient — Django → ai-service HTTP client."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import httpx
import jwt
import pytest
from django.conf import settings

from apps.recommendations.services.ai_client import AIClient, AIServiceUnavailableError

SAMPLE_RESPONSE = {
    "student_id": "stu_01HXJ123",
    "model_version": "0.1.0-statistical",
    "scored_occupations": [
        {
            "occupation_id": "occ_01",
            "score": 75,
            "signals_contributifs": [
                {"signal": "passions_overlap", "weight": 0.35, "contribution": 26}
            ],
            "confidence_level": "medium",
        }
    ],
    "computation_time_ms": 42,
}


@pytest.fixture
def client() -> AIClient:
    return AIClient()


class TestGenerateToken:
    def test_token_is_valid_jwt(self, client: AIClient) -> None:
        token = client._generate_token()
        payload = jwt.decode(
            token,
            settings.AI_SERVICE_JWT_SECRET,
            algorithms=["HS256"],
        )
        assert payload["sub"] == "django-api"
        assert "iat" in payload
        assert "exp" in payload

    def test_token_not_expired(self, client: AIClient) -> None:
        token = client._generate_token()
        payload = jwt.decode(
            token,
            settings.AI_SERVICE_JWT_SECRET,
            algorithms=["HS256"],
        )
        assert payload["exp"] > int(time.time())

    def test_token_ttl_matches_settings(self, client: AIClient) -> None:
        before = int(time.time())
        token = client._generate_token()
        payload = jwt.decode(
            token,
            settings.AI_SERVICE_JWT_SECRET,
            algorithms=["HS256"],
        )
        expected_ttl = settings.AI_SERVICE_JWT_TTL_SECONDS
        assert payload["exp"] - payload["iat"] == expected_ttl
        assert payload["iat"] >= before


class TestScoreMetiers:
    def test_success_returns_parsed_json(self, client: AIClient) -> None:
        mock_resp = MagicMock()
        mock_resp.json.return_value = SAMPLE_RESPONSE
        mock_resp.raise_for_status.return_value = None

        with patch("apps.recommendations.services.ai_client.httpx.post", return_value=mock_resp):
            result = client.score_metiers(
                student_id="stu_01HXJ123",
                profile={"has_bulletins": True, "niveau": "terminale_generale"},
                occupation_ids=["occ_01"],
            )

        assert result["model_version"] == "0.1.0-statistical"
        assert len(result["scored_occupations"]) == 1

    def test_sends_bearer_jwt_header(self, client: AIClient) -> None:
        mock_resp = MagicMock()
        mock_resp.json.return_value = SAMPLE_RESPONSE
        mock_resp.raise_for_status.return_value = None

        with patch(
            "apps.recommendations.services.ai_client.httpx.post", return_value=mock_resp
        ) as mock_post:
            client.score_metiers("stu_01", {"has_bulletins": False}, [])

        call_kwargs = mock_post.call_args.kwargs
        auth_header = call_kwargs["headers"]["Authorization"]
        assert auth_header.startswith("Bearer ")
        token = auth_header.split(" ", 1)[1]
        payload = jwt.decode(token, settings.AI_SERVICE_JWT_SECRET, algorithms=["HS256"])
        assert payload["sub"] == "django-api"

    def test_timeout_raises_unavailable_error(self, client: AIClient) -> None:
        with patch(
            "apps.recommendations.services.ai_client.httpx.post",
            side_effect=httpx.TimeoutException("timeout"),
        ), pytest.raises(AIServiceUnavailableError):
            client.score_metiers("stu_01", {}, [])

    def test_http_5xx_raises_unavailable_error(self, client: AIClient) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 503
        http_error = httpx.HTTPStatusError("503", request=MagicMock(), response=mock_resp)

        with patch(
            "apps.recommendations.services.ai_client.httpx.post",
            side_effect=http_error,
        ), pytest.raises(AIServiceUnavailableError):
            client.score_metiers("stu_01", {}, [])

    def test_posts_to_correct_url(self, client: AIClient) -> None:
        mock_resp = MagicMock()
        mock_resp.json.return_value = SAMPLE_RESPONSE
        mock_resp.raise_for_status.return_value = None

        with patch(
            "apps.recommendations.services.ai_client.httpx.post", return_value=mock_resp
        ) as mock_post:
            client.score_metiers("stu_01", {"has_bulletins": False}, ["occ_01"])

        expected_url = f"{settings.AI_SERVICE_URL}/v1/score-metiers"
        assert mock_post.call_args.args[0] == expected_url
