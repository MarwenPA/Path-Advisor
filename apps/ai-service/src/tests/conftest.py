"""Test environment bootstrap — provides required env vars and shared fixtures."""

from __future__ import annotations

import os
import time

import jwt
import pytest
from fastapi.testclient import TestClient

# pydantic-settings reads `jwt_secret` as `AI_SERVICE_JWT_SECRET` (env_prefix).
# No default in Settings → must be set before `src.config` is imported.
os.environ.setdefault("AI_SERVICE_JWT_SECRET", "test-only-jwt-secret-not-real-min32chars!!")

from src.main import app

TEST_SECRET = os.environ["AI_SERVICE_JWT_SECRET"]


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def auth_client() -> TestClient:
    now = int(time.time())
    token = jwt.encode(
        {"sub": "django-api", "iat": now, "exp": now + 300},
        TEST_SECRET,
        algorithm="HS256",
    )
    return TestClient(app, headers={"Authorization": f"Bearer {token}"})


@pytest.fixture
def expired_token() -> str:
    now = int(time.time())
    return jwt.encode(
        {"sub": "django-api", "iat": now - 600, "exp": now - 300},
        TEST_SECRET,
        algorithm="HS256",
    )
