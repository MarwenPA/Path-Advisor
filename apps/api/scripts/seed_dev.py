"""Idempotent dev seed: super-user + MinIO buckets.

Run via `make seed` from the repo root, or `uv run python scripts/seed_dev.py`.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "path_advisor.settings.local")
    api_root = Path(__file__).resolve().parent.parent
    if str(api_root) not in sys.path:
        sys.path.insert(0, str(api_root))

    import django

    django.setup()

    from django.conf import settings as django_settings

    if not django_settings.DEBUG:
        raise SystemExit(
            "Refusing to seed: DEBUG is False. This script provisions a known admin "
            "password and is only safe in local development."
        )

    _ensure_admin()
    _ensure_minio_buckets()


def _ensure_admin() -> None:
    from django.contrib.auth import get_user_model

    user_model = get_user_model()
    if user_model.objects.filter(email="admin@path-advisor.local").exists():
        print("Super-user admin@path-advisor.local already present (skip)")
        return

    # Custom User model (Story 1.3) — `username` field removed, email is the identifier.
    user_model.objects.create_superuser(
        email="admin@path-advisor.local",
        password="admin-local-dev",  # documented in README, never used in prod
    )
    print("Super-user admin@path-advisor.local created")


def _ensure_minio_buckets() -> None:
    import boto3
    from botocore.exceptions import ClientError
    from django.conf import settings

    s3 = boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )

    for bucket in ("bulletins-encrypted", "exports-gdpr", "audit-logs-archive"):
        try:
            s3.head_bucket(Bucket=bucket)
            print(f"Bucket '{bucket}' already present (skip)")
        except ClientError as exc:
            # Only "bucket not found" (404) is expected — surface every other failure
            # (403 permission denied, 5xx, transport errors, …) instead of masking them.
            status = exc.response.get("Error", {}).get("Code", "")
            if status not in {"404", "NoSuchBucket"}:
                raise
            s3.create_bucket(Bucket=bucket)
            print(f"Bucket '{bucket}' created")


if __name__ == "__main__":
    main()
