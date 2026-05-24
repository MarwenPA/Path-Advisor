"""Celery tasks for the `accounts` app — Story 1.4 (parental consent) + Story 1.11 (GDPR export).

Two unrelated task families share this module because Celery's autodiscovery
binds `accounts.<task_name>` to whatever `apps/accounts/tasks.py` exposes:

- **Parental-consent lifecycle (Story 1.4)** — daily pull-based reminders and
  suspensions on `requested_at + N days`. Idempotent against beat drop-outs
  thanks to `reminder_sent_at IS NULL` guards.
- **GDPR Article 20 export pipeline (Story 1.11)** — `build_export` →
  `notify_export_ready` (single task: link + 30s sleep + password email) →
  nightly `expire_old_exports`. The single-task notify keeps the cleartext
  password inside one worker process, never on the broker between hops.

Discovery: registered via `app.autodiscover_tasks()` in `path_advisor/celery.py`.
"""

from __future__ import annotations

import hashlib
import io
import json
import secrets
import time
from datetime import timedelta
from smtplib import SMTPException
from types import SimpleNamespace
from typing import Any

import pyzipper
import structlog
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
)
from botocore.exceptions import (
    ConnectionError as BotoConnectionError,
)
from celery import shared_task
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from apps.accounts.exporters import ExporterEntry, iter_exporters
from apps.accounts.models import (
    GdprExportRequest,
    GdprExportStatus,
    ParentalConsent,
    ParentalConsentDecision,
    User,
    UserStatus,
)
from apps.accounts.services.gdpr_service import gdpr_s3_client
from apps.accounts.services.parental_consent import suspend_for_unresolved_consent
from apps.accounts.services.parental_consent_email import (
    send_expired_to_child,
    send_granted_to_child,
    send_reminder_to_parent,
)
from apps.audit.decorators import record_audit
from apps.audit.models import AuditResult
from apps.core.rls import with_system_actor

log = structlog.get_logger(__name__)


# ============================================================================
#  Story 1.4 — Parental consent lifecycle
# ============================================================================

# Reminder threshold from Story 1.4 §AC6. Centralised as a constant so tests can
# monkey-patch — `time_machine`/`freezegun` is the preferred path. The 60-day
# suspension threshold is baked into `ParentalConsent.expires_at` at insertion
# (`_default_parental_consent_expires_at`), so the suspend task queries on
# `expires_at__lte=now()` directly — see §P13.
_REMINDER_AFTER_DAYS = 30


@shared_task(name="accounts.send_parental_consent_reminders")
def send_parental_consent_reminders() -> int:
    """Reminder dispatch — runs daily at 04:00 UTC (cf. path_advisor.celery beat).

    Returns the number of reminders sent so the task's success row in Celery flower /
    structlog is queryable. The DB write happens **after** the SMTP send completes:
    if mail dispatch raises, `reminder_sent_at` stays NULL and the next run retries.
    """
    cutoff = timezone.now() - timedelta(days=_REMINDER_AFTER_DAYS)

    # Story 1.8 D4: Celery has no `request.user`; without the audited bypass,
    # the RLS policies deny every SELECT / UPDATE on `parental_consents` and
    # the join with `users` via `select_related`.
    with with_system_actor(reason="parental_consent.send_reminders"):
        pending = ParentalConsent.objects.filter(
            decision__isnull=True,
            reminder_sent_at__isnull=True,
            requested_at__lte=cutoff,
            expires_at__gt=timezone.now(),
        ).select_related("student")

        sent = 0
        for consent in pending:
            try:
                if send_reminder_to_parent(consent):
                    consent.reminder_sent_at = timezone.now()
                    consent.save(update_fields=["reminder_sent_at", "updated_at"])
                    sent += 1
            except Exception:
                log.exception("parental_consent.reminder_failed", consent_id=consent.id)
                continue

    log.info("parental_consent.reminders_sent", count=sent)
    return sent


@shared_task(name="accounts.suspend_unresolved_parental_consents")
def suspend_unresolved_parental_consents() -> int:
    """Suspend `pending_parental_consent` users whose 60-day window has expired.

    Idempotent: skips users already in `SUSPENDED` state. Returns the number of
    user accounts flipped — important for the Celery beat structlog summary.
    """
    now = timezone.now()

    # Story 1.8 D4: requires the audited system actor — touches both
    # `parental_consents` (SELECT) and `users` (UPDATE via the suspend service +
    # role-change which is also gated by the anti-escalation trigger; the
    # `actor_role='system'` GUC lets the trigger through).
    with with_system_actor(reason="parental_consent.suspend_unresolved"):
        expired = ParentalConsent.objects.filter(
            decision__isnull=True,
            expires_at__lte=now,
        ).select_related("student")

        suspended_count = 0
        for consent in expired:
            student = consent.student
            if student.status == UserStatus.SUSPENDED:
                continue
            try:
                suspend_for_unresolved_consent(consent=consent)
                send_expired_to_child(student)
                suspended_count += 1
            except Exception:
                log.exception(
                    "parental_consent.suspend_failed",
                    consent_id=consent.id,
                    user_id=student.id,
                )
                continue

    log.info("parental_consent.suspended", count=suspended_count)
    return suspended_count


@shared_task(name="accounts.notify_unconfirmed_granted_consents")
def notify_unconfirmed_granted_consents() -> int:
    """Resend the "granted" child email for rows where SMTP failed (Story 1.4 §P14).

    The synchronous `/decide/` POST stamps `notification_sent_at` only on
    successful SMTP send. This hourly reconciliation closes the gap when the
    parent has clicked "Autoriser" but the child never got the confirmation.
    """
    with with_system_actor(reason="parental_consent.notify_unconfirmed_granted"):
        rows = ParentalConsent.objects.filter(
            decision=ParentalConsentDecision.GRANTED,
            notification_sent_at__isnull=True,
        ).select_related("student")

        sent = 0
        for consent in rows:
            try:
                if send_granted_to_child(consent.student):
                    consent.notification_sent_at = timezone.now()
                    consent.save(update_fields=["notification_sent_at", "updated_at"])
                    sent += 1
            except Exception:
                log.exception("parental_consent.grant_notify_failed", consent_id=consent.id)
                continue

    log.info("parental_consent.grant_notifications_sent", count=sent)
    return sent


# ============================================================================
#  Story 1.11 — GDPR Article 20 export pipeline
# ============================================================================

SCHEMA_VERSION = "1.0"

# Sentinel "actor" for system-triggered audit rows (Story 1.11 post-review D3).
# `record_audit` reads `.id` and `.role` from this object — actor_id=None means
# "no human", actor_role="system" makes the DPO filter explicit.
_SYSTEM_ACTOR = SimpleNamespace(id=None, role="system")

# Narrow retryable email exceptions — programming bugs (TemplateDoesNotExist,
# KeyError) must NOT be retried with the password in kwargs (Story 1.11
# post-review patch).
_EMAIL_RETRY_EXC = (SMTPException, ConnectionError, TimeoutError, OSError)

README_BODY = """\
Path-Advisor — Export RGPD (Article 20)
=======================================

Cet export contient l'intégralité de tes données personnelles détenues par
Path-Advisor au moment de la génération.

Fichiers inclus :
- profile/profile.json       — ton profil utilisateur (rôle, email, dates)
- audit/audit-log.jsonl      — l'historique des accès à tes données
- manifest.json              — description technique de cet export
- (autres dossiers selon les fonctionnalités que tu as utilisées)

Format : JSON / JSON Lines UTF-8, conformes Article 20 RGPD
(structuré, machine-readable, communément utilisé).

Pour toute question : dpo@path-advisor.fr
"""


# --- BUILD -----------------------------------------------------------------


@shared_task(
    name="gdpr.build_export",
    bind=True,
    soft_time_limit=settings.GDPR_EXPORT_TASK_HARD_TIMEOUT_SECONDS - 60,
    time_limit=settings.GDPR_EXPORT_TASK_HARD_TIMEOUT_SECONDS,
)
def build_export(self, export_id: str) -> dict[str, Any]:
    """Assemble the encrypted ZIP, upload to S3, transition `pending → ready`."""
    # Story 1.8 D4: Celery has no request actor — wrap the whole body in the
    # audited system bypass so `User.objects.get(pk=user_id)` and exporters
    # that read `users` (e.g., audit-log exporter) pass through RLS.
    # `gdpr_export_requests` is itself NOT under RLS (no FORCE), but the
    # exporters touch protected tables.
    with with_system_actor(
        reason="gdpr.build_export",
        metadata={"export_id": export_id},
    ):
        return _build_export_impl(export_id)


def _build_export_impl(export_id: str) -> dict[str, Any]:
    try:
        export = GdprExportRequest.objects.get(pk=export_id)
    except GdprExportRequest.DoesNotExist:
        log.warning("gdpr.build_export.missing", export_id=export_id)
        return {"skipped": "missing"}

    # Idempotence: only pick up `pending`. A second run on `in_progress`/`ready`/
    # `failed` becomes a no-op so retries do not double-write.
    if export.status != GdprExportStatus.PENDING:
        log.info(
            "gdpr.build_export.skipped",
            export_id=export.id,
            current_status=export.status,
        )
        return {"skipped": export.status}

    export.status = GdprExportStatus.IN_PROGRESS
    export.started_at = timezone.now()
    export.save(update_fields=["status", "started_at"])

    try:
        user = User.objects.get(pk=export.user_id)
    except User.DoesNotExist:
        _mark_failed(export, code="gdpr.user_missing", message="User account no longer exists.")
        return {"failed": "user_missing"}

    archive_s3_key: str | None = None
    try:
        password = secrets.token_urlsafe(24)
        archive_bytes, manifest, errors_per_domain = _build_zip(user=user, password=password)
        sha256 = hashlib.sha256(archive_bytes).hexdigest()
        archive_s3_key = f"gdpr-exports/{user.id}/{export.id}.zip"

        s3 = gdpr_s3_client()
        s3.put_object(
            Bucket=settings.GDPR_EXPORTS_BUCKET,
            Key=archive_s3_key,
            Body=archive_bytes,
            ContentType="application/zip",
            ServerSideEncryption="AES256",
            Metadata={
                "export_id": export.id,
                "user_id": user.id,
                "schema_version": SCHEMA_VERSION,
            },
        )

        now = timezone.now()
        export.status = GdprExportStatus.READY
        export.ready_at = now
        export.expires_at = now + timedelta(days=settings.GDPR_EXPORT_VALIDITY_DAYS)
        export.archive_s3_key = archive_s3_key
        export.archive_sha256 = sha256
        export.archive_size_bytes = len(archive_bytes)
        export.password_hash = make_password(password)
        export.save(
            update_fields=[
                "status",
                "ready_at",
                "expires_at",
                "archive_s3_key",
                "archive_sha256",
                "archive_size_bytes",
                "password_hash",
            ],
        )

        record_audit(
            action="gdpr.export_ready",
            result=AuditResult.SUCCESS,
            actor=_SYSTEM_ACTOR,
            subject_id=user.id,
            metadata={
                "export_id": export.id,
                "size_bytes": len(archive_bytes),
                "domains": [d["name"] for d in manifest["domains"]],
                "exporter_errors": errors_per_domain,
            },
        )

        # `notify_export_ready` is a Celery task — `.delay()` may itself raise
        # on broker outage. In that case we still ack the build (the ZIP is
        # in S3 and the DB row is READY) but Sentry-flag the missed email.
        try:
            notify_export_ready.delay(export_id=export.id, password=password)
        except Exception as dispatch_exc:
            log.error(
                "gdpr.notify_dispatch_failed",
                export_id=export.id,
                error=str(dispatch_exc),
                exc_info=True,
            )

        return {
            "export_id": export.id,
            "size_bytes": len(archive_bytes),
            "key": archive_s3_key,
            "sha256": sha256,
        }

    except Exception as exc:
        # Sanitize the error message: only the exception CLASS NAME persists.
        # Raw `str(exc)` can carry S3 endpoints, region, bucket paths, partial
        # secrets — all of which leak via the serializer + failure email
        # (post-review patch).
        code = "gdpr.build_failed"
        _mark_failed(
            export,
            code=code,
            message=f"{exc.__class__.__name__}: see Sentry for details.",
            archive_s3_key_to_purge=archive_s3_key,
        )
        log.error(
            "gdpr.build_export.failed",
            export_id=export.id,
            error_type=exc.__class__.__name__,
            error=str(exc),
            exc_info=True,
        )
        try:
            send_gdpr_export_failed_email.delay(export_id=export.id)
        except Exception:
            log.warning("gdpr.notify_failed_email_dispatch_failed", export_id=export.id)
        return {"failed": code}


def _build_zip(*, user: User, password: str) -> tuple[bytes, dict[str, Any], dict[str, str]]:
    """Build the in-memory AES-256 encrypted ZIP and return (bytes, manifest, errors).

    Streaming-to-disk is deferred until Story 2.3 ships an exporter heavy enough
    to OOM the worker (cf. deferred-work code review 2026-05-24).
    """
    buf = io.BytesIO()
    files: list[dict[str, Any]] = []
    domains_summary: list[dict[str, Any]] = []
    errors_per_domain: dict[str, str] = {}

    with pyzipper.AESZipFile(
        buf,
        mode="w",
        compression=pyzipper.ZIP_DEFLATED,
        encryption=pyzipper.WZ_AES,
    ) as zf:
        zf.setpassword(password.encode("utf-8"))

        # README.txt — always included, before any data, so the user sees it
        # in the file listing of every ZIP viewer.
        readme_bytes = README_BODY.encode("utf-8")
        zf.writestr("README.txt", readme_bytes)
        files.append(
            {
                "path": "README.txt",
                "size_bytes": len(readme_bytes),
                "sha256": hashlib.sha256(readme_bytes).hexdigest(),
            }
        )

        for domain, exporter_fn in iter_exporters():
            entries_count = 0
            try:
                for entry in exporter_fn(user):
                    if not isinstance(entry, ExporterEntry):
                        # Defensive: a misimplemented exporter yielding wrong types
                        # must not corrupt the archive. Skip and record an error.
                        raise TypeError(
                            f"Exporter '{domain}' yielded {type(entry).__name__}, "
                            "expected ExporterEntry."
                        )
                    zf.writestr(entry.archive_path, entry.content)
                    files.append(
                        {
                            "path": entry.archive_path,
                            "size_bytes": len(entry.content),
                            "sha256": hashlib.sha256(entry.content).hexdigest(),
                        }
                    )
                    entries_count += 1
                domains_summary.append({"name": domain, "entries": entries_count, "errors": 0})
            except Exception as exc:
                # One exporter failing does not abort the whole export — the
                # remaining domains keep their data. The error is recorded both
                # in the ZIP (errors/<domain>.error.txt) and in the manifest.
                errors_per_domain[domain] = exc.__class__.__name__
                err_bytes = (
                    f"Exporter '{domain}' failed: {exc.__class__.__name__}\n"
                    "Contact dpo@path-advisor.fr if this happens repeatedly.\n"
                ).encode()
                zf.writestr(f"errors/{domain}.error.txt", err_bytes)
                files.append(
                    {
                        "path": f"errors/{domain}.error.txt",
                        "size_bytes": len(err_bytes),
                        "sha256": hashlib.sha256(err_bytes).hexdigest(),
                    }
                )
                domains_summary.append({"name": domain, "entries": entries_count, "errors": 1})
                log.warning("gdpr.exporter_failed", domain=domain, error=str(exc))

        # Manifest is written LAST so its `files` list reflects every other
        # entry above (excluding itself).
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "format": ("ISO Article 20 RGPD — structured, machine-readable, commonly used"),
            "user_id": user.id,
            "generated_at": timezone.now().isoformat(),
            "domains": domains_summary,
            "files": files,
        }
        manifest_bytes = json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True).encode(
            "utf-8"
        )
        zf.writestr("manifest.json", manifest_bytes)

    return buf.getvalue(), manifest, errors_per_domain


def _mark_failed(
    export: GdprExportRequest,
    *,
    code: str,
    message: str,
    archive_s3_key_to_purge: str | None = None,
) -> None:
    """Transition to `failed` and best-effort purge any orphan S3 object.

    `message` MUST already be sanitized — only class names / safe codes belong
    here (post-review patch — `str(exc)` leaked boto endpoint/region/path).

    If `archive_s3_key_to_purge` is set, we attempt to delete it before
    marking the row failed. Without this cleanup, a put_object that succeeds
    followed by a save() that raises orphans the encrypted archive on S3 —
    direct GDPR Art. 5(1)(e) storage-limitation breach (post-review patch).
    """
    if archive_s3_key_to_purge:
        try:
            gdpr_s3_client().delete_object(
                Bucket=settings.GDPR_EXPORTS_BUCKET,
                Key=archive_s3_key_to_purge,
            )
        except Exception as cleanup_exc:
            # Log + Sentry but do not block the failure transition — orphan
            # cleanup can be retried manually via the DPO runbook.
            log.error(
                "gdpr.mark_failed.s3_orphan_cleanup_failed",
                export_id=export.id,
                key=archive_s3_key_to_purge,
                error=str(cleanup_exc),
                exc_info=True,
            )

    export.status = GdprExportStatus.FAILED
    export.error_code = code
    export.error_message = message
    export.save(update_fields=["status", "error_code", "error_message"])
    record_audit(
        action="gdpr.export_failed",
        result=AuditResult.FAILURE,
        actor=_SYSTEM_ACTOR,
        subject_id=export.user_id,
        metadata={"export_id": export.id, "error_code": code},
    )


# --- NOTIFY  (single task — keeps password OFF the broker between hops) ---


@shared_task(
    name="gdpr.notify_export_ready",
    autoretry_for=_EMAIL_RETRY_EXC,
    max_retries=3,
    default_retry_delay=60,
    retry_backoff=True,
)
def notify_export_ready(*, export_id: str, password: str) -> dict[str, Any]:
    """Send link email, sleep 30s, send password email — all in one worker process.

    Single-task design (Story 1.11 post-review decision D1): the cleartext
    password is an argument of THIS task only. It never moves to a follow-up
    task, so it sits in the broker for the in-flight time of this task and is
    discarded on ACK. Retries on the narrow `_EMAIL_RETRY_EXC` keep that
    window bounded.
    """
    # Story 1.8 D4: needs system actor to SELECT `users` for the email lookup.
    with with_system_actor(
        reason="gdpr.notify_export_ready",
        metadata={"export_id": export_id},
    ):
        return _notify_export_ready_impl(export_id, password)


def _notify_export_ready_impl(export_id: str, password: str) -> dict[str, Any]:
    try:
        export = GdprExportRequest.objects.get(pk=export_id)
    except GdprExportRequest.DoesNotExist:
        return {"skipped": "missing"}

    if export.status != GdprExportStatus.READY:
        return {"skipped": export.status}

    # Idempotence guard — set BEFORE the first email goes out. On retry,
    # `emails_sent_at is not None` short-circuits us before any second send.
    # (Post-review patch — previously set AFTER apply_async, opening a window
    # for duplicate link emails on partial failure.)
    if export.emails_sent_at is not None:
        return {"skipped": "already_sent"}

    user = User.objects.filter(pk=export.user_id).only("email").first()
    if user is None or not user.email:
        # Silent strand: audit + Sentry so the DPO can intervene
        # (post-review patch — previously logged warning only).
        log.error(
            "gdpr.notify_export_ready.no_email",
            export_id=export.id,
            user_id=export.user_id,
        )
        record_audit(
            action="gdpr.notify_skipped",
            result=AuditResult.FAILURE,
            actor=_SYSTEM_ACTOR,
            subject_id=export.user_id,
            metadata={"export_id": export.id, "reason": "no_email"},
        )
        try:
            import sentry_sdk

            sentry_sdk.capture_message(
                f"gdpr.notify_skipped: export {export.id} ready but user has no email",
                level="error",
            )
        except Exception:
            log.warning("gdpr.sentry_capture_failed", export_id=export.id)
        return {"skipped": "no_email"}

    # Reserve the idempotence slot BEFORE the first send. If the link email
    # fails, autoretry hits the guard at the top and skips — no duplicate send.
    GdprExportRequest.objects.filter(pk=export.id).update(emails_sent_at=timezone.now())

    _send_gdpr_email(
        subject="[Path-Advisor] Ton export RGPD est prêt",
        template="accounts/email/gdpr_export_ready",
        to=user.email,
        context={
            "export": export,
            "expires_at": export.expires_at,
        },
    )

    # In-process gap so the password email doesn't land in the same Gmail
    # conversation / push notification batch as the link email.
    time.sleep(30)

    _send_gdpr_email(
        subject="[Path-Advisor] Mot de passe de ton export RGPD",
        template="accounts/email/gdpr_export_password",
        to=user.email,
        context={"export": export, "password": password},
    )

    return {"sent": "link+password"}


@shared_task(
    name="gdpr.send_gdpr_export_failed_email",
    autoretry_for=_EMAIL_RETRY_EXC,
    max_retries=3,
    default_retry_delay=60,
    retry_backoff=True,
)
def send_gdpr_export_failed_email(*, export_id: str) -> dict[str, Any]:
    # Story 1.8 D4: SELECT on `users` requires system actor bypass.
    with with_system_actor(
        reason="gdpr.send_failed_email",
        metadata={"export_id": export_id},
    ):
        try:
            export = GdprExportRequest.objects.get(pk=export_id)
        except GdprExportRequest.DoesNotExist:
            return {"skipped": "missing"}

        user = User.objects.filter(pk=export.user_id).only("email").first()
        if user is None or not user.email:
            return {"skipped": "no_email"}

        _send_gdpr_email(
            subject="[Path-Advisor] Ton export RGPD a échoué",
            template="accounts/email/gdpr_export_failed",
            to=user.email,
            context={"export": export},
        )
    return {"sent": "failed"}


def _send_gdpr_email(
    *,
    subject: str,
    template: str,
    to: str,
    context: dict[str, Any],
) -> None:
    html_body = render_to_string(f"{template}.html", context)
    text_body = render_to_string(f"{template}.txt", context)
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)


# --- EXPIRE ----------------------------------------------------------------


# Concrete S3-side exceptions we know how to handle gracefully during the
# nightly sweep. Anything else still bubbles to the worker logs.
_S3_EXPIRE_EXC = (BotoCoreError, ClientError, BotoConnectionError)


@shared_task(name="gdpr.expire_old_exports")
def expire_old_exports() -> dict[str, Any]:
    """Move `ready` exports past `expires_at` to `expired` and purge S3 objects.

    Idempotent: runs nightly via beat. A second run within the same day finds
    no `ready` rows and no-ops.
    """
    now = timezone.now()
    expired_count = 0
    # Materialise the id list up-front so server-side cursor semantics don't
    # interact with the in-loop saves (post-review patch — `iterator()` while
    # mutating the same queryset was risky).
    expired_ids = list(
        GdprExportRequest.objects.filter(
            status=GdprExportStatus.READY,
            expires_at__lt=now,
        )
        .order_by("expires_at")
        .values_list("pk", flat=True)
    )

    s3 = gdpr_s3_client()
    for export_id in expired_ids:
        export = GdprExportRequest.objects.filter(pk=export_id).first()
        if export is None or export.status != GdprExportStatus.READY:
            continue
        # Purge S3 first — if it fails, we leave the DB row as `ready` and the
        # next nightly run will retry. Otherwise we'd lose the S3 reference.
        if export.archive_s3_key:
            try:
                s3.delete_object(
                    Bucket=settings.GDPR_EXPORTS_BUCKET,
                    Key=export.archive_s3_key,
                )
            except _S3_EXPIRE_EXC as exc:
                log.warning(
                    "gdpr.expire_old_exports.s3_delete_failed",
                    export_id=export.id,
                    key=export.archive_s3_key,
                    error=str(exc),
                )
                continue
            except Exception as exc:
                # Unknown error — same conservative bail-out as boto failures.
                log.warning(
                    "gdpr.expire_old_exports.s3_delete_unexpected",
                    export_id=export.id,
                    key=export.archive_s3_key,
                    error_type=exc.__class__.__name__,
                    error=str(exc),
                )
                continue

        export.status = GdprExportStatus.EXPIRED
        downloaded = export.download_count > 0
        export.archive_s3_key = None
        export.manifest_s3_key = None
        export.archive_size_bytes = None
        export.save(
            update_fields=[
                "status",
                "archive_s3_key",
                "manifest_s3_key",
                "archive_size_bytes",
            ]
        )

        record_audit(
            action="gdpr.export_expired",
            result=AuditResult.SUCCESS,
            actor=_SYSTEM_ACTOR,
            subject_id=export.user_id,
            metadata={"export_id": export.id, "downloaded": downloaded},
        )
        expired_count += 1

    log.info("gdpr.expire_old_exports.completed", expired_count=expired_count)
    return {"expired": expired_count}


# ============================================================================
#  Story 1.12 — Account deletion sweep (GDPR Article 17, right to erasure)
# ============================================================================


@shared_task(
    name="accounts.sweep_account_deletions",
    soft_time_limit=600,
    time_limit=900,
)
def sweep_account_deletions() -> dict[str, Any]:
    """Daily beat sweep — hard-deletes accounts past their 30-day grace window.

    Idempotent: a second run on the same day picks up zero new rows because
    `hard_deleted_at` becomes non-null after each successful row. The
    `hard_delete_attempt_count` cap (default 7) guards against retry storms
    on permanently broken S3 buckets — after the cap fires, the row is
    surfaced via a `gdpr.account_hard_delete_giving_up` audit row and skipped
    in subsequent sweeps.

    Cf. Story 1.12 §AC6 for the per-row state machine.
    """
    # Local imports — keep the module load light, the model + service are
    # heavy at import (Django model registry + boto3).
    from django.conf import settings

    from apps.accounts.models import AccountDeletionRequest
    from apps.accounts.services import account_deletion as deletion_service

    now = timezone.now()
    max_attempts = getattr(settings, "GDPR_ACCOUNT_DELETION_MAX_HARD_DELETE_ATTEMPTS", 7)

    # Materialise the id list up-front so server-side cursor semantics don't
    # interact with the per-row commits inside the loop. Same pattern as
    # `expire_old_exports` (Story 1.11 review patch — `iterator()` while
    # mutating the same queryset was risky).
    candidate_ids = list(
        AccountDeletionRequest.objects.filter(
            cancelled_at__isnull=True,
            hard_deleted_at__isnull=True,
            hard_delete_after__lte=now,
            hard_delete_attempt_count__lt=max_attempts,
        )
        .order_by("hard_delete_after")
        .values_list("pk", flat=True)
    )

    log.info(
        "accounts.sweep_started",
        candidate_count=len(candidate_ids),
        max_attempts=max_attempts,
    )

    processed = 0
    failed = 0
    gave_up = 0

    for request_id in candidate_ids:
        # Re-fetch outside the service's atomic block — the service does its
        # own SELECT FOR UPDATE. We just need the latest snapshot to decide
        # whether to even call it.
        request = AccountDeletionRequest.objects.filter(pk=request_id).first()
        if request is None:
            continue
        if request.cancelled_at is not None or request.hard_deleted_at is not None:
            # Cancelled or hard-deleted between candidate-selection and now.
            continue

        try:
            result = deletion_service.hard_delete(request)
            processed += 1
            log.info(
                "accounts.hard_delete_completed",
                deletion_request_id=request_id,
                result=result,
            )
        except Exception as exc:
            # Sanitise — only the exception class name persists on disk; raw
            # `str(exc)` can carry boto endpoints / paths (Story 1.11 review
            # patch §319-342).
            error_code = exc.__class__.__name__
            log.error(
                "accounts.hard_delete_failed",
                deletion_request_id=request_id,
                error_type=error_code,
                exc_info=True,
            )
            failed += 1

            # Increment the attempt counter outside the service's transaction
            # (it rolled back). Story 1.12 code review §P9: use an atomic
            # F-expression so two concurrent sweep workers can't both read
            # the same `original+0` and both write `original+1` (silently
            # undercounting toward the cap). The defensive `refresh_from_db`
            # captures the post-update value for the subsequent comparison.
            from django.db.models import F

            AccountDeletionRequest.objects.filter(pk=request.pk).update(
                hard_delete_attempt_count=F("hard_delete_attempt_count") + 1,
                last_failure_code=error_code[:50],
            )
            try:
                request.refresh_from_db()
            except AccountDeletionRequest.DoesNotExist:
                # Manual DB intervention removed the row mid-sweep; benign.
                continue

            # Failure audit row OUTSIDE the rolled-back transaction so it
            # actually persists (Story 1.11 _mark_failed pattern).
            record_audit(
                action="gdpr.account_hard_delete_failed",
                result=AuditResult.FAILURE,
                actor=_SYSTEM_ACTOR,
                subject_id=request.user_id_snapshot,
                metadata={
                    "deletion_request_id": request.id,
                    "error_code": error_code,
                    "attempt": request.hard_delete_attempt_count,
                },
            )

            # If we just crossed the cap, write a separate giving-up row so
            # the DPO inbox surfaces frozen rows during the next inspection.
            # Story 1.12 code review §P9: use `==` instead of `>=` so a
            # concurrent second sweep that pushed the counter past the cap
            # does NOT also write a duplicate `_giving_up` row. The sweep's
            # candidate filter `__lt=max_attempts` then naturally excludes
            # the row from subsequent runs.
            if request.hard_delete_attempt_count == max_attempts:
                gave_up += 1
                record_audit(
                    action="gdpr.account_hard_delete_giving_up",
                    result=AuditResult.FAILURE,
                    actor=_SYSTEM_ACTOR,
                    subject_id=request.user_id_snapshot,
                    metadata={
                        "deletion_request_id": request.id,
                        "max_attempts": max_attempts,
                        "last_failure_code": error_code,
                    },
                )
                log.error(
                    "accounts.hard_delete_giving_up",
                    deletion_request_id=request.id,
                    max_attempts=max_attempts,
                )

    log.info(
        "accounts.sweep_completed",
        processed_count=processed,
        failed_count=failed,
        gave_up_count=gave_up,
    )
    return {
        "candidates": len(candidate_ids),
        "processed": processed,
        "failed": failed,
        "gave_up": gave_up,
    }
