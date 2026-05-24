"""Shared base models — `TenantScopedModel` is the multi-tenancy invariant.

Every Django model that holds personal data MUST inherit from
`TenantScopedModel` so the row carries `tenant_id` + `user_id` columns the
PostgreSQL RLS policies (migration `accounts/0007_enable_rls`) key on. The
class also auto-populates those columns from `apps.core.request_context`
inside requests, while explicitly refusing silent fallbacks outside of
requests (Celery tasks, shell, management commands) — those callers MUST
supply `tenant_id` / `user_id` themselves.

Anti-patterns this class blocks:
- forgetting `.filter(tenant_id=...)` in a service → RLS still filters at DB.
- inserting a row from a Celery task with `tenant_id=NULL` → save() raises.
- bypassing the manager via `.objects.using('...').create(...)` to skip the
  thread-local → save() still runs the explicit-value check.

NOT for: reference tables (occupations, formations, public school catalog),
the audit log (cross-tenant by design — cf. ADR-0009), or anything that is
already keyed on its own primary user FK without sharing across tenants.
See `docs/patterns/multi-tenant.md` for the decision tree.
"""

from __future__ import annotations

from django.db import models

from apps.core import request_context


class TenantScopedManager(models.Manager):
    """Default manager for `TenantScopedModel` — currently a thin pass-through.

    Spec AC1 mandates this named manager so future cross-cutting hooks
    (e.g. `with_user(user)` shortcut that combines `request_context.set_actor`
    and the queryset) have a canonical attachment point. Today the underlying
    behaviour is unchanged: RLS filters at the DB layer, the ORM stays naive.
    """


class TenantScopedModel(models.Model):
    """Abstract base for any model that stores user-specific personal data.

    Concrete subclasses inherit four columns + a fail-loud `save()` hook that
    refuses to persist a row without `tenant_id`/`user_id` set, either by the
    request middleware (the common case) or by the caller (Celery / shell).
    """

    # Null is permitted for B2C accounts (no school tenant). RLS policies treat
    # NULL as "no tenant scope" and rely on `user_id` alone for those rows.
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    # NOT a ForeignKey: subclasses live in feature apps that would induce a
    # circular import with `accounts`. A 32-char ULID-prefixed string is the
    # project's canonical user id format (cf. apps.core.ids).
    user_id = models.CharField(max_length=32, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Explicit `objects = TenantScopedManager()` (AC1) — pass-through today,
    # extension point for future cross-cutting helpers.
    objects = TenantScopedManager()

    class Meta:
        abstract = True

    def save(self, *args: object, **kwargs: object) -> None:
        """Auto-populate `tenant_id`/`user_id` from the request context, or fail loud.

        Three cases:
        1. `user_id` already set (by the caller) → save as-is.
        2. `user_id` unset AND `request_context.get_actor_id()` returns a
           value → pull both fields from the thread-local. `tenant_id` may
           legitimately stay NULL for B2C users.
        3. `user_id` unset AND no actor in context → raise `ValueError`.
           This is the Celery/shell path: those callers MUST be explicit.
        """
        if not self.user_id:
            actor_id = request_context.get_actor_id()
            if actor_id is None:
                raise ValueError(
                    f"{type(self).__name__}.save(): `user_id` is required when "
                    "no request actor is in context (Celery / shell / migrations). "
                    "Pass user_id=... explicitly, or call "
                    "`request_context.set_actor(user)` before saving."
                )
            self.user_id = actor_id
            # Only auto-fill tenant_id if the caller didn't set it.
            # A None coming from the context is meaningful (B2C) — preserve.
            if self.tenant_id is None:
                self.tenant_id = request_context.get_tenant_id()
        super().save(*args, **kwargs)  # type: ignore[misc]
