"""Parental-consent service — Story 1.4.

Owns every write to the `parental_consents` table and to the linked `User.status`
field for minor accounts. Views must never touch these models directly: the audit
trail (`@audit_action`) lives here so each state transition produces exactly one
`AuditLog` row, hash-chained against the previous one (Story 1.13).

Public entry points:
    - create_parental_consent_request(student, parent_email, *, ip, user_agent)
    - record_decision(consent, decision, *, content_hash, ip, user_agent)
    - suspend_for_unresolved_consent(consent)
    - sha256_hex(value) — shared helper for the audit-log `parent_email_hash`.

The token is `secrets.token_urlsafe(32)`. 60-day TTL; multi-use (the parent can
re-open the same email link before deciding). Re-use after a decision is blocked
by `record_decision` raising `ParentalConsentAlreadyDecided`.
"""

from __future__ import annotations

import hashlib
import ipaddress
import secrets
from datetime import timedelta
from typing import Literal

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import (
    ParentalConsent,
    ParentalConsentDecision,
    User,
    UserStatus,
)
from apps.audit.decorators import audit_action
from apps.core.exceptions import ParentalConsentAlreadyDecided

Decision = Literal["granted", "refused"]

_TOKEN_BYTES = 32  # secrets.token_urlsafe → 43 base64 chars; well under the CharField(64) cap.
_CONSENT_TTL_DAYS = 60


def sha256_hex(value: str) -> str:
    """Lowercase SHA-256 hex of `value` — used for `parent_email_hash` in audit metadata."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _generate_token() -> str:
    return secrets.token_urlsafe(_TOKEN_BYTES)


def _truncate_ip(ip: str | None) -> str | None:
    """Coarsen an IPv4 to /24 or an IPv6 to /48 for forensic logging.

    Uses the stdlib `ipaddress` module so we handle the full address syntax —
    compressed IPv6 (`::1`), IPv4-mapped IPv6 (`::ffff:1.2.3.4`), zone IDs.
    Story 1.4 review §P7 / §P20: previous manual `split(":")` produced invalid
    IPv6 literals like `::1::` on compressed inputs.

    Returns None for unparseable inputs (defence in depth — forensic IP is best-
    effort, never a load-bearing field).
    """
    if not ip:
        return None
    try:
        addr = ipaddress.ip_address(ip.strip())
    except ValueError:
        return None
    if isinstance(addr, ipaddress.IPv4Address):
        return str(ipaddress.ip_network(f"{addr}/24", strict=False).network_address)
    # IPv6 (incl. IPv4-mapped): /48 prefix.
    return str(ipaddress.ip_network(f"{addr}/48", strict=False).network_address)


@audit_action(
    "parental_consent.requested",
    subject_from=lambda kwargs, ret: kwargs["student"].id,
    metadata_from=lambda kwargs, ret: {
        "parent_email_hash": sha256_hex(kwargs["parent_email"]),
        "consent_id": ret.id,
    },
)
def create_parental_consent_request(
    *,
    student: User,
    parent_email: str,
    ip: str | None = None,
    user_agent: str | None = None,
) -> ParentalConsent:
    """Create the row + return it. The transactional caller (`signals.py`) wraps both
    the User insert and this call so a failure rolls back together.

    The audit metadata uses **hashed** parent email so audit_logs (3-year retention)
    do not duplicate plain PII that lives in `parental_consents` (≤ 60-day effective use).
    """
    now = timezone.now()
    with transaction.atomic():
        consent = ParentalConsent.objects.create(
            student=student,
            parent_email=parent_email,
            token=_generate_token(),
            requested_at=now,
            expires_at=now + timedelta(days=_CONSENT_TTL_DAYS),
        )
    return consent


@audit_action(
    "parental_consent.decided",
    # Story 1.4 review §P18: prefer `ret` over `kwargs["consent"]` for fields that
    # may have been refreshed by `select_for_update()` inside the function — the
    # input arg is the pre-lock snapshot. `subject_from` and `parent_email_hash`
    # both keyed off ret keeps the audit row consistent with the row we actually
    # mutated. Falls back to kwargs only when the function raised pre-success.
    subject_from=lambda kwargs, ret: ret.student_id if ret else kwargs["consent"].student_id,
    metadata_from=lambda kwargs, ret: {
        "consent_id": (ret.id if ret else kwargs["consent"].id),
        "decision": kwargs["decision"],
        "content_hash": kwargs.get("content_hash"),
        "parent_email_hash": sha256_hex(
            ret.parent_email if ret else kwargs["consent"].parent_email
        ),
        # IP and UA are stored coarsened on the consent row itself; the audit only
        # carries the decision outcome + the hash chain proof.
    },
)
def record_decision(
    *,
    consent: ParentalConsent,
    decision: Decision,
    content_hash: str | None = None,
    client_accepted_at: timezone.datetime | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
) -> ParentalConsent:
    """Lock in a parent's grant/refuse. Idempotency is enforced — calling this on
    an already-decided or expired consent raises `ParentalConsentAlreadyDecided`.

    On grant: if the child has already verified their email, the User transitions
    to `ACTIVE`; otherwise the User waits in `pending_parental_consent` until the
    verify-email click. On refuse: User → `SUSPENDED` immediately.

    `client_accepted_at` (Story 1.4 review §P26 / D1) is the timestamp the parent's
    browser computed at confirm time. It is stored alongside the server-side
    `decided_at` for forensic clock-drift detection. We log a warning if the two
    diverge by > 5 min but do not reject — the server stamp remains authoritative.

    The transaction wraps both the consent update AND the student-status update
    so callers never observe a half-applied state.
    """
    now = timezone.now()
    with transaction.atomic():
        # Re-read under FOR UPDATE to serialize double-click races on the same token.
        consent = ParentalConsent.objects.select_for_update().get(pk=consent.pk)
        if consent.decision is not None or consent.expires_at <= now:
            raise ParentalConsentAlreadyDecided()

        consent.decision = decision
        consent.decided_at = now
        consent.client_accepted_at = client_accepted_at
        consent.content_hash = content_hash
        consent.decision_ip_truncated = _truncate_ip(ip)
        consent.decision_user_agent = (user_agent or "")[:200] or None
        consent.save(
            update_fields=[
                "decision",
                "decided_at",
                "client_accepted_at",
                "content_hash",
                "decision_ip_truncated",
                "decision_user_agent",
                "updated_at",
            ]
        )

        # §P26 — skew detection (informational; the server stamp is authoritative).
        if client_accepted_at is not None:
            skew = abs((now - client_accepted_at).total_seconds())
            if skew > 300:
                # Structlog only — not an error, just an oddity worth surfacing.
                import structlog

                structlog.get_logger(__name__).warning(
                    "parental_consent.client_clock_skew",
                    consent_id=consent.id,
                    skew_seconds=skew,
                )

        student = consent.student
        if decision == ParentalConsentDecision.GRANTED:
            if student.email_verified_at is not None:
                student.status = UserStatus.ACTIVE
                student.save(update_fields=["status", "updated_at"])
            # else: stays pending_parental_consent until email is verified (cf. AC3).
        else:
            # refused → suspend immediately (soft-suspended; not deleted).
            student.status = UserStatus.SUSPENDED
            student.save(update_fields=["status", "updated_at"])

    return consent


@audit_action(
    "parental_consent.expired",
    subject_from=lambda kwargs, ret: kwargs["consent"].student_id,
    metadata_from=lambda kwargs, ret: {
        "consent_id": kwargs["consent"].id,
        "parent_email_hash": sha256_hex(kwargs["consent"].parent_email),
    },
)
def suspend_for_unresolved_consent(*, consent: ParentalConsent) -> User:
    """Day-60 suspension path — called from the Celery beat job (T5).

    Sets the linked User to `SUSPENDED`. The consent row stays in the DB (for
    forensics + the `/decide/` endpoint to detect the expiry and return 409).

    Wrapped in `transaction.atomic()` so the audit row and the user.status flip
    commit together (Story 1.4 review §P4) — matching the contract of
    `record_decision` above.
    """
    student = consent.student
    if student.status != UserStatus.SUSPENDED:
        with transaction.atomic():
            student.status = UserStatus.SUSPENDED
            student.save(update_fields=["status", "updated_at"])
    return student
