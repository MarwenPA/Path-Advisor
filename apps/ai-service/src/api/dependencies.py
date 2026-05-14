"""Reusable FastAPI dependencies.

JWT verification stub for service-to-service auth (Django -> ai-service).
Full implementation lands when the first scoring endpoint is wired.
"""

from fastapi import Header, HTTPException, status

from src.config import settings


async def verify_jwt(authorization: str | None = Header(default=None)) -> dict[str, str]:
    """No-op JWT verification in Story 1.1 — returns an empty claim set.

    Story 3.1 will activate real HS256 verification using `settings.jwt_secret`.
    """
    _ = settings  # Touch settings so import-time errors surface during tests.
    if authorization is not None and not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header")
    return {}
