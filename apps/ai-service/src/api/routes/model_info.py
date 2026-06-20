"""GET /v1/model-version — model metadata, no auth required."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter

from src.api.schemas import ModelVersionResponse
from src.config import settings
from src.domain.recommendation.statistical_scorer import FEATURES, MODEL_TYPE

router = APIRouter(prefix="/v1", tags=["model-info"])

_DEPLOYED_AT = datetime(2026, 6, 20, tzinfo=UTC)


@router.get("/model-version", response_model=ModelVersionResponse)
async def model_version() -> ModelVersionResponse:
    return ModelVersionResponse(
        model_version=settings.model_version,
        model_type=MODEL_TYPE,
        deployed_at=_DEPLOYED_AT,
        features=FEATURES,
    )
