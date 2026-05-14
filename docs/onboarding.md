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

## 7. Troubleshooting

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

## 8. What's next

After the foundation is up, the next stories live in
[`_bmad-output/implementation-artifacts/sprint-status.yaml`](../_bmad-output/implementation-artifacts/sprint-status.yaml).
Pick the first one with status `ready-for-dev`.

For architecture context: [ADR-0001](./adr/0001-stack-django-nextjs-fastapi-docker.md) and the
sharded architecture under `_bmad-output/planning-artifacts/architecture/`.
