"""Pydantic v2 schemas for ai-service API contracts.

All field names use snake_case to match the project-wide convention
(implementation-patterns-consistency-rules §Naming Patterns).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class BulletinSummary(BaseModel):
    average: float | None = None
    appreciation_keywords: list[str] = []


class StudentProfile(BaseModel):
    passions: list[str] = []
    valeurs: list[str] = []
    niveau: str
    specialites: list[str] = []
    has_bulletins: bool = False
    bulletin_summary: BulletinSummary | None = None


class ScoreMeRequest(BaseModel):
    student_id: str
    profile: StudentProfile
    occupation_ids: list[str]


class SignalContributif(BaseModel):
    signal: str
    weight: float
    contribution: int


class OccupationScore(BaseModel):
    occupation_id: str
    score: int
    signals_contributifs: list[SignalContributif]
    confidence_level: Literal["low", "medium", "high"]


class ScoreMeResponse(BaseModel):
    student_id: str
    model_version: str
    scored_occupations: list[OccupationScore]
    computation_time_ms: int


class ModelVersionResponse(BaseModel):
    model_version: str
    model_type: str
    deployed_at: datetime
    features: list[str]


class HealthResponse(BaseModel):
    status: str
    version: str
    model_version: str
