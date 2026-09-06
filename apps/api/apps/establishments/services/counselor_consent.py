"""Counselor consent — Story 6.7.

A counselor must have an explicit, non-revoked `granted` `CounselorConsent`
before viewing a student's individual profile (Story 6.8). This module owns
the request/decide/require lifecycle; `apps.profiles.access_list.sources.
counselor_consent.CounselorConsentSource` is the read/revoke adapter that
surfaces granted consents in the student's unified access list (Story 6.11).
"""

from __future__ import annotations

import logging

from django.utils import timezone

from apps.accounts.models import User
from apps.audit.decorators import record_audit
from apps.audit.models import AuditResult
from apps.core.rls import bypass_rls
from apps.establishments.exceptions import (
    ConsentAlreadyDecided,
    ConsentCooldownActive,
    ConsentNotGranted,
)
from apps.establishments.models import CounselorConsent, CounselorConsentStatus

log = logging.getLogger(__name__)


def request_consent(*, counselor: User, student: User, cohort_id: str) -> CounselorConsent:
    """AC — counselor asks a student for consent. Idempotent-ish: re-asks
    reuse the same row. Raises `ConsentCooldownActive` if the student
    refused within the last 7 days."""
    consent, _ = CounselorConsent.objects.get_or_create(
        student=student,
        counselor=counselor,
        defaults={"cohort_id": cohort_id, "status": CounselorConsentStatus.PENDING},
    )
    if consent.cooldown_active:
        raise ConsentCooldownActive()
    if consent.status != CounselorConsentStatus.GRANTED:
        consent.status = CounselorConsentStatus.PENDING
        consent.requested_at = timezone.now()
        consent.decided_at = None
        consent.revoked_at = None
        consent.save(update_fields=["status", "requested_at", "decided_at", "revoked_at"])
    try:
        from apps.establishments.services.emails import send_counselor_consent_requested

        send_counselor_consent_requested(student=student, counselor=counselor)
    except Exception:
        log.warning(
            "establishments.consent_requested.notify_failed",
            extra={"consent_id": consent.id},
            exc_info=True,
        )
    return consent


def list_pending_consent_requests(*, student: User) -> list[CounselorConsent]:
    """AC — the student's own pending requests, to render the ConsentDialog.

    `bypass_rls` after the `student=` scoping (the sole authorization
    source) — a student's own RLS session can't see the *counselor*'s
    `users` row, which would silently turn `select_related("counselor")`'s
    JOIN into zero rows on real Postgres (same class of bug already hit and
    fixed in Stories 5.6/5.7/5.9 — SQLite doesn't enforce RLS so this only
    shows up against a real Postgres backend).
    """
    with bypass_rls(reason="counselor_consent.list_pending_consent_requests"):
        return list(
            CounselorConsent.objects.filter(
                student=student, status=CounselorConsentStatus.PENDING
            ).select_related("counselor", "cohort")
        )


def decide_consent(*, student: User, consent_id: str, granted: bool) -> CounselorConsent:
    """AC — the student accepts or refuses. Scoped to `student=student` so a
    student can never decide someone else's request (404, via `.get()`
    raising `DoesNotExist` — caller uses `get_object_or_404`). Same
    `bypass_rls`-after-scoping rationale as `list_pending_consent_requests`.
    """
    with bypass_rls(reason="counselor_consent.decide_consent"):
        consent = CounselorConsent.objects.select_related("counselor").get(
            id=consent_id, student=student
        )
    if consent.status != CounselorConsentStatus.PENDING:
        raise ConsentAlreadyDecided()

    consent.status = CounselorConsentStatus.GRANTED if granted else CounselorConsentStatus.REFUSED
    consent.decided_at = timezone.now()
    consent.save(update_fields=["status", "decided_at"])

    record_audit(
        action="establishments.counselor_consent_decided",
        result=AuditResult.SUCCESS,
        actor=student,
        subject_id=consent.id,
        metadata={"counselor_id": consent.counselor_id, "granted": granted},
    )
    return consent


def require_granted_consent(*, counselor: User, student_id: str) -> CounselorConsent:
    """AC — the gate `get_student_profile` (Story 6.8) calls before showing
    anything. Raises `ConsentNotGranted` (403) otherwise — the caller's
    fallback view (name + cohort + "consentement requis" flag) is built on
    top of this, not inside it."""
    consent = CounselorConsent.objects.filter(
        student_id=student_id,
        counselor=counselor,
        status=CounselorConsentStatus.GRANTED,
        revoked_at__isnull=True,
    ).first()
    if consent is None:
        raise ConsentNotGranted()
    return consent


def touch_last_accessed(consent: CounselorConsent) -> None:
    """Story 6.11 — stamp "dernière consultation", surfaced to the student
    via the access-list source adapter."""
    consent.last_accessed_at = timezone.now()
    consent.save(update_fields=["last_accessed_at"])
