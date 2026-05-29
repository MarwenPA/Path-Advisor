"""Shared fixtures for the accounts test suite.

Started as the GDPR-export S3 stub (Story 1.11); Story 1.5 promoted the
`_clear_ratelimit_cache` autouse fixture here from `test_account_deletion_views.py`
so every auth test stays isolated from rate-limit counter bleed (signup,
login, password-reset, account-deletion all run through django-ratelimit).
"""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _clear_ratelimit_and_login_counters():
    """Reset the in-memory cache between tests so per-test cases don't leak
    rate-limit counters OR login-failure counters (Story 1.5 lockout) into
    each other. Promoted from Story 1.12's test_account_deletion_views.py
    fixture so the full auth test suite shares one isolation guard.
    """
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


class FakeS3:
    """Minimal in-memory S3 stub that records all calls + holds objects."""

    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], dict] = {}
        self.delete_calls: list[tuple[str, str]] = []
        self.presign_calls: list[dict] = []
        self.fail_on_delete: bool = False

    def put_object(self, **kwargs):
        bucket = kwargs["Bucket"]
        key = kwargs["Key"]
        self.objects[(bucket, key)] = {
            "Body": kwargs.get("Body"),
            "ContentType": kwargs.get("ContentType"),
            "ServerSideEncryption": kwargs.get("ServerSideEncryption"),
            "Metadata": kwargs.get("Metadata", {}),
        }
        return {"ETag": "fake-etag"}

    def delete_object(self, **kwargs):
        bucket = kwargs["Bucket"]
        key = kwargs["Key"]
        self.delete_calls.append((bucket, key))
        if self.fail_on_delete:
            raise RuntimeError("simulated S3 failure")
        self.objects.pop((bucket, key), None)
        return {}

    def generate_presigned_url(self, op, *, Params, ExpiresIn):
        self.presign_calls.append({"op": op, "params": Params, "ttl": ExpiresIn})
        return f"https://fake-s3.test/{Params['Bucket']}/{Params['Key']}?X-Amz-Expires={ExpiresIn}"


@pytest.fixture
def fake_s3() -> Iterator[FakeS3]:
    """Patch `gdpr_s3_client` everywhere it is used."""
    fake = FakeS3()

    with (
        patch(
            "apps.accounts.tasks.gdpr_s3_client",
            return_value=fake,
        ),
        patch(
            "apps.accounts.views.gdpr_s3_client",
            return_value=fake,
        ),
        patch(
            "apps.accounts.services.gdpr_service.gdpr_s3_client",
            return_value=fake,
        ),
    ):
        yield fake
