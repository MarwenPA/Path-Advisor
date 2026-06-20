"""Liveness probe — no auth required."""

from fastapi import APIRouter

from src.api.schemas import HealthResponse
from src.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        model_version=settings.model_version,
    )
