"""Login lockout — Story 1.5 §AC4.

Per-account failed-attempt counter + lockout state machine. Orthogonal to the
per-IP throttle on `ThrottledLoginView` (Story 1.12 §D5, 5/min/IP) — the two
protect against different attack shapes:

- Per-IP throttle: capped at the HTTP layer, blunts a single botnet IP from
  hammering the endpoint regardless of which email it tries.
- Per-account lockout (this module): triggered by 5 failures in 15 min
  against the SAME user, locks the account for 10 min. Defends against an
  attacker that spreads attempts across many IPs but targets one email.

Storage asymmetry (§4.5 #1 of the story):

- The **counter** lives in Django's `default` cache (Redis in prod /
  LocMemCache in tests). Atomic `add` + `incr` survives the worker pool but
  is lost on a cache flush. That degradation is acceptable: a flush resets
  counters to zero, the user gets a fresh 5-attempt budget — at MVP scale
  no attacker can usefully sync to a flush.
- The **lockout** itself lives on `User.locked_until` (DB column from Story
  1.5 T1). The DB column is the source of truth for the "currently locked"
  state and survives every cache flush.

The order is load-bearing: callers MUST consult `is_account_locked(user)`
BEFORE doing the auth call, so a locked user is refused without their
password ever being checked against the hash.
"""

from __future__ import annotations

from datetime import timedelta

import structlog
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.audit.decorators import record_audit
from apps.audit.models import AuditResult

log = structlog.get_logger(__name__)


def _counter_key(user_id: str) -> str:
    return f"auth.login_fail:{user_id}"


def is_account_locked(user: User) -> bool:
    """Pure DB check — never touches the cache. The DB column is the source
    of truth for the lock state (cf. module docstring).
    """
    return user.is_locked


def record_failed_attempt(*, user: User, ip_truncated: str | None = None) -> int:
    """Increment the failed-attempt counter and trip the lockout if threshold reached.

    Returns the new counter value (1, 2, … N). On the Nth attempt (where N
    equals `LOGIN_FAIL_THRESHOLD`), sets `User.locked_until = now() + lock`
    inside a transaction and emits a `auth.account_locked` audit row.

    Idempotent under concurrent calls:
    - `cache.add` + `cache.incr` are atomic at the Redis layer (NX+INCR).
      Two workers that both see the threshold value will both attempt the
      DB update, but the SQL update filters on `locked_until__isnull=True`
      so only the first one writes.
    - The audit row likewise fires only when `update()` reports rowcount > 0.
    """
    threshold = getattr(settings, "LOGIN_FAIL_THRESHOLD", 5)
    window = getattr(settings, "LOGIN_FAIL_WINDOW_SECONDS", 900)
    lock_duration = getattr(settings, "LOGIN_LOCK_DURATION_SECONDS", 600)

    key = _counter_key(user.id)
    # `cache.add(key, 0, timeout=window)` is atomic SET-IF-NOT-EXISTS.
    # When the key already exists this is a no-op, and crucially does NOT
    # refresh the TTL — the window slides from the FIRST failure, which is
    # the semantic the spec mandates ("5 failures in 15 min", not "5
    # failures within 15 min of the last one").
    cache.add(key, 0, timeout=window)
    try:
        new_count = cache.incr(key)
    except ValueError:
        # Race: the key TTL expired between our `add` and our `incr`.
        # Re-seed it. This collapses the rare race window to "the new
        # counter starts at 1 instead of N" which is the conservative
        # outcome (caller still sees a failure, just no lockout yet).
        cache.set(key, 1, timeout=window)
        new_count = 1

    if new_count < threshold:
        return new_count

    # Threshold reached — trip the lockout. The `filter(locked_until__isnull=True)`
    # makes the update idempotent: a concurrent worker that already set the
    # lockout will not produce a second `auth.account_locked` audit row.
    # The audit write runs INSIDE the same atomic block as the column update
    # so a DB failure on the audit chain rolls back the lockout itself (no
    # silently-unlocked-but-counter-thinks-locked split-brain — code-review
    # P3, Story 1.5 review 2026-05-27).
    unlock_at = timezone.now() + timedelta(seconds=lock_duration)
    with transaction.atomic():
        updated = User.objects.filter(pk=user.pk, locked_until__isnull=True).update(
            locked_until=unlock_at,
        )
        if updated:
            record_audit(
                action="auth.account_locked",
                result=AuditResult.SUCCESS,
                actor=user,
                subject_id=user.id,
                metadata={
                    "window_seconds": window,
                    "lock_duration_seconds": lock_duration,
                    "unlock_at": unlock_at.isoformat(),
                    "ip_truncated": ip_truncated,
                },
            )

    if updated:
        log.warning(
            "auth.account_locked",
            user_id=user.id,
            unlock_at=unlock_at.isoformat(),
            ip_truncated=ip_truncated,
        )

    return new_count


def clear_failed_attempts(*, user: User, trigger: str = "successful_login") -> None:
    """Reset the counter + the lockout column, and emit `auth.account_unlocked`
    when the clear actually un-locks an account.

    Called from three paths (each passes `trigger` so the DPO can replay the
    cause):
    - Successful login (`trigger="successful_login"`, default) — Story 1.5 §AC4.
    - Password reset confirm (`trigger="password_reset"`) — Story 1.5 §AC6
      (recovery flow releases a locked account).
    - DPO admin shell override (`trigger="dpo_manual"`) — `docs/runbooks/
      login-and-password-reset.md` §3.

    Symmetry with `record_failed_attempt`'s `auth.account_locked`:
    - The DB UPDATE + audit row run inside ONE `transaction.atomic()` block,
      so an audit failure rolls back the unlock (code-review P3 + P4).
    - The unlock event fires ONLY when an actual lockout was cleared
      (`rowcount > 0`); a clear-on-already-unlocked is silent.

    Idempotent — `cache.delete` is safe against missing keys; the conditional
    UPDATE is safe against missing rows.
    """
    cache.delete(_counter_key(user.id))
    if user.locked_until is None:
        return

    # Use the conditional UPDATE (rowcount > 0) as the unlock-event gate so a
    # concurrent clear from another worker emits the event at most once
    # (code-review P7 — Story 1.5 review 2026-05-27).
    with transaction.atomic():
        unlocked = User.objects.filter(pk=user.pk, locked_until__isnull=False).update(
            locked_until=None,
        )
        if unlocked:
            record_audit(
                action="auth.account_unlocked",
                result=AuditResult.SUCCESS,
                actor=user if trigger == "successful_login" else None,
                subject_id=user.id,
                metadata={"trigger": trigger},
            )

    # Refresh the in-memory user so the caller's `is_locked` property
    # reflects the cleared state.
    user.locked_until = None
    if unlocked:
        log.info("auth.account_unlocked", user_id=user.id, trigger=trigger)
