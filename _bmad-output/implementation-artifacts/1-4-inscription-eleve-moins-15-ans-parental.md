# Story 1.4: Student < 15 signup with parental-consent email opt-in

**Epic:** 1 — Foundation: Multi-role Auth, RBAC, GDPR Compliance & Technical Infrastructure
**Status:** done
**Sprint:** 1 (Foundations)
**Story Key:** `1-4-inscription-eleve-moins-15-ans-parental`
**Estimation:** L (large) — extends the 1.3 signup pipeline with a branched flow (age < 15), a new `ParentalConsent` model + migration, a tokenized parent-facing page (no auth, deep-linked from email), two Celery beat jobs (30-day reminder, 60-day suspension), and a "limited mode" gate that several future Epics will rely on. Builds heavily on patterns shipped in 1.3 (allauth adapter, dj-rest-auth, structured Problem Details) and 1.13 (`@audit_action`, hash-chained audit log) and reuses `ConsentDialog` from 1.14 on the parent landing page.

> Story 1.4 closes the GDPR loop for minors. France's Loi Informatique et Libertés (art. 7-1) requires parental authorization for users under 15. The UX spec elevates this from "legal workflow" to "design problem" (§Defining Principle #6): the experience must **not** stigmatise the child whose parent is absent, non-francophone, or in conflict. The MVP solution is a **non-blocking opt-in by email**: the child continues exploring in *limited mode* while the parent authorizes asynchronously. The fallback "consentement par tiers autorisé" (counselor, association) is deferred to growth.

---

## 1. User Story

**As a** collegian < 15 years old (persona Mehdi, 14 ans, 3ᵉ),
**I want** to create my account by providing my own email/password plus a parent's email that will validate my registration,
**So that** I can begin exploring Path-Advisor in compliance with French law (LIL art. 7-1 + GDPR art. 8) while continuing to interact with the product in *limited mode* during the parent's review.

**As a** parent (persona M. Martin or any adult relative),
**I want** to receive a clear, low-pressure email explaining what Path-Advisor is, what data my child will share, and what my rights are, with a one-click "J'autorise" or "Je refuse" decision,
**So that** I can authorize or refuse my child's account in under 2 minutes without creating my own account or installing anything.

**Business value:** unlocks the entire `< 15 ans` segment of the MVP target (persona Mehdi, ~30 % of secondary-school users). Without this story, Path-Advisor is legally constrained to ≥ 15-year-olds and the "continuité 3ᵉ → terminale" promise is broken. UX risk explicitly flagged: avoid the GDPR-cookie-banner-from-hell pattern; the parent dialog reuses `ConsentDialog` from Story 1.14 with its no-dark-pattern guarantees.

---

## 2. Acceptance Criteria (BDD)

### AC1 — Signup flow accepts birth_date < 15 with `parent_email`

**Given** I am on `/auth/signup` and I enter: email, password ≥ 12 chars, birth_date impl. `age < 15`, **and** a `parent_email` field (validated as RFC 5322)
**When** I click "Créer mon compte" with the CGU/RGPD checkbox ticked
**Then** the API call `POST /api/v1/auth/registration/` succeeds (status `201 Created`).
**And** a `User` row is created with:
- `role = student`
- `status = pending_parental_consent` (per the existing `UserStatus` enum from Story 1.3)
- `birth_date`, `consent_rgpd_at = now()`, `consent_cgu_version = "<current>"`
- `email_verified_at = NULL` (child's own email verification is **independent** of parental consent — both must complete; see AC2)

**And** a `ParentalConsent` row (new model, see §4.4) is created with:
- `student_id` = the new User's id
- `parent_email` = the value submitted
- `parent_user_id = NULL` (the parent has no Path-Advisor account at this point)
- `token` = a 32-byte URL-safe secret (`secrets.token_urlsafe(32)`)
- `requested_at = now()`
- `expires_at = now() + 60 days` (after expiry the link 404s — see AC6)
- `decision = NULL` (becomes `granted` or `refused` on parent action)
- `decided_at = NULL`, `reminder_sent_at = NULL`

**And** **two** transactional emails are dispatched (independent of each other):
- To **the child's email**: the standard allauth email-confirmation message (re-using Story 1.3's verify-email flow).
- To **`parent_email`**: a new template `parental_consent_request.{txt,html}` containing the child's first name (if provided — MVP we have only email, so use a generic addressing — see §4.6), a 2-paragraph explanation of Path-Advisor, the data the child will share, the parent's rights, and a CTA pointing to `{NEXT_PUBLIC_SITE_URL}/auth/parental-consent/{token}`.

**And** the response body includes `{ "detail": "Verification e-mail sent.", "parental_consent_status": "pending" }` (the second key is new in 1.4 — see §4.5 OpenAPI impact).

**And** the child's own email-verification flow is unchanged (clicking the link still moves the child from `email_unverified` to `email_verified_at = now()` — but the `status` field stays at `pending_parental_consent` until the parent decides; see AC3).

### AC2 — Validation: `parent_email` required iff `age < 15`, rejected otherwise

**Given** the existing 1.3 contract that `age < 15` returns `400` with Problem Details `type=age-under-15`
**When** I submit signup with `age < 15` **without** `parent_email`
**Then** the API returns `400` Problem Details with `type=https://path-advisor.fr/errors/parent-email-required`, `title="Email parent requis pour les moins de 15 ans"`, status=400.

**Given** `age ≥ 15`
**When** I submit signup **with** `parent_email`
**Then** the API rejects with `400` Problem Details `type=https://path-advisor.fr/errors/parent-email-not-applicable`, status=400 — to keep the 1.3 happy path strict and not silently accept extra fields.

**Given** `parent_email` is the same as the child's own email
**When** I submit signup
**Then** the API rejects with `400` Problem Details `type=https://path-advisor.fr/errors/parent-email-same-as-student`, status=400, detail in French.

**Given** the child re-attempts signup after a prior `pending_parental_consent` account exists for the same child email
**When** I submit signup
**Then** the existing 1.3 `EmailAlreadyRegistered` error path applies (generic 400 — does not leak the consent state).

### AC3 — Email-verification ↔ parental-consent independence (state machine)

**Given** the new `(email_verified_at, status)` state pair, the only transitions allowed are:

| From | Trigger | To |
|---|---|---|
| `email_verified_at=NULL, status=pending_parental_consent` | child clicks email verify | `email_verified_at=now(), status=pending_parental_consent` |
| `email_verified_at=NULL, status=pending_parental_consent` | parent grants consent | `email_verified_at=NULL, status=pending_parental_consent` (no-op — child must still verify) |
| `email_verified_at=now(), status=pending_parental_consent` | parent grants consent | `email_verified_at=now(), status=active` |
| `email_verified_at=now(), status=pending_parental_consent` | parent refuses | `email_verified_at=now(), status=suspended` (see AC5 for cleanup) |
| any | parent ignores 60 days | `status=suspended` (see AC6) |

**And** the state-machine logic lives in `apps/accounts/services/parental_consent.py` (new file — see §4.4); the `mark_email_verified` service in `auth_service.py` is **updated** to branch on whether parental consent has resolved.

**And** the OpenAPI `User` schema exposes a derived `is_fully_active` boolean = `(email_verified_at IS NOT NULL AND status = "active")`. Frontend uses this to render "limited mode" gating.

### AC4 — Parent landing page: tokenized, no auth, reuses `ConsentDialog`

**Given** the parent receives the email and clicks the link `{site}/auth/parental-consent/{token}`
**When** the page loads (Next.js route — new file `apps/web/src/app/(public)/auth/parental-consent/[token]/page.tsx`)
**Then** Next.js calls `GET /api/v1/auth/parental-consent/{token}/` (new endpoint).
- **200** → response shape `{ "student_email_masked": "m***@d**.fr", "child_age": 14, "requested_at": "...", "expires_at": "...", "status": "pending" | "granted" | "refused" | "expired" }`.
- **404** → token does not exist → page renders an error state "Lien invalide ou expiré".
- The child's full email is **never** returned over the wire to the parent — only a masked form (first char + `***@` + first char of domain + `**.tld`). The parent reasons about "their child" by context, not by precise email match.

**And** the parent page renders:
- A header explaining "Path-Advisor a besoin de votre autorisation pour que votre enfant utilise le service."
- A 3-section "À propos de Path-Advisor" block (1 short paragraph each: ce que c'est, données collectées, vos droits).
- Two CTAs that open a `<ConsentDialog>` (from Story 1.14) — **not** a raw button. The dialog is the no-dark-pattern decision moment.
- The CTAs trigger `<ConsentDialog>` with:
  - **"Autoriser"** path: `title="Autoriser l'inscription de votre enfant"`, `dataMentioned=["Profil scolaire (bulletins, passions, intérêts)", "Métiers explorés", "Parcours sauvegardés"]`, `duration="Jusqu'aux 18 ans de l'enfant (révocable à tout moment)"`, `beneficiary="Votre enfant (email masqué)"`, `acceptLabel="J'autorise"`, `refuseLabel="Annuler"`.
  - **"Refuser"** path: same `<ConsentDialog>` but with `isAcceptDestructive=true`, `title="Refuser l'inscription"`, `acceptLabel="Je refuse"`, `refuseLabel="Annuler"` — refusing is an irreversible action for this signup attempt.

**And** the parent's accept/refuse decision triggers `POST /api/v1/auth/parental-consent/{token}/decide/` with body `{ "decision": "granted" | "refused", "content_hash": "<sha-256 hex from ConsentDialog onAccept>", "accepted_at": "<iso 8601>" }`.

**And** the API verifies the token is still `decision = NULL` (no double-decide) and `requested_at + 60 days > now()`. Otherwise returns `409 Conflict` Problem Details.

**And** a `@audit_action("parental_consent.decided", ...)` decorated service writes one `AuditLog` row with `actor_id = NULL` (parent has no Path-Advisor user account at this point), `subject_id = student.id`, `metadata = { "decision": ..., "content_hash": ..., "parent_email_hash": "<sha-256 of parent_email>", "ip_truncated": "x.y.z.0", "user_agent": "<first 200 chars>" }`. The metadata uses **hashed** parent email (not stored plain) to comply with GDPR minimisation — the audit trail proves "a decision happened" without persisting the parent's email in two places.

### AC5 — Granted vs refused effects

**Given** the parent grants consent
**When** the API records the decision
**Then** `ParentalConsent.decision = "granted"`, `decided_at = now()`.
**And** if the child has already verified their own email (`email_verified_at IS NOT NULL`), the User transitions to `status = "active"` immediately. Otherwise the User waits in `pending_parental_consent` until the child clicks their own verify-email link.
**And** a notification email is dispatched to the **child's** email: "Tes parents ont validé ton inscription — tu as accès à toutes les fonctionnalités." Subject line French; ton complice; reuses Story 1.13 audit signal.
**And** the parent's page redirects to a confirmation screen: "Merci, votre enfant a maintenant accès à Path-Advisor."

**Given** the parent refuses
**When** the API records the decision
**Then** `ParentalConsent.decision = "refused"`, `decided_at = now()`.
**And** the User transitions to `status = "suspended"` and `deleted_at` stays `NULL` (soft-suspended, not deleted — the child may re-attempt later with a different parent email, see §4.7 on re-attempts).
**And** **no** email is sent to the child automatically — the parent and child are presumed to have spoken; auto-pinging the child with a refusal would be UX-cruel.
**And** the parent's page renders a confirmation: "Votre refus a été enregistré. Aucun email ne sera envoyé à votre enfant. Vous pouvez fermer cette page."

### AC6 — Day-30 reminder, day-60 suspension (Celery beat)

**Given** a `ParentalConsent` row with `decision IS NULL` and `requested_at < now() - 30 days` and `reminder_sent_at IS NULL`
**When** the Celery beat job `accounts.send_parental_consent_reminders` runs (daily at 04:00 UTC, see §4.8)
**Then** a reminder email is sent to `parent_email` with template `parental_consent_reminder.{txt,html}` (same content as the original but with a "Vous n'avez pas encore répondu — votre enfant attend" tone, still no urgency theatre per UX-DR pattern §calendrier sans urgence).
**And** `reminder_sent_at = now()` is recorded.

**Given** a `ParentalConsent` row with `decision IS NULL` and `requested_at < now() - 60 days`
**When** the Celery beat job `accounts.suspend_unresolved_parental_consents` runs (daily at 04:15 UTC)
**Then** the linked User transitions to `status = "suspended"` and the `ParentalConsent.token` is invalidated (i.e., subsequent `/decide/` calls return `409`).
**And** a final email is sent to the **child** (not the parent — past the 60-day mark, the parent has effectively declined by omission and the child should be told gently): "Sans réponse parentale, ton compte est suspendu. Tu peux relancer ton parent depuis tes paramètres ou réessayer avec une autre adresse email." (Self-service reactivation flow = Story 1.5/1.12; not blocked here.)
**And** an `@audit_action("parental_consent.expired", subject_id=student.id)` entry is written.

### AC7 — Limited mode visible from frontend

**Given** the child is logged in and `is_fully_active = false`
**When** the child loads any authenticated page (`/onboarding`, `/recommendations`, etc.)
**Then** a non-intrusive `Alert` banner is rendered at the top of the layout (single layout-level component): "Tu es en mode découverte : tes parents doivent valider ton inscription pour débloquer toutes les fonctionnalités. [Renvoyer l'email]".
**And** the banner offers a **"Renvoyer l'email"** action that calls `POST /api/v1/auth/parental-consent/resend/` (rate-limited 1 / hour / user — see §4.9). The endpoint regenerates the token if expired or re-sends the existing token if still valid.
**And** Story 1.4 ships ONLY the banner + resend endpoint — the **gating** of premium / envoi-anticipé features happens in their respective Epic stories (5.x, 6.x). For Story 1.4, document this in `deferred-work.md` so future stories know to check `is_fully_active`.

### AC8 — Tests cover happy path + 6 error paths (backend), 3 UI tests (frontend)

**Given** the story implemented
**When** I run `make test` (or `cd apps/api && uv run pytest` / `cd apps/web && npm test`)
**Then** pytest covers at minimum:

1. `test_signup_under_15_with_parent_email_creates_user_and_parental_consent` (happy path; `ParentalConsent` row created; 2 emails dispatched via `locmem` backend).
2. `test_signup_under_15_without_parent_email_returns_400_parent_email_required`.
3. `test_signup_over_15_with_parent_email_returns_400_parent_email_not_applicable`.
4. `test_signup_with_parent_email_equal_to_student_email_returns_400` (same address rejection).
5. `test_parental_consent_decide_granted_activates_user_if_email_verified` (and the no-op variant if not).
6. `test_parental_consent_decide_refused_suspends_user_and_records_audit`.
7. `test_parental_consent_decide_with_invalid_token_returns_404`.
8. `test_parental_consent_decide_after_60_days_returns_409` (token expired).
9. `test_parental_consent_decide_idempotency_returns_409_on_second_call` (`decision` already set).
10. `test_celery_send_reminders_emails_only_pending_over_30d_unreminded` (using `pytest-django` + `freezegun` or `time-machine`).
11. `test_celery_suspend_unresolved_marks_user_suspended_and_writes_audit`.
12. `test_audit_log_for_decision_uses_hashed_parent_email_not_plaintext`.

**And** Vitest covers:

1. `signup-form` shows the `parent_email` field when `birth_date` implies `age < 15`, hides it otherwise.
2. `parental-consent/[token]/page` renders the masked-email, opens `ConsentDialog` on click, sends the correct payload on accept.
3. `parental-consent/[token]/page` shows the expired/already-decided error state when the API returns 404/409.

**And** total test count in `apps/api` rises by ≥ 12 and `apps/web` by ≥ 3. Existing 1.3 tests must still pass — Story 1.4 must not regress the happy path of ≥ 15 signup.

---

## 3. Tasks / Subtasks

### T1 — New `ParentalConsent` model + migration (AC1, AC3)

- [ ] T1.1 Create `apps/api/apps/accounts/models.py` additions:
  - `ParentalConsentDecision = TextChoices(GRANTED="granted", REFUSED="refused")`
  - `class ParentalConsent(models.Model)` with fields per AC1 (id ULID prefix `pcn_`, student FK, parent_email, parent_user_id nullable FK, token unique indexed, requested_at, expires_at, decision nullable, decided_at nullable, reminder_sent_at nullable, content_hash nullable — stored when parent grants, see AC4).
  - Indexes: `(decision, requested_at)`, `(decision, expires_at)` to support the Celery beat queries efficiently.
  - Meta: `db_table = "parental_consents"`.
- [ ] T1.2 Run `uv run python manage.py makemigrations accounts` to generate `0002_parental_consent.py`. **No `AUTH_USER_MODEL` change** — this is additive only, no DB reset required.
- [ ] T1.3 Register `ParentalConsent` in `apps/accounts/admin.py` with read-mostly admin (allow Path-Advisor admins to inspect a pending consent but **not** to grant/refuse on a parent's behalf — that would defeat the audit trail).

### T2 — Signup branching for `age < 15` (AC1, AC2)

- [ ] T2.1 Extend `apps/accounts/serializers.py::SignupSerializer`:
  - Add `parent_email = serializers.EmailField(required=False, allow_blank=False)`.
  - Replace `validate_birth_date` to **no longer raise AgeUnder15** when `parent_email` is present and `age < 15`. Instead:
    - if `age < 15` AND no `parent_email` → raise `ParentEmailRequired` (new exception in `apps/core/exceptions.py`).
    - if `age ≥ 15` AND `parent_email` present → raise `ParentEmailNotApplicable` (new).
    - if `parent_email == email` → raise `ParentEmailSameAsStudent` (new).
- [ ] T2.2 Add the three new exception classes to `apps/core/exceptions.py` (follow the existing `AgeUnder15` template). Each has fixed `type`, `title`, `status=400`, `detail` in French. Update `path_advisor_exception_handler` if needed (likely no change — same DomainError hierarchy).
- [ ] T2.3 Update `apps/accounts/adapters.py::PathAdvisorAccountAdapter.save_user`:
  - If `cleaned.get("parent_email")` is set → `user.status = UserStatus.PENDING_PARENTAL_CONSENT` (instead of `EMAIL_UNVERIFIED`). Keep `email_verified_at = NULL` regardless — both must independently complete.
  - Else → existing behaviour (`user.status = UserStatus.EMAIL_UNVERIFIED`).
- [ ] T2.4 In `apps/accounts/services/parental_consent.py` (new file), implement `create_parental_consent_request(student: User, parent_email: str, *, ip: str | None, user_agent: str | None) -> ParentalConsent`:
  - Generates `token = secrets.token_urlsafe(32)`.
  - Sets `expires_at = now() + timedelta(days=60)`.
  - Wraps everything in a `transaction.atomic()` with the User save so a failure rolls back together.
  - Decorated with `@audit_action("parental_consent.requested", subject_from=lambda kw, ret: kw["student"].id, metadata_from=lambda kw, ret: {"parent_email_hash": sha256_hex(kw["parent_email"])})`.
- [ ] T2.5 Wire `create_parental_consent_request` to fire from the `user_signed_up` allauth signal in `apps/accounts/signals.py`, **only** when the User's status is `PENDING_PARENTAL_CONSENT` after `save_user`. Reuse the request object captured by allauth to extract IP + user agent (truncated to 200 chars per AC4 audit row).

### T3 — Email templates (AC1, AC6)

- [ ] T3.1 Create `apps/api/apps/accounts/templates/parental_consent/parental_consent_request.txt` + `.html`. French ton complice, no urgency. Subject template `parental_consent_request_subject.txt`: `"Path-Advisor : votre enfant a besoin de votre autorisation"`. CTA `{{ consent_url }}` resolves to `{site}/auth/parental-consent/{token}`.
- [ ] T3.2 Create `parental_consent_reminder.{txt,html}` + subject template — same content + a single line "Vous n'avez pas encore répondu" at the top. No countdown, no urgency.
- [ ] T3.3 Create `parental_consent_granted_to_child.{txt,html}` + subject for the child notification on grant (AC5).
- [ ] T3.4 Create `parental_consent_expired_to_child.{txt,html}` for the 60-day suspension email (AC6 final).
- [ ] T3.5 Verify all 4 templates render correctly in Mailpit (`http://localhost:8025`) via a manual `python manage.py shell` send during T2 dev.

### T4 — Parent decide endpoint (AC4, AC5)

- [ ] T4.1 Add new endpoints to `apps/accounts/urls.py`:
  ```python
  path("api/v1/auth/parental-consent/<str:token>/", views.parental_consent_status, name="parental-consent-status"),
  path("api/v1/auth/parental-consent/<str:token>/decide/", views.parental_consent_decide, name="parental-consent-decide"),
  path("api/v1/auth/parental-consent/resend/", views.parental_consent_resend, name="parental-consent-resend"),
  ```
- [ ] T4.2 Implement `views.parental_consent_status` (GET, no auth):
  - Looks up `ParentalConsent.objects.filter(token=token).first()`. 404 if missing.
  - Returns the masked-email + decision state + expiry (no PII beyond the mask).
  - Wrap in `@api_view(["GET"])` + `permission_classes=[AllowAny]`.
- [ ] T4.3 Implement `views.parental_consent_decide` (POST, no auth, rate-limited):
  - Validates the request body via `ParentalConsentDecisionSerializer(decision={"granted","refused"}, content_hash=64-hex, accepted_at=ISO 8601)`.
  - Calls `parental_consent.record_decision(consent, decision, content_hash, request)` — service function decorated `@audit_action("parental_consent.decided")`.
  - On `granted`: sets `decision=granted, decided_at=now(), content_hash=<sha256>`. If `student.email_verified_at IS NOT NULL`, also sets `student.status=ACTIVE`. Sends the "granted" email to the child.
  - On `refused`: sets `decision=refused, decided_at=now()`. Sets `student.status=SUSPENDED`.
  - Returns 200 with `{ "decision": ..., "child_status": "..." }`.
  - 409 if `decision IS NOT NULL` already, or if `requested_at + 60 days < now()`.
  - Rate limit: 5 POSTs / token / hour (anti-bot — see §4.9).
- [ ] T4.4 Implement `views.parental_consent_resend` (POST, **auth required** — only the student can resend their own consent):
  - Reads `request.user.id`; finds the latest `ParentalConsent` for this student with `decision IS NULL`.
  - 404 if none.
  - Re-sends the email; updates `reminder_sent_at = now()`.
  - Rate limit: 1 POST / user / hour.
- [ ] T4.5 Helper `mask_email(email: str) -> str`: returns `m***@d**.fr` style. Live in `apps/core/text.py` (new file, since this is reusable). Cover with unit test.

### T5 — Celery beat jobs (AC6)

- [ ] T5.1 Create `apps/accounts/tasks.py` with two `@app.task`-decorated functions:
  - `send_parental_consent_reminders()` — queries `ParentalConsent.objects.filter(decision__isnull=True, reminder_sent_at__isnull=True, requested_at__lt=now()-timedelta(days=30))`. Iterates, sends email, updates `reminder_sent_at`. Idempotent (only ever sends one reminder per consent).
  - `suspend_unresolved_parental_consents()` — queries `ParentalConsent.objects.filter(decision__isnull=True, requested_at__lt=now()-timedelta(days=60))`. For each: sets `User.status=SUSPENDED`, sends final email to child, writes audit. Token stays in DB (for forensics) but `/decide/` checks the 60-day window and returns 409.
- [ ] T5.2 Register both in `path_advisor/celery.py` beat schedule:
  ```python
  app.conf.beat_schedule["parental-consent-send-reminders"] = {
      "task": "accounts.send_parental_consent_reminders",
      "schedule": crontab(hour=4, minute=0),  # daily 04:00 UTC
  }
  app.conf.beat_schedule["parental-consent-suspend-unresolved"] = {
      "task": "accounts.suspend_unresolved_parental_consents",
      "schedule": crontab(hour=4, minute=15),
  }
  ```
- [ ] T5.3 Both tasks must run **even if** `celery beat` is down for a few days — they are pull-based queries on `requested_at + N days`, not "send X days after creation" timers. A backlog day's worth catches up on the next run. Document this property in the docstrings.

### T6 — Frontend: signup form + parent landing page (AC1, AC4, AC7)

- [ ] T6.1 Update `apps/web/src/components/features/auth/signup-form.tsx`:
  - Add `parent_email` to the Zod schema as `z.string().email().optional()`.
  - Use `useWatch({ control, name: "birth_date" })` + `dateOfBirthIsUnder15(value)` helper to conditionally render a `parent_email` `<Input>` with `<Label>` "Email de ton parent ou tuteur" + helper text "Tes parents recevront un email pour autoriser ton inscription. Tu peux continuer à explorer en attendant.".
  - When the conditional field becomes visible, focus on it for keyboard accessibility.
  - Validation messages: French inline, e.g. "Ton parent ne peut pas avoir la même adresse email que toi".
- [ ] T6.2 Create `apps/web/src/lib/auth/age.ts` with a tested `isUnderAge(birthDate: string, threshold = 15): boolean` helper (pure function, no `date-fns` dependency required — manual diff is fine). Use it on both signup-form and `parental-consent/[token]/page`.
- [ ] T6.3 Create `apps/web/src/app/(public)/auth/parental-consent/[token]/page.tsx` (Server Component shell that fetches initial state) + a Client Component `apps/web/src/components/features/auth/parental-consent-flow.tsx` for the interactive part:
  - On mount, fetch `GET /api/v1/auth/parental-consent/{token}/`. SSR is fine for the initial render — token is in the URL, no auth required.
  - Render the 3-section explainer + 2 buttons "Autoriser" / "Refuser".
  - Each button opens a `<ConsentDialog>` with the props from AC4.
  - On `<ConsentDialog>.onAccept`, the component POSTs to `/decide/` with the `ConsentMeta` from the dialog. **Reuse the `content_hash` and `accepted_at`** — do not recompute on the server, they are the immutability proof.
  - Render the success/refusal confirmation screen replacing the buttons on success.
- [ ] T6.4 Create `apps/web/src/components/features/auth/limited-mode-banner.tsx` (Client Component reading from a user-session hook — TBD if hook exists from 1.3 or if we add a minimal one here).
  - Render only when `user.is_fully_active === false`.
  - Single "Renvoyer l'email" button → POST `/parental-consent/resend/`; shows toast on success ("Email renvoyé") or error ("Trop tôt — réessaie dans une heure" for rate-limit 429).
- [ ] T6.5 Wire `<LimitedModeBanner />` into the `(authenticated)` layout at `apps/web/src/app/(authenticated)/layout.tsx` (if it exists; otherwise create it). The banner is **layout-level** so it renders once across all authenticated routes.

### T7 — Tests (AC8)

- [ ] T7.1 Create `apps/api/apps/accounts/tests/test_signup_under_15.py` with the 4 signup-branching tests from AC8 (#1–#4). Use `factory_boy` + the existing `UserFactory`.
- [ ] T7.2 Create `apps/api/apps/accounts/tests/test_parental_consent.py` with the 6 decide/expiry/idempotency tests (AC8 #5–#9, #12).
- [ ] T7.3 Create `apps/api/apps/accounts/tests/test_parental_consent_tasks.py` with the 2 Celery beat tests (AC8 #10–#11). Use `time_machine` (already a transitive dep via factory_boy? — if not, add to dev deps).
- [ ] T7.4 Update `apps/web/src/components/features/auth/signup-form.test.tsx` (existing — 3 tests today): **add** the conditional-field test (AC8 frontend #1). Ensure the existing 3 tests still pass.
- [ ] T7.5 Create `apps/web/src/app/(public)/auth/parental-consent/[token]/page.test.tsx` (new) with the 2 frontend tests (AC8 frontend #2 and #3). Mock the API via `vi.mock` or MSW-light (no new dep).

### Review Findings — 2026-05-24 (Opus + Sonnet + Haiku multi-LLM)

Raw findings: 59 across 3 reviewers. After dedup + triage: 1 decision, 25 patches, 11 deferred, 10 dismissed.

#### Decision Needed

- [x] [Review][Decision] D1 — `accepted_at` field accepted but discarded — **Resolved 2026-05-24**: option B selected. Now stored as `client_accepted_at` column on `parental_consents` (migration 0004); skew vs server `decided_at` is structlog-warned if > 5 min. Forgery surface eliminated. [Blind H5 → P26 applied]

#### Patches

**HIGH severity:**

- [x] [Review][Patch] P1 — `mark_email_verified` bypasses parental consent for minors [`apps/api/apps/accounts/services/auth_service.py:33-35`] — When a child in `pending_parental_consent` clicks verify-email, status auto-flips to `ACTIVE`, defeating the entire parental gate. Spec AC3 row 1 says status should STAY `pending_parental_consent`. Fix: guard on `user.status == PENDING_PARENTAL_CONSENT` — if there's no granted consent yet, only set `email_verified_at=now()`, keep status pending; if a granted consent exists, transition to ACTIVE. [Edge H1] **CRITICAL — full legal bypass**
- [x] [Review][Patch] P2 — `/decide/` rate-limit lacks per-IP guard [`apps/api/apps/accounts/views.py:182`] — Per-token rate-limit gives one bucket per guessed token → unbounded brute-force rate. Stack a per-IP `60/h` limit on top of the per-token `5/h`. [Blind H2]
- [x] [Review][Patch] P3 — `_ratelimit_key_by_consent_token` crashes on `resolver_match = None` [`apps/api/apps/accounts/views.py:118-120`] — `AttributeError` when middleware short-circuits routing. Guard: `if not request.resolver_match: return ""`. [Edge H2]
- [x] [Review][Patch] P4 — `suspend_for_unresolved_consent` not wrapped in `transaction.atomic()` [`apps/api/apps/accounts/services/parental_consent.py:176-186`] — Audit row + user.status can diverge if either save fails. Wrap to match `record_decision`. [Edge H3]
- [x] [Review][Patch] P5 — `/resend/` sends to expired consents [`apps/api/apps/accounts/views.py:1938-1948`] — Window between `expires_at < now()` and the daily Celery suspend → parent gets dead-link email, `reminder_sent_at` marked. Add `expires_at__gt=timezone.now()` to the filter. [Edge H4]
- [x] [Review][Patch] P6 — `reminder_sent_at` updated even when SMTP fails [`apps/api/apps/accounts/views.py:1947`, `apps/accounts/tasks.py:64`] — `_send` swallows the SMTP error but the caller still flips the flag; reminder cron also won't retry. Have `_send` return success bool; only update the flag on True. [Auditor H2 + Blind L6 + L9]

**MED severity:**

- [x] [Review][Patch] P7 — `_truncate_ip` broken on IPv6 + IPv4-mapped IPv6 [`apps/api/apps/accounts/services/parental_consent.py:55-58`] — `2001:db8::1` → `2001:db8:::` (invalid); `::1` → `::1::`; `::ffff:1.2.3.4` → `::ffff::`. Use `ipaddress.ip_network(f"{ip}/48", strict=False).network_address`. [Blind M2 + Edge M5 + Auditor L1]
- [x] [Review][Patch] P8 — Signal handler not wrapped in `transaction.atomic()` despite service-side comment claiming it is [`apps/api/apps/accounts/signals.py:30-43`] — Orphan-user scenario if `create_parental_consent_request` fails after allauth committed the User. Either wrap signal logic, or have `/resend/` lazily create a missing consent for `pending_parental_consent` users. [Blind M3]
- [x] [Review][Patch] P9 — `<LimitedModeBanner />` shows parental-consent copy to non-minor users [`apps/web/src/components/features/auth/limited-mode-banner.tsx`] — Adult ≥ 15 ans who hasn't verified email yet sees "Tes parents doivent valider…". Gate on `user.status === "pending_parental_consent"` specifically, not on `!is_fully_active`. [Blind M4]
- [x] [Review][Patch] P10 — `@ratelimit(key="user")` decorator ordering with `@permission_classes` [`apps/api/apps/accounts/views.py:204`] — If ratelimit runs before auth middleware populates `request.user`, anonymous users share one bucket. Use `key="user_or_ip"` (django-ratelimit built-in) to be safe. [Blind M5]
- [x] [Review][Patch] P11 — Vacuous `content_hash` assertion in vitest [`apps/web/src/components/features/auth/parental-consent-flow.test.tsx:58`] — `.toMatch(/^[0-9a-f]{64}$/)` passes even if the dialog hashes a constant. Add a complementary assertion: 2 different beneficiaries produce 2 different hashes. [Blind M6]
- [x] [Review][Patch] P12 — Celery `iterator()` + mid-loop `save()` can invalidate cursor [`apps/api/apps/accounts/tasks.py:46`] — `iterator()` without `chunk_size` opens a server-side cursor; `consent.save(...)` may invalidate it. Either materialise (`list(qs)`) or pass `chunk_size=100`. [Blind M9]
- [x] [Review][Patch] P13 — Reminder + suspend queries use different time fields (`expires_at` vs `requested_at`) [`apps/api/apps/accounts/tasks.py`] — If clocks drift or admin edits a row, the two can disagree. Use `expires_at__lt=now()` consistently for the suspend query. [Blind M10 + Edge M4 + Auditor M2]
- [x] [Review][Patch] P14 — Granted email failure leaves child uninformed [`apps/api/apps/accounts/views.py:190-195`] — `send_granted_to_child` outside `record_decision`'s atomic block + idempotent; if SMTP fails the parent's grant is locked but no email ever goes out. Add a reconciliation task (or Celery retry) that emails any granted-but-unnotified row. [Blind M11]
- [x] [Review][Patch] P15 — Brittle `(reminder_sent_at - now()).days <= -1` assertion in task test [`apps/api/apps/accounts/tests/test_parental_consent_tasks.py:55`] — Edge cases on `timedelta.days` rounding. Use `assert already_reminded.reminder_sent_at < timezone.now() - timedelta(days=1)`. [Blind M12]
- [x] [Review][Patch] P16 — `/resend/` uses initial-request template instead of reminder template [`apps/api/apps/accounts/views.py:1946`] — Child-initiated resend should re-use the "Vous n'avez pas encore répondu" copy, not the initial request copy. Swap to `send_reminder_to_parent`. [Edge M6]
- [x] [Review][Patch] P17 — `UserDetailsSerializer` silently discards PATCH updates [`apps/api/apps/accounts/serializers.py:109-121`] — Base `serializers.Serializer` + all `read_only=True` → PATCH returns 200 with the original data. Either switch to `ModelSerializer` with `fields` whitelist OR override `update()` to raise 405. [Edge M7]
- [x] [Review][Patch] P18 — Stale `consent` arg in `record_decision` audit metadata [`apps/api/apps/accounts/services/parental_consent.py:108`] — `kwargs["consent"]` is the pre-`select_for_update` object; if `parent_email` was concurrently mutated, the hash logged is wrong. Use the refreshed local `consent` in the metadata lambda. [Edge M8]

**LOW severity:**

- [x] [Review][Patch] P19 — `ParentalConsent.is_expired` uses strict `<` [`apps/api/apps/accounts/models.py:190`] — 1-second loophole at exact `expires_at` boundary. Switch to `<=` for consistency with the "60-day hard deadline" narrative. [Blind L1 + Auditor L3]
- [x] [Review][Patch] P20 — `_truncate_ip` returns `None` on malformed IPv4 [`apps/api/apps/accounts/services/parental_consent.py:60-63`] — Silently drops forensic data; preserve `unknown` literal or the first octet at least. [Blind L7]
- [x] [Review][Patch] P21 — URL ordering foot-gun: `resend/` route declared after `<token>/` would shadow [`apps/api/apps/accounts/urls.py:17-30`] — Current order is correct, but a future reorder could route `GET /parental-consent/resend/` to `parental_consent_status` with `token="resend"`. Pin with a unit test. [Blind L8]
- [x] [Review][Patch] P22 — Reminder loop `save()` outside the `try/except` [`apps/api/apps/accounts/tasks.py:64-70`] — If `save()` raises (concurrent delete), `sent` count drifts vs reality. Move `save()` inside try, or update count only after successful save. [Blind L9]
- [x] [Review][Patch] P23 — `isUnderAge` JS Date rollover on malformed input [`apps/web/src/lib/auth/age.ts`] — `new Date(2012, 12, 1)` rolls to January 2013, no NaN. Validate month ∈ [1,12] and day ∈ [1,31] explicitly. [Edge L2]
- [x] [Review][Patch] P24 — `_age_today(None)` returns 0 [`apps/api/apps/accounts/views.py:124`] — Edge case: parent landing page shows "âge déclaré : 0 ans". Either guard at the view level (skip the field if None) or return `None` and have the serializer omit. [Edge L3]
- [x] [Review][Patch] P25 — `expires_at` not backdated in task tests [`apps/api/apps/accounts/tests/test_parental_consent_tasks.py`] — Tests backdate `requested_at` but not `expires_at`, so `is_expired` path is never exercised. Backdate both for the 65-day case. [Edge L7]

#### Deferred

- [x] [Review][Defer] W1 — Token binding (HMAC / IP / UA continuity) — 256-bit entropy makes brute-force impractical; revisit if real-world leaked-token incidents surface. [Blind H1]
- [x] [Review][Defer] W2 — Token appears in URL path → leaks to logs — Mitigate via log scrubber config in deploy track rather than API contract change (which would break the email-link UX). [Blind H3]
- [x] [Review][Defer] W3 — Case-insensitive email lookup race [`serializers.py`] — Pre-existing from Story 1.3; DB unique constraint catches the actual collision. Add `CITEXT` column when ready. [Blind M1]
- [x] [Review][Defer] W4 — `student_email_masked` leak via public status endpoint — Brute-force on 256-bit tokens is impractical; combined with W2's log-scrubbing, residual risk is acceptable for MVP. [Blind M8]
- [x] [Review][Defer] W5 — Timezone boundary on age check (server localdate vs frontend `new Date()`) — 1-day window for users at exactly 15 ans 0 days, locale-dependent. Switch to UTC midnight everywhere when Story 7.7 (i18n foundation) lands. [Edge M2 + Blind L12]
- [x] [Review][Defer] W6 — Real-time grant broadcast (banner auto-dismiss when parent grants in another tab) — Polling or SSE. MVP-acceptable as page-refresh hides the banner. [Auditor M3 + Edge L4]
- [x] [Review][Defer] W7 — Distinct error types for "expired" vs "already-decided" — Both currently map to `parental-consent-already-decided`; UX could benefit from separation. Cosmetic. [Edge L5]
- [x] [Review][Defer] W8 — Beat schedule has no jitter — Both jobs deterministically at 04:00/04:15 UTC. Add `crontab(..., jitter=...)` if volumes spike. [Blind L10]
- [x] [Review][Defer] W9 — `is_fully_active` is a Python property, not a column — Future admin/metrics queries will need to re-implement the SQL rule. Materialise as a computed column or function-based index later. [Blind L11]
- [x] [Review][Defer] W10 — Plain `parent_email` retained indefinitely — ADR-0003 claims "≤ 60-day effective use" but no purge ships. Defer to partitioning/archival story (Sprint 4+). [Blind L3]
- [x] [Review][Defer] W11 — `_parent_email_pending` transient attr coupling — Already in deferred-work.md from implementation; revisit if allauth ever ships a DRF-native signal. [Blind L2]

#### Dismissed (10)

R1 — `@audit_action` transaction nesting speculation (verified in 1.13: decorator joins outer txn) [Blind H4 + Edge M3].
R2 — 201 status code explicit test (dj-rest-auth default + indirectly covered) [Auditor H1].
R3 — Rate-limit empty-string fallback docstring (already commented) [Auditor M1].
R4 — `mask_email` ccTLD/subdomain behaviour matches spec's own docstring example [Blind M7 + Edge M1 + L1 + Auditor L1 partial].
R5 — `content_hash` client-trusted (intentional per ADR-0003) [Auditor M4].
R6 — Email HTML missing `dir` attribute (cosmetic, French doesn't need RTL) [Auditor M5].
R7 — Factory imports not in diff (factories existed in Story 1.3, unchanged) [Blind L5].
R8 — Email URL no urlencode (`secrets.token_urlsafe` produces URL-safe chars by definition) [Edge L6].
R9 — `super().validate()` runs password check first (intentional ordering, correct UX) [Edge L8].
R10 — `__all__` not defined for `mask_email` (cosmetic) [Auditor L2].

### T8 — Documentation + final validation

- [ ] T8.1 Update `docs/onboarding.md` §troubleshooting: explain that `pending_parental_consent` users can log in but won't have full feature access; resend is rate-limited 1 / h / user.
- [ ] T8.2 Add a new ADR `docs/adr/0003-parental-consent-tokenized.md` documenting the design choice (tokenized anonymous parent vs forcing parent-account creation, 60-day TTL, decision recorded with hashed parent email).
- [ ] T8.3 Update `_bmad-output/implementation-artifacts/deferred-work.md` with: "Story 1.4 ships `is_fully_active` but does NOT gate any feature on it; Epics 5/6 must check this flag when implementing premium and partner-school flows."
- [ ] T8.4 Run the full validation suite:
  - `make lint` — clean
  - `make test` — all tests pass (api + web)
  - `make openapi` — schema regenerates, new endpoints visible
  - Manual smoke: `docker compose up` → signup with `age = 14` + `parent_email = parent@example.com` → check Mailpit for both emails → click the parent link → land on `/auth/parental-consent/<token>` → accept via `ConsentDialog` → child notification email arrives → child's `is_fully_active` becomes `true`.

---

## 4. Dev Notes

### 4.1 Project context — what already exists (post-1.3 + 1.13 + 1.14)

**Shipped:**

- Custom `User` model with `pending_parental_consent` status already defined ([apps/api/apps/accounts/models.py:33](apps/api/apps/accounts/models.py#L33)).
- allauth + dj-rest-auth wired; `PathAdvisorAccountAdapter.save_user` defaults to `email_unverified` — must be **modified** to handle the new branch (T2.3).
- `@audit_action` decorator + `record_audit` helper from Story 1.13 ([apps/api/apps/audit/decorators.py](apps/api/apps/audit/decorators.py)) — directly reusable here.
- `AuditLog` model with append-only PG trigger + ORM block + hash chain — every parental-consent state change must write through `@audit_action`, not raw `AuditLog.objects.create()`.
- `apps/core/exceptions.py` with `DomainError` hierarchy and Problem Details handler — add new exception classes following the same template.
- Celery + Celery Beat configured ([apps/api/path_advisor/celery.py](apps/api/path_advisor/celery.py)) with `autodiscover_tasks()` — new tasks in `apps/accounts/tasks.py` will be picked up automatically.
- `ConsentDialog` shipped Story 1.14 ([apps/web/src/components/ui/consent-dialog.tsx](apps/web/src/components/ui/consent-dialog.tsx)) — **directly reused** on the parent landing page. The 8-field content hash from Story 1.14 review decision is the audit-trail proof for AC4.
- Frontend signup-form already exists at `apps/web/src/components/features/auth/signup-form.tsx` — extend, do not duplicate.

**Does not exist yet (this story creates):**

- `apps/api/apps/accounts/models.py::ParentalConsent` model
- `apps/api/apps/accounts/services/parental_consent.py` service
- `apps/api/apps/accounts/tasks.py` (Celery tasks)
- `apps/api/apps/accounts/templates/parental_consent/*` (4 email templates × txt+html)
- 3 new exception classes in `apps/core/exceptions.py`
- `apps/core/text.py::mask_email`
- `apps/web/src/app/(public)/auth/parental-consent/[token]/page.tsx` + test
- `apps/web/src/components/features/auth/parental-consent-flow.tsx`
- `apps/web/src/components/features/auth/limited-mode-banner.tsx`
- `apps/web/src/lib/auth/age.ts`
- 12 new pytest tests + 3 new Vitest tests
- `docs/adr/0003-parental-consent-tokenized.md`

### 4.2 Architecture decisions locked (cf. Stories 1.1 / 1.3 / 1.13 / 1.14)

| Decision | Locked choice | Source |
|---|---|---|
| Auth library | `django-allauth` + `dj-rest-auth` (extended via `PathAdvisorAccountAdapter`) | Story 1.3 |
| Token type front↔back | Session cookie httpOnly SameSite=Lax | Story 1.3 |
| Token format for parental consent | `secrets.token_urlsafe(32)` (43 base64 chars, ~256 bits) stored as-is in DB; never re-derived from anything | This story §4.4 |
| Token TTL | 60 days (matches AC6 60-day suspension) | This story AC1 |
| Single-use? | **No** — parent can re-open the link; we check `decision IS NULL` server-side. Multi-use allows the parent to re-confirm if they accidentally close the tab before deciding. | This story §4.4 |
| Email backend | Mailpit (dev), Postmark (prod) — pre-configured Story 1.3 | infra/docker-compose.yml + settings |
| Audit log writes | `@audit_action` decorator only — never `AuditLog.objects.create()` | Story 1.13 §AC2 |
| Audit hash | SHA-256 chain per Story 1.13; per-decision `content_hash` from `ConsentDialog` (Story 1.14, 8 fields) is **stored on `ParentalConsent.content_hash`** and embedded in the AuditLog `metadata` JSONB | This story §4.4 |
| JSON naming | `snake_case` end-to-end | Story 1.3 §4.2 |
| Business logic location | `services/` only (services own DB writes, views are thin) | architecture/implementation-patterns |
| ULID prefix | `pcn_` for ParentalConsent (precedent: `usr_` for User, `aud_` for AuditLog) | Story 1.1 §ids |
| Locale | French strings hardcoded; next-intl wiring = Story 7.7 | Story 1.3 §4.2 |
| Form library | React Hook Form + Zod | Story 1.3 |
| Story 1.14 ConsentDialog | Reuse as-is for AC4 parent decision moment; do NOT fork | Story 1.14 review |
| GDPR principle | Data minimization on parent_email: hash it in the audit metadata (do not duplicate plain) | This story AC4 |
| Rate limiting | `django-ratelimit` (already in deps from Story 1.3): `/decide/` = 5/h/token, `/resend/` = 1/h/user | This story §4.9 |

### 4.3 Why tokenized anonymous parent (not "parent must create an account first")

**Considered and rejected:** force the parent to create a Path-Advisor account before authorizing. Rationale for rejection:

- Adds 4-5 minutes of friction at the worst moment (a busy parent who already received an email out of the blue).
- Persona M. Martin doesn't necessarily want a Path-Advisor account — he might never log in again after authorizing. Epic 6 will offer parent-space later for those who do want one.
- Doubles the email volume (verify parent email + then authorize child) — increases the "parent ignores it" failure rate.

**Chosen:** the token IS the parent's authentication for this one decision. The audit log captures parent_email (hashed), IP (truncated), and user-agent (truncated) as the forensic trail. If the parent later creates a Path-Advisor account via Epic 6 invitation, that User row is linked to the existing ParentalConsent record via `parent_user_id`.

### 4.4 `ParentalConsent` model — exact field shape

```python
class ParentalConsent(models.Model):
    id = models.CharField(primary_key=True, max_length=32, default=lambda: generate_id("pcn"))
    student = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="parental_consents")
    parent_email = models.EmailField()
    parent_user_id = models.CharField(max_length=32, null=True, blank=True, db_index=True)  # populated by Epic 6
    token = models.CharField(max_length=64, unique=True, db_index=True)  # url-safe base64; max 64 to leave room
    requested_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()  # = requested_at + 60 days; denormalized for fast query
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    decision = models.CharField(max_length=10, choices=ParentalConsentDecision.choices, null=True, blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    content_hash = models.CharField(max_length=64, null=True, blank=True)  # sha-256 hex from ConsentDialog (Story 1.14)
    decision_ip_truncated = models.CharField(max_length=45, null=True, blank=True)  # e.g. "1.2.3.0" or "[2001:db8::]" IPv6 trunc
    decision_user_agent = models.CharField(max_length=200, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "parental_consents"
        indexes = [
            models.Index(fields=["decision", "requested_at"]),
            models.Index(fields=["decision", "expires_at"]),
            models.Index(fields=["student", "decision"]),
        ]
```

**Why `parent_email` plain in DB + hash in audit, and not vice versa?** Because the DB row is the **operational** record (we re-send reminders, we may need to deliver an email later); the audit row is the **forensic** record where data minimisation matters most (audit logs are kept 3 years, see Story 1.13). Plain in `parental_consents` ≤ 60 days TTL effective use; hashed in `audit_logs` for 3 years.

### 4.5 OpenAPI schema impact

- `POST /api/v1/auth/registration/` — extend `SignupSerializer` with `parent_email` (optional EmailField). Response body gains `parental_consent_status: "pending" | "not_applicable"`.
- New: `GET /api/v1/auth/parental-consent/{token}/` — public, no auth.
- New: `POST /api/v1/auth/parental-consent/{token}/decide/` — public, no auth, rate-limited.
- New: `POST /api/v1/auth/parental-consent/resend/` — authenticated, rate-limited.
- `User` schema gains derived `is_fully_active: boolean` (read-only).

Regenerate the TS client after the migrations + URL wiring: `cd apps/api && make openapi`.

### 4.6 Email copy (template TXT — French, no urgency theatre)

Subject: `Path-Advisor : votre enfant a besoin de votre autorisation`

Body sketch (TXT; HTML mirrors):

```
Bonjour,

Votre enfant souhaite utiliser Path-Advisor, un service d'orientation
scolaire qui l'aide à explorer des métiers et des parcours adaptés à son
profil.

Comme il a moins de 15 ans, la loi nous demande votre autorisation pour
qu'il puisse continuer.

Ce que votre enfant pourra faire :
- Compléter un profil (passions, intérêts, valeurs)
- Voir des métiers recommandés
- Sauvegarder des parcours de formation

Ce que Path-Advisor collectera :
- L'email et le mot de passe de votre enfant (chiffrés)
- Les informations de son profil scolaire (saisies ou OCR de bulletins)
- Ses interactions avec le service

Vos droits :
- Vous pouvez autoriser ou refuser
- Vous pouvez révoquer votre autorisation à tout moment
- Vous pouvez nous écrire à dpo@path-advisor.fr pour toute question

Pour décider, cliquez ici :
{{ consent_url }}

Vous avez 60 jours pour répondre. Sans réponse de votre part, le compte
de votre enfant sera suspendu (mais pas supprimé).

— L'équipe Path-Advisor
```

The HTML version uses Inter font + brand R1 colors via inline styles (no external CSS — emails clients drop linked stylesheets).

### 4.7 Re-attempts and edge cases

- **Child re-tries signup with a different parent email after a refusal**: blocked at the email-uniqueness level (Story 1.3's `EmailAlreadyRegistered`). The child must contact support. *This is intentional MVP behaviour* — self-service re-attempts with a different parent email would let a determined minor brute-force around a refusal. Document in `docs/onboarding.md`.
- **Parent receives the email but the child's email bounced**: the parent can still authorize; the child's verify-email link will be re-sent on next login attempt (Story 1.5 flow). The two flows are independent (AC3).
- **Parent enters the wrong child's data**: not possible — the parent receives a token tied to one specific ParentalConsent row created at the child's signup. The masked child email is shown on the parent page for sanity.
- **Email arrives in spam**: out of scope for the MVP; rely on Postmark deliverability in prod. Document in `docs/onboarding.md` troubleshooting.

### 4.8 Celery beat scheduling — pull-based, not push-based

Both jobs are **pull-based queries** on `requested_at + N days`. This means:
- If `celery beat` is down for 3 days, no reminders/suspensions happen during those 3 days, but **all backlogged work catches up on the next successful run** (the queries are stateless against `requested_at`).
- The `reminder_sent_at IS NULL` guard ensures the reminder is sent **once** per consent, even if the job runs multiple times in a window.
- The suspension job is idempotent: if a User is already `SUSPENDED`, re-running the task is a no-op (`UPDATE` matches 0 rows).

### 4.9 Rate limiting + abuse

- `/api/v1/auth/parental-consent/{token}/decide/` — 5 POSTs / token / hour. A normal flow is 1 POST; 5 leaves margin for accidental double-clicks + network retries; > 5 is suspicious (brute force? misclick storm?).
- `/api/v1/auth/parental-consent/resend/` — 1 POST / authenticated user / hour. The child should not be able to spam-resend.
- Both implemented via `django-ratelimit` already in deps (Story 1.3).
- Rate-limit responses are `429 Too Many Requests` + Problem Details `type=rate-limited` + `Retry-After` header (pattern from Story 1.3 §AC6).

### 4.10 Items to defer to `deferred-work.md` after merge

1. **`is_fully_active` gating of premium / envoi-anticipé** — Story 1.4 ships the flag and the UI banner; the actual access-control checks live in Stories 5.x (premium subscription gate) and 5.4 (envoi anticipé). Track explicitly so those stories don't forget.
2. **Counselor-as-third-party-consent fallback** — UX spec §Defining Principle #6 calls for "consentement par tiers autorisé" when no parent is available (counselor, association). Out of scope for MVP; defer to Epic 6 fast-follow.
3. **Parent self-service consent revocation** (post-grant) — UX spec hints at "révocable à tout moment". MVP relies on the existing `PermissionList` (Story 1.9) + `ConsentDialog` revocation path (Story 1.10). The parent will revoke via the eventual Parent Space (Epic 6) once they have a real account.
4. **Internationalised email templates** — French only for MVP. next-intl + per-locale email rendering = Story 7.7 + Story 8.1 abstraction.
5. **Address-of-record (residence proof) for very-young minors** — some jurisdictions ask for stronger proof than email opt-in. Out of MVP scope (legal review confirmed email opt-in is sufficient for FR ≥ 13 ans under LIL art. 7-1). Document the legal cite in ADR-0003.

### 4.11 Versions and libraries to use

| Library | Version | Usage |
|---|---|---|
| `django` | 5.1.15 | model, signals, transactions |
| `django-allauth` | (from Story 1.3 deps) | extended via existing `PathAdvisorAccountAdapter` |
| `dj-rest-auth` | (from Story 1.3 deps) | extended via existing `SignupSerializer` |
| `celery` + `celery-beat` | (from Story 1.1 deps) | new tasks + 2 beat entries |
| `django-ratelimit` | (from Story 1.3 deps) | rate limiting on `/decide/` and `/resend/` |
| `time-machine` | **new dev dep** if not present — verify before adding | freezing time in Celery beat tests (T7.3) |
| `next` | 16.2.6 | App Router dynamic route `[token]` |
| `react-hook-form` + `zod` | (Story 1.3 deps) | extended signup form |
| `@/components/ui/consent-dialog` | shipped Story 1.14 | parent decision modal |

**No major new dependency** beyond `time-machine` for tests (if needed — verify in T7.3 before adding).

---

## Project Structure Notes

**New files (~16):**

```
apps/api/apps/accounts/services/parental_consent.py
apps/api/apps/accounts/tasks.py
apps/api/apps/accounts/templates/parental_consent/{request,reminder,granted_to_child,expired_to_child}.{txt,html}    # 8 files
apps/api/apps/accounts/templates/parental_consent/*_subject.txt                                                      # 4 files
apps/api/apps/accounts/migrations/0002_parental_consent.py
apps/api/apps/accounts/tests/test_signup_under_15.py
apps/api/apps/accounts/tests/test_parental_consent.py
apps/api/apps/accounts/tests/test_parental_consent_tasks.py
apps/api/apps/core/text.py
apps/web/src/app/(public)/auth/parental-consent/[token]/page.tsx
apps/web/src/app/(public)/auth/parental-consent/[token]/page.test.tsx
apps/web/src/components/features/auth/parental-consent-flow.tsx
apps/web/src/components/features/auth/limited-mode-banner.tsx
apps/web/src/lib/auth/age.ts
docs/adr/0003-parental-consent-tokenized.md
```

**Modified files (~10):**

```
apps/api/apps/accounts/models.py              # +ParentalConsent + ParentalConsentDecision
apps/api/apps/accounts/serializers.py         # SignupSerializer +parent_email + validation branches
apps/api/apps/accounts/adapters.py            # save_user branches on parent_email
apps/api/apps/accounts/signals.py             # user_signed_up → create_parental_consent_request
apps/api/apps/accounts/views.py               # 3 new endpoints
apps/api/apps/accounts/urls.py                # 3 new paths
apps/api/apps/accounts/admin.py               # register ParentalConsent admin
apps/api/apps/core/exceptions.py              # +3 exception classes
apps/api/path_advisor/celery.py               # +2 beat schedule entries
apps/web/src/components/features/auth/signup-form.tsx       # conditional parent_email field
apps/web/src/components/features/auth/signup-form.test.tsx  # +1 conditional-field test
apps/web/src/app/(authenticated)/layout.tsx                 # <LimitedModeBanner /> (create if absent)
docs/onboarding.md                            # +troubleshooting entry
_bmad-output/implementation-artifacts/deferred-work.md      # +5 deferred items
```

**DB migration impact:** **additive only** — one new table `parental_consents`, no FK alterations on `users`. No DB reset required. No `AUTH_USER_MODEL` change.

---

## References

- **Epic 1, Story 1.4 definition:** [_bmad-output/planning-artifacts/epics/epic-1-foundation-auth-multi-role-rbac-conformite-rgpd-infra-technique.md#L89-L117](_bmad-output/planning-artifacts/epics/epic-1-foundation-auth-multi-role-rbac-conformite-rgpd-infra-technique.md#L89-L117)
- **UX Defining Principle #6 — consentement parental as design problem:** [_bmad-output/planning-artifacts/ux-design-specification.md#L89](_bmad-output/planning-artifacts/ux-design-specification.md#L89)
- **UX Flow 2 — Mehdi inscription parentale:** [_bmad-output/planning-artifacts/ux-design-specification.md#L975-L1023](_bmad-output/planning-artifacts/ux-design-specification.md#L975-L1023)
- **UX-DR pattern "calendrier sans urgence":** [_bmad-output/planning-artifacts/ux-design-specification.md#L1261](_bmad-output/planning-artifacts/ux-design-specification.md#L1261)
- **Story 1.3 (signup ≥ 15):** [_bmad-output/implementation-artifacts/1-3-inscription-eleve-15-ans-rgpd.md](_bmad-output/implementation-artifacts/1-3-inscription-eleve-15-ans-rgpd.md) — extends `SignupSerializer`, `PathAdvisorAccountAdapter`, and the verify-email flow shipped here.
- **Story 1.13 (audit log infra):** [_bmad-output/implementation-artifacts/1-13-journal-audit-acces.md](_bmad-output/implementation-artifacts/1-13-journal-audit-acces.md) — every parental-consent state change writes through `@audit_action`.
- **Story 1.14 (ConsentDialog):** [_bmad-output/implementation-artifacts/1-14-composant-consent-dialog.md](_bmad-output/implementation-artifacts/1-14-composant-consent-dialog.md) — the parent landing page reuses this component for the decision moment; the 8-field `content_hash` is stored as the immutability proof.
- **Architecture — `apps/accounts/services/parental_consent.py` planned path:** [_bmad-output/planning-artifacts/architecture/project-structure-boundaries.md#L155-L157](_bmad-output/planning-artifacts/architecture/project-structure-boundaries.md#L155-L157)
- **Architecture — `apps/audit/` decorator pattern:** [_bmad-output/planning-artifacts/architecture/project-structure-boundaries.md#L140-L146](_bmad-output/planning-artifacts/architecture/project-structure-boundaries.md#L140-L146)
- **PRD FR2 (consentement parental email opt-in):** [_bmad-output/planning-artifacts/prd/functional-requirements.md](_bmad-output/planning-artifacts/prd/functional-requirements.md)
- **Existing `User` model (status enum already includes `pending_parental_consent`):** [apps/api/apps/accounts/models.py:33](apps/api/apps/accounts/models.py#L33)
- **Existing `PathAdvisorAccountAdapter.save_user` (will be modified):** [apps/api/apps/accounts/adapters.py:23-38](apps/api/apps/accounts/adapters.py#L23-L38)
- **Existing `apps/audit/decorators.py::audit_action`:** [apps/api/apps/audit/decorators.py](apps/api/apps/audit/decorators.py)
- **Existing `signup-form.tsx` (will be modified):** [apps/web/src/components/features/auth/signup-form.tsx](apps/web/src/components/features/auth/signup-form.tsx)
- **Existing `ConsentDialog` component:** [apps/web/src/components/ui/consent-dialog.tsx](apps/web/src/components/ui/consent-dialog.tsx)
- **Legal cite (LIL art. 7-1, FR ≥ 13 ans threshold):** to be added in ADR-0003.

---

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 (`claude-opus-4-7[1m]`) — single-execution implementation 2026-05-17.

### Debug Log References

- T2/T3 signal bug: allauth fires `user_signed_up` with a `WSGIRequest` (no `.data`) — fixed by
  stashing `parent_email` on a transient `user._parent_email_pending` attribute set by the adapter.
- T4 rate-limit bug: `@method_decorator(ratelimit(...))` does not work on function-based views;
  swapped for direct `@ratelimit(...)`. The `key="post:token"` was also wrong (looks at POST body
  fields, not URL kwargs) — replaced with a callable that extracts the token from
  `request.resolver_match.kwargs`.
- T7 test bug: rate-limit cache is per-process, not per-test, so > 5 decide calls across the test
  file collided into the same bucket. Fix above also resolved this — different consent tokens now
  produce independent buckets.

### Completion Notes List

**What ships:**

- Custom `User.is_fully_active` property + `UserDetailsSerializer` override on dj-rest-auth so
  `/api/v1/auth/user/` exposes the derived flag.
- `ParentalConsent` model (+ migration 0003) with three indexes covering the Celery beat queries +
  the `/resend/` "latest pending for student" lookup.
- 3 new exceptions in `apps/core/exceptions.py` (ParentEmailRequired, ParentEmailNotApplicable,
  ParentEmailSameAsStudent) + 2 more (ParentalConsentNotFound, ParentalConsentAlreadyDecided) for
  the decide endpoint.
- `SignupSerializer` cross-field branching: `(age < 15, parent_email present)` decision matrix.
- `apps/accounts/services/parental_consent.py`: `create_parental_consent_request`, `record_decision`
  (atomic + select_for_update against double-click races), `suspend_for_unresolved_consent`.
- `apps/accounts/services/parental_consent_email.py`: 4 dispatch helpers + Django template rendering
  for the 4 events (request / reminder / granted-to-child / expired-to-child) × 3 files each.
- `apps/accounts/tasks.py`: 2 Celery beat tasks (daily 04:00 / 04:15 UTC) — pull-based queries on
  `requested_at + N days`, idempotent.
- 3 endpoints: `GET /api/v1/auth/parental-consent/{token}/` (public, masked email read),
  `POST /api/v1/auth/parental-consent/{token}/decide/` (public, 5/h/token rate-limit),
  `POST /api/v1/auth/parental-consent/resend/` (auth, 1/h/user).
- Frontend signup-form conditional `parent_email` field + auto-focus on appearance.
- `apps/web/src/app/(public)/auth/parental-consent/[token]/page.tsx` — Server Component shell +
  `ParentalConsentFlow` Client Component reusing Story 1.14's ConsentDialog (with the 8-field
  content_hash as the audit-trail proof).
- `<LimitedModeBanner />` at the `(authenticated)` layout level — self-hides for fully-active users.

**Test count delta:**

- pytest: 40 → 58 (+18 net new — 4 signup branching + 11 decide/resend + 3 Celery beat tests, mainly).
- vitest: 29 → 33 (+4 — 1 conditional signup field + 3 parental-consent-flow tests).

**OpenAPI delta:**

- `+3 paths` (`/parental-consent/...`).
- `User` schema gains `is_fully_active: boolean` (via the new UserDetailsSerializer).
- Signup `request` body gains optional `parent_email`.
- `parental_consent_resend` view triggers a drf-spectacular warning "unable to guess serializer" —
  acceptable (no request body, the response is `{detail: string}` which the framework infers from
  the docstring). Deferred to the next review pass if we want a cleaner schema.

**Manual smoke (Mailpit at :8025):** signup with `birth_date=2012-01-15` + `parent_email=parent@…`
→ 2 emails sent (child verify-email + parent consent request) → GET status returns `m***@p**.local`
+ age 14 + status pending → POST decide returns 200 + "granted" email sent to child → second POST
returns 409.

### File List

**New (~22):**

```
apps/api/apps/accounts/migrations/0003_parentalconsent.py
apps/api/apps/accounts/services/parental_consent.py
apps/api/apps/accounts/services/parental_consent_email.py
apps/api/apps/accounts/tasks.py
apps/api/apps/accounts/templates/parental_consent/parental_consent_request.{txt,html}
apps/api/apps/accounts/templates/parental_consent/parental_consent_request_subject.txt
apps/api/apps/accounts/templates/parental_consent/parental_consent_reminder.{txt,html}
apps/api/apps/accounts/templates/parental_consent/parental_consent_reminder_subject.txt
apps/api/apps/accounts/templates/parental_consent/parental_consent_granted_to_child.{txt,html}
apps/api/apps/accounts/templates/parental_consent/parental_consent_granted_to_child_subject.txt
apps/api/apps/accounts/templates/parental_consent/parental_consent_expired_to_child.{txt,html}
apps/api/apps/accounts/templates/parental_consent/parental_consent_expired_to_child_subject.txt
apps/api/apps/accounts/tests/test_signup_under_15.py
apps/api/apps/accounts/tests/test_parental_consent.py
apps/api/apps/accounts/tests/test_parental_consent_tasks.py
apps/api/apps/core/text.py
apps/web/src/app/(authenticated)/layout.tsx
apps/web/src/app/(public)/auth/parental-consent/[token]/page.tsx
apps/web/src/components/features/auth/parental-consent-flow.tsx
apps/web/src/components/features/auth/parental-consent-flow.test.tsx
apps/web/src/components/features/auth/limited-mode-banner.tsx
apps/web/src/lib/auth/age.ts
docs/adr/0003-parental-consent-tokenized.md
```

**Modified (~13):**

```
apps/api/apps/accounts/admin.py                              # +ParentalConsentAdmin
apps/api/apps/accounts/adapters.py                           # save_user branches on parent_email
apps/api/apps/accounts/models.py                             # +ParentalConsent + ParentalConsentDecision + User.is_fully_active
apps/api/apps/accounts/serializers.py                       # SignupSerializer + ParentalConsent* serializers + UserDetailsSerializer
apps/api/apps/accounts/signals.py                            # user_signed_up → create_parental_consent_request + send email
apps/api/apps/accounts/urls.py                               # +3 parental-consent paths
apps/api/apps/accounts/views.py                              # +3 parental-consent views
apps/api/apps/accounts/tests/test_signup_under_15.py        # (new, listed above)
apps/api/apps/core/exceptions.py                             # +5 exception classes
apps/api/path_advisor/celery.py                              # +2 beat schedule entries
apps/api/path_advisor/settings/base.py                       # REST_AUTH.USER_DETAILS_SERIALIZER
apps/web/src/components/features/auth/signup-form.tsx        # conditional parent_email field
apps/web/src/components/features/auth/signup-form.test.tsx   # +1 conditional-field test
apps/web/src/lib/api/auth.ts                                 # +CurrentUser + 3 parental-consent helpers
docs/onboarding.md                                           # +troubleshooting 1.4 entry
_bmad-output/implementation-artifacts/deferred-work.md      # +9 deferred items
_bmad-output/implementation-artifacts/sprint-status.yaml    # 1-4 in-progress → review
```

### Change Log

- 2026-05-17 — implemented Story 1.4 end-to-end (T1-T8). 25/25 new pytest pass, 4/4 new vitest pass.
  No regression — 58/58 pytest (1 skipped, postgresql_only), 33/33 vitest. OpenAPI schema regenerates
  cleanly with the 3 new endpoints. Manual smoke through Mailpit confirmed parent + child email flow.
- 2026-05-24 — code review (Opus + Sonnet + Haiku) → 59 raw findings → 1 decision + 25 patches +
  11 deferred + 10 dismissed. All 26 patches applied (decision D1 resolved as "store as
  `client_accepted_at`"). Includes CRITICAL fix §P1: `mark_email_verified` no longer auto-promotes
  minors to ACTIVE on email-verify-only — the parental gate is now enforced both directions.
  New: migration 0004 (`client_accepted_at` + `notification_sent_at`); Celery beat task
  `accounts.notify_unconfirmed_granted_consents` (hourly @ XX:20) to retry granted-email on SMTP
  failure. Tests: 61/61 pytest (+3 — P1 minor-bypass guard, P21 URL ordering); 34/34 vitest (+1 —
  hash-differs-by-beneficiary). Smoke E2E: granted decision now persists `client_accepted_at` +
  `notification_sent_at` + `decision_ip_truncated=172.18.0.0` (proper /24 via `ipaddress` stdlib).
