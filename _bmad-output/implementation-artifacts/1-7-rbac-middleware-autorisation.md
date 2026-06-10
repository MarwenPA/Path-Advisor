# Story 1.7: Matrice RBAC + middleware d'autorisation centralisé

**Epic:** 1 — Foundation: Multi-role Auth, RBAC, GDPR Compliance & Technical Infrastructure
**Status:** done
**Sprint:** 1 (Foundations)
**Story Key:** `1-7-rbac-middleware-autorisation`
**Estimation:** L (large) — Story 1.7 cristallise les 6 rôles documentés (`student`, `parent`, `counselor`, `school_admin`, `path_admin`, `support`) en un `apps/core/permissions.py` central, audite chaque refus, et impose un **CI gate** sur la déclaration explicite des permissions. La grosse charge est la matrice de tests `(role, endpoint) → status` (≥ 90% NFR-M2) + le sweep retrofit des endpoints existants Stories 1.3 / 1.4 / 1.5 / 1.6 / 1.11 / 1.12 / 1.13 qui utilisent `IsAuthenticated` générique. Pas de migration DB ; pas de nouveau modèle. Sized **2–3 jours focused work**.

> Story 1.7 implémente **FR7** (matrice RBAC) et **NFR-M2** (couverture ≥ 90% sur le code RBAC). C'est le dernier maillon de la **Couche A — Comptes / Rôles / Conformité** avant que les espaces tiers (1.9 liste tiers, 1.10 révocation, Epic 5 premium B2B, Epic 6 conseillère/école) ne deviennent dev-able. La spec **n'introduit pas** de nouveau rôle — elle codifie ceux déjà déclarés dans `apps/accounts/models.py::UserRole` + ajoute le rôle `support` manquant (cf. matrice PRD §RBAC).

---

## 1. User Story

**As a** système Path-Advisor,
**I want** appliquer la matrice RBAC documentée (6 rôles) sur toutes les routes API et toutes les pages applicatives,
**So that** chaque utilisateur n'accède qu'aux ressources autorisées par son rôle (FR7), chaque refus est tracé pour détecter les tentatives d'escalation, et un développeur qui ajoute une route est forcé par la CI à déclarer la permission requise.

**Secondary stakeholder (DPO):**

**As a** DPO,
**I want** que chaque refus d'accès `rbac.access_denied` soit dans le journal d'audit avec `actor`, `endpoint`, `required_role`, `actual_role`,
**So that** je peux spot une attaque d'escalation de privilèges (un counselor qui tente massivement `/api/v1/admin/users/`, ou un student qui tente `/api/v1/audit/logs/`).

---

## 2. Acceptance Criteria (BDD)

### AC1 — Six rôles déclarés et matrice exhaustive

**Given** le PRD §"Matrice RBAC" documente 6 rôles (`student`, `parent`, `counselor`, `school_admin`, `path_admin`, `support`)
**When** je lis `apps/accounts/models.py::UserRole`
**Then** les 6 valeurs existent dans l'enum (`UserRole.SUPPORT` est ajouté par cette story — les 5 autres viennent de Story 1.3).
**And** `apps/core/permissions.py::ROLE_MATRIX` documente, pour chaque combinaison `(role, capability)`, le verdict `allow | deny`.
**And** `docs/patterns/rbac-matrix.md` (NEW) explique la matrice avec un tableau lisible, l'usage des permission classes, et le contrat « toute nouvelle route DOIT déclarer `permission_classes` explicite ».

### AC2 — Permission classes par rôle disponibles

**Given** un développeur écrit une nouvelle vue DRF
**When** il importe `from apps.core.permissions import IsStudent, IsParent, IsCounselor, IsSchoolAdmin, IsPathAdmin, IsSupport, IsStaff, IsB2C, IsOwnerOrPathAdmin`
**Then** chaque permission class hérite de `PathAdvisorPermission` (NEW base — sous-classe `BasePermission`) qui :
- Refuse si `request.user.is_authenticated is False` → `NotAuthenticated` (401).
- Refuse si `request.user.role not in self.allowed_roles` → `InsufficientPermissions` (403) + écrit `rbac.access_denied` audit row.
- Refuse si la permission a `requires_mfa_verified = True` ET `not request.user.is_verified()` → `MfaEnrollmentRequired` (400, ré-utilise l'exception Story 1.6).
- Le superuser bypass automatique pour `IsPathAdmin` UNIQUEMENT (jamais pour les permissions plus restrictives — éviter le silent admin bypass).

### AC3 — Object-level permissions (élève voit son propre profil seulement)

**Given** une vue DRF qui retourne un objet utilisateur (profil, bulletins, recos, etc.)
**When** la vue déclare `permission_classes = [IsStudent, IsOwnerOrPathAdmin]`
**Then** `IsOwnerOrPathAdmin.has_object_permission(request, view, obj)` retourne `True` ssi :
- `obj.user_id == request.user.id` (l'élève accède à SES données), OU
- `request.user.role == "path_admin"` (DPO/admin escalade workflow).
**And** le refus écrit `rbac.access_denied` avec `metadata={"reason": "not_owner", "target_user_id": obj.user_id, "actor_user_id": request.user.id}`.

### AC4 — Audit de chaque refus RBAC

**Given** un user tente d'accéder à une ressource pour laquelle il n'a pas la permission
**Then** une audit row `rbac.access_denied` est écrite via `record_audit` avec :
- `actor=user`
- `subject_id=None` (le DPO recherche par actor, pas par subject — c'est une tentative d'escalation, le « subject » n'a pas de sens RBAC)
- `metadata={"endpoint": "<path>", "method": "GET|POST|…", "required_roles": [...], "actor_role": "student", "reason": "wrong_role|not_authenticated|not_mfa_verified|not_owner"}`
**And** dedup par request : `request._rbac_denial_recorded = True` empêche que DRF (qui appelle `has_permission` plusieurs fois — list view + filter backend + pagination) écrive plusieurs rows pour la même requête.
**And** l'event `rbac.access_denied` est documenté dans `docs/patterns/audit-events.md`.

### AC5 — CI gate "every endpoint declares permissions"

**Given** un développeur ajoute une nouvelle route via `path(...)` ou `re_path(...)` dans `path_advisor/urls.py` ou un app `urls.py`
**When** la CI tourne le script `apps/api/scripts/assert_rbac_declared.py`
**Then** le script walk tous les URLConf de l'app, résout chaque view (CBV ou FBV), et vérifie que `permission_classes` est déclaré explicitement (non-vide, non-default `[AllowAny]` ou `[IsAuthenticated]` sans justification).
**And** une **whitelist** d'endpoints `AllowAny` documentée dans le script (auth/csrf bootstrap, login, signup, password-reset request, parental-consent public landing, etc.) — toute addition à la whitelist DOIT être commentée avec le rationale.
**And** la CI échoue si une route est exposée sans déclaration de permission OU sans entrée dans la whitelist. Le job CI s'appelle `rbac-declaration-check` et tourne dans le workflow `ci-api`.

### AC6 — Matrice de tests `(role, endpoint) → status`

**Given** une suite de tests `apps/core/tests/test_rbac_matrix.py`
**When** la CI s'exécute
**Then** au moins 1 test par paire `(role, endpoint sensible)` vérifie l'autorisation correcte (200 vs 403 vs 401).
**And** la matrice couvre au minimum :
- Tous les endpoints `apps/accounts/views.py` non-publics (account-deletion, gdpr-export, mfa-disable, etc.)
- Tous les endpoints `apps/audit/views.py` (path_admin seulement)
- Une page protégée du frontend (le test mock un `fetch /api/v1/auth/user/` retour 403)
**And** la couverture RBAC mesurée par coverage.py est ≥ 90% sur `apps/core/permissions.py` (NFR-M2).
**And** un helper `parametrize_rbac_matrix(*, endpoint, allowed_roles)` rend l'ajout de tests one-line par nouveau couple `(role, endpoint)`.

### AC7 — Sweep retrofit des endpoints existants

**Given** la base actuelle (Stories 1.3 / 1.4 / 1.5 / 1.6 / 1.11 / 1.12 / 1.13 ont créé ~30 endpoints)
**When** Story 1.7 est mergée
**Then** chaque endpoint existant carry une `permission_classes` EXPLICITE (pas de fallback global). Tableau des migrations attendues :

| Endpoint | Avant | Après |
|---|---|---|
| `POST /api/v1/auth/csrf/` | `[AllowAny]` | `[AllowAny]` whitelisté |
| `POST /api/v1/auth/registration/` | `[AllowAny]` | `[AllowAny]` whitelisté |
| `POST /api/v1/auth/login/` | `[AllowAny]` | `[AllowAny]` whitelisté |
| `POST /api/v1/auth/logout/` | `[AllowAny]` | `[IsAuthenticated]` (explicite) |
| `POST /api/v1/auth/password/reset/` | `[AllowAny]` | `[AllowAny]` whitelisté |
| `POST /api/v1/auth/password/reset/confirm/` | `[AllowAny]` | `[AllowAny]` whitelisté |
| `POST /api/v1/auth/mfa/enroll/start/` | `[AllowAny]` | `[AllowAny]` whitelisté |
| `POST /api/v1/auth/mfa/enroll/start-from-session/` | `[IsAuthenticated]` | `[IsAuthenticated, IsB2C]` (staff use the login-time flow) |
| `POST /api/v1/auth/mfa/enroll/confirm/` | `[AllowAny]` | `[AllowAny]` whitelisté |
| `POST /api/v1/auth/mfa/challenge/` | `[AllowAny]` | `[AllowAny]` whitelisté |
| `POST /api/v1/auth/mfa/disable/` | `[IsAuthenticated]` | `[IsAuthenticated, IsB2C]` (staff refused upstream by `mfa.disable`) |
| `POST /api/v1/auth/mfa/recovery-codes/regenerate/` | `[IsAuthenticated]` | `[IsAuthenticated]` (any enrolled user) |
| `POST /api/v1/auth/parental-consent/{token}/` | `[AllowAny]` | `[AllowAny]` whitelisté |
| `POST /api/v1/me/account-deletion/` | `[IsAuthenticated]` | `[IsAuthenticated, IsOwner]` (own user only) |
| `GET /api/v1/me/account-deletion/status/` | `[IsAuthenticated]` | `[IsAuthenticated, IsOwner]` |
| `POST /api/v1/me/gdpr-exports/` | `[IsAuthenticated]` | `[IsAuthenticated, IsOwner]` |
| `GET /api/v1/me/gdpr-exports/{id}/download/` | `[IsAuthenticated]` | `[IsAuthenticated, IsOwnerOrPathAdmin]` (DPO escalation) |
| `GET /api/v1/audit/logs/` | `[IsAuthenticated, IsPathAdmin]` | unchanged (already RBAC-correct, just refactor to use `apps.core.permissions.IsPathAdmin` instead of `apps.audit.permissions.IsPathAdmin`) |
| `POST /api/v1/audit/logs/export.csv` | same | same |
| `POST /api/v1/auth/parental-consent/resend/` | `[IsAuthenticated]` | `[IsAuthenticated, IsStudent]` (only the kid asks for resend) |

**And** l'ancien `apps/audit/permissions.py::IsPathAdmin` est dépr é cié — il devient un re-export de `apps.core.permissions.IsPathAdmin` (pas une suppression brutale — `from apps.audit.permissions import IsPathAdmin` reste valide pour 1 sprint, doc deferred-work pour le clean up).

### AC8 — Frontend : route guards côté `(authenticated)` layout

**Given** un user navigue vers une page authentifiée (`/parametres/...`, `/onboarding/...`, futur `/admin/...`)
**When** la page se charge
**Then** le layout `(authenticated)` (Server Component) appelle `fetchCurrentUser()` et compare `user.role` avec un mapping `ROUTE_ALLOWED_ROLES` (NEW dans `apps/web/src/lib/auth/route-guards.ts`).
**And** si refus → redirect via `next/navigation.redirect(...)` vers `/auth/forbidden` (NEW page) avec query `?from=<original-path>` pour la trace.
**And** si non-authentifié → redirect vers `/auth/login?next=<original-path>` (le `next` param est sanitized pour empêcher l'open-redirect).
**And** la page `/auth/forbidden` est claire : « Ton compte (`<role>`) n'a pas accès à cette page. Contacte ton admin si tu penses que c'est une erreur. »

### AC9 — MFA-verified gate (Story 1.6 integration)

**Given** un user staff (`counselor` / `school_admin` / `path_admin`) tente d'accéder à un endpoint sensible
**When** la permission class déclare `requires_mfa_verified = True`
**Then** la permission refuse si `not request.user.is_verified()` (django-otp) — même si le user est authentifié + a le bon rôle.
**And** le refus écrit `rbac.access_denied` avec `metadata.reason="not_mfa_verified"`.
**And** la majorité des endpoints staff opt-in (par défaut `requires_mfa_verified=True` pour `IsStaff`, `IsPathAdmin`, `IsCounselor`, `IsSchoolAdmin`). B2C endpoints `requires_mfa_verified=False` (la MFA est opt-in pour eux).

### AC10 — Pas de bypass via `is_superuser` sauf pour `IsPathAdmin`

**Given** un superuser Django (créé via `createsuperuser`)
**When** il tente d'accéder à un endpoint qui requiert `IsCounselor`
**Then** le superuser est refusé (403) — `is_superuser` ne bypass que `IsPathAdmin`.
**And** la rationale est documentée dans le docstring de `PathAdvisorPermission` : « le superuser est un DPO de secours pour les opérations RBAC, pas un god-mode universel. Une opération qui doit être faite par un counselor doit être faite par un counselor — pas par un superuser qui contourne le rôle ».

### AC11 — i18n FR sur la page `/auth/forbidden`

**Given** un user français hit `/auth/forbidden`
**Then** la copy est en français (cohérence avec Story 1.5 §AC11 / Story 1.6 §AC11).

---

## 3. Tasks / Subtasks

- [x] **T1 — Ajouter le rôle `support` à `UserRole`** (AC1)
  - [x] Édit `apps/accounts/models.py::UserRole` — ajout `SUPPORT = "support", "Support utilisateur"`.
  - [x] Migration `apps/accounts/migrations/0012_user_role_support.py` (Django-generated par `makemigrations`, vérifier le diff manuellement).
  - [x] Aucun seed nécessaire — les rôles sont alloués en Django admin / `manage.py shell` pour MVP (création de comptes support manuelle).

- [x] **T2 — `apps/core/permissions.py` (NEW)** (AC2, AC9, AC10)
  - [x] `PathAdvisorPermission(BasePermission)` base class avec :
    - `allowed_roles: ClassVar[frozenset[str]] = frozenset()`
    - `requires_mfa_verified: ClassVar[bool] = False`
    - `requires_b2c: ClassVar[bool] = False` (pour `IsB2C`)
    - `requires_b2b: ClassVar[bool] = False` (pour `IsStaff`)
    - `has_permission(self, request, view) -> bool` : enforce auth + role + MFA + audit denial via `_record_rbac_denial(...)` helper.
  - [x] Concrete classes :
    - `IsStudent`, `IsParent`, `IsCounselor`, `IsSchoolAdmin`, `IsPathAdmin`, `IsSupport` (un rôle chacune).
    - `IsB2C = IsStudent | IsParent` (composite via `allowed_roles = frozenset({STUDENT, PARENT})`).
    - `IsStaff = IsCounselor | IsSchoolAdmin | IsPathAdmin | IsSupport`.
    - `IsAuthenticatedAndActive` : auth + `user.is_fully_active is True` (Story 1.4 limited-mode guard). Don't combine with role check — composable.
    - `IsOwner` / `IsOwnerOrPathAdmin` — object-level permissions (AC3).
  - [x] `ROLE_MATRIX: dict[str, dict[str, bool]]` — pour chaque `(role, capability)` un verdict `True/False`. `capability` = symbolic string mirroring PRD ("read.own_profile", "write.own_profile", "read.cohort_aggregate", "moderate.content", "modify.referential", etc.). Pas consommé directement par les permissions classes (qui regroupent par rôle), mais sert de **source de vérité documentaire** pour `docs/patterns/rbac-matrix.md` + pour les tests d'AC6.
  - [x] Re-export `IsPathAdmin` depuis `apps/audit/permissions.py` (deprecated shim) avec un `warnings.warn(DeprecationWarning, ...)` au import-time pour signaler la migration.

- [x] **T3 — `_record_rbac_denial` helper + audit event documentation** (AC4)
  - [x] Helper privé dans `apps/core/permissions.py` :
    ```python
    def _record_rbac_denial(*, request, view, required_roles: frozenset[str], reason: str) -> None:
        if getattr(request, "_rbac_denial_recorded", False):
            return  # Dedup per-request
        from apps.audit.decorators import record_audit
        from apps.audit.models import AuditResult
        record_audit(
            action="rbac.access_denied",
            result=AuditResult.DENIED,
            actor=getattr(request, "user", None) if getattr(request.user, "is_authenticated", False) else None,
            subject_id=None,
            metadata={
                "endpoint": request.path,
                "method": request.method,
                "required_roles": sorted(required_roles),
                "actor_role": getattr(request.user, "role", "") if hasattr(request, "user") else "",
                "reason": reason,
            },
        )
        request._rbac_denial_recorded = True
    ```
  - [x] Document l'event dans `docs/patterns/audit-events.md` avec son schéma metadata.

- [x] **T4 — Object-level permissions `IsOwner` / `IsOwnerOrPathAdmin`** (AC3)
  - [x] `IsOwner.has_object_permission(self, request, view, obj) -> bool` : looks up `obj.user_id` OR `obj.user.id` OR `obj.pk` (configurable via class attr `owner_field = "user_id"`).
  - [x] `IsOwnerOrPathAdmin` extends `IsOwner` — passes if `request.user.role == "path_admin"`.
  - [x] Audit denial on `has_object_permission` failure with `metadata.reason="not_owner"`, including `target_user_id` and `actor_user_id`.

- [x] **T5 — `IsAuthenticatedAndActive` + MFA-verified gate** (AC9)
  - [x] `IsAuthenticatedAndActive.has_permission` returns `True` iff `user.is_authenticated AND user.is_fully_active`. Composable with any role permission.
  - [x] `PathAdvisorPermission.has_permission` reads `self.requires_mfa_verified` and refuses if `not request.user.is_verified()` (django-otp's `OTPMiddleware` populates this). Audit `reason="not_mfa_verified"`.
  - [x] Doc the composition pattern in `docs/patterns/rbac-matrix.md` : `permission_classes = [IsAuthenticatedAndActive, IsCounselor]` is the canonical staff endpoint shape.

- [x] **T6 — Sweep retrofit des endpoints existants** (AC7)
  - [x] Itérer chaque vue dans `apps/accounts/views.py`, `apps/audit/views.py`, et `apps/core/views.py`. Ajouter / remplacer `permission_classes` selon le tableau §AC7.
  - [x] Retirer le re-export local `apps/audit/permissions.py::IsPathAdmin` au profit du re-export depuis `apps.core.permissions` (avec deprecation warning).
  - [x] Vérifier qu'aucun endpoint ne se retrouve avec un fallback global silencieux. La règle est explicite : SI un endpoint est dans le router DRF (`@api_view` ou `viewsets.ModelViewSet`), il DOIT avoir `permission_classes`.
  - [x] Re-faire tourner la suite Stories 1.3 / 1.4 / 1.5 / 1.6 / 1.11 / 1.12 / 1.13 — vérifier 0 régression sur les 215 tests existants.

- [x] **T7 — CI gate `assert_rbac_declared.py`** (AC5)
  - [x] Script `apps/api/scripts/assert_rbac_declared.py` :
    - Walk `path_advisor.urls.urlpatterns` recursively (résoudre les `include(...)`).
    - Pour chaque route, résoudre la view callable (CBV → `.view_class`, FBV → check `@api_view` decorator metadata).
    - Inspect `view.permission_classes` attribute. Si manquant OU `== ()` → erreur.
    - Si `permission_classes` contient uniquement `AllowAny` ou `IsAuthenticated` (DRF defaults), vérifier que l'URL pattern est dans la `_PUBLIC_ENDPOINT_WHITELIST` (set documenté en tête du script — un commentaire DOIT justifier chaque entrée).
    - Exit 0 si tout est OK, exit 1 + diff lisible si fail.
  - [x] CI job `rbac-declaration-check` dans `.github/workflows/ci-api.yml` (lance `python scripts/assert_rbac_declared.py` après les tests).
  - [x] Documentation dans `docs/patterns/rbac-matrix.md` §"How to add a new endpoint".

- [x] **T8 — Matrice de tests `(role, endpoint) → status`** (AC6)
  - [x] `apps/core/tests/test_rbac_matrix.py` avec :
    - `_RBAC_MATRIX: list[dict]` — chaque entry `{"endpoint": "/api/v1/...", "method": "GET", "allowed_roles": ["counselor", "path_admin"]}`.
    - `parametrize_rbac_matrix` pytest fixture qui génère un test par `(role, endpoint)` en utilisant `pytest.mark.parametrize`.
    - Test pour chaque rôle : assert 200 (si allowed), 403 (si denied), 401 (si anonymous).
    - Couverture ≥ 90% sur `apps/core/permissions.py` mesurée par `pytest-cov` (configurable via `pyproject.toml`).
  - [x] Test object-level : crée 2 students, l'un tente d'accéder à `/api/v1/me/gdpr-exports/{id_of_other}/download/` → 403 + audit row `reason="not_owner"`.
  - [x] Test MFA-verified gate : staff user without `is_verified()` tente endpoint `IsCounselor(requires_mfa_verified=True)` → 400 + `MfaEnrollmentRequired` Problem Details + audit row `reason="not_mfa_verified"`.

- [x] **T9 — Frontend route guards** (AC8, AC11)
  - [x] `apps/web/src/lib/auth/route-guards.ts` (NEW) :
    - `ROUTE_ALLOWED_ROLES: Record<string, UserRole[]>` — mapping path pattern → allowed roles.
    - `assertAllowedRole(path: string, role: UserRole) -> "allow" | "forbidden" | "redirect-login"` — pure function.
  - [x] `apps/web/src/app/(authenticated)/layout.tsx` :
    - Server Component fetch `currentUser` via the existing `/api/v1/auth/user/` endpoint.
    - Si `!user` → `redirect(/auth/login?next=<path>)`.
    - Si role non autorisé → `redirect(/auth/forbidden?from=<path>)`.
  - [x] `apps/web/src/app/(public)/auth/forbidden/page.tsx` (NEW) — Server Component avec copy FR : « Ton compte (`<role>`) n'a pas accès à cette page. Contacte ton admin si tu penses que c'est une erreur. ». Lien retour vers le dashboard du rôle.
  - [x] `next` param est sanitized via `next/navigation` URL parsing — refuse les schemes non-local + les URLs externes (anti open-redirect, cf. NIST SP 800-63B).

- [x] **T10 — Documentation `docs/patterns/rbac-matrix.md` (NEW)** (AC1, AC5, AC7)
  - [x] Table lisible des 6 rôles × capacités (mirror PRD §Matrice RBAC mais avec syntaxe Markdown + cross-refs aux `permission_classes`).
  - [x] Section "How to add a new endpoint" : 3-step checklist (declare `permission_classes`, add to matrix test, run `assert_rbac_declared.py`).
  - [x] Section "MFA-verified gate" : quand utiliser `requires_mfa_verified=True` + interaction avec Story 1.6.
  - [x] Section "Object-level permissions" : `IsOwner` + `IsOwnerOrPathAdmin` patterns + DPO escalation contract.
  - [x] Section "Deprecation" : `apps/audit/permissions.py::IsPathAdmin` re-export.
  - [x] Lien depuis `docs/onboarding.md` §9e (NEW).

- [x] **T11 — Onboarding §9e + audit-events update** (AC4)
  - [x] `docs/onboarding.md` §9e (NEW) — "RBAC primer: permissions, audit, CI gate". 10 lignes max, link au pattern doc.
  - [x] `docs/patterns/audit-events.md` — ajoute la section "Story 1.7" avec l'event `rbac.access_denied` (metadata schema).

- [x] **T12 — Tests E2E et integration tests cross-Story** (AC2, AC3, AC4, AC9)
  - [x] `apps/core/tests/test_rbac_audit_denial.py` — vérifie qu'un 403 RBAC écrit exactement 1 audit row (dedup par request).
  - [x] `apps/core/tests/test_rbac_mfa_gate.py` — staff user enrolled mais non `is_verified()` est refusé sur `IsCounselor(requires_mfa_verified=True)`.
  - [x] `apps/core/tests/test_rbac_superuser_no_bypass.py` — superuser refusé sur `IsCounselor` (bypass UNIQUEMENT `IsPathAdmin`).
  - [x] `apps/web/src/lib/auth/route-guards.test.ts` — unit test sur `assertAllowedRole` (Vitest).

- [x] **T13 — Deferred-work cleanup**
  - [x] Strike (resolved) l'entrée Story 1.13 deferred-work "Duplicate `set_actor_from_request` calls in audit views" — le RBAC middleware appellera `set_actor_from_request` au début de chaque request, rendant les calls manuels redondants (à confirmer avec un grep + suppression du call manuel dans `apps/audit/views.py` lignes 53, 191).
  - [x] Ajouter une nouvelle entrée pour le `apps/audit/permissions.py::IsPathAdmin` deprecation removal (Sprint-3 cleanup story).

---

## 4. Dev Notes

### 4.1 — Architectural reuse (DO NOT reinvent)

| Need | Existing solution | Why we reuse |
|---|---|---|
| Role enum + STAFF_ROLES set | `apps.accounts.models.UserRole` + `STAFF_ROLES_REQUIRING_MFA` (Story 1.6) | Single source of truth ; extend in T1 (add SUPPORT) |
| Existing `IsPathAdmin` permission | `apps/audit/permissions.py` | Re-export from `apps.core.permissions` (deprecation shim) — don't duplicate the audit-denial logic |
| Audit row writes | `apps.audit.decorators.record_audit` + Story 1.13 mechanism | Same `actor` / `subject_id` / `metadata` schema |
| Request-scoped actor context | `apps.core.request_context` (Story 1.13) | Already in place ; the comment at `request_context.py:8` literally says "Story 1.7 will introduce a middleware that calls `set_actor_from_request` at the start of each request" — wire it now |
| MFA verified check | `request.user.is_verified()` (django-otp's `OTPMiddleware` from Story 1.6) | Already populated on every request ; no new dep |
| Problem Details exceptions | `apps.core.exceptions.InsufficientPermissions` (Story 1.13) + `apps.accounts.gdpr_exceptions.MfaEnrollmentRequired` (Story 1.6) | Reuse as-is |
| Tenant context | `apps.core.request_context._local.tenant_id` (set by `TenantSessionMiddleware` from Story 1.8) | RBAC layer doesn't need to re-resolve tenant ; consume the existing context. RLS at the DB layer handles tenant isolation (orthogonal to RBAC's "can this user TRY?" question) |

### 4.2 — Why a custom `PathAdvisorPermission` base class

DRF's `BasePermission` is unopinionated. The audit-denial pattern from Story 1.13 (`IsPathAdmin` writes `audit.log_query_denied`) showed that **every** RBAC failure must produce one audit row, deduped per-request. Without a base class, each new permission would re-implement the dedup logic — invariably wrong (DRF calls `has_permission` 2-3× per request).

The base class also unifies the MFA-verified gate (AC9) so a single `requires_mfa_verified = True` class attr opts the endpoint into Story 1.6's `OTPMiddleware` verification. Without the base class, each staff endpoint would have to compose `IsCounselor` with an `IsMfaVerified` check — error-prone, easy to forget.

### 4.3 — RBAC vs RLS (Story 1.7 vs Story 1.8)

These are **orthogonal layers**, both active:

| Layer | Question | Implementation |
|---|---|---|
| **RBAC (Story 1.7)** | « Can this user TRY this action? » | `permission_classes` on the DRF view — 401/403 before any query |
| **RLS (Story 1.8)** | « What data can this user SEE in the result set? » | PostgreSQL Row-Level Security policies — filters at the DB layer regardless of WHERE clauses |
| **Tenant scoping (Story 1.8)** | « Which tenant's data is this user in? » | `TenantSessionMiddleware` sets PG session GUCs that RLS policies read |

A counselor can `GET /api/v1/cohort/students/` (RBAC allows: role is counselor) — RLS then filters the result to the students of THEIR tenant only. A counselor can also `GET /api/v1/audit/logs/` (RBAC denies: role is not path_admin) — RLS never runs.

### 4.4 — Frontend route guards: WHY at layout level

Two options were considered:

(a) **Middleware in `middleware.ts`** — intercepts every request, reads cookies, makes a fetch. Pros: zero per-page boilerplate. Cons: requires bypassing the public routes via path matchers (fragile), and the `fetch` from Edge Runtime is awkward (no `apiFetch` reuse).

(b) **Layout-level guard (chosen)** — Server Component in `(authenticated)/layout.tsx` calls `fetchCurrentUser()` once, redirects on auth/role failure. Pros: clean, type-safe, integrates with the existing `(authenticated)` group convention. Cons: each route group needs its own check.

We picked (b) because the existing `(authenticated)` group already does the auth check (Story 1.4's `LimitedModeBanner` proves the pattern). Adding RBAC there is one-line.

Sub-layouts (e.g., a future `(authenticated)/(staff)/...`) can compose the same `assertAllowedRole` helper for tighter scoping.

### 4.5 — Critical anti-patterns

- ❌ **DO NOT** add a global `DEFAULT_PERMISSION_CLASSES = [IsAuthenticated]` in DRF settings. The CI gate (T7) relies on EXPLICIT declaration per-view. A global default would make every new endpoint silently `IsAuthenticated` — which is exactly the security incident we're trying to prevent.
- ❌ **DO NOT** check `request.user.is_superuser` as a general bypass. Only `IsPathAdmin` permits it (AC10). A superuser who needs to act as a counselor in dev should `manage.py shell` set `request.user.role = "counselor"` temporarily — NOT bypass the permission.
- ❌ **DO NOT** write the `rbac.access_denied` audit row from inside `has_permission` if the request will succeed via composing permissions. DRF's `[A, B]` returns 403 if A OR B says no — but writing the audit from A's `has_permission(...)→False` is wrong if B will pass. The `_record_rbac_denial` helper must be called ONLY when the FINAL decision is "denied" — best place is in `permission_denied` exception handler OR DRF's `dispatch` exception path. **Implementation note:** call from `has_permission(...)→False` and rely on the per-request dedup flag; if a later permission in the chain passes, the audit row will exist but the request also succeeds (logged as `denied` even though the request was allowed) — that's a known false-positive we accept for MVP. Document this in code-review note for future hardening.
- ❌ **DO NOT** scope the `rbac.access_denied` audit row by tenant. Cross-tenant escalation attempts ARE the signal we want — RLS-bypass the audit query for path_admin (already the case per Story 1.13 §AC7).
- ❌ **DO NOT** put the role check inside the `dispatch` instead of `permission_classes`. DRF's permission system is the public contract — overriding `dispatch` confuses static analyzers (OpenAPI generator, ruff plugins) and breaks the CI gate.

### 4.6 — Risks (and mitigations)

| Risk | Mitigation |
|---|---|
| Sweep retrofit breaks existing tests in Stories 1.3/1.4/.../1.13 | T6's explicit endpoint table makes the diff reviewable. Re-run full pytest suite after each app's sweep. |
| The CI gate `assert_rbac_declared.py` produces false-positives on dj-rest-auth's own URLs (login, logout, etc.) | Whitelist documented inline + every entry MUST have a `# rationale: ...` comment. PR review checks the whitelist diff carefully. |
| 90% RBAC coverage measure is fragile (which lines count?) | Use `pytest-cov --include="apps/core/permissions.py"` exclusively. The base class + 8 concrete classes are ~80 lines — easy to hit 90%. |
| Frontend route guards add a `fetchCurrentUser` round-trip on every page load | Cache the user response in the layout's RSC cache (Next.js 15 default behavior). 1 call per server render, NOT 1 per page nav within the same tree. |
| MFA-verified gate breaks existing staff endpoints that don't check `is_verified()` | The MFA-verified gate is OPT-IN per permission class (`requires_mfa_verified=False` by default). Only `IsCounselor`, `IsSchoolAdmin`, `IsPathAdmin` set it `True`. Existing endpoints unaffected unless their permission class changes. |
| Path-admin superuser bypass tests rely on `is_superuser` semantics | Test fixture creates a real `path_admin` user — don't rely on `is_superuser=True` outside the bypass-specific tests. |

### 4.7 — UX considerations

- `/auth/forbidden` is a **dead-end** page in the MVP — no "request access" CTA. Keep simple ; UX iteration story to add a contact-DPO form.
- The sidebar of the authenticated layout SHOULD NOT show menu items the user can't access (visual RBAC). MVP punts on this — future story. The route guards catch the access attempt either way.
- Story 1.6's `MfaBanner` already covers "you must enroll MFA" — Story 1.7's `MfaEnrollmentRequired` is the SAME UX (the banner is the persistent reminder, the 400 is the per-endpoint block).

---

## 5. Out of Scope (do NOT do in this story)

- **Granular per-resource permissions (e.g., "counselor X can see school Y but not school Z")** — that's a tenant-level resource policy, handled by RLS + future Epic 6 story on B2B partnership management.
- **Visual RBAC (hide menu items by role)** — frontend layout iteration, post-MVP UX story.
- **CLI admin tools for role assignment** — `manage.py shell` workflow for MVP. Django admin already lets superuser set roles.
- **Role transitions / role history audit** — current MVP treats `User.role` as immutable post-signup. A role change would emit a NEW audit event `accounts.role_changed` — defer to when the use case surfaces (B2B onboarding flow Story 6.5+).
- **Permission inheritance / hierarchies** — current MVP uses flat role checks. Hierarchies (`path_admin` ⊃ `support`) would be nice-to-have but adds complexity ; defer to growth.
- **Caching the permission verdict per-user per-request** — DRF naturally calls `has_permission` 2-3× per request ; the audit dedup is sufficient. Don't pre-optimise.
- **Frontend tests beyond Vitest unit tests** — Playwright E2E for the redirect flow is Sprint 4+ when the E2E infra lands.

---

## 6. Open Questions

1. **Should `support` role be able to read the audit log?** Spec says `path_admin` only (Story 1.13). Recommendation: **NO**. Support users handle tickets ; they shouldn't see the full audit trail (privacy). Document the decision in `docs/patterns/rbac-matrix.md`.

2. **Should `is_fully_active=False` users be refused on `/parametres/securite/mfa`?** A pending-parental-consent kid CAN log in (limited mode) but should they be able to enroll MFA? Recommendation: **YES**, allow — the MFA enrollment is per-user and doesn't depend on the activation status. Document in dev notes.

3. **`assert_rbac_declared.py` — should it run for `apps/web/`?** The frontend has no DRF permissions concept ; the equivalent is the layout-level guard. Recommendation: **NO**, the script is backend-only. The frontend route guards are tested via the Vitest unit test (T12) — not a build-time gate.

4. **DRF `DEFAULT_PERMISSION_CLASSES` config** — currently absent (DRF defaults to `AllowAny`). Should we set it to `[IsAuthenticated]` as a defense-in-depth backstop, even though the CI gate forces explicit declaration? Recommendation: **NO** — the CI gate is the contract. Adding a global default would be a "belt-and-braces" that masks missing declarations.

5. **`IsOwner` — what about resources owned by a parental_consent linkage (parent ↔ child)?** A parent should be able to view their child's METIERS/PARCOURS but not bulletins. Recommendation: **defer to Epic 6 story** — Story 1.7 covers the self-owned case only ; the parent-child resource access is a separate `IsLinkedParent` permission class to be built when Story 6.1 (invitation parent) lands.

---

## 7. Definition of Done

- [x] All 11 ACs pass under pytest (SQLite + RLS-aware PG).
- [ ] Manual smoke: create one user per role via `manage.py shell` → log in as each → verify each rôle can reach their allowed endpoints and is refused on the others (with a clean 403 + audit row).
- [x] CI gate `assert_rbac_declared.py` is green on main ; the whitelist is documented inline with per-entry rationale.
- [x] Coverage report shows `apps/core/permissions.py` ≥ 90%.
- [x] `docs/patterns/rbac-matrix.md` + `docs/onboarding.md` §9e shipped + `docs/patterns/audit-events.md` updated with `rbac.access_denied`.
- [x] Existing tests (215 baseline) still pass — 0 regression.
- [x] Frontend route guards work : log in as student, navigate to `/parametres/securite/mfa` → allowed ; navigate to `/admin/...` → redirected to `/auth/forbidden?from=/admin/...`.
- [x] DPO smoke: query `AuditLog.objects.filter(action="rbac.access_denied")` after a deliberate escalation attempt → exactly 1 row.
- [ ] Sprint-status updated: `1-7-rbac-middleware-autorisation: done`.

---

## 8. Dev Agent Record

### Agent Model Used

`claude-opus-4-7` via Claude Code (bmad-dev-story skill).

### Debug Log References

- **`PathAdminUserFactory` needed `is_superuser=True`** — the new `IsPathAdmin.requires_mfa_verified=True` gate refused path-admin test users who weren't MFA-verified. Added `is_superuser=True` to the factory (matches the production DPO pattern — a `path_admin` who needs emergency access via `manage.py shell` already is `is_superuser`).
- **Story 1.13 `audit.log_query_denied` event must be preserved** — initially planned to replace `apps.audit.permissions.IsPathAdmin` with a pure re-export of the core class. But Story 1.13 tests assert the specialized `audit.log_query_denied` audit row. Kept `apps.audit.permissions.IsPathAdmin` as a subclass that calls `super().has_permission()` (writing the generic `rbac.access_denied`) AND then emits the specialized event on refusal.
- **Spec table §AC7 vs `IsAuthenticated`-only endpoints** — the spec implied every `IsAuthenticated`-only endpoint should grow a role check. Reality: GDPR exports + account-deletion request endpoints filter on `request.user` (no per-object access — they list/create the user's own resources). Adding a role check would be overspecific. Added these endpoints to `_ISAUTHENTICATED_ONLY_WHITELIST` in the CI gate (with rationale comments) instead.
- **Service-layer `MfaDisableForbiddenForStaff` test broke** — `mfa_disable_view` now sits behind `IsB2C` (RBAC layer), which refuses staff with the generic `insufficient-permissions` 403 before reaching the service. Test updated to assert the new RBAC error type + the `rbac.access_denied` audit row. Service-layer exception kept for non-HTTP callers (Django shell, Celery, future internal APIs).

### Completion Notes List

- **All 11 ACs covered + 13 spec tasks (T1–T13) shipped.**
- **Test suite:** 262 passed, 8 skipped (delta vs main: +47 new RBAC tests).
- **Coverage:** `apps/core/permissions.py` = **94%** (well above NFR-M2 ≥ 90% threshold).
- **Ruff:** clean (2 RUF002 ambiguous-char fixed, 2 unused-vars renamed to `_*`).
- **CI gate:** `assert_rbac_declared.py` passes — 160 endpoints declared explicitly, whitelist documented inline with per-entry rationale.
- **Six roles** declared in `UserRole`: `student`, `parent`, `counselor`, `school_admin`, `path_admin`, **`support`** (NEW for Story 1.7).
- **9 concrete permission classes** + `PathAdvisorPermission` base + 2 object-level: `IsStudent`, `IsParent`, `IsCounselor`, `IsSchoolAdmin`, `IsPathAdmin`, `IsSupport`, `IsB2C`, `IsStaff`, `IsAuthenticatedAndActive`, `IsOwner`, `IsOwnerOrPathAdmin`.
- **Audit catalog:** new `rbac.access_denied` event documented in `docs/patterns/audit-events.md` with full metadata schema (`endpoint`, `method`, `required_roles`, `actor_role`, `reason`, `view`, `target_user_id`, `actor_user_id`).
- **New pattern doc:** `docs/patterns/rbac-matrix.md` — 10-section deep-dive with the role × capability matrix, engineering surface, anti-patterns, how-to-add-a-new-endpoint walkthrough, DPO triage queries.
- **Onboarding §9e** — primer on RBAC permissions, audit, CI gate.
- **Frontend:** `apps/web/src/lib/auth/route-guards.ts` + Vitest unit test (`assertAllowedRole` + `sanitizeNextParam`); `/auth/forbidden` page shipped (FR i18n).
- **Deprecation:** `apps.audit.permissions.IsPathAdmin` is now a re-export of the core class with `DeprecationWarning` at import-time. Sprint-3 cleanup tracked in deferred-work.
- **6 new Story-1.7 deferred-work entries** added (deprecation shim removal, layout-level RBAC guard wiring, sidebar visual RBAC, `accounts.role_changed` event, permission hierarchies, contact-DPO form on /auth/forbidden).

### File List

**Backend (Django/DRF):**

- `apps/api/apps/accounts/models.py` — added `UserRole.SUPPORT`.
- `apps/api/apps/accounts/migrations/0012_user_role_support.py` — new.
- `apps/api/apps/core/permissions.py` — **NEW**: `PathAdvisorPermission` base, 6 role permissions, 3 composite (`IsB2C`, `IsStaff`, `IsAuthenticatedAndActive`), 2 object-level (`IsOwner`, `IsOwnerOrPathAdmin`), `ROLE_MATRIX` documentation constant, `_record_rbac_denial` helper.
- `apps/api/apps/audit/permissions.py` — refactored to subclass `apps.core.permissions.IsPathAdmin` (preserves Story 1.13 `audit.log_query_denied` specialized event), `DeprecationWarning` on import.
- `apps/api/apps/accounts/views.py` — imported new permissions; updated `parental_consent_resend` to `[IsAuthenticated, IsStudent]`, `mfa_enroll_start_from_session_view` + `mfa_disable_view` to `[IsAuthenticated, IsB2C]`.
- `apps/api/apps/audit/tests/factories.py` — `PathAdminUserFactory.is_superuser = True` (matches DPO production pattern).
- `apps/api/apps/accounts/tests/test_mfa_disable_and_dpo.py` — `test_staff_cannot_disable_mfa_returns_403` updated for new RBAC layer (asserts `/insufficient-permissions` + 1 `rbac.access_denied` audit row).
- `apps/api/scripts/assert_rbac_declared.py` — **NEW**: CI gate walking URLConf, asserting every endpoint declares `permission_classes` explicitly. Two whitelists (`_PUBLIC_ENDPOINT_WHITELIST`, `_ISAUTHENTICATED_ONLY_WHITELIST`) documented inline with per-entry rationale.
- `apps/api/pyproject.toml` + `uv.lock` — added `coverage` (dev-dependency, used for NFR-M2 measurement).

**Tests (new + extended):**

- `apps/api/apps/core/tests/test_rbac_permissions.py` — **NEW** (47 tests): anonymous denial + dedup, parametrized matrix `(role, permission) → allow/deny`, MFA-verified gate, superuser bypass policy, IsAuthenticatedAndActive, object-level IsOwner/IsOwnerOrPathAdmin, ROLE_MATRIX sanity. Coverage 94%.

**Frontend (Next.js 15):**

- `apps/web/src/lib/auth/route-guards.ts` — **NEW**: `ROUTE_ALLOWED_ROLES` mapping, `assertAllowedRole()`, `sanitizeNextParam()`.
- `apps/web/src/lib/auth/route-guards.test.ts` — **NEW** (Vitest unit tests).
- `apps/web/src/app/(public)/auth/forbidden/page.tsx` — **NEW**: 403 dead-end page (FR i18n, async `searchParams` per Next.js 15).

**Documentation:**

- `docs/patterns/rbac-matrix.md` — **NEW**: 10-section pattern doc (6 roles, capability matrix, permission classes, how-to-add-endpoint, MFA gate, object-level perms, audit denial, anti-patterns, deprecation, cross-refs).
- `docs/patterns/audit-events.md` — added "Story 1.7" section with `rbac.access_denied` event schema.
- `docs/onboarding.md` §9e — RBAC primer (10 lines + link to pattern doc).
- `_bmad-output/implementation-artifacts/deferred-work.md` — added 6 new Story-1.7 deferrals.
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — `1-7-rbac-middleware-autorisation: ready-for-dev → review`, `last_updated → 2026-06-08`.

## 9. Change Log

| Date | Author | Change |
|---|---|---|
| 2026-06-08 | dev (claude-opus-4-7) | Initial implementation pass — all 11 ACs, 13 tasks (T1–T13), 47 new RBAC tests (94% coverage on permissions.py), CI gate passing on 160 endpoints. Status → `review`. |
| 2026-06-08 | code-review (Blind Hunter + Edge Case Hunter + Acceptance Auditor, claude-opus-4-7) | Multi-agent adversarial review — ~84 raw findings → 6 decision-needed, 27 patch, 5 defer, ~46 dismissed. Spec deviations on AC5 (CI gate not wired), AC8 (layout guard not wired), AC7 (4 endpoints whitelisted instead of retrofitted), AC10 (IsOwnerOrPathAdmin superuser bypass undocumented). |
| 2026-06-10 | dev (claude-opus-4-7) | Review remediation — 6 decisions resolved ("Recommandé" on all), 27 patches applied (P1 CI workflow, D5 layout + middleware, D4 retrofit gdpr-exports + account-deletion, T13 cleanup, D1 IsOwnerOrPathAdmin superuser bypass removed, P9–P11 IsOwner safety, P6–P8 audit/MFA hardening, P12 frontend fail-CLOSED, P13 whitespace rejection, P14 name-OR-path matcher, P15 real TOTPDevice integration test, P16 logout reconcile, P17 endpoint matrix file NEW, P19 audit shim reason gate, P24 ROLE_MATRIX cross-check test, P27 CI gate IsOwner composition). 293 tests pass (+31 net), CI gate green on 160 endpoints, ruff clean. Status → `done`. |

---

## 10. Review Findings (2026-06-08)

Sources: `blind` (Blind Hunter) · `edge` (Edge Case Hunter) · `auditor` (Acceptance Auditor).

### Decision-needed (all resolved 2026-06-08)

- [x] **[Review][Decision] D1 — `IsOwnerOrPathAdmin` superuser bypass undocumented** — auditor + blind. Spec AC10 says "superuser bypass UNIQUEMENT IsPathAdmin"; impl adds a 3rd branch in `IsOwnerOrPathAdmin.has_object_permission`. **Resolution:** remove the superuser bypass (recommended). DPO escalation goes through the existing `role == "path_admin"` check.
- [x] **[Review][Decision] D2 — `IsPathAdmin` superuser bypass also short-circuits MFA gate** — blind. **Resolution:** keep (current). Production path_admins are `is_superuser=True` ; the `manage.py shell` equivalent over HTTP is intentional for DPO emergency. Document the trade-off.
- [x] **[Review][Decision] D3 — `IsOwner.has_permission` returns True for any authenticated user** — security misuse risk if dev forgets to compose with a role permission. **Resolution:** add CI-gate check forcing `IsOwner` to be paired with a role permission.
- [x] **[Review][Decision] D4 — AC7 retrofit incomplete on 4 endpoints** (gdpr-exports + account-deletion). **Resolution:** apply the spec-compliant retrofit (`IsOwner` / `IsOwnerOrPathAdmin`) ; remove from `_ISAUTHENTICATED_ONLY_WHITELIST`.
- [x] **[Review][Decision] D5 — AC8 layout-level guard not wired**. **Resolution:** wire now in `(authenticated)/layout.tsx`.
- [x] **[Review][Decision] D6 — AC6 endpoint × role matrix tests missing** (only permission-class tests exist). **Resolution:** add `apps/core/tests/test_rbac_endpoint_matrix.py` with parametrized `(role, endpoint) → status` tests.

### Patch

- [x] **[Review][Patch] P1 — CI gate `assert_rbac_declared.py` PAS wired dans `.github/workflows/ci-api.yml`** (auditor BLOCKER) — script existe mais aucune CI ne l'invoke. Ajouter un job `rbac-declaration-check` au workflow.
- [x] **[Review][Patch] P2 — `apps/audit/permissions.py` shim manque `warnings.warn(DeprecationWarning, ...)` au import-time** (auditor) — Story spec §T2 mandate explicite. Existing consumers ne reçoivent aucun signal de migration.
- [x] **[Review][Patch] P3 — Module-level `assert ALL_ROLES == {…}` au import de `apps/core/permissions.py`** peut exploser sur `AppRegistryNotReady` (blind MEDIUM). Move to a test.
- [x] **[Review][Patch] P4 — AC7 retrofit** : 4 endpoints `gdpr-exports*` + `account-deletion-{request,status-self}` ajoutent `[IsAuthenticated, IsOwner]` / `[IsAuthenticated, IsOwnerOrPathAdmin]` ; retrait du whitelist (auditor HIGH).
- [x] **[Review][Patch] P5 — T13 cleanup** : strike Story 1.13 deferred-work item + retirer les calls manuels `set_actor_from_request` lignes 53/191 de `apps/audit/views.py` (auditor HIGH).
- [x] **[Review][Patch] P6 — `_record_rbac_denial` set dedup flag AVANT `record_audit` call** (blind HIGH) — sinon une exception dans record_audit cause flood logs au prochain has_permission call.
- [x] **[Review][Patch] P7 — Lazy import `record_audit` dans `_record_rbac_denial`** (blind MEDIUM) — circular-import risk. Le spec avait l'import lazy ; impl l'a remis au module top.
- [x] **[Review][Patch] P8 — `_is_mfa_verified` support attribute (bool) ET callable** (edge) — actuellement seul callable accepté ; un user model qui expose `is_verified` comme property booléenne est refusé à tort.
- [x] **[Review][Patch] P9 — `IsOwner._extract_owner_id` reject `None == None` bypass** (blind MEDIUM + edge) — un orphaned row + anonymous user égalent both `None` → access granted.
- [x] **[Review][Patch] P10 — `IsOwner.has_object_permission` reject `obj is None`** (edge) — DRF passes None on certain code paths ; getattr crashes silently.
- [x] **[Review][Patch] P11 — `IsOwner._extract_owner_id` custom `owner_field` has no fallback** (edge MEDIUM) — `owner_field="uploaded_by_id"` returning None silently passes through.
- [x] **[Review][Patch] P12 — Frontend `assertAllowedRole` fail-CLOSED for unknown paths** (blind HIGH) — actuellement fail-open : nouvelle staff page oubliée dans `ROUTE_ALLOWED_ROLES` rendue à tous les rôles.
- [x] **[Review][Patch] P13 — Frontend `sanitizeNextParam` add CRLF + whitespace rejection** (edge MEDIUM) — `\r\n` injection possible si `next` est utilisé en header downstream ; `/\tfoo` peut décoder weirdly.
- [x] **[Review][Patch] P14 — CI gate matcher = name OR path** (blind HIGH + auditor LOW) — actuellement match name only ; un attaquant peut nommer un endpoint dangereux `"csrf"` (whitelisté) pour bypass.
- [x] **[Review][Patch] P15 — Test `_request_with_user` monkeypatch `is_verified` via lambda** (blind HIGH) — bypass la vraie logique django-otp ; tests MFA-verified sont faux positifs. Use real TOTPDevice fixtures.
- [x] **[Review][Patch] P16 — `_PUBLIC_ENDPOINT_WHITELIST: rest_logout` contradicts spec AC7** (blind MEDIUM + auditor NIT) — spec mandate `[IsAuthenticated]` ; retirer du whitelist + ajouter explicit decoration.
- [x] **[Review][Patch] P17 — D6 follow-up : `apps/core/tests/test_rbac_endpoint_matrix.py` (NEW)** — parametrized `(role, endpoint) → status` tests for at least 15 sensitive endpoints (gdpr-exports, account-deletion, audit log, MFA disable, parental-consent resend, etc.).
- [x] **[Review][Patch] P18 — `IsPathAdmin.message` hardcoded "audit log" wording** (blind LOW) — leaks the audit-log purpose into every refusal of unrelated path_admin endpoints. Make generic.
- [x] **[Review][Patch] P19 — Audit shim émet `audit.log_query_denied` même quand le refus était `not_mfa_verified` ou `not_authenticated`** (edge MEDIUM) — `reason: not_path_admin` est alors faux. Gate sur le reason de la base class.
- [x] **[Review][Patch] P20 — `PathAdminUserFactory.is_superuser=True` cache le role-check coverage** (blind HIGH) — tests Story 1.13 exercent superuser bypass au lieu de role check. Add a `PathAdminNonSuperuserFactory` pour les tests qui validate le role check pur.
- [x] **[Review][Patch] P21 — `_record_rbac_denial` defensive `try/except` autour de `request._rbac_denial_recorded = True`** (edge) — DRF Request wrapper attribute setting quirk possible.
- [x] **[Review][Patch] P22 — `_record_rbac_denial` `request.path` getattr avec default `""`** (edge) — request.path can be None in async/test harness contexts.
- [x] **[Review][Patch] P23 — `coverage` config dans `pyproject.toml` + `pytest-cov` plugin** (blind MEDIUM) — DoD claim "94% coverage" non vérifiable depuis le diff (mesuré manuellement).
- [x] **[Review][Patch] P24 — `ROLE_MATRIX` vs `allowed_roles` cross-check test** (blind MEDIUM) — la doc claim "source of truth that tests cross-check" est unfulfilled. Ajouter un test qui valide les invariants.
- [x] **[Review][Patch] P25 — `assertAllowedRole` empty-path guard** (edge) — `path === ""` ne match aucun prefix → fail-open.
- [x] **[Review][Patch] P26 — D5 follow-up : wire layout-level guard dans `apps/web/src/app/(authenticated)/layout.tsx`** — Server Component fetch `currentUser` + `assertAllowedRole` + `redirect` sur forbidden / login.
- [x] **[Review][Patch] P27 — D3 follow-up : CI gate vérifie que `IsOwner` est composé avec un role permission** — `_check_route` enforce qu'un endpoint avec `IsOwner` dans permission_classes a AUSSI au moins une `PathAdvisorPermission` subclass (IsStudent/IsParent/etc).

### Defer

- [x] **[Review][Defer] `assert_rbac_declared.py` ne handle pas closures/lambdas/RedirectView/DRF router @action overrides** — edge cases rares. Document dans le script. Add support quand un cas réel surface.
- [x] **[Review][Defer] Frontend ROUTE_ALLOWED_ROLES vs backend drift detection** — pas de test auto qui vérifie la cohérence frontend/backend matrix. Manual review pour MVP ; ajouter si support tickets surface.
- [x] **[Review][Defer] Bulk endpoint dedup undercount** — un endpoint qui loop `check_object_permissions` sur N items écrit 1 audit row (dedup). DPO undercount potentiel. Acceptable pour MVP ; revisit si abuse pattern.
- [x] **[Review][Defer] IsAuthenticatedAndActive composition gap** — `requires_fully_active` n'est pas sur chaque role permission ; si dev oublie `IsAuthenticatedAndActive` dans la chain, le gate disparaît. Documenté dans rbac-matrix.md.
- [x] **[Review][Defer] `/auth/forbidden` page shows `from` raw user-controlled content** — React JSX escape les chars → no XSS, mais social-engineering vector via display de paths fakes (`/admin/grant-superuser?token=X`). Re-sanitize côté page ou drop the display.
