# Deferred Work

Items flagged during code reviews but consciously deferred. Each has a target story or trigger condition.

## Deferred from: code review of 1-1-initialisation-projet (2026-05-14)

- **`verify_jwt` no-op stub** — to be hardened in Story 3.1 (ai-service scoring activation).
- ~~**`apiFetch` no timeout / no RFC 7807 parsing** — Story 1.5 (login flow + error handling).~~ **Resolved in Story 1.5 (2026-05-26):** `apps/web/src/lib/api/client.ts` now applies a 15s default timeout via `AbortSignal.timeout` + `AbortSignal.any` composition with the caller-supplied signal. RFC 7807 parsing arrives with the auth flow's typed error consumers (`gdpr_exceptions.py` Problem Details).
- **`bulletins-encrypted` bucket has no SSE config** — Story 2.3 (upload bulletins) must call `PutBucketEncryption` + versioning + deny-public ACL.
- ~~**`CSRF_TRUSTED_ORIGINS` / `SESSION_COOKIE_SAMESITE` / `CSRF_COOKIE_SAMESITE` not configured** — Story 1.5 (cross-origin auth flow).~~ **Resolved in Story 1.5 (2026-05-26):** `prod.py` enforces strict `CSRF_TRUSTED_ORIGINS` (raises `ImproperlyConfigured` if unset); `staging.py` is forgiving (env-driven). SameSite + Secure flags follow Django defaults in HTTPS-only envs.
- **`legacy-peer-deps=true` at repo level instead of scoped `overrides`** — to revisit when next-intl publishes Next 16 support.
- ~~**Test settings use SQLite while prod uses pgvector** — Story 1.8 (Row-Level Security tests need real postgres).~~ **Resolved in Story 1.8 (2026-05-24):** `make test-rls` runs the `postgresql_only` + `rls` suite under `path_advisor.settings.test_postgres` against a non-superuser PG role provisioned by the `rls-tests` CI job. SQLite fast path remains the default for the ~95 % of tests that have no RLS dependency.
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

## Deferred from: code review of 1-11-export-portabilite-rgpd (2026-05-24)

- **`_build_zip` charge l'archive entière en BytesIO** — viole l'anti-pattern §3.2 "ne télécharge pas l'archive en mémoire". OK MVP (exporters accounts+audit < 100 KB), critique en Story 2.3 quand bulletins.pdf entreront dans l'archive. À reprendre avec `tempfile.NamedTemporaryFile()` + `upload_fileobj` en streaming dans Story 2.3 ou story dédiée.
- **`[locale]` routing + next-intl namespace `gdpr` non câblés** — cohérent avec Story 1.3/1.14 qui n'utilisent pas next-intl non plus. Cross-cutting i18n à reprendre en Epic 7 (découverte publique SEO multilingue).
- **Relative timestamps + tooltip absolu manquants** (UX polish AC8) — implémentation actuelle affiche uniquement `formatDateTime` absolu. À reprendre quand le design-system livre un composant `<RelativeTime>` partagé.
- **Playwright `e2e/gdpr-export.spec.ts` manquant** — infra Playwright non bootstrapée pour 1.x (aucune story 1.x n'a livré de e2e). Cross-cutting story dédiée à créer pour bootstrap + tests des parcours PRD critiques.
- **`build_export` sans `transaction.atomic` global + pas de reaper task pour `in_progress` stuck** — scénario : DB connection drop entre la transition `PENDING → IN_PROGRESS` et `IN_PROGRESS → READY`, la ligne reste bloquée pour toujours (l'idempotence guard refuse de re-picker). Risque faible MVP ; ajouter un reaper Celery beat quotidien qui flip `IN_PROGRESS > 1h` vers `FAILED` en growth.
- ~~**CSRF token silently optional sur POST** (`readCsrfCookie() ?? undefined`) — pattern à harmoniser avec Story 1.5 login flow qui livrera le contrat CSRF strict.~~ **Résolu en Story 1.5 (2026-05-26) :** les callers `loginUser` / `requestPasswordReset` / `confirmPasswordReset` font systématiquement `readCsrfCookie() ?? (await fetchCsrfToken())` avant la POST, ce qui garantit un token CSRF présent (jamais `undefined`). Le pattern à propager aux endpoints existants (exports GDPR notamment) reste à faire — voir nouvelle entrée Story 1.5.

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
- ~~**`exclude_token_endpoints` workaround comment + TODO test** — Story 1.5 (login) ré-inclura ces endpoints avec `@extend_schema`.~~ **Résolu en Story 1.5 (2026-05-26) :** `ThrottledLoginView` / `ThrottledPasswordResetView` / `ThrottledPasswordResetConfirmView` portent leurs `@extend_schema` décorateurs et apparaissent dans `/api/schema/`. Le workaround `exclude_token_endpoints` reste pour les endpoints `/api/v1/auth/token/*` que dj-rest-auth expose par défaut mais qu'on n'utilise pas (session-cookie only, ADR-0004).
- **Rate limit `X-Forwarded-For` trust** — production gateway config (Caddy + `RATELIMIT_TRUSTED_PROXIES`). Deploy track.
- **Signal-based activation transaction atomicity** — Story 1.13 (audit log) durcira avec retry idempotent Celery.
- **CI gate "[À DÉFINIR]" detection sur build prod `/legal/rgpd`** — implementation simple (`grep -lr "À DÉFINIR" .next/server` exit ≠ 0) à ajouter dans une story deploy/CI dédiée.

## Deferred from: planning of 1-8-multi-tenant-rls-postgresql (2026-05-17)

- **Duplicate `set_actor_from_request` calls in audit views** — once Story 1.8's `TenantSessionMiddleware` lands, the manual calls at [apps/api/apps/audit/views.py:53,191](apps/api/apps/audit/views.py) (added defensively in Story 1.13 T5.7) become redundant. Keep them in 1.8 for safety; remove in a follow-up cleanup story once the middleware has run a full sprint without issues.
- **Demote local `path_advisor` Postgres role from superuser** — Story 1.8 accepts that local dev silently bypasses RLS (relies on `make test-rls` + CI for enforcement). Fixing this requires a non-superuser app role + a separate migration role in `docker-compose.yml` + `infra/postgres/init.sql`. Deploy-track.
- **Staging environment provisioning** — Story 1.8 §6 Q2 surfaced that no staging env exists yet. If/when it's created, revisit migrations that add NOT-NULL columns to existing tables (currently `parental_consents.tenant_id` uses a one-shot `UPDATE` safe only because the table is empty in every env).

## Deferred from: implementation of 1-12-suppression-compte-rgpd (2026-05-24)

- **Re-registration of the same email during the 30-day grace window** — pre-hard-delete, the `users.email` unique constraint still blocks signup with the deleted user's email. UX cost: minor. Workaround: cancel the deletion first, OR wait the 30 days. A "mass-rename on soft-delete to `deleted+<ulid>@deleted.local`" alternative was considered and rejected for MVP (additional surface area for the 0-user scale). Revisit if re-registration friction surfaces in support tickets.
- **`_terminate_user_sessions` O(N) over all Django sessions** — the helper iterates the full `Session` table to find rows matching `_auth_user_id`. Acceptable at MVP scale (≤ 500 active sessions). When the session store migrates to Redis (Sprint 4+ likely), reduce to a single SCAN+DEL.
- **Token-in-URL log leakage carry-over from Story 1.4** — the cancel-deletion URL embeds the 256-bit token in the path. Same mitigation as parental-consent (log-scrubber config at the gateway, in the deploy track). Documented in Story 1.4's deferred section; flagged here for completeness.
- **Stripe subscription cancellation on hard-delete (Story 5.x dependency)** — when the `billing/` app lands, it MUST add a `pre_delete` signal on User that cancels active subscriptions via the Stripe API. The cascade contract CI script does not enforce this (Stripe lives outside the DB). Cross-reference: `docs/patterns/account-deletion.md` §"Anti-patterns" lists it.
- **Bulletins-encrypted S3 cleanup (Story 2.3 dependency)** — when Story 2.3 ships, add `("BULLETINS_BUCKET", "bulletins-encrypted/{user_id}/")` to `settings.GDPR_USER_OWNED_S3_PREFIXES`. The sweep registry-driven design accepts the new prefix without touching `_purge_s3_prefixes`.
- **Configurable grace window per tenant (B2B)** — the 30 days is hard-coded in `GDPR_ACCOUNT_DELETION_GRACE_DAYS`. A B2B school contracting for a tighter window (e.g., 7 days for a cohort export) would currently need a settings override. Defer to Sprint 4+ when a B2B contract surfaces the need.
- **DPO-triggered immediate hard-delete (skip the grace window)** — for "user under court order to be erased *now*" scenarios. Currently requires manual `manage.py shell` work (set `hard_delete_after = now() - 1`, fire the sweep). Document in the runbook as the workaround; add a proper admin action when the legal team flags the gap.
- **`gdpr.account_hard_deleted` audit row written for "user_already_absent" case** — if the User row is gone before the sweep runs (manual delete via shell, or a previous failed sweep that died after `user.delete()`), the audit row is still written with `metadata.reason = "user_already_absent"`. This is correct behaviour but worth flagging — DPO inspections will see slightly different metadata shapes for the two paths.
- **Plaintext password in Celery task arguments for the confirmation email path** — for Story 1.12, the password never crosses a Celery boundary (the confirmation email is synchronous). Carry-over from Story 1.11's deferred item is informational only here.

## Deferred from: code review of 1-12-suppression-compte-rgpd (2026-05-24)

- **Worker clock skew vs DB clock during sweep** — if Celery worker `timezone.now()` runs ahead of PostgreSQL `now()`, the sweep candidate filter (`hard_delete_after__lte=now()`) can pick up rows whose 30-day grace has not actually elapsed in DB-clock terms. Mitigation: NTP on workers + DB hosts. Operational, not code; revisit if incident.
- **Migration 0007 reverse drops `account_deletion_requests` table** — destructive on rollback; loses the 3-year audit retention for any in-flight rows. Acceptable for a brand-new table (no historical data to lose), but the partitioning / archival story should plan an explicit "archive before rollback" runbook.
- **Migration 0008 reverse leaves orphan `auth_permission` row** — `AlterModelOptions` removing `permissions` does not delete the already-granted `auth_permission` table row. Low-impact (DPO would re-grant it on re-apply); add a `RunPython` cleanup to a future migration story if needed.
- **`email__iexact` lookup race vs CITEXT unique index** — pre-existing concern from Stories 1.3 / 1.4; the login serializer's case-insensitive lookup can match a row that the underlying unique index considers distinct. Mitigation: migrate `users.email` to CITEXT (or add a functional unique on `LOWER(email)`) when convenient.
- **No advisory lock on the sweep task** — two concurrent `accounts.sweep_account_deletions` invocations (e.g. operator runs `delay()` while beat fires) can serialise on `select_for_update` but inflate attempt counters via timeouts. MVP runs Celery beat as a singleton, so this is currently moot; add `pg_advisory_lock("sweep_account_deletions")` when the deployment topology demands it.
- **CI gate `assert_user_cascade.py` misses M2M `through=` policies and env-specific apps** — script only inspects `ForeignKey`/`OneToOneField`, and runs in `settings.local` so apps gated by `if env == "prod"` slip past. Extend to (a) walk `_meta.many_to_many` through tables and (b) iterate every settings module declared in `apps/api/path_advisor/settings/`. Sprint 4+.
- **Distributed token brute-force not stopped by per-IP cap** — 256-bit cancel-token entropy makes brute-force economically infeasible; per-IP 30/h cap (or 5/h post-patch) still allows a 1000-IP botnet to bombard the endpoint at 5000-30000/h. Acceptable given entropy; revisit if abuse surfaces.
- **UX: deletion confirmation does not warn that the email is unusable during the 30-day grace** — pre-hard-delete, the `users.email` unique constraint blocks re-signup. UX could surface this in the ConsentDialog or the post-soft-delete page. Defer to UX iteration.
- **`password_hash_at_request` can drift if user rotates password via DPO during grace window** — spec §4.5 #4 explicitly accepts this: cancel-time auth checks against the CURRENT hash, not the snapshot. The snapshot is forensic-only. No-op for MVP; revisit if forensic continuity is challenged.
- **Non-DB session backend is not purged on soft-delete** — `_terminate_user_sessions` iterates `Session` table rows decoded with the current SECRET_KEY. Redis-backed or signed-cookie sessions would survive the soft-delete and let the deleted user keep a tab alive until session expiry. Revisit on the Redis-session migration story.
- **Story 1.12 frontend strings inline FR — `accountDeletion.*` i18n namespace missing** — Spec T8 last subtask mandated `useTranslations("accountDeletion")` for every user-facing line, but the implementation ships ~30 FR string literals inline in `delete-account-section.tsx`, `cancel-deletion-form.tsx`, `account-deleted/page.tsx`, and the cancel landing. Refactor when Story 7.7 (i18n foundation) ships and locks the next-intl pattern; until then there's no second locale to support so the deferral is materially zero-cost.
- **DPO sign-off needed on the "pseudonymisation by absence" claim** — `docs/patterns/account-deletion.md` (Story 1.12 §AC7 contract) describes the audit log row referencing a hard-deleted user as pseudonymised. The pseudonymisation is via the absence of the linking User row, NOT via cryptographic hashing of the ULID. CNIL may consider a stable direct identifier still PII (Article 4(1)) — get explicit DPO sign-off before production launch and record the decision in an ADR. If sign-off is denied, the remediation is to hash `subject_id`/`actor_id` at write time post-cascade (breaks hash-chain consistency unless a double-hash scheme is designed).

## Deferred from: implementation of 1-5-connexion-email-password (2026-05-26)

- **Timing side-channel on `/api/v1/auth/password/reset/`** — the known-email branch hits the email backend (synchronous SMTP queue in MVP) while the unknown-email branch returns immediately after the audit write. A patient attacker timing the response over many requests could distinguish the two paths despite the identical 200/body shape. MVP mitigation = per-IP 5/h cap on the request endpoint; revisit when (a) abuse surfaces in audit logs or (b) email sending moves to a Celery task with a randomised delay floor (Story 8.1 — email transactional abstraction).
- **`gdpr_exceptions.py` rename to `auth_exceptions.py` (or split)** — the module is now broader than its original name suggests: it carries `AccountLocked`, `AccountSuspended`, `EmailNotVerified` (Story 1.5) alongside `AccountDeleted` (Story 1.12) and the existing GDPR-flow exceptions (Stories 1.11 / 1.12). Cosmetic refactor — touch every importer (~ 8 files). Defer to a Sprint-3 cleanup story; risk of merge churn now is higher than the readability gain.
- **MFA hook in `PathAdvisorLoginSerializer.validate()`** — Story 1.6 (MFA TOTP for staff) will intercept the success path of the login serializer and return `{"mfa_required": true, "mfa_session": "<short-lived token>"}` for users whose role is `path_admin` or `support`, instead of completing the login. The serializer is structured so the MFA branch slots in between `super().validate(attrs)` succeeding and `login_security.clear_failed_attempts(user=attrs["user"])` running — the lockout reset MUST happen on MFA challenge success, not on password-only success.
- **`_truncate_ip` / `_hash_email_for_audit` consolidation** — both helpers currently live as private functions in `apps/api/apps/accounts/views.py`. Per spec §4.1 "third-consumer rule", once a third audit-writing endpoint outside `accounts/` needs them, lift them into `apps/core/text.py` (or `apps/audit/redaction.py`). Today's consumers: `ThrottledLoginView` + `ThrottledPasswordResetView` + `ThrottledPasswordResetConfirmView` — all in `accounts/`, so the threshold is not yet tripped.
- **`completion email` for password reset is best-effort** — `ThrottledPasswordResetConfirmView` calls `get_adapter(request).send_mail("account/email/password_reset_completed", ...)` inside a `try/except` that only logs warnings. A delivery failure does NOT roll back the password change. Acceptable because the password is already changed at this point and the user just authenticated via the reset link, but a Celery-backed delivery + retry would be more robust. Tie-in: Story 8.1 (email transactional abstraction with DLQ + observability).
- **Propagate the strict CSRF pattern to pre-Story-1.5 POST callers** — Story 1.5 standardises `readCsrfCookie() ?? (await fetchCsrfToken())` for its three new endpoints. The Story 1.11 GDPR export client (`apps/web/src/lib/api/gdpr.ts`) and Story 1.12 account-deletion client still use `readCsrfCookie() ?? undefined`. Migrate them in a tiny follow-up PR once Story 1.5 lands and the helper pattern is settled.
- **`apiFetch` RFC 7807 typed error parsing** — Story 1.5's auth callers manually inspect `response.json()` for the `type` URN to discriminate (e.g., `…/account-locked` vs `…/email-not-verified`). A typed `ApiProblem` parser at the `apiFetch` layer (returning a discriminated union) would remove the per-caller boilerplate. Cross-cutting refactor; defer until the third caller outside `auth.ts` needs it.

## Deferred from: code review of 1-5-connexion-email-password (2026-05-27)

- **Password-reset request endpoint timing oracle (deleted vs unknown vs active)** — allauth's `PasswordResetForm.get_users()` filters `is_active=True`, so deleted users hit the audit row but produce no SMTP traffic — distinguishable from never-existed and active in wall-clock time. Documented in spec §4.5 #8. Mitigation: defer the SMTP send to Celery with a randomised delay floor (Story 8.1 — email transactional abstraction).
- **`terminate_user_sessions` is a no-op for non-DB session backends** — the helper iterates `Session` table rows (DB backend). signed_cookies / Redis / cached_db backends would leave sessions alive past soft-delete and password-reset. Tracked in Story 1.12's deferred-work too; migrate the helper when the session backend changes.
- **Redis `cache.add(...) + cache.incr(...)` TTL slide race under heavy concurrency** — the SET-NX + INCR pair is not atomic; counter could reset on TTL boundary, defeating the 15-min lockout window. Mitigation requires a Lua script or Redis MULTI. MVP volume does not justify the complexity; revisit if abuse logs surface a burst-pattern bypass.
- **`ThrottledPasswordResetView.post` does not audit `auth.password_reset_requested_invalid` for malformed-email-field 400s** — if `super().post()` raises a 400 from the serializer's email-format validator, no audit row is written. Low-impact (the known/unknown branches are already covered by dedicated audit actions; malformed format is self-evident in HTTP logs). Add when an abuse pattern justifies it.

## Deferred from: code review Pass 2 of 2-8-composant-scenario-loader (2026-06-09)

Pass 2 re-review on commit `2849c1d` of the Pass 1 fix. 3 new defers (the 1 H + 2 M were patched in pass-2 fix commit).

- **(PR4) Crossfade aria-live cascade may over-announce on some screen readers** — Outer `<section role="status">` is a live region; phraseIndex changes mutate its text content, and SR behavior on the resulting announcement is implementation-specific (VoiceOver tends to read only the diff, NVDA may read the whole region including `aria-label` + caption). Not testable in jsdom. Address in the Story 2.3+ VoiceOver/NVDA manual a11y checklist when consuming `ScenarioLoader` for the real OCR wait.
- **(PR5) `tertiaryLink` object identity in M9 focus effect deps** — Passing a fresh `{label, onClick}` literal every render makes the focus effect re-run constantly. The `document.activeElement === document.body` guard prevents focus theft in the normal path, but narrowing the deps to `[primary.isDisabled, secondary.isDisabled, tertiary?.isDisabled, Boolean(tertiary)]` (or memoising the prop in the caller) would skip unnecessary re-runs. Low impact.
- **(PR6) Rapid `isError: true → false → true` batched into one render may miss the recovery emission** — If React batches the renders, the recovery effect never sees `isError === false` between the two flips, leaving `erroredEmittedRef` set and the second error silent on analytics. Realistic only for caller code that programmatically toggles `isError` synchronously back-to-back, which the API surface does not encourage. Narrow trigger surface; revisit if production analytics show a gap.
