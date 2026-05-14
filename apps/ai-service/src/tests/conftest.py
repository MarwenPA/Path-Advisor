"""Test environment bootstrap — provides required env vars before settings load."""

import os

# pydantic-settings reads `jwt_secret` as `AI_SERVICE_JWT_SECRET` (env_prefix).
# No default in Settings → must be set before `src.config` is imported.
os.environ.setdefault("AI_SERVICE_JWT_SECRET", "test-only-jwt-secret-not-real")
