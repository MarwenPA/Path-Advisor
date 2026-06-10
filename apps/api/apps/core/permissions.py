"""Path-Advisor RBAC permission classes — Story 1.7.

Six roles (`student`, `parent`, `counselor`, `school_admin`, `path_admin`,
`support`) declared as DRF `BasePermission` subclasses. Every endpoint in
the codebase MUST declare `permission_classes` explicitly (enforced by
`scripts/assert_rbac_declared.py` in CI — story §AC5).

Design choices (cf. story §4.2):

- **`PathAdvisorPermission` base class** unifies the audit-denial pattern.
  Every refusal writes ONE `rbac.access_denied` audit row, deduped per-
  request (DRF calls `has_permission` 2-3 times per request).
- **`requires_mfa_verified` opt-in flag** (Story 1.6 integration). Staff
  permissions (`IsCounselor`, `IsSchoolAdmin`, `IsPathAdmin`, `IsSupport`)
  default it to True — they refuse if `request.user.is_verified()` is
  False (django-otp `OTPMiddleware`). B2C (`IsStudent`, `IsParent`) leave
  it False — MFA is opt-in for them.
- **No `is_superuser` god-mode bypass** except for `IsPathAdmin` (story §AC10).
  Rationale: a superuser who needs to act as a counselor must do so via
  their actual role, NOT bypass the permission. Keeps audit semantics clean.
- **Object-level permissions** (`IsOwner`, `IsOwnerOrPathAdmin`) for per-
  user resources (élève views own profile only; DPO escalation explicit).
"""

from __future__ import annotations

from typing import Any, ClassVar

import structlog
from rest_framework.permissions import BasePermission

from apps.accounts.models import UserRole

# Note: `apps.audit.decorators.record_audit` is imported LAZILY inside
# `_record_rbac_denial` to break the import cycle between this module and
# the audit app (code-review P7).

log = structlog.get_logger(__name__)

#: Aliases for readability — these are str values matching `UserRole.value`.
STUDENT = UserRole.STUDENT.value
PARENT = UserRole.PARENT.value
COUNSELOR = UserRole.COUNSELOR.value
SCHOOL_ADMIN = UserRole.SCHOOL_ADMIN.value
PATH_ADMIN = UserRole.PATH_ADMIN.value
SUPPORT = UserRole.SUPPORT.value

#: B2C role bucket — students + parents.
B2C_ROLES: frozenset[str] = frozenset({STUDENT, PARENT})

#: B2B / staff role bucket — counselor, school_admin, path_admin, support.
STAFF_ROLES: frozenset[str] = frozenset({COUNSELOR, SCHOOL_ADMIN, PATH_ADMIN, SUPPORT})

#: ALL roles — should equal the union of `UserRole.choices`. The invariant
#: is enforced by `test_all_roles_matches_user_role_enum` in
#: `apps/core/tests/test_rbac_permissions.py` rather than a module-level
#: `assert` — the prior assert could explode with `AppRegistryNotReady` if
#: any module imported `apps.core.permissions` before `apps.accounts` was
#: ready (code-review P3).
ALL_ROLES: frozenset[str] = B2C_ROLES | STAFF_ROLES


# ---------------------------------------------------------------------------
# Audit helper — emit ONE rbac.access_denied row per request (deduped)
# ---------------------------------------------------------------------------


def _record_rbac_denial(
    *,
    request: Any,
    view: Any,
    required_roles: frozenset[str],
    reason: str,
    extra_metadata: dict[str, object] | None = None,
) -> None:
    """Write a single `rbac.access_denied` audit row per request.

    DRF calls `has_permission` repeatedly (list view + filter backends +
    pagination). The dedup flag `request._rbac_denial_recorded` prevents
    audit-log amplification.

    `actor` is the authenticated user (when known); `None` for anonymous
    requests. `subject_id=None` because RBAC denial is an actor-side event
    — the DPO queries `WHERE actor_id = X AND action = "rbac.access_denied"`
    to spot escalation patterns.

    **Code-review hardening (2026-06-08):**
    - P6: set dedup flag BEFORE `record_audit` so a failure in the audit
      write doesn't trigger flood-retry on the next has_permission call.
    - P7: lazy import of `record_audit` to break the circular-import risk
      between `apps.core.permissions` and `apps.audit.decorators`.
    - P21: defensive `try/except` around `request.__setattr__` for DRF
      Request wrapper attribute-setting quirks.
    - P22: `request.path` default to `""` for async/test harness contexts.
    """
    if getattr(request, "_rbac_denial_recorded", False):
        return

    # P21 — set dedup flag FIRST + defensively. The flag must be set on the
    # request even if record_audit raises ; otherwise the next
    # has_permission call triggers a retry → flood logs.
    try:
        request._rbac_denial_recorded = True
    except (AttributeError, TypeError):
        # Some test harnesses use immutable requests ; tolerate but log.
        log.warning("rbac.denial_dedup_flag_failed")

    user = getattr(request, "user", None)
    is_authenticated = user is not None and getattr(user, "is_authenticated", False)
    actor = user if is_authenticated else None
    actor_role = (getattr(user, "role", "") or "") if is_authenticated else ""

    metadata: dict[str, object] = {
        "endpoint": getattr(request, "path", "") or "",
        "method": getattr(request, "method", "") or "",
        "required_roles": sorted(required_roles),
        "actor_role": actor_role,
        "reason": reason,
        "view": view.__class__.__name__ if view is not None else "",
    }
    if extra_metadata:
        metadata.update(extra_metadata)

    # P7 — lazy import to avoid the import cycle:
    # apps.core.permissions → apps.audit.decorators → (transitively any
    # apps.audit module that ever imports apps.core.permissions).
    from apps.audit.decorators import record_audit as _record_audit
    from apps.audit.models import AuditResult as _AuditResult

    try:
        _record_audit(
            action="rbac.access_denied",
            result=_AuditResult.DENIED,
            actor=actor,
            subject_id=None,
            metadata=metadata,
        )
    except Exception:
        # `record_audit` itself is best-effort (Story 1.13 design — the
        # decorator swallows on DB failure). Catch the rare case where the
        # caller raised and structlog the failure.
        log.warning(
            "rbac.access_denied.audit_failed",
            reason=reason,
            view=metadata["view"],
            exc_info=True,
        )


# ---------------------------------------------------------------------------
# Base class — every Path-Advisor permission inherits from this
# ---------------------------------------------------------------------------


class PathAdvisorPermission(BasePermission):
    """Path-Advisor base permission with role + MFA + audit-denial wiring.

    Subclasses set `allowed_roles` (set of `UserRole.value` strings) and
    optionally `requires_mfa_verified` / `requires_fully_active`.

    The default `has_permission` flow:
    1. Refuse if user is not authenticated → audit `reason="not_authenticated"`.
    2. Refuse if `user.role not in allowed_roles` → audit `reason="wrong_role"`.
    3. Refuse if `requires_mfa_verified and not user.is_verified()` → audit
       `reason="not_mfa_verified"`.
    4. Refuse if `requires_fully_active and not user.is_fully_active` →
       audit `reason="not_fully_active"`.
    5. Otherwise allow.
    """

    #: Set of `UserRole.value` strings allowed by this permission.
    allowed_roles: ClassVar[frozenset[str]] = frozenset()

    #: When True, refuses unless `request.user.is_verified()` (django-otp).
    #: Staff permissions default this to True; B2C permissions leave False.
    requires_mfa_verified: ClassVar[bool] = False

    #: When True, refuses unless `request.user.is_fully_active` (Story 1.4
    #: limited-mode gate — kid pending_parental_consent is False here).
    requires_fully_active: ClassVar[bool] = False

    #: Class-level allow-superuser bypass. Only `IsPathAdmin` opts in;
    #: every other permission refuses superusers without the matching role
    #: (story §AC10 anti-pattern).
    allow_superuser_bypass: ClassVar[bool] = False

    message = "Vous n'avez pas l'autorisation d'accéder à cette ressource."

    def has_permission(self, request: Any, view: Any) -> bool:
        user = getattr(request, "user", None)

        if user is None or not getattr(user, "is_authenticated", False):
            _record_rbac_denial(
                request=request,
                view=view,
                required_roles=self.allowed_roles,
                reason="not_authenticated",
            )
            return False

        # Superuser bypass — opt-in per subclass.
        if self.allow_superuser_bypass and getattr(user, "is_superuser", False):
            return True

        actor_role = getattr(user, "role", "")
        if actor_role not in self.allowed_roles:
            _record_rbac_denial(
                request=request,
                view=view,
                required_roles=self.allowed_roles,
                reason="wrong_role",
            )
            return False

        if self.requires_mfa_verified and not _is_mfa_verified(user):
            _record_rbac_denial(
                request=request,
                view=view,
                required_roles=self.allowed_roles,
                reason="not_mfa_verified",
            )
            return False

        if self.requires_fully_active and not getattr(user, "is_fully_active", False):
            _record_rbac_denial(
                request=request,
                view=view,
                required_roles=self.allowed_roles,
                reason="not_fully_active",
            )
            return False

        return True


def _is_mfa_verified(user: Any) -> bool:
    """Check django-otp's `is_verified` flag — the attribute is added by
    `OTPMiddleware` and may be missing in tests that bypass middleware.

    Code-review P8 — accept both method (`is_verified()`) AND attribute
    (`is_verified` as a property / bool). Some auth backend stacks expose
    it as a cached property ; refusing those legitimate verified users
    would break the staff login flow.
    """
    is_verified = getattr(user, "is_verified", None)
    if is_verified is None:
        return False
    # Callable path — django-otp's canonical interface.
    if callable(is_verified):
        try:
            return bool(is_verified())
        except Exception:
            log.warning("rbac.is_verified_call_raised", exc_info=True)
            return False
    # Attribute / property path — defensive accept.
    try:
        return bool(is_verified)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Concrete role permissions (Story 1.7 §AC2)
# ---------------------------------------------------------------------------


class IsStudent(PathAdvisorPermission):
    allowed_roles = frozenset({STUDENT})


class IsParent(PathAdvisorPermission):
    allowed_roles = frozenset({PARENT})


class IsCounselor(PathAdvisorPermission):
    allowed_roles = frozenset({COUNSELOR})
    requires_mfa_verified = True


class IsSchoolAdmin(PathAdvisorPermission):
    allowed_roles = frozenset({SCHOOL_ADMIN})
    requires_mfa_verified = True


class IsPathAdmin(PathAdvisorPermission):
    """Path-Advisor backstaff admin. Only role that gets the superuser bypass.

    Compatible with the prior `apps.audit.permissions.IsPathAdmin` (which
    re-exports this class as a deprecation shim).

    Code-review P18 — message reverted from the audit-log-specific wording
    to a generic phrasing. The prior text leaked "audit log" context onto
    every IsPathAdmin refusal even on unrelated endpoints (referential
    update, moderation, etc.). The specialized `audit.log_query_denied`
    audit row is what tags audit-log-specific refusals, not the user-
    facing message.
    """

    allowed_roles = frozenset({PATH_ADMIN})
    requires_mfa_verified = True
    allow_superuser_bypass = True
    # Inherited generic message from PathAdvisorPermission.


class IsSupport(PathAdvisorPermission):
    """Support staff — ticket handling, masked profile view, NO audit log
    access (cf. story §6 #1).
    """

    allowed_roles = frozenset({SUPPORT})
    requires_mfa_verified = True


class IsB2C(PathAdvisorPermission):
    """Composite: student OR parent. Used by endpoints that are B2C-only
    (e.g., MFA disable / enrollment-from-session — staff use the login-time
    flow instead).
    """

    allowed_roles = B2C_ROLES


class IsStaff(PathAdvisorPermission):
    """Composite: any staff role (counselor / school_admin / path_admin / support).
    Used by sidebar guard, B2B dashboard, etc.
    """

    allowed_roles = STAFF_ROLES
    requires_mfa_verified = True


class IsAuthenticatedAndActive(PathAdvisorPermission):
    """Auth + `is_fully_active` check, role-agnostic. Composable with any
    role permission (e.g., `[IsAuthenticatedAndActive, IsCounselor]`).

    Used by endpoints that need the limited-mode gate (Story 1.4) on top of
    the role check — e.g., premium subscription endpoints (Epic 5).
    """

    allowed_roles = ALL_ROLES
    requires_fully_active = True


# ---------------------------------------------------------------------------
# Object-level permissions (Story 1.7 §AC3)
# ---------------------------------------------------------------------------


class IsOwner(BasePermission):
    """Object-level permission — passes iff `obj.user_id == request.user.id`.

    Configurable via `owner_field` class attribute (default: `"user_id"`).
    For models where the owner reference is `obj.user.id` (the FK), set
    `owner_field = "user"` and the check falls back to `obj.user.id`.

    DOES NOT inherit `PathAdvisorPermission` because object-level checks
    don't fit the "all-roles-allowed-here" semantic. Compose with a role
    permission in `permission_classes` — the CI gate `assert_rbac_declared`
    enforces this composition (code-review D3) to prevent permission
    misuse (a stand-alone `IsOwner` would let any authenticated user
    reach `has_object_permission`):

        permission_classes = [IsAuthenticatedAndActive, IsStudent, IsOwner]

    **Code-review hardening (2026-06-08):**
    - P9: refuse when both `owner_id` AND `actor_id` are `None` (an
      orphaned-row owner_id paired with anonymous user passes the
      `None == None` equality otherwise).
    - P10: refuse when `obj is None` (DRF passes None on some empty-set
      code paths).
    - P11: fallback chain for custom `owner_field` — try `.user.id` if
      the configured field returns None.
    """

    owner_field: ClassVar[str] = "user_id"
    message = "Vous n'avez pas accès à cette ressource."

    def has_permission(self, request: Any, view: Any) -> bool:
        # Object-level only — the role check is handled by sibling permissions
        # in the chain. Always-True (modulo auth) so the chain proceeds to
        # has_object_permission. The CI gate refuses an endpoint that uses
        # `IsOwner` without also declaring a role permission.
        return getattr(request.user, "is_authenticated", False)

    def has_object_permission(self, request: Any, view: Any, obj: Any) -> bool:
        # P10 — obj=None is never owned by anyone.
        if obj is None:
            return False

        actor_id = getattr(request.user, "id", None)
        owner_id = self._extract_owner_id(obj)

        # P9 — refuse both-None bypass. An anonymous/stale user (id=None)
        # paired with an orphaned-row owner_id=None would pass `==` equality
        # without this guard.
        if owner_id is None or actor_id is None:
            _record_rbac_denial(
                request=request,
                view=view,
                required_roles=frozenset(),
                reason="not_owner",
                extra_metadata={
                    "target_user_id": owner_id,
                    "actor_user_id": actor_id,
                },
            )
            return False

        if owner_id == actor_id:
            return True

        _record_rbac_denial(
            request=request,
            view=view,
            required_roles=frozenset(),
            reason="not_owner",
            extra_metadata={
                "target_user_id": owner_id,
                "actor_user_id": actor_id,
            },
        )
        return False

    def _extract_owner_id(self, obj: Any) -> Any:
        """Read the configured owner field, with a `.user.id` fallback chain
        for any field name (code-review P11 — was previously gated on
        `owner_field == "user_id"` only, leaving custom fields without a
        fallback).
        """
        value = getattr(obj, self.owner_field, None)
        if value is None:
            # Fall back to obj.user.id (works for both the default
            # `user_id` field and any custom field whose related object
            # is exposed via `.user`).
            user_obj = getattr(obj, "user", None)
            if user_obj is not None:
                return getattr(user_obj, "id", None)
        return value


class IsOwnerOrPathAdmin(IsOwner):
    """Object-level: passes if owner OR `request.user.role == "path_admin"`.

    Documented DPO-escalation path for `gdpr-exports/{id}/download/`,
    account-deletion records, and any other per-user resource the DPO must
    audit.

    **Code-review D1 (2026-06-08):** the prior implementation added a
    third bypass branch `is_superuser=True` that contradicted spec §AC10
    ("superuser bypass UNIQUEMENT IsPathAdmin"). A superuser with
    `role=student` would have accessed every user's GDPR export with no
    audit signal. The bypass is REMOVED — a DPO who needs cross-user
    access either:
    1. Has `role=path_admin` (the documented DPO account shape), OR
    2. Uses `manage.py shell` (which does not flow through DRF
       permissions and is independently audited).
    """

    def has_object_permission(self, request: Any, view: Any, obj: Any) -> bool:
        user = request.user
        if getattr(user, "role", "") == PATH_ADMIN:
            return True
        return super().has_object_permission(request, view, obj)


# ---------------------------------------------------------------------------
# ROLE_MATRIX — documentation source-of-truth (consumed by docs + tests)
# ---------------------------------------------------------------------------

#: Symbolic capabilities → which roles can perform them. Mirrors PRD
#: §"Matrice RBAC". NOT consumed by the permission classes themselves
#: (which group by role), but USED by `docs/patterns/rbac-matrix.md` and
#: by `apps/core/tests/test_rbac_matrix.py` to assert the table stays in
#: sync with the actual `allowed_roles` of each concrete permission.
ROLE_MATRIX: dict[str, frozenset[str]] = {
    # Self-owned (any authenticated user can act on their OWN data)
    "read.own_profile": ALL_ROLES,
    "write.own_profile": ALL_ROLES,
    "delete.own_account": ALL_ROLES,
    "export.own_data": ALL_ROLES,
    # B2C-specific
    "manage.own_mfa": ALL_ROLES,  # any role can manage their own MFA
    "disable.own_mfa": B2C_ROLES,  # staff CANNOT self-disable (NFR-S2)
    "invite.parent": frozenset({STUDENT}),
    # Parent (read-only on linked child)
    "read.linked_child_profile": frozenset({PARENT}),
    "pay.premium_for_linked_child": frozenset({PARENT}),
    # Counselor (cohort view)
    "read.cohort_aggregate": frozenset({COUNSELOR}),
    "read.cohort_student_with_consent": frozenset({COUNSELOR}),
    # School admin (received profiles)
    "read.received_profile": frozenset({SCHOOL_ADMIN}),
    "respond.received_profile": frozenset({SCHOOL_ADMIN}),
    # Path admin
    "read.audit_log": frozenset({PATH_ADMIN}),
    "moderate.content": frozenset({PATH_ADMIN}),
    "modify.referential": frozenset({PATH_ADMIN}),
    "reset.user_mfa": frozenset({PATH_ADMIN}),
    # Support
    "read.user_ticket": frozenset({SUPPORT}),
    "read.masked_user_profile": frozenset({SUPPORT}),
}
