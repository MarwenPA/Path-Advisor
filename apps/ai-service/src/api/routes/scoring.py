"""POST /v1/score-metiers — vocationnel scoring endpoint."""

from __future__ import annotations

import time
from typing import Annotated

from fastapi import APIRouter, Depends

from src.api.dependencies import verify_jwt
from src.api.schemas import ScoreMeRequest, ScoreMeResponse
from src.config import settings
from src.domain.recommendation.statistical_scorer import score_occupations

router = APIRouter(prefix="/v1", tags=["scoring"])


@router.post("/score-metiers", response_model=ScoreMeResponse)
async def score_metiers(
    body: ScoreMeRequest,
    _claims: Annotated[dict, Depends(verify_jwt)],
) -> ScoreMeResponse:
    start = time.monotonic()
    professions_data = (
        [p.model_dump() for p in body.professions_data] if body.professions_data else None
    )
    scored = score_occupations(body.profile.model_dump(), body.occupation_ids, professions_data)
    elapsed_ms = int((time.monotonic() - start) * 1000)
    return ScoreMeResponse(
        student_id=body.student_id,
        model_version=settings.model_version,
        scored_occupations=scored,
        computation_time_ms=elapsed_ms,
    )
