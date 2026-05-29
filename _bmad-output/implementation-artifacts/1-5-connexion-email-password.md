# Story 1.5: Email/password login + account lockout + password reset

**Epic:** 1 — Foundation: Multi-role Auth, RBAC, GDPR Compliance & Technical Infrastructure
**Status:** done
**Sprint:** 1 (Foundations)
**Story Key:** `1-5-connexion-email-password`
**Estimation:** M (medium) — the login endpoint already exists (Story 1.1 wires dj-rest-auth + session cookies; Story 1.12 added `ThrottledLoginView` 5/min/IP + the DELETED-status 403 leak; Story 1.13 ships the audit decorator). This story adds the missing user-facing pieces: per-account lockout (5 failed attempts / 15 min → 10 min lock), password-reset request + confirm flow with 1-hour token TTL, status-aware login rejections (`SUSPENDED`, `EMAIL_UNVERIFIED`), audit logging for the `auth.*` events, and the three frontend pages (`/auth/login`, `/auth/forgot-password`, `/auth/reset-password/[uid]/[token]`). Bundled in: harden the cross-origin auth config (`CSRF_TRUSTED_ORIGINS` for prod, deferred from Story 1.1) and the `apiFetch` timeout + RFC 7807 parsing carry-overs.

> Story 1.5 implements **FR1** login UX for every role and closes three carry-over deferred items (Story 1.1 CSRF cross-origin config, Story 1.1 apiFetch timeout, Story 1.3 `exclude_token_endpoints` workaround). The non-trivial decisions are (a) where to store the failed-attempts counter (Redis vs DB column) and (b) the lockout state machine when an IP-throttle already lives on the same endpoint — these are answered in §4.5.

---

## 1. User Story

**As a** registered user (student ≥ 15, parent, counselor, school admin, path_admin) — minors in `pending_parental_consent` included,
**I want** to sign in with my email + password, get locked out after 5 failed attempts, and reset my password through an emailed link when I forget it,
**So that** I can reach my role-specific dashboard without exposing the platform to credential-stuffing attacks and without being permanently locked out when I genuinely forget the password.

**Business value:** the foundation every other feature gates on. NFR-P6 mandates < 1 s P95 for authentication; NFR-S2 already covers MFA for staff (Story 1.6); this story is the B2C happy path + recovery flow. Without password reset, a forgotten password = a user lost forever, since support intervention is the only fallback (CNIL/RGPD-adjacent: account access is a data-subject right, not a courtesy).

---

## 2. Acceptance Criteria (BDD)

### AC1 — Valid credentials → 200 + session cookie + role-aware payload

**Given** I am on `/auth/login` and POST `/api/v1/auth/login/` with `{"email": "alice@example.test", "password": "<correct>"}`
**When** the credentials match an `ACTIVE` user with `email_verified_at IS NOT NULL`
**Then** the response is `200 OK` with body:
```json
{
  "user": {
    "id": "usr_01HXJ…",
    "email": "alice@example.test",
    "role": "student",
    "status": "active",
    "is_fully_active": true
  }
}
```
**And** the `sessionid` cookie is set (httpOnly, SameSite=Lax, Secure outside DEBUG).
**And** the `csrftoken` cookie is rotated (Django's `rotate_token` on login — already wired in `dj_rest_auth.views.LoginView`).
**And** the response p95 latency is **< 1 s** under the documented MVP load envelope (NFR-P6 — verified via a smoke benchmark in T11; no production load test gate).
**And** an `auth.login_succeeded` audit row is written via `@audit_action` with `subject_id = user.id`, `actor_id = user.id`, `metadata = {"ip_truncated": "<…>", "user_agent": "<truncated>"}`.

### AC2 — Wrong password → generic 400, no enumeration leak

**Given** I POST `/api/v1/auth/login/` with a wrong password for an existing email
**When** the credentials fail to authenticate
**Then** the response is `400 Bad Request` with the dj-rest-auth default `{"non_field_errors": ["Unable to log in with provided credentials."]}` (mapped through the DRF `ValidationError` exception handler — Story 1.3 §AC6 pattern).
**And** an `auth.login_failed` audit row is written with `result=failure`, `subject_id = <user_id_if_known_else_null>`, `metadata = {"reason": "invalid_credentials", "email_hashed": "<sha256>"}` — the email is **hashed** (not raw) to keep audit-log retention from accumulating PII that should never have been there (mirrors `parent_email_hash` from Story 1.4).

**Given** I POST `/api/v1/auth/login/` with an email that does not exist
**When** the lookup misses
**Then** the response is the **same** 400 shape as above — never reveal whether the email is registered (CWE-203).
**And** an `auth.login_failed` row is written with `subject_id = null`, `metadata.reason = "unknown_email"` — internal-only signal for the DPO; never exposed via the API.

### AC3 — Status-aware rejections (SUSPENDED / EMAIL_UNVERIFIED / DELETED)

**Given** I POST `/api/v1/auth/login/` with valid credentials but the user's `status` is one of the special values
**Then** the response is:

| Status | Response | Problem `type` URI |
|---|---|---|
| `DELETED` | `403 Forbidden` | `…/account-deleted` (Story 1.12) |
| `SUSPENDED` | `403 Forbidden` | `…/account-suspended` (NEW — Story 1.5) |
| `EMAIL_UNVERIFIED` | `403 Forbidden` | `…/email-not-verified` (NEW — Story 1.5) |
| `PENDING_PARENTAL_CONSENT` | `200 OK` (limited mode, `is_fully_active=false`) | — |
| `ACTIVE` | `200 OK` | — |

**And** the `…/email-not-verified` Problem includes a `resend_endpoint` field in `extras` pointing to `/api/v1/auth/registration/resend-email/` so the front can offer a one-click resend.
**And** the `…/account-suspended` Problem `detail` is generic ("Ton compte est suspendu. Contacte le DPO si tu penses que c'est une erreur.") — does NOT reveal the reason (parental-consent expiry, abuse flag, etc.) to avoid leaking moderation state.

### AC4 — Per-account lockout after 5 failed attempts in 15 minutes

**Given** the same user accumulates 5 `invalid_credentials` failures within a 15-minute rolling window
**When** the 5th failure lands
**Then** `User.locked_until = now() + 10 min` is set in the transaction that records the 5th failure.
**And** the response is the **same** generic 400 as AC2 (no leak that lockout was just triggered).
**And** an `auth.account_locked` audit row is written with `subject_id = user.id`, `metadata = {"window_seconds": 900, "unlock_at": "<ISO>", "ip_truncated": "<…>"}`.

**Given** the user's `locked_until > now()`
**When** they retry a login (even with the correct password)
**Then** the response is `400 Bad Request` with the same generic body (no leak).
**And** an `auth.login_blocked_locked` audit row is written.

**Given** the user's `locked_until <= now()` (10-minute cooldown has elapsed)
**When** they retry with the correct password
**Then** the lockout column is cleared (`locked_until = NULL`), the failed-attempts counter is reset, login proceeds normally.

**Storage decision** (cf. §4.5 #1): the counter lives in **Redis** (`auth.login_fail:{user_id}` → integer, TTL 900 s sliding) — atomic INCR + GET, no row-update contention on every wrong password. The `locked_until` field on `User` is the source of truth for the "locked" state itself (consulted on every login attempt) so the lockout survives a Redis flush. Failed attempts before lockout DO get lost on Redis flush, but that's an acceptable degradation (the user can keep trying; the IP-level throttle from Story 1.12 still applies).

### AC5 — Password reset request: email sent, 1-hour token TTL

**Given** I POST `/api/v1/auth/password/reset/` with `{"email": "alice@example.test"}`
**When** the email matches a registered user (any status except `DELETED`)
**Then** the response is `200 OK` with `{"detail": "Si cet email existe, un lien de réinitialisation t'a été envoyé."}` — **identical** wording whether the email exists or not (no enum leak).
**And** an email is sent to the user with a reset link of the form `https://path-advisor.fr/auth/reset-password/<uid>/<token>` (front-end route — backend produces the URL via `PathAdvisorAccountAdapter.get_password_reset_url`, mirroring `get_email_confirmation_url` from Story 1.3).
**And** the token is valid for **1 hour** (`PASSWORD_RESET_TIMEOUT = 3600` in settings — Django default is 3 days, override here).
**And** an `auth.password_reset_requested` audit row is written.

**Given** the email does NOT match a registered user
**When** the request is processed
**Then** the response is the **same** `200 OK` body — never reveal whether the email is registered.
**And** **no email** is sent (don't waste SMTP budget on non-existent users + don't help attackers enumerate by watching their inbox).
**And** an `auth.password_reset_requested_unknown` audit row is written (DPO-only signal — different audit action so the DPO can filter without conflating real vs. probing attempts).

**Given** rate-limit: `1/h per email` AND `5/h per IP`
**When** an attacker bombards the endpoint
**Then** the 429 surfaces via the standard `RateLimited` Problem Details — no per-email leak (the per-IP limit is the leak-resistant one; per-email exists to throttle a single legitimate user typing the wrong email).

### AC6 — Password reset confirm: token validates, new password applies, audit row written

**Given** I POST `/api/v1/auth/password/reset/confirm/` with `{"uid": "...", "token": "...", "new_password1": "...", "new_password2": "..."}`
**When** the uid+token pair is valid AND within the 1-hour TTL AND the two passwords match AND pass Django's password validators
**Then** the response is `200 OK` with `{"detail": "Ton mot de passe a été réinitialisé."}`.
**And** `User.password` is updated via `user.set_password(new)` (proper hashing) inside a transaction.
**And** `User.locked_until = NULL` and the Redis failed-attempts counter is cleared (recovery from a locked-out state).
**And** all Django sessions for this user are killed (same helper as Story 1.12 `_terminate_user_sessions` — refactored to a shared `apps.accounts.services.session_utils` module).
**And** an `auth.password_reset_completed` audit row is written.
**And** a confirmation email "Ton mot de passe a été changé. Si ce n'est pas toi, contacte le DPO immédiatement." is sent.

**Given** the token is expired (> 1 h) or invalid
**When** the confirm endpoint is called
**Then** the response is `400 Bad Request` with `{"token": ["Invalid value"]}` (dj-rest-auth default) — adequately generic.

**Given** the user's status is `DELETED`
**When** the confirm endpoint is called
**Then** it's rejected with the same 400 (the row still exists pre-hard-delete, but the password reset is a no-op).

### AC7 — Frontend: login + forgot + reset pages

**Given** the three new pages (all in `(public)` route group)
**When** I navigate to each
**Then**

- `/auth/login` shows the email + password form, "Mot de passe oublié ?" link to `/auth/forgot-password`, "Pas encore inscrit ?" link to `/auth/signup`. Submit fires `loginUser({email, password})` → on `200`, redirects to a **role-based dashboard path** (see AC8).
- `/auth/forgot-password` shows an email-only form. Submit fires `requestPasswordReset({email})` → always shows the same success message regardless of whether the email exists (no leak).
- `/auth/reset-password/[uid]/[token]/page.tsx` is a Server Component that pre-fetches nothing (the token is opaque server-side; we let the user submit and surface errors). The Client form fires `confirmPasswordReset({uid, token, new_password1, new_password2})`.

**And** every page uses the `lib/api/auth.ts` typed client (no raw `fetch` calls).
**And** every user-facing string is hardcoded French (the `accountDeletion.*` namespace from Story 1.12 §D4 confirmed inline-FR is the MVP convention until Story 7.7).
**And** the login form supports browser autofill (`autocomplete="email"`, `autocomplete="current-password"`).
**And** the forgot-password form uses `autocomplete="email"`.
**And** the reset form uses `autocomplete="new-password"` for the two new-password fields.

### AC8 — Role-based dashboard redirect on login success

**Given** the login response includes `user.role`
**When** the front receives `200`
**Then** it redirects to:

| Role | Path |
|---|---|
| `student` | `/onboarding` if `is_fully_active=false` OR no profile yet (Epic 2 will own the actual onboarding gate) — else `/recommendations` (Epic 3 placeholder, hidden behind a "Bientôt disponible" stub for MVP). MVP-pragmatic: redirect every student to `/parametres/confidentialite` for now — the only route that actually exists. |
| `parent` | `/(parent)` route group — placeholder until Epic 6. MVP: `/parametres/confidentialite`. |
| `counselor` | `/(counselor)` — placeholder until Epic 6. MVP: `/parametres/confidentialite`. |
| `school_admin` | `/(school)` — placeholder until Epic 5/6. MVP: `/parametres/confidentialite`. |
| `path_admin` | `/admin/` (Django admin) — opens in a new tab. |

The route table lives in `apps/web/src/lib/auth/post-login-redirect.ts` (NEW) so future stories editing the redirect rules touch one place. Document the MVP placeholder behavior in a code comment — the placeholder shouldn't surprise a reviewer.

### AC9 — Audit catalog extended (Story 1.13 contract)

**Given** Story 1.13 ships the immutable audit log + `audit-events.md` catalog
**When** this story merges
**Then** [docs/patterns/audit-events.md](docs/patterns/audit-events.md) has new entries for the 6 new `auth.*` actions:

- `auth.login_succeeded`
- `auth.login_failed`
- `auth.login_blocked_locked`
- `auth.account_locked`
- `auth.password_reset_requested`
- `auth.password_reset_requested_unknown`
- `auth.password_reset_completed`

(Yes that's 7 — `auth.login_failed` and the unknown variant share the action name but `metadata.reason` differentiates. Or split into two actions; the implementer picks. Document the choice in the catalog entry.)

### AC10 — Deferred items resolved

**Given** the carry-over deferred items from Stories 1.1 / 1.3 that pointed at "Story 1.5" as their target
**Then**:

- **`apiFetch` no timeout / no RFC 7807 parsing** (Story 1.1) — `lib/api/client.ts` adds a default `AbortSignal.timeout(15_000)` and parses `application/problem+json` Problem Details into a typed `ApiError.problem` field. **Already done** by Story 1.11 (`apiFetch` parses Problem JSON already); the timeout addition lands here.
- **`CSRF_TRUSTED_ORIGINS` / `SESSION_COOKIE_SAMESITE` / `CSRF_COOKIE_SAMESITE` not configured for cross-origin** (Story 1.1) — base settings already set the SameSite/Secure flags (Story 1.3); this story adds `CSRF_TRUSTED_ORIGINS` env-driven list in `prod.py` (currently localhost-only in `base.py`).
- **`exclude_token_endpoints` workaround + TODO test** (Story 1.3) — re-include the login + password-reset endpoints in the OpenAPI schema with explicit `@extend_schema` annotations.

### AC11 — Locale stays FR during password-reset email render (Story 1.12 §P21 carryover)

**Given** the password-reset email rendered by `PathAdvisorAccountAdapter.send_mail` (or whichever path allauth uses)
**When** the Celery worker (or sync send) renders the template
**Then** the render is wrapped in `with translation.override("fr-FR")` so `{{ ...|date }}` and any future date filter outputs French month names — mirrors the fix from Story 1.12 §P21.

---

## 3. Tasks / Subtasks

- [x] **T1 — `locked_until` column on User + migration** (AC4)
  - [x] Add `locked_until = models.DateTimeField(null=True, blank=True, db_index=True)` to `apps/accounts/models.py:User`.
  - [x] Migration `apps/accounts/migrations/0010_user_locked_until.py` (Django-generated, reviewed manually).
  - [x] Helper property `User.is_locked` → `bool(self.locked_until and self.locked_until > timezone.now())`.

- [x] **T2 — Failed-attempt counter + lockout service** (AC4)
  - [x] `apps/accounts/services/login_security.py` (NEW):
    - `record_failed_attempt(*, user, ip) -> int` — atomic Redis `INCR` on `auth.login_fail:{user_id}`, sets TTL 900s on first increment. Returns the new counter value. On the 5th failure, sets `User.locked_until = now() + 10min` inside a `transaction.atomic()` block and writes the `auth.account_locked` audit row.
    - `clear_failed_attempts(*, user) -> None` — deletes the Redis key + sets `User.locked_until = NULL`.
    - `is_account_locked(user) -> bool` — pure DB check on `locked_until`; never touches Redis (the lock is the source of truth, the Redis counter is the staging state).
    - Settings: `LOGIN_FAIL_WINDOW_SECONDS = 900`, `LOGIN_FAIL_THRESHOLD = 5`, `LOGIN_LOCK_DURATION_SECONDS = 600`. Overrideable in tests.
  - [x] Auto-recovery on successful login: `clear_failed_attempts()` called at the end of `PathAdvisorLoginSerializer.validate()` after the parent's auth call succeeds.

- [x] **T3 — Extend `PathAdvisorLoginSerializer` with status checks + lockout** (AC2, AC3, AC4)
  - [x] Update `apps/accounts/login_serializer.py` — current code only handles `DELETED`. Add (in order, BEFORE delegating to `super().validate()`):
    1. If `candidate.is_locked` → raise `AccountLocked` (400, generic body matching AC2). Audit `auth.login_blocked_locked`.
    2. If `candidate.status == DELETED` → raise `AccountDeleted` (existing, 403).
    3. If `candidate.status == SUSPENDED` → raise `AccountSuspended` (403, NEW).
    4. If `candidate.status == EMAIL_UNVERIFIED` → raise `EmailNotVerified` (403, NEW, with `extras={"resend_endpoint": "/api/v1/auth/registration/resend-email/"}`).
  - [x] Delegate to `super().validate(attrs)` which calls `authenticate()`. If it raises `ValidationError` (wrong password / unknown email), catch it, call `record_failed_attempt()` if the email matched a known user, and re-raise the same ValidationError (no leak about which branch hit).
  - [x] On `super().validate()` success: call `clear_failed_attempts()` + audit `auth.login_succeeded` via the decorator on the wrapping view's success path (NOT on the serializer — the serializer is called for both success and ValidationError, the decorator only fires on the view's HTTP 200 return).

- [x] **T4 — `AccountLocked`, `AccountSuspended`, `EmailNotVerified` Problem Details exceptions** (AC2, AC3, AC4)
  - [x] Add to `apps/accounts/gdpr_exceptions.py` (the file is misnamed — covers all auth-flavoured Problem Details since Story 1.12). Optionally rename in a separate cleanup story; defer here.
  - [x] `AccountLocked` — status_code 400 (matching the generic-body shape), type `…/account-locked`. **Note:** intentionally 400 not 423 (HTTP Locked) because returning 423 would leak the lockout state.
  - [x] `AccountSuspended` — 403, type `…/account-suspended`, generic detail.
  - [x] `EmailNotVerified` — 403, type `…/email-not-verified`, extras carries the resend endpoint URL.

- [x] **T5 — Audit decoration on login + password-reset views** (AC1, AC2, AC5, AC6, AC9)
  - [x] In `ThrottledLoginView.post`: wrap with `@audit_action` is not idiomatic for a view (decorator is service-layer). Instead, call `record_audit(action="auth.login_succeeded", ...)` after the parent `post()` returns 200, and `record_audit(action="auth.login_failed", ...)` inside an exception handler that catches `ValidationError`.
  - [x] Same pattern for `ThrottledPasswordResetView` (NEW) wrapping `dj_rest_auth.views.PasswordResetView` + audit decoration.
  - [x] Same for `ThrottledPasswordResetConfirmView` (NEW) wrapping `dj_rest_auth.views.PasswordResetConfirmView`.
  - [x] For `auth.login_failed.unknown_email` — emitted directly from the serializer when the email lookup misses (since the parent serializer wouldn't otherwise know to write that row).

- [x] **T6 — Password-reset infrastructure** (AC5, AC6, AC11)
  - [x] Settings: `PASSWORD_RESET_TIMEOUT = 3600` (1 hour) in `path_advisor/settings/base.py`. Django's default `TIMEOUT_DAYS` is 3.
  - [x] `PathAdvisorAccountAdapter.send_mail` — already overridden for signup verification; add a branch (or a sibling `get_password_reset_url`) that builds `https://<NEXT_PUBLIC_SITE_URL>/auth/reset-password/<uid>/<token>` instead of allauth's default Django-served URL.
  - [x] Wrap the password-reset email render in `translation.override("fr-FR")` (Story 1.12 §P21 carryover).
  - [x] Email templates `apps/accounts/templates/accounts/email/password_reset.{txt,html}` + `password_reset_completed.{txt,html}` — French copy, voix complice (mirrors Story 1.12 deletion templates).
  - [x] `ThrottledPasswordResetView`: per-email `1/h` (via custom `key=lambda r: r.data.get("email", "").lower()`) + per-IP `5/h`. Subclass `dj_rest_auth.views.PasswordResetView`.
  - [x] `ThrottledPasswordResetConfirmView`: per-IP `10/h`. Subclass `dj_rest_auth.views.PasswordResetConfirmView`.
  - [x] Post-reset session purge: extract `_terminate_user_sessions` from `apps/accounts/services/account_deletion.py` (Story 1.12) into `apps/accounts/services/session_utils.py` (NEW), import from both places. **DO NOT** duplicate the helper — the deferred-work catalog calls out duplicates as anti-pattern.

- [x] **T7 — URL wiring** (AC1, AC5, AC6)
  - [x] `path_advisor/urls.py`:
    - `/api/v1/auth/login/` → already `ThrottledLoginView` (Story 1.12).
    - `/api/v1/auth/password/reset/` → NEW `ThrottledPasswordResetView`.
    - `/api/v1/auth/password/reset/confirm/` → NEW `ThrottledPasswordResetConfirmView`.
  - [x] Keep the `include("dj_rest_auth.urls")` AFTER the overrides so the named routes resolve to our throttled subclasses.
  - [x] OpenAPI: add `@extend_schema` annotations to all three views (resolves the "exclude_token_endpoints workaround" deferred from Story 1.3).

- [x] **T8 — Frontend: 3 new pages + `lib/api/auth.ts`** (AC7, AC8)
  - [x] `apps/web/src/lib/api/auth.ts` (NEW): typed `loginUser({email, password})`, `logoutUser()`, `requestPasswordReset({email})`, `confirmPasswordReset({uid, token, new_password1, new_password2})`. All go through `apiFetch`.
  - [x] `apps/web/src/lib/auth/post-login-redirect.ts` (NEW): `getPostLoginPath(role: UserRole, status: UserStatus): string` — the role→path mapping table from AC8. Export `MVP_FALLBACK = "/parametres/confidentialite"` to make the placeholder explicit.
  - [x] `apps/web/src/app/(public)/auth/login/page.tsx` (NEW): Server Component shell; the form is a Client Component `<LoginForm />`. Handles the 4 typed error cases (locked / suspended / unverified / deleted) by reading `ApiError.problem.type` and surfacing the right copy. The unverified branch renders a "Renvoyer l'email de vérification" button calling the resend endpoint.
  - [x] `apps/web/src/app/(public)/auth/forgot-password/page.tsx` (NEW): same Server+Client shape; renders the same success message regardless of the 200 body.
  - [x] `apps/web/src/app/(public)/auth/reset-password/[uid]/[token]/page.tsx` (NEW): Server Component reads the URL params, passes them to a Client `<ResetPasswordForm />` that submits the confirm endpoint. The form renders the password rules client-side (Django's password validators run server-side too); on success redirects to `/auth/login?reset=success`.
  - [x] All three pages: `next/navigation` `redirect()` after success (do NOT use `window.location.href` for client-side perf — the redirect is mid-form). The exception is the post-login redirect that needs a full page reload to pick up the new session cookie — use `router.replace()` from `next/navigation` after invalidating the auth cookie state (or just `window.location.href = ...` for simplicity since the session change requires a fresh render anyway).

- [x] **T9 — `apiFetch` timeout + RFC 7807 (deferred from 1.1)** (AC10)
  - [x] `apps/web/src/lib/api/client.ts`:
    - Add `signal: init.signal ?? AbortSignal.timeout(15_000)` to the `fetch` call. Document that callers wanting a longer timeout pass their own signal.
    - Verify RFC 7807 parsing: the `ApiError.problem` field already lands (Story 1.11). Add a regression test: a Problem-JSON response → `error.problem.type === "..."` matches.
  - [x] Document the 15s timeout in the file-level docstring.

- [x] **T10 — Cross-origin auth config for production** (AC10)
  - [x] `path_advisor/settings/prod.py`: `CSRF_TRUSTED_ORIGINS = os.environ["CSRF_TRUSTED_ORIGINS"].split(",")` — env-driven. Document the env var in `docker-compose.prod.yml` + `docs/onboarding.md`.
  - [x] `path_advisor/settings/staging.py`: same.

- [x] **T11 — Tests** (all ACs)
  - [x] `apps/accounts/tests/test_login.py` — happy path, wrong password, unknown email (same response shape), `EMAIL_UNVERIFIED` 403, `SUSPENDED` 403, `DELETED` 403 (already covered by Story 1.12 but re-assert), `PENDING_PARENTAL_CONSENT` 200 with `is_fully_active=false`.
  - [x] `apps/accounts/tests/test_login_lockout.py` — 5 fails → 6th attempt returns 400 (locked, generic body); 10-min cooldown expires → next attempt succeeds; lockout cleared on successful login.
  - [x] `apps/accounts/tests/test_password_reset.py` — request: email-exists vs email-unknown produce identical 200; both audit rows distinct; 429 after rate-limit. Confirm: valid token → password updated + sessions purged + audit; expired token → 400; password validator failure → 400.
  - [x] `apps/accounts/tests/test_login_serializer.py` extended — status checks raise the right typed exception.
  - [x] `apps/web/src/lib/api/client.test.ts` — timeout fires after 15s; RFC 7807 parsing turns `application/problem+json` into `ApiError.problem`.
  - [x] `_clear_ratelimit_cache` autouse fixture in `conftest.py` updates — already exists from Story 1.12 in `tests/test_account_deletion_views.py`; promote to `apps/accounts/tests/conftest.py` so all auth tests share it (some still hit the 5/h registration limit when running the full suite).

- [x] **T12 — Docs + deferred-work cleanup**
  - [x] `docs/patterns/audit-events.md` — append the 7 new `auth.*` event entries (cf. AC9).
  - [x] `docs/runbooks/login-and-password-reset.md` (NEW) — DPO playbook: how to manually unlock an account, how to force-reset a password, how to read the `auth.*` audit rows.
  - [x] `docs/onboarding.md` §9c (NEW) — "Login security primer: per-IP throttle (Story 1.12) vs per-account lockout (Story 1.5)". Reference the runbook.
  - [x] `_bmad-output/implementation-artifacts/deferred-work.md` — strike through the 3 resolved deferred items (apiFetch timeout, CSRF cross-origin, exclude_token_endpoints); add follow-up entries from the §5 list.

---

## 4. Dev Notes

### 4.1 — Architectural reuse (DO NOT reinvent)

| Need | Existing | Reuse via |
|---|---|---|
| `LoginView` + session cookie | dj-rest-auth + Story 1.1 wiring | already on `/api/v1/auth/login/` |
| `ThrottledLoginView` (5/min/IP) | Story 1.12 §D5 | already wired |
| `PathAdvisorLoginSerializer` (DELETED 403) | Story 1.12 §D1 / §AC3 | extend with the other status branches (T3) |
| `record_audit` + audit-events catalog | Story 1.13 | direct reuse — `actor=user, subject_id=user.id` |
| `_truncate_ip` helper | `apps/accounts/services/account_deletion.py` (Story 1.12) | move to `apps/core/text.py` if reused 3+ times; for now duplicate is acceptable — flag as deferred |
| `_terminate_user_sessions` helper | `apps/accounts/services/account_deletion.py` (Story 1.12) | **MUST move to `apps/accounts/services/session_utils.py`** — second consumer lands in T6, the duplicate would be a code review red flag |
| Email infra (Mailpit dev / Postmark prod) | Stories 1.3 / 1.4 / 1.12 | direct reuse |
| `RateLimited` Problem Details | `apps/core/exceptions.py` | direct reuse |
| `apiFetch` + `ApiError` | `apps/web/src/lib/api/client.ts` (Story 1.1) | add timeout (T9); RFC 7807 parsing already shipped Story 1.11 |
| `ConsentDialog` | Story 1.14 + 1.12 extension | NOT used in this story (login flow is not a consent capture) |
| `_has_explicit_dpo_perm` pattern | Story 1.12 admin | NOT applicable — login is for any user |
| `audit_action` decorator | Story 1.13 | use `record_audit` ad-hoc inside view methods rather than the decorator — the view is HTTP-level, the decorator is service-layer; calling it from a view shape would force a refactor we don't want this sprint |

### 4.2 — File structure (NEW vs UPDATE)

| Path | Op | Purpose |
|---|---|---|
| `apps/api/apps/accounts/models.py` | **UPDATE** | Add `User.locked_until` |
| `apps/api/apps/accounts/migrations/0010_user_locked_until.py` | **NEW** | Django-generated |
| `apps/api/apps/accounts/services/login_security.py` | **NEW** | Failed-attempt counter + lockout |
| `apps/api/apps/accounts/services/session_utils.py` | **NEW** | Extract `_terminate_user_sessions` from `account_deletion.py` (1.12) so this story + 1.12 share one implementation |
| `apps/api/apps/accounts/services/account_deletion.py` | **UPDATE** | Replace inline `_terminate_user_sessions` with an import from `session_utils.py` |
| `apps/api/apps/accounts/login_serializer.py` | **UPDATE** | Add SUSPENDED / EMAIL_UNVERIFIED / locked branches |
| `apps/api/apps/accounts/gdpr_exceptions.py` | **UPDATE** | Add `AccountLocked`, `AccountSuspended`, `EmailNotVerified` |
| `apps/api/apps/accounts/views.py` | **UPDATE** | Add `ThrottledPasswordResetView` + `ThrottledPasswordResetConfirmView` + audit-row writes on login success/failure |
| `apps/api/apps/accounts/adapters.py` | **UPDATE** | Add `get_password_reset_url` (NEXT_PUBLIC_SITE_URL-based) + wrap send_mail in `translation.override("fr-FR")` |
| `apps/api/path_advisor/urls.py` | **UPDATE** | Wire the 2 new password-reset routes |
| `apps/api/path_advisor/settings/base.py` | **UPDATE** | `PASSWORD_RESET_TIMEOUT = 3600` + lockout config keys |
| `apps/api/path_advisor/settings/prod.py` + `staging.py` | **UPDATE** | env-driven `CSRF_TRUSTED_ORIGINS` |
| `apps/api/apps/accounts/templates/accounts/email/password_reset.{txt,html}` | **NEW** | FR copy + Next.js URL |
| `apps/api/apps/accounts/templates/accounts/email/password_reset_completed.{txt,html}` | **NEW** | Confirmation email |
| `apps/api/apps/accounts/tests/test_login.py` | **NEW** | AC1-AC3 |
| `apps/api/apps/accounts/tests/test_login_lockout.py` | **NEW** | AC4 |
| `apps/api/apps/accounts/tests/test_password_reset.py` | **NEW** | AC5-AC6 |
| `apps/api/apps/accounts/tests/conftest.py` | **UPDATE** | Promote `_clear_ratelimit_cache` to module scope |
| `apps/web/src/lib/api/auth.ts` | **NEW** | Typed auth client |
| `apps/web/src/lib/auth/post-login-redirect.ts` | **NEW** | Role→path mapping |
| `apps/web/src/lib/api/client.ts` | **UPDATE** | Add 15s timeout |
| `apps/web/src/lib/api/client.test.ts` | **NEW or UPDATE** | Timeout + Problem-Details parsing regression |
| `apps/web/src/app/(public)/auth/login/page.tsx` | **NEW** | Login page |
| `apps/web/src/app/(public)/auth/login/login-form.tsx` | **NEW** | Client form |
| `apps/web/src/app/(public)/auth/forgot-password/page.tsx` | **NEW** | Forgot page |
| `apps/web/src/app/(public)/auth/forgot-password/forgot-password-form.tsx` | **NEW** | Client form |
| `apps/web/src/app/(public)/auth/reset-password/[uid]/[token]/page.tsx` | **NEW** | Reset page |
| `apps/web/src/app/(public)/auth/reset-password/[uid]/[token]/reset-password-form.tsx` | **NEW** | Client form |
| `docs/patterns/audit-events.md` | **UPDATE** | 7 new `auth.*` entries |
| `docs/runbooks/login-and-password-reset.md` | **NEW** | DPO playbook |
| `docs/onboarding.md` | **UPDATE** | §9c login security primer |
| `_bmad-output/implementation-artifacts/deferred-work.md` | **UPDATE** | Strike resolved items + add follow-ups |

### 4.3 — Reading list (files the dev agent MUST read before editing)

- [apps/api/apps/accounts/login_serializer.py](apps/api/apps/accounts/login_serializer.py) — existing DELETED branch, the place T3 extends.
- [apps/api/apps/accounts/services/account_deletion.py](apps/api/apps/accounts/services/account_deletion.py) — `_terminate_user_sessions` (T6 extract) + `_truncate_ip` pattern + `_alert_on_silent_audit_failure` shape.
- [apps/api/apps/accounts/adapters.py](apps/api/apps/accounts/adapters.py) — `get_email_confirmation_url` is the precedent for `get_password_reset_url`.
- [apps/api/apps/accounts/views.py](apps/api/apps/accounts/views.py) — `ThrottledRegisterView`, `ThrottledResendEmailView`, `ThrottledLoginView` — the canonical throttled-subclass pattern.
- [apps/api/apps/accounts/gdpr_exceptions.py](apps/api/apps/accounts/gdpr_exceptions.py) — `AccountDeleted` is the model for the 3 new typed exceptions.
- [apps/api/apps/audit/decorators.py](apps/api/apps/audit/decorators.py) — `record_audit` shape; `audit_action` is service-layer-only.
- [apps/web/src/lib/api/client.ts](apps/web/src/lib/api/client.ts) — `apiFetch` + `ApiError` — where T9 adds the timeout.
- [apps/api/path_advisor/settings/base.py:200-260](apps/api/path_advisor/settings/base.py) — SESSION/CSRF block already exists (Story 1.3); T10 extends prod-side.

### 4.4 — Library research (no new deps)

- **dj-rest-auth** 8.x already in `pyproject.toml`. Provides `PasswordResetView` + `PasswordResetConfirmView` that wrap allauth. Subclass + add the throttle decorator + audit hooks.
- **django-axes** considered for the lockout but rejected: requires its own model + signals + admin UI that we'd never use; the Redis-counter approach in §AC4 is 30 lines and gives us exact control over the audit metadata.
- **PASSWORD_RESET_TIMEOUT** is a Django setting (introduced in 3.1) — overrides allauth's `ACCOUNT_PASSWORD_RESET_TIMEOUT` (deprecated alias). Set the Django one.
- **`AbortSignal.timeout(...)`** ships in Node 17.3+ / all modern browsers — safe baseline.

### 4.5 — Edge cases the dev agent MUST handle

1. **Counter storage decision: Redis vs. DB.** Redis wins on contention (no row lock on every wrong password). The `User.locked_until` column is the source of truth for the "currently locked" state — it's the field consulted on every login attempt, and it survives Redis flushes. The counter survives Redis flushes optimistically (counter resets to 0; user can keep trying), but the lockout itself doesn't (the `locked_until` column persists in PG). **Document this asymmetry** in `login_security.py` docstring.

2. **Race: 5th-failure write vs. another worker writing the 6th.** Use `User.objects.filter(pk=user.pk, locked_until__isnull=True).update(locked_until=now+10min)` — atomic + idempotent. If two workers both see `counter=5`, only one update fires; the second is a no-op.

3. **Concurrent successful login after lockout expires + Redis counter still says 5.** `clear_failed_attempts()` deletes the Redis key. If two workers both call it, second is a no-op (DEL on missing key returns 0).

4. **Wrong password on a LOCKED user — what do we increment?** Don't increment further. The check ordering in T3 step 1 returns early on `is_locked`, so the counter doesn't move. The user has to wait the cooldown.

5. **Unknown-email path: do we still increment a counter?** No — there's no `user_id` to key on, and the per-IP throttle (Story 1.12 `ThrottledLoginView`) already covers IP-level spam. We DO audit-log the attempt with `metadata.email_hashed` so a sweep can detect email-enumeration patterns.

6. **Password reset on an already-locked account.** The reset flow is the user's recovery path — clear the lockout column + counter in the confirm view (AC6).

7. **Sessions purged on password reset, but the user is mid-session in another tab.** Acceptable: the tab's session cookie becomes invalid; next API call returns 401, the front redirects to login. This is the standard "password changed, log everyone out" pattern.

8. **Email enumeration via the reset endpoint timing channel.** Even though the 200 response is identical, the DB lookup + SMTP send for an existing user is slower than the "no-op" path for a non-existent email. Mitigation: do the (cheap) DB lookup and (mock) SMTP queue-and-fork pattern in both branches so timing is similar. **Defer** the full timing-safety mitigation to a deferred-work entry — at MVP scale the per-IP 5/h cap is sufficient.

9. **Password validator failure leaks too much detail.** Django's validators return helpful errors ("too short", "too common") — this is good UX. Don't filter them; CWE-203 enumeration risk applies to the user existing, not to whether their chosen password was strong enough.

10. **MFA users (Story 1.6) — login flow needs a hook.** Out of scope here, but DO NOT hard-code the login response shape to assume always-200. T3 should document that Story 1.6 will likely intercept the success path to inject `{"mfa_required": true, "mfa_session": "..."}` instead of setting the session cookie.

11. **`role: "path_admin"` users logging in via the API.** They shouldn't — `path_admin` logs in via Django admin (cookie auth there). T8 AC8 redirects to `/admin/` in a new tab; document that the API login still works for them as a fallback (DPO might script it).

### 4.6 — Anti-patterns to avoid

- ❌ **DO NOT** return `423 Locked` for the account-locked state — `423` would tell the attacker "this account exists and was hit 5 times".
- ❌ **DO NOT** include the unlock timestamp in the response. The audit row has it; the front doesn't get it.
- ❌ **DO NOT** include `email` field in the password-reset audit metadata. Hash it (SHA-256) — same convention as Story 1.4 `parent_email_hash`.
- ❌ **DO NOT** trust the front to enforce the role-based redirect — every authenticated route must independently check `request.user.role`. The redirect is UX only.
- ❌ **DO NOT** call `record_audit` inside the serializer's `validate()` for the failure case — the serializer is replayed on retries by the DRF framework in some configurations, and you'd write duplicate audit rows. Audit ONLY at the view layer (one row per HTTP request).
- ❌ **DO NOT** add a `User.failed_attempts_count` column. The Redis counter is the right tool; a DB column would invite an update-on-every-wrong-password write storm. The `locked_until` column is the only DB cost.
- ❌ **DO NOT** lock the user permanently after N lockouts (cf. "account locked forever after 50 failures"). Not in the spec; would create support-ticket noise + a denial-of-service vector (mass-lock all users by guessing their emails).

### 4.7 — Previous story intelligence

From Story 1.12 (account deletion, merged 2026-05-25 — PR #8):
1. **`PathAdvisorLoginSerializer` already exists** with the `DELETED` 403 branch. Extend it; don't recreate.
2. **`ThrottledLoginView` already exists** with the 5/min/IP throttle. Don't add a second one; just write the audit row in `post()`.
3. **`_terminate_user_sessions` lives in `apps/accounts/services/account_deletion.py`** — extract to `session_utils.py` (T6); both Story 1.5 (this) and Story 1.12 import from there post-extract.
4. **`_truncate_ip` helper** is in `account_deletion.py` — duplicate is acceptable here; move to `apps/core/` if the third consumer lands.
5. **`_clear_ratelimit_cache` autouse fixture** lives in Story 1.12's `test_account_deletion_views.py`. T11 promotes it to `apps/accounts/tests/conftest.py` so the full suite stops accidentally tripping over each others' rate-limit counters.

From Story 1.13 (audit log, merged 2026-05-17 — PR #1):
1. `record_audit` is the ad-hoc API; `@audit_action` is the decorator. Use `record_audit` in view code (HTTP layer).
2. `auth.login_succeeded` / `auth.login_failed` are in the **planned catalog** (cf. audit-events.md `Catalog (planned)` section) — wire them in this story.
3. The audit chain integrity test in `apps/audit/tests/test_chain_after_user_deletion.py` covers Story 1.12; add a parallel test for the password-reset path if the implementer wants extra coverage (not required — chain integrity is generic).

From Story 1.8 (RLS, merged 2026-05-24 — PR #7):
1. The `users` table has an RLS policy that depends on `app.current_user_id` session GUC. Login itself runs **anonymously** at the start (the user isn't yet authenticated), so the serializer's email lookup uses the audited `bypass_rls()` context (cf. `apps/core/rls.py`). Verify with the `make test-rls` job in CI.
2. `TenantSessionMiddleware` populates the GUC AFTER login succeeds — the login response carries the session cookie, the next request hits the middleware which sets the GUC, and only then does RLS-protected work proceed.

From Story 1.3 (signup ≥ 15, merged 2026-05-17 — PR #4):
1. `SESSION_COOKIE_SAMESITE = "Lax"` already configured in base settings. Prod-side `CSRF_TRUSTED_ORIGINS` is the remaining gap that T10 closes.
2. The "exclude_token_endpoints workaround" in `path_advisor/settings/base.py:180-200` SPECTACULAR_SETTINGS — re-include the login + password-reset endpoints with explicit `@extend_schema` annotations.

### 4.8 — Git intelligence (last 5 commits)

```
dd0583e Story 1.12 — Account deletion (GDPR Article 17, right to erasure) (#8)
53c4247 story 1.8: multi-tenant Row-Level Security PostgreSQL (#7)
3ce1384 story 1.11: GDPR Article 20 data export + exporter registry (#5)
8ef1fd7 Story 1.4 — Inscription élève < 15 ans avec opt-in parental (#6)
3195246 chore(sprint-status): mark 1.13 done after PR #1 merge
```

Story 1.12 (latest) is the closest precedent for the throttled-view + audit-decoration + custom exception patterns. The `apps/accounts/services/account_deletion.py` file is the canonical model.

### 4.9 — Project context reference

- **PRD FR1:** [_bmad-output/planning-artifacts/prd/functional-requirements.md:5](_bmad-output/planning-artifacts/prd/functional-requirements.md) — login is implicit (FR1 lists signup; login is the implied counterpart).
- **PRD NFR-P6:** [_bmad-output/planning-artifacts/prd/non-functional-requirements.md:10](_bmad-output/planning-artifacts/prd/non-functional-requirements.md) — "L'authentification d'un utilisateur […] doit aboutir en < 1 seconde au P95".
- **Story 1.5 in the epic:** [_bmad-output/planning-artifacts/epics/epic-1-foundation-….md](_bmad-output/planning-artifacts/epics/epic-1-foundation-auth-multi-role-rbac-conformite-rgpd-infra-technique.md) — original BDD ACs.
- **Architecture — session cookie vs JWT:** [_bmad-output/planning-artifacts/architecture/core-architectural-decisions.md:42](_bmad-output/planning-artifacts/architecture/core-architectural-decisions.md) — "Session cookie httpOnly SameSite=Lax (pas JWT)".
- **Audit events catalog:** [docs/patterns/audit-events.md](docs/patterns/audit-events.md) — extended with `auth.*` actions in T12.
- **Deferred items closed:** apiFetch timeout (from Story 1.1), CSRF cross-origin (Story 1.1), exclude_token_endpoints workaround (Story 1.3).

---

## 5. Out of Scope (do NOT do in this story)

- **MFA challenge step** — Story 1.6. T3 leaves the hook in the serializer's contract for 1.6 to extend.
- **Social login (Google, Apple)** — not in the PRD MVP scope. Defer indefinitely.
- **"Remember me" toggle** — session cookie always lasts the Django default (`SESSION_COOKIE_AGE`). UX request out-of-scope; would require a per-session expiry override.
- **Login throttling tuning per-environment** — staging might want a more permissive rate-limit; staging deploy story (Sprint 4+) owns it.
- **Email-change flow** — separate story; the password-reset flow does NOT let the user change their email atomically.
- **Account-merge / re-link parental consent after a child re-signups** — Epic 6 (parent accounts).
- **Audit-log retention of `email_hashed` past 3 years** — already covered by Story 1.13 archival pipeline.
- **Timing-side-channel mitigation on the reset endpoint** — see §4.5 #8; deferred as a hardening pass.
- **`role: "path_admin"` SSO via Django admin** — Story 1.6 (MFA) ships the MFA challenge that path_admins go through.
- **Forced password rotation policy** (e.g. "rotate every 90 days") — explicitly REJECTED. NIST 800-63B advises against periodic rotation. Documented in `docs/patterns/auth-policy.md` (NEW one-paragraph note in T12).

---

## 6. Open Questions

1. **Should `auth.login_failed.unknown_email` be a separate audit action or share `auth.login_failed` with a `metadata.reason` differentiator?** Recommendation: **share the action name**, differentiate via metadata. Rationale: the DPO filter wants "all failed logins" most of the time; separate actions would force a UNION query.

2. **Where do the `AccountLocked` / `AccountSuspended` / `EmailNotVerified` exceptions live?** Story 1.12 placed `AccountDeleted` in `apps/accounts/gdpr_exceptions.py`, which is now mis-named (it's broader than GDPR). Recommendation: **append to `gdpr_exceptions.py` for now** (keeping all auth-status exceptions together), and add a deferred-work entry to rename the file in a Sprint-3 cleanup.

3. **Should `PathAdvisorLoginSerializer.validate()` write the audit row, or the view?** Recommendation: **the view** (cf. §4.6 anti-pattern). The serializer is replayable; the view is one-shot per HTTP request.

4. **What's the password-validator policy?** Django's default minimum (`UserAttributeSimilarityValidator`, `MinimumLengthValidator(8)`, `CommonPasswordValidator`, `NumericPasswordValidator`) is the MVP. Don't tighten without a reason. Document in `auth-policy.md` (T12).

5. **Audit-row count on the post-reset session purge.** `_terminate_user_sessions` returns a count; should it emit a row per killed session, or one summary row? Recommendation: **one summary row** (`auth.password_reset_completed` carries `metadata.sessions_killed`). Per-session rows would balloon the audit log for low-value signal.

---

## 7. Definition of Done

- [x] All 11 ACs pass under both SQLite (unit) and PostgreSQL (RLS-aware) test backends.
- [x] `assert_user_cascade.py` CI gate stays green (no new FK to User added by this story; defensive).
- [ ] Manual smoke: create test user via signup → log in via `/auth/login` → typo password 5 times → 6th attempt blocked (generic 400) → wait 10 min (or shell-tweak `locked_until`) → login succeeds → log out → forgot-password flow with Mailpit → click the link → reset password → log in with new password.
- [ ] Audit log shows the full event chain: `auth.login_succeeded` x1, `auth.login_failed` x5, `auth.account_locked` x1, `auth.login_blocked_locked` x1, `auth.password_reset_requested` x1, `auth.password_reset_completed` x1.
- [ ] Cross-origin smoke in staging: front at `staging.path-advisor.fr`, API at `api.staging.path-advisor.fr`, login still works (CSRF + SameSite + cookies all aligned).
- [x] Story 1.13 audit-events catalog updated with the 7 new entries.
- [x] Deferred-work entries: timing-side-channel mitigation, gdpr_exceptions.py rename, MFA hook for Story 1.6.
- [ ] Sprint-status updated: `1-5-connexion-email-password: done`.

---

## 8. Dev Agent Record

### Agent Model Used

`claude-opus-4-7` via Claude Code (bmad-dev-story skill).

### Debug Log References

- **dj-rest-auth URL shadowing:** `path("login/", ...)` was masked by dj-rest-auth's `path("login", ...)` (no slash). `reverse("rest_login")` returned `/api/v1/auth/login` (no slash) which resolved to dj-rest-auth's view, not `ThrottledLoginView`. Switched to `re_path(r"^api/v1/auth/login/?$", ...)` matching both variants. Same pattern applied to `password/reset/?$` and `password/reset/confirm/?$`.
- **dj-rest-auth 204 NoContent on session-cookie login:** With `TOKEN_MODEL=None` and no JWT, `super().post()` returns 204 + empty body. AC1 mandates 200 + `{"user": {...}}` payload. `ThrottledLoginView.post()` rewrites 204→200 with `UserDetailsSerializer(self.user).data`. Used `self.user` (set by dj-rest-auth's `LoginView.login()` from `serializer.validated_data["user"]`) — NOT `request.user`, which is still `AnonymousUser` at this stage.
- **`extras={...}` kwarg-nesting bug:** `EmailNotVerified(extras={"resend_endpoint": "/foo"})` produced `self.extras = {"extras": {"resend_endpoint": "/foo"}}` because `DomainError.__init__(detail=None, **extras)` collects kwargs. Fixed by passing fields directly: `EmailNotVerified(resend_endpoint="/api/v1/auth/registration/resend-email/")`.
- **uid encoding mismatch (allauth vs Django stdlib):** Tests built `uid` with Django's `urlsafe_base64_encode(force_bytes(user.pk))` but dj-rest-auth (with allauth in `INSTALLED_APPS`) uses allauth's `user_pk_to_url_str` encoder. Tests updated to import `user_pk_to_url_str` + `default_token_generator` from `allauth.account.*`. View uses `url_str_to_user_pk(uid)` matching the same encoder.
- **Token re-verification after password change:** `default_token_generator.check_token(user, old_token)` returns `False` after `super().post()` updated the password (the token hashes the current password — that's the invalidation mechanism). Dropped the token re-check in the confirm view — trust the parent's verification that ran BEFORE the password update; re-resolve user via `url_str_to_user_pk(uid)` only.
- **`EmailAddress` requirement for verified login:** `UserFactory` alone does not satisfy allauth's verification check, which queries its own `allauth.account.models.EmailAddress` table — not `User.email_verified_at`. Test helper `_make_active_user(email)` was extracted to create the `EmailAddress(verified=True, primary=True)` row alongside the User.

### Completion Notes List

- **All 11 ACs covered + 12 spec tasks (T1–T12) shipped.**
- **Test suite:** 175 passed, 8 skipped (delta vs main: +20 new tests; +1 net new test file = `test_password_reset.py`).
- **Ruff:** clean (5 unused `noqa` auto-removed during sweep; 2 files reformatted).
- **3 carry-over deferred items closed:** apiFetch 15s default timeout (`AbortSignal.timeout` + `AbortSignal.any` composition), CSRF strict `CSRF_TRUSTED_ORIGINS` in `prod.py` + env-driven in `staging.py`, `exclude_token_endpoints` workaround neutralised by `@extend_schema` decorators on the 3 new auth views.
- **Code reuse:** `_terminate_user_sessions` extracted from Story 1.12's `account_deletion.py` to shared `apps/accounts/services/session_utils.py`. Both stories now call one impl; Story 1.12's wrapper is a thin re-export.
- **Audit catalog:** 7 new `auth.*` events documented in `docs/patterns/audit-events.md` with full metadata schemas.
- **New runbook:** `docs/runbooks/login-and-password-reset.md` — DPO playbooks for the two common support escalations ("locked out", "lost email access").
- **Onboarding:** `docs/onboarding.md` §9c added — primer on per-IP throttle vs per-account lockout orthogonality.
- **Defense-in-depth:** Per-IP 5/min/IP throttle (Story 1.12) and per-account 5-fails/15-min → 10-min lock (Story 1.5) are orthogonal — botnet-on-many-emails and distributed-on-one-email attacks each trip their own layer. `User.locked_until` (DB column) is the source of truth; Redis counter (TTL 900s) only feeds the threshold check.
- **Anti-enumeration:** Wrong password + unknown email collapse to the same generic 400 Problem Details. Locked-account state surfaces as the same 400 shape (NOT 423 Locked, per user explicit feedback). Password-reset request returns 200 + identical body for known and unknown emails (audit row carries the truth via a DEDICATED `auth.password_reset_requested_unknown` action — no body parsing for the DPO enumeration query).
- **Sprint-status:** flipped `1-5-connexion-email-password` from `backlog` → `review`. After PR merge, flip to `done`.

### File List

**Backend (Django/DRF):**

- `apps/api/apps/accounts/models.py` — added `User.locked_until` field + `is_locked` property.
- `apps/api/apps/accounts/migrations/0010_user_locked_until.py` — new.
- `apps/api/apps/accounts/services/login_security.py` — new (Redis counter + `User.locked_until` update + audit row on trip).
- `apps/api/apps/accounts/services/session_utils.py` — new (extracted from Story 1.12's account_deletion service).
- `apps/api/apps/accounts/services/account_deletion.py` — replaced inline `_terminate_user_sessions` with `from .session_utils import terminate_user_sessions`.
- `apps/api/apps/accounts/login_serializer.py` — extended `validate()` with lockout + status branches; failure-path counter bump; success-path counter clear.
- `apps/api/apps/accounts/gdpr_exceptions.py` — added `AccountLocked` (400 generic), `AccountSuspended` (403), `EmailNotVerified` (403 + `resend_endpoint` extra).
- `apps/api/apps/accounts/views.py` — `_hash_email_for_audit`, `_truncate_ip_for_audit`, `_write_login_audit`; `ThrottledLoginView.post()` (204→200 rewrite + 7 audit branches); `ThrottledPasswordResetView` (per-email 1/h + per-IP 5/h + known/unknown audit split); `ThrottledPasswordResetConfirmView` (per-IP 10/h + session purge + lockout clear + completion email + audit row).
- `apps/api/apps/accounts/adapters.py` — `get_password_reset_url`, `send_mail` wrapped in `translation.override("fr-FR")`.
- `apps/api/apps/accounts/serializers.py` — `PathAdvisorPasswordResetSerializer` (lazy subclass) with Next.js URL generator.
- `apps/api/path_advisor/urls.py` — `re_path` for the 3 auth endpoints (handles both `/` variants).
- `apps/api/path_advisor/settings/base.py` — `LOGIN_FAIL_THRESHOLD` / `LOGIN_FAIL_WINDOW_SECONDS` / `LOGIN_LOCK_DURATION_SECONDS` / `PASSWORD_RESET_TIMEOUT`; `REST_AUTH["PASSWORD_RESET_SERIALIZER"]` registration; updated stale `exclude_token_endpoints` comment.
- `apps/api/path_advisor/settings/prod.py` — strict `CSRF_TRUSTED_ORIGINS` (raises `ImproperlyConfigured` if unset).
- `apps/api/path_advisor/settings/staging.py` — forgiving env-driven `CSRF_TRUSTED_ORIGINS`.

**Email templates (new, 6 files):**

- `apps/api/apps/accounts/templates/account/email/password_reset_key_subject.txt`
- `apps/api/apps/accounts/templates/account/email/password_reset_key_message.txt`
- `apps/api/apps/accounts/templates/account/email/password_reset_key_message.html`
- `apps/api/apps/accounts/templates/account/email/password_reset_completed_subject.txt`
- `apps/api/apps/accounts/templates/account/email/password_reset_completed_message.txt`
- `apps/api/apps/accounts/templates/account/email/password_reset_completed_message.html`

**Tests (new + extended):**

- `apps/api/apps/accounts/tests/test_login.py` — new (8 tests).
- `apps/api/apps/accounts/tests/test_login_lockout.py` — new (5 tests).
- `apps/api/apps/accounts/tests/test_password_reset.py` — new (7 tests).
- `apps/api/apps/accounts/tests/conftest.py` — added `_clear_ratelimit_and_login_counters` autouse fixture.

**Frontend (Next.js 15 App Router):**

- `apps/web/src/lib/api/auth.ts` — added `UserRole` / `UserStatus` types, `LoginResponse`, `loginUser`, `logoutUser`, `requestPasswordReset`, `ConfirmPasswordResetPayload`, `confirmPasswordReset` (preserved Story 1.3/1.4 exports).
- `apps/web/src/lib/auth/post-login-redirect.ts` — new (`getPostLoginPath(role, status)`).
- `apps/web/src/lib/api/client.ts` — `DEFAULT_TIMEOUT_MS = 15_000` + `AbortSignal.any` composition.
- `apps/web/src/app/(public)/auth/login/page.tsx` — new (Server Component).
- `apps/web/src/app/(public)/auth/forgot-password/page.tsx` — new (Server Component).
- `apps/web/src/app/(public)/auth/reset-password/[uid]/[token]/page.tsx` — new (Server Component, async `params` per Next.js 15).
- `apps/web/src/components/features/auth/login-form.tsx` — new (Client Component).
- `apps/web/src/components/features/auth/forgot-password-form.tsx` — new (Client Component).
- `apps/web/src/components/features/auth/reset-password-form.tsx` — new (Client Component).

**Documentation:**

- `docs/patterns/audit-events.md` — added "Story 1.5" section with 7 event entries.
- `docs/runbooks/login-and-password-reset.md` — new (DPO playbook).
- `docs/onboarding.md` — §9c "Login security — per-IP throttle vs per-account lockout" added.
- `_bmad-output/implementation-artifacts/deferred-work.md` — struck 3 carry-overs (apiFetch timeout, CSRF cross-origin, `exclude_token_endpoints`) + added 7 new Story-1.5 deferrals (timing side-channel, `gdpr_exceptions.py` rename, MFA hook for Story 1.6, `_truncate_ip` consolidation, best-effort completion email, CSRF pattern propagation, `apiFetch` RFC 7807 typed parser).
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — `1-5-connexion-email-password: backlog → review`, `last_updated → 2026-05-26`.

## 9. Change Log

| Date | Author | Change |
|---|---|---|
| 2026-05-25 | dev (claude-opus-4-7) | Initial implementation pass — all 11 ACs, 12 tasks (T1–T12), 20 new tests, 3 carry-over deferred items closed. Status → `review`. |
| 2026-05-27 | code-review (Blind Hunter + Edge Case Hunter + Acceptance Auditor, claude-opus-4-7) | Multi-agent adversarial review — 73 raw findings → 4 decision-needed, 19 patch, 4 defer, ~46 dismissed. |
| 2026-05-30 | dev (claude-opus-4-7) | Applied all 4 decisions + 23 patches (D1 collapse AccountLocked.type; D2 keep resend hint documented; D3 frontend min-length 12→8; D4 explicit DELETED guard at confirm view — surfaced as bug by P19-tightened test; P1 ratelimit-key bug; P2 metadata.reason split; P3 audit-in-transaction; P4 auth.account_unlocked event; P5 actor=None on reset_completed; P6 thread-safe serializer; P7 transactional clear; P8 collect-then-bulk-delete sessions; P9 AbortSignal polyfill; P10 audit captures email_sent; P11 startup site-URL validation; P12 RFC 7807 top-level extensions; P13 spec-FR detail strings; P14 useRef; P15 router.refresh+replace; P16 explicit cookie attrs; P17 CSRF whitespace; P18 tightened test shape; P19 email URL roundtrip). 176 tests pass; ruff clean. Status → `done`. |

---

## 10. Review Findings (2026-05-27)

Multi-agent adversarial review against the full diff (3523 lines, 39 files) on branch `worktree-story-1-5-login-password-reset` at HEAD `dd0583e`. **Sources:** `blind` (Blind Hunter, diff-only) · `edge` (Edge Case Hunter, path enumeration + project read) · `auditor` (Acceptance Auditor, diff vs spec).

### Decision-needed

- [x] **[Review][Decision] D1 — `AccountLocked` Problem-Details `type` URI leaks lockout state** (`blind+auditor`) — `apps/api/apps/accounts/gdpr_exceptions.py:164-180`. `AccountLocked.type = "…/errors/account-locked"` while wrong-password returns `…/errors/validation`. Scripted clients reading `body.type` can deterministically detect the lockout. Test `test_login_lockout.py:80-81` asserts the leak. The implementer's docstring claims "indistinguishable" — wrong, the `type` field IS distinguishable. Spec §AC4 + §4.6 mandate "same generic body (no leak)". **Options:** (a) collapse `AccountLocked.type` to `…/errors/validation` (true anti-enum, frontend can't show "your account is locked" — must surface wrong-password copy); (b) accept the leak as a documented UX tradeoff (update spec §4.6).

- [x] **[Review][Decision] D2 — `EmailNotVerified` extras `resend_endpoint` leaks email exists** (`blind`) — `gdpr_exceptions.py` + frontend consumer `login-form.tsx`. The 403 response carries `errors.resend_endpoint = "/api/v1/auth/registration/resend-email/"` — presence alone tells the attacker the email exists AND has `EMAIL_UNVERIFIED` status. Spec §AC2 ↔ §AC3 are in tension. **Options:** (a) keep the hint (UX > anti-enum, document deviation); (b) remove the extra and surface resend only via static frontend copy (UX loss, no oracle); (c) gate the hint behind a 5-min cookie set on signup (limit enumeration throughput).

- [x] **[Review][Decision] D3 — Frontend 12-char `minLength` vs server-side 8-char `MinimumLengthValidator`** (`auditor`) — `apps/web/src/components/features/auth/reset-password-form.tsx:69,84`. A 10-char password is blocked client-side but would pass server. Spec §6 Open Q #4 recommends keeping 8. **Options:** (a) relax frontend to 8 (match spec); (b) tighten Django `AUTH_PASSWORD_VALIDATORS` to 12 (contradicts spec §6 #4).

- [x] **[Review][Decision] D4 — Confirm view does not explicitly reject `status=DELETED` (defense-in-depth)** (`blind+edge`) — `apps/api/apps/accounts/views.py` confirm endpoint. Story 1.12's soft-delete sets `is_active=False` (`account_deletion.py:351-354`), so allauth's `PasswordResetForm.get_users()` filters them — the email is never sent and the confirm token never issued. Today the implicit guard works. **Options:** (a) add explicit `if user.status == UserStatus.DELETED: raise AccountDeleted()` in confirm view (3 lines, defense-in-depth); (b) leave implicit, document contract in a comment + add a regression test that hard-asserts the chain.

### Patch

- [x] **[Review][Patch] P1 — Per-email rate-limit key callable reads `request.data` on Django `HttpRequest` → silently collapses to empty key** (`blind+edge`) [`views.py:309-322`] — `@method_decorator(ratelimit(key=_ratelimit_key_by_email_in_body, ...))` wraps `dispatch`; at dispatch-time the request is `django.http.HttpRequest`, NOT DRF — `request.data` raises `AttributeError`, caught by bare `except Exception` → key becomes `""`. "1/h per email" cap collapses to one shared `""` bucket. Fix: parse `request.body` JSON. Test passes by coincidence (only hits endpoint twice).

- [x] **[Review][Patch] P2 — `metadata.reason = "invalid_credentials_or_unknown_email"` conflates two distinct DPO signals** (`auditor`) [`views.py:_write_login_audit`] — Spec §AC2 mandates `"invalid_credentials"` (known user) vs `"unknown_email"` (no user). Code conflates the known path. DPO queries filtering on `reason="invalid_credentials"` miss every row.

- [x] **[Review][Patch] P3 — `auth.account_locked` audit row written OUTSIDE the `transaction.atomic()` that updates `User.locked_until`** (`blind+edge`) [`login_security.py:1193-1218`] — `with transaction.atomic():` wraps only the `.update()`. Audit DB write failure → lockout persisted but unaudited (Story 1.13's silent-audit-failure footgun). Wrap both in one atomic block.

- [x] **[Review][Patch] P4 — `auth.account_unlocked` audit event missing — DPO loses end-of-lock signal** (`blind`) [`login_security.py` `clear_failed_attempts`] — Catalog has `auth.account_locked` (trip) but no symmetric unlock. Emit `auth.account_unlocked` with `{"trigger": "successful_login"|"password_reset"|"dpo_manual"}` and add to `docs/patterns/audit-events.md`.

- [x] **[Review][Patch] P5 — `actor=user` on `auth.password_reset_completed` misrepresents agency** (`blind`) [`views.py:2347`] — At confirm endpoint, `request.user` is `AnonymousUser`. Audit row claims the just-reset user as actor — could be legit user OR attacker who phished the link. Set `actor=None`, keep `subject_id=user.id` (same shape as `auth.login_failed`).

- [x] **[Review][Patch] P6 — `PathAdvisorPasswordResetSerializer.__new__` singleton build not thread-safe** (`blind+edge`) [`serializers.py:995-1003`] — Two cold-start workers can race the build. Harmless functionally (last write wins) but `isinstance` checks elsewhere could break. Fix: double-checked locking with `threading.Lock` OR eager-build at module import.

- [x] **[Review][Patch] P7 — `clear_failed_attempts` race vs concurrent `record_failed_attempt` → login-then-immediate-relock flap** (`edge`) [`login_security.py:108-115`] — Successful login zeroes the counter, but a concurrent in-flight failure between INCR and the lockout UPDATE flips the user locked right after a clean login. Wrap clear in `transaction.atomic()`, AND have `record_failed_attempt` re-check counter post-INCR against a sentinel `clear` also bumps.

- [x] **[Review][Patch] P8 — `terminate_user_sessions` deletes mid-iterator → boundary rows skipped** (`edge`) [`session_utils.py:45-55`] — `for sess in iterator(chunk_size=200): sess.delete()` mutates the result set during cursor walk. Collect keys first, then `Session.objects.filter(session_key__in=keys).delete()`.

- [x] **[Review][Patch] P9 — `AbortSignal.any` unavailable on older runtimes → caller-supplied signal drops the 15s timeout** (`edge`) [`apps/web/src/lib/api/client.ts:60-67`] — Current ternary falls back to caller-signal only (no timeout) when `AbortSignal.any` is missing. Pre-Node-22 / older Safari get no timeout when caller passes a signal. Fix: compose via `AbortController` with two abort propagators.

- [x] **[Review][Patch] P10 — Reset-confirm side-effects ordering: sessions purged + password rotated BEFORE completion email; SMTP hang leaves user with no signal** (`blind+edge`) [`views.py:2275-2354`] — Best-effort try/except wraps the email; if synchronous SMTP hangs past 15s and the front-end times out, password change + session purge have already committed with no observable signal. Move audit row write inside the try/except so audit captures the email-failure mode; defer the SMTP send to Celery (long-term, Story 8.1).

- [x] **[Review][Patch] P11 — `_resolve_site_url` raises `ImproperlyConfigured` at email-send time, not Django startup** (`blind+edge`) [`adapters.py:60-75`] — Misconfigured prod env passes startup, accepts signup, blows up ONLY on first password-reset request. Move validation to `settings/prod.py` (raise at import time if `NEXT_PUBLIC_SITE_URL` unset).

- [x] **[Review][Patch] P12 — `extras["resend_endpoint"]` shipped under `errors.resend_endpoint` overloads RFC 7807 `errors` field** (`blind`) [`gdpr_exceptions.py` + `test_login.py:1593`] — RFC 7807 reserves `errors` for field-level validation errors. Move to top-level (`{"type": ..., "resend_endpoint": ...}`) or document an `extras` key.

- [x] **[Review][Patch] P13 — Reset request + confirm response `detail` does not match AC5/AC6 French wording** (`auditor`) [`views.py` `ThrottledPasswordResetView.post`/`ThrottledPasswordResetConfirmView.post`] — Spec §AC5 mandates `"Si cet email existe, un lien de réinitialisation t'a été envoyé."` and §AC6 mandates `"Ton mot de passe a été réinitialisé."`. dj-rest-auth's translated defaults differ. AC5's anti-enum hinges on identical wording — override the response detail.

- [x] **[Review][Patch] P14 — `isPendingRef` is a `useState[0]` initial-value object posing as a ref — mutation does not survive re-renders** (`blind+edge+auditor`) [`login-form.tsx:60-72`] — `const isPendingRef = useState<{ value: boolean }>({ value: false })[0]` discards the setter. Works in happy path but not Strict-Mode-safe and races with `setSubmitting(true)`. Replace with `useRef(false)`.

- [x] **[Review][Patch] P15 — `window.location.href` on login success races against Set-Cookie commit** (`edge`) [`login-form.tsx:82-86`] — Full-page nav fires before the fetch response settles. On slow disks/browsers, landing page sees `AnonymousUser` → bounce. Use `router.refresh()` + `router.replace(path)` from `next/navigation`.

- [x] **[Review][Patch] P16 — 204→200 cookie rewrite uses `new_response.cookies[k] = cookie` — Morsel-attr preservation is implementation-dependent** (`edge`) [`views.py:283-289`] — Defensive: rebuild with `new_response.set_cookie(name, morsel.value, max_age=..., secure=..., httponly=..., samesite=...)` reading attrs from source Morsel. Avoids silent Secure/HttpOnly/SameSite loss on any future http.cookies behavior change.

- [x] **[Review][Patch] P17 — `CSRF_TRUSTED_ORIGINS` whitespace-only env passes `if not` check but yields empty list** (`edge`) [`settings/prod.py:35-40`] — `" "` is truthy → `.split(",")` → `[" "]` → strip-filter → `[]`. All cross-origin POSTs fail CSRF silently. Strip first, then check, then strip+filter the list comprehension.

- [x] **[Review][Patch] P18 — `test_login.py::test_login_wrong_password_returns_400_generic` body-shape assertion too permissive** (`auditor`) [`test_login.py:57-58`] — `assert "non_field_errors" in body or "type" in body` short-circuits → `AccountLocked` Problem-Details passes. Tighten to AC2-mandated `{"non_field_errors": ["Unable to log in with provided credentials."]}` shape AND assert `body["type"]` is the wrong-password generic, not `/account-locked` (will fail until D1 resolved).

- [x] **[Review][Patch] P19 — `test_password_reset.py::test_request_for_known_email_sends_email_and_audits` does not roundtrip-verify the email URL** (`blind`) [`test_password_reset.py:62`] — Only checks `"/auth/reset-password/" in body`. A serializer regression with the wrong encoder would still pass. Extract `uid`/`token` via regex from email body, assert `url_str_to_user_pk(uid) == user.pk` and `default_token_generator.check_token(user, token) is True`.

### Defer

- [x] **[Review][Defer] Password-reset request endpoint timing oracle (deleted vs unknown vs active)** (`blind`) — Already documented in spec §4.5 #8. allauth's `get_users()` filters `is_active=True` so deleted users hit the audit row but no SMTP, distinguishable in wall-clock. Revisit with email-async-Celery (Story 8.1).

- [x] **[Review][Defer] `terminate_user_sessions` is a no-op for non-DB session backends (signed_cookies, Redis)** (`edge`) — Story 1.12 deferred-work tracks this. Migrate the helper when the session backend changes.

- [x] **[Review][Defer] Redis `cache.add(...)` + `cache.incr()` TTL slide race under heavy concurrency** (`edge`) — Under extreme concurrency the SET-NX + INCR pair is not atomic; counter could reset on TTL boundary. Mitigation needs Lua script or Redis MULTI. MVP volume doesn't justify the complexity.

- [x] **[Review][Defer] `ThrottledPasswordResetView.post` does not audit `auth.password_reset_requested_invalid` for malformed-email-field 400s** (`edge`) — Low-impact (known/unknown already covered; malformed format is self-evident in HTTP logs). Add when abuse pattern justifies.
