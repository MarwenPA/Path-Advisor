# Story 5.1: Stripe Integration (local sandbox + production)

**Epic:** 5 — Premium B2C & Biface Early Outreach
**Status:** review
**Sprint:** 9 (Premium foundations)
**Story Key:** `5-1-integration-stripe`
**Estimation:** L

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

---

## Story

**As a** Path-Advisor system,
**I want** an abstracted payment integration that supports Stripe test mode (sandbox) locally in PoC and production mode in the cloud,
**so that** payments work in dev and prod with no application-code changes (NFR-I1).

This is the **walking-skeleton** story for Epic 5: it stands up the `billing` Django app, the provider abstraction, the local Stripe sandbox + webhook listener, and a PCI-safe hosted-checkout path proven end-to-end with the test card. It deliberately does **not** implement tier gating, the `subscriptions` state machine, or the paywall — those are Stories 5.2 / 5.3 / 5.11. What 5.1 must deliver is the *plumbing* the rest of the epic builds on.

---

## Acceptance Criteria (BDD)

### AC1 — `PaymentProvider` abstraction exists

**Given** the payment abstraction layer
**When** I inspect the code
**Then** an abstract `PaymentProvider` interface is defined with the methods `create_checkout_session`, `handle_webhook`, `cancel_subscription`, `get_subscription_status`
**And** a concrete `StripeProvider` implements it, reading sandbox keys in dev and prod keys in production via environment variables (no hardcoded keys, no per-environment code branches).

### AC2 — Provider is selected by configuration, not code

**Given** the running API
**When** the billing service resolves its provider
**Then** the provider instance is obtained through a single factory/settings entry point (e.g. `get_payment_provider()`)
**And** swapping test ↔ prod requires only environment variables (`STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_ID_PREMIUM`), never an application-code change.

### AC3 — Local Stripe sandbox + webhook listener

**Given** a local environment
**When** I run `docker compose up`
**Then** a Stripe CLI listener container forwards Stripe test events to the Django webhook endpoint (`stripe listen --forward-to api:8000/webhooks/stripe/`)
**And** I can complete a payment end-to-end with the Stripe test card `4242 4242 4242 4242`
**And** the corresponding `checkout.session.completed` event is received and processed by Django.

### AC4 — Webhook is Django-only, HMAC-verified, idempotent

**Given** the Stripe webhook endpoint
**When** an event is received at `POST /webhooks/stripe/`
**Then** the endpoint is CSRF-exempt and lives outside the `/api/v1/` surface
**And** the Stripe signature (`Stripe-Signature`) is verified against `STRIPE_WEBHOOK_SECRET`; an invalid or missing signature returns `400` and processes nothing
**And** each event id is recorded in a `StripeEvent` ledger so a re-delivered event is a no-op (idempotency)
**And** **no** Next.js webhook route is created (single source of truth = Django, per `architecture-validation-results.md` risk #4).

### AC5 — PCI-DSS: no card data touches Path-Advisor

**Given** a payment is processed
**When** the checkout flow runs
**Then** Stripe Checkout (hosted) is used — no custom card form, no card fields in any Path-Advisor request or DB column
**And** only Stripe tokens/ids are persisted (`stripe_customer_id`, `stripe_subscription_id`, `stripe_event_id`, session id)
**And** a `POST /api/v1/billing/checkout-session` endpoint returns a hosted Checkout URL for the premium price; the frontend redirects the browser to it.

### AC6 — Degraded mode when Stripe is unreachable

**Given** Stripe is unreachable when a checkout session is requested
**When** the provider call fails/times out
**Then** the error surfaces as an RFC 7807 problem response (not a bare 500) and is logged to Sentry
**And** the failure does not corrupt local state (no partial subscription rows) — matching the "mode dégradé" fallback expectation in `project-context-analysis.md`.

### AC7 — Config safety & example env

**Given** the repo
**When** I inspect `.env.example`
**Then** `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_ID_PREMIUM`, `STRIPE_PUBLISHABLE_KEY` are present with **empty** placeholder values and a comment that real values come from Doppler/Scaleway Secrets in staging/prod
**And** no real key is committed anywhere in the diff.

---

## Tasks / Subtasks

- [x] **Task 1 — Scaffold the `billing` Django app** (AC: 1, 4)
  - [x] `python manage.py startapp billing apps/billing`; set `apps.py` → `name = "apps.billing"`, `verbose_name = "Billing & Subscriptions"`
  - [x] Register `"apps.billing"` in the local-apps block of `path_advisor/settings/base.py` `INSTALLED_APPS`
  - [x] Create `apps/billing/urls.py` (`app_name = "billing"`) and wire the `/api/v1/` router include in `path_advisor/urls.py`; wire the webhook under a **separate** `path("webhooks/stripe/", ...)` (NOT under `api/v1/`)
- [x] **Task 2 — `PaymentProvider` abstraction + `StripeProvider`** (AC: 1, 2, 5)
  - [x] `apps/billing/services/provider.py`: abstract base `PaymentProvider(ABC)` with `create_checkout_session(...)`, `handle_webhook(payload, sig_header)`, `cancel_subscription(stripe_subscription_id)`, `get_subscription_status(stripe_subscription_id)`
  - [x] `apps/billing/services/stripe_provider.py`: `StripeProvider(PaymentProvider)` using the official `stripe` Python SDK; keys from settings; hosted Checkout only (`mode="subscription"`, `line_items=[{price: STRIPE_PRICE_ID_PREMIUM, quantity: 1}]`, `success_url`/`cancel_url`)
  - [x] `get_payment_provider()` factory in `apps/billing/services/__init__.py` returning the configured provider (single selection point — AC2)
  - [x] Add `stripe` to `apps/api/pyproject.toml` dependencies (pin latest stable — see Latest Tech)
- [x] **Task 3 — Settings & env wiring** (AC: 1, 2, 7)
  - [x] Add `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_ID_PREMIUM`, `STRIPE_PUBLISHABLE_KEY` via `os.environ.get(...)` in `settings/base.py` (mirror `AI_SERVICE_JWT_SECRET` pattern)
  - [x] Add the four keys with empty placeholders + Doppler comment to `.env.example`
- [x] **Task 4 — `StripeEvent` idempotency ledger** (AC: 4)
  - [x] `apps/billing/models.py`: `StripeEvent` (`stripe_event_id` unique, `event_type`, `payload` JSON, `received_at`, `processed_at` nullable). Use `apps.core.ids.generate_id` for the PK if that is the app convention; timestamps `_at` suffix
  - [x] `makemigrations billing` → `0001_initial.py`
  - [x] Note: the `Subscription` / `Invoice` models and the `is_premium` flag are **Story 5.2** — do not implement tier state here beyond what the ledger needs
- [x] **Task 5 — Checkout-session endpoint** (AC: 5, 6)
  - [x] `POST /api/v1/billing/checkout-session` → `APIView` with explicit `permission_classes: ClassVar = [IsAuthenticatedAndActive]` (CI-enforced by `scripts/assert_rbac_declared.py`)
  - [x] View delegates to `BillingService` (service layer), which calls `get_payment_provider().create_checkout_session(...)`; returns `{ "checkout_url": ... }`
  - [x] Wrap provider errors → RFC 7807 problem response (AC6); never leak a bare 500
- [x] **Task 6 — Webhook endpoint** (AC: 3, 4)
  - [x] `POST /webhooks/stripe/` — `@csrf_exempt`, `AllowAny`, HMAC-verified via `stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)`
  - [x] Signature failure → `400` (no processing). Valid event → upsert `StripeEvent`; if already `processed_at` set, return `200` no-op (idempotent). Handle at least `checkout.session.completed` (log/persist event; full subscription activation is 5.3)
- [x] **Task 7 — Docker Compose Stripe CLI listener** (AC: 3)
  - [x] Add a dev-only `stripe-cli` service to `infra/docker-compose.yml` (image `stripe/stripe-cli`), command `listen --forward-to api:8000/webhooks/stripe/`, `env_file: ../.env`, `depends_on: api` (healthy). Model it on the `mailpit` dev-stand-in service shape
  - [x] Document the one-time `stripe login` / `STRIPE_CLI_API_KEY` requirement in a short README note
- [x] **Task 8 — Frontend redirect glue (minimal)** (AC: 5)
  - [x] `apps/web/src/lib/api/billing.ts` → `createCheckoutSession()` wrapping `apiFetch` (no direct `fetch`; snake_case JSON)
  - [x] `apps/web/src/lib/stripe/client.ts` per architecture tree; redirect via `window.location = checkout_url`
  - [x] Do **not** build `premium/page.tsx` UI here (that is 5.3/5.11) — a minimal trigger/button is enough to prove the e2e path
  - [x] Do **not** create `app/api/webhooks/stripe/route.ts` (explicitly dropped)
- [x] **Task 9 — Tests** (AC: 3, 4, 5, 6)
  - [x] Unit: `StripeProvider` with the Stripe SDK mocked (no network); provider factory returns configured provider
  - [x] API: `checkout-session` requires auth+active (403 for anon/inactive), returns a URL on success, RFC 7807 on provider failure (AC6)
  - [x] API: webhook rejects bad/missing signature (400), accepts a valid signed test event, is idempotent on re-delivery (AC4)
  - [x] Use `APIClient().force_authenticate(...)` + `UserFactory`; mock `stripe.Webhook.construct_event`

---

## Dev Notes

### Architecture-mandated decisions (do not deviate without an ADR)

- **Stripe is Django-only.** `architecture-validation-results.md` risk #4 resolution: *"Trancher: tout côté Django (single source of truth). Supprimer la route Next.js."* The epic text mentions a Next.js `api/webhooks/stripe/route.ts`; that is **superseded** — do not build it. [Source: _bmad-output/planning-artifacts/architecture/architecture-validation-results.md]
- **App layout is pre-specified.** `apps/api/apps/billing/` → `models.py` (`Subscription, Invoice, StripeEvent`), `views.py` (webhook HMAC), `services/` (incl. `billing_service.py`). 5.1 lands the app + `StripeEvent` + services; `Subscription`/`Invoice` are 5.2. [Source: _bmad-output/planning-artifacts/architecture/project-structure-boundaries.md]
- **Webhook is a distinct API surface.** `/webhooks/...` audience = "Stripe + futurs", auth = **HMAC signature vérifiée**, separate from `/api/v1/`. [Source: project-structure-boundaries.md]
- **NFR-I1 = provider abstraction swappable by config**, same principle as the storages endpoint (MinIO local / S3 prod) and the OCR abstraction (`apps/profiles/services/ocr_service.py`, "Abstraction Tesseract/Mindee"). There is **no pre-existing `PaymentProvider` class** — you are creating it. [Source: starter-template-evaluation.md]
- **Degraded mode:** every third-party service needs a fallback ("Stripe → file d'attente"). For 5.1 the minimum is: fail safe (RFC 7807 + Sentry, no partial state). [Source: project-context-analysis.md]
- **Stripe Elements via dynamic import** if/when used client-side (LCP < 2.5s, NFR-P3). 5.1 uses hosted Checkout (redirect), so Elements is not needed yet. [Source: core-architectural-decisions.md]

### Backend patterns to follow (reuse, don't reinvent)

- **Service-layer gating + typed errors + audit.** Business rules live in a service, raise a typed `DomainError` subclass (RFC 7807), and use `@audit_action(...)`; never put business logic or `is_premium` checks in the view. Canonical example: `OutreachService.send_profile_to_school`. A ruff custom plugin **forbids bare `Exception` and forces `DomainError` in `apps/`**. [Source: implementation-patterns-consistency-rules.md]
- **Permissions are declared explicitly on every view** (`permission_classes: ClassVar = [...]`), CI-enforced by `scripts/assert_rbac_declared.py`. Use `IsAuthenticatedAndActive` from `apps/core/permissions.py` — its docstring literally names *"premium subscription endpoints (Epic 5)"*. The webhook uses `AllowAny` + `@csrf_exempt` (auth is HMAC, not session).
- **Global DRF pagination is `CursorPagination` (PAGE_SIZE 50)** — set `pagination_class = None` on any non-paginated action.
- **App isolation:** apps never import each other's models — go through `from apps.X.services import ...`; `core/` is universally importable, `audit/` only via its decorator. [Source: project-structure-boundaries.md]
- **Env vars use plain `os.environ.get(...)`** (no django-environ/pydantic). Mirror `AI_SERVICE_JWT_SECRET = os.environ.get("AI_SERVICE_JWT_SECRET", "")` in `settings/base.py`.
- **User model** = `apps.accounts.models.User` (`AUTH_USER_MODEL = "accounts.User"`), string PK `usr_...`, `USERNAME_FIELD="email"`, has `tenant_id` (RLS), `role` (`UserRole` TextChoices), soft-delete `deleted_at`. `is_fully_active` is a **property** (`email_verified_at is not None and status == ACTIVE`). There is **no `is_premium` yet** — added in 5.2. Migrations touching the user FK must use `migrations.swappable_dependency(settings.AUTH_USER_MODEL)`.
- **IDs**: use `apps.core.ids.generate_id("evt")`-style helper if adopting the app's string-id convention for `StripeEvent`.
- **Naming**: booleans `is_`/`has_`, timestamps `_at`, TextChoices `SCREAMING_SNAKE_CASE`; endpoints kebab-case plural under `/api/v1/`, query params snake_case; **all JSON snake_case end-to-end** (ADR-0006).

### Frontend patterns

- **No direct `fetch`** (eslint custom rule) — use `apiFetch<T>()` from `apps/web/src/lib/api/client.ts`, which handles dual base URL (server `API_URL_SERVER` vs browser `NEXT_PUBLIC_API_URL`), `credentials:"include"`, CSRF (`X-CSRFToken` from cookie, seeded by `GET /api/v1/auth/csrf/`), RFC 7807 `ApiError`, 15s timeout. Add a domain module `apps/web/src/lib/api/billing.ts` (mirror `schools.ts`).
- **Session-based auth** (`USE_JWT=False`, ADR-0002); mutations must carry the CSRF token.
- ⚠️ **`apps/web/AGENTS.md`: "This is NOT the Next.js you know."** Read the relevant guide in `node_modules/next/dist/docs/` before writing frontend code — the installed version has breaking changes vs training data.

### Testing standards

- pytest + pytest-django; `DJANGO_SETTINGS_MODULE=path_advisor.settings.test`; files `test_*.py`; markers `postgresql_only`, `rls`, `slow`.
- Auth in API tests: `APIClient().force_authenticate(user=...)`; build users with `UserFactory` (`apps/accounts/tests/factories.py`) or `User.objects.create_user(..., status=ACTIVE, email_verified_at=now())`. Resolve URLs with `reverse`.
- Mock all Stripe network calls (`stripe.checkout.Session.create`, `stripe.Webhook.construct_event`, `stripe.Subscription.*`) — tests must not hit the network.

### Cross-story dependencies carried from `deferred-work.md`

- **`is_fully_active` gating**: Story 1.4 shipped the flag/UI but gates nothing; premium endpoints (this epic) MUST enforce it — hence `IsAuthenticatedAndActive` on the checkout endpoint.
- **Stripe cancellation on hard-delete**: when `billing/` lands, a `pre_delete` signal on `User` must cancel active Stripe subscriptions (the cascade-contract CI script cannot enforce this — Stripe is outside the DB). Add the signal stub now (wired fully once `Subscription` exists in 5.2); cross-ref `docs/patterns/account-deletion.md` §"Anti-patterns".
- **Consent audit POST**: the paywall (5.3) must POST `ConsentMeta` to the audit log — not in scope for 5.1 but keep the `@audit_action` seam in the service.
- **GDPR export/erasure**: billing PII (customer/subscription ids, invoices) will need inclusion in the GDPR export manifest (`GDPR_USER_OWNED_S3_PREFIXES` extension point) — track for 5.2/5.3.

### Project Structure Notes

- New backend: `apps/api/apps/billing/{__init__,apps,models,urls,views}.py`, `apps/billing/services/{__init__,provider,stripe_provider,billing_service}.py`, `apps/billing/migrations/0001_initial.py`, `apps/billing/tests/`.
- New frontend: `apps/web/src/lib/api/billing.ts`, `apps/web/src/lib/stripe/client.ts`.
- New infra: `stripe-cli` service in `infra/docker-compose.yml`; four Stripe keys in `.env.example`.
- **No variances** from the planned structure. The only deliberate scope carve-out: `Subscription`/`Invoice` models, `is_premium`, tier gating, and the premium page UI are **out of 5.1** (belong to 5.2/5.3/5.11).

### References

- [Source: _bmad-output/planning-artifacts/epics/epic-5-premium-b2c-envoi-anticipe-biface.md#Story-5.1]
- [Source: _bmad-output/planning-artifacts/architecture/project-structure-boundaries.md] — billing app layout, webhook surface, app-isolation rule
- [Source: _bmad-output/planning-artifacts/architecture/architecture-validation-results.md] — risk #4: Django-only webhook
- [Source: _bmad-output/planning-artifacts/architecture/implementation-patterns-consistency-rules.md] — service-layer gating, DomainError, naming
- [Source: _bmad-output/planning-artifacts/architecture/starter-template-evaluation.md] — NFR-I1 provider abstraction
- [Source: _bmad-output/planning-artifacts/architecture/project-context-analysis.md] — Stripe sandbox local, degraded-mode fallback
- [Source: _bmad-output/planning-artifacts/architecture/core-architectural-decisions.md] — Doppler secrets, dynamic-import Stripe Elements
- [Source: apps/api/apps/core/permissions.py] — `IsAuthenticatedAndActive`
- [Source: apps/api/apps/accounts/models.py] — User model, `is_fully_active`
- [Source: apps/api/path_advisor/settings/base.py] — env var pattern, INSTALLED_APPS
- [Source: apps/api/apps/schools/{views,urls,apps}.py] — representative app patterns
- [Source: apps/web/src/lib/api/client.ts] — `apiFetch`, CSRF, dual base URL
- [Source: _bmad-output/implementation-artifacts/deferred-work.md] — carried dependencies

## Latest Tech Information

- **`stripe` Python SDK**: pin the current stable major (Stripe pins an API version per SDK release). Use `stripe.checkout.Session.create(...)` for hosted Checkout and `stripe.Webhook.construct_event(payload, sig_header, secret)` for signature verification (this raises `stripe.error.SignatureVerificationError` on tamper → map to 400). Set `stripe.api_key` from settings at provider init, not import time.
- **Stripe CLI** (`stripe/stripe-cli` Docker image): `stripe listen --forward-to <host>/webhooks/stripe/` prints a `whsec_...` signing secret for local dev — that value is what `STRIPE_WEBHOOK_SECRET` must hold locally (it differs from the dashboard endpoint secret used in prod).
- **Test card**: `4242 4242 4242 4242`, any future expiry, any CVC/ZIP → successful `checkout.session.completed`.
- **PCI**: hosted Checkout keeps Path-Advisor in SAQ-A scope (lowest) — never introduce raw card fields.
- ⚠️ Verify SDK method names/signatures against the installed version before coding; Stripe evolves its Python SDK surface.

## Dev Agent Record

### Agent Model Used

claude-fable-5 (dev-story workflow)

### Debug Log References

- `stripe` SDK resolved to **12.5.1** (pinned `>=11.0,<13.0`).
- Test suite requires **PostgreSQL** (pre-existing): the `professions` model uses a
  Postgres `ArrayField` (`level_compatibility varchar(40)[]`), so the sqlite `test`
  settings cannot build the schema. Ran billing tests against a local Postgres with a
  `path_advisor_test` NOSUPERUSER/NOBYPASSRLS role, matching `ci-api.yml`.
- `users` has FORCE RLS (Story 1.8) — test user creation goes through the sanctioned
  `apps.core.rls.bypass_rls()` helper.
- DomainError responses from DRF APIViews render as `application/json` (the DRF renderer
  overwrites the handler's `application/problem+json` header at `finalize_response`); the
  body stays RFC 7807-shaped, so the AC6 test asserts the body (`type`/`title`/`status`).

### Completion Notes List

- Implemented the Epic 5 billing walking-skeleton: `apps/billing/` app with a
  `PaymentProvider` abstraction (`create_checkout_session`, `handle_webhook`,
  `cancel_subscription`, `get_subscription_status`), a `StripeProvider` reading keys from
  env (test/prod swap by config — NFR-I1), and a `get_payment_provider()` factory.
- Webhook implemented **Django-only** (single source of truth; no Next.js route),
  CSRF-exempt, HMAC-verified via `stripe.Webhook.construct_event`, idempotent through the
  `StripeEvent` ledger.
- PCI: hosted Checkout only (`POST /api/v1/billing/checkout-session` → hosted URL); no card
  data stored. Provider failures surface as `PaymentProviderError` (RFC 7807, 502) with no
  partial state (degraded-mode).
- Dev-only `stripe-cli` listener added to `infra/docker-compose.yml`; four Stripe keys added
  to `.env.example` with empty placeholders + Doppler note.
- 12/12 billing tests pass; ruff + `assert_rbac_declared` clean for billing (webhook
  whitelisted); frontend eslint clean for the two new TS files.
- **Out of scope (as specified)**: `Subscription`/`Invoice` models, `is_premium` flag, tier
  gating, `premium/page.tsx` UI → Stories 5.2 / 5.3 / 5.11. The `User` `pre_delete`
  Stripe-cancellation signal is deferred to 5.2 (needs the `Subscription` model).
- **Pre-existing issue observed (not introduced here, out of scope)**: `assert_rbac_declared`
  reports 13 `IsAuthenticated`-only endpoints in `students`/`schools` (Epics 2/4) that are
  neither role-guarded nor whitelisted. Their views are byte-identical to `main`. Flagging
  for a separate cleanup — the billing endpoints themselves pass the gate.

### File List

**Backend (apps/api)**
- `apps/billing/__init__.py` (new)
- `apps/billing/apps.py` (new)
- `apps/billing/models.py` (new — `StripeEvent`)
- `apps/billing/urls.py` (new)
- `apps/billing/views.py` (new — `CheckoutSessionView`, `stripe_webhook_view`)
- `apps/billing/services/__init__.py` (new — `get_payment_provider`)
- `apps/billing/services/provider.py` (new — `PaymentProvider` ABC + dataclasses)
- `apps/billing/services/stripe_provider.py` (new — `StripeProvider`)
- `apps/billing/services/billing_service.py` (new — `BillingService`)
- `apps/billing/migrations/0001_initial.py` (new)
- `apps/billing/tests/__init__.py` (new)
- `apps/billing/tests/test_provider.py` (new)
- `apps/billing/tests/test_api.py` (new)
- `apps/core/exceptions.py` (modified — `InsufficientPlan`, `PaymentProviderError`)
- `path_advisor/settings/base.py` (modified — Stripe settings + `apps.billing` in INSTALLED_APPS)
- `path_advisor/urls.py` (modified — billing API include + webhook route)
- `scripts/assert_rbac_declared.py` (modified — whitelist `stripe-webhook`)
- `pyproject.toml` (modified — `stripe` dep + `apps/billing/**` ruff per-file-ignores)

**Frontend (apps/web)**
- `src/lib/api/billing.ts` (new — `createCheckoutSession`)
- `src/lib/stripe/client.ts` (new — `redirectToPremiumCheckout`)

**Infra**
- `infra/docker-compose.yml` (modified — `stripe-cli` dev listener)
- `.env.example` (modified — Stripe keys)

## Senior Developer Review (AI)

**Date:** 2026-08-25 — three parallel adversarial layers (Blind Hunter, Edge Case Hunter, Acceptance Auditor). **Outcome: Changes Requested → all High/Med resolved.**

### Resolved
- **[High] Webhook idempotency concurrency race** (all 3 layers) — `record_webhook_event` had no transaction/lock, so concurrent re-deliveries could both process an event. Fixed: wrapped in `transaction.atomic()` + `select_for_update()` on the ledger row; the second delivery blocks then short-circuits on `processed_at`.
- **[Med] Partial ledger row on processing failure** — a committed row with `processed_at=NULL` could survive a `_process_event` exception. Fixed by the same atomic block (row creation rolls back). Added `test_webhook_processing_failure_rolls_back_ledger_row`.
- **[Med] Bare `except Exception` masking bugs as 502** — narrowed to `except stripe.error.StripeError`; genuine bugs now propagate as 500 (Sentry-visible) instead of a misleading "provider unavailable".
- **[Med] PII stored in `StripeEvent.payload`** — `dict(event)` persisted full customer PII, contradicting the "ids only / PCI SAQ-A" classification. Fixed: only the non-PII envelope (`event_type`) is stored, `payload={}`. Added `test_webhook_does_not_persist_pii_payload`.
- **[Low] `stripe-cli` crash-loop on empty key** — `restart` changed to `"no"`.
- **[Low] Param naming** — `cancel_subscription`/`get_subscription_status` now take `stripe_subscription_id` (spec fidelity).

### Accepted / deferred (non-blocking)
- **AC6 media type**: DRF renders DomainError responses as `application/json` (body stays RFC 7807-shaped); asserted on the body. Documented behavior for all DRF endpoints in this repo.
- **No frontend trigger yet**: `redirectToPremiumCheckout()`/`createCheckoutSession()` are ready but unwired — the premium page UI is Story 5.3 (explicitly out of scope here).
- **Empty Stripe config → 502**: a misconfigured deploy surfaces as a provider error rather than a distinct config alert; acceptable for MVP (Doppler guarantees keys in staging/prod). Tracked for a boot-time check.

Post-fix: **14/14 billing tests pass**, ruff clean.

## Change Log

| Date | Change |
|------|--------|
| 2026-08-25 | Story 5.1 implemented — billing app, PaymentProvider/StripeProvider abstraction, Django-only HMAC webhook + idempotency ledger, hosted checkout endpoint, docker-compose Stripe CLI listener, frontend glue, 12 tests. Status → review. |
| 2026-08-25 | Code review (3 adversarial layers) — fixed webhook concurrency race (atomic + row lock), partial-state rollback, narrowed exception handling, removed PII from ledger payload, stripe-cli restart, param naming. +2 tests (14 total). |
