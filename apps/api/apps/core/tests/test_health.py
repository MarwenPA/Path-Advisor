"""Smoke test for the /api/v1/health/ endpoint."""

from rest_framework import status
from rest_framework.test import APIClient


def test_health_endpoint_returns_ok() -> None:
    client = APIClient()
    response = client.get("/api/v1/health/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}
