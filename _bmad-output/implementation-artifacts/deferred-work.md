# Deferred Work

Items flagged during code reviews but consciously deferred. Each has a target story or trigger condition.

## Deferred from: code review of 1-1-initialisation-projet (2026-05-14)

- **`verify_jwt` no-op stub** — to be hardened in Story 3.1 (ai-service scoring activation).
- **`apiFetch` no timeout / no RFC 7807 parsing** — Story 1.5 (login flow + error handling).
- **`bulletins-encrypted` bucket has no SSE config** — Story 2.3 (upload bulletins) must call `PutBucketEncryption` + versioning + deny-public ACL.
- **`CSRF_TRUSTED_ORIGINS` / `SESSION_COOKIE_SAMESITE` / `CSRF_COOKIE_SAMESITE` not configured** — Story 1.5 (cross-origin auth flow).
- **`legacy-peer-deps=true` at repo level instead of scoped `overrides`** — to revisit when next-intl publishes Next 16 support.
- **Test settings use SQLite while prod uses pgvector** — Story 1.8 (Row-Level Security tests need real postgres).
- **`export_openapi.py` uses `request=None`** — to revisit if generated schema diverges from live `/api/schema/`.
- **`next.config.ts` is empty stub** — set `output: "standalone"` + `images.remotePatterns` when prod Dockerfile is created (deploy track).
- **No resource limits / non-root containers in Compose** — prod hardening (deploy track).
- **No `CONN_MAX_AGE` / `OPTIONS={"sslmode":"require"}`** — prod hardening (deploy track).
- **MinIO root credentials reused as workload credentials** — create a dedicated service account when RBAC story lands (Story 2.3+).
- **No GH Actions smoke workflow asserting `docker compose up` works** — Sprint 4+ once stack is stable.
- **No SAST / CodeQL / `pip-audit` / `npm audit`** — Sprint 3+.
- **Ruff `select` lists drift between api and ai-service** — when Python patterns converge (Sprint 3+, create root `ruff.toml`).
- **Mixed FR / EN policy for docs and code** — write style guide in `docs/patterns/` (Sprint 2+).
