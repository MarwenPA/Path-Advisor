"""Shared fixtures for the GDPR-export test suite (Story 1.11).

The S3 stub is intentionally local (not `moto`) so tests stay fast and have
no external download: we only need `put_object`, `delete_object`, and
`generate_presigned_url` behaviour, all easy to fake.
"""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import patch

import pytest


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
        return (
            f"https://fake-s3.test/{Params['Bucket']}/{Params['Key']}"
            f"?X-Amz-Expires={ExpiresIn}"
        )


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
