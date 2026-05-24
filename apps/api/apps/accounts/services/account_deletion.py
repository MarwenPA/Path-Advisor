"""Account-deletion service — Story 1.12 (GDPR Article 17, right to erasure).

Owns every write to the `account_deletion_requests` table and to the linked
`User.status` field. Views must never touch these models directly: the audit
trail (`@audit_action`) lives here so each state transition produces exactly
one `AuditLog` row, hash-chained against the previous one (Story 1.13).

Public entry points:
    - request_deletion(*, user, password, ip, user_agent) -> AccountDeletionRequest
    - cancel_deletion(*, request, password, actor, cancel_reason) -> AccountDeletionRequest
    - hard_delete(request) -> dict[str, int]

Lifecycle (cf. Story 1.12 §AC1, §AC5, §AC6):
    [click] → soft-delete (status=DELETED, is_active=False) + 30-day grace
            → cancel (self-service via token OR DPO admin override) → restore
                                       OR
            → sweep_account_deletions Celery beat → hard_delete cascade.
"""

from __future__ import annotations

import ipaddress
import secrets
from datetime import timedelta
from types import SimpleNamespace
from typing import Any

import structlog
from django.conf import settings
from django.contrib.auth.hashers import check_password as django_check_password
from django.contrib.auth.hashers import make_password
from django.contrib.sessions.models import Session
from django.db import transaction
from django.utils import timezone

from apps.accounts.gdpr_exceptions import (
    AccountDeletionAlreadyPending,
    AccountDeletionAlreadyResolved,
    AccountDeletionExpired,
    AccountDeletionNotFound,
    InvalidPassword,
)
from apps.accounts.models import AccountDeletionRequest, User, UserStatus
from apps.audit.decorators import audit_action, record_audit
from apps.audit.models import AuditResult

log = structlog.get_logger(__name__)


# Sentinel actor for sweep-triggered audit rows. Same shape Story 1.11's tasks.py
# uses — `record_audit` reads `.id` and `.role` from this object. `actor_id=None`
# + `actor_role="system"` makes the DPO filter explicit.
_SYSTEM_ACTOR = SimpleNamespace(id=None, role="system")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _truncate_ip(ip: str | None) -> str | None:
    """Coarsen IPv4 to /24 and IPv6 to /48 — same helper shape as parental_consent."""
    if not ip:
        return None
    try:
        addr = ipaddress.ip_address(ip.strip())
    except ValueError:
        return None
    if isinstance(addr, ipaddress.IPv4Address):
        return str(ipaddress.ip_network(f"{addr}/24", strict=False).network_address)
    return str(ipaddress.ip_network(f"{addr}/48", strict=False).network_address)


def _generate_cancel_token() -> str:
    # 32 bytes → 43 base64-urlsafe chars ≈ 256 bits of entropy. Same primitive
    # ParentalConsent uses (cf. Story 1.4 _generate_token).
    return secrets.token_urlsafe(32)


def _terminate_user_sessions(user: User) -> int:
    """Delete every Django session whose payload matches this user.

    Sessions are NOT FK-linked to User (Django stores `_auth_user_id` inside the
    encoded payload), so we walk the table and decode each row. Acceptable at
    MVP scale (≤ 500 active sessions). Returns the number of sessions killed
    so the structlog summary captures it.

    A Sprint-4+ Redis session backend swap reduces this to a single SCAN+DEL;
    documented as deferred-work.
    """
    user_id_str = str(user.pk)
    killed = 0
    # Skip already-expired rows (Story 1.12 code review §P16). Iterate with a
    # chunked queryset so a large session table doesn't OOM.
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    for sess in active_sessions.iterator(chunk_size=200):
        try:
            data = sess.get_decoded()
        except Exception as exc:
            # Malformed payload (manual DB poke, expired signing key, SECRET_KEY
            # rotation) — skip, don't fail the whole deletion on one bad row.
            # Log so a flurry of decode failures surfaces in observability
            # (Story 1.12 code review §P15).
            log.warning(
                "accounts.session_decode_failed",
                session_key_prefix=(sess.session_key or "")[:6],
                error_type=exc.__class__.__name__,
            )
            continue
        if data.get("_auth_user_id") == user_id_str:
            sess.delete()
            killed += 1
    return killed


def _alert_on_silent_audit_failure(audit_row: object | None, *, request_id: str) -> None:
    """Sentry-flag silent audit-write failures during a hard-delete (Story 1.12 §D6).

    `record_audit` returns None when the audit-DB is unreachable (Story 1.13 §9 #4
    swallow contract). For account deletion that means we could wipe the user's
    data without any compliance trail. We keep the best-effort semantics
    (don't block the deletion) but alert the DPO so they can investigate.
    """
    if audit_row is not None:
        return
    log.error(
        "accounts.hard_delete.audit_write_silent_failure",
        deletion_request_id=request_id,
    )
    try:
        import sentry_sdk

        sentry_sdk.capture_message(
            f"gdpr.audit_write_returned_none for deletion {request_id}",
            level="error",
        )
    except Exception:
        log.warning("accounts.sentry_capture_failed", deletion_request_id=request_id)


def _raise_on_s3_partial_failure(resp: dict, *, bucket: str, prefix: str) -> None:
    """`delete_objects` returns 200 OK even with per-key `Errors[]` (Story 1.12 §P6).

    A partial purge is unacceptable for the deletion promise: raise so the
    sweep marks the request `failed` and retries on the next pass.
    """
    errors = resp.get("Errors") or []
    if not errors:
        return
    from botocore.exceptions import ClientError

    log.error(
        "accounts.purge_s3.partial_failure",
        bucket=bucket,
        prefix=prefix,
        error_count=len(errors),
        first_error_code=errors[0].get("Code"),
    )
    raise ClientError(
        {
            "Error": {
                "Code": "DeleteObjectsPartial",
                "Message": f"{len(errors)} keys failed to delete (first: {errors[0].get('Code')})",
            },
            "ResponseMetadata": {},
        },
        "DeleteObjects",
    )


def _purge_s3_prefixes(user_id: str) -> tuple[int, list[str]]:
    """List + bulk-delete every key under the user's prefixes across configured buckets.

    Returns (total_keys_deleted, list_of_processed_prefixes) for the audit
    metadata. Errors per bucket are caught and logged — a single broken bucket
    must not block the whole cascade.

    The list of (bucket_setting, prefix_template) tuples lives in
    `settings.GDPR_USER_OWNED_S3_PREFIXES` so future stories that add per-user
    buckets (Story 2.3 bulletins-encrypted, etc.) extend the registry without
    touching this function.
    """
    # Local import — avoids forcing boto3 at module load for unit tests that mock S3.
    import boto3
    from botocore.config import Config as BotoConfig
    from botocore.exceptions import BotoCoreError, ClientError

    prefixes = getattr(settings, "GDPR_USER_OWNED_S3_PREFIXES", [])
    if not prefixes:
        return 0, []

    s3 = boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
        config=BotoConfig(connect_timeout=5, read_timeout=30, retries={"max_attempts": 3}),
    )

    total = 0
    processed: list[str] = []
    for bucket_setting, prefix_template in prefixes:
        bucket = getattr(settings, bucket_setting, None)
        if not bucket:
            log.warning(
                "accounts.purge_s3.bucket_unset",
                bucket_setting=bucket_setting,
                user_id=user_id,
            )
            continue
        # Defensive: a malformed prefix template (missing/wrong placeholder)
        # must skip the bucket rather than crash the whole cascade
        # (Story 1.12 code review §P7).
        try:
            prefix = prefix_template.format(user_id=user_id)
        except (KeyError, IndexError) as exc:
            log.warning(
                "accounts.purge_s3.bad_prefix_template",
                bucket_setting=bucket_setting,
                prefix_template=prefix_template,
                error_type=exc.__class__.__name__,
            )
            continue
        try:
            paginator = s3.get_paginator("list_objects_v2")
            batch: list[dict[str, str]] = []
            for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                for obj in page.get("Contents", []) or []:
                    batch.append({"Key": obj["Key"]})
                    # S3 DeleteObjects caps at 1000 keys per request.
                    if len(batch) >= 1000:
                        resp = s3.delete_objects(Bucket=bucket, Delete={"Objects": batch})
                        _raise_on_s3_partial_failure(resp, bucket=bucket, prefix=prefix)
                        total += len(batch)
                        batch = []
            if batch:
                resp = s3.delete_objects(Bucket=bucket, Delete={"Objects": batch})
                _raise_on_s3_partial_failure(resp, bucket=bucket, prefix=prefix)
                total += len(batch)
            processed.append(f"{bucket}/{prefix}")
        except (BotoCoreError, ClientError) as exc:
            # Log + re-raise: a partial purge is unacceptable for the deletion
            # promise. The Celery task's outer handler will mark the deletion
            # as failed-with-retry; the next sweep tries again.
            log.error(
                "accounts.purge_s3.failed",
                bucket=bucket,
                prefix=prefix,
                user_id=user_id,
                error_type=exc.__class__.__name__,
            )
            raise

    return total, processed


# ---------------------------------------------------------------------------
# request_deletion — AC1, AC4
# ---------------------------------------------------------------------------


@audit_action(
    "gdpr.account_deletion_requested",
    subject_from=lambda kwargs, ret: ret.user_id_snapshot if ret else kwargs["user"].id,
    # Story 1.12 code review §P24: guard against the failure path where `ret`
    # is None (e.g. SMTP rollback inside the inner transaction). The decorator
    # calls metadata_from on exception too — without the guard, the lambda
    # crashes on `None.id` and the FAILURE audit row is never written.
    # §D2 follow-up: include `content_hash` + `accepted_at` from the
    # ConsentDialog so the audit row carries the FR12 immutability proof of
    # what copy the user saw at decision time.
    metadata_from=lambda kwargs, ret: (
        {
            "deletion_request_id": ret.id,
            "hard_delete_after": ret.hard_delete_after.isoformat(),
            "content_hash": kwargs.get("content_hash"),
            "accepted_at": (
                kwargs["accepted_at"].isoformat() if kwargs.get("accepted_at") is not None else None
            ),
        }
        if ret is not None
        else {
            "deletion_request_id": None,
            "content_hash": kwargs.get("content_hash"),
        }
    ),
)
def request_deletion(
    *,
    user: User,
    password: str,
    content_hash: str | None = None,
    accepted_at: timezone.datetime | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
) -> AccountDeletionRequest:
    """Soft-delete the user and create the cancel-window record.

    Atomic: the User status flip, the AccountDeletionRequest insert, the session
    teardown and the audit row commit together. The confirmation email is sent
    **before** the transaction commits — if SMTP raises, everything rolls back
    and the user can retry (Story 1.12 §AC4 atomicity invariant).

    Raises:
        InvalidPassword: the password does not match the user's current hash.
        AccountDeletionAlreadyPending: an in-flight request already exists for
            this user (the partial unique index on `user_id_snapshot` makes the
            DB the source of truth; this pre-check just gives a clearer error).
    """
    if not user.check_password(password):
        raise InvalidPassword()

    # Pre-check (cheap, race-condition-tolerant via the partial unique index).
    if AccountDeletionRequest.objects.filter(
        user_id_snapshot=str(user.id),
        cancelled_at__isnull=True,
        hard_deleted_at__isnull=True,
    ).exists():
        raise AccountDeletionAlreadyPending()

    # Imported lazily so the test suite can stub the email send without pulling
    # the template loader at module load.
    from apps.accounts.services.account_deletion_email import (
        send_account_deletion_requested_email,
    )

    grace_days = getattr(settings, "GDPR_ACCOUNT_DELETION_GRACE_DAYS", 30)
    now = timezone.now()

    with transaction.atomic():
        # SELECT FOR UPDATE on the user so two concurrent deletes serialize.
        user_locked = User.objects.select_for_update().get(pk=user.pk)
        if user_locked.status == UserStatus.DELETED:
            # Another request slipped in between our pre-check and the lock.
            # The partial unique index on the new row insert would also catch
            # this, but raising the typed error here gives a cleaner response.
            raise AccountDeletionAlreadyPending()

        deletion = AccountDeletionRequest.objects.create(
            user=user_locked,
            user_id_snapshot=str(user_locked.id),
            cancel_token=_generate_cancel_token(),
            requested_at=now,
            hard_delete_after=now + timedelta(days=grace_days),
            password_hash_at_request=make_password(password),
            requested_ip_truncated=_truncate_ip(ip),
            requested_user_agent=(user_agent or "")[:200] or None,
        )

        user_locked.status = UserStatus.DELETED
        user_locked.is_active = False
        user_locked.deleted_at = now
        user_locked.save(update_fields=["status", "is_active", "deleted_at", "updated_at"])

        killed_sessions = _terminate_user_sessions(user_locked)

        # SMTP send inside the transaction: failure → rollback → user sees a
        # 503 and retries. Acceptable cost (200-500 ms) for the atomicity
        # invariant that "the user got the email iff the soft-delete persisted".
        send_account_deletion_requested_email(
            user=user_locked,
            deletion=deletion,
        )

    log.info(
        "accounts.deletion_requested",
        user_id=user_locked.id,
        deletion_request_id=deletion.id,
        hard_delete_after=deletion.hard_delete_after.isoformat(),
        killed_sessions=killed_sessions,
    )
    return deletion


# ---------------------------------------------------------------------------
# cancel_deletion — AC5, AC9
# ---------------------------------------------------------------------------


@audit_action(
    "gdpr.account_deletion_cancelled",
    subject_from=lambda kwargs, ret: (
        ret.user_id_snapshot if ret else kwargs["request"].user_id_snapshot
    ),
    metadata_from=lambda kwargs, ret: {
        "deletion_request_id": (ret.id if ret else kwargs["request"].id),
        "via": (
            "dpo_override"
            if kwargs.get("actor") is not None and kwargs.get("password") is None
            else "user_self_service"
        ),
        "cancel_reason": (ret.cancel_reason if ret else None),
    },
)
def cancel_deletion(
    *,
    request: AccountDeletionRequest,
    password: str | None,
    actor: Any | None = None,
    cancel_reason: str | None = None,
) -> AccountDeletionRequest:
    """Restore the user account and lock the request as cancelled.

    Two callers:
        - User self-service (AC5): `password` is the cleartext from the cancel
          form; `actor=None` (the user IS the request's subject — the audit
          decorator's actor resolver reads from request_context).
        - DPO admin override (AC9): `password=None` (skip the password check),
          `actor=<dpo_user>`, `cancel_reason` prefixed with `dpo_override:<id>:`.

    State machine guards (AC5 steps 3-4):
        - already-cancelled / already-hard-deleted → AccountDeletionAlreadyResolved (409)
        - past `hard_delete_after` → AccountDeletionExpired (410)
        - wrong password (self-service path) → InvalidPassword (400)
    """
    if request.cancelled_at is not None or request.hard_deleted_at is not None:
        raise AccountDeletionAlreadyResolved()
    if request.is_past_grace_window:
        raise AccountDeletionExpired()

    # User self-service path: validate the password against the CURRENT user
    # hash (not the snapshot — the user may have rotated it via support during
    # the grace window; see story §4.5 #4).
    if password is not None:
        user_ref = request.user
        if user_ref is None:
            # User row already gone — shouldn't happen pre-cancellation since
            # SET_NULL only fires on hard_delete (which would have set
            # `hard_deleted_at`). Treat defensively as already-resolved.
            raise AccountDeletionAlreadyResolved()
        if not user_ref.check_password(password):
            raise InvalidPassword()

    # DPO admin override path: the caller MUST pass a privileged actor with the
    # `accounts.cancel_deletion_request` permission. The admin view enforces
    # this; here we just refuse a None-password without an actor as a guard.
    if password is None and actor is None:
        raise InvalidPassword(
            detail="Cancellation without password requires an authenticated admin actor."
        )

    # Default cancel_reason if the caller didn't pass one. Use the actor's id
    # (not "unknown") when on the DPO path so the prefix is meaningful even
    # without a free-text reason — Story 1.12 code review §L6/§P14.
    if cancel_reason is None:
        if password is None:
            actor_id = getattr(actor, "id", None) or "unknown"
            cancel_reason = f"dpo_override:{actor_id}:no_reason_provided"
        else:
            cancel_reason = "user_self_service"

    # Truncate the FREE-TEXT portion only, not the prefix (`dpo_override:<id>:`).
    # Naive `cancel_reason[:200]` could eat the DPO id and break the audit
    # playbook's prefix filter (Story 1.12 code review §P14).
    if len(cancel_reason) > 200:
        if cancel_reason.startswith("dpo_override:"):
            try:
                _, dpo_id, free_text = cancel_reason.split(":", 2)
            except ValueError:
                free_text = ""
                dpo_id = ""
            prefix = f"dpo_override:{dpo_id}:"
            cancel_reason = prefix + free_text[: max(0, 200 - len(prefix))]
        else:
            cancel_reason = cancel_reason[:200]

    from apps.accounts.services.account_deletion_email import (
        send_account_deletion_cancelled_email,
    )

    now = timezone.now()
    with transaction.atomic():
        # Re-read under FOR UPDATE — guards against a concurrent sweep firing
        # at the exact moment the user clicks cancel.
        request_locked = AccountDeletionRequest.objects.select_for_update().get(pk=request.pk)
        if request_locked.cancelled_at is not None or request_locked.hard_deleted_at is not None:
            raise AccountDeletionAlreadyResolved()
        if request_locked.is_past_grace_window:
            raise AccountDeletionExpired()

        request_locked.cancelled_at = now
        request_locked.cancel_reason = cancel_reason
        request_locked.save(update_fields=["cancelled_at", "cancel_reason", "updated_at"])

        user_locked = request_locked.user
        if user_locked is None:
            # As above — defensive. The user row should still be here mid-grace.
            raise AccountDeletionAlreadyResolved()

        # Lock the user row before restoring so we don't race with another worker.
        # Story 1.12 code review §P13: a concurrent shell delete of the user
        # row between the select_related FK fetch and the lock surfaces as
        # `DoesNotExist`. Treat it as already-resolved.
        try:
            user_locked = User.objects.select_for_update().get(pk=user_locked.pk)
        except User.DoesNotExist:
            raise AccountDeletionAlreadyResolved()  # noqa: B904
        user_locked.status = UserStatus.ACTIVE
        user_locked.is_active = True
        user_locked.deleted_at = None
        user_locked.save(update_fields=["status", "is_active", "deleted_at", "updated_at"])

        # Restoration email — same atomicity policy as request_deletion.
        send_account_deletion_cancelled_email(user=user_locked, deletion=request_locked)

    log.info(
        "accounts.deletion_cancelled",
        user_id=user_locked.id,
        deletion_request_id=request_locked.id,
        via=("dpo_override" if password is None else "user_self_service"),
    )
    return request_locked


# ---------------------------------------------------------------------------
# hard_delete — AC6, AC7
# ---------------------------------------------------------------------------


def hard_delete(request: AccountDeletionRequest) -> dict[str, Any]:
    """Cascade-delete the user, purge S3 prefixes, and write the final audit row.

    Called from the Celery sweep `accounts.sweep_account_deletions` exclusively.
    Idempotent: a second call on a row already past `hard_deleted_at` is a no-op.

    Order of operations (story §AC6 — load-bearing):
        1. Re-fetch the user under FOR UPDATE; bail if the row is gone or the
           deletion was cancelled between selection and execution.
        2. Capture deletion-cascade preview (`Collector` row counts) for the
           audit metadata — done before delete() so we know what we're about
           to wipe.
        3. Purge S3 prefixes (errors raise; outer task catches + audits failure).
        4. Write the `gdpr.account_hard_deleted` audit row FIRST — audit_logs
           rows have no FK to User, so the row survives the cascade. Writing
           first preserves the invariant "audit never claims a deletion that
           did not complete" (the converse is acceptable: a deletion that
           completed without an audit row is the worse outcome, but the audit
           row + cascade are in the same transaction so this should not happen).
        5. `user.delete()` — PostgreSQL ON DELETE CASCADE wipes parental_consents
           (FK with CASCADE), GDPR export requests' user_id is a logical FK
           (CharField, survives intentionally for the 7-day download window).
        6. Best-effort completion email — fire-and-forget; SMTP errors are
           logged but never fail the deletion (story §4.5 #9).
        7. Set `hard_deleted_at` on the request row.

    Returns a dict suitable for structlog + Celery beat reporting:
        {
            "deletion_request_id": str,
            "user_id": str,
            "s3_keys_deleted": int,
            "s3_prefixes": list[str],
            "cascade_row_counts": dict[str, int],
        }
    """
    from django.db.models.deletion import Collector, ProtectedError

    from apps.accounts.services.account_deletion_email import (
        send_account_deletion_completed_email,
    )

    if request.hard_deleted_at is not None:
        return {"skipped": "already_hard_deleted", "deletion_request_id": request.id}
    if request.cancelled_at is not None:
        return {"skipped": "cancelled", "deletion_request_id": request.id}

    user_id_snapshot = request.user_id_snapshot

    # Story 1.12 code review §P3: structured event at the start of the per-row
    # cascade. Pairs with `accounts.hard_delete_completed` / `_failed` for
    # incident debugging on stalled rows.
    log.info(
        "accounts.hard_delete_started",
        user_id=user_id_snapshot,
        deletion_request_id=request.id,
    )

    with transaction.atomic():
        request_locked = AccountDeletionRequest.objects.select_for_update().get(pk=request.pk)
        # Re-check the guards under the lock — defends against a concurrent
        # cancellation that slipped in between the sweep's candidate selection
        # and this row's execution.
        if request_locked.hard_deleted_at is not None:
            return {"skipped": "already_hard_deleted", "deletion_request_id": request.id}
        if request_locked.cancelled_at is not None:
            return {"skipped": "cancelled", "deletion_request_id": request.id}

        user_ref = request_locked.user
        if user_ref is None:
            # User already gone (e.g. manual delete via shell, or a previous
            # sweep run that died after user.delete() but before setting
            # hard_deleted_at). Finalise the row so the sweep stops picking
            # it up.
            request_locked.hard_deleted_at = timezone.now()
            request_locked.save(update_fields=["hard_deleted_at", "updated_at"])
            audit_row = record_audit(
                action="gdpr.account_hard_deleted",
                result=AuditResult.SUCCESS,
                actor=_SYSTEM_ACTOR,
                subject_id=user_id_snapshot,
                metadata={
                    "deletion_request_id": request.id,
                    "reason": "user_already_absent",
                    "s3_keys_deleted": 0,
                },
            )
            _alert_on_silent_audit_failure(audit_row, request_id=request.id)
            return {
                "deletion_request_id": request.id,
                "user_id": user_id_snapshot,
                "s3_keys_deleted": 0,
                "s3_prefixes": [],
                "cascade_row_counts": {},
                "reason": "user_already_absent",
            }

        # Story 1.12 code review §P13: re-locking the user can race with a
        # manual shell delete. Treat the missing row as already-resolved.
        try:
            user_locked = User.objects.select_for_update().get(pk=user_ref.pk)
        except User.DoesNotExist:
            log.warning(
                "accounts.hard_delete.user_missing_under_lock",
                deletion_request_id=request.id,
                user_id_snapshot=user_id_snapshot,
            )
            request_locked.hard_deleted_at = timezone.now()
            request_locked.save(update_fields=["hard_deleted_at", "updated_at"])
            audit_row = record_audit(
                action="gdpr.account_hard_deleted",
                result=AuditResult.SUCCESS,
                actor=_SYSTEM_ACTOR,
                subject_id=user_id_snapshot,
                metadata={
                    "deletion_request_id": request.id,
                    "reason": "user_missing_under_lock",
                    "s3_keys_deleted": 0,
                },
            )
            _alert_on_silent_audit_failure(audit_row, request_id=request.id)
            return {
                "deletion_request_id": request.id,
                "user_id": user_id_snapshot,
                "s3_keys_deleted": 0,
                "s3_prefixes": [],
                "cascade_row_counts": {},
                "reason": "user_missing_under_lock",
            }

        # Step 2 — preview the cascade so the audit metadata captures the
        # blast radius. Collector.delete is called by `Model.delete()` under
        # the hood; we call `.collect()` manually for the preview. Story 1.12
        # code review §P4: prefer the fast-path planners (`fast_deletes`,
        # `field_updates`) over `data` (which only captures the slow
        # instance-fetch path). We merge both: SQL-only cascades show up in
        # `fast_deletes` (e.g. ON DELETE CASCADE) while Python-side cascades
        # (`signals=True` or model-defined `delete()`) show up in `data`.
        # Story 1.12 code review §P8: a PROTECT FK that slipped past the CI
        # gate (e.g. via M2M `through=`) raises `ProtectedError` here — catch
        # it explicitly and surface a typed error to the sweep.
        try:
            collector = Collector(using=user_locked._state.db)
            collector.collect([user_locked])
        except ProtectedError:
            log.error(
                "accounts.hard_delete.protected_fk_violation",
                user_id=user_locked.id,
                deletion_request_id=request_locked.id,
            )
            raise
        cascade_row_counts: dict[str, int] = {}
        # `collector.data`: {model_class: ordered_set(instances)} — Python-side cascades
        # (signal handlers, model `.delete()` overrides). Counts the fetched instances.
        for model_class, instances in collector.data.items():
            label = model_class._meta.label
            cascade_row_counts[label] = cascade_row_counts.get(label, 0) + len(instances)
        # `collector.fast_deletes`: list[QuerySet] for SQL-only `DELETE FROM x
        # WHERE pk IN (...)` cascades (the optimised path Django picks when no
        # signals/overrides are involved). `qs.count()` issues a COUNT(*)
        # against the planned delete predicate.
        for qs in collector.fast_deletes or []:
            label = qs.model._meta.label
            try:
                cascade_row_counts[label] = cascade_row_counts.get(label, 0) + qs.count()
            except Exception:
                cascade_row_counts.setdefault(label, 0)
        # `collector.field_updates` (Django 5.x): `defaultdict(list)` keyed by
        # `(field, value)` → list of instances. Used for `SET_NULL`/`SET_DEFAULT`
        # policies (e.g. `AccountDeletionRequest.user → NULL` post-cascade).
        # Counted under a `:field_update` suffix so DPO inspections can tell
        # the two cascade flavours apart.
        for (field, _value), instances in (collector.field_updates or {}).items():
            label = f"{field.model._meta.label}:field_update"
            cascade_row_counts[label] = cascade_row_counts.get(label, 0) + len(instances)

        # Step 3 — purge S3 (raises on any bucket error → outer task handles retry).
        s3_keys_deleted, s3_prefixes = _purge_s3_prefixes(user_id=user_locked.id)

        # Step 4 — write the audit row BEFORE the cascade. `record_audit`
        # uses `transaction.atomic()` internally; the outer atomic block joins
        # so a failure of either side rolls both back. Story 1.12 code review
        # §D6: when `record_audit` returns None (audit-DB down), the deletion
        # would silently proceed with no compliance record. We keep the
        # best-effort Story 1.13 contract but Sentry-flag the silent failure.
        audit_row = record_audit(
            action="gdpr.account_hard_deleted",
            result=AuditResult.SUCCESS,
            actor=_SYSTEM_ACTOR,
            subject_id=user_locked.id,
            metadata={
                "deletion_request_id": request_locked.id,
                "s3_keys_deleted": s3_keys_deleted,
                "s3_prefixes": s3_prefixes,
                "cascade_row_counts": cascade_row_counts,
            },
        )
        _alert_on_silent_audit_failure(audit_row, request_id=request_locked.id)

        # Story 1.12 code review §P5: cascade BEFORE the completion email.
        # The original ordering (email then delete) risked sending "your data
        # is gone" while the cascade still rolled back on a ProtectedError or
        # constraint trigger. `user_locked` survives `user.delete()` as a
        # Python object — `.email` stays accessible on the in-memory instance
        # so the email send works fine after the cascade.
        user_locked.delete()

        # Step 6 — completion email AFTER the cascade. Failures are swallowed:
        # the wipe is the legal obligation; the notification is best-effort
        # (story §4.5 #9).
        try:
            send_account_deletion_completed_email(user=user_locked, deletion=request_locked)
        except Exception:
            log.warning(
                "accounts.hard_delete.completion_email_failed",
                user_id=user_id_snapshot,
                deletion_request_id=request_locked.id,
                exc_info=True,
            )

        # Step 7 — finalise the request row. After user.delete() the request's
        # `user` FK is now NULL (SET_NULL), but `user_id_snapshot` survives.
        request_locked.hard_deleted_at = timezone.now()
        request_locked.save(update_fields=["hard_deleted_at", "updated_at"])

    log.info(
        "accounts.hard_delete_completed",
        user_id=user_id_snapshot,
        deletion_request_id=request.id,
        s3_keys_deleted=s3_keys_deleted,
        cascade_row_counts=cascade_row_counts,
    )
    return {
        "deletion_request_id": request.id,
        "user_id": user_id_snapshot,
        "s3_keys_deleted": s3_keys_deleted,
        "s3_prefixes": s3_prefixes,
        "cascade_row_counts": cascade_row_counts,
    }


# ---------------------------------------------------------------------------
# Lookup helpers used by the views
# ---------------------------------------------------------------------------


def lookup_request_by_token(token: str) -> AccountDeletionRequest:
    """Constant-time token lookup. Returns the row or raises 404."""
    # Step 1 — ORM equality fetch. This DOES leak DB lookup timing, but a token
    # with 256-bit entropy makes timing-based enumeration impractical (compare
    # with parental-consent which uses the same shape per Story 1.4 §P3).
    # Belt-and-braces: constant-time verify AFTER fetch.
    candidate = AccountDeletionRequest.objects.filter(cancel_token=token).first()
    if candidate is None:
        raise AccountDeletionNotFound()
    # Defence-in-depth: a hypothetical DB bug returning a partial match would
    # be caught by the constant-time compare; the equality filter above gives
    # full-string match in practice.
    if not secrets.compare_digest(candidate.cancel_token, token):
        raise AccountDeletionNotFound()
    return candidate


def lookup_active_request_for_user(user: User) -> AccountDeletionRequest | None:
    """Return the in-flight deletion request for a user, or None."""
    return (
        AccountDeletionRequest.objects.filter(
            user_id_snapshot=str(user.id),
            cancelled_at__isnull=True,
            hard_deleted_at__isnull=True,
        )
        .order_by("-requested_at")
        .first()
    )


# Re-exported only for tests that need to override password-check behaviour.
__all__ = [
    "_SYSTEM_ACTOR",
    "cancel_deletion",
    "django_check_password",
    "hard_delete",
    "lookup_active_request_for_user",
    "lookup_request_by_token",
    "request_deletion",
]
