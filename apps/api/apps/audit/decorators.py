"""`@audit_action(...)` decorator + `record_audit(...)` helper.

Two write paths into the audit log:

1. `@audit_action("event.name", subject_from=..., metadata_from=...)` wraps a
   service function. On success → one `AuditLog` row with `result=success`. On
   exception → one row with `result=failure` (and the exception is re-raised
   so business logic keeps its semantics).

2. `record_audit(action=..., result=..., actor=..., ...)` is the ad-hoc form
   used by call sites that can't be a function boundary — e.g. a DRF permission
   class refusing access. It is also what the decorator delegates to internally.

Reliability contract (Story 1.13 §9 #4): audit writes MUST NOT block business
flow. If the DB is unavailable, we log + Sentry-capture, then swallow the
error. A retry queue is deferred to growth.
"""

from __future__ import annotations

import functools
import json
from collections.abc import Callable
from typing import Any

import structlog
from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditLog, AuditResult
from apps.audit.services.hash_chain import compute_row_hash, get_last_row_hash
from apps.core import request_context

log = structlog.get_logger(__name__)


SubjectResolver = str | Callable[[dict, Any], str | None] | None
MetadataResolver = Callable[[dict, Any], dict] | None


def audit_action(
    action: str,
    *,
    subject_from: SubjectResolver = None,
    metadata_from: MetadataResolver = None,
) -> Callable:
    """Persist an AuditLog entry on each invocation of the decorated function.

    Args:
        action: Event name, format `<domain>.<action>` (e.g. `"user.signed_up"`).
        subject_from: How to resolve `subject_id`.
            - `None` → no subject (e.g. `"auth.login_failed"`).
            - `str` → name of a kwarg whose value is the subject id.
            - callable `(kwargs, return_value) -> str | None`.
        metadata_from: callable `(kwargs, return_value) -> dict`. Default `{}`.

    Example:
        @audit_action(
            "user.email_verified",
            subject_from=lambda kwargs, ret: ret.id,
            metadata_from=lambda kwargs, ret: {"role": ret.role},
        )
        def mark_email_verified(user: User) -> User: ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                ret = func(*args, **kwargs)
            except Exception as exc:
                record_audit(
                    action=action,
                    result=AuditResult.FAILURE,
                    subject_id=_resolve_subject(subject_from, kwargs, None),
                    metadata={"error_type": exc.__class__.__name__},
                )
                raise
            subject_id = _resolve_subject(subject_from, kwargs, ret)
            metadata = metadata_from(kwargs, ret) if metadata_from else {}
            record_audit(
                action=action,
                result=AuditResult.SUCCESS,
                subject_id=subject_id,
                metadata=metadata,
            )
            return ret

        return wrapper

    return decorator


def record_audit(
    *,
    action: str,
    result: str,
    actor: Any = None,
    subject_id: str | None = None,
    metadata: dict | None = None,
) -> AuditLog | None:
    """Persist one AuditLog row. NEVER raises — failures are logged + Sentry.

    Transaction semantics: the audit write joins the caller's transaction if
    one is open (typical service code), so an outer rollback also rolls back
    the audit row. This is the desired compliance behavior — we should not
    audit operations that didn't actually persist. Story 1.13 §9 #4 swallow
    contract addresses the orthogonal case of audit-DB unavailability, not
    transactional rollbacks.

    Returns the created row, or `None` if persistence failed.
    """
    actor_id, actor_role = _resolve_actor(actor)
    tenant_id = request_context.get_tenant_id()
    request_id = request_context.get_request_id()
    ip_hash = request_context.get_ip_hash()
    user_agent = request_context.get_user_agent()
    metadata_clean = _sanitize_metadata(metadata, action=action)

    try:
        with transaction.atomic():
            prev_hash = get_last_row_hash()
            now = timezone.now()
            row_hash = compute_row_hash(
                actor_id=actor_id,
                action=action,
                subject_id=subject_id,
                metadata=metadata_clean,
                created_at=now,
                prev_hash=prev_hash,
            )
            return AuditLog.objects.create(
                actor_id=actor_id,
                actor_role=actor_role or "",
                tenant_id=tenant_id,
                subject_id=subject_id,
                action=action,
                result=result,
                request_id=request_id,
                ip_address_hash=ip_hash,
                user_agent=user_agent,
                metadata=metadata_clean,
                prev_hash=prev_hash,
                row_hash=row_hash,
                created_at=now,
            )
    except Exception as exc:
        log.error("audit.record_failed", action=action, error=str(exc), exc_info=True)
        try:
            import sentry_sdk

            sentry_sdk.capture_exception(exc)
        except Exception:
            log.warning("audit.sentry_capture_failed")
        return None


def _sanitize_metadata(metadata: dict | None, *, action: str) -> dict:
    """Reject non-JSON-primitive values so the hash chain stays reproducible.

    `json.dumps(default=str)` would let `datetime`/`Decimal`/model instances
    slip through and produce hashes that depend on `repr` stability across
    Python versions. We round-trip via strict `json.dumps` to catch them
    early; on failure we drop to an empty dict and Sentry-flag the caller.
    """
    if not metadata:
        return {}
    try:
        json.dumps(metadata, sort_keys=True)
        return metadata
    except (TypeError, ValueError) as exc:
        log.warning("audit.metadata_rejected", action=action, error=str(exc))
        try:
            import sentry_sdk

            sentry_sdk.capture_message(
                f"audit.metadata_rejected: non-JSON-primitive in {action}",
                level="warning",
            )
        except Exception:
            pass
        return {}


def _resolve_subject(spec: SubjectResolver, kwargs: dict, ret: Any) -> str | None:
    if spec is None:
        return None
    if isinstance(spec, str):
        value = kwargs.get(spec)
        # Coerce any concrete id (int, UUID, custom) to str; only None means "no subject".
        return str(value) if value is not None else None
    return spec(kwargs, ret)


def _resolve_actor(override: Any | None) -> tuple[str | None, str]:
    if override is not None:
        actor_id = getattr(override, "id", None)
        return (str(actor_id) if actor_id is not None else None), (
            getattr(override, "role", "") or ""
        )
    actor_id = request_context.get_actor_id()
    return (str(actor_id) if actor_id is not None else None), request_context.get_actor_role() or ""
