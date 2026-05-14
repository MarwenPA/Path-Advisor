"""FastAPI application entrypoint."""

from fastapi import FastAPI

from src.api.routes import health

app = FastAPI(
    title="Path-Advisor AI Service",
    description="Scoring + embeddings microservice. Talks to Django via JWT-signed HTTP.",
    version="0.1.0",
)

app.include_router(health.router)
