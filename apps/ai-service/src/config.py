"""Runtime configuration for the ai-service, loaded from env vars."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Single source of truth for environment-driven config.

    `jwt_secret` has no default — every consumer must supply `AI_SERVICE_JWT_SECRET`
    (mapped via `env_prefix="AI_SERVICE_"`). Local dev reads it from `.env` /
    `.env.example`; CI sets it in the workflow; prod via secret manager.
    """

    model_config = SettingsConfigDict(env_file=".env", env_prefix="AI_SERVICE_", extra="ignore")

    app_version: str = "0.1.0"
    jwt_secret: str
    jwt_ttl_seconds: int = 300
    jwt_algorithm: str = "HS256"


settings = Settings()  # type: ignore[call-arg]  # populated from env
