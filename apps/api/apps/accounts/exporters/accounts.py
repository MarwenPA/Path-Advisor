"""Account-level exporter: the user's profile JSON."""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import TYPE_CHECKING

from apps.accounts.exporters import ExporterEntry, register_exporter

if TYPE_CHECKING:
    from apps.accounts.models import User


@register_exporter("accounts")
def export_account_profile(user: User) -> Iterable[ExporterEntry]:
    """Yield a single `profile/profile.json` document."""
    profile = {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "birth_date": user.birth_date.isoformat() if user.birth_date else None,
        "status": user.status,
        "email_verified_at": (
            user.email_verified_at.isoformat() if user.email_verified_at else None
        ),
        "consent_rgpd_at": (
            user.consent_rgpd_at.isoformat() if user.consent_rgpd_at else None
        ),
        "consent_cgu_version": user.consent_cgu_version,
        "tenant_id": str(user.tenant_id) if user.tenant_id else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }
    yield ExporterEntry(
        archive_path="profile/profile.json",
        content=json.dumps(profile, indent=2, ensure_ascii=False, sort_keys=True).encode(
            "utf-8"
        ),
        content_type="application/json",
    )
