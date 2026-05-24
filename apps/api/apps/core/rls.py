"""RLS escape hatches for anonymous flows and system tasks (Story 1.8 review).

Two context managers, two narrowly-scoped GUCs, every use audited.

- `bypass_rls()` — opens `app.bypass_rls = 'true'` for the duration of the
  block. Policies include `OR current_setting('app.bypass_rls', true) = 'true'`
  so the protected tables become readable/writable. **Only** for anonymous
  endpoints whose business logic is unambiguous from the URL alone
  (parental-consent /decide/<token>/, signup signal). Each entry emits an
  audit row so an attacker who finds a way to call the helper from new code
  still leaves a trail.

- `with_system_actor()` — same surface but pre-sets `actor_role='system'`
  before opening the bypass. Used by Celery beat tasks (parental
  reminder/suspend, GDPR expire, audit archive) that have no `request.user`
  but DO run on behalf of the platform — distinct from an anonymous web
  request for forensics.

Both helpers are PostgreSQL-only — they no-op on SQLite (the unit-test fast
path can't have RLS anyway). The `audit_logs` table is RLS-exempt, so the
audit hook itself never depends on the bypass it announces.

Anti-patterns:
- ❌ DO NOT call `bypass_rls()` from a generic helper. The set of call
  sites MUST stay countable on one hand — a code reviewer should be able
  to grep for it and audit each one.
- ❌ DO NOT extend the policies to read any new bypass GUC without
  updating this module + audit-events.md.
- ❌ DO NOT swallow exceptions inside the `with` block — that masks
  whether RLS was the rejecter.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from django.db import connection


def _set_guc(name: str, value: str) -> None:
    """SET SESSION (`is_local=false`) — paired with explicit clear in finally."""
    if connection.vendor != "postgresql":
        return
    with connection.cursor() as cursor:
        cursor.execute("SELECT set_config(%s, %s, false)", [name, value])


def _audit_bypass(reason: str, metadata: dict[str, Any] | None = None) -> None:
    """Best-effort `rls.bypass_used` audit row. Never raises."""
    try:
        from apps.audit.decorators import record_audit
        from apps.audit.models import AuditResult

        record_audit(
            action="rls.bypass_used",
            result=AuditResult.SUCCESS,
            metadata={"reason": reason, **(metadata or {})},
        )
    except Exception:
        # Audit failure must never block the bypass itself — the bypass is
        # the load-bearing behaviour, audit is observability.
        pass


@contextmanager
def bypass_rls(*, reason: str, metadata: dict[str, Any] | None = None) -> Iterator[None]:
    """Open `app.bypass_rls = 'true'` for the duration of the block.

    Call sites (whitelisted — keep updated):
    1. `apps.accounts.signals.create_parental_consent_for_minor` — signup
       signal runs anonymously, must INSERT into `users` + `parental_consents`.
    2. `apps.accounts.views.parental_consent_decide` — parent authenticated
       by URL token, must UPDATE `parental_consents` (anonymous request).
    3. `apps.accounts.views.parental_consent_status` — same, read-only.

    `reason` is mandatory and persisted in the audit row so DPO can grep.
    """
    _audit_bypass(reason, metadata)
    _set_guc("app.bypass_rls", "true")
    try:
        yield
    finally:
        _set_guc("app.bypass_rls", "")


@contextmanager
def with_system_actor(*, reason: str, metadata: dict[str, Any] | None = None) -> Iterator[None]:
    """Run a block as the `system` actor (Celery, beat, management commands).

    Combines two GUC writes:
    - `app.actor_role = 'system'` so audit rows + RLS policies see a typed
      actor (distinct from anonymous-web `''`).
    - `app.bypass_rls = 'true'` so the block can read/write protected tables.

    Whitelisted call sites:
    1. `apps.accounts.tasks.send_parental_consent_reminders`
    2. `apps.accounts.tasks.suspend_unresolved_parental_consents`
    3. `apps.accounts.tasks.notify_unconfirmed_granted_consents`
    4. `apps.accounts.tasks.build_export` (GDPR — touches `users`)
    5. `apps.accounts.tasks.expire_old_exports`
    6. `apps.accounts.tasks.notify_export_ready`
    7. `apps.accounts.tasks.send_gdpr_export_failed_email`
    8. `apps.audit.tasks.archive_old_logs` / `verify_chain_integrity` /
       `export_csv_to_s3` — read-only on `audit_logs` (RLS-exempt) but they
       may join with `users` so the wrap is defensive.

    Maintainers: any new Celery task that touches RLS-protected tables MUST
    wrap its body in `with_system_actor()` or set GUCs manually.
    """
    _audit_bypass(reason, {"actor": "system", **(metadata or {})})
    _set_guc("app.actor_role", "system")
    _set_guc("app.bypass_rls", "true")
    try:
        yield
    finally:
        _set_guc("app.actor_role", "")
        _set_guc("app.bypass_rls", "")


__all__ = ["bypass_rls", "with_system_actor"]
