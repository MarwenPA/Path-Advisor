"""POST /v1/score-metiers — vocationnel scoring endpoint."""

from __future__ import annotations

import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import verify_jwt
from src.api.schemas import ScoreMeRequest, ScoreMeResponse
from src.config import settings
from src.domain.recommendation.statistical_scorer import MODEL_REGISTRY, score_occupations

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
    # Story 9.5 — serve an archived version on demand (decision replay).
    served_version = body.model_version or settings.model_version
    weights = MODEL_REGISTRY.get(served_version)
    if weights is None:
        raise HTTPException(
            status_code=422,
            detail=f"Version de modèle inconnue du registre : {served_version!r}.",
        )
    scored = score_occupations(
        body.profile.model_dump(), body.occupation_ids, professions_data, weights=weights
    )
    elapsed_ms = int((time.monotonic() - start) * 1000)
    return ScoreMeResponse(
        student_id=body.student_id,
        model_version=served_version,
        scored_occupations=scored,
        computation_time_ms=elapsed_ms,
    )
