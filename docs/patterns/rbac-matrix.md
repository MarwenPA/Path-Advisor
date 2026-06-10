# RBAC Matrix — Pattern doc

**Source:** Story 1.7 (RBAC middleware + matrice d'autorisation).
**Code:** [`apps/api/apps/core/permissions.py`](../../apps/api/apps/core/permissions.py)
**Tests:** [`apps/api/apps/core/tests/test_rbac_permissions.py`](../../apps/api/apps/core/tests/test_rbac_permissions.py)
**CI gate:** [`apps/api/scripts/assert_rbac_declared.py`](../../apps/api/scripts/assert_rbac_declared.py)

This document is the **source of truth** for the Path-Advisor role-based access control matrix. The PRD §"Matrice RBAC" is the product-side spec ; this doc is the engineering implementation contract.

---

## 1. The 6 roles

| Role | `UserRole.value` | Story | Production assignment |
|---|---|---|---|
| Élève | `student` | 1.3 | Self-signup (≥ 15 ans) or via parental opt-in (< 15 ans, Story 1.4) |
| Parent | `parent` | 1.3 | Invitation by linked student (Story 6.1 onwards) |
| Conseiller B2B | `counselor` | 1.6 | Manual provisioning by `path_admin` (Epic 6.5) |
| École partenaire | `school_admin` | 1.6 | Manual provisioning by `path_admin` (Epic 5.6) |
| Admin Path-Advisor | `path_admin` | 1.6 | `manage.py shell` + `is_superuser=True` |
| Support utilisateur | `support` | **1.7** | Manual provisioning by `path_admin` |

---

## 2. Capability matrix

Symbolic capabilities from `apps.core.permissions.ROLE_MATRIX`. Each row is a `(capability, allowed_roles)` pair. **NOT** consumed directly by the permission classes (which group by role for ergonomics) — this is the **documentation source of truth** that `apps/core/tests/test_rbac_permissions.py` cross-checks.

| Capability | Student | Parent | Counselor | School admin | Path admin | Support |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `read.own_profile` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `write.own_profile` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `delete.own_account` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `export.own_data` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `manage.own_mfa` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `disable.own_mfa` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `invite.parent` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `read.linked_child_profile` | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `pay.premium_for_linked_child` | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `read.cohort_aggregate` | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| `read.cohort_student_with_consent` | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| `read.received_profile` | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| `respond.received_profile` | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| `read.audit_log` | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| `moderate.content` | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| `modify.referential` | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| `reset.user_mfa` | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| `read.user_ticket` | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| `read.masked_user_profile` | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

**Notes:**
- `disable.own_mfa` is B2C-only — NFR-S2 mandates MFA for staff. The DPO reset path (Story 1.6 `mfa.reset_by_dpo`) is the only way to clear MFA for staff.
- `read.audit_log` is `path_admin`-only — support users handle tickets with a masked-profile view but do NOT see the full audit trail (cf. Story 1.7 §6 #1).

---

## 3. Permission classes (engineering surface)

All in [`apps/core/permissions.py`](../../apps/api/apps/core/permissions.py).

### Role permissions

| Class | `allowed_roles` | `requires_mfa_verified` | `allow_superuser_bypass` |
|---|---|:---:|:---:|
| `IsStudent` | `{student}` | False | False |
| `IsParent` | `{parent}` | False | False |
| `IsCounselor` | `{counselor}` | **True** | False |
| `IsSchoolAdmin` | `{school_admin}` | **True** | False |
| `IsPathAdmin` | `{path_admin}` | **True** | **True** |
| `IsSupport` | `{support}` | **True** | False |

### Composite permissions

| Class | Roles | Purpose |
|---|---|---|
| `IsB2C` | `{student, parent}` | B2C-only endpoints (MFA disable, in-place enrollment) |
| `IsStaff` | `{counselor, school_admin, path_admin, support}` | Generic staff guard for B2B dashboards (also requires MFA-verified) |
| `IsAuthenticatedAndActive` | all 6 | Auth + `user.is_fully_active` gate (Story 1.4 limited-mode filter). Compose with role permissions. |

### Object-level permissions

| Class | Purpose |
|---|---|
| `IsOwner` | Per-object check `obj.user_id == request.user.id`. Configurable via `owner_field` class attr. |
| `IsOwnerOrPathAdmin` | Same as `IsOwner` but also passes if `request.user.role == "path_admin"` OR `is_superuser=True` (documented DPO-escalation path). |

---

## 4. How to add a new endpoint

3-step checklist. The CI gate `assert_rbac_declared.py` enforces step 1.

**Step 1 — Declare `permission_classes` explicitly on every new view.**

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from apps.core.permissions import IsCounselor

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsCounselor])
def cohort_dashboard(request):
    ...
```

Compose the right primitives. For a B2C-only mutation: `[IsAuthenticated, IsB2C]`. For a staff dashboard: `[IsAuthenticated, IsCounselor]` (MFA-verified is automatic via `IsCounselor.requires_mfa_verified=True`).

**Step 2 — Add a matrix test in `apps/core/tests/test_rbac_permissions.py`.**

For every new sensitive endpoint, add a `(role, endpoint) → expected_status` row to the parametrized matrix. At minimum: one allowed role (200) and one denied role (403).

**Step 3 — Run the CI gate locally before pushing.**

```bash
cd apps/api
DJANGO_SETTINGS_MODULE=path_advisor.settings.test python scripts/assert_rbac_declared.py
```

If the script flags your endpoint, either fix the declaration OR add the URL `name=` to:
- `_PUBLIC_ENDPOINT_WHITELIST` if the endpoint is intentionally anonymous (signup, login, etc.) — comment WHY.
- `_ISAUTHENTICATED_ONLY_WHITELIST` if the endpoint is self-service scoped to `request.user` (e.g., `/me/gdpr-exports/`) — comment WHY.

The whitelist diff is the surface a PR reviewer scrutinizes.

---

## 5. MFA-verified gate (Story 1.6 integration)

Staff permissions (`IsCounselor`, `IsSchoolAdmin`, `IsPathAdmin`, `IsSupport`) default `requires_mfa_verified = True`. The base class refuses unless `request.user.is_verified()` is True (django-otp's `OTPMiddleware` populates this).

A staff user with a valid session cookie but who hasn't passed the MFA challenge sees a `400 MfaEnrollmentRequired` (with `extras_as_extensions=True` per Story 1.6 code-review P7).

**Why not enforce at the login layer?** The login flow already does this — `ThrottledLoginView` returns `mfa_required:true` for users with `requires_mfa`. The permission-class check is defense-in-depth: if a non-MFA session ever exists for a staff user (DPO reset window, future bug, etc.), they're refused at the endpoint.

**B2C permissions** (`IsStudent`, `IsParent`, `IsB2C`) leave `requires_mfa_verified=False`. MFA is opt-in for them.

---

## 6. Object-level permissions

`IsOwner` and `IsOwnerOrPathAdmin` check at the OBJECT layer (called by DRF AFTER `get_object()`):

```python
class GdprExportDownloadView(APIView):
    permission_classes = [IsAuthenticated, IsStudent, IsOwnerOrPathAdmin]

    def get(self, request, pk):
        export = get_object_or_404(GdprExport, pk=pk)
        self.check_object_permissions(request, export)  # ← runs IsOwnerOrPathAdmin
        ...
```

**Configuration:** set `owner_field` on the permission class if your model uses a non-default name:

```python
class IsBulletinOwner(IsOwner):
    owner_field = "uploaded_by_id"  # default: "user_id"
```

**DPO escalation path:** `IsOwnerOrPathAdmin` passes when:
1. `obj.user_id == request.user.id` (the owner), OR
2. `request.user.role == "path_admin"`, OR
3. `request.user.is_superuser is True` (production DPO has both).

Use case: a DPO investigating a complaint must access the user's GDPR export without impersonating them. The audit log captures `actor_id=<dpo>, target_user_id=<victim>` so the action is traceable.

---

## 7. Audit denial — `rbac.access_denied`

Every refusal produces exactly ONE `rbac.access_denied` audit row per request (deduped via `request._rbac_denial_recorded`).

Metadata schema:

```python
{
    "endpoint": "/api/v1/cohorte/students/",
    "method": "GET",
    "required_roles": ["counselor", "path_admin"],
    "actor_role": "student",  # may be "" for anonymous
    "reason": "wrong_role",  # | "not_authenticated" | "not_mfa_verified" | "not_fully_active" | "not_owner"
    "view": "CohortStudentListView",
    # Object-level only:
    "target_user_id": "usr_other",  # only for `reason="not_owner"`
    "actor_user_id": "usr_actor",   # only for `reason="not_owner"`
}
```

**DPO triage queries:**

```python
# Spot escalation attempts (an attacker probing endpoints they shouldn't reach)
AuditLog.objects.filter(
    action="rbac.access_denied",
    actor_id="usr_suspected",
).values("metadata__endpoint", "metadata__reason").distinct()

# Spot patterns: many denials from same IP across multiple actors
AuditLog.objects.filter(action="rbac.access_denied").values(
    "ip_address_hash"
).annotate(count=Count("id")).order_by("-count")[:10]
```

---

## 8. Anti-patterns (don't do this)

- ❌ **Setting `DEFAULT_PERMISSION_CLASSES = [IsAuthenticated]` in DRF settings.** This masks missing declarations — the whole point of the CI gate is that EVERY endpoint declares its permission explicitly.
- ❌ **Checking `request.user.is_superuser` as a generic bypass.** Only `IsPathAdmin` opts in. A superuser who needs to act as a counselor must do so via their actual role.
- ❌ **Writing the audit row inside `dispatch` override.** DRF's permission system is the contract — overrides confuse static analyzers (OpenAPI generator, ruff plugins) and bypass the CI gate.
- ❌ **Scoping `rbac.access_denied` by tenant.** Cross-tenant escalation attempts ARE the signal we want — the audit endpoint is RLS-exempt (Story 1.13 §AC7) so path_admin sees everything.

---

## 9. Deprecation (Story 1.7)

`apps.audit.permissions.IsPathAdmin` is a deprecation shim re-exporting `apps.core.permissions.IsPathAdmin`. Existing imports work (with `DeprecationWarning`) ; remove in Sprint 3 cleanup story (deferred-work entry).

Use the canonical import going forward:

```python
from apps.core.permissions import IsPathAdmin
```

---

## 10. Cross-references

- [Story 1.7 spec](../../_bmad-output/implementation-artifacts/1-7-rbac-middleware-autorisation.md)
- [Story 1.6 — MFA TOTP (powers the MFA-verified gate)](../../_bmad-output/implementation-artifacts/1-6-mfa-staff.md)
- [Story 1.8 — RLS multi-tenant (orthogonal to RBAC; both layers active)](../../_bmad-output/implementation-artifacts/1-8-multi-tenant-rls-postgresql.md)
- [Story 1.13 — Audit log (consumes `rbac.access_denied`)](../../_bmad-output/implementation-artifacts/1-13-journal-audit-acces.md)
- [PRD §Matrice RBAC](../../_bmad-output/planning-artifacts/prd/web-app-saas-specifications-techniques.md#matrice-rbac-permissions-par-rle)
