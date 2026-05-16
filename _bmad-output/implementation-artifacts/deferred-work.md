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

## Deferred from: code review of 1-2-design-system-tokens (2026-05-16)

- **Rename `bg-bg` / `bg-bg-2` → `surface` / `surface-raised`** — clearer semantics; rename will touch every future component, defer to a harmonisation story (Sprint 3+).
- **`forced-colors: active` (Windows High Contrast Mode)** — accessibility hardening, Sprint 4+.
- **`letterSpacing` missing on h1/h2/h3 fontSize tokens** — browser default is fine for short headings; revisit if typographic regressions appear.
- **Pin exact `wcag-contrast@3.0.0`** — caret OK while no surprise minor; revisit if a release breaks the tests.
- **Tighten contrast test for `brand on bg` to ≥ 5.0:1** — current threshold is the WCAG AA minimum (4.5); measured value is 5.2. Tightening would catch silent regressions earlier.
- **Mixed FR / EN comments in `tokens.css` / `tailwind-plugin.ts` / `tailwind.config.ts`** — resolved during code review (converted to EN); tracking item closed.
