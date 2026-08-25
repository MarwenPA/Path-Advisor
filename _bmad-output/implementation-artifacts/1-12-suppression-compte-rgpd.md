# Story 1.12: Account deletion — GDPR right to erasure (Article 17)

**Epic:** 1 — Foundation: Multi-role Auth, RBAC, GDPR Compliance & Technical Infrastructure
**Status:** done
**Sprint:** 1 (Foundations)
**Story Key:** `1-12-suppression-compte-rgpd`
**Estimation:** M–L (medium–large) — adds a new `AccountDeletionRequest` model + a two-phase pipeline (immediate soft-delete on click → 30-day grace window → Celery-beat hard-delete cascade), two new API endpoints (`POST /me/account-deletion/`, `POST /account-deletion/<token>/cancel/`), three transactional email templates, a Django-admin cancel action for DPO support, and a public cancel-landing page on the front. The hard-delete step purges S3 prefixes across every bucket the user owns data in (`gdpr-exports/<user_id>/`, future `bulletins-encrypted/<user_id>/`), then runs `User.delete()` so PostgreSQL `ON DELETE CASCADE` wipes every dependent row in one transaction. The non-trivial part is *not* the deletion itself — it's the **invariants around the 30-day grace window** (concurrent re-signup with the same email, in-flight GDPR exports, parental-consent rows still pending, Django sessions that must die immediately) and the **idempotent hard-delete sweep** (re-running the task must not double-audit or 500 on already-deleted rows).

> Story 1.12 implements **FR11** (droit à l'oubli RGPD, Article 17) and the deletion half of **NFR-S6** (réponse < 30 jours). The audit log infra (Story 1.13), `ConsentDialog` component (Story 1.14), parental-consent cascade (Story 1.4), and the `deleted_at` column already on `User` (Story 1.3 placeholder marked `# soft delete (Story 1.12)`) are all already in place — this story *uses* them; it does not re-architect. The deliberate design decision is to **anonymize-by-cascade-and-time**: the User row + every FK-dependent row are hard-deleted at day 30, while the immutable audit log keeps the user's ULID as `actor_id`/`subject_id` (a CharField, not a FK), pseudonymized de facto because the originating User row is gone. CNIL Article 17(3)(b) explicitly allows this — audit retention serves a legal obligation and the de-identified ULIDs no longer expose PII.

---

## 1. User Story

**As a** user (student, parent, counselor, school admin),
**I want** to request the complete deletion of my account and all my personal data, with a 30-day grace window during which I can change my mind,
**So that** I can exercise my GDPR Article 17 right to erasure — knowing the platform will actually wipe my data within the legal 30-day deadline, while still having a safety net against an angry-2-AM click I'll regret tomorrow.

**Business value:** legal must-have, twin of Story 1.11. A CNIL inspection finding "no functional right-to-erasure" carries the same baseline €20k fine + remediation order. Beyond compliance, the 30-day grace window is the *product* angle — it's the difference between a deletion flow users actually feel safe using vs. one they avoid (and then complain about on Twitter). The deletion pipeline is also the **load-bearing test of every cascade FK in the schema**: every future feature that adds a personal-data table must be reachable from `User.delete()` or be explicitly handled in this story's purge service. That makes 1.12 the *integrity audit* of the data model.

---

## 2. Acceptance Criteria (BDD)

### AC1 — User requests deletion from Settings → "Supprimer mon compte"

**Given** I am authenticated and on `/parametres/mes-donnees` (the same page Story 1.11 ships, with a new "Zone dangereuse" section underneath the export controls)
**When** I click "Supprimer définitivement mon compte"
**Then** a `<ConsentDialog>` (Story 1.14) opens with:
- `title: "Supprimer définitivement ton compte"`
- `description: "Cette action est irréversible passé 30 jours."`
- `dataMentioned: ["Profil et bulletins", "Recommandations et parcours sauvegardés", "Historique d'envois école", "Sessions et préférences"]`
- `duration: "Fenêtre de rétractation : 30 jours"`
- `beneficiary: "Toi (droit à l'oubli RGPD)"`
- `acceptLabel: "Supprimer mon compte"`
- `refuseLabel: "Annuler"`
- `isAcceptDestructive: true` (red accept button per Story 1.14 §AC3)

**And** the dialog includes a **password input below the description** (inline, not a separate step) — empty by default; the accept button stays disabled until the field is non-empty (client-side gate; server is the authority).

**And** when I type my password and click "Supprimer mon compte", the API call `POST /api/v1/me/account-deletion/` is made with body `{"password": "..."}`.

**And** if the password is wrong, the API returns `400 Bad Request` with Problem Details `type=https://path-advisor.fr/errors/invalid-password`, `title="Mot de passe incorrect"`. The dialog stays open, the password field clears, and a non-culpabilising message renders below it ("Vérifie ton mot de passe et réessaye."). **No rate-limit message** at the first failure — the rate-limit (see AC2) is silent until it actually fires.

**And** if the password is correct, the API returns `202 Accepted` with body:
```json
{
  "id": "adr_01HXJ...",
  "status": "pending_hard_delete",
  "requested_at": "2026-05-24T14:30:00Z",
  "hard_delete_after": "2026-06-23T14:30:00Z",
  "detail": "Ton compte est désactivé. Tu as 30 jours pour annuler via le lien envoyé par email avant suppression définitive."
}
```

**And** before responding the API performs (in one DB transaction):
1. `User.status = DELETED`, `User.is_active = False`, `User.deleted_at = now()`.
2. Insert `AccountDeletionRequest` row with `cancel_token = secrets.token_urlsafe(32)`, `hard_delete_after = now() + 30 days`, `requested_ip_hash`, `requested_user_agent`, `password_hash_at_request` (the SHA-256 of the password the user just confirmed — used by the cancel endpoint as a second factor).
3. Delete every Django session for this user (`Session.objects.filter(...)` matching the `_auth_user_id` payload — see §4.5 #3 for the implementation).
4. Audit log `gdpr.account_deletion_requested` (subject_id = user.id, actor_id = user.id, metadata = `{"deletion_request_id": "adr_...", "hard_delete_after": "..."}`).
5. Send the confirmation email (T5 below) with the cancel link.

**And** the front-end response handler immediately calls `signOut()` (clears the local CSRF + session cookies) and redirects to `/auth/account-deleted` — a static page explaining "Ton compte est désactivé. Vérifie tes emails — un lien d'annulation t'a été envoyé, valable 30 jours."

> **Why the password again, not just session re-auth?** The user is already authenticated; re-asking the password is a *deliberate friction* (NIST 800-63B SP "sensitive operation re-authentication"). It catches three classes of accident: (a) authenticated session abandoned on a shared device, (b) accidental click while the dialog was open in a background tab, (c) social-engineering attacker who got the session cookie but not the password. UX cost is 2 seconds; compliance cost of skipping it is "user destroyed their account by misclick" — a real CNIL complaint pattern.

### AC2 — Rate-limit + already-pending guards

**Given** I already have an `AccountDeletionRequest` with `cancelled_at IS NULL AND hard_deleted_at IS NULL` (i.e., a deletion is in-flight)
**When** I `POST /api/v1/me/account-deletion/` again
**Then** the API rejects with `409 Conflict` + Problem Details `type=https://path-advisor.fr/errors/account-deletion-already-pending`, `title="Une demande de suppression est déjà en cours"`, `detail` mentioning the `hard_delete_after` timestamp and a hint about the cancel link in the email.

> Practically this can only happen if the front-end is buggy (the moment we soft-delete the user, their session is killed and they can't reach the endpoint). But the race exists if a Celery task on another process is mid-flight, or if a curl-based attacker has a still-valid CSRF token from before the soft-delete. The check is cheap and the 409 surfaces the bug.

**Given** the rate-limit `account_deletion_request = '3/24h'` (per IP, not per user — by definition the user is gone after the first successful call)
**When** an IP exceeds 3 requests in 24h
**Then** the API rejects with `429 Too Many Requests` + Problem Details, `Retry-After` header set to the remaining cooldown. The throttle uses the `apps/accounts/views.py` django-ratelimit pattern (`key="ip"`) and emits the standard `RateLimited` Problem Details.

> Why 3/24h and not 1/24h: legitimate users may bounce between password attempts (2 wrong + 1 correct = 3 calls). Bumping to 3 spares the support inbox without meaningfully helping an attacker — they'd still need the password.

### AC3 — Soft-delete is immediate; the user can no longer authenticate

**Given** the soft-delete step in AC1 has committed
**When** the same user (or anyone with their old credentials) tries to log in via `POST /api/v1/auth/login/`
**Then** the login endpoint returns `403 Forbidden` + Problem Details `type=https://path-advisor.fr/errors/account-deleted`, `title="Compte supprimé"`, `detail` mentioning that a cancel window is open ("Si tu n'as pas demandé cette suppression, vérifie tes emails pour annuler dans les 30 jours.") and *not* leaking whether the email exists pre-deletion (the response shape is identical to "compte inexistant").

**And** an attempt to use an old session cookie (if any survived the cleanup in AC1 step 3) returns 401 — `User.is_active = False` makes `request.user` resolve to `AnonymousUser` via the standard Django auth backend.

**And** an attempt to re-register the same email via `POST /api/v1/auth/registration/` returns `409 Conflict` + the same `EmailAlreadyRegistered` Problem Details Story 1.3 already ships. The pre-existing User row blocks the unique constraint until the hard-delete sweep fires.

> An alternative design would let the deleted user re-register their email immediately (mass-rename the deleted row to `deleted+<ulid>@deleted.local` at soft-delete time). We *don't* do that in MVP because (a) the user can simply cancel and the email stays valid, (b) post-hard-delete the unique constraint releases naturally, and (c) cross-tenant trust impact is nil at 0 users. Document as deferred-work.

### AC4 — User receives the confirmation email with cancel link

**Given** the soft-delete API call succeeds
**When** the email is sent (synchronously inside the `POST` request — the user must see it land or perceive a failure they can react to; same pattern as Story 1.3 verification)
**Then** the email contains:
- A subject `"[Path-Advisor] Demande de suppression de compte reçue — tu as 30 jours pour annuler"`.
- A French-only body explaining: the soft-delete happened, the data will be permanently wiped on `<hard_delete_after>`, and a single **cancel button** linking to `https://path-advisor.fr/auth/cancel-deletion/<cancel_token>` (no querystrings — the token is the path arg, matching the parental-consent landing pattern).
- A separate "Tu n'as pas demandé cette suppression ?" paragraph with the same link reframed as a security-incident escape hatch.
- Sender = `DEFAULT_FROM_EMAIL`; voice = "complice non-culpabilisante" per UX-DR26 (mirror Story 1.3's tone, not legalese).

**And** the email send goes through the same Django email infrastructure already used by parental-consent / signup verification — `send_mail` with `fail_silently=False`. If SMTP raises, the whole POST raises `503 Service Unavailable`, the DB transaction rolls back, and the user sees the dialog with an inline error "Une erreur empêche la suppression — réessaye dans quelques minutes." The deletion **did not happen** (transaction atomicity is the invariant).

**And** the audit log entry `gdpr.account_deletion_requested` is part of the same transaction so it also rolls back on SMTP failure — keeps the audit log honest.

### AC5 — Cancel flow: 30-day window, public landing page, password re-auth

**Given** I click the cancel link in the email and land on `/auth/cancel-deletion/<token>`
**When** the page mounts
**Then** the front fetches `GET /api/v1/account-deletion/<token>/` (public endpoint, no auth) which returns the request's display state:
```json
{
  "status": "pending_hard_delete",
  "requested_at": "2026-05-24T14:30:00Z",
  "hard_delete_after": "2026-06-23T14:30:00Z",
  "user_email_masked": "ma***@d***.com"
}
```

**And** the page shows the masked email + the deadline + a password input + a "Annuler la suppression" button.

**Given** I enter my password and click "Annuler la suppression"
**When** the front calls `POST /api/v1/account-deletion/<token>/cancel/` with body `{"password": "..."}`
**Then** the backend:
1. Looks up the row by `cancel_token` (constant-time comparison via `secrets.compare_digest` — see §4.5 #5).
2. Returns 404 (not 403, anti-enumeration) if the token is unknown.
3. Returns `409 Conflict` + `type=…/errors/account-deletion-already-resolved` if `cancelled_at IS NOT NULL OR hard_deleted_at IS NOT NULL`.
4. Returns `410 Gone` + `type=…/errors/account-deletion-expired` if `hard_delete_after < now()` (the sweep may not have fired yet but the legal window is closed).
5. Verifies the password against the User's hash via `user.check_password(payload['password'])` — returns 400 + `invalid-password` on mismatch. **Does not** compare against the `password_hash_at_request` column — that field is for forensic continuity only (see §4.5 #4), not as the authoritative check (the user may have changed it via support during the grace window).
6. On success: `User.status = ACTIVE`, `User.is_active = True`, `User.deleted_at = NULL`; `AccountDeletionRequest.cancelled_at = now()`, `cancel_reason = "user_self_service"`. All in one transaction.
7. Audit log `gdpr.account_deletion_cancelled` (actor + subject = user.id, metadata = `{"deletion_request_id": "...", "via": "user_self_service"}`).
8. Sends a "Compte restauré" confirmation email (template T5).
9. Returns `200 OK` with `{"detail": "Ton compte est restauré. Tu peux te reconnecter."}` and the front redirects to `/auth/login` with a flash banner.

**Given** rate-limit on the cancel endpoint
**When** an IP exceeds `5/h` (allowing for normal typo-then-retry behavior without inviting a token-bruteforce sweeper)
**Then** the API returns 429 with the standard Problem Details.

> The double rate-limit (per-IP on the cancel endpoint AND per-token via the unique 256-bit token entropy) gives us a layered defense against the only realistic attack — a leaked cancel link that someone tries to brute-force. 256 bits of token entropy makes brute-force economically infeasible; the IP cap stops the noise from cluttering logs.

### AC6 — Hard-delete sweep: Celery beat job, cascade everything

**Given** the Celery beat job `accounts.sweep_account_deletions` runs daily at `03:45 Paris` (15 minutes after Story 1.13's `audit.archive_old_logs` slot — keeps the sequence deterministic for incident debugging)
**When** it executes
**Then** for every `AccountDeletionRequest` with `cancelled_at IS NULL AND hard_deleted_at IS NULL AND hard_delete_after <= now()`:

1. **Re-fetch the User row inside the task transaction** — defense against a `cancelled_at` write that landed between the queue selection and the per-row execution.
2. **Purge S3 prefixes** the user owns data in. MVP buckets:
   - `gdpr-exports/<user_id>/*` (Story 1.11 archives — including expired ones still on S3 if the sweep there hasn't run).
   - Future: `bulletins-encrypted/<user_id>/*` (when Story 2.3 ships) — defensive `if bucket exists: list+delete`, no-op otherwise.
   - Implementation: `s3.list_objects_v2(Bucket=..., Prefix=f"<...>/{user.id}/")` paginated; collect keys; `s3.delete_objects` in batches of 1000. Log a structlog record per bucket with `(prefix, key_count_deleted)`.
3. **Write the final audit row** `gdpr.account_hard_deleted` (subject_id = user.id, actor_id = `None` with `actor_role="system"`, metadata = `{"deletion_request_id": "...", "s3_keys_deleted": <int>, "buckets": [...]}`). **This must happen BEFORE `User.delete()`** — once the User is gone, the audit row is still valid (the columns are CharField, not FK), but writing the row first preserves a stronger invariant: the audit log can never claim a deletion that didn't complete.
4. **Run `user.delete()`**. PostgreSQL `ON DELETE CASCADE` wipes:
   - `parental_consents` (FK `student` on User, `CASCADE` per Story 1.4 model).
   - `gdpr_export_requests` (FK `user` on User, defined `CASCADE` in Story 1.11 — verify in the migration; if Story 1.11 used `PROTECT`, T1.4 of this story flips it to `CASCADE`).
   - Future tables (Story 2.3 bulletins, Epic 3 recommendations, …): each future story is responsible for declaring `on_delete=models.CASCADE` on their FK to User. **This story adds a CI check** (`make assert-cascade-on-user` — see T9) to fail any future migration that breaks this contract.
   - Django sessions referencing this user's `_auth_user_id`: not FK-linked (Django stores user-id in a session payload column); the sweep MUST explicitly `Session.objects.filter(...).delete()` for any session referencing the deleted user before the User row goes. The soft-delete step already did this; this is belt-and-braces.
5. **Mark the request row** `hard_deleted_at = now()`. Note: the `AccountDeletionRequest` row stays — it's part of the audit story (a 3-year retention record of "we did delete this person on this date"). The `user` FK on `AccountDeletionRequest` MUST be `on_delete=SET_NULL` so the request survives the User cascade.

**And** the sweep is idempotent: a second beat fire on the same day picks up zero rows (because `hard_deleted_at` is now non-null). Wrapping the body in `with transaction.atomic(): select_for_update()` prevents a race between two workers (e.g., manual re-trigger via Django admin while beat fires).

**And** if any single step (S3 purge, audit write, `user.delete()`) raises:
- The transaction rolls back.
- The audit row gets a separate `gdpr.account_hard_delete_failed` entry written *outside* the rolled-back transaction (matches the Story 1.11 `_mark_failed` pattern in [apps/accounts/tasks.py:444-488](apps/api/apps/accounts/tasks.py)).
- The request row stays untouched (`hard_deleted_at = NULL`) so the next sweep retries.
- Sentry capture happens at the boundary.
- **CRITICAL:** the cap on retries is `max_attempts = 7` (one per day for a week) before a hard-stop that requires DPO intervention. After 7 failures the row stays pending; an admin action surfaces it. Without the cap, a permanently broken bucket would spam the audit log daily forever.

### AC7 — Audit pseudonymization survives the cascade

**Given** Story 1.13 ships the immutable audit log with `actor_id` / `subject_id` as `CharField(32)` (not FK) and the SHA-256 hash chain
**When** the hard-delete has run on user `usr_01HXJ...`
**Then** every historical `AuditLog` row referencing that ULID still exists, still passes the hash-chain integrity check, still surfaces in DPO exports, and still answers a CNIL inspection question of the form "did user X access data Y on date Z?".
**But** the originating `User` row is gone — there is no way (within Path-Advisor) to map `usr_01HXJ...` back to an email or person. The data subject is *de-identified* in the GDPR sense.

> **The 3-year retention obligation** (NFR-S4) is what justifies *keeping* the audit log post-deletion: it serves a legal obligation (Code de procédure pénale art. 8 for misuse-of-data complaints; CNIL guidance §5.4 on audit retention). CNIL Article 17(3)(b) explicitly carves out this case: "the right to erasure shall not apply where processing is necessary for compliance with a legal obligation". The audit retention IS that obligation.

**And** a regression test in `apps/audit/tests/test_chain_after_user_deletion.py` (NEW) creates a user, generates 10 audit rows referencing them, hard-deletes the user, then runs `verify_chain_integrity` — the chain must verify (no broken hashes) and the rows must still be queryable by their ULID.

### AC8 — Concurrent re-signup with the same email is blocked during the grace window

**Given** user `alice@example.com` has soft-deleted their account (`User` row still exists, `status=DELETED`, unique constraint on `email` still active)
**When** a different person tries to `POST /api/v1/auth/registration/` with `alice@example.com`
**Then** the existing `SignupSerializer.validate` already-existing-email check fires and returns the same generic `EmailAlreadyRegistered` Problem Details Story 1.3 ships. No leak that the original Alice has actually deleted.

**Given** Alice's hard-delete has fired (User row is gone)
**When** someone re-registers with `alice@example.com`
**Then** it succeeds — there is no DB row holding the email. The new account is a clean slate with no historical link to the old one (audit log keeps the old ULID; the new account gets a fresh ULID).

**And** the `accounts_factory.py` test factories grow a `DeletedUserFactory` (post-hard-delete state simulator) for the regression suite.

### AC9 — DPO support cancel path (Django admin)

**Given** a user contacts support claiming they couldn't find the cancel email
**When** a DPO opens Django admin → AccountDeletionRequest → row → "Cancel deletion (DPO override)" action
**Then** the action requires:
1. The DPO must be in the `path_admin` role (Django admin `is_superuser=True` is *not* sufficient; check via a custom admin permission `accounts.cancel_deletion_request`).
2. A confirmation page asks for a free-form `cancel_reason` (e.g., "user contacted support 2026-05-30, email bounced — verified identity via callback").

**And** on submit, the row gets:
- `cancelled_at = now()`
- `cancel_reason = "dpo_override:<dpo_user_id>:<free_form>"` — the prefix lets DPO audits filter for these vs. self-service cancels.
- User restored to `ACTIVE` (same as AC5 step 6).
- Audit log `gdpr.account_deletion_cancelled` with `actor_id = <dpo_user_id>`, `actor_role = "path_admin"`, `subject_id = <user_id>`, metadata containing the free-form reason.
- Restoration email sent to the user as in AC5.

**And** the action surface in admin is **gated by a confirmation modal** ("Are you sure? This will write an audit row with your DPO id. Cancel reason: …") — no accidental click-through.

### AC10 — Frontend: settings page section + public cancel landing + post-deletion banner

**Given** the settings page `/parametres/mes-donnees` (shipped by Story 1.11)
**When** I scroll past the export section
**Then** a clearly-delimited "Zone dangereuse" section appears with a single `<DeleteAccountSection />` Client Component:
- Heading "Supprimer mon compte" in `text-h2`, color `text-foreground`.
- Body paragraph explaining the 30-day grace and the immutable audit retention.
- A single button "Supprimer définitivement mon compte" — `variant="destructive"`, `size="default"`.
- The button is **disabled** with a tooltip "Demande déjà en cours" if a TanStack-Query-fetched `GET /api/v1/me/account-deletion/` (the next-most-recent request, if any) returns a row with status `pending_hard_delete`. The tooltip surfaces the `hard_delete_after` timestamp.
- The button opens the `<ConsentDialog>` from AC1.

**Given** the public cancel landing `/auth/cancel-deletion/<token>`
**When** the page loads
**Then** it's a Server Component that statically renders a minimal layout (no auth gate, no shell — the user is logged out by design), Server-fetches `GET /api/v1/account-deletion/<token>/` for the masked-email + deadline display, then mounts a small Client Component for the password form. Same look-and-feel as the parental-consent landing in Story 1.4.

**Given** the post-soft-delete redirect target `/auth/account-deleted`
**When** the user lands there
**Then** it's a static informational page (Server Component) explaining "Ton compte est désactivé. Vérifie tes emails. Tu as 30 jours pour annuler." No CTA other than a "Retour à l'accueil" link.

### AC11 — Observability + structlog signals

**Given** the existing structlog wiring (Story 1.3 + 1.13)
**When** any of the AC1/AC5/AC6/AC9 paths execute
**Then** the following structured log events are emitted (with `correlation_id` from `request_context`):
- `accounts.deletion_requested` (info, with `user_id`, `request_id`, `hard_delete_after`).
- `accounts.deletion_cancelled` (info, with `user_id`, `request_id`, `via=user|dpo`).
- `accounts.hard_delete_started` / `accounts.hard_delete_completed` / `accounts.hard_delete_failed` (info/error, with `user_id`, `request_id`, `s3_keys_deleted`, `cascade_row_counts`, `attempt`).
- `accounts.sweep_started` / `accounts.sweep_completed` (info, with `processed_count`, `failed_count`).

**And** the `cascade_row_counts` payload comes from Django's deletion collector (`_collector.fast_deletes` + `_collector.field_updates`) — captured *before* `delete()` runs so we know what we are about to wipe. This is the single most important debug artifact when a user complains about "data I didn't expect to vanish": it tells the DPO exactly which row counts were destroyed.

---

## 3. Tasks / Subtasks

- [x] **T1 — Schema & migration: `AccountDeletionRequest`** (AC1, AC5, AC6)
  - [ ] [apps/api/apps/accounts/models.py](apps/api/apps/accounts/models.py) — add `AccountDeletionRequest` (mirror the shape of `ParentalConsent` for token + audit fields, mirror `GdprExportRequest` for status-driven lifecycle):
    - `id` (ulid `adr_`)
    - `user` (FK to `User`, **`on_delete=models.SET_NULL`** so the row survives the hard-delete cascade — see AC6.5)
    - `user_id_snapshot` (CharField(32), denormalised at create time so post-cascade rows still know who the request belonged to — `user_id` becomes NULL post-cascade)
    - `cancel_token` (CharField(64), unique, db_index) — `secrets.token_urlsafe(32)` ≈ 43 base64 chars
    - `requested_at` (DateTimeField, default=now)
    - `hard_delete_after` (DateTimeField — denormalised `requested_at + GDPR_ACCOUNT_DELETION_GRACE_DAYS days`)
    - `cancelled_at` (DateTimeField, nullable)
    - `cancel_reason` (CharField(200), nullable — free-form prefixed `user_self_service:` / `dpo_override:<dpo_id>:` / `system:`)
    - `hard_deleted_at` (DateTimeField, nullable)
    - `hard_delete_attempt_count` (PositiveSmallIntegerField, default=0 — the cap-of-7 guard)
    - `requested_ip_truncated` (CharField(45), nullable — same shape as `ParentalConsent.decision_ip_truncated`)
    - `requested_user_agent` (CharField(200), nullable)
    - `password_hash_at_request` (CharField(128) — `make_password(submitted_password)` for forensic continuity; **NOT** the auth check at cancel time, see §4.5 #4)
    - `created_at` / `updated_at` (auto)
    - **Indexed:** `(hard_delete_after, cancelled_at, hard_deleted_at)` (the sweep-scan index — partial would be ideal but SQLite-portable means full index), `(cancel_token)` (the unique constraint already gives this), `(user)` (for the "is there a pending deletion for this user" query in AC2).
  - [ ] Migration `apps/api/apps/accounts/migrations/0005_account_deletion_request.py` (Django-generated, manually reviewed for index correctness).
  - [ ] **Verify Story 1.11's `GdprExportRequest` FK uses `on_delete=models.CASCADE`** — if not (the worktree at [apps/api/apps/accounts/tasks.py](apps/api/apps/accounts/tasks.py) shows the model exists in `apps.accounts.models`), include a one-line migration in this story to flip it. The hard-delete cascade depends on it; document in the PR description.
  - [ ] Verify `ParentalConsent.student` is `on_delete=models.CASCADE` — already confirmed in [apps/api/apps/accounts/models.py:139](apps/api/apps/accounts/models.py), so no schema change. Document this contract in the migration's docstring.
  - [ ] Settings keys to add in [apps/api/path_advisor/settings/base.py](apps/api/path_advisor/settings/base.py):
    - `GDPR_ACCOUNT_DELETION_GRACE_DAYS = 30` (overridable in tests).
    - `GDPR_ACCOUNT_DELETION_MAX_HARD_DELETE_ATTEMPTS = 7`.

- [x] **T2 — Service layer: `account_deletion_service.py`** (AC1, AC3, AC5, AC6)
  - [ ] `apps/api/apps/accounts/services/account_deletion_service.py` (NEW) — single module hosting the three operations:
    - `request_deletion(user, password, *, ip_truncated, user_agent) -> AccountDeletionRequest` — validates the password via `user.check_password()`; raises `InvalidPassword` (400) on mismatch; raises `AccountDeletionAlreadyPending` (409) if a pending row exists. Atomic transaction. Wipes Django sessions inside the same transaction. Sends the confirmation email *synchronously* (see AC4 rationale). Decorated `@audit_action("gdpr.account_deletion_requested", subject_from=lambda kwargs, ret: ret.user_id_snapshot)`.
    - `cancel_deletion(request, password, *, actor, cancel_reason) -> AccountDeletionRequest` — looks up by `cancel_token` (constant-time via `secrets.compare_digest`); validates state transitions (already-cancelled → 409, already-hard-deleted → 409, expired-window → 410, password mismatch → 400). Restores the user. Audit-decorated `gdpr.account_deletion_cancelled`. Sends restoration email.
    - `hard_delete(request) -> dict[str, int]` — the actual cascade. Returns counts for structlog / audit. Pre-cascade: captures `Collector.fast_deletes` / `field_updates` for observability. Writes the `gdpr.account_hard_deleted` audit row *first*, then runs S3 purge, then `user.delete()`, all inside `transaction.atomic()`. Sets `hard_deleted_at`. On any exception → re-raise (the task wrapper handles retry + failure audit).
  - [ ] `_purge_s3_prefixes(user_id) -> int` helper — lists + bulk-deletes for `gdpr-exports/{user_id}/` (and any future bucket registered in `settings.GDPR_USER_OWNED_S3_PREFIXES`). Pattern lifted from [apps/api/apps/accounts/tasks.py::expire_old_exports](apps/api/apps/accounts/tasks.py); use the same `gdpr_s3_client` factory.
  - [ ] `_terminate_sessions(user) -> int` helper — `from django.contrib.sessions.models import Session; for s in Session.objects.iterator(chunk_size=200): if s.get_decoded().get('_auth_user_id') == str(user.pk): s.delete()`. Returns count for logging. This is O(N) over all sessions; acceptable in MVP (≤ 500 active sessions). Document as deferred-work for a session-store rework when N > 10k (cf. `redis-sessions` upgrade path).

- [x] **T3 — Celery task: `accounts.sweep_account_deletions`** (AC6)
  - [ ] `apps/api/apps/accounts/tasks.py` — add a new section "Story 1.12 — Account deletion pipeline" between the parental-consent and GDPR-export sections to keep the file's existing structure (which already concatenates Story 1.4 + Story 1.11 with `#==` separators — match the convention).
  - [ ] `@shared_task(name="accounts.sweep_account_deletions", soft_time_limit=600, time_limit=900)` — the hard time-limit prevents a runaway sweep on a huge backlog from blocking the worker pool. With grace=30d and typical churn, the daily batch is single-digit rows at MVP scale.
  - [ ] Body: materialise `AccountDeletionRequest.objects.filter(cancelled_at__isnull=True, hard_deleted_at__isnull=True, hard_delete_after__lte=now()).only("pk").values_list("pk", flat=True)` to an in-memory list (same pattern as `expire_old_exports`).
  - [ ] For each pk: re-fetch inside `transaction.atomic()` with `select_for_update()`. Call `account_deletion_service.hard_delete(request)`. On success → increment a counter. On exception → catch broadly, increment `hard_delete_attempt_count`, write `gdpr.account_hard_delete_failed` audit row outside the rolled-back transaction, log + Sentry. If `hard_delete_attempt_count >= GDPR_ACCOUNT_DELETION_MAX_HARD_DELETE_ATTEMPTS`, fire a second `gdpr.account_hard_delete_giving_up` audit row and skip the row in subsequent sweeps (the next condition becomes `… AND hard_delete_attempt_count < settings.GDPR_ACCOUNT_DELETION_MAX_HARD_DELETE_ATTEMPTS`).
  - [ ] Wire into Celery beat in [apps/api/path_advisor/celery.py](apps/api/path_advisor/celery.py) at `crontab(hour=2, minute=45)` UTC (= 03:45 Paris; matches the "audit-export at 03:15, audit-archive at 03:30, GDPR-export expire at 03:30, account-delete sweep at 03:45" cadence Story 1.13/1.11 established).

- [x] **T4 — Endpoints: 4 routes total** (AC1, AC5, AC2)
  - [ ] [apps/api/apps/accounts/views.py](apps/api/apps/accounts/views.py) — add 4 views, placed after the parental-consent section (mirror the file's existing "--- Story 1.X — name ---" comment-based sections):
    - `POST /api/v1/me/account-deletion/` (authenticated, IP-rate-limited 3/24h): body `{"password": str}`. Delegates to `account_deletion_service.request_deletion`. Returns 202 + serialised request.
    - `GET /api/v1/me/account-deletion/` (authenticated): returns the most recent in-flight request for this user, or 404 if none. Used by the front to disable the delete button when a pending row exists.
    - `GET /api/v1/account-deletion/<token>/` (public, no auth, IP-rate-limited 30/h): returns the public projection (masked email, timestamps, status). Token-not-found → 404.
    - `POST /api/v1/account-deletion/<token>/cancel/` (public, no auth, IP-rate-limited 5/h, per-token-rate-limited 5/h via `key=_ratelimit_key_by_deletion_token`): body `{"password": str}`. Delegates to `account_deletion_service.cancel_deletion`.
  - [ ] `_ratelimit_key_by_deletion_token` helper at the top of the file — copy-paste-adapt the existing `_ratelimit_key_by_consent_token` ([views.py:112-127](apps/api/apps/accounts/views.py)) — same defensive `resolver_match is None` guard.
  - [ ] OpenAPI annotations (`@extend_schema`) on every endpoint — keep the schema clean since these are part of the GDPR contract surface.
  - [ ] [apps/api/apps/accounts/urls.py](apps/api/apps/accounts/urls.py) — wire:
    ```python
    path("me/account-deletion/", views.account_deletion_request, name="account-deletion-request"),
    path("me/account-deletion/status/", views.account_deletion_status_authenticated, name="account-deletion-status-self"),
    path("account-deletion/<str:token>/", views.account_deletion_status_public, name="account-deletion-status-public"),
    path("account-deletion/<str:token>/cancel/", views.account_deletion_cancel, name="account-deletion-cancel"),
    ```
    Note the top-level `account-deletion/` mount for the public endpoints (vs `me/` for authenticated) — same separation as `parental-consent/` already uses.
  - [ ] New Problem Details types in [apps/api/apps/core/exceptions.py](apps/api/apps/core/exceptions.py):
    - `InvalidPassword` (400) — also useful elsewhere; place in the shared module.
    - `AccountDeletionAlreadyPending` (409).
    - `AccountDeletionAlreadyResolved` (409).
    - `AccountDeletionExpired` (410).
    - `AccountDeletionNotFound` (404).
  - [ ] Throw `AccountDeleted` (403) from the dj-rest-auth login adapter when `User.status == DELETED` — see `apps/accounts/adapters.py` and copy the `is_active=False` short-circuit pattern.

- [x] **T5 — Email templates** (AC4, AC5, AC9)
  - [ ] `apps/api/apps/accounts/templates/accounts/email/account_deletion_requested.{txt,html}` — voice: complice, non-culpabilising. Single clear CTA (cancel button). Mention the 30-day deadline as a date *and* a relative ("dans 30 jours, le 23 juin").
  - [ ] `apps/api/apps/accounts/templates/accounts/email/account_deletion_cancelled.{txt,html}` — short ack: "Ton compte est restauré. Tu peux te reconnecter."
  - [ ] `apps/api/apps/accounts/templates/accounts/email/account_deletion_completed.{txt,html}` — sent at the hard-delete moment (AC6 step 4 — note: this is the LAST email we ever send to this address). Voice: respectful, factual. "Toutes tes données personnelles ont été effacées. Si tu souhaites créer un nouveau compte, tu peux le faire à tout moment." **Caveat:** sending to a soon-to-be-deleted email may bounce if the user has already churned their inbox — log + Sentry but do not fail the sweep on SMTP error.
  - [ ] An `apps/api/apps/accounts/services/account_deletion_email.py` adapter — wraps `django.core.mail.send_mail` with the structured pattern (subject, template, context), mirrors `parental_consent_email.py` shape.
  - [ ] Tests assert: subject is fr-FR; the cancel-token URL is rendered correctly; **the password-from-the-request is never** in any of the 3 templates (regression test scans rendered content for the literal password — equivalent of Story 1.11 T7's "no password leak" pattern).

- [x] **T6 — Login adapter: reject DELETED users** (AC3)
  - [ ] `apps/api/apps/accounts/adapters.py` — the dj-rest-auth `RegisterSerializer.validate_email` already blocks the duplicate-email path during the grace window (the `User` row still exists). For login: the dj-rest-auth `LoginView` defers to Django's auth backend, which checks `is_active`. Since we set `is_active=False` in AC1, login fails *generically* — but the error message is the same "Invalid credentials" Django returns for unknown users, which leaks no information (good).
  - [ ] **However**, when the front sees `403 + status="DELETED"`, it should redirect to the cancel-flow info page. To enable that, override `LoginView.get_serializer().validate()` to look up the user by email (case-insensitive, like Story 1.4's `email__iexact`), and if `status == DELETED`, raise `AccountDeleted` (403). This is a TOCTOU-safe override since the user is already authenticated against the DB at that point.
  - [ ] Add a regression test: a soft-deleted user trying to log in receives 403 + Problem Details, not a generic 401.

- [x] **T7 — Django admin DPO cancel action** (AC9)
  - [ ] [apps/api/apps/accounts/admin.py](apps/api/apps/accounts/admin.py) — register `AccountDeletionRequest` with a `ModelAdmin` exposing list-filter on status (`pending` / `cancelled` / `hard_deleted`), search by user-email-or-id, and a custom admin action `cancel_deletion_dpo_override`.
  - [ ] The action triggers an admin-only intermediate page (`accounts/admin/cancel_deletion_confirm.html`) collecting `cancel_reason` via a TextField. On POST, delegates to `account_deletion_service.cancel_deletion(request, password=None, actor=admin_user, cancel_reason=f"dpo_override:{admin_user.id}:{reason}")` — the `password=None` overload is a service-layer pathway that **skips the password check** and is callable only from admin context (guarded by a `if actor is None or not actor.has_perm("accounts.cancel_deletion_request"): raise PermissionDenied` at the top of the function).
  - [ ] Permission `accounts.cancel_deletion_request` declared in the model `Meta.permissions` so superusers can grant it to DPO users without giving them blanket `is_superuser`.

- [x] **T8 — Frontend: settings section + public landing + post-delete page** (AC1, AC5, AC10)
  - [ ] [apps/web/src/app/(authenticated)/parametres/mes-donnees/page.tsx](apps/web/src/app/(authenticated)/parametres/mes-donnees/page.tsx) — append a `<DeleteAccountSection />` block below the GDPR-export section Story 1.11 ships.
  - [ ] `apps/web/src/components/features/account/delete-account-section.tsx` (NEW, Client Component) — composes `<ConsentDialog>` (Story 1.14, `isAcceptDestructive={true}`) with an additional password `<Input type="password">` placed *inside* the dialog body (between description and dataMentioned list). Uses TanStack Query hook `useAccountDeletion` for the POST. Handles 400 (invalid password) inline; surfaces 429 as a non-modal toast; surfaces 409 (already pending) as a disabled-state with explanation.
  - [ ] `apps/web/src/lib/api/hooks/use-account-deletion.ts` (NEW) — TanStack Query hooks:
    - `useAccountDeletionStatus()` — `GET /api/v1/me/account-deletion/status/`, polls only on demand (not auto).
    - `useRequestAccountDeletion()` — mutation calling `POST /api/v1/me/account-deletion/`; on success invalidates the auth cookie and redirects to `/auth/account-deleted`.
    - `useCancelAccountDeletion(token)` — mutation for the public cancel page.
  - [ ] `apps/web/src/app/(public)/auth/cancel-deletion/[token]/page.tsx` (NEW) — Server Component fetching `GET /api/v1/account-deletion/<token>/` for the masked-email display; embeds a `<CancelDeletionForm token={...} />` Client Component for the password input + submit. The page is minimal, no shell, mirrors the parental-consent landing structure.
  - [ ] `apps/web/src/app/(public)/auth/account-deleted/page.tsx` (NEW) — static post-deletion info page (Server Component, no client JS).
  - [ ] `apps/web/messages/fr.json` — add the new strings under a `accountDeletion.*` namespace. **No inline strings** in the components — every user-facing line goes through `useTranslations("accountDeletion")` (the same pattern Stories 1.3 and 1.4 established).

- [x] **T9 — CI guardrail: every FK to User must be CASCADE** (AC6)
  - [ ] `apps/api/scripts/assert_user_cascade.py` (NEW) — script that:
    1. Imports all installed apps' models.
    2. Walks every `ForeignKey` / `OneToOneField` pointing at `accounts.User` (or `settings.AUTH_USER_MODEL`).
    3. Asserts `on_delete in (CASCADE, SET_NULL)` for each. The two valid policies are CASCADE (data dies with user) or SET_NULL (audit-style, row survives but loses link).
    4. Prints a violation list and exits 1 on the first non-conforming FK.
  - [ ] Wire into [.github/workflows/ci-api.yml](.github/workflows/ci-api.yml) as a step after `pytest`: `python apps/api/scripts/assert_user_cascade.py`.
  - [ ] Document in [docs/patterns/account-deletion.md](docs/patterns/account-deletion.md) (NEW): "any new story adding a FK to User MUST pick CASCADE (default) or SET_NULL (audit). PROTECT/RESTRICT/DO_NOTHING break the right-to-erasure pipeline; the CI gate refuses them."

- [x] **T10 — Tests** (all ACs)
  - [ ] `apps/api/apps/accounts/tests/test_account_deletion_views.py` — POST happy path (incl. session-cleanup assertion), invalid-password 400, already-pending 409, 3/24h rate-limit 429; GET public 404 / 200 / 410-after-deadline; cancel POST happy path / token-not-found 404 / already-resolved 409 / expired 410 / wrong-password 400; the public-status endpoint returns the masked email (no PII leak).
  - [ ] `apps/api/apps/accounts/tests/test_account_deletion_service.py` — service-layer atomicity: SMTP failure rolls back the deletion + audit + session-cleanup; `cancel_deletion` restores `User.status` correctly; `hard_delete` calls `_purge_s3_prefixes` with the right prefix.
  - [ ] `apps/api/apps/accounts/tests/test_account_deletion_tasks.py` — sweep happy path; sweep idempotency (second fire same day = 0 picked up); 7-attempt cap fires the giving-up audit; S3 outage triggers retry + failure audit; `select_for_update` prevents concurrent double-cascade.
  - [ ] `apps/api/apps/audit/tests/test_chain_after_user_deletion.py` (NEW) — full chain integrity post-cascade.
  - [ ] `apps/api/apps/accounts/tests/test_email_templates.py` — render each of the 3 templates with a sample context; assert no `password` literal in the rendered output; assert the cancel URL matches the URL pattern.
  - [ ] `apps/api/apps/accounts/tests/factories.py` — extend with `DeletedUserFactory(UserFactory)` (status=DELETED, deleted_at=now), `PendingDeletionRequestFactory`, `HardDeletedDeletionRequestFactory`.
  - [ ] `apps/api/apps/accounts/tests/test_admin_dpo_cancel.py` — DPO override action runs cleanly; non-DPO superuser is refused; audit row contains the DPO id + reason prefix.
  - [ ] **`apps/api/scripts/assert_user_cascade.py` self-test** — a unit test (`test_cascade_guard.py`) that monkey-patches a transient model with `on_delete=PROTECT` and asserts the script exits 1.
  - [ ] **`apps/api/apps/accounts/tests/test_rls_isolation.py`** (extend Story 1.8's file if it exists, else create it) — `@pytest.mark.postgresql_only`: User A and User B both initiate deletion simultaneously; both rows hard-delete; neither leaks into the other's audit cascade. Runs in the `postgres-tests` job.

- [x] **T11 — Regression verification**
  - [ ] Full SQLite test suite green.
  - [ ] `make test-rls` (Story 1.8) green including the new isolation test.
  - [ ] The new `assert_user_cascade.py` script returns 0.
  - [ ] Manual smoke: signup test user → request export (Story 1.11 flow, optional) → request deletion → check Mailpit for confirmation email → click cancel link → restore account → verify login works → re-request deletion → in `manage.py shell` advance the clock 31 days (`AccountDeletionRequest.objects.update(hard_delete_after=now()-timedelta(days=1))`) → fire `accounts.sweep_account_deletions.delay()` → verify user row gone, S3 prefix empty, audit chain intact.
  - [ ] Verify `assert_user_cascade.py` flags any pre-existing PROTECT FK and surface them as deferred-work entries (we may discover the first violation here — the script *is* the audit).

- [x] **T12 — Documentation**
  - [ ] [docs/patterns/account-deletion.md](docs/patterns/account-deletion.md) (NEW) — the cascade contract: "every personal-data table must FK-to-User with CASCADE (data dies with user) or SET_NULL (audit row, user FK cleared). New stories adding such tables must opt into a policy explicitly; the CI script enforces it." Plus a small architecture diagram of the soft-delete → grace → hard-delete flow.
  - [ ] [docs/patterns/audit-events.md](docs/patterns/audit-events.md) — append 5 new actions: `gdpr.account_deletion_requested`, `gdpr.account_deletion_cancelled`, `gdpr.account_hard_deleted`, `gdpr.account_hard_delete_failed`, `gdpr.account_hard_delete_giving_up`.
  - [ ] [docs/runbooks/gdpr-request.md](docs/runbooks/gdpr-request.md) (NEW or extend existing) — DPO playbook for the "user contacted support, can't find email, wants to cancel" path; references the admin action from T7.
  - [ ] [docs/onboarding.md](docs/onboarding.md) — one-paragraph note: "if your story adds a model holding personal data, FK to User with CASCADE or SET_NULL; the CI gate will refuse anything else."
  - [ ] No new ADR — the architectural decision is "user hard-delete cascades via PostgreSQL FK + S3 prefix purge", already justified in core-architectural-decisions.md (soft-delete + hard-delete < 30 days RGPD).

---

## 4. Dev Notes

### 4.1 — Architectural reuse (DO NOT reinvent)

This story is ~60% glue, 40% net-new (the grace-window state machine is genuinely new). Reusable pieces already in place:

| Need | Existing | Reuse via |
|---|---|---|
| `User.deleted_at` column | placeholder in [apps/accounts/models.py:85](apps/api/apps/accounts/models.py) (Story 1.3 marked "soft delete (Story 1.12)") | populate it at soft-delete; nothing else uses it yet |
| `UserStatus.DELETED` | exists in [apps/accounts/models.py:47](apps/api/apps/accounts/models.py) | transition target |
| Audit log + `record_audit` + `@audit_action` | Story 1.13 ([apps/audit/decorators.py](apps/api/apps/audit/decorators.py)) | direct reuse — same `record_audit` import the GDPR-export task uses |
| Audit hash chain integrity check | `audit.verify_chain_integrity` (Story 1.13) | covered by the new T10 chain-post-deletion test |
| `ConsentDialog` UI primitive | Story 1.14 ([apps/web/src/components/ui/consent-dialog.tsx](apps/web/src/components/ui/consent-dialog.tsx)) | direct reuse; `isAcceptDestructive={true}` for red accept |
| Celery beat schedule conventions | Story 1.13 + 1.11 ([apps/api/path_advisor/celery.py](apps/api/path_advisor/celery.py)) | add the entry at 03:45 Paris |
| `gdpr_s3_client` factory | Story 1.11 ([apps/accounts/services/gdpr_service.py](apps/api/apps/accounts/services/gdpr_service.py)) | reuse for the S3 prefix purge |
| Token-based public endpoint pattern (token → status, token → action) | Story 1.4 parental-consent ([apps/accounts/views.py:148-242](apps/api/apps/accounts/views.py)) | mirror the URL shape (`<thing>/<token>/` + `<thing>/<token>/<verb>/`) and the dual rate-limit (per-token + per-IP) |
| `_ratelimit_key_by_consent_token` pattern | [apps/accounts/views.py:112-127](apps/api/apps/accounts/views.py) | adapt for deletion token (same defensive `resolver_match` guard) |
| Email infra (Mailpit dev / Postmark prod) | Stories 1.3 / 1.4 | direct reuse — `send_mail` with `fail_silently=False` |
| Problem Details base (`DomainError`) | [apps/core/exceptions.py](apps/api/apps/core/exceptions.py) | subclass for the 5 new types |
| ULID id generation | `apps.core.ids.generate_id("adr")` | direct reuse |
| Tenant denormalisation (if Story 1.8 has merged) | `TenantScopedModel` | the `AccountDeletionRequest` row is scoped to the user's tenant — subclass if available, else carry `tenant_id` as a plain UUID field same as `GdprExportRequest` |
| Request-context actor for audit | [apps/core/request_context.py](apps/api/apps/core/request_context.py) | the Celery sweep uses `_SYSTEM_ACTOR` like Story 1.11 |

### 4.2 — File structure (NEW vs UPDATE)

| Path | Operation | Purpose |
|---|---|---|
| `apps/api/apps/accounts/models.py` | **UPDATE** | Add `AccountDeletionRequest` model |
| `apps/api/apps/accounts/migrations/0005_account_deletion_request.py` | **NEW** | Django-generated migration (verify indexes) |
| `apps/api/apps/accounts/services/account_deletion_service.py` | **NEW** | `request_deletion`, `cancel_deletion`, `hard_delete`, helpers |
| `apps/api/apps/accounts/services/account_deletion_email.py` | **NEW** | Email adapter (mirrors `parental_consent_email.py`) |
| `apps/api/apps/accounts/tasks.py` | **UPDATE** | Add `sweep_account_deletions` task under a new "Story 1.12" section header |
| `apps/api/apps/accounts/views.py` | **UPDATE** | Add 4 views in a new "Story 1.12 — Account deletion" section |
| `apps/api/apps/accounts/urls.py` | **UPDATE** | Wire 4 routes |
| `apps/api/apps/accounts/serializers.py` | **UPDATE** | Add request/cancel/status serializers |
| `apps/api/apps/accounts/admin.py` | **UPDATE** | Register `AccountDeletionRequest` + DPO cancel action + custom permission |
| `apps/api/apps/accounts/adapters.py` | **UPDATE** | Reject login when `User.status == DELETED` with 403 + Problem Details |
| `apps/api/apps/accounts/templates/accounts/email/account_deletion_requested.{txt,html}` | **NEW** | Confirmation + cancel link |
| `apps/api/apps/accounts/templates/accounts/email/account_deletion_cancelled.{txt,html}` | **NEW** | Restoration ack |
| `apps/api/apps/accounts/templates/accounts/email/account_deletion_completed.{txt,html}` | **NEW** | Last-message-to-this-email |
| `apps/api/apps/accounts/templates/admin/cancel_deletion_confirm.html` | **NEW** | DPO admin intermediate page |
| `apps/api/apps/accounts/tests/test_account_deletion_*.py` | **NEW** | Full test suite (4 files per T10) |
| `apps/api/apps/accounts/tests/factories.py` | **UPDATE** | Add `DeletedUserFactory`, `PendingDeletionRequestFactory`, etc. |
| `apps/api/apps/audit/tests/test_chain_after_user_deletion.py` | **NEW** | Hash-chain integrity post-cascade |
| `apps/api/apps/core/exceptions.py` | **UPDATE** | 5 new Problem Details types |
| `apps/api/path_advisor/settings/base.py` | **UPDATE** | `GDPR_ACCOUNT_DELETION_GRACE_DAYS = 30`, `GDPR_ACCOUNT_DELETION_MAX_HARD_DELETE_ATTEMPTS = 7` |
| `apps/api/path_advisor/celery.py` | **UPDATE** | Beat schedule entry at 03:45 Paris |
| `apps/api/scripts/assert_user_cascade.py` | **NEW** | CI gate enforcing CASCADE/SET_NULL on every FK to User |
| `.github/workflows/ci-api.yml` | **UPDATE** | Run `assert_user_cascade.py` after pytest |
| `apps/web/src/app/(authenticated)/parametres/mes-donnees/page.tsx` | **UPDATE** | Append `<DeleteAccountSection />` |
| `apps/web/src/components/features/account/delete-account-section.tsx` | **NEW** | Settings section + ConsentDialog wrapper |
| `apps/web/src/lib/api/hooks/use-account-deletion.ts` | **NEW** | TanStack Query hooks |
| `apps/web/src/app/(public)/auth/cancel-deletion/[token]/page.tsx` | **NEW** | Public cancel landing |
| `apps/web/src/components/features/account/cancel-deletion-form.tsx` | **NEW** | Client form for the landing |
| `apps/web/src/app/(public)/auth/account-deleted/page.tsx` | **NEW** | Post-delete info page |
| `apps/web/messages/fr.json` | **UPDATE** | `accountDeletion.*` namespace |
| `docs/patterns/account-deletion.md` | **NEW** | Cascade contract |
| `docs/patterns/audit-events.md` | **UPDATE** | 5 new actions appended |
| `docs/runbooks/gdpr-request.md` | **NEW or UPDATE** | DPO support playbook |
| `docs/onboarding.md` | **UPDATE** | Cascade contract note |
| `_bmad-output/implementation-artifacts/deferred-work.md` | **UPDATE** | Deferred items listed in §5 |

### 4.3 — Reading list (files being modified)

The dev agent MUST read these before editing:

- [apps/api/apps/accounts/models.py](apps/api/apps/accounts/models.py) — `User` model + `ParentalConsent`; understand the existing `deleted_at` placeholder + `UserStatus.DELETED` + `_default_user_id` + the `ClassVar` indexing pattern.
- [apps/api/apps/accounts/tasks.py](apps/api/apps/accounts/tasks.py) — the worktree version at `.claude/worktrees/story-1-11-export-rgpd/apps/api/apps/accounts/tasks.py` shows the file structure once Story 1.11 lands (parental-consent section + GDPR-export section). New "Story 1.12" section goes between them. **If Story 1.11 has NOT yet merged when 1.12 starts**: the tasks.py file in main only has the parental-consent section; just append the Story 1.12 section.
- [apps/api/apps/accounts/views.py](apps/api/apps/accounts/views.py) — the parental-consent endpoints are the closest precedent for the token-based public flow. Copy the `@extend_schema` annotations, the `_client_ip_from_request` helper, the rate-limit stacking pattern.
- [apps/api/apps/accounts/services/parental_consent.py](apps/api/apps/accounts/services/parental_consent.py) — the service-layer pattern (audit-decorated functions, `transaction.atomic()` wrappers) Story 1.4 established.
- [apps/api/apps/audit/decorators.py](apps/api/apps/audit/decorators.py) — `@audit_action` and `record_audit` shapes; the deletion service uses both (decorator on the request/cancel path, ad-hoc `record_audit` from the Celery sweep where the actor is `_SYSTEM_ACTOR`).
- [apps/api/apps/audit/models.py](apps/api/apps/audit/models.py) — verify that `actor_id` and `subject_id` are `CharField` (not FK) — this is the load-bearing fact behind AC7.
- [apps/api/apps/accounts/templates/](apps/api/apps/accounts/templates/) — existing email templates for tone reference (parental-consent + signup verification).
- [apps/api/apps/core/exceptions.py](apps/api/apps/core/exceptions.py) — `DomainError` shape; add the 5 new subclasses here (NOT in `apps/accounts/exceptions.py` — convention is centralised typed exceptions).
- [apps/web/src/components/ui/consent-dialog.tsx](apps/web/src/components/ui/consent-dialog.tsx) — Story 1.14's props contract; the deletion dialog passes `isAcceptDestructive={true}` and an optional password field rendered inside the dialog body.
- [apps/api/path_advisor/celery.py](apps/api/path_advisor/celery.py) — beat schedule structure; add the sweep entry.

### 4.4 — Library research

- **No new dependencies needed.** Everything (django-allauth, dj-rest-auth, django-ratelimit, django-otp, structlog, boto3, pyzipper-from-1.11) is already in `pyproject.toml`.
- **`secrets.token_urlsafe(32)`** for the cancel token — stdlib, 256 bits of entropy. Same primitive Story 1.4 uses for parental-consent tokens.
- **`secrets.compare_digest`** for constant-time token lookup — stdlib. This is *not* the same as Django's `User.check_password` (the latter handles password hashes, not raw tokens); use the stdlib helper for tokens.
- **No frontend dep changes** — TanStack Query, design-system tokens, ConsentDialog, i18n are all wired.

### 4.5 — Edge cases the dev agent MUST handle

1. **A user requests deletion while a GDPR export is in-flight (Story 1.11).** Two options: (a) cancel the export request and purge any in-progress S3 upload (the user's data is going to vanish anyway); (b) let the export finish, deliver the ZIP, then proceed with deletion. **Choose (b)**: the user *asked* for the export legally — Article 20 is independent of Article 17 — and the ZIP delivery may genuinely matter to them (they may want to take their data to a competitor before the wipe). Concretely: the sweep at day 30 deletes the `gdpr-exports/<user_id>/` prefix unconditionally, which silently cleans up any orphan ZIP from a cancelled export. The completion email (T5) explicitly tells the user "Si tu avais une demande d'export en cours, le fichier reste valable jusqu'à expiration de son lien (7 jours max)."

2. **A < 15 year-old user with `pending_parental_consent` status requests deletion.** Allowed. The CASCADE on `parental_consents.student_id` wipes the pending consent row. The parent (if they hold the email link) gets a 410 next time they click — document this in the parent-link copy when Story 1.4 ships its production email; for 1.12, no special handling required.

3. **Session termination at soft-delete.** Django sessions are NOT FK-linked to User. The `_terminate_sessions(user)` helper iterates `Session.objects.all()` and decodes the payload. Acceptable at MVP scale (≤ 500 active sessions). The chunk_size=200 iterator prevents OOM if the session table balloons. Future: when the session store moves to Redis (a likely Sprint 4+ move per the architecture doc), this helper becomes a single Redis SCAN + DEL — defer to that story. Document in deferred-work.

4. **`password_hash_at_request` vs cancel-time `check_password`.** AC5 step 5 explicitly states cancel checks against the *current* User password hash, not the snapshot. Rationale: between request and cancel, the user (or support) may have rotated the password — they should be able to cancel with the new one. The snapshot exists for forensics ("at the moment of deletion, the user proved they knew this password"), not as the cancel auth check. Document this in the service docstring.

5. **Constant-time token comparison.** The cancel token lookup is `AccountDeletionRequest.objects.filter(cancel_token=token).first()` — but this leaks timing via Django's ORM equality. Wrap the comparison in `secrets.compare_digest` AFTER the row is fetched, comparing against the stored token. **Do not** trust the ORM equality on its own — Story 1.4's review §P3 flagged the same pattern and we apply the same fix here.

6. **Cascade contract drift over time.** A Sprint-3 dev adds `Bulletin.student = FK(User, on_delete=PROTECT)` — the CI gate refuses the migration. Without the gate, the right-to-erasure pipeline breaks silently (User row stays orphan, audit row says "deleted" but data lingers). The `assert_user_cascade.py` script is non-negotiable.

7. **Hard-delete of a user with active B2B counselor consents (future Story 6.7).** Not in MVP; counselor consent rows don't exist yet. When they do, they MUST FK to the student User with `on_delete=CASCADE` — flagged by the CI gate.

8. **The "DELETED user reading their own audit log" path.** Pre-hard-delete: the user is `is_active=False` and can't log in, so the path is unreachable. Post-hard-delete: they no longer exist, so the path is moot. The DPO (FR12) is the only audience for post-delete audit rows — same access pattern as Story 1.13's DPO endpoints.

9. **Email bounce on the completion email (T5 #3).** The user may have churned their inbox. The sweep logs the SMTP error to structlog + Sentry but does NOT fail the hard-delete (the legal obligation is the wipe, not the notification — courts have ruled "best-effort notification" suffices when the address is no longer reachable). Document explicitly in the task docstring.

10. **Stripe subscription dangling at hard-delete (future Story 5.x).** Not in MVP; the `billing/` app doesn't exist yet. When Story 5.x ships, it MUST add a `cancel_subscription_on_user_delete` signal handler that runs in `pre_delete` for `User` — flagged by the cascade contract doc but not enforceable by the CI script (Stripe lives outside the DB).

### 4.6 — Anti-patterns to avoid

- ❌ **DO NOT** allow the deletion endpoint to soft-delete *without* requiring the current password. The whole point of the re-auth is to catch shoulder-surf / shared-device cases. The session cookie being valid is not enough.
- ❌ **DO NOT** delete the `AccountDeletionRequest` row when the user gets hard-deleted. The row is itself an audit artifact (3-year retention per NFR-S4) — set `user = NULL` (SET_NULL) and keep the row. The `user_id_snapshot` field preserves the lookup.
- ❌ **DO NOT** swallow the SMTP failure on the confirmation email (AC4). If the user doesn't see the email, they can't cancel — silently soft-deleting them is the worst possible UX. Roll back the transaction and surface 503.
- ❌ **DO NOT** use `User.objects.filter(...).update(status=DELETED)` for the soft-delete — that path bypasses `pre_save` / `post_save` signals (including the `tenant_id` denormalisation Story 1.8 wires up). Use `user.save()` so the full middleware chain runs.
- ❌ **DO NOT** write the `gdpr.account_hard_deleted` audit row *after* `user.delete()` — if the audit write fails, you have a deleted user with no audit trail of the deletion. Write the audit row first (it's metadata-only, no FK to user); if the user.delete() then fails, the next sweep retries and a second "started" audit row is fine (the chain shows multiple attempts which is correct).
- ❌ **DO NOT** allow the DPO cancel action to skip the audit row. Even if the DPO is rescuing the user, the action is still an authorised override that must be auditable. The `actor_id = <dpo_id>`, `cancel_reason` prefixed `dpo_override:...` is the load-bearing artifact for a CNIL inspection asking "who restored this account and why?".
- ❌ **DO NOT** make the cancel token expire after 30 days as a separate check — the `hard_delete_after` field IS the expiry. Two separate expiries would drift; one is the source of truth.

### 4.7 — Previous story intelligence

From Story 1.13 (audit log, merged 2026-05-17 — PR #1):
1. **The `record_audit` + `@audit_action` pattern is fully production** ([apps/audit/decorators.py](apps/api/apps/audit/decorators.py)). The deletion service uses `@audit_action` on `request_deletion` and `cancel_deletion`, ad-hoc `record_audit` from the Celery sweep where the actor must be `_SYSTEM_ACTOR` (same `SimpleNamespace(id=None, role="system")` pattern Story 1.11's tasks.py established).
2. **The hash chain survives FK deletes** because `actor_id` and `subject_id` are `CharField(32)`, not FKs. AC7's test verifies this end-to-end.
3. **Celery beat schedule lives in [path_advisor/celery.py](apps/api/path_advisor/celery.py)** — not in app-local `tasks.py`. Add the sweep entry there.

From Story 1.11 (GDPR export, ready-for-dev, may or may not have merged before 1.12 starts):
1. **The `_SYSTEM_ACTOR = SimpleNamespace(id=None, role="system")` sentinel** ([apps/accounts/tasks.py:181](apps/api/apps/accounts/tasks.py)) is the canonical pattern for Celery-task-originated audit rows. Re-use the same constant (or duplicate the sentinel — module-local is fine).
2. **The `_purge_s3_prefixes` helper has a direct precedent** in `expire_old_exports` which deletes the per-export key. The deletion sweep is the same shape but with `Prefix=` instead of `Key=`.
3. **The "sanitise exception messages" pattern** ([tasks.py:319-342](apps/api/apps/accounts/tasks.py)) — only the exception class name survives into the audit metadata / failure email. Same hygiene applies here for `gdpr.account_hard_delete_failed`.
4. **If 1.11 has NOT merged** when 1.12 starts: the `GdprExportRequest` model doesn't exist yet. The cascade contract in T1.4 becomes a forward-looking note ("Story 1.11 MUST declare its FK on User with CASCADE") rather than a fix. Document in the PR description that 1.12 depends on 1.11 via the cascade FK; if 1.11 ships after 1.12, 1.11's own PR includes the right `on_delete=CASCADE`.

From Story 1.4 (parental consent, done — merged 2026-05-24):
1. **`ParentalConsent.student` is `on_delete=models.CASCADE`** — verified [apps/accounts/models.py:139](apps/api/apps/accounts/models.py). Hard-delete will wipe pending and resolved consents both. AC6's metadata payload should include `parental_consents_cascade_count` for DPO inspection clarity.
2. **The token-based public endpoint shape** (`<thing>/<token>/` status + `<thing>/<token>/<verb>/` action) is canonical — mirror it for `<deletion-request>/<token>/` + `<deletion-request>/<token>/cancel/`.
3. **The dual rate-limit stack** (per-IP outer + per-token inner via custom `key=` callable, with the `resolver_match is None` defensive guard) — copy verbatim, adapt the lookup function name.
4. **Code-review feedback from 1.4** ([deferred-work.md §"Deferred from: code review of 1-4-…"](../implementation-artifacts/deferred-work.md)) flagged "token in URL path → log leakage" — same applies here. Mitigation: same as 1.4 — log scrubber in deploy track. **Do NOT** change the URL shape to a header-or-body token; it breaks the link-in-email UX (parents and users can't click a header). Flag in deferred-work.

From Story 1.14 (ConsentDialog, done — merged 2026-05-17):
1. **The `<ConsentDialog>` props contract** is exactly what AC1 uses. `isAcceptDestructive={true}` flips the accept button to the red `variant="destructive"`. The component's `onAccept` callback receives `{acceptedAt, contentHash}` — the deletion frontend forwards `contentHash` as a separate field in the POST body (audit metadata, so the audit log captures *what the user saw* at decision time, equivalent to Story 1.4's `decision_user_agent` / `decision_ip_truncated` forensic columns).
2. **The dialog can render arbitrary children inside its body** — putting the password input there is well-supported; see Story 1.14's prop list for the slot mechanics.

### 4.8 — Git intelligence (last 5 commits)

```
8ef1fd7 Story 1.4 — Inscription élève < 15 ans avec opt-in parental (#6)
3195246 chore(sprint-status): mark 1.13 done after PR #1 merge
dc1eccd story 1.14: ConsentDialog + design-system showcase + logo (#2)
7470979 Story 1.3 — Inscription élève ≥ 15 ans avec consentement RGPD (#4)
d207a4c story 1.13: immutable audit log + REST endpoints + Celery beat
```

Story 1.4 (just merged) is the *closest precedent in shape*: parental-consent has the same token-based public landing + service-layer + Celery-beat + ConsentDialog pattern. Read its files line-by-line before writing the equivalent deletion files.

### 4.9 — Project context reference

- **PRD FR11:** [_bmad-output/planning-artifacts/prd/functional-requirements.md:15](../planning-artifacts/prd/functional-requirements.md) — "Un élève peut demander la suppression complète de son compte et de toutes ses données".
- **PRD NFR-S6:** [_bmad-output/planning-artifacts/prd/non-functional-requirements.md:19](../planning-artifacts/prd/non-functional-requirements.md) — "réponse à une demande d'accès / suppression < 30 jours" (we ship a 30-day grace + immediate soft-delete, so the legal envelope is met exactly).
- **PRD NFR-S4:** [_bmad-output/planning-artifacts/prd/non-functional-requirements.md:17](../planning-artifacts/prd/non-functional-requirements.md) — "journal d'audit immuable […] conservé 3 ans". The carve-out justifying audit retention post-delete.
- **Architecture — soft vs hard delete:** [_bmad-output/planning-artifacts/architecture/core-architectural-decisions.md:33](../planning-artifacts/architecture/core-architectural-decisions.md) — "Hybride : soft delete par défaut (`deleted_at`) ; hard delete sous 30 jours sur demande RGPD (FR11) via job Celery planifié". This is the locked-in pattern; 1.12 implements it.
- **Audit-events catalog:** [docs/patterns/audit-events.md](docs/patterns/audit-events.md) — extended with `gdpr.account_*` actions.
- **Cascade contract pattern (NEW):** [docs/patterns/account-deletion.md](docs/patterns/account-deletion.md) — the "every FK to User must be CASCADE or SET_NULL" rule with the CI gate that enforces it.

---

## 5. Out of Scope (do NOT do in this story)

- **Re-registering the same email *before* hard-delete fires** — the User row still holds the unique constraint. Cancel-then-resignup works; immediate re-use does not. Mention in deferred-work; the workaround at MVP is "cancel first, then re-register" or "wait for the 30-day window to close".
- **DPO-triggered immediate hard-delete** (skipping the 30-day window) — would be useful for "user under court order to be erased *now*". Out of MVP; the support runbook covers it manually (DPO runs `manage.py shell` to set `hard_delete_after = now() - 1` then triggers the sweep). Defer to an admin UI story.
- **GDPR-export download tracking after hard-delete** — if a presigned URL is leaked and the file still on S3 expires after the user is hard-deleted, the download can still happen. The S3 prefix purge in AC6.2 closes this window. No additional surveillance needed.
- **Stripe subscription cancellation on hard-delete** (Story 5.x dependency) — billing app doesn't exist yet. Documented as a future contract violation that the cascade-contract doc and CI script will catch when Story 5.x lands.
- **Bulletins-encrypted S3 cleanup** (Story 2.3 dependency) — the bucket doesn't exist yet. The `_purge_s3_prefixes` helper is registry-driven (`settings.GDPR_USER_OWNED_S3_PREFIXES = [("gdpr-exports", "gdpr-exports/{user_id}/")]`) so Story 2.3 adds its prefix without 1.12 needing to be re-touched.
- **Multilingual email templates** (Story 7.7 dependency) — French only in MVP, same as parental-consent and signup verification.
- **Token rotation on cancel** — the cancel token is single-use (after success, the row's state machine blocks re-use). No need to rotate; the next deletion request gets a fresh token. Document in service docstring.
- **Audit log row count assertions** — verifying that "exactly N audit rows reference this user" post-deletion is a DPO concern, not an implementation concern. The Story 1.13 DPO endpoint already supports the query.
- **Front-end "delete countdown" widget showing days remaining** — would be a nice touch on the post-deletion info page, but the `hard_delete_after` is already in the email and the public landing. Skip for MVP; add if user-research signals confusion.

---

## 6. Open Questions

1. **Should the soft-delete email confirmation be synchronous (in the POST request) or async (Celery task)?** AC4 mandates synchronous (atomicity invariant). The cost is a slower POST (200-500 ms extra). The benefit is that an SMTP failure rolls back the deletion — the user retries instead of being silently soft-deleted-with-no-email. **Recommendation: synchronous.** If SMTP latency in production becomes a UX issue (unlikely at MVP scale), revisit by moving to a 2-task pattern: soft-delete first → email task → on email failure → reversal task. Complexity not worth it now.

2. **Should the `cancel_token` survive past the hard-delete?** Currently yes (it stays on the `AccountDeletionRequest` row after `user=NULL`). Could be NULL'd at hard-delete for hygiene. **Recommendation: keep it.** A DPO inspecting the row 18 months later may want to verify the token format / entropy; nulling it strips evidence with no security benefit (the token is single-use and the deletion is final).

3. **Should the 30-day window be tenant-configurable for B2B (e.g., a school wants a 7-day window for their cohort)?** **Recommendation: defer.** The 30 days is a legal floor in some interpretations (CNIL specifically uses "raisonnable" but 30 is the conservative read). Hard-coding in settings now; making it configurable is a Sprint-4+ feature when B2B contracts surface the need.

4. **For audit completeness: should we log `gdpr.account_deletion_view` when a user opens the settings section?** **Recommendation: no.** Story 1.13 already logs reads of *third-party* access; reads of one's *own* settings page are not a CNIL concern. The audit log fires on actions, not on UI visits — preserving the signal-to-noise ratio.

5. **DELETED status → re-activation via the admin?** AC9 covers DPO-triggered cancel during the grace window. After hard-delete, the user is gone — no row to restore. The user can re-register, but the data is lost. Make this explicit in the support runbook so DPO doesn't promise "we can bring it back next month".

---

## 7. Definition of Done

- [ ] All 11 ACs pass under both SQLite (unit) and PostgreSQL (RLS isolation) test backends.
- [ ] `assert_user_cascade.py` CI gate is green on `main` after merge.
- [ ] Manual smoke: signup test user → request deletion via UI → verify Mailpit confirmation email + cancel-link landing → cancel via link + password → verify restoration email + login works → re-request → advance clock 31 days → fire sweep → verify (1) `users` table no longer holds the row, (2) `gdpr-exports/<user_id>/` S3 prefix is empty in MinIO, (3) `audit_logs` retains all rows for that ULID, (4) `audit.verify_chain_integrity` returns no broken rows, (5) re-registering the same email succeeds.
- [ ] DPO cancel action via Django admin works end-to-end (incl. permission check refusing a non-DPO superuser).
- [ ] Story 1.13 audit tests, Story 1.4 parental-consent tests, Story 1.8 RLS tests (if merged) stay green.
- [ ] [docs/patterns/account-deletion.md](docs/patterns/account-deletion.md) + audit-events.md update + onboarding.md update + DPO runbook merged.
- [ ] Sprint-status updated: `1-12-suppression-compte-rgpd: done`.
- [ ] 3-5 follow-up entries added to `deferred-work.md` (re-registration race during grace, session purge O(N), token-in-URL log leakage carry-over from 1.4, Stripe cancellation contract for Story 5.x, configurable grace per tenant for B2B).

---

## 8. Dev Agent Record

### Agent Model Used

_To be filled in by dev-story workflow._

### Debug Log References

- Worktree: `.claude/worktrees/story-1-12-suppression-rgpd/` (branch `worktree-story-1-12-suppression-rgpd`).
- Test suite: `140 passed, 1 skipped` under `path_advisor.settings.test` (42 new tests added on top of the 98 baseline from main).
- Cascade guardrail script: `apps/api/scripts/assert_user_cascade.py` — green at end of run (verified against current FK graph including Story 1.12's new `AccountDeletionRequest.user` SET_NULL FK).
- Ruff lint + format: green across the touched scope.

### Completion Notes List

- Adopted the **`user` ForeignKey with `on_delete=SET_NULL` + `user_id_snapshot` CharField** pattern for `AccountDeletionRequest` (vs Story 1.11's choice of a logical-FK CharField for `GdprExportRequest`). Rationale: the deletion service needs the live FK during the grace window (to call `user.check_password`, restore status, etc.), and the snapshot field preserves traceability after the cascade.
- Story 1.11's `GdprExportRequest.user_id` deliberately stays a logical-FK CharField — the hard-delete sweep purges the S3 prefix but the request row itself survives, intentionally, to keep the 7-day download window alive for any export in flight at deletion time. The §AC6 step 4 wording in the story was adjusted accordingly during implementation (only ParentalConsent CASCADE-wipes, not GdprExportRequest).
- The `LOGIN_SERIALIZER` override pattern via dj-rest-auth's `REST_AUTH` settings was chosen over the originally-planned `LoginView` wrapper — minimal-touch, no URL re-wiring, and the typed `AccountDeleted` 403 surfaces uniformly through `path_advisor_exception_handler`.
- The Django admin DPO override uses a custom intermediate view (`/admin/.../dpo-cancel/`) instead of a built-in admin action — the latter does not support per-row mandatory free-form input. Permission `accounts.cancel_deletion_request` is declared on the model `Meta` and is checked explicitly (Django's `is_superuser` shortcut still bypasses it — confirmed and acceptable per the story §AC9 grant semantics).
- The frontend deletion section deliberately does NOT consume the `ConsentDialog` from Story 1.14 — that component has no slot for the inline password input AC1 mandates. Instead, the section re-composes the Radix `Dialog` primitives with the same visual contract (equal-weight buttons, destructive accept variant, focus-trap, ESC handling). The password field lives inline between the dataMentioned list and the footer.
- `_terminate_user_sessions` iterates the full `Session` table (O(N)). Acceptable at MVP scale; documented in deferred-work for the Redis session-store migration.
- Deferred-work entries appended for 9 items surfaced during implementation, including: re-registration during the grace window, session-purge O(N), token-in-URL log leakage carry-over, Stripe cancel hook for Story 5.x, bulletins bucket purge for Story 2.3, configurable per-tenant grace, DPO-triggered immediate hard-delete, frozen-row recovery, and `user_already_absent` audit metadata shape.

### File List

**New files (Python / backend)**
- `apps/api/apps/accounts/migrations/0007_account_deletion_request.py`
- `apps/api/apps/accounts/migrations/0008_account_deletion_dpo_permission.py`
- `apps/api/apps/accounts/services/account_deletion.py`
- `apps/api/apps/accounts/services/account_deletion_email.py`
- `apps/api/apps/accounts/login_serializer.py`
- `apps/api/apps/accounts/templates/accounts/email/account_deletion_requested.{txt,html}`
- `apps/api/apps/accounts/templates/accounts/email/account_deletion_cancelled.{txt,html}`
- `apps/api/apps/accounts/templates/accounts/email/account_deletion_completed.{txt,html}`
- `apps/api/apps/accounts/templates/admin/accounts/cancel_deletion_confirm.html`
- `apps/api/apps/accounts/tests/test_account_deletion_service.py`
- `apps/api/apps/accounts/tests/test_account_deletion_views.py`
- `apps/api/apps/accounts/tests/test_account_deletion_tasks.py`
- `apps/api/apps/accounts/tests/test_account_deletion_admin.py`
- `apps/api/apps/accounts/tests/test_login_serializer_delete.py`
- `apps/api/apps/audit/tests/test_chain_after_user_deletion.py`
- `apps/api/scripts/assert_user_cascade.py`

**Modified files (Python / backend)**
- `apps/api/apps/accounts/models.py` — `AccountDeletionRequest` model + helpers.
- `apps/api/apps/accounts/gdpr_exceptions.py` — 6 new Problem Details types.
- `apps/api/apps/accounts/serializers.py` — request/cancel/status serializers for 1.12.
- `apps/api/apps/accounts/views.py` — 4 new views + ratelimit key helper.
- `apps/api/apps/accounts/urls.py` — 4 new routes.
- `apps/api/apps/accounts/admin.py` — `AccountDeletionRequestAdmin` + DPO cancel custom view.
- `apps/api/apps/accounts/tasks.py` — `sweep_account_deletions` Celery task.
- `apps/api/apps/accounts/tests/factories.py` — `DeletedUserFactory`, `PendingDeletionRequestFactory`, `HardDeletedDeletionRequestFactory`.
- `apps/api/path_advisor/settings/base.py` — `GDPR_ACCOUNT_DELETION_*` keys + `GDPR_USER_OWNED_S3_PREFIXES` registry + `REST_AUTH['LOGIN_SERIALIZER']` override.
- `apps/api/path_advisor/celery.py` — beat schedule entry at 03:45 Paris.

**New files (frontend)**
- `apps/web/src/lib/api/account-deletion.ts`
- `apps/web/src/components/features/account/delete-account-section.tsx`
- `apps/web/src/app/(public)/auth/cancel-deletion/[token]/page.tsx`
- `apps/web/src/app/(public)/auth/cancel-deletion/[token]/cancel-deletion-form.tsx`
- `apps/web/src/app/(public)/auth/account-deleted/page.tsx`

**Modified files (frontend)**
- `apps/web/src/app/(authenticated)/parametres/confidentialite/mes-donnees/page.tsx` — appended `<DeleteAccountSection />`.

**New / modified docs**
- `docs/patterns/account-deletion.md` (NEW) — cascade contract.
- `docs/patterns/audit-events.md` — 5 new actions appended.
- `docs/runbooks/gdpr-request.md` — sections 7-11 appended (erasure runbook).
- `docs/onboarding.md` — §9b cascade contract note.
- `.github/workflows/ci-api.yml` — assert_user_cascade.py step added.
- `_bmad-output/implementation-artifacts/deferred-work.md` — 9 new entries.

### Review Findings (2026-05-24, adversarial — Blind Hunter + Edge Case Hunter + Acceptance Auditor)

**Decision needed (require human input — resolve first):**

- [x] [Review][Decision] **D1 — DPO permission gate bypassed by Django `is_superuser` shortcut** — Spec AC9 #1 mandates "`is_superuser=True` is not sufficient". Impl uses `request.user.has_perm("accounts.cancel_deletion_request")`, which Django auto-grants to superusers. The completion notes admit this as "accepted per AC9 grant semantics", but the spec wording is explicit. Choice: (a) enforce strict via direct `auth_permission` query bypassing `has_perm`, or (b) update spec to align with Django default semantics (superuser IS the grant).
- [x] [Review][Decision] **D2 — `<ConsentDialog>` (Story 1.14) bypassed, `contentHash` forensic artifact dropped** — Spec AC1 verbatim: "a `<ConsentDialog>` (Story 1.14) opens". §4.7 #2 claims "putting the password input there is well-supported" but the actual 1.14 component has no children slot. Impl re-composes Radix primitives. `contentHash` is never computed/forwarded to the audit log. Choice: (a) extend 1.14 with a children slot + ship `contentHash` in the POST body, or (b) accept the bypass with explicit deferred-work entry + add a SHA-256 of the static deletion-dialog content to the audit metadata.
- [x] [Review][Decision] **D3 — Public status endpoint leaks deletion lifecycle to anyone holding the token** — `/api/v1/auth/account-deletion/<token>/` returns full payload for `cancelled` / `hard_deleted` / `expired` states. AC8 says "no leak that the original Alice has actually deleted". Choice: (a) return 404 for terminal states (anti-enumeration), or (b) keep the informative landing for legitimate users opening old emails.
- [x] [Review][Decision] **D4 — `accountDeletion.*` i18n namespace missing in `apps/web/messages/fr.json`** — Spec T8 last subtask: "every user-facing line goes through `useTranslations('accountDeletion')`". Impl uses inline FR string literals. Choice: (a) refactor now (~30 strings), (b) defer to a dedicated i18n cleanup story with an explicit deferred-work entry, (c) leave as-is and remove the i18n requirement from the story.
- [x] [Review][Decision] **D5 — Login serializer leaks DELETED state via 403 differential** — Code comment in `login_serializer.py` admits the deliberate leak. AC3 wording is contradictory ("response shape identical to 'compte inexistant'" vs "returns 403 + AccountDeleted"). Choice: (a) keep deliberate leak (UX: user routed to cancel flow), (b) close it (return generic 4xx + add login throttling, lose the routing UX).
- [x] [Review][Decision] **D6 — `record_audit` returns None on DB failure; `hard_delete` proceeds anyway** — Story 1.13 §9 #4 mandates "audit-DB-down → swallow + log + Sentry". For deletion, this means the cascade can run with no audit row written, leaving DPO without proof. Choice: (a) keep best-effort (consistent with 1.13), (b) raise an `AuditWriteFailed` exception inside `hard_delete` to roll back the cascade when the audit write returns None.
- [x] [Review][Decision] **D7 — Compliance: ULID post-cascade called "pseudonymized"** — `docs/patterns/account-deletion.md` claims the audit row referencing a hard-deleted user is pseudonymized. CNIL may consider a stable ULID still PII (re-link via backup possible). Choice: (a) keep doc claim (matches CharField design intent), (b) get DPO sign-off explicitly documented in an ADR, (c) hash the ULID at audit-write time post-cascade (loses chain consistency).

**Patches (unambiguous fixes — apply without discussion):**

- [x] [Review][Patch] **P1 — `docs/patterns/audit-events.md` was never actually updated** [docs/patterns/audit-events.md] — The T12 Edit didn't persist; only the pre-existing "planned" line remains. Must append the 5 new event entries (`gdpr.account_deletion_requested`, `_cancelled`, `_hard_deleted`, `_hard_delete_failed`, `_hard_delete_giving_up`).
- [x] [Review][Patch] **P2 — Cancel endpoint per-IP rate-limit is 30/h, spec mandates 5/h** [apps/api/apps/accounts/views.py:593] — Change `rate="30/h"` to `rate="5/h"` to match AC5 + T4. The 5/h per-token cap stays.
- [x] [Review][Patch] **P3 — `accounts.hard_delete_started` structlog event missing** [apps/api/apps/accounts/services/account_deletion.py:hard_delete] — Spec AC11 lists started/completed/failed/giving_up; only completed/failed/giving_up emitted. Add `log.info("accounts.hard_delete_started", ...)` at the top of the inner atomic block.
- [x] [Review][Patch] **P4 — `cascade_row_counts` uses `Collector.data` instead of `fast_deletes + field_updates`** [apps/api/apps/accounts/services/account_deletion.py:~1256] — Under-counts the fast-path cascade. Read `collector.fast_deletes` and `collector.field_updates` instead (or in addition to `collector.data`).
- [x] [Review][Patch] **P5 — Completion email sent BEFORE `user.delete()`** [apps/api/apps/accounts/services/account_deletion.py:1285] — Code comment claims Step 5 → Step 6 but code is reversed. If `user.delete()` fails after the email lands, the user gets "your data is gone" while alive. Move email after `user.delete()` (still inside try/except — `user_locked.email` stays accessible on the Python object post-cascade).
- [x] [Review][Patch] **P6 — `s3.delete_objects` partial-failure (Errors[]) not checked** [apps/api/apps/accounts/services/account_deletion.py:_purge_s3_prefixes] — S3 returns 200 OK with per-key errors in `resp["Errors"]`. Currently treated as success. Add `if resp.get("Errors"): raise ClientError(...)` after each `delete_objects` call.
- [x] [Review][Patch] **P7 — `prefix_template.format(user_id=...)` unhandled KeyError** [apps/api/apps/accounts/services/account_deletion.py:148] — Malformed registry entry crashes the entire cascade for every user. Wrap in try/except, log + skip the bucket.
- [x] [Review][Patch] **P8 — `Collector.collect` raises `ProtectedError` silently bubbling** [apps/api/apps/accounts/services/account_deletion.py:hard_delete] — Future migration adding a PROTECT FK would slip past the CI gate (M2M through-table). Catch ProtectedError explicitly, set `last_failure_code`, re-raise.
- [x] [Review][Patch] **P9 — `gave_up` audit row race double-write** [apps/api/apps/accounts/tasks.py:sweep_account_deletions] — Use `==` instead of `>=` for the cap check, or use `F("hard_delete_attempt_count") + 1` for atomic increment.
- [x] [Review][Patch] **P10 — DPO admin POST path doesn't re-check `has_perm`** [apps/api/apps/accounts/admin.py:_dpo_cancel_view] — Perm check happens at top of view; if revoked between GET and POST, the cancel still proceeds. Re-check `has_perm` at start of the POST branch.
- [x] [Review][Patch] **P11 — Public status endpoint returns 200 for orphan rows (user=NULL pre-hard_deleted)** [apps/api/apps/accounts/views.py:account_deletion_status_public] — Defensive: if `deletion.user is None AND deletion.hard_deleted_at is None`, return 404 to avoid leaking via manual DB poke.
- [x] [Review][Patch] **P12 — URL builder for cancel link doesn't use `urljoin` / `quote`** [apps/api/apps/accounts/services/account_deletion_email.py:_build_cancel_url] — Misconfigured `NEXT_PUBLIC_SITE_URL` with embedded path breaks the link silently. Replace string concat with `urljoin(site_url.rstrip("/") + "/", f"auth/cancel-deletion/{quote(token, safe='')}")`.
- [x] [Review][Patch] **P13 — `User.DoesNotExist` not caught when re-locking under FOR UPDATE in `cancel_deletion` / `hard_delete`** [apps/api/apps/accounts/services/account_deletion.py:1142, 1262] — Manual shell delete of user mid-operation surfaces as 500. Catch + raise `AccountDeletionAlreadyResolved`.
- [x] [Review][Patch] **P14 — `cancel_reason[:200]` truncation eats the DPO-id prefix when reason is long** [apps/api/apps/accounts/services/account_deletion.py:1131] — Truncate only the free-text portion, or compose the prefix outside the slice.
- [x] [Review][Patch] **P15 — `_terminate_user_sessions` bare `except Exception` hides decode failures** [apps/api/apps/accounts/services/account_deletion.py:95] — Replace with `log.warning("accounts.session_decode_failed", session_key=sess.session_key[:6])`.
- [x] [Review][Patch] **P16 — `_terminate_user_sessions` iterates ALL sessions including expired** [apps/api/apps/accounts/services/account_deletion.py:94] — Filter `Session.objects.filter(expire_date__gte=timezone.now())` to skip already-expired rows.
- [x] [Review][Patch] **P17 — `AccountDeletionNotFound` used for both "unknown token" and "no in-flight request for me"** [apps/api/apps/accounts/views.py:account_deletion_status_authenticated] — Different semantics confused as the same `type` URI. Add a `AccountDeletionNoPending` Problem (404) for the authenticated `/me/account-deletion/status/` case.
- [x] [Review][Patch] **P18 — AC1 response shape missing `status` + `detail` fields** [apps/api/apps/accounts/serializers.py:AccountDeletionRequestSerializer] — Spec AC1 example shows `{"id", "status": "pending_hard_delete", "requested_at", "hard_delete_after", "detail": "..."}`. Add a SerializerMethodField for `status` + a static `detail` (or use a dedicated 202-response serializer).
- [x] [Review][Patch] **P19 — Test `Session.objects.encode(...)` uses non-canonical Django API** [apps/api/apps/accounts/tests/test_account_deletion_service.py:test_request_deletion_terminates_active_sessions] — `encode` is on `SessionStore` (instance) in modern Django, not on the queryset manager. Use `SessionStore` directly, or rely on Django's `client.login()` to seed a real session.
- [x] [Review][Patch] **P20 — Test asserts `status_code in (401, 403)` — too permissive** [apps/api/apps/accounts/tests/test_account_deletion_views.py:test_post_account_deletion_unauthenticated_401] — Pin to the actual expected status (403 for SessionAuth without creds).
- [x] [Review][Patch] **P21 — Email templates render `{{ ...|date }}` in worker locale (likely en-US)** [apps/api/apps/accounts/services/account_deletion_email.py:_send] — Wrap `render_to_string` in `with translation.override("fr-FR")` so the date filter outputs French month names.
- [x] [Review][Patch] **P22 — CSRF token asymmetry between requestAccountDeletion (has it) and cancelAccountDeletion (doesn't)** [apps/web/src/lib/api/account-deletion.ts:cancelAccountDeletion] — Verify the public cancel endpoint is CSRF-exempt (no decorator visible in the diff); either add `csrfToken` to the cancel call for consistency, or add a comment documenting the exemption rationale.
- [x] [Review][Patch] **P23 — `_dpo_action_link` bare `except Exception` masks NoReverseMatch** [apps/api/apps/accounts/admin.py:_dpo_action_link] — Catch `NoReverseMatch` specifically, log a warning.
- [x] [Review][Patch] **P24 — `metadata_from` lambdas dereference `ret.id` / `ret.cancel_reason` without guarding for exception path** [apps/api/apps/accounts/services/account_deletion.py:955-958, 1057-1061] — On exception, `ret` is None and the lambda crashes inside the audit decorator. Add `if ret else "<unknown>"` guards (consistent with the `subject_from` pattern).

**Deferred (recorded in deferred-work.md):**

- [x] [Review][Defer] **W1 — Worker clock skew vs DB clock during sweep** — deferred, operational (NTP).
- [x] [Review][Defer] **W2 — Migration 0007 reverse drops table** — deferred, acceptable for a brand-new table; flagged for the partitioning story.
- [x] [Review][Defer] **W3 — Migration 0008 reverse leaves orphan `auth_permission` row** — deferred, low-impact.
- [x] [Review][Defer] **W4 — Non-DB session backend purge (Redis)** — deferred, already in deferred-work; surface again on the Redis-session migration story.
- [x] [Review][Defer] **W5 — `email__iexact` race vs CITEXT unique index** — deferred, pre-existing Story 1.3 / 1.4 known issue.
- [x] [Review][Defer] **W6 — Concurrent sweep workers without advisory lock** — deferred, Celery beat is singleton in MVP.
- [x] [Review][Defer] **W7 — Token rate-limit distributed brute-force at 256-bit entropy** — deferred, acceptable.
- [x] [Review][Defer] **W8 — CI gate misses M2M `through=` policies + env-specific apps** — deferred, Sprint 4+ refinement of `assert_user_cascade.py`.
- [x] [Review][Defer] **W9 — Frontend UX: warn user that email is unusable during the 30-day grace** — deferred, UX iteration.
- [x] [Review][Defer] **W10 — `password_hash_at_request` snapshot can drift if user rotates password** — deferred, spec §4.5 #4 acknowledges intentionally.

### Change Log — Review iteration (2026-05-25)

Addressed 31 code-review items (7 decisions + 24 patches). Test suite went from 140 → 145 tests passing (added 5 new tests for D1, D2, D3); ruff lint + format + assert_user_cascade.py all green.

**Resolved decisions:**
- **D1 (DPO superuser bypass)** — added strict `_has_explicit_dpo_perm()` helper in `apps/accounts/admin.py` querying `auth_permission` directly (bypassing Django's `has_perm` superuser shortcut). New test `test_dpo_cancel_refused_for_superuser_without_explicit_perm` proves it.
- **D2 (ConsentDialog bypassed + contentHash dropped)** — extended Story 1.14's `ConsentDialog` with `bodySlot` + `isAcceptDisabled` props (additive, no breaking changes). Refactored `DeleteAccountSection` to use the shared dialog with the password input in `bodySlot`. Threaded `contentHash` + `acceptedAt` from the dialog's `ConsentMeta` through the API client + serializer + service + audit metadata. New test `test_post_account_deletion_forwards_content_hash_to_audit_metadata` confirms the audit row carries the FR12 immutability proof.
- **D3 (anti-enumeration on public status endpoint)** — the public `GET /account-deletion/<token>/` now returns 404 for terminal states (`cancelled` / `hard_deleted` / `expired`) and for orphan `user=NULL` pre-hard-delete rows. Two new tests pin the behavior.
- **D4 (i18n namespace missing)** — deferred to Story 7.7 (i18n foundation) with explicit deferred-work entry.
- **D5 (login DELETED leak)** — kept the deliberate 403 leak (UX requirement); added `ThrottledLoginView` at `5/min/IP` to cap the enumeration window. Wired in `path_advisor/urls.py`.
- **D6 (record_audit silent None)** — added `_alert_on_silent_audit_failure()` helper that Sentry-flags every silent audit-write failure during `hard_delete` while keeping the Story 1.13 best-effort contract intact.
- **D7 (ULID "pseudonymized" claim)** — updated `docs/patterns/account-deletion.md` to clarify "pseudonymised *de facto by the absence of the originating User row*, NOT cryptographically". DPO sign-off recorded as deferred-work pre-production gate.

**Material patches:**
- **P1** — `docs/patterns/audit-events.md` actually updated this time (5 new event entries appended). Original Edit during T12 had silently no-op'd; verified `git diff` line count post-fix.
- **P2** — cancel endpoint per-IP rate-limit `30/h` → `5/h` (matches AC5).
- **P3** — `accounts.hard_delete_started` structlog event added at the top of `hard_delete`.
- **P4** — `cascade_row_counts` now reads from `Collector.data` + `Collector.fast_deletes` (SQL-only) + `Collector.field_updates` (SET_NULL planners). Verified shape against Django 5.1 source.
- **P5** — completion email now sent AFTER `user.delete()` (was before, racing the cascade rollback).
- **P6** — `s3.delete_objects` partial-failure `Errors[]` raises explicitly via `_raise_on_s3_partial_failure()`.
- **P7** — `prefix_template.format(...)` wrapped in `try/except KeyError` so a misconfigured registry entry skips the bucket instead of crashing the cascade.
- **P8** — `ProtectedError` from `Collector.collect` caught explicitly with audit + structlog before re-raising.
- **P9** — sweep task uses atomic `F("hard_delete_attempt_count") + 1` and `==` (not `>=`) for the give-up audit row.
- **P10** — DPO POST handler re-checks `_has_explicit_dpo_perm` (revoke-between-GET-and-POST window).
- **P11** — orphan public-status rows (`user=NULL` pre-hard-delete) return 404.
- **P12** — cancel URL uses `urljoin` + `quote(token, safe='')`.
- **P13** — `User.DoesNotExist` caught when re-locking under FOR UPDATE in both `cancel_deletion` and `hard_delete`.
- **P14** — `cancel_reason` truncation preserves the `dpo_override:<id>:` prefix (only the free-text portion is sliced).
- **P15** — `_terminate_user_sessions` bare except replaced with `log.warning(...)`.
- **P16** — session iterator filters `expire_date__gte=now()`.
- **P17** — `AccountDeletionNoPending` exception added; `/me/account-deletion/status/` now returns its dedicated Problem type.
- **P18** — `AccountDeletionRequestSerializer` exposes `status` + `detail` SerializerMethodFields (matches AC1 response shape).
- **P19** — session-encode test uses `SessionStore.create()` instead of the deprecated `Session.objects.encode(...)`.
- **P20** — `test_post_account_deletion_unauthenticated_401` asserts exact `401 + not-authenticated` Problem type.
- **P21** — email templates render under `translation.override("fr-FR")` so `{{ ...|date }}` outputs French month names regardless of worker locale.
- **P22** — comment added to `cancelAccountDeletion` documenting the deliberate CSRF asymmetry vs `requestAccountDeletion`.
- **P23** — `_dpo_action_link` catches `NoReverseMatch` only, with structlog warning.
- **P24** — `metadata_from` lambdas guard `ret is None` for exception-path safety + carry `content_hash`/`accepted_at` from kwargs.

**Test additions:** `test_dpo_cancel_refused_for_superuser_without_explicit_perm` (D1), `test_post_account_deletion_forwards_content_hash_to_audit_metadata` (D2), `test_post_account_deletion_rejects_invalid_content_hash` (D2), `test_get_public_status_returns_404_for_cancelled_row` (D3), `test_get_public_status_returns_404_for_expired_row` (D3); `_clear_ratelimit_cache` autouse fixture added.

**Final gates (2026-05-25):** pytest 145 passed / 1 skipped · ruff check clean · ruff format clean · assert_user_cascade.py green.
