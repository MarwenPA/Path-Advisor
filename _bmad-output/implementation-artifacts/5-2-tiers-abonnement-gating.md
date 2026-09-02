# Story 5.2: Subscription tiers (freemium / premium) + gating

**Epic:** 5 — Premium B2C & Biface Early Outreach
**Status:** done
**Sprint:** 9 (Premium foundations)
**Story Key:** `5-2-tiers-abonnement-gating`
**Estimation:** L
**Depends on:** 5.1 (billing app, `PaymentProvider`, webhook + `StripeEvent` ledger)

## Story

**As a** Path-Advisor system,
**I want** to manage the two B2C tiers (Freemium free / Premium 10.99€/mo) with feature gating,
**so that** premium features are reachable only by active subscribers.

## Acceptance Criteria (BDD)

### AC1 — `Subscription` model
**Given** the DB is migrated
**Then** a `Subscription` links a `user` to a `tier` (`free`/`premium`), a `status` (`active`/`cancelled`/`past_due`), a `current_period_end`, and a `stripe_subscription_id` (+ `stripe_customer_id`) for traceability.

### AC2 — `is_premium` truth
**Given** a user with an `active` premium subscription (or `past_due` within the 7-day grace window)
**When** `user.is_premium` is evaluated
**Then** it returns `True`; for `free`, `cancelled`, or grace-expired `past_due` it returns `False`.

### AC3 — Gating blocks free users
**Given** a `free` user calling a premium-gated endpoint
**Then** the service layer raises `InsufficientPlan` → HTTP 402 RFC 7807 with `type=.../insufficient-plan` (the front maps this to the contextual paywall, Story 5.11)
**And** a `premium` active user is allowed without friction.

### AC4 — Webhook lifecycle drives subscription state
**Given** Stripe webhook events (built on 5.1's verified + idempotent pipeline)
**Then** `checkout.session.completed` → upsert `Subscription` `active`/`premium` with period + stripe ids;
**And** `customer.subscription.updated` → sync `status` + `current_period_end`;
**And** `customer.subscription.deleted` → `cancelled`;
**And** `invoice.payment_failed` → `past_due` with `grace_until = now + 7d`.

### AC5 — Grace period + dunning
**Given** a subscription that went `past_due`
**Then** premium stays accessible for 7 days (grace)
**And** dunning emails are sent at J+0, J+3, J+7
**And** after 7 days without recovery the tier drops to `free` and premium closes cleanly.

### AC6 — Subscription status endpoint + user flag
**Given** an authenticated user
**When** `GET /api/v1/billing/subscription`
**Then** returns `{ tier, status, current_period_end, is_premium }`
**And** the current-user serializer (`/api/v1/auth/user/`) exposes `is_premium` for frontend gating.

## Tasks / Subtasks

- [ ] **T1 — `Subscription` model + migration** (AC1) — `apps/billing/models.py`: `Subscription` (OneToOne `user`, `tier`/`status` TextChoices, `current_period_end`, `grace_until` nullable, `stripe_subscription_id` unique-nullable, `stripe_customer_id`, `_at` timestamps). `makemigrations billing`.
- [ ] **T2 — `is_premium`** (AC2) — property on `Subscription` (`is_active_now`) + a `User.is_premium` property delegating to it (grace-aware). Add `SubscriptionService.is_premium(user)`.
- [ ] **T3 — Gating** (AC3) — `IsPremium` permission (composed `[IsAuthenticatedAndActive, IsPremium]`) AND the canonical service-layer check raising `InsufficientPlan` (already in `core/exceptions.py`). Prefer the service-layer gate for business endpoints; the permission for pure read endpoints.
- [ ] **T4 — Webhook lifecycle handlers** (AC4) — extend `BillingService._process_event` (5.1) to handle the 4 event types via `SubscriptionService.apply_event(...)`; upserts under `bypass_rls` (system actor) + `@audit_action`.
- [ ] **T5 — Grace + dunning** (AC5) — `grace_until` set on `past_due`; `is_premium` honors grace; Celery beat task `process_dunning` sends J0/J3/J7 emails (email abstraction stub — Story 8.1 will formalize) and downgrades to `free` past grace.
- [ ] **T6 — Status endpoint + serializer** (AC6) — `GET /api/v1/billing/subscription` (`SubscriptionStatusView`); add `is_premium` to `UserDetailsSerializer` + the web `CurrentUser` interface.
- [ ] **T7 — Deferred-dep wiring** — add the `User` `pre_delete` signal cancelling active Stripe subscriptions (carried from `deferred-work.md`); include billing data in GDPR export manifest note.
- [ ] **T8 — Tests** — model/property (grace math), gating (402 free / allow premium), each webhook event → state, dunning downgrade, status endpoint, serializer flag. Postgres lane (`bypass_rls` for user creation, per 5.1 pattern).

## Dev Notes
- Build on 5.1: reuse `StripeEvent` idempotency + the verified webhook; `_process_event` now dispatches to `SubscriptionService`. Keep webhook Django-only.
- Service-layer gating + typed `InsufficientPlan` (RFC 7807) + `@audit_action`; never gate in the view body (repo convention).
- `is_premium` must be grace-aware: `active` OR (`past_due` AND `grace_until > now`).
- Subscription writes from the webhook run as system actor → wrap in `apps.core.rls.bypass_rls` (the anonymous webhook session has no RLS identity), mirroring 5.1's family fixes.
- Email: no transactional email infra yet (Story 8.1). Implement `send_dunning_email` behind a thin function that logs + is patchable in tests; wire real delivery in 8.x.
- Frontend: extend `CurrentUser` (`apps/web/src/lib/api/auth.ts`) with `is_premium`; add `getSubscription()` in `apps/web/src/lib/api/billing.ts`. Read `apps/web/AGENTS.md` first.

### References
- [Source: _bmad-output/planning-artifacts/epics/epic-5-premium-b2c-envoi-anticipe-biface.md#Story-5.2]
- [Source: 5-1-integration-stripe.md] — billing app, webhook, ledger, provider
- [Source: apps/api/apps/core/exceptions.py] — `InsufficientPlan`
- [Source: apps/api/apps/core/permissions.py], [apps/api/apps/core/rls.py], [apps/api/apps/audit/decorators.py]

**Status:** done

### Review Findings (BMad code-review, 2026-08-26 — 3 adversarial layers)

- [x] [Review][Decision] Second checkout for an already-subscribed user silently overwrote `stripe_subscription_id` on the OneToOne row, orphaning the prior Stripe subscription (never cancelled) — a billing leak. **Resolved: "merge subscriptions"** — `_on_checkout_completed` now locks the existing row (`select_for_update`) and, if a different `stripe_subscription_id` is already on file, cancels it at Stripe (best-effort, `_cancel_superseded_subscription`) before activating the new one. Exactly one live Stripe subscription per user going forward. [apps/billing/services/subscription_service.py `_on_checkout_completed`, `_cancel_superseded_subscription`]
- [x] [Review][Decision] The `rls.bypass_used` audit row (and the `billing.subscription_event_applied` failure row) was lost if the enclosing `record_webhook_event` transaction rolled back. **Resolved: dedicated audit path** (simplified from an initial thread-based design that leaked writes across pytest-django's transactional test isolation and was reverted) — `record_webhook_event` now wraps its `transaction.atomic()` block in `try/except`; the `except` clause runs strictly after the block has unwound and rolled back, so a fresh `record_audit(action="billing.webhook_processing_failed", ...)` call there starts and commits its own independent transaction, guaranteeing at least one durable audit row per failed webhook attempt. `rls.py`'s `_audit_bypass` itself still joins the caller's transaction (Story 1.13 policy, unchanged) — its docstring now states this caveat explicitly and points callers at this pattern. [apps/billing/services/billing_service.py `record_webhook_event`, apps/core/rls.py `_audit_bypass`]
- [x] [Review][Patch] `apply_event` returned `True` (marking the event permanently `processed_at`) merely because a handler function existed for the event type — even when that handler silently no-op'd because `_by_stripe_sub` found no matching `Subscription` row yet. Fixed: every handler now returns whether it actually found+mutated a row, and `apply_event` propagates that. [apps/billing/services/subscription_service.py]
- [x] [Review][Patch] `_on_subscription_updated` had no branch for terminal/negative Stripe statuses. Fixed: anything outside `active`/`trialing`/`past_due` now sets `tier=FREE, status=CANCELLED` (mirrors `_on_subscription_deleted`). [apps/billing/services/subscription_service.py]
- [x] [Review][Patch] No `select_for_update()` on the `Subscription` row while applying webhook events. Fixed: `apply_event` now wraps its dispatch in `transaction.atomic()` (nested-safe, also works standalone e.g. in tests) and both `_on_checkout_completed` and `_by_stripe_sub` use `select_for_update()`. [apps/billing/services/subscription_service.py]
- [x] [Review][Patch] `_ts()` called `int(value)` unguarded. Fixed: wrapped in `try/except (TypeError, ValueError, OSError, OverflowError)`, logs and returns `None` instead of poisoning the transaction. [apps/billing/services/subscription_service.py]
- [x] [Review][Patch] `process_dunning` skipped any `past_due` row with `grace_until=None` forever. Fixed: self-heals by starting the grace clock instead of skipping. [apps/billing/services/subscription_service.py]
- [x] [Review][Patch] `pre_delete` signal's initial `Subscription` lookup sat outside the `try/except`. Fixed: the whole signal body is now inside one try/except. [apps/billing/signals.py]
- [x] [Review][Defer] Out-of-order webhook delivery can let a stale `checkout.session.completed` replay overwrite a newer `past_due`/cancelled state — no event-timestamp-based conflict resolution exists. Real, but requires plumbing Stripe's event-level `created` timestamp through and designing a conflict-resolution rule; bigger than a quick patch. — deferred, revisit when Story 5.3 adds real subscription-lifecycle side effects. [apps/billing/services/subscription_service.py `_on_checkout_completed`]

**Dismissed as noise:** "AuditLog write could be rejected by RLS" (false — `audit_logs` is explicitly RLS-exempt, verified in `apps/core/rls.py` + migration `0007_enable_rls.py`); "bare `except Exception` in signals.py violates a ruff plugin" (no such plugin exists in this repo — ruff passes clean); "AC3 gating not proven end-to-end" (expected — premium-gated business endpoints belong to Story 5.3+).

## Dev Agent Record
### Agent Model Used
claude-fable-5 (dev-story)
### Completion Notes List
- `Subscription` model (OneToOne user, tier/status/grace_until/stripe ids) + grace-aware `is_active_now`; migration `0002_subscription`.
- `User.is_premium` property delegating to `SubscriptionService` (local import, no app-layer cycle); exposed on `UserDetailsSerializer` + web `CurrentUser`.
- Gating: `SubscriptionService.require_premium` → `InsufficientPlan` (402 RFC 7807) for business endpoints; `IsPremium` DRF permission for read endpoints.
- Webhook lifecycle wired into 5.1's `_process_event` → `SubscriptionService.apply_event` (checkout.completed / subscription.updated / subscription.deleted / invoice.payment_failed), run under `bypass_rls` + `@audit_action`.
- Grace + dunning: `past_due` sets `grace_until = now+7d`; `process_dunning` Celery beat task (04:40 daily) downgrades grace-expired subs to free and sends the final email. **Partial-scope note:** graduated J+0/J+3 reminder emails are stubbed (`_send_dunning_email` logs only) — real delivery + per-reminder idempotency tracking are deferred to Story 8.1 (transactional email infra). The enforceable part (grace window + downgrade) is complete and tested.
- `GET /api/v1/billing/subscription` status endpoint; `getSubscription()` web fetcher.
- Carried dependency resolved: `pre_delete` signal on User cancels the active Stripe subscription (best-effort, never blocks RGPD deletion).
- **Tests: 29 billing tests pass** (14 from 5.1 + 15 new); ruff clean; RBAC gate clean for billing endpoints; frontend eslint clean.

### File List
**Backend:** apps/billing/models.py (Subscription), apps/billing/migrations/0002_subscription.py, apps/billing/services/subscription_service.py (new), apps/billing/services/billing_service.py (dispatch), apps/billing/tasks.py (new), apps/billing/signals.py (new), apps/billing/apps.py (ready), apps/billing/views.py (SubscriptionStatusView), apps/billing/urls.py, apps/billing/tests/test_subscription.py (new), apps/accounts/models.py (is_premium), apps/accounts/serializers.py (is_premium), apps/core/permissions.py (IsPremium), path_advisor/celery.py (dunning beat)
**Frontend:** apps/web/src/lib/api/auth.ts (CurrentUser.is_premium), apps/web/src/lib/api/billing.ts (getSubscription)

## Change Log
| Date | Change |
|------|--------|
| 2026-08-26 | Story 5.2 implemented — Subscription model + tiers, is_premium gating (InsufficientPlan 402 / IsPremium), webhook lifecycle, grace+dunning, status endpoint, pre_delete Stripe cancel, 15 tests. Status → review. |
