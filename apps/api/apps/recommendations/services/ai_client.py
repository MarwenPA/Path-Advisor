"""HTTP client for Django → ai-service communication.

Django is the single caller of the ai-service.  All JWT generation and
HTTP transport live here so the rest of the codebase stays decoupled.
Architecture: core-architectural-decisions §API — Communication Django ↔ AI service.
"""

from __future__ import annotations

import time

import httpx
import jwt
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from apps.core.exceptions import DomainError


class AIServiceUnavailableError(DomainError):
    type = "https://path-advisor.fr/errors/ai-service-unavailable"
    title = "Service IA indisponible"
    default_detail = "Le service de recommandation est temporairement indisponible."


class AIClient:
    """Facade for calling the FastAPI ai-service scoring endpoints."""

    def _generate_token(self) -> str:
        if not settings.AI_SERVICE_JWT_SECRET:
            raise ImproperlyConfigured("AI_SERVICE_JWT_SECRET must be set (non-empty string).")
        now = int(time.time())
        payload = {
            "sub": "django-api",
            "iat": now,
            "exp": now + settings.AI_SERVICE_JWT_TTL_SECONDS,
        }
        return jwt.encode(payload, settings.AI_SERVICE_JWT_SECRET, algorithm="HS256")

    def score_metiers(
        self,
        student_id: str,
        profile: dict,
        occupation_ids: list[str],
        professions_data: list[dict] | None = None,
    ) -> dict:
        """Call POST /v1/score-metiers and return the parsed JSON response.

        Args:
            professions_data: Optional list of profession signal dicts
                (occupation_id, signals_json, level_compatibility) for
                content-based scoring. When None, the AI service scores
                without profession signals (niveau + bulletin only).

        Raises AIServiceUnavailableError on timeout or HTTP 5xx.
        """
        token = self._generate_token()
        payload: dict = {
            "student_id": student_id,
            "profile": profile,
            "occupation_ids": occupation_ids,
        }
        if professions_data is not None:
            payload["professions_data"] = professions_data
        try:
            response = httpx.post(
                f"{settings.AI_SERVICE_URL}/v1/score-metiers",
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0,
            )
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
        except httpx.TimeoutException as exc:
            raise AIServiceUnavailableError(
                detail="Le service IA n'a pas répondu dans les délais."
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise AIServiceUnavailableError(
                detail=f"Le service IA a retourné une erreur: {exc.response.status_code}"
            ) from exc


ai_client = AIClient()
