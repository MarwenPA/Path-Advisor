# Path-Advisor — Developer onboarding

> Goal: get a new dev from a clean checkout to a running local stack in **under 15 minutes**.

## 1. Prerequisites

| Tool | Version | Install |
|---|---|---|
| Docker Desktop (or Colima) | ≥ 4.30 with **Compose v2.20+** | <https://docs.docker.com/desktop/> |
| Node.js | 22 LTS (newer works) | `brew install node@22` / [nvm](https://github.com/nvm-sh/nvm) |
| Python | 3.12 | Installed automatically by `uv` if missing |
| uv | ≥ 0.5 | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| GNU Make | 3.81+ | preinstalled on macOS |
| Git | ≥ 2.40 | preinstalled |

Recommended Docker Desktop resources: **≥ 4 GB RAM**, **≥ 4 CPU**, **≥ 10 GB disk**.

## 2. Bootstrap

```bash
git clone <repo-url> path-advisor
cd path-advisor
cp .env.example .env          # local defaults are safe; tweak only if needed

# Pre-pull base images while you set up other tooling (optional, speeds up first up)
docker compose pull
```

## 3. Start the stack

```bash
docker compose up -d
```

Expected services on `localhost`:

| Service | URL | Note |
|---|---|---|
| Next.js (web) | http://localhost:3000 | Hello page in dev |
| Django (api) | http://localhost:8000/admin | Login: `admin@path-advisor.local` / `admin-local-dev` after `make seed` |
| FastAPI (ai-service) | http://localhost:8001/health | `{"status":"ok"}` |
| Mailpit UI | http://localhost:8025 | catches outgoing email |
| MinIO console | http://localhost:9001 | `minio_local` / `minio_local_password` |

PostHog is **not** started by default — enable on demand:

```bash
docker compose --profile analytics up -d posthog
```

## 4. Seed dev data

```bash
make seed
```

Idempotent: creates the super-user and the three MinIO buckets (`bulletins-encrypted`,
`exports-gdpr`, `audit-logs-archive`). Safe to run repeatedly.

## 5. Smoke checks (copy-paste)

```bash
curl -s http://localhost:3000/ | grep -q "Hello Path-Advisor" && echo "✓ web"
curl -s http://localhost:8000/api/v1/health/ | grep -q '"status":"ok"' && echo "✓ api"
curl -s http://localhost:8001/health           | grep -q '"status":"ok"' && echo "✓ ai-service"
```

## 6. Day-to-day commands

```bash
make help        # list everything
make dev         # docker compose up
make down        # docker compose down
make test        # vitest + pytest (api) + pytest (ai)
make lint        # ESLint + Prettier + tsc + Ruff + mypy
make openapi     # regenerate packages/openapi/openapi.json + TS client
make seed        # idempotent dev seed
make clean       # remove generated artifacts and caches
```

## 7. Design system tokens

All colors, type scale, spacing, and motion live in
[`apps/web/src/styles/tokens.css`](../apps/web/src/styles/tokens.css) (CSS variables) and
[`apps/web/tailwind.config.ts`](../apps/web/tailwind.config.ts) (Tailwind theme mapping).
Custom utilities (e.g. `font-tabular`) live in
[`apps/web/src/lib/design-system/tailwind-plugin.ts`](../apps/web/src/lib/design-system/tailwind-plugin.ts).

**Rules of the road:**

- Never hardcode a `#hex` colour in a component — always use a Tailwind class that
  references the tokens (`bg-brand`, `text-text-muted`, `border-border`, etc.).
- Type scale is mobile-first: pair `text-h1` with `md:text-h1-desktop` for the
  desktop variant where the spec differs.
- Animations must use one of the four duration tokens: `duration-instant`,
  `duration-quick`, `duration-standard`, `duration-narrative` (the last is
  reserved for the journey graph in Epic 4).
- A 5-pair WCAG contrast audit runs as a Vitest test
  ([`contrast.test.ts`](../apps/web/src/lib/design-system/contrast.test.ts)) — keep it green.

If a new colour or utility is needed, extend the tokens; don't add one-off CSS.

## 8. Audit log — when to use `@audit_action`

Story 1.13 ships an append-only journal (`audit_logs`) that records every access to a
student's personal data by a third party. Anytime your service code reads, mutates, or
**refuses** access to sensitive data, decorate it:

```python
from apps.audit.decorators import audit_action

@audit_action(
    "outreach.profile_sent",
    subject_from=lambda kwargs, ret: kwargs["student"].id,
    metadata_from=lambda kwargs, ret: {"school_id": kwargs["school"].id},
)
def send_profile_to_school(*, student, school, motivation): ...
```

Then add your event name to [`docs/patterns/audit-events.md`](./patterns/audit-events.md)
in the same PR. The catalog is the source of truth — silent additions break compliance
review.

Refusal paths (DRF `has_permission` returning `False`, RBAC blocks, etc.) call
`record_audit(action="…", result="denied", actor=…, metadata={…})` directly — see
`apps/audit/permissions.py::IsPathAdmin` for the canonical pattern.

The audit log itself is read by the DPO via `GET /api/v1/audit/logs/` (path_admin role)
or in Django admin (read-only listing).

See [ADR 0009](./adr/0009-audit-log-immutable-trigger.md) for the immutability /
hash-chain rationale.

## 9. Troubleshooting

**Ports already in use** (3000 / 8000 / 8001 / 5432 / 6379 / 1025 / 8025 / 9000 / 9001) — stop
whatever owns them or change the host-side port in `infra/docker-compose.yml`.

**`pgvector` extension missing** — happens if you re-use an old `postgres_data` volume. Run
`docker compose down -v && docker compose up -d` to recreate it; `infra/postgres/init.sql` will
register the extension on the next first boot.

**MinIO buckets missing** — `make seed` creates them. If MinIO was unhealthy when seed ran,
restart and re-run `make seed`.

**Web dev server slow / not picking up changes** — the `node_modules` and `.next` directories
are mounted as anonymous Docker volumes; if something looks stale, `docker compose down web && docker compose up -d web`.

**`legacy-peer-deps` warning on `npm install`** — expected until next-intl publishes Next 16
support. See [ADR-0001](./adr/0001-stack-django-nextjs-fastapi-docker.md#tooling-notes).

**uv can't find Python 3.12** — uv installs it on first sync; ensure network access. The pinned
version sits in `apps/api/.python-version` and `apps/ai-service/.python-version`.

**`AUTH_USER_MODEL` migration error** — switching to a custom User model (Story 1.3) after
the DB has already run `auth.0001_initial` against the built-in `auth.User` is a breaking
change in Django. If you see migration errors mentioning `accounts.User` or `auth.User`,
reset the local database:

```bash
docker compose down -v       # wipe postgres_data volume
docker compose up -d
docker compose exec api uv run python manage.py migrate
make seed                    # recreate admin@path-advisor.local
```

See [ADR-0002](./adr/0002-auth-allauth-dj-rest-auth.md) for the full auth-stack rationale.

### Story 1.4 — Sub-15 users stuck in "limited mode"

Users whose `status = pending_parental_consent` can log in but **don't** have `is_fully_active = true`,
so the `<LimitedModeBanner />` shows at the top of every authenticated page. A few quirks to know:

- The child's own email-verification flow is independent of parental consent (cf. Story 1.4 §AC3
  state machine) — they must both complete to reach `active`.
- `/api/v1/auth/parental-consent/resend/` is rate-limited 1 per hour per user; the banner button
  surfaces a friendly "Trop tôt — réessaie dans une heure" on the 429.
- A child who tried to re-attempt signup with a different parent email after a refusal will hit
  the existing `EmailAlreadyRegistered` guard (Story 1.3). This is intentional — self-service
  re-attempts would let a determined minor brute-force around a refusal. They have to contact
  support, or wait for Epic 5/6 to ship the proper resolution flow.
- Tokens are 60-day TTL. After 60 days the daily Celery beat job suspends the user (final email
  sent to the child explaining the pause). Old tokens stay in the DB for audit replay; `/decide/`
  returns 409 past expiry.

See [ADR-0003](./adr/0003-parental-consent-tokenized.md) for the tokenised-parent design rationale.

## 9bis. Multi-tenant isolation (Story 1.8 — load-bearing)

Any new model that stores personal data MUST inherit from
[`apps.core.models.TenantScopedModel`](../apps/api/apps/core/models.py) — the
PostgreSQL Row-Level Security policies on `users` + `parental_consents` rely
on session GUCs that `TenantSessionMiddleware` populates per request, and
the same plumbing is what enforces tenant isolation at the DB layer.

- **If `make test-rls` fails after your change, your model likely needs `TenantScopedModel`** —
  read [`docs/patterns/multi-tenant.md`](./patterns/multi-tenant.md) for the 5-line recipe +
  decision tree, then [ADR-0010](./adr/0010-multi-tenant-rls.md) for the rationale.
- Audit logs are deliberately RLS-exempt (cross-tenant by DPO design — ADR-0009 §7).
- Anonymous endpoints (parental-consent `/decide/`, signup signal) + Celery tasks
  use the audited bypasses `apps.core.rls.bypass_rls()` / `with_system_actor()` —
  see the docstring whitelist before adding a new call site.

## 9b. Cascade contract — every FK to User MUST be CASCADE or SET_NULL

If your story adds a model holding personal data, the FK to `accounts.User`
must use `on_delete=models.CASCADE` (data dies with the user) or
`on_delete=models.SET_NULL` (audit row, FK cleared but row survives the
3-year retention window). Anything else (`PROTECT`, `RESTRICT`,
`DO_NOTHING`) breaks the right-to-erasure pipeline (Story 1.12) and is
refused by `scripts/assert_user_cascade.py` in CI.

If your model owns a per-user S3 prefix, register it in
`settings.GDPR_USER_OWNED_S3_PREFIXES` so the hard-delete sweep purges it.

Full details: [docs/patterns/account-deletion.md](./patterns/account-deletion.md).

## 9c. Login security — per-IP throttle vs per-account lockout (Story 1.5)

The login endpoint runs two **orthogonal** rate-limit shapes:

| Layer | Scope | Trigger | Owner |
|---|---|---|---|
| Per-IP throttle | 5/min/IP | `django-ratelimit` on `ThrottledLoginView.dispatch` | Story 1.12 |
| Per-account lockout | 5 fails / 15 min → 10 min lock on `User.locked_until` | `apps.accounts.services.login_security.record_failed_attempt` | Story 1.5 |

- A botnet IP hammering many emails trips the per-IP throttle without filling any per-account counter.
- A distributed attack on one email (multiple IPs) trips the per-account lockout without exhausting any IP's budget.

The Redis counter (`auth.login_fail:{user_id}`, TTL 900s) is allowed to lose data on a cache flush. The DB column `User.locked_until` is the source of truth — the lockout itself never lapses early.

Status-aware rejections (suspended, email unverified, deleted) and the lockout state all return a Problem Details payload via `apps.accounts.gdpr_exceptions`. Wrong-password and unknown-email collapse to the **same** generic 400 — never tell the caller which side failed. The audit row carries the truth (sha256-hashed email + truncated IP) for DPO triage.

DPO playbooks for the two common support escalations ("I'm locked out", "I lost email access — please reset my password") live in [`docs/runbooks/login-and-password-reset.md`](./runbooks/login-and-password-reset.md).

## 9d. MFA TOTP — flow + lockout interaction (Story 1.6)

Mandatory for `counselor` / `school_admin` / `path_admin` (NFR-S2), opt-in for `student` / `parent`. Stack: `django-otp` 1.7 (`TOTPDevice` + `StaticDevice` + `StaticToken`) + a 5-min IP-bound `mfa_session` JWT minted at password-success.

**Login flow with MFA:**

1. `POST /api/v1/auth/login/` with email + password → server-side serializer authenticates.
2. **Hook in `ThrottledLoginView`:** if `user.requires_mfa` (staff OR already enrolled), the response is `200` with `{"mfa_required": true, "mfa_enrollment_required": <bool>, "mfa_session": "<JWT>", "user": {...}}` and the session cookie is NOT set. `request.session.flush()` is called so `SessionMiddleware` doesn't re-emit the cookie.
3. Frontend stashes `mfa_session` in `sessionStorage` → routes to `/auth/mfa/enroll` or `/auth/mfa/challenge`.
4. Enrollment flow: `POST /api/v1/auth/mfa/enroll/start/` → QR code → `POST /api/v1/auth/mfa/enroll/confirm/` with first 6-digit TOTP code → 200 + 8 recovery codes + session cookie posted.
5. Challenge flow: `POST /api/v1/auth/mfa/challenge/` with TOTP (or recovery code) → 200 + session cookie posted.

**Critical lockout-clear semantic (Story 1.6 moved this from Story 1.5):**

The per-account failed-attempt counter (Story 1.5's `login_security` service) is **NOT** cleared on password-only success when the user has MFA. It is only cleared on:
- The non-MFA happy path (B2C non-enrolé) inside `ThrottledLoginView.post`.
- A successful MFA challenge / enrollment-confirm.

If we cleared on password-only success, an attacker who guesses the password but can't pass MFA could reset the lockout on every guess, defeating the 5-failures-in-15-min cap for the password leg.

**MFA failures fill the SAME lockout counter** as password failures — 5 wrong TOTP codes in 15 min lock the account for 10 min, identical to 5 wrong passwords.

**DPO playbook** for users who lost both their authenticator AND their 8 recovery codes lives in [`docs/runbooks/mfa-lost-device.md`](./runbooks/mfa-lost-device.md).

## 9e. RBAC — permissions, audit, CI gate (Story 1.7)

Six roles (`student`, `parent`, `counselor`, `school_admin`, `path_admin`, `support`) gated via `apps.core.permissions` permission classes. Every new view MUST declare `permission_classes` explicitly — enforced by the `assert_rbac_declared.py` CI gate.

**Canonical staff endpoint shape:**

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from apps.core.permissions import IsCounselor  # requires_mfa_verified=True by default

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsCounselor])
def cohort_dashboard(request):
    ...
```

Every refusal writes ONE `rbac.access_denied` audit row per request (deduped). DPO triage queries on `actor_id + action="rbac.access_denied"` spot escalation patterns.

**RBAC vs RLS (Story 1.7 vs Story 1.8):** orthogonal layers, both active. RBAC = "can this user TRY this action?" (view layer, 401/403). RLS = "what data can this user SEE in the result set?" (DB layer, automatic filter).

Full matrix + how-to-add-a-new-endpoint walkthrough: [`docs/patterns/rbac-matrix.md`](./patterns/rbac-matrix.md).

## 9f. Access-list aggregator (Story 1.9)

`GET /api/v1/profile/access-list/` returns a unified list of every third party (parent, école, conseillère) currently authorized to see a student's profile. The endpoint is powered by a polymorphic source registry in [`apps/profiles/access_list/`](../apps/api/apps/profiles/access_list/) — each tier type (`parental_consent`, `school_partnership`, `counselor_consent`) ships its own `AccessListSource` adapter, and the aggregator concatenates results.

Today only `ParentalConsentSource` is live (Story 1.4 data). Stories 5.4 and 6.7 will add the other two adapters with no change to the API or the frontend page.

The visibility matrix in [`visibility_matrix.py`](../apps/api/apps/profiles/access_list/visibility_matrix.py) is the single source of truth for "what does tier X see / not see" — `bulletins_detailles` masked for parents, `motivation_libre` masked for conseillère, etc. Every change to that matrix triggers a parametrized test that fails if you forget to update a tier.

Full pattern + extension recipe: [`docs/patterns/access-list-aggregator.md`](./patterns/access-list-aggregator.md).

## 10. What's next

After the foundation is up, the next stories live in
[`_bmad-output/implementation-artifacts/sprint-status.yaml`](../_bmad-output/implementation-artifacts/sprint-status.yaml).
Pick the first one with status `ready-for-dev`.

For architecture context: [ADR-0001](./adr/0001-stack-django-nextjs-fastapi-docker.md) and the
sharded architecture under `_bmad-output/planning-artifacts/architecture/`.
