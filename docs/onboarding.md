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

## 10. What's next

After the foundation is up, the next stories live in
[`_bmad-output/implementation-artifacts/sprint-status.yaml`](../_bmad-output/implementation-artifacts/sprint-status.yaml).
Pick the first one with status `ready-for-dev`.

For architecture context: [ADR-0001](./adr/0001-stack-django-nextjs-fastapi-docker.md) and the
sharded architecture under `_bmad-output/planning-artifacts/architecture/`.
