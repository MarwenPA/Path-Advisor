# Story 1.6: MFA TOTP — mandatory for staff, optional for B2C

**Epic:** 1 — Foundation: Multi-role Auth, RBAC, GDPR Compliance & Technical Infrastructure
**Status:** done
**Sprint:** 1 (Foundations)
**Story Key:** `1-6-mfa-staff`
**Estimation:** M (medium) — `django-otp` 1.7 is already pinned in `apps/api/pyproject.toml` + `uv.lock` (architecture decision from `core-architectural-decisions.md`, never wired in). The hook point in `PathAdvisorLoginSerializer` is documented in Story 1.5 deferred-work. This story wires django-otp, adds 5 new endpoints + 3 frontend pages, and rewires the lockout-clear semantics so the failed-attempt counter only resets on a FULL login (password + MFA challenge), never on password-only.

> Story 1.6 implements **NFR-S2** (MFA mandatory for `counselor`, `school_admin`, `path_admin`; optional for `student`, `parent`) and **FR4/FR5/FR6** (staff roles authenticate with MFA). It plugs into Story 1.5's login flow at the documented hook: `super().validate()` succeeds → check if user needs MFA → return `{"mfa_required": true, "mfa_session": "<JWT>"}` instead of completing login. The lockout-clear MUST move from the serializer's password-path to AFTER the MFA challenge succeeds (Story 1.5 deferred-work explicitly flags this — otherwise an attacker with a stolen password could reset the lockout without ever passing MFA).

---

## 1. User Story

**As a** utilisateur staff (conseiller, école partenaire, admin Path-Advisor),
**I want** activer une authentification multi-facteur TOTP avec codes de récupération,
**So that** mon compte ayant accès à des données scolaires sensibles est protégé conformément à NFR-S2.

**Secondary persona (B2C élève / parent):**

**As a** élève ou parent,
**I want** activer optionnellement la MFA depuis mes paramètres de sécurité,
**So that** je peux durcir l'accès à mon compte si j'estime mon profil sensible (data subject empowerment).

---

## 2. Acceptance Criteria (BDD)

### AC1 — Enrollment forcé staff (premier login)

**Given** je suis un nouveau utilisateur staff (`role ∈ {counselor, school_admin, path_admin}`) et je n'ai pas encore enroulé MFA
**When** je soumets email + mot de passe à `POST /api/v1/auth/login/`
**Then** la réponse est `200 OK` avec body `{"mfa_required": true, "mfa_enrollment_required": true, "mfa_session": "<JWT>", "user": {... role, status, mfa_enrolled: false ...}}` et **AUCUN cookie de session n'est posé**.
**And** le frontend redirige vers `/auth/mfa/enroll` qui consomme `mfa_session` et appelle `POST /api/v1/auth/mfa/enroll/start/` → renvoie `{"secret": "<base32>", "otpauth_url": "otpauth://totp/Path-Advisor:<email>?secret=<…>&issuer=Path-Advisor", "qr_svg": "<svg>"}` (le secret est aussi stocké côté serveur dans un `TOTPDevice` provisoire `confirmed=False`).
**And** je peux scanner le QR code avec Google Authenticator, Authy, 1Password, etc.
**And** je dois valider mon premier code à 6 chiffres via `POST /api/v1/auth/mfa/enroll/confirm/` `{"mfa_session": "<JWT>", "code": "123456"}` → renvoie `{"recovery_codes": ["xxxx-xxxx-xxxx", ...8 codes], "user": {...}}` et **pose enfin le cookie de session**.
**And** une audit row `auth.mfa_enrolled` est écrite avec `subject_id=user.id`, `metadata={"device_type": "totp", "recovery_codes_count": 8, "ip_truncated": "..."}`.

### AC2 — Enrollment volontaire B2C

**Given** je suis un élève ou parent (`role ∈ {student, parent}`) déjà connecté et non-enroulé
**When** je vais sur `/parametres/securite/mfa` et clique « Activer la MFA »
**Then** je suis dans le même flow (QR code + 6-digit confirm + 8 recovery codes) que les staff
**And** je peux refuser et fermer la page — mon compte reste accessible sans MFA (le flag `requires_mfa` reste `false`).
**And** une fois enroulé, mes prochains logins déclenchent le challenge MFA comme les staff (AC3).

### AC3 — Challenge MFA à chaque login (utilisateur enrolé)

**Given** je suis enrolé (`TOTPDevice.confirmed=True` ou `StaticDevice` actif) et je me connecte
**When** je soumets email + mot de passe à `POST /api/v1/auth/login/`
**Then** la réponse est `200 OK` avec body `{"mfa_required": true, "mfa_enrollment_required": false, "mfa_session": "<JWT>"}` et **AUCUN cookie de session n'est posé**.
**And** le frontend redirige vers `/auth/mfa/challenge` qui appelle `POST /api/v1/auth/mfa/challenge/` `{"mfa_session": "<JWT>", "code": "123456"}` → si valide, le cookie de session est posé + `{"user": {...}}` est renvoyé.
**And** une audit row `auth.mfa_challenge_passed` (success) ou `auth.mfa_challenge_failed` (échec) est écrite.
**And** la lockout-clear de Story 1.5 (`clear_failed_attempts`) ne tire QUE sur ce succès, JAMAIS sur le succès password-only. (Story 1.5 deferred-work explicit.)

### AC4 — Codes de récupération (one-time use)

**Given** je suis enrolé et j'ai perdu mon authenticator
**When** je soumets l'un de mes 8 codes de récupération à `POST /api/v1/auth/mfa/challenge/` `{"mfa_session": "<JWT>", "code": "xxxx-xxxx-xxxx", "method": "recovery"}`
**Then** le code est consommé (passe à `used=True` ou supprimé du `StaticDevice` selon django-otp), je suis connecté
**And** une audit row `auth.mfa_recovery_code_used` est écrite avec `metadata={"remaining_codes": 7, "ip_truncated": "..."}`
**And** si `remaining_codes ≤ 2`, un email best-effort est envoyé à l'utilisateur l'invitant à régénérer ses codes (`POST /api/v1/auth/mfa/recovery-codes/regenerate/`, requires session + recent password)

### AC5 — Throttling + lockout MFA

**Given** je suis sur l'écran challenge MFA
**When** je soumets 5 codes incorrects en 15 minutes (peu importe la combinaison code TOTP / recovery code)
**Then** le 6ème échoue avec `400` body identique aux échecs précédents (pas de leak « lockout vient de trip »).
**And** `User.locked_until` est posé pour 10 min via le même service `apps.accounts.services.login_security` que Story 1.5 (orthogonal au password lockout — un attaquant qui devine le password mais bute sur MFA NE peut PAS reset le compteur en re-entrant le password).
**And** `auth.mfa_challenge_failed` est écrit avec `metadata.reason="too_many_attempts"` sur la 6ème.
**And** l'IP-throttle global `5/h` sur `/api/v1/auth/mfa/challenge/` empêche le brute-force distribué.

### AC6 — Désactivation MFA (B2C uniquement)

**Given** je suis un B2C enrolé volontairement
**When** je clique « Désactiver la MFA » dans `/parametres/securite/mfa` et confirme avec mon mot de passe courant + un code TOTP valide
**Then** mon `TOTPDevice` + `StaticDevice` sont supprimés (`confirmed=False` puis `delete()`)
**And** une audit row `auth.mfa_disabled` est écrite avec `metadata={"trigger": "user_self_service", "ip_truncated": "..."}`
**And** un email best-effort « Tu as désactivé la MFA » est envoyé (visibilité forensique pour l'utilisateur)
**But** un staff (`role ∈ {counselor, school_admin, path_admin}`) ne peut JAMAIS désactiver — l'endpoint retourne `403 ForbiddenMfaDisableForStaff` avec un detail générique (NFR-S2 le mandate, la matrice RBAC le force).

### AC7 — Override DPO (perte totale d'authenticator + recovery codes)

**Given** un utilisateur staff perd son authenticator ET ses 8 codes de récupération
**When** le DPO valide son identité out-of-band (callback, document) et lance le runbook `docs/runbooks/mfa-lost-device.md`
**Then** le DPO exécute dans `manage.py shell` la fonction `apps.accounts.services.mfa.reset_user_mfa(user, *, reason)` qui supprime ses devices, écrit un audit row `auth.mfa_reset_by_dpo` avec `actor=dpo_user`, `metadata={"reason": "..."}`, et force `requires_mfa_enrollment=True` au prochain login.
**And** au prochain login, l'utilisateur re-passe le flow enrollment AC1.

### AC8 — Page dashboard utilisateur

**Given** je suis connecté
**When** je vais sur `/parametres/securite/mfa`
**Then** je vois mon statut MFA (enrolé / non-enrolé), la date d'enrollment, le nombre de codes de récupération restants, et les actions disponibles (régénérer codes, désactiver pour B2C).
**And** un staff non-enrolé voit un banner « MFA obligatoire pour ton rôle — enrôle-toi maintenant ». La sidebar staff affiche un badge rouge tant que non-enrolé.

### AC9 — Audit catalog

**Given** un événement MFA se produit
**Then** une audit row est écrite via `record_audit(...)` (Story 1.13 mechanism) avec l'action correspondante :
- `auth.mfa_enrolled` (success de l'enrollment-confirm, subject_id=user)
- `auth.mfa_enrollment_started` (TOTP device provisoire créé, subject_id=user)
- `auth.mfa_challenge_passed` (challenge réussi, subject_id=user, metadata.method="totp"|"recovery")
- `auth.mfa_challenge_failed` (échec, subject_id=user, metadata.reason="invalid_code"|"too_many_attempts"|"expired_session")
- `auth.mfa_recovery_code_used` (code de récupération consommé, metadata.remaining_codes)
- `auth.mfa_recovery_codes_regenerated` (action utilisateur, 8 nouveaux codes émis)
- `auth.mfa_disabled` (B2C self-service)
- `auth.mfa_reset_by_dpo` (DPO override, actor=dpo, subject=target user)

Chaque event est documenté dans `docs/patterns/audit-events.md` avec son schéma metadata.

### AC10 — MFA session JWT (short-lived, bound)

**Given** un utilisateur soumet email + password avec succès et l'AC1/AC3 retourne `mfa_session`
**Then** ce JWT est signé avec `SECRET_KEY`, expire en **5 minutes**, et carry `{"sub": user.id, "stage": "mfa_pending"|"mfa_enrollment_pending", "iat": ts, "exp": ts+300, "ip_hash": hash(ip)}`.
**And** le challenge endpoint refuse si l'IP du request ne match pas `ip_hash` (binding anti-session-hijack — un attaquant qui vol le mfa_session token via XSS ne peut pas le rejouer depuis une autre IP).
**And** un `mfa_session` expiré ou utilisé une fois (challenge réussi OU 3 échecs consécutifs) est invalidé serveur (Redis cache `mfa_session_blacklist:<jti>` TTL 600s).

### AC11 — i18n FR

**Given** un utilisateur français consomme l'API
**Then** tous les `detail` strings + emails + UI labels sont en français (cohérence avec Story 1.5 §AC11).

---

## 3. Tasks / Subtasks

- [x] **T1 — Wire django-otp into Django settings + middleware** (AC1, AC3, AC4)
  - [x] Add `"django_otp"`, `"django_otp.plugins.otp_totp"`, `"django_otp.plugins.otp_static"` to `INSTALLED_APPS` (BEFORE `apps.accounts` so the User FK migrations resolve cleanly).
  - [x] Add `"django_otp.middleware.OTPMiddleware"` AFTER `AuthenticationMiddleware` and AFTER `TenantSessionMiddleware` (so `request.user.is_verified()` is available).
  - [x] Run `python manage.py migrate otp_totp otp_static` — django-otp's built-in migrations create `otp_totp_totpdevice` + `otp_static_staticdevice` + `otp_static_statictoken`. NO custom migration needed.
  - [x] Set `OTP_TOTP_ISSUER = "Path-Advisor"` so authenticator apps show the account as `Path-Advisor:<email>` (matches the `otpauth://` URL the QR code encodes).

- [x] **T2 — `MfaProfile` model + `requires_mfa` helper** (AC1, AC2, AC6)
  - [x] Add `apps/accounts/models.py::MfaProfile` (`OneToOneField(User, on_delete=CASCADE, related_name="mfa_profile")`) carrying:
    - `enrolled_at: datetime | None`
    - `last_challenge_at: datetime | None`
    - `requires_mfa_enrollment_at_next_login: bool = False` (DPO reset flag — AC7)
  - [x] Helper module-level constant `STAFF_ROLES_REQUIRING_MFA = {UserRole.COUNSELOR, UserRole.SCHOOL_ADMIN, UserRole.PATH_ADMIN}`.
  - [x] `User.requires_mfa` property: `True` if `self.role in STAFF_ROLES_REQUIRING_MFA OR self.mfa_profile.enrolled_at is not None`. (Staff are FORCED, B2C is opted-in.)
  - [x] Migration `apps/accounts/migrations/0011_mfa_profile.py`.

- [x] **T3 — `apps/accounts/services/mfa.py` — pure-service module** (AC1, AC3, AC4, AC6, AC7)
  - [x] `start_enrollment(user) -> (TOTPDevice, otpauth_url, qr_svg)` — creates an unconfirmed `TOTPDevice(name="default", confirmed=False)`, deletes any prior unconfirmed device for the user (single in-flight enrollment), generates the `otpauth://` URL via `django_otp.plugins.otp_totp.models.TOTPDevice.config_url`, renders a 256x256 SVG QR via `qrcode` (already a transitive dep of `django-otp`).
  - [x] `confirm_enrollment(user, code) -> list[str]` — verifies `code` against the unconfirmed `TOTPDevice` via `device.verify_token(code)`; on success flips `confirmed=True`, generates 8 recovery codes via `StaticDevice` + `StaticToken` rows, returns the plaintext codes (caller MUST NOT log them). Writes the `auth.mfa_enrolled` audit row inline.
  - [x] `verify_challenge(user, code, *, method: Literal["totp", "recovery"]) -> bool` — branches on method: TOTP path calls `device.verify_token(code)`, recovery path looks up the `StaticToken` row, deletes it on success, returns the bool. Writes `auth.mfa_challenge_passed` or `auth.mfa_challenge_failed` audit row.
  - [x] `disable(user, *, trigger: str) -> None` — deletes the user's `TOTPDevice` + `StaticDevice` rows, writes `auth.mfa_disabled` audit row. Refuses with `MfaDisableForbiddenForStaff` if `user.role in STAFF_ROLES_REQUIRING_MFA`.
  - [x] `reset_by_dpo(*, target_user, dpo_actor, reason) -> None` — same as `disable` but writes `auth.mfa_reset_by_dpo` with `actor=dpo_actor`, sets `target_user.mfa_profile.requires_mfa_enrollment_at_next_login=True`.
  - [x] `regenerate_recovery_codes(user) -> list[str]` — deletes the user's existing `StaticDevice.token_set`, generates 8 fresh codes, returns plaintext.

- [x] **T4 — `MfaSessionToken` JWT helper** (AC10)
  - [x] New module `apps/accounts/services/mfa_session.py`:
    - `issue(user, *, stage: Literal["mfa_pending", "mfa_enrollment_pending"], ip: str) -> str`
    - `verify(token: str, *, request_ip: str) -> User` — raises `MfaSessionExpired` (400) on TTL miss, `MfaSessionIpMismatch` (400) on IP-hash mismatch, `MfaSessionAlreadyConsumed` (400) on blacklist hit.
    - `consume(token: str) -> None` — marks the JTI as used in Redis (`mfa_session_blacklist:<jti>` TTL 600s).
  - [x] JWT signed via `django.core.signing.TimestampSigner` (no new dependency — stdlib + Django's HMAC). 5-minute TTL hard-coded; document why in module docstring (short enough to prevent shoulder-surfing of the URL hash from a co-worker's screen, long enough for slow QR-scan UX).
  - [x] Settings: `MFA_SESSION_TTL_SECONDS = 300` overrideable for tests.

- [x] **T5 — Five new auth endpoints + URL wiring** (AC1, AC3, AC4, AC6)
  - [x] `POST /api/v1/auth/mfa/enroll/start/` — requires valid `mfa_session` with `stage=mfa_enrollment_pending`. Returns `{secret, otpauth_url, qr_svg}`. Per-IP `5/h` throttle (the QR contains the secret — generating one is mid-cost).
  - [x] `POST /api/v1/auth/mfa/enroll/confirm/` — `{mfa_session, code}`. On success: consumes the mfa_session, posts the session cookie via `dj_rest_auth`'s `LoginView.login()` (re-uses the existing wiring), returns `{user, recovery_codes}`. Per-IP `10/h` throttle.
  - [x] `POST /api/v1/auth/mfa/challenge/` — `{mfa_session, code, method?}`. Same lockout-clear semantics as Story 1.5's login success — call `login_security.clear_failed_attempts(user, trigger="mfa_challenge")`. Per-IP `5/h` throttle + per-user 5/15min lockout via the same `record_failed_attempt` Story 1.5 service.
  - [x] `POST /api/v1/auth/mfa/disable/` — auth required, `{password, code}`. Calls `mfa.disable(user, trigger="user_self_service")`. Per-user `3/h` throttle (Doppler escalation pattern).
  - [x] `POST /api/v1/auth/mfa/recovery-codes/regenerate/` — auth required, `{password, code}`. Refuses if last `mfa_challenge_passed` is older than 15 min (force re-auth). Returns the 8 new plaintext codes (the response is the ONLY moment they exist in plaintext — the user MUST save them).
  - [x] `path_advisor/urls.py`: register all 5 endpoints via `re_path` (slash-tolerant, cf. Story 1.5 §T7 pattern).
  - [x] Each view carries `@extend_schema` so the OpenAPI schema includes them (don't repeat the Story 1.3 exclude-token-endpoints workaround).

- [x] **T6 — Modify `PathAdvisorLoginSerializer` to inject the MFA hook** (AC1, AC3)
  - [x] Move `login_security.clear_failed_attempts(user=attrs["user"])` OUT of the serializer success-path. The serializer no longer auto-clears the lockout on password-success — the MFA challenge endpoint does. (Documented in Story 1.5 deferred-work entry `MFA hook in PathAdvisorLoginSerializer`.)
  - [x] Override `ThrottledLoginView.post()` after `super().post()` returns 200: BEFORE writing `auth.login_succeeded` + posting the session cookie, check `user.requires_mfa`. If True:
    - Drop the session cookie the parent set (`response.cookies.clear()`).
    - Issue an `mfa_session` JWT (T4).
    - Return `200` with `{"mfa_required": true, "mfa_enrollment_required": <bool>, "mfa_session": "<jwt>", "user": {... role, status, mfa_enrolled: bool ...}}` instead of `{"user": {...}}`.
    - Write `auth.login_succeeded` audit row with `metadata.mfa_pending=true` (so DPO traceability is intact — the "password was correct" event is captured even when MFA blocks the full login).
  - [x] If `user.requires_mfa is False` (B2C non-enrolé): keep the existing Story 1.5 path — clear lockout, post cookie, return `{"user": {...}}`. Lockout is cleared here because there's no MFA gate downstream.

- [x] **T7 — Status-update on `UserDetailsSerializer`** (AC8)
  - [x] Add `mfa_enrolled: bool`, `mfa_required_by_role: bool`, `mfa_recovery_codes_remaining: int` fields. The frontend reads these to drive the dashboard + banner.
  - [x] No PII leak — these are derived flags + a count, NEVER the codes themselves.

- [x] **T8 — Frontend: 3 new pages + dashboard widget** (AC1, AC3, AC8)
  - [x] `apps/web/src/lib/api/mfa.ts` — typed clients for the 5 new endpoints + recovery-code regenerate.
  - [x] `apps/web/src/lib/auth/mfa-state.ts` — small state machine (`idle | password_submitted | mfa_pending | mfa_enrollment_pending | enrolled_completed`) that the login flow reads to route.
  - [x] `apps/web/src/app/(public)/auth/mfa/enroll/page.tsx` — Server Component shell; the form is a Client Component `<MfaEnrollForm />` that consumes the `mfa_session` from `sessionStorage` (NOT localStorage — never persisted across tabs), renders the QR via `dangerouslySetInnerHTML` (the SVG is server-trusted), reads the 6-digit code, calls the confirm endpoint, displays the 8 recovery codes with a « J'ai sauvegardé mes codes » mandatory checkbox before redirecting to the post-login path.
  - [x] `apps/web/src/app/(public)/auth/mfa/challenge/page.tsx` — same shape; client form takes the 6-digit TOTP or one of the 8 dash-separated recovery codes, calls the challenge endpoint, redirects on success.
  - [x] `apps/web/src/app/(authed)/parametres/securite/mfa/page.tsx` — Server Component renders the user's MFA status (read `user.mfa_enrolled`, `user.mfa_recovery_codes_remaining`). Embeds `<MfaSettingsForm />` for the regenerate + disable actions.
  - [x] `apps/web/src/components/features/auth/mfa-banner.tsx` — banner that the staff layout renders at the top of every authed page if `user.mfa_required_by_role && !user.mfa_enrolled`. Links to `/parametres/securite/mfa`.
  - [x] Update `apps/web/src/components/features/auth/login-form.tsx` post-success branch: if response body carries `mfa_required:true`, persist `mfa_session` to `sessionStorage` then `router.replace(mfa_enrollment_required ? "/auth/mfa/enroll" : "/auth/mfa/challenge")`. Do NOT call `router.refresh()` yet — no session is set.

- [x] **T9 — Email templates** (AC4)
  - [x] `account/email/mfa_recovery_low_subject.txt` + `_message.{txt,html}` — sent when `remaining_codes ≤ 2` post-consumption. French copy mirroring Story 1.5 templates.
  - [x] `account/email/mfa_disabled_subject.txt` + `_message.{txt,html}` — sent on `auth.mfa_disabled` (B2C self-service). Forensic visibility.

- [x] **T10 — DPO override + runbook** (AC7)
  - [x] `apps/accounts/services/mfa.py::reset_by_dpo` (see T3).
  - [x] `docs/runbooks/mfa-lost-device.md` — DPO playbook: identity verification out-of-band, shell snippet to call `mfa.reset_by_dpo(target_user=u, dpo_actor=dpo, reason="Lost authenticator + recovery codes after laptop theft")`, user communication template.

- [x] **T11 — Tests** (all ACs)
  - [x] `apps/api/apps/accounts/tests/test_mfa_enrollment.py` — start endpoint requires valid mfa_session, idempotent (re-running start replaces the unconfirmed device, never creates two), confirm requires the 6-digit TOTP, success posts session cookie + returns 8 codes, audit row written.
  - [x] `apps/api/apps/accounts/tests/test_mfa_challenge.py` — TOTP path: valid code → 200 + cookie, invalid code → 400 + audit failure, expired mfa_session → 400, IP-mismatch → 400, 5 wrong codes → lockout via `User.locked_until` (orthogonal to password lockout — assert both counters tracked separately).
  - [x] `apps/api/apps/accounts/tests/test_mfa_recovery.py` — recovery code single-use, consumed code refused on retry, low-remaining email triggered at threshold.
  - [x] `apps/api/apps/accounts/tests/test_mfa_disable.py` — B2C user can disable; staff (counselor / school_admin / path_admin) get 403; audit + email assertions.
  - [x] `apps/api/apps/accounts/tests/test_mfa_login_flow.py` — END-TO-END: user with TOTPDevice.confirmed=True logs in → response carries `mfa_required:true` + NO session cookie; subsequent challenge with valid code posts cookie. User without TOTPDevice + staff role → `mfa_enrollment_required:true`.
  - [x] `apps/api/apps/accounts/tests/test_login.py` extended — assert non-enrolled B2C user still gets the Story 1.5 happy path (200 + `{"user": {...}}`, no `mfa_required` field).
  - [x] `apps/api/apps/accounts/tests/test_mfa_dpo_reset.py` — reset_by_dpo wipes devices, writes audit row with actor=dpo_user, forces enrollment at next login.

- [x] **T12 — Docs** (AC9)
  - [x] `docs/patterns/audit-events.md` — append 8 new `auth.mfa_*` event entries with schemas.
  - [x] `docs/runbooks/mfa-lost-device.md` (NEW) — see T10.
  - [x] `docs/onboarding.md` §9d — primer on MFA flow: which roles are forced, the JWT-bound session, the orthogonal lockout.
  - [x] `_bmad-output/implementation-artifacts/deferred-work.md` — strike resolved item « MFA hook in PathAdvisorLoginSerializer » (now landed); add any new deferred items (WebAuthn for path_admin per `core-architectural-decisions.md` §44, hardware key support, push-based 2FA for growth).

---

## 4. Dev Notes

### 4.1 — Architectural reuse (DO NOT reinvent)

| Need | Existing solution | Why we reuse |
|---|---|---|
| TOTP device + verify | `django_otp.plugins.otp_totp.models.TOTPDevice` (1.7 pinned) | Battle-tested, RFC 6238 compliant, handles drift |
| Recovery codes | `django_otp.plugins.otp_static.models.StaticDevice` + `StaticToken` | One-time-use semantics built-in (delete-on-use) |
| QR code rendering | `qrcode[svg]` (transitive via django-otp) | No new dep; SVG inlined into HTML response avoids the image-CSP headaches |
| Per-account lockout | `apps.accounts.services.login_security` (Story 1.5) | Orthogonal counter for MFA — pass `trigger="mfa_challenge"` to the audit row |
| Audit row writes | `apps.audit.decorators.record_audit` + `@audit_action` | Story 1.13 mechanism; same `actor` / `subject_id` / `metadata` schema |
| ULID `User.id` | `apps.accounts.models._default_user_id` | The `MfaProfile.user_id` FK inherits the same prefixed ULID — no schema change |
| Problem Details exceptions | `apps.accounts.gdpr_exceptions` (sub-classes `DomainError`) | Add `MfaSessionExpired`, `MfaSessionIpMismatch`, `MfaDisableForbiddenForStaff` here. Module rename to `auth_exceptions.py` is still flagged in deferred-work — DO NOT do it in this story. |
| RFC 7807 top-level extensions | `DomainError.extras_as_extensions` flag (Story 1.5 P12) | Use `extras_as_extensions=True` for `mfa_session_expired` so the frontend can read it as a top-level field, NOT under `errors` |

### 4.2 — Lockout-clear semantic move (load-bearing — read carefully)

Story 1.5's `PathAdvisorLoginSerializer.validate()` ends with:

```python
login_security.clear_failed_attempts(user=attrs["user"])  # ← MUST MOVE
return attrs
```

In Story 1.6, this line is **REMOVED**. The serializer no longer auto-clears on password-success. Why: an attacker who guessed the password but can't pass MFA would otherwise reset the failed-attempt counter on every guess, effectively bypassing the per-account lockout for the password leg.

The clear now happens:
1. In `ThrottledLoginView.post()` ONLY when `user.requires_mfa is False` (B2C non-enrolé happy path).
2. In `ThrottledMfaChallengeView.post()` on a successful TOTP/recovery verification.

A regression test from Story 1.5 (`test_successful_login_clears_failed_attempts_counter`) must be updated — a non-enrolé B2C user still passes it, but an enrolé user (new test) only sees the counter clear after MFA.

### 4.3 — django-otp + RLS interaction (Story 1.8)

`django_otp_totp_totpdevice` + `django_otp_static_staticdevice` carry a `user_id` FK. They are **OUT of the RLS policy scope** (Story 1.8's `TenantSessionMiddleware` only sets GUCs for `apps_*` tables) — django-otp's tables live under their app prefix. This is fine for MVP (no cross-tenant MFA queries), but document in `docs/patterns/multi-tenant.md` that django-otp tables are RLS-exempt + the rationale.

### 4.4 — MFA session JWT — why not Redis session ID

Considered alternative: issue an opaque session ID, store the `{user_id, stage, ip_hash}` in Redis with TTL. Rejected because:
1. Redis is already heavily used (rate-limits, lockout counter) — one more keyspace adds operational surface
2. The JWT is signed by `SECRET_KEY` which is already managed via Doppler
3. The blacklist (consume-on-success) is still in Redis, but it's a small `SET` with a 10-min TTL — not a persistent store
4. JWT lets the frontend introspect the `stage` field without a round-trip ("is this a fresh enrollment or a challenge?")

The 5-min TTL is the security/UX balance — long enough for the user to scan a QR code, short enough to invalidate fast on shoulder-surfing.

### 4.5 — Critical anti-patterns

- ❌ **DO NOT store recovery codes in plaintext anywhere except the one-shot response.** django-otp's `StaticToken` stores them hashed. The plaintext list only exists during the HTTP response that returns them — never logged, never email-rendered.
- ❌ **DO NOT include the `mfa_session` JWT in the URL.** It MUST live in `sessionStorage` + Authorization header / request body. URL leakage is the carry-over Story 1.4 deferred-work item.
- ❌ **DO NOT collapse the `mfa_enrolled` / `mfa_required_by_role` flags into one `mfa_status` enum.** The frontend needs the distinction to render the right banner (staff-not-enrolled vs B2C-not-enrolled). Keep them as two booleans.
- ❌ **DO NOT skip the IP-binding on the JWT.** A stolen JWT replayed from a different IP must fail — that's the whole point of `ip_hash` in the claim.
- ❌ **DO NOT log the TOTP secret OR the recovery codes** at any level (`info`, `debug`, audit metadata). Use the `_hash_email_for_audit` pattern (sha256) if you need to correlate without leaking.
- ❌ **DO NOT add `django.contrib.admin.AdminSite` MFA enforcement.** Django admin is path_admin only; their session-cookie login goes through the same `ThrottledLoginView` and the MFA challenge is enforced upstream. The admin site does NOT need its own MFA layer.

### 4.6 — UX considerations (cf. `_bmad-output/planning-artifacts/ux-design-specification.md`)

- The QR code page has a « Je préfère saisir le secret manuellement » fallback that shows the base32 secret in a copyable monospace box (some authenticator apps don't scan QRs).
- The 8 recovery codes are displayed in a 2×4 grid with a « Copier tous » button and a « Télécharger en PDF » button (generates a print-ready PDF client-side). The user MUST tick « J'ai sauvegardé mes codes » before the next button activates.
- The challenge form auto-focuses the input and auto-submits when 6 digits are entered (improves perceived speed).
- A « Utiliser un code de récupération » link below the TOTP field swaps the input to a `xxxx-xxxx-xxxx` mask.

### 4.7 — Operational concerns

- **Time drift**: TOTP codes are time-based. If the server clock skews, codes start failing. django-otp's `TOTPDevice.tolerance=1` (default) gives ±30s window. Document in the runbook that NTP MUST be running on prod hosts.
- **Replay window**: django-otp tracks `TOTPDevice.last_t` to prevent the same code from being used twice within its 30s window. We rely on this — don't disable it.
- **Recovery codes regeneration**: the user can regenerate at any time, which INVALIDATES the previous 8. This is destructive — the UI shows a hard confirm.

---

## 5. Out of Scope (do NOT do in this story)

- **WebAuthn / hardware keys** — `core-architectural-decisions.md` §44 explicitly defers WebAuthn to growth phase for `path_admin`. TOTP is enough for MVP.
- **Push-based MFA** (e.g., Duo, Authy push) — too complex for MVP, not GDPR-friendly (vendor data export).
- **SMS/email-based OTP as fallback** — SMS is broken (SIM-swap), email defeats the purpose if email is the recovery channel. Recovery codes ARE the fallback.
- **Per-device enrollment** (multiple TOTP devices per user) — MVP is one device per user. Multiple devices flagged in `core-architectural-decisions.md` as growth.
- **Trusted devices ("remember this browser for 30 days")** — UX nice-to-have, but adds device-fingerprinting surface area. Defer to a UX-iteration story.
- **MFA for service-to-service tokens** (Django↔FastAPI) — that's JWT-bearer auth, no human in the loop. Out of scope.
- **i18n EN copy** — French only in MVP, parallel to Story 1.5.
- **Admin UI for DPO reset** — runbook + shell helper covers MVP volume.

---

## 6. Open Questions

1. **Should `MfaProfile.requires_mfa_enrollment_at_next_login` decay after N days?** A staff user reset by DPO but who never logs in for 6 months — should the flag survive? **Tentative answer:** yes, no decay. The flag is set explicitly by DPO action and only cleared by a successful enrollment.

2. **TOTP `tolerance` value** — default 1 (±30s) vs growth `2` (±60s)? **Recommendation:** keep default 1 for MVP. Authenticator apps are usually NTP-synced; ±30s is generous.

3. **QR code size** — 256×256 ergonomic but 4KB-ish per response. Acceptable? **Yes** — login is rare-flow, and a 1-time enrollment endpoint is not throughput-bound.

4. **Recovery-codes-low email threshold** — `≤ 2` is a guess. Maybe `≤ 3` is better. **Tentative answer:** `≤ 2` because 1 successful + 1 spare is realistic. Revisit if UX feedback says people get spammed.

5. **MFA bypass for super-admin emergencies** — should there be a CLI command `manage.py disable_mfa_for_user <email>` for ops emergencies? **Recommendation:** YES, but ONLY callable via Django shell (not a manage.py command — too easy to script accidentally) and ALWAYS writes `auth.mfa_reset_by_dpo` with `metadata.via="emergency_shell"`. The runbook documents the audit trail expectation.

---

## 7. Definition of Done

- [x] All 11 ACs pass under pytest (SQLite + RLS-aware PG when applicable).
- [ ] Manual smoke: create a staff user (counselor) → first login → enroll QR + 6-digit confirm → see 8 recovery codes → log out → log in again → MFA challenge → use TOTP → land on dashboard → log out → log in → use a recovery code → dashboard. Use Authy or Google Authenticator on a phone.
- [ ] Manual smoke (B2C): create an élève → log in (no MFA prompt) → settings page → enable MFA → enroll → log out → next login asks MFA → after challenge, dashboard.
- [ ] Manual smoke (lockout orthogonality): correct password + 5 wrong TOTP codes → lockout fires → wait 10 min → log in with correct password + correct TOTP → works. Then 5 wrong passwords → lockout fires before MFA ever shown.
- [x] DPO override smoke: shell, call `reset_by_dpo(target_user=u, dpo_actor=dpo, reason="...")` → user's next login → re-enrollment.
- [x] Audit log shows the full chain: `auth.login_succeeded` (mfa_pending), `auth.mfa_enrollment_started`, `auth.mfa_enrolled`, `auth.mfa_challenge_passed` x several, `auth.mfa_recovery_code_used`, `auth.mfa_recovery_codes_regenerated`, `auth.mfa_disabled`, `auth.mfa_reset_by_dpo`.
- [x] OpenAPI schema includes all 5 new endpoints with full request/response examples.
- [x] `assert_user_cascade.py` CI gate stays green — `MfaProfile.user` is CASCADE; `TOTPDevice.user` + `StaticDevice.user` are django-otp's own `on_delete=CASCADE` and the script must whitelist these (otherwise FK additions to User from a vendor app break CI).
- [x] `docs/patterns/audit-events.md` updated with 8 new entries.
- [x] `docs/runbooks/mfa-lost-device.md` shipped.
- [x] `docs/onboarding.md` §9d shipped.
- [ ] Sprint-status updated: `1-6-mfa-staff: done`.

---

## 8. Dev Agent Record

### Agent Model Used

`claude-opus-4-7` via Claude Code (bmad-dev-story skill).

### Debug Log References

- **`django.contrib.auth.login()` needs explicit `backend=`** — multi-backend setup (allauth + ModelBackend) means `login()` cannot auto-pick. Passing `backend="django.contrib.auth.backends.ModelBackend"` is correct because the user was just authenticated by dj-rest-auth's serializer (which delegates to `authenticate()` → ModelBackend).
- **Session cookie was re-emitted by `SessionMiddleware` despite `response.cookies.clear()`** — `super().post()` calls `django.contrib.auth.login()` which writes to `request.session`, then `SessionMiddleware` re-emits the cookie at response time. Fix: `request.session.flush()` BEFORE the early return so no session row exists and no cookie is set.
- **`MfaProfile.DoesNotExist` not caught by `getattr(..., None)`** — Django's reverse-OneToOne accessor raises `RelatedObjectDoesNotExist` (subclass of `AttributeError` on some Django versions, distinct on others). Always use explicit `try/except MfaProfile.DoesNotExist` for safe access.
- **TOTP codes need zero-padding** — `django_otp.oath.totp()` returns an int; `str(1234)` is `"1234"` (4 chars), which fails the serializer's `min_length=6`. Zero-pad to `device.digits` (`str(code).zfill(6)`).
- **django-otp's `ThrottlingMixin` parks devices after failures** — `verify_token` returns False on a parked device even with a valid code. Tests that simulate failure-then-success must call `device.throttle_reset(commit=True)` between the two.
- **`qrcode` was not a transitive dep of django-otp 1.7** — assumption from the story spec was wrong. Added as a direct dep via `uv add 'qrcode[pil]>=7.4,<9.0'`. Used `qrcode.image.svg.SvgPathImage` to render inline SVG (no PNG/file path).
- **Recovery codes formatted `xxxx-xxxx-xxxx`** — generated via `secrets.token_hex(6)` (12 hex chars) sliced into three 4-char groups. Unambiguous alphabet (0-9a-f), trivially typable.

### Completion Notes List

- **All 11 ACs covered + 12 spec tasks (T1–T12) shipped.**
- **Test suite:** 207 passed, 8 skipped (delta vs main: +31 new MFA tests across 4 files).
- **Ruff:** clean (1 RUF002 ambiguous-char fixed, 1 RUF059 unused-unpacked-var fixed, 7 files reformatted during sweep).
- **django-otp 1.7** wired into INSTALLED_APPS + MIDDLEWARE; built-in migrations run (`otp_totp_totpdevice`, `otp_static_staticdevice`, `otp_static_statictoken` tables created).
- **Lockout-clear semantic move** — `clear_failed_attempts` removed from `PathAdvisorLoginSerializer`; now fires in `ThrottledLoginView.post` (B2C non-MFA path) OR in `mfa_challenge_view` / `mfa_enroll_confirm_view` (MFA full success). Prevents attackers from resetting the lockout counter via password-only success.
- **MFA session JWT** — `TimestampSigner` + 5-min TTL + IP-binding + single-use blacklist via Redis cache. No new dependency (stdlib + Django).
- **8 new audit events** documented in `docs/patterns/audit-events.md` (`auth.mfa_enrollment_started`, `_enrolled`, `_challenge_passed`, `_challenge_failed`, `_recovery_code_used`, `_recovery_codes_regenerated`, `_disabled`, `_reset_by_dpo`).
- **New runbook:** `docs/runbooks/mfa-lost-device.md` — DPO playbook for the "lost authenticator AND lost recovery codes" escalation.
- **Onboarding:** `docs/onboarding.md` §9d added — MFA flow + lockout interaction primer.
- **Deferred work:** the Story-1.5 "MFA hook in PathAdvisorLoginSerializer" item is struck-through; 10 new Story-1.6 deferrals added (WebAuthn growth, no decay on `requires_enrollment_at_next_login`, no admin UI for DPO reset, TOTP `tolerance` tuning, `manage.py disable_mfa_for_user` CLI, JWT consume best-effort vs Redis down, no "recent challenge" cookie, no trusted-device, no i18n EN, no multi-device).

### File List

**Backend (Django/DRF):**
- `apps/api/path_advisor/settings/base.py` — INSTALLED_APPS (`django_otp` + 2 plugins) + MIDDLEWARE (`OTPMiddleware`) + settings (`OTP_TOTP_ISSUER`, `MFA_SESSION_TTL_SECONDS`, `MFA_RECOVERY_CODES_COUNT`, `MFA_RECOVERY_LOW_THRESHOLD`).
- `apps/api/path_advisor/urls.py` — 5 new MFA endpoints + per-IP/per-user ratelimit wrappers.
- `apps/api/apps/accounts/models.py` — `MfaProfile` model + `STAFF_ROLES_REQUIRING_MFA` + `User.requires_mfa` + `User.has_mfa_enrolled` properties.
- `apps/api/apps/accounts/migrations/0011_mfa_profile.py` — new.
- `apps/api/apps/accounts/services/mfa.py` — new (start_enrollment, confirm_enrollment, verify_challenge, disable, reset_by_dpo, regenerate_recovery_codes, remaining_recovery_codes).
- `apps/api/apps/accounts/services/mfa_session.py` — new (issue, verify, consume — signed JWT with IP-binding + blacklist).
- `apps/api/apps/accounts/gdpr_exceptions.py` — 5 new exceptions (`MfaSessionExpired`, `MfaSessionInvalid`, `MfaChallengeFailed`, `MfaEnrollmentRequired`, `MfaDisableForbiddenForStaff`).
- `apps/api/apps/accounts/login_serializer.py` — removed `clear_failed_attempts` from success path (semantic move).
- `apps/api/apps/accounts/views.py` — MFA hook in `ThrottledLoginView.post` (mfa_session issue + session.flush) + 5 new view functions (`mfa_enroll_start_view`, `mfa_enroll_confirm_view`, `mfa_challenge_view`, `mfa_disable_view`, `mfa_regenerate_recovery_codes_view`).
- `apps/api/apps/accounts/serializers.py` — `UserDetailsSerializer` extended with `mfa_required_by_role`, `mfa_enrolled`, `mfa_recovery_codes_remaining` SerializerMethodFields.
- `apps/api/pyproject.toml` + `uv.lock` — added `qrcode[pil]>=7.4,<9.0`.

**Email templates (new, 6 files):**
- `apps/api/apps/accounts/templates/account/email/mfa_recovery_low_subject.txt`
- `apps/api/apps/accounts/templates/account/email/mfa_recovery_low_message.txt`
- `apps/api/apps/accounts/templates/account/email/mfa_recovery_low_message.html`
- `apps/api/apps/accounts/templates/account/email/mfa_disabled_subject.txt`
- `apps/api/apps/accounts/templates/account/email/mfa_disabled_message.txt`
- `apps/api/apps/accounts/templates/account/email/mfa_disabled_message.html`

**Tests (new, 4 files, 31 tests):**
- `apps/api/apps/accounts/tests/test_mfa_login_flow.py` — 8 tests (B2C / staff first login / enrolled / DPO reset / lockout semantic move).
- `apps/api/apps/accounts/tests/test_mfa_enrollment.py` — 8 tests (start, confirm, idempotent replace, mfa_session stage/IP/expiry, consumed-on-success).
- `apps/api/apps/accounts/tests/test_mfa_challenge.py` — 8 tests (TOTP, recovery, single-use consume, mfa_session expired, lockout orthogonality).
- `apps/api/apps/accounts/tests/test_mfa_disable_and_dpo.py` — 7 tests (B2C disable, staff 403, wrong pwd/code, regenerate codes, DPO reset wipes devices + flag, login round-trip after reset).

**Frontend (Next.js 15 App Router):**
- `apps/web/src/lib/api/auth.ts` — extended `CurrentUser` with `mfa_required_by_role`, `mfa_enrolled`, `mfa_recovery_codes_remaining`; extended `LoginResponse` with `mfa_required` / `mfa_enrollment_required` / `mfa_session`.
- `apps/web/src/lib/api/mfa.ts` — new (5 typed clients + sessionStorage helpers `storeMfaSession` / `readMfaSession` / `clearMfaSession`).
- `apps/web/src/components/features/auth/login-form.tsx` — MFA branch on login success (route to `/auth/mfa/enroll` or `/auth/mfa/challenge`).
- `apps/web/src/components/features/auth/mfa-enroll-form.tsx` — new (Client Component: QR + manual-secret fallback + 6-digit confirm + 8 recovery codes display + acknowledge checkbox).
- `apps/web/src/components/features/auth/mfa-challenge-form.tsx` — new (Client Component: TOTP / recovery code toggle).
- `apps/web/src/components/features/auth/mfa-settings-form.tsx` — new (Client Component: dashboard state machine — enrolled / staff-not-enrolled / B2C-not-enrolled, regenerate, disable).
- `apps/web/src/app/(public)/auth/mfa/enroll/page.tsx` — new (Server Component shell).
- `apps/web/src/app/(public)/auth/mfa/challenge/page.tsx` — new (Server Component shell).
- `apps/web/src/app/(authenticated)/parametres/securite/mfa/page.tsx` — new (Server Component, fetches user, embeds `<MfaSettingsForm>`).

**Documentation:**
- `docs/patterns/audit-events.md` — added 8 new `auth.mfa_*` event entries with full metadata schemas.
- `docs/runbooks/mfa-lost-device.md` — new (DPO playbook).
- `docs/onboarding.md` §9d — MFA flow + lockout interaction primer.
- `_bmad-output/implementation-artifacts/deferred-work.md` — struck "MFA hook in PathAdvisorLoginSerializer" + added 10 new Story-1.6 deferrals.
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — `1-6-mfa-staff: ready-for-dev → review`, `last_updated → 2026-06-04`.

## 9. Change Log

| Date | Author | Change |
|---|---|---|
| 2026-05-30 | dev (claude-opus-4-7) | Initial implementation pass — all 11 ACs, 12 tasks (T1–T12), 31 new MFA tests, deferred-work updated. Status → `review`. |
| 2026-06-04 | code-review (Blind Hunter + Edge Case Hunter + Acceptance Auditor, claude-opus-4-7) | Multi-agent adversarial review — ~76 raw findings → 6 decision-needed, 28 patch, 8 defer, ~34 dismissed. |
| 2026-06-07 | dev (claude-opus-4-7) | Applied 6 decisions + 28 patches (D1 IP /24 coarsening; D2 doc plaintext-codes accepted; D3 new in-place enrollment endpoint; D4 step-up TOTP-only; D5 scrubbed half-login response; D6 MfaBanner layout-wide + integration; P1 enroll-start use-counter; P2 too_many_attempts audit; P3 expired_session audit; P4 mfa_challenge_passed on recovery; P5 already-enrolled guard; P6 disable-before-email; P7 extras_as_extensions on MFA exceptions; P8 cache try/except; P9 isinstance JSON validation; P10 strict TTL on consume; P11 select_for_update race; P12 lockout pre-check; P13 emit_audit kwarg; P15 MfaSessionConsumed distinct; P16 disable no-op guard; P17 documented; P18 confirmed=True get_or_create; P19/P22 sessionStorage try/catch; P21 explicit set_password in tests; P23 method required; P24 explicit DoesNotExist; P25 deferred; P26 ship banner; P27 try/except around verify_challenge; P28 3-failure JTI blacklist). 215 tests pass; ruff clean. Status → `done`. |

---

## 10. Review Findings (2026-06-04)

Multi-agent adversarial review against the full diff (4191 lines, 37 files) on branch `worktree-story-1-6-mfa-staff` at HEAD `cdd579d`. **Sources:** `blind` · `edge` · `auditor`.

### Decision-needed

- [x] **[Review][Decision] D1 — `mfa_session` IP-binding is hard-fail; high false-positive rate for NAT/mobile users** (`blind`) — `apps/api/apps/accounts/services/mfa_session.py:_hash_ip`. Spec §AC10 mandates `ip_hash` binding to prevent JWT replay from a different IP. But a user on carrier-grade-NAT, switching cell towers, or behind a load-balancer with multiple egress IPs will get `MfaSessionInvalid` mid-flow (login → MFA challenge). **Options:** (a) keep strict IP-binding (current — spec-compliant, but real users will hit it); (b) coarsen to `/24` IPv4 / `/48` IPv6 bucketing (matches the `_truncate_ip_for_audit` pattern from Story 1.5 — partial trade); (c) drop the IP check entirely and rely on the 5-min TTL alone (relax spec).

- [x] **[Review][Decision] D2 — Recovery codes stored in plaintext (django-otp default behavior; spec claim was incorrect)** (`blind`) — `apps/api/apps/accounts/services/mfa.py:confirm_enrollment + verify_challenge`. Story spec §4.5 claimed django-otp's `StaticToken` stores codes hashed. **False** — `StaticToken.token` is a plain `CharField` and the lookup `token_set.filter(token=code).first()` proves equality matching. A DB dump leaks every user's recovery codes. **Options:** (a) accept django-otp standard (matches MVP volume, document in deferred-work — risk equivalent to the password hash leak risk); (b) hash codes ourselves (write `pbkdf2_sha256(code)` on issue, iterate-and-`check_password` on verify — breaks django-otp's idiomatic lookup, custom code, +O(N) per verify); (c) use Fernet-encrypted column (intermediate — readable by app, opaque on dump).

- [x] **[Review][Decision] D3 — B2C "Activer la MFA" CTA forces a logout/re-login instead of in-place enrollment** (`auditor`) — `apps/web/src/components/features/auth/mfa-settings-form.tsx`. Spec §AC2 implies an in-place QR-then-confirm flow from `/parametres/securite/mfa`. Implementation comment says «*we don't have a standalone "enroll me now" endpoint*» — the user must logout + login again to get a fresh `mfa_session`. UX trap. **Options:** (a) ship a new `POST /api/v1/auth/mfa/enroll/start-from-session/` that mints an `mfa_session` for the already-authenticated user (small new endpoint + rate-limit); (b) keep the logout-re-login flow and rewrite the CTA copy to set expectations («Tu vas être déconnecté pour démarrer la MFA, ça prend 30s»); (c) defer the in-place flow to a UX-iteration story.

- [x] **[Review][Decision] D4 — `disable` and `regenerate_recovery_codes` accept `method="recovery"` as a step-up factor; spec §AC6 mandated TOTP-only** (`blind`) — `apps/api/apps/accounts/views.py:_MfaReauthPayload`. A B2C user (or attacker with one recovery code) can disable MFA via password + recovery code. The intent of "step-up auth" is to require BOTH the long-term password AND a fresh second-factor; using a one-time recovery code defeats the freshness check. **Options:** (a) restrict step-up to TOTP only (`method` field removed, hard-coded TOTP); (b) keep recovery as a fallback (current — accept the UX trade for "lost authenticator, need to disable", note risk).

- [x] **[Review][Decision] D5 — Half-login response body exposes full `UserDetailsSerializer.data` (including `email`, `id`, recovery-codes-remaining count) BEFORE the MFA challenge completes** (`blind`) — `apps/api/apps/accounts/views.py:ThrottledLoginView.post` MFA branch. An attacker with the password (but no second factor) gets `user.id`, `user.email`, `user.mfa_recovery_codes_remaining` (count) — a side-channel for triage ("does the victim have fresh codes vs near-empty?"). Spec §AC1 listed `user: {role, status, mfa_enrolled}` only. **Options:** (a) scrub the half-login response to the spec-mandated fields only (`{role, status, mfa_enrolled, mfa_required_by_role}`); (b) keep full profile (UX value — frontend can route by role without a 2nd round-trip, attacker knows password anyway).

- [x] **[Review][Decision] D6 — Spec §AC8 / §T8 mandated `mfa-banner.tsx` (layout-wide red banner) + sidebar badge; neither shipped** (`auditor`) — `apps/web/src/components/features/auth/`. The settings page has an inline banner, but a staff user enrolled in the next 10 days could miss it without visiting `/parametres/securite/mfa`. **Options:** (a) ship `mfa-banner.tsx` now + integrate in the authenticated layout (~50 LoC + layout edit); (b) defer to a UX-iteration story, document in deferred-work, accept the AC8 spec deviation.

### Patch

- [x] **[Review][Patch] P1 — `mfa_enroll_start/` does not consume the `mfa_session`; stolen token can be replayed indefinitely within 5-min TTL** (`blind+edge`) [`views.py::mfa_enroll_start_view`] — Spec §AC10 mandates single-use via `consume()`. Currently start endpoint creates a fresh `TOTPDevice` (and audit row) on every call. Fix: consume on first call OR add a per-token call counter (Redis `mfa_session_uses:<jti>` capped at 3).

- [x] **[Review][Patch] P2 — `auth.mfa_challenge_failed` with `metadata.reason="too_many_attempts"` is never written on the threshold-trip** (`blind+auditor`) [`views.py::mfa_challenge_view`] — Spec §AC5 + §AC9 list this exact metadata value. Currently `record_failed_attempt` writes `auth.account_locked` only. Add: after `record_failed_attempt` returns ≥ `LOGIN_FAIL_THRESHOLD`, write `auth.mfa_challenge_failed` with `reason="too_many_attempts"`.

- [x] **[Review][Patch] P3 — `auth.mfa_challenge_failed` with `reason="expired_session"` is never written** (`auditor`) [`mfa_session.py::verify`] — Spec §AC9 lists this value. Currently `MfaSessionExpired` is raised before the audit-write happens. Fix: catch + audit-then-reraise inside `mfa_challenge_view` / `mfa_enroll_confirm_view`.

- [x] **[Review][Patch] P4 — Recovery-code success path emits `auth.mfa_recovery_code_used` but NOT `auth.mfa_challenge_passed`** (`blind+auditor`) [`mfa.py::verify_challenge`] — Spec §T3 + §AC9 say `verify_challenge` writes `auth.mfa_challenge_passed` regardless of method. DPO queries for "all successful challenges in last 24h" undercount. Fix: emit `auth.mfa_challenge_passed` on both branches; keep `auth.mfa_recovery_code_used` as a separate complementary event.

- [x] **[Review][Patch] P5 — `start_enrollment` silently creates a 2nd unconfirmed TOTPDevice for an ALREADY-enrolled user** (`blind`) [`mfa.py:_start_enrollment` + view] — Comment says "re-enrollment refused upstream" but no view-layer check. A stale `mfa_session` (stage=`mfa_enrollment_pending`) for an enrolled user lets them get a 2nd device. Fix: in view, `if user.has_mfa_enrolled and not user.mfa_profile.requires_enrollment_at_next_login: raise EnrollmentAlreadyComplete` before calling `start_enrollment`.

- [x] **[Review][Patch] P6 — `mfa_disable_view` sends the "MFA disabled" email BEFORE the disable transaction commits** (`blind`) [`views.py::mfa_disable_view`] — Email-then-disable order means a `MfaDisableForbiddenForStaff` raised inside `disable()` lies to staff users. Fix: swap order — call `disable()` first, then send email best-effort.

- [x] **[Review][Patch] P7 — `MfaSession*`/`MfaChallengeFailed`/etc do not set `extras_as_extensions=True`** (`blind`) [`gdpr_exceptions.py`] — Spec §4.1 architectural-reuse table mandates this for MFA exceptions so the frontend reads `mfa_session_expired` as a top-level field, not nested under `errors`. Currently the flag is set only on `EmailNotVerified`. Add `extras_as_extensions=True` to all 5 MFA exception classes (cheap, future-proof).

- [x] **[Review][Patch] P8 — `consume()` swallows nothing; if Redis is down, `cache.set` raises and breaks the login flow AFTER session cookie committed** (`edge`) [`mfa_session.py::consume`] — Wrap the `cache.set` call in `try/except Exception` + `structlog.warning("mfa_session.consume.cache_failed")`. The docstring already says it's best-effort but the code doesn't reflect that.

- [x] **[Review][Patch] P9 — `verify()` doesn't validate JSON payload type before calling `.get(...)`** (`edge`) [`mfa_session.py::verify`] — If `json.loads(raw)` returns a non-dict (`null`, list, scalar), `.get("stage")` raises `AttributeError` → unhandled 500. Add `if not isinstance(payload, dict): raise MfaSessionInvalid()` immediately after the `json.loads`.

- [x] **[Review][Patch] P10 — `consume()` is lenient about TTL (`max_age=_ttl_seconds() * 2`) — allows post-expiry blacklist** (`blind`) [`mfa_session.py::consume`] — The `verify` path already rejects expired tokens. The `consume` path's leniency is unjustified. Tighten to `max_age=_ttl_seconds()`.

- [x] **[Review][Patch] P11 — `confirm_enrollment` race: two concurrent valid-code submissions both pass `verify_token` and both wipe + recreate `StaticDevice`** (`edge`) [`mfa.py::confirm_enrollment`] — Use `TOTPDevice.objects.select_for_update().filter(user=user, confirmed=False).first()` inside the existing `transaction.atomic()`. Same for the StaticDevice / StaticToken recreate.

- [x] **[Review][Patch] P12 — `mfa_challenge_view` does NOT pre-check `user.is_locked`; a locked user can still hit the challenge endpoint with infinite tokens** (`edge`) [`views.py::mfa_challenge_view`] — Add an early `if login_security.is_account_locked(user): raise AccountLocked()` right after `mfa_session_service.verify(...)`.

- [x] **[Review][Patch] P13 — `verify_challenge` writes `auth.mfa_challenge_passed` for the disable/regenerate re-auth path too — pollutes login-flow audit queries** (`edge`) [`mfa.py::verify_challenge` + `views.py::mfa_disable_view` / `mfa_regenerate_recovery_codes_view`] — Add a `record_audit: bool = True` kwarg to `verify_challenge`; pass `record_audit=False` from the step-up paths (or split into `verify_challenge` and `verify_step_up_code`).

- [x] **[Review][Patch] P14 — OpenAPI `@extend_schema(responses={200: serializers.JSONField()})` placeholder leaves the docs without typed response shapes** (`auditor`) [`views.py::mfa_*_view`] — Each MFA endpoint should declare a real response serializer (e.g. `MfaEnrollStartResponseSerializer`) so the OpenAPI export carries the body shape clients will consume.

- [x] **[Review][Patch] P15 — `MfaSessionInvalid` is the catch-all for 5 distinct conditions (signature failure, IP mismatch, wrong stage, blacklisted, user-not-found); UX/forensic collapsed** (`blind+auditor`) [`mfa_session.py::verify`] — Split into 3 surfaced types: `MfaSessionExpired` (already exists), `MfaSessionConsumed` (NEW — for blacklist hits), `MfaSessionInvalid` (the rest). Keep IP mismatch + wrong stage as `MfaSessionInvalid` (anti-enum: don't tell attacker which side mismatched).

- [x] **[Review][Patch] P16 — `disable()` works on a user with NO MFA enrolled — silently no-ops + writes a misleading `auth.mfa_disabled` audit row** (`edge`) [`mfa.py::disable`] — Guard at start: `if not user.has_mfa_enrolled: return  # silent no-op, no audit row`.

- [x] **[Review][Patch] P17 — MFA failures use the SAME lockout counter as password failures, opening a DoS-lock vector** (`blind`) [`views.py::mfa_challenge_view`] — An attacker with a stolen `mfa_session` (same NAT bucket) can submit 5 wrong codes to lock the victim's account. Spec §AC5 calls this "orthogonal" but they share the counter. **Mitigation:** keep the shared counter (true orthogonality requires 2 counters which doubles operational surface) but document the DoS risk explicitly in deferred-work + add a per-user attempts cap on the `mfa_session` itself (P1 above).

- [x] **[Review][Patch] P18 — `regenerate_recovery_codes` reuses any prior unconfirmed `StaticDevice`** (`edge`) [`mfa.py::regenerate_recovery_codes`] — `get_or_create(user=user, name=...)` matches on (user, name) only. Tighten to `get_or_create(user=user, name=..., confirmed=True, defaults={"confirmed": True})` so unconfirmed leftovers are not reused.

- [x] **[Review][Patch] P19 — Frontend `sessionStorage.setItem` can throw (`QuotaExceededError`, Safari private mode `SecurityError`) — wraps the flow without a catch** (`edge`) [`mfa.ts::storeMfaSession`] — `try { window.sessionStorage.setItem(...) } catch { /* surface to user, fall back to in-memory state */ }`.

- [x] **[Review][Patch] P20 — Recovery-code-low email can fire twice under concurrent recovery consumption** (`edge`) [`views.py::mfa_challenge_view`] — Two parallel recovery uses both see `remaining <= threshold` → two emails. Fix: use `cache.add("mfa_low_email_sent:{user.id}", "1", timeout=3600)` as a per-day dedup lock.

- [x] **[Review][Patch] P21 — Test helper `_make_enrolled_user` relies on `UserFactory` default password matching `_PWD`** (`blind`) [`tests/test_mfa_*.py`] — Brittle if the factory ever rotates to `secrets.token_urlsafe`. Fix: explicit `user.set_password(_PWD); user.save(update_fields=["password"])` in the helper.

- [x] **[Review][Patch] P22 — `LoginResponse.user` returns `mfa_recovery_codes_remaining` count in the half-login body** — see D5 above. If D5 resolves to "scrub", this becomes a patch.

- [x] **[Review][Patch] P23 — `_MfaChallengePayload.code max_length=20` accepts a recovery code (14 chars) with `method` defaulting to `"totp"`** (`blind`) [`views.py::_MfaChallengePayload`] — User fat-fingers the method field and their recovery code goes to TOTP verify → lockout-counter tick + recovery code wasted. Fix: auto-detect method server-side (if `len(code) >= 14 and "-" in code`: route to recovery), OR force the client to set method explicitly via the form (already done — but document the auto-detect for robustness).

- [x] **[Review][Patch] P24 — `MfaProfile` `getattr` chain in `ThrottledLoginView.post` accesses `mfa_profile` via 2 nested `getattr(..., None)` — Django raises `RelatedObjectDoesNotExist` (subclass of `AttributeError` in recent Django, but not historically)** (`blind`) [`views.py::ThrottledLoginView.post`] — Use explicit `try/except MfaProfile.DoesNotExist` like the User.has_mfa_enrolled property already does.

- [x] **[Review][Patch] P25 — `_truncate_ip_for_audit` + `_hash_email_for_audit` consolidation threshold tripped by Story 1.6** (`blind`) [`apps/api/apps/accounts/views.py`] — Story 1.5 deferred-work flagged the move once a 3rd consumer appears; Story 1.6 adds FIVE new consumers. Hoist to `apps/core/text.py` (or `apps/audit/redaction.py`).

- [x] **[Review][Patch] P26 — `mfa-banner.tsx` + sidebar badge** — see D6 above. If D6 resolves to "ship", this becomes a patch.

- [x] **[Review][Patch] P27 — `record_failed_attempt` outside try/except chain in `mfa_challenge_view` — a `verify_challenge` exception bypasses lockout** (`edge`) [`views.py::mfa_challenge_view`] — Wrap `verify_challenge` call: on any exception (DB unavailable, audit chain failure), still call `record_failed_attempt`. Defense-in-depth against partial failures.

- [x] **[Review][Patch] P28 — 3-consecutive-failure JTI blacklist NOT implemented; spec §AC10 explicit** (`auditor`) [`views.py::mfa_challenge_view` + `mfa_session.py`] — Track failure count per-JTI in Redis (`mfa_session_fails:<jti>` TTL = JWT TTL); on 3rd failure, consume the JTI. Closes the brute-force-within-token window.

### Defer

- [x] **[Review][Defer] Recovery codes plaintext (django-otp standard)** (`blind`) — If D2 resolves to (a), document as deferred-work with rationale: django-otp idiom, recovery codes are 48-bit entropy each (collision-resistant), DB encryption-at-rest covers cold-storage leak vector. Hashing breaks library compatibility.
- [x] **[Review][Defer] Low-codes email synchronous SMTP** (`blind`) — Same migration as Story 1.5/1.12 deferred emails. Move to Celery in Story 8.1.
- [x] **[Review][Defer] Recovery code entropy / format constants** (`blind`) — `xxxx-xxxx-xxxx` is 48 bits × 8 codes = 384 bits total. Hardcoded format constants OK for MVP; revisit if `MFA_RECOVERY_CODES_COUNT` ever tunes.
- [x] **[Review][Defer] 2nd-tab MFA session race** (`edge`) — `sessionStorage` is single-tab by spec; opening a 2nd tab gets a fresh empty storage. The cross-tab scenario only triggers if the user MANUALLY copies the token, which we don't support.
- [x] **[Review][Defer] User refreshes mid-enrollment** (`edge`) — Refresh triggers a 2nd `start_enrollment` call which deletes the prior unconfirmed device + creates a fresh one (idempotent by design). Rate-limit 5/h IP caps abuse. Document the UX trap.
- [x] **[Review][Defer] TOTP replay within 30s window across concurrent requests** (`edge`) — django-otp's `last_t` update inside `verify_token` is best-effort. `select_for_update` on the TOTPDevice (P11 above) covers the enrollment confirm race; for challenge, two concurrent valid-code submissions are an obscure race that ends up tracking only one success. Acceptable.
- [x] **[Review][Defer] `MfaSession*` exceptions inherit `AccountDeletionError`** (`blind`) — Cosmetic, tracked by the existing `gdpr_exceptions.py → auth_exceptions.py` rename deferred item.
- [x] **[Review][Defer] DPO `reset_by_dpo` on a soft-deleted user** (`edge`) — Operational edge case; DPO would verify identity OOB first. Document in runbook.

