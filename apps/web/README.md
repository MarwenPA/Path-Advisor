# Path-Advisor — Web

Next.js 16 frontend for Path-Advisor. **The canonical dev workflow is `docker compose up -d`
from the repo root** — see [`docs/onboarding.md`](../../docs/onboarding.md) for prereqs, smoke
checks, and troubleshooting.

For a standalone `cd apps/web && npm run dev` workflow you'll also need the API and ai-service
running (typically via Docker Compose). See [`README.md`](../../README.md) at the repo root for
stack overview and [`docs/adr/0001-stack-django-nextjs-fastapi-docker.md`](../../docs/adr/0001-stack-django-nextjs-fastapi-docker.md)
for the architecture decision.
