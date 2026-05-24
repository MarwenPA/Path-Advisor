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

## Deferred from: code review of 1-14-composant-consent-dialog (2026-05-16)

- **No regression test for empty `dataMentioned`** — current implementation renders an empty `<ul>` without a label-only fallback. Low-impact edge case (callers in MVP always pass ≥ 1 item); revisit when the component sees real production usage in Stories 1.4, 1.10, 6.7.

## Deferred from: implementation of 1-14-composant-consent-dialog (2026-05-16)

- **Audit log POST of `ConsentMeta`** — `ConsentDialog.onAccept` emits `{ acceptedAt, contentHash }` but no consumer persists it yet. Each consuming feature (1.4 parental, 1.10 revocation, 1.12 deletion, 5.3 paywall, 6.7 counselor consent) must POST to `/api/v1/me/consents` (or equivalent) when Story 1.13 (audit log infra) lands.
- **`axe-core` automated a11y CI gate** — `ConsentDialog` relies on Radix's a11y guarantees + manual screen-reader QA (cf. story §T5). When the 2nd Couche 3 component lands (likely `ScoreVocationnel` Story 3.11), introduce `axe-core` via `vitest-axe` as a cross-cutting story and back-fill it on `ConsentDialog`.
- **Storybook (or equivalent isolation viewer)** — UX spec recommends one Storybook per Couche 3 component. We substitute the `/design-system` showcase for MVP. Re-evaluate at Sprint 4+ when 4-5 Couche 3 composites exist and the page becomes hard to navigate.
- **`ConsentDialog` path may migrate to `components/path-advisor/`** — colocated with `components/ui/` for now (cf. story §4.3). Revisit at Story 3.11 if the `ui/` folder is becoming crowded with custom composites.

## Deferred from: code review of 1-4-inscription-eleve-moins-15-ans-parental (2026-05-24)

- **Token binding via HMAC / IP / UA continuity** — Parental-consent token is the sole auth for the decision moment (256-bit entropy). Adversarial reviewer flagged absence of constant-time comparison + leaked-token replay window. Mitigation acceptable for MVP given entropy; revisit if leaked-token incidents surface.
- **Token in URL path → log leakage** — Parent-landing fetch passes token in URL; logs/observability stores will record it. Move to log-scrubber config in deploy track rather than changing the email-link UX.
- **Case-insensitive email lookup race** — `email__iexact` doesn't use the unique index; pre-existing from Story 1.3, DB constraint still catches collisions. Add a `CITEXT` column when convenient.
- **`student_email_masked` leak via public status endpoint** — Anyone with a valid token can read masked email. Combined with log-scrubbing mitigation, residual risk is acceptable for MVP given 256-bit token entropy.
- **Timezone boundary on age check (server `localdate()` vs frontend `new Date()`)** — 1-day window for users at exactly 15 ans 0 days, locale-dependent. Switch to UTC-midnight comparison everywhere when Story 7.7 (i18n foundation) lands.
- **Real-time grant broadcast (`<LimitedModeBanner />` auto-dismiss)** — Banner doesn't poll; refresh required for users in `pending_parental_consent` to see the grant flip. Polling or SSE in a later story (8.x notifications).
- **Distinct error types for "expired" vs "already-decided"** — Both map to `parental-consent-already-decided` (409) today; UX could differentiate them. Cosmetic.
- **Celery beat schedule has no jitter** — Both parental-consent tasks at 04:00 / 04:15 UTC deterministically. Add `crontab(..., jitter=…)` if multi-tenant volumes spike (post-MVP).
- **`is_fully_active` is a Python property, not a column** — Future admin/metrics queries duplicate the SQL rule. Materialise as a generated column or function-based index later.
- **Plain `parent_email` retained indefinitely** — ADR-0003 claims "≤ 60-day effective use" but no purge job ships. Defer to partitioning/archival story (Sprint 4+) — see also pre-existing item below from implementation review.
- **`_parent_email_pending` transient attribute coupling** — Acceptable but coupling-y. Revisit if allauth ever ships a DRF-native `user_signed_up` signal.

## Deferred from: implementation of 1-4-inscription-eleve-moins-15-ans-parental (2026-05-17)

- **`is_fully_active` gating of premium / envoi anticipé** — Story 1.4 ships the flag and the
  `<LimitedModeBanner />` UI but does NOT gate any feature on it. Stories 5.x (premium subscription)
  and 5.4 (envoi anticipé profil → école) MUST check `is_fully_active` before granting paywall /
  external-dispatch features. Tracked here so the implementers do not forget.
- **Counselor / tiers autorisé fallback for parental consent** — UX spec §Defining Principle #6
  calls for "consentement par tiers autorisé" when no parent is available. Out of MVP scope; revisit
  when Epic 6 ships partner-counselor identity (Story 6.5+).
- **Parent self-service consent revocation post-grant** — UX spec hints at "révocable à tout moment".
  MVP relies on Story 1.10 (revocation via `PermissionList`) + ConsentDialog revoke path. When Epic 6
  ships the Parent Space, parents with real accounts can revoke from their dashboard via
  `parent_user_id` linkage on the ParentalConsent row.
- **Internationalised parental-consent email templates** — French only in MVP. next-intl + per-locale
  rendering = Story 7.7 + Story 8.1 (email transactional abstraction).
- **Address-of-record / residence proof for very-young minors** — some jurisdictions ask for stronger
  proof than email opt-in. Out of MVP scope; LIL art. 7-1 cite documented in ADR-0003. Reopen if
  CNIL guidance shifts post-MVP launch.
- **`parental_consents` table partitioning / archival** — table grows monotonically, no purge in MVP.
  Steady-state under ~10k rows / year at the target funnel — revisit when partitioning is worth the
  Celery beat complexity (Sprint 4+ if volumes exceed projections).
- **Salted hash for `parent_email_hash` in audit metadata** — currently a plain SHA-256 so the same
  parent across multiple children is detectable across audit rows (intentional, ADR-0003). Revisit
  if a post-launch legal review requires unlinkability across rows.
- **Transient `user._parent_email_pending` attribute coupling** — allauth fires `user_signed_up`
  with a plain `WSGIRequest` (no `.data`), so the adapter stashes `parent_email` on the user
  object for the signal handler to read. Acceptable but coupling-y; revisit if allauth ever exposes
  a DRF-native signal alternative or if we move away from allauth.
- **Parent-link `<LimitedModeBanner />` resend cooldown UX** — currently surfaces a single line
  "Trop tôt — réessaie dans une heure" on the 429. A countdown / next-available-at would be
  friendlier; do it when the banner gets real product analytics (Story 10.2+ web push integration).

## Deferred from: code review of 1-13-journal-audit-acces (2026-05-17)

- **Durable retry queue for failed audit writes** — `record_audit` swallow on DB failure is the §9 #4 decision, but a Redis list / outbox-style retry buffer was acknowledged as growth scope. Currently dropped audit events surface only via structlog + Sentry.
- **Email DPO on chain-break detection** — `verify_chain_integrity` Sentry-alerts but doesn't email DPO (per Story §AC6 step 2). Tied to open question §10 #1 (which DPO email address to use in MVP).
- **Documented actor-swap-mid-decorated-function contract** — if a service mutates `request_context` between entry and return, the audit row uses the new actor; behavior is currently undocumented.
- **`_stream_csv` relies on undocumented `csv.writer.writerow` return value** — works on CPython but technically depends on the writer returning whatever `self.write()` returns. Refactor to use a buffered queue if we need to support alternate Python implementations.
- **Sentry `except Exception: pass` blocks** — idiomatic defensive pattern; replace with `log.warning("sentry.capture_failed", ...)` when we add structured-log assertions in tests (likely Story 8.1 — structlog wiring).
- **`AuditLogImmutable` HTTP status 409** — RFC 7231 suggests 403/405 fits "immutability refusal" better than 409 Conflict. Cosmetic, change with care if any client deeply switches on status.
- **`__str__` format `%Y-%m-%dT%H:%M:%SZ`** — `Z` is a literal, not a UTC marker; misleading if timezone is non-UTC. Cosmetic for logging output.
- **`archive_logs_older_than` two-query race window** — `qs.exists()` then `qs.iterator()` can disagree under concurrent inserts; acceptable for monthly batch but document.
- **`archive_old_logs` idempotency on Celery beat double-fire** — overwrite at same S3 key is mostly idempotent but document operationally.
- **`_validated_filters` echoes raw `from`/`to` strings into audit metadata** — hypothetical XSS if metadata is ever rendered as HTML in a UI (none planned MVP).
- **Celery beat timezone unset** — runs UTC; project TIME_ZONE is Europe/Paris. Pure cosmetic offset on schedules (3 AM UTC = 4 AM Paris).
- **No test for `mark_email_verified` / `record_signup_event` failure path** — when `record_audit` returns `None` (DB unreachable), no test asserts the business operation still succeeds. Coverage gap.
- **`postgresql_only` tampering test could use `session_replication_role`** — current test uses `Model.save(...)` to bypass the override; functionally validates chain recompute, but a PG-faithful variant would exercise the actual prod attack vector.

## Deferred from: code review of 1-2-design-system-tokens (2026-05-16)

- **Rename `bg-bg` / `bg-bg-2` → `surface` / `surface-raised`** — clearer semantics; rename will touch every future component, defer to a harmonisation story (Sprint 3+).
- **`forced-colors: active` (Windows High Contrast Mode)** — accessibility hardening, Sprint 4+.
- **`letterSpacing` missing on h1/h2/h3 fontSize tokens** — browser default is fine for short headings; revisit if typographic regressions appear.
- **Pin exact `wcag-contrast@3.0.0`** — caret OK while no surprise minor; revisit if a release breaks the tests.
- **Tighten contrast test for `brand on bg` to ≥ 5.0:1** — current threshold is the WCAG AA minimum (4.5); measured value is 5.2. Tightening would catch silent regressions earlier.
- **Mixed FR / EN comments in `tokens.css` / `tailwind-plugin.ts` / `tailwind.config.ts`** — resolved during code review (converted to EN); tracking item closed.

## Deferred from: code review of 1-3-inscription-eleve-15-ans-rgpd (2026-05-17)

- **a11y consent checkbox label/description coupling (Radix `<button>` vs `htmlFor`)** — Story 1.14 (ConsentDialog) ou story a11y dédiée Sprint 4+.
- **a11y live-region `/auth/verify-email/` + auto-redirect 1.5s** — Story a11y Sprint 4+.
- **Redis graceful degradation pour rate limit** — prod hardening (deploy track Sprint 4+).
- **Email observability (bounce / DLQ / metric)** — Story 8.1 (email transactionnel abstraction).
- **Index sur `consent_cgu_version` / `consent_rgpd_at`** — premature MVP (≤ 500 users) ; revisit ≥ 10k.
- **`consent_cgu_version` 3 sources of truth (model null=True / serializer required / admin)** — Story 1.12 (suppression compte) ou refonte modèle Sprint 3+.
- **`MinorUserFactory` dead code** — sera utilisé par Story 1.4 (inscription < 15 ans avec parental opt-in).
- **`fireEvent.change` → `userEvent.type` dans signup-form tests** — refactor Sprint 4+ story a11y.
- **`z.literal(true)` + `false as unknown as true` casts dans signup-form** — refactor avec `z.boolean().refine`. Story 1.4 ou cleanup pass.
- **`exclude_token_endpoints` workaround comment + TODO test** — Story 1.5 (login) ré-inclura ces endpoints avec `@extend_schema`.
- **Rate limit `X-Forwarded-For` trust** — production gateway config (Caddy + `RATELIMIT_TRUSTED_PROXIES`). Deploy track.
- **Signal-based activation transaction atomicity** — Story 1.13 (audit log) durcira avec retry idempotent Celery.
- **CI gate "[À DÉFINIR]" detection sur build prod `/legal/rgpd`** — implementation simple (`grep -lr "À DÉFINIR" .next/server` exit ≠ 0) à ajouter dans une story deploy/CI dédiée.

## Deferred from: planning of 1-8-multi-tenant-rls-postgresql (2026-05-17)

- **Duplicate `set_actor_from_request` calls in audit views** — once Story 1.8's `TenantSessionMiddleware` lands, the manual calls at [apps/api/apps/audit/views.py:53,191](apps/api/apps/audit/views.py) (added defensively in Story 1.13 T5.7) become redundant. Keep them in 1.8 for safety; remove in a follow-up cleanup story once the middleware has run a full sprint without issues.
- **Demote local `path_advisor` Postgres role from superuser** — Story 1.8 accepts that local dev silently bypasses RLS (relies on `make test-rls` + CI for enforcement). Fixing this requires a non-superuser app role + a separate migration role in `docker-compose.yml` + `infra/postgres/init.sql`. Deploy-track.
- **Staging environment provisioning** — Story 1.8 §6 Q2 surfaced that no staging env exists yet. If/when it's created, revisit migrations that add NOT-NULL columns to existing tables (currently `parental_consents.tenant_id` uses a one-shot `UPDATE` safe only because the table is empty in every env).
