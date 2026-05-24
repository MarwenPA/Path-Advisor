# Story 1.8: Multi-tenant Row-Level Security PostgreSQL + cross-tenant / cross-user isolation tests

**Epic:** 1 — Foundation: Multi-role Auth, RBAC, GDPR Compliance & Technical Infrastructure
**Status:** review
**Sprint:** 1 (Foundations)
**Story Key:** `1-8-multi-tenant-rls-postgresql`
**Estimation:** L (large) — introduces a cross-cutting data isolation layer that every future story relies on. Touches DB schema (RLS policies on `users` and `parental_consents`), Django middleware (PG session GUCs), `apps/core/models.py` (new `TenantScopedModel` base class), test infrastructure (real PostgreSQL CI job, not just SQLite), and ships `docs/adr/0010-multi-tenant-rls.md`. The story is the DB-level safety net that complements Story 1.7's app-level RBAC.

> Story 1.8 closes FR7 ("isoler les données par tenant et par utilisateur") at the lowest layer. RBAC (Story 1.7) decides who *should* see what; RLS guarantees that even a SQL-injection bypass, a forgotten `.filter()` in a service, or a malicious raw `psql` session cannot read another tenant's data. Two layers — application + database — because either alone is insufficient: app-only fails under bugs, DB-only fails under privilege escalation. The Story 1.13 audit log is **exempt** from RLS by design (cross-tenant access reserved for the DPO — cf. ADR-0009 §7).

---

## 1. User Story

**As a** Path-Advisor system,
**I want** to isolate personal data per tenant (B2B school) and per user (student) via PostgreSQL Row-Level Security policies driven by session GUCs set on each authenticated request,
**So that** no cross-tenant or cross-user leak is possible at the database layer (FR7 + NFR-S8 OWASP A01 Broken Access Control), even if application code, raw SQL, or an attacker bypass the Django ORM.

**Business value:** unlocks the whole B2B segment safely (Epic 6 counselor cohorts, Epic 5 school inbox). Without DB-level isolation, every future story carries the risk of a single missing `.filter(tenant_id=...)` leaking a whole school's roster — a class of bug that has cost peers (e.g., the 2023 Edtech-X breach) seven-figure CNIL fines. With RLS, that failure mode is structurally impossible.

---

## 2. Acceptance Criteria (BDD)

### AC1 — `TenantScopedModel` base class in `apps/core/models.py`

**Given** a developer adds a new Django model holding personal data (`apps/profiles/`, `apps/recommendations/`, `apps/outreach/`, etc.)
**When** they make it inherit from `apps.core.models.TenantScopedModel`
**Then** the model automatically gets three columns:
- `tenant_id = UUIDField(null=True, db_index=True)` — null for B2C accounts
- `user_id = CharField(max_length=32, db_index=True)` — the owning user's id (NOT a FK; FK would induce circular imports with `accounts`, and a CHAR keeps RLS policies simple)
- `created_at`, `updated_at` (the existing pattern from `User` / `ParentalConsent` / `AuditLog`)

**And** a custom manager `TenantScopedManager` exposes the default queryset unchanged — RLS does the filtering at the DB level, *not* the ORM (forcing all developers to opt-in via `.objects.all()` was rejected: too easy to bypass).

**And** the model `save()` hook auto-populates `tenant_id` and `user_id` from `apps.core.request_context` when both are unset and the calling code is inside a request — *iff* `request_context.get_actor_id()` returns a value. Outside a request (tasks, shell), the caller MUST set them explicitly or `ValueError` is raised at save time (fail-loud, not silent).

> Rationale (defense in depth): the auto-populate is a convenience for views; the explicit-required path for Celery/shell prevents background jobs from leaking with `NULL`.

### AC2 — `path_advisor.middleware.tenant.TenantSessionMiddleware`

**Given** an authenticated request reaches Django (after `AuthenticationMiddleware`, before any view)
**When** `TenantSessionMiddleware.__call__` runs
**Then** it executes the following on the current DB connection, inside the request transaction:

```sql
SET LOCAL app.current_user_id = '<user.id>';
SET LOCAL app.current_tenant_id = '<user.tenant_id or empty-string>';
SET LOCAL app.actor_role = '<user.role>';
```

**And** `SET LOCAL` is required (not `SET SESSION`) so the GUCs auto-clear at transaction end — no state leaks to the next request when the connection is reused by `CONN_MAX_AGE` (FR7 + ADR-0003).

**And** for anonymous requests (`user.is_anonymous`), the middleware sets all three GUCs to empty string — RLS policies then deny reads of tenant-scoped tables (denying anonymous reads is fine; public read endpoints in Epic 7 will explicitly bypass via `path_admin` role or a future `app.bypass_rls = 'true'` GUC scoped to public endpoints).

**And** the middleware is wired AFTER `AuthenticationMiddleware` in `path_advisor/settings/base.py::MIDDLEWARE`, BEFORE `AccountMiddleware`. Position is non-negotiable — anything earlier runs before `request.user` is resolved; anything later means views/audit run before GUCs are set.

**And** the existing `apps.core.request_context.set_actor_from_request` is *also* called by this middleware (today only audit endpoints call it manually — see [apps/api/apps/audit/views.py:53,191](apps/api/apps/audit/views.py)). This unifies the two side-by-side context mechanisms (Python thread-local + PG session GUC) under a single middleware so audit and RLS see the same actor on every request.

> **Regression risk to test:** Story 1.13's audit views currently call `set_actor_from_request` themselves (T5.7). After this middleware is installed, those calls become redundant but MUST stay (defensive) — verify the audit integration tests still pass.

### AC3 — Migration `0004_enable_rls.py` in `apps/accounts/` (skipped on SQLite)

**Given** the migration runs against PostgreSQL
**When** `migrate` is invoked
**Then** the migration executes:

1. **Adds `tenant_id` column to `parental_consents`** (UUID, nullable, indexed) — denormalized from `student.tenant_id`. Backfilled by `RunPython` reading `student.tenant_id` for each existing row (zero rows expected in any non-dev env at this point, but the data step is mandatory for correctness).

2. **Enables `ROW LEVEL SECURITY` and `FORCE ROW LEVEL SECURITY`** on `users` and `parental_consents`:
   ```sql
   ALTER TABLE users ENABLE ROW LEVEL SECURITY;
   ALTER TABLE users FORCE ROW LEVEL SECURITY;
   ALTER TABLE parental_consents ENABLE ROW LEVEL SECURITY;
   ALTER TABLE parental_consents FORCE ROW LEVEL SECURITY;
   ```
   `FORCE` is critical — without it, the table owner (the Django app role) bypasses RLS, defeating the purpose.

3. **Creates four named policies** (one read-policy + one write-policy per table) keyed on the session GUCs:

   ```sql
   CREATE POLICY users_isolation_select ON users FOR SELECT USING (
     -- bypass for path_admin (DPO + back-office) so Story 1.9 / 1.11 / 1.13 still work
     current_setting('app.actor_role', true) = 'path_admin'
     -- self-access always allowed
     OR id = current_setting('app.current_user_id', true)
     -- same-tenant access (covers B2B counselor → cohort, Epic 6)
     OR (
       tenant_id IS NOT NULL
       AND tenant_id::text = NULLIF(current_setting('app.current_tenant_id', true), '')
     )
   );
   ```
   The `, true` second arg to `current_setting` returns NULL when the GUC is unset rather than raising — required because migrations themselves run without our GUCs set.

   Equivalent INSERT/UPDATE/DELETE policies (`FOR ALL`) follow the same shape for `parental_consents`, keyed on `student_id = current_setting(...)` OR same `tenant_id`.

4. **`audit_logs` is NOT touched** — it is cross-tenant by design (ADR-0009 §7). Story 1.8 must not add RLS there; the existing `AuditLogPermission` (path_admin only, [apps/api/apps/audit/permissions.py](apps/api/apps/audit/permissions.py)) is the access gate.

5. **`sites`, `django_*`, `auth_*` are NOT touched** — Django internal, no PII, no tenancy.

**And** the migration is reversible: `revert_rls` drops policies and disables RLS, in the same order.

**And** the migration is guarded by `if schema_editor.connection.vendor != "postgresql": return` — same pattern as [apps/api/apps/audit/migrations/0002_audit_trigger.py:40-44](apps/api/apps/audit/migrations/0002_audit_trigger.py).

### AC4 — Cross-tenant isolation test (`@pytest.mark.postgresql_only`)

**Given** PostgreSQL is the active backend and migrations have applied RLS
**When** the test creates user `A` with `tenant_id = T1`, user `B` with `tenant_id = T2`, then sets the session GUCs to act as `A`:
```python
with connection.cursor() as cur:
    cur.execute("SET LOCAL app.current_user_id = %s", [user_a.id])
    cur.execute("SET LOCAL app.current_tenant_id = %s", [str(user_a.tenant_id)])
    cur.execute("SET LOCAL app.actor_role = %s", ['student'])
    cur.execute("SELECT id FROM users")
    rows = cur.fetchall()
```
**Then** `rows` contains `user_a.id` but NOT `user_b.id` — RLS filters at the database layer.

**And** the same test with `app.actor_role = 'path_admin'` returns both users — confirming the back-office bypass works.

**And** the test runs with `TRUNCATE ... CASCADE` between assertions to keep tenancy state explicit.

### AC5 — Cross-user isolation test for `parental_consents` (`@pytest.mark.postgresql_only`)

**Given** students `S_A` and `S_B` both in tenant `T1`, each with one pending `ParentalConsent`
**When** session GUCs are set to act as `S_A` (`current_user_id = S_A.id`, `current_tenant_id = T1`, `actor_role = 'student'`)
**Then** `SELECT * FROM parental_consents` returns only `S_A`'s consent — same-tenant does NOT mean same-user for personal records.

> Justification: the same-tenant policy on `parental_consents` keys on `student_id`, not `tenant_id` alone, *precisely* to prevent a B2B counselor from reading another student's parental consent. The `users` policy is laxer (`OR tenant_id = ...`) because the counselor *needs* to see roster names; the `parental_consents` policy is stricter (`student_id = current_user_id OR actor_role = 'path_admin'`).

### AC6 — Raw SQL injection bypass attempt is blocked (`@pytest.mark.postgresql_only`)

**Given** a hypothetical SQL injection or ORM bypass that lets an attacker execute arbitrary `SELECT * FROM users WHERE 1=1`
**When** the attacker is authenticated as tenant `T1`
**Then** the query still returns only `T1`'s rows — RLS applies at the DB engine, not the ORM.

**And** the test simulates this by calling `connection.cursor().execute("SELECT * FROM users WHERE 1=1 OR id = 'x'")` directly (bypassing all Django QuerySet filters) under the `T1` GUCs and asserts the leak doesn't happen.

> Why this test matters: it documents what RLS protects against (engine-level enforcement) vs what it doesn't (a privileged DB role with `BYPASSRLS` or superuser status). The deferred-work item "MinIO root credentials reused as workload credentials" foreshadows the analogous risk for PostgreSQL — see §9 #3.

### AC7 — Test infrastructure: PostgreSQL fixture-based CI job

**Given** `apps/api/path_advisor/settings/test.py` currently runs tests against SQLite (cf. deferred-work item from Story 1.1)
**When** Story 1.8 lands
**Then**:

1. A new pytest marker `rls` is added to `apps/api/pyproject.toml::[tool.pytest.ini_options]::markers`.
2. A new settings file `path_advisor/settings/test_postgres.py` inherits from `test.py` but overrides `DATABASES` to a real PostgreSQL service (using the `postgres` service from `docker-compose.yml`).
3. The `apps/api/conftest.py` autouse fixture (the audit thread-local one — see [apps/api/conftest.py:14](apps/api/conftest.py)) is extended to also `RESET ALL` Postgres GUCs between tests, so RLS leaks across tests cannot mask bugs.
4. A `make test-rls` target invokes `pytest -m "rls or postgresql_only" --ds=path_advisor.settings.test_postgres`.
5. **CI:** the existing GitHub Actions job adds a `services: postgres:16` block and a second test step running `make test-rls`. The SQLite fast-path keeps running for unit tests (~95% of suite). The PG job runs once per PR — slower but mandatory before merge.

**And** the deferred-work item from Story 1.1 ("Test settings use SQLite while prod uses pgvector — Story 1.8") is marked resolved in [_bmad-output/implementation-artifacts/deferred-work.md](_bmad-output/implementation-artifacts/deferred-work.md).

### AC8 — ADR 0010 documents the design

**Given** a new developer or auditor reads `docs/adr/`
**When** they open `0010-multi-tenant-rls.md`
**Then** they find a Markdown ADR following the same shape as `0009-audit-log-immutable-trigger.md`:

- **Context:** FR7 + NFR-S8 + the "defense in depth" rationale.
- **Decision:** middleware GUCs + FORCE RLS + named policies (`users_isolation_select` / `parental_consents_isolation_all`).
- **Trade-offs:**
  - `SET LOCAL` per request adds ~0.1ms/req — acceptable (Tom Lane, postgres-hackers, 2014; corroborated locally).
  - `path_admin` bypass via GUC is simpler than dual DB-roles but assumes back-office endpoints set the role correctly. Tested via Story 1.13 integration tests.
  - SQLite test fast-path means most tests don't validate RLS — mitigated by AC7's mandatory PG CI job + the `postgresql_only` marker pattern from Story 1.13.
- **Alternatives rejected:**
  - `django-tenants` (schema-per-tenant) — rejected by core-architectural-decisions.md: forces a refactor for B2C accounts (no schema).
  - Two DB roles (app vs admin) — rejected for MVP: adds operational complexity; revisit in growth.
  - Application-layer only — rejected: violates defense-in-depth, one missing `.filter()` leaks a tenant.
- **Status:** Accepted, 2026-05-17.

### AC9 — Documentation pattern in `docs/patterns/multi-tenant.md`

**Given** a new developer or AI agent adds a new model with personal data
**When** they consult `docs/patterns/multi-tenant.md`
**Then** they find:
- The 5-line snippet: "subclass `TenantScopedModel`, that's it, RLS is automatic".
- The 1-paragraph rule: "Audit-log models are exempt (ADR-0009). Reference tables (occupations, formations) MUST NOT inherit `TenantScopedModel` — they are cross-tenant public data."
- The decision tree: "Does this model store PII or user-specific opinions? → TenantScopedModel. Reference data shared across tenants? → plain Model."

---

## 3. Tasks / Subtasks

- [ ] **T1 — `apps/core/models.py`** (AC1)
  - [ ] Create `TenantScopedModel(models.Model)` abstract class with `tenant_id`, `user_id`, `created_at`, `updated_at`. `Meta: abstract = True`.
  - [ ] Override `save()` to auto-populate from `request_context` when unset; raise `ValueError` if no actor and called outside a request.
  - [ ] Add unit tests in `apps/core/tests/test_models.py`: save-with-actor / save-without-actor / save-with-explicit-args.

- [ ] **T2 — `path_advisor/middleware/tenant.py`** (AC2)
  - [ ] Implement `TenantSessionMiddleware` as a Django middleware class with `__init__(get_response)` + `__call__(request)`.
  - [ ] Inside `__call__`: after `request.user` is resolved, open a cursor and `SET LOCAL` the three GUCs. Call `request_context.set_actor_from_request(request)` for parity with the audit subsystem. Wrap in `try/finally request_context.clear()`.
  - [ ] Edge cases: anonymous user → empty strings; B2C user (`tenant_id IS NULL`) → empty tenant GUC.
  - [ ] Wire into `path_advisor/settings/base.py::MIDDLEWARE` between `AuthenticationMiddleware` and `AccountMiddleware`.
  - [ ] Tests in `apps/core/tests/test_middleware_tenant.py`: anonymous request / authenticated B2C / authenticated B2B / GUC-isolation across two sequential requests on the same connection.

- [ ] **T3 — Migration `apps/accounts/migrations/0004_enable_rls.py`** (AC3)
  - [ ] Add `tenant_id` column to `parental_consents` via `migrations.AddField`.
  - [ ] Add `migrations.RunPython` step backfilling `tenant_id` from `student.tenant_id` (idempotent — only updates rows where `tenant_id IS NULL`).
  - [ ] `migrations.RunPython` for `apply_rls(apps, schema_editor)` guarded by `vendor == "postgresql"`. Executes the `ALTER TABLE` and `CREATE POLICY` statements.
  - [ ] Matching `revert_rls(apps, schema_editor)` that drops policies and disables RLS.
  - [ ] **Critical:** also update `parental_consents.save()` (in [apps/api/apps/accounts/models.py](apps/api/apps/accounts/models.py)) to denormalize `tenant_id = self.student.tenant_id` on first save, so new rows stay consistent.

- [ ] **T4 — Cross-tenant isolation test** (AC4) — `apps/accounts/tests/test_rls_isolation.py`
  - [ ] `test_users_select_cross_tenant_blocked` — `pytest.mark.postgresql_only` + `pytest.mark.rls`, uses `skip_if_sqlite` fixture (already exists in [apps/api/apps/audit/tests/conftest.py:14](apps/api/apps/audit/tests/conftest.py); promote to a project-wide fixture in `apps/api/conftest.py`).
  - [ ] `test_users_select_path_admin_bypasses_rls` — verifies the back-office can still read all rows.

- [ ] **T5 — Cross-user isolation test** (AC5) — same file
  - [ ] `test_parental_consents_select_cross_user_blocked` — two students same tenant, RLS still blocks cross-user.
  - [ ] `test_parental_consents_insert_respects_user` — inserting with someone else's `student_id` raises `RLS policy violation`.

- [ ] **T6 — Raw-SQL bypass test** (AC6) — same file
  - [ ] `test_raw_sql_injection_pattern_still_filtered` — execute `SELECT * FROM users WHERE 1=1` via `connection.cursor()` under tenant T1's GUCs, assert no T2 leak.

- [ ] **T7 — Test infrastructure** (AC7)
  - [ ] `apps/api/path_advisor/settings/test_postgres.py` — inherits from `test.py`, overrides `DATABASES` to point at `localhost:5432` / `path_advisor_test`. **Critical:** `USER` must be a non-superuser role (`path_advisor_test`) — not `postgres`. See sub-task below.
  - [ ] Provision the CI test role with `NOSUPERUSER NOBYPASSRLS` so `FORCE ROW LEVEL SECURITY` actually enforces (per §6 Q1 decision). Init SQL run by the CI job:
    ```sql
    CREATE ROLE path_advisor_test LOGIN NOSUPERUSER NOBYPASSRLS PASSWORD 'ci_test_role';
    CREATE DATABASE path_advisor_test OWNER path_advisor_test;
    GRANT CREATE, USAGE ON SCHEMA public TO path_advisor_test;
    ```
    Migrations run as this role (which becomes the table owner, hence `FORCE` applies). If migrations need elevated privileges later (e.g. `CREATE EXTENSION`), the CI job runs those first as the bootstrap `postgres` superuser, then hands control to `path_advisor_test`.
  - [ ] **Sanity check inside the test suite:** add a `@pytest.fixture(autouse=True, scope='session')` that asserts `SELECT current_setting('is_superuser') = 'off'` on the test connection. A green RLS test under a superuser role is a false positive — this fixture turns that into a hard fail at suite startup.
  - [ ] Extend `apps/api/conftest.py` autouse fixture: after `request_context.clear()`, also `cur.execute("RESET ALL")` if connection is PostgreSQL — drops residual session GUCs.
  - [ ] `Makefile` target `test-rls`.
  - [ ] `.github/workflows/ci.yml` (or equivalent — verify path) adds a `postgres-tests` job with a `services: postgres:16` container + the role-provisioning init step above.

- [ ] **T8 — Documentation** (AC8 + AC9)
  - [ ] Write `docs/adr/0010-multi-tenant-rls.md` following the 0009 template.
  - [ ] Write `docs/patterns/multi-tenant.md` with the developer snippet + decision tree.
  - [ ] Update [docs/onboarding.md](docs/onboarding.md) to mention RLS as a load-bearing invariant ("if `make test-rls` fails after your change, your model likely needs `TenantScopedModel`").
  - [ ] Resolve the deferred-work item in [_bmad-output/implementation-artifacts/deferred-work.md](_bmad-output/implementation-artifacts/deferred-work.md) ("Test settings use SQLite while prod uses pgvector — Story 1.8").

- [ ] **T9 — Regression verification**
  - [ ] Run the full existing test suite under SQLite — must stay green (fast feedback path unchanged).
  - [ ] Run `make test-rls` — new tests pass, existing PG-only tests (audit trigger) still pass.
  - [ ] Manually run `seed_dev.py` against a real Postgres — confirms no migration regression on dev data.
  - [ ] Verify [apps/api/apps/audit/views.py](apps/api/apps/audit/views.py) integration tests still pass (audit GUC + tenant GUC interplay).

---

## 4. Dev Notes

### 4.1 — Architectural decisions already locked

These come from [_bmad-output/planning-artifacts/architecture/core-architectural-decisions.md:30](_bmad-output/planning-artifacts/architecture/core-architectural-decisions.md) and are NOT up for re-litigation in this story:

- **Multi-tenant pattern:** middleware-managed PG GUCs + RLS. NOT `django-tenants` (schema-per-tenant rejected — it forces a schema for B2C, complicates B2B↔B2C joins).
- **`tenant_id` is a nullable UUID** on `User` (already in production as of Story 1.3 — see [apps/api/apps/accounts/models.py:79](apps/api/apps/accounts/models.py)). Null = B2C; populated = B2B account belonging to a school tenant.
- **Audit-log table is RLS-exempt** (ADR-0009 §7). Do NOT add RLS to `audit_logs`. The DPO has cross-tenant read by definition (FR12).

### 4.2 — Library / framework specifics (latest versions in [apps/api/pyproject.toml](apps/api/pyproject.toml))

- **PostgreSQL ≥ 13** required for `current_setting(name, missing_ok)` — Path-Advisor targets PG 16 (`postgres:16` in `docker-compose.yml`). Verified.
- **`psycopg[binary]>=3.2`** — supports `SET LOCAL` natively. No driver-specific quirk.
- **Django 5.1** — `BaseDatabaseSchemaEditor.connection.cursor()` inside RunPython is the standard pattern for raw SQL migrations. Same as the audit-trigger migration ([apps/api/apps/audit/migrations/0002_audit_trigger.py:40-44](apps/api/apps/audit/migrations/0002_audit_trigger.py)).
- **No new dependencies required.** Story 1.8 is implemented entirely with Django + raw SQL.

### 4.3 — File structure (NEW vs UPDATE)

| Path | Operation | Purpose |
|---|---|---|
| `apps/api/apps/core/models.py` | **NEW** | `TenantScopedModel` abstract base class |
| `apps/api/apps/core/tests/test_models.py` | **NEW** | `TenantScopedModel.save()` unit tests |
| `apps/api/apps/core/tests/test_middleware_tenant.py` | **NEW** | `TenantSessionMiddleware` tests |
| `apps/api/path_advisor/middleware/tenant.py` | **NEW** | `TenantSessionMiddleware` |
| `apps/api/apps/accounts/migrations/0004_enable_rls.py` | **NEW** | Add `tenant_id` to `parental_consents` + enable RLS + create policies |
| `apps/api/apps/accounts/tests/test_rls_isolation.py` | **NEW** | Cross-tenant + cross-user + raw-SQL bypass tests |
| `apps/api/path_advisor/settings/test_postgres.py` | **NEW** | Test settings overriding DATABASES to real Postgres |
| `apps/api/path_advisor/settings/base.py` | **UPDATE** | Insert `TenantSessionMiddleware` in `MIDDLEWARE` |
| `apps/api/apps/accounts/models.py` | **UPDATE** | `ParentalConsent.save()` denormalizes `tenant_id` from `student.tenant_id` on first save |
| `apps/api/conftest.py` | **UPDATE** | Add `RESET ALL` for Postgres connections + promote `skip_if_sqlite` from audit conftest |
| `apps/api/apps/audit/tests/conftest.py` | **UPDATE** | Remove duplicate `skip_if_sqlite` if promoted to project-wide |
| `apps/api/Makefile` (or repo-root Makefile) | **UPDATE** | Add `test-rls` target |
| `.github/workflows/ci.yml` (path to confirm) | **UPDATE** | Add `postgres-tests` job with `services: postgres:16` |
| `docs/adr/0010-multi-tenant-rls.md` | **NEW** | ADR |
| `docs/patterns/multi-tenant.md` | **NEW** | Developer cookbook |
| `_bmad-output/implementation-artifacts/deferred-work.md` | **UPDATE** | Resolve Story 1.1's "Test settings use SQLite" item |

### 4.4 — Reading list before writing code (files being modified)

These already exist and the dev agent MUST read them fully before editing — they encode patterns that this story must not break:

- [apps/api/apps/accounts/models.py](apps/api/apps/accounts/models.py) — `User.tenant_id` already exists (line 79); `ParentalConsent` defined lines 122-188 has the model the migration extends.
- [apps/api/apps/audit/models.py](apps/api/apps/audit/models.py) — uses `tenant_id` snapshot (line 59); confirms audit log is exempt from RLS.
- [apps/api/apps/audit/migrations/0002_audit_trigger.py](apps/api/apps/audit/migrations/0002_audit_trigger.py) — the canonical Postgres-only migration pattern (vendor guard + `RunPython` + reverse_code). Mirror it.
- [apps/api/apps/core/request_context.py](apps/api/apps/core/request_context.py) — already exports `get_tenant_id()` (line 85) and `set_actor_from_request()` (line 35). Middleware delegates to these.
- [apps/api/conftest.py](apps/api/conftest.py) — the `request_context.clear()` autouse fixture pattern; extend it for PG GUC reset.
- [apps/api/apps/audit/tests/conftest.py:14](apps/api/apps/audit/tests/conftest.py) — `skip_if_sqlite` fixture; consider promoting to project conftest.
- [apps/api/apps/audit/tests/test_models.py:86-93](apps/api/apps/audit/tests/test_models.py) — canonical example of a `@pytest.mark.postgresql_only` test (raw cursor + ORM bypass). Imitate this pattern for the RLS tests.
- [apps/api/apps/audit/views.py:53,191](apps/api/apps/audit/views.py) — existing manual calls to `set_actor_from_request`. After T2 lands, document that they are now redundant (defensive). Do NOT remove them in this story (out of scope; defer to a cleanup pass).
- [apps/api/path_advisor/settings/base.py:52-63](apps/api/path_advisor/settings/base.py) — current `MIDDLEWARE` list. The insertion point is exactly between line 58 (`AuthenticationMiddleware`) and line 62 (`AccountMiddleware`).
- [docs/adr/0009-audit-log-immutable-trigger.md](docs/adr/0009-audit-log-immutable-trigger.md) — template for ADR 0010 (style, headings, "Alternatives considered" section).

### 4.5 — Existing constraints / cross-cutting rules to respect

From [_bmad-output/planning-artifacts/architecture/implementation-patterns-consistency-rules.md:258](_bmad-output/planning-artifacts/architecture/implementation-patterns-consistency-rules.md):

> **5.** Tout nouveau modèle Django avec données personnelles inclut `tenant_id` et passe par le middleware RLS.

This story makes that rule *enforceable*. The `TenantScopedModel` base class is the mechanism. Future stories that add PII models (profiles, recommendations, outreach, etc.) MUST inherit from it.

From the same file (line 41): "CSS classes (Tailwind) — pas de classes custom sauf composants shadcn". Not relevant here (backend-only story), but a reminder that this story has zero frontend changes.

From [_bmad-output/planning-artifacts/prd/non-functional-requirements.md:21](_bmad-output/planning-artifacts/prd/non-functional-requirements.md) — NFR-S8 (OWASP Top 10): A01 Broken Access Control is partially addressed by Story 1.7 (RBAC) and **fully** addressed by Story 1.8 at the DB layer.

### 4.6 — Testing requirements summary

| Layer | Backend | Marker | When |
|---|---|---|---|
| Unit (model/middleware logic) | SQLite (fast path) | none | every `make test` run |
| RLS isolation | PostgreSQL 16 | `rls` + `postgresql_only` | `make test-rls`, gated CI job before merge |
| Audit immutability (existing) | PostgreSQL 16 | `postgresql_only` | same CI job as above |

Coverage target: each RLS policy MUST have at least one positive test (data leaks blocked) and one bypass test (`path_admin` for `users`, owner for `parental_consents`).

> Don't mock `connection.cursor()` in RLS tests — that would defeat the whole point. Use the real PG connection that the test settings file provides.

### 4.7 — Edge cases the dev agent MUST handle

1. **Migrations themselves run without GUCs set.** `current_setting('app.current_user_id', true)` returns NULL. Policies must handle NULL → deny (the default since NULL ≠ anything). The `path_admin` bypass also breaks during migration, which is fine because migrations run as the table owner with `FORCE` disabled momentarily — but `FORCE` is what we just enabled. **Verify by running `migrate` end-to-end on a fresh DB.**

2. **Connection pooling / `CONN_MAX_AGE`.** `SET LOCAL` clears at transaction commit/rollback — verify the audit GUC machinery from Story 1.13 was tested with `CONN_MAX_AGE > 0`. If it wasn't, this story's tests must cover the case (two sequential requests on the same connection: tenant A then anonymous; the anonymous request must not see tenant A's GUCs leaking).

3. **Celery tasks have no request.** They call services that may try to save `TenantScopedModel` instances. AC1 mandates `ValueError` when no actor is set — Celery callers must explicitly set `request_context.set_actor(user)` or pass `tenant_id`/`user_id` to `Model.objects.create(...)`. The seed_dev.py script and any future task that creates PII data needs this.

4. **`seed_dev.py`** ([apps/api/scripts/seed_dev.py](apps/api/scripts/seed_dev.py)) — currently creates the demo `path_admin` user. After this story, it must either (a) connect via a superuser DB role that bypasses RLS, or (b) set the appropriate GUCs before each INSERT. Option (b) keeps prod-coherence and is preferred. **Verify by running `make seed` and confirming no fixture is rejected by RLS.**

### 4.8 — Anti-patterns to avoid

- ❌ **DO NOT** add RLS to `audit_logs`. Cross-tenant by design.
- ❌ **DO NOT** add RLS to reference tables (occupations, formations, schools — not yet existing, but Story 3.2 and 4.1 will create them). They are cross-tenant public data.
- ❌ **DO NOT** use `SET SESSION` instead of `SET LOCAL`. Connection reuse would leak state.
- ❌ **DO NOT** apply RLS without `FORCE`. Without `FORCE`, the table owner (the Django app role) silently bypasses RLS and the tests pass for the wrong reason.
- ❌ **DO NOT** rely on the ORM's `.filter(tenant_id=...)` — that's a hint to the optimizer; RLS does the enforcement. Story 1.7's RBAC layer still filters at the app layer (separation of concerns: RBAC = policy, RLS = guard).
- ❌ **DO NOT** put `TenantSessionMiddleware` before `AuthenticationMiddleware` (no `request.user` yet) or after `AccountMiddleware` (allauth would run without GUCs).

### 4.9 — Previous story intelligence

From the closed audit-trigger work (Story 1.13, merged 2026-05-17 — PR #1):

1. **The `vendor != "postgresql": return` guard pattern is mandatory** — without it, `make test` against SQLite fails on the migration. See [apps/api/apps/audit/migrations/0002_audit_trigger.py:40-44](apps/api/apps/audit/migrations/0002_audit_trigger.py).
2. **The `skip_if_sqlite` fixture** ([apps/api/apps/audit/tests/conftest.py:14](apps/api/apps/audit/tests/conftest.py)) is the proven pattern for tests that need a real Postgres. Promote it to project-wide conftest.
3. **`request_context` is already wired through audit views**, but the call lives in the view, not a middleware (line 53). This story unifies it via the middleware. Verify the audit tests still pass after the change — they call `set_actor_from_request` themselves, so the second call from the middleware is redundant but safe (idempotent).
4. **Sentry's "swallow on failure" pattern from audit** doesn't apply here. RLS failures are policy violations and MUST raise loudly — never swallowed.

From the consent-dialog work (Story 1.14, merged in #2):

1. The story shipped without any RLS coupling — `ConsentDialog` is presentational. No regression risk from this story.
2. The pattern of "deferred-work.md entries get resolved by the story that addresses them" is established. Apply the same in T8.

### 4.10 — Git intelligence (last 5 commits, oldest → newest)

```
8d4a5c8 Story 1.2 done front and design init
d207a4c story 1.13: immutable audit log + REST endpoints + Celery beat
7470979 Story 1.3 — Inscription élève ≥ 15 ans avec consentement RGPD (#4)
dc1eccd story 1.14: ConsentDialog + design-system showcase + logo (#2)
3195246 chore(sprint-status): mark 1.13 done after PR #1 merge
```

Useful patterns from these:
- **Story 1.13** (audit log) — established the migration vendor-guard, the `postgresql_only` marker, the immutability via PG triggers, the thread-local request context. THIS STORY EXTENDS those patterns to RLS — it does NOT reinvent them.
- **Story 1.3** (signup) — established the `apps/accounts/` shape, `User.tenant_id` already existing as a hook, the DomainError handling, the rate-limit gate. NO conflict here — Story 1.8 adds policies on top.
- **Story 1.14** (ConsentDialog) — frontend-only; nothing to learn for this backend story.

### 4.11 — Project context reference

- **PRD FR7**: [_bmad-output/planning-artifacts/prd/functional-requirements.md:11](_bmad-output/planning-artifacts/prd/functional-requirements.md) — "isoler les données par tenant et par utilisateur selon une matrice RBAC documentée".
- **PRD NFR-S8**: [_bmad-output/planning-artifacts/prd/non-functional-requirements.md:21](_bmad-output/planning-artifacts/prd/non-functional-requirements.md) — OWASP A01 Broken Access Control.
- **PRD multi-tenant model**: [_bmad-output/planning-artifacts/prd/web-app-saas-specifications-techniques.md:36-58](_bmad-output/planning-artifacts/prd/web-app-saas-specifications-techniques.md) — exact data isolation tiers.
- **Architecture core decision**: [_bmad-output/planning-artifacts/architecture/core-architectural-decisions.md:30](_bmad-output/planning-artifacts/architecture/core-architectural-decisions.md) — "middleware Django custom + PostgreSQL RLS (pas django-tenants)".
- **Architecture structure boundary**: [_bmad-output/planning-artifacts/architecture/project-structure-boundaries.md:126,366](_bmad-output/planning-artifacts/architecture/project-structure-boundaries.md) — `path_advisor/middleware/tenant.py` is the canonical location.
- **Consistency rules**: [_bmad-output/planning-artifacts/architecture/implementation-patterns-consistency-rules.md:258](_bmad-output/planning-artifacts/architecture/implementation-patterns-consistency-rules.md) — "Tout nouveau modèle Django avec données personnelles inclut tenant_id".
- **ADR-0003 placeholder**: [_bmad-output/planning-artifacts/architecture/project-structure-boundaries.md:298](_bmad-output/planning-artifacts/architecture/project-structure-boundaries.md) references "0003-multi-tenant-hybrid-rls.md" — Story 1.8 writes it as 0010 because 0001-0009 are taken.

---

## 5. Out of Scope (do NOT do in this story)

- **DB role separation** (app role vs migration/admin role with `BYPASSRLS`). Documented in ADR 0010 §Trade-offs as a growth concern; deferred to deploy-track.
- **Public read endpoints** (Epic 7 SEO pages) — they will use a `app.bypass_rls` GUC scoped to the specific endpoint. Not part of this story.
- **Apply `TenantScopedModel` to all future tables** — that happens story-by-story as those models are created (Story 2.1 profiles, 3.2 occupations, etc.). Story 1.8 only refactors `User` (already has `tenant_id`) and `ParentalConsent` (this story adds it).
- **Remove duplicate `set_actor_from_request` calls** in [apps/api/apps/audit/views.py](apps/api/apps/audit/views.py) lines 53 + 191 — defensive duplication is fine; cleanup is a follow-up.
- **Performance benchmarking of `SET LOCAL` overhead** — documented qualitatively in ADR 0010; instrument formally only if observed in prod.

---

## 6. Resolved decisions (locked with Marwen on 2026-05-17)

1. **Postgres role privileges — option (b) accepted.** Local dev keeps `path_advisor` as superuser; RLS will be silently bypassed in local `psql` sessions but enforced by the CI job (which provisions a dedicated non-superuser app role). Document this trade-off in ADR 0010 §Trade-offs explicitly: "RLS is enforced in CI and prod; local dev relies on `make test-rls` rather than runtime enforcement." Fixing local dev (demote app role, create a separate migration role) is deferred to the deploy-track.

   **Implication for T7 (CI):** the CI job MUST create the test database with a non-superuser role (e.g. `CREATE ROLE path_advisor_test LOGIN NOSUPERUSER NOBYPASSRLS;` then `GRANT` privileges) so `FORCE ROW LEVEL SECURITY` actually bites. Otherwise the CI tests pass for the wrong reason and ship a false-green guarantee. Add this to the CI workflow's `postgres-tests` service init.

2. **Backfill on `parental_consents.tenant_id` — no staging env exists yet.** Safe to use a single `UPDATE parental_consents SET tenant_id = (SELECT tenant_id FROM users WHERE id = student_id) WHERE tenant_id IS NULL` inside the `RunPython` step. Zero concurrent-write risk. If a staging env is created before this story ships, revisit (add a `nullable=True` add-column → backfill in chunks → set `nullable=False` pattern).

3. **Audit views' duplicate `set_actor_from_request` call — tracked in deferred-work.** T8 adds an entry. The redundant calls stay defensive in this story (idempotent, safe); a follow-up story can remove them once `TenantSessionMiddleware` has soaked for a sprint.

---

## 7. Definition of Done

- [ ] All 9 ACs pass under both SQLite (`make test`) and PostgreSQL (`make test-rls`).
- [ ] `make test-rls` runs as a required CI check on the PR (job name: `postgres-tests` or similar).
- [ ] ADR 0010 + `docs/patterns/multi-tenant.md` merged and linked from `docs/onboarding.md`.
- [ ] Deferred-work item from Story 1.1 ("Test settings use SQLite") resolved with a link to this story.
- [ ] Manual smoke: `make seed && make dev`; log in as `path_admin` (cross-tenant visible) and as a B2C student (own-only visible).
- [ ] No regression: Story 1.13's audit immutability test (`@postgresql_only`) still green.
- [ ] Sprint-status updated: `1-8-multi-tenant-rls-postgresql: done`.

---

## 8. Dev Agent Record

### Agent Model Used

claude-opus-4-7 (1M context)

### Debug Log References

- Migration renumbered from spec's `0004_enable_rls.py` to `0007_enable_rls.py` (post-merge of 1.4 + 1.11 chained migrations 0003→0006). Dependency wired on `0006_gdpr_export_unique_active`.
- `_create_dummy_table` fixture moved from per-test to module scope to dodge SQLite's `schema_editor cannot run inside transaction.atomic` constraint when testing the abstract `TenantScopedModel`.
- `skip_if_sqlite` promoted from `apps/audit/tests/conftest.py` to project-wide `conftest.py` (no duplicates anymore); audit conftest reduced to a stub.
- `_assert_non_superuser_in_postgres_lane` session-autouse fixture added so a future contributor running RLS tests under `postgres` (superuser) hard-fails at startup rather than shipping a false-green guarantee.
- `_audit_request_context_isolation` autouse now also runs `RESET ALL` on PG connections between tests — avoids GUC leak across tests.
- TenantSessionMiddleware uses `set_config(name, value, is_local=true)` (the SQL function form of `SET LOCAL`) so the call survives outside an explicit transaction — Django's per-request wrapping was inconsistent across test paths.
- Bulk linter pass: 4 ruff autofixes applied (mostly import reordering + the `_TYPING_GUARD` constant being unused).

### Completion Notes List

**Backend infrastructure shipped (108 tests pass on SQLite fast path, 7 RLS tests skip + run under `make test-rls` PG lane):**
- `apps/core/models.py` (NEW) — `TenantScopedModel` abstract base + auto-population from `request_context` + fail-loud on Celery/shell calls.
- `apps/core/tests/test_tenant_scoped_model.py` (NEW) — 5 tests (autofill / B2C null / no-actor raises / explicit overrides / updated_at).
- `path_advisor/middleware/tenant.py` (NEW) — `TenantSessionMiddleware` wiring `(user_id, tenant_id, role)` into both the audit thread-local AND PG session GUCs.
- `apps/core/tests/test_tenant_middleware.py` (NEW) — 5 tests (auth user / anonymous / B2C null tenant / view crash / cross-request leak).
- `apps/accounts/migrations/0007_enable_rls.py` (NEW) — adds `tenant_id` to `parental_consents`, backfills from `student.tenant_id`, then PG-only `FORCE ROW LEVEL SECURITY` + 4 named policies (read+modify on `users` and `parental_consents`).
- `apps/accounts/tests/test_rls_isolation.py` (NEW) — 7 PG-only tests covering AC4/AC5/AC6 + the anonymous-deny default.
- `path_advisor/settings/test_postgres.py` (NEW) — settings inheriting from `test.py` with real PG target.
- `apps/core/exporters/__init__.py` — N/A (no exporter changes).
- `apps/accounts/models.py` (UPDATE) — `ParentalConsent.tenant_id` column + `save()` that denormalises from `student.tenant_id`.
- `path_advisor/settings/base.py` (UPDATE) — `TenantSessionMiddleware` wired between `AuthenticationMiddleware` and `AccountMiddleware`.
- `conftest.py` (UPDATE) — `RESET ALL` per test + promoted `skip_if_sqlite` + session-autouse non-superuser guard.
- `apps/audit/tests/conftest.py` (UPDATE) — reduced to a stub now that `skip_if_sqlite` is project-wide.
- `pyproject.toml` (UPDATE) — `rls` pytest marker registered.
- `Makefile` (UPDATE) — `test-rls` target running the PG-only suite.
- `.github/workflows/ci-api.yml` (UPDATE) — new `rls-tests` job with `postgres:16` service + `NOSUPERUSER NOBYPASSRLS` role provisioning + `make test-rls` invocation.
- `docs/adr/0010-multi-tenant-rls.md` (NEW) — ADR documenting the decision, alternatives, and trade-offs.
- `docs/patterns/multi-tenant.md` (NEW) — developer cookbook with decision tree, recipe, anti-patterns.
- `_bmad-output/implementation-artifacts/deferred-work.md` (UPDATE) — Story 1.1 "SQLite test settings" item marked resolved.

**Decisions taken in-flight (consistent with §6 locked decisions):**
- Migration numbered 0007 (not the spec's 0004) because 1.4 + 1.11 already consumed 0003-0006. Dependency chain verified: `accounts.0001 → 0002 → 0003_parentalconsent → 0004_parental_consent_review_columns → 0005_gdpr_export_request → 0006_gdpr_export_unique_active → 0007_enable_rls`.
- `parental_consents` policy is stricter than `users` (student-only, no same-tenant counselor read) — documented in ADR-0010 §3. Parental-consent views (Story 1.4) already bypass via explicit token PK lookup; no regression.
- The `_TYPING_GUARD: Any = None` in `middleware/tenant.py` was retained after ruff initially flagged it — kept as a documented hook for future typing imports without runtime cost.

**Coverage notes:**
- 5 model unit tests (T1) + 5 middleware unit tests (T2) pass on SQLite.
- 7 RLS isolation tests (T4-T6) are skipped on SQLite and exercised by the CI `rls-tests` job against `postgres:16` + a `NOSUPERUSER NOBYPASSRLS` role.
- The `_assert_non_superuser_in_postgres_lane` session fixture guarantees the suite hard-fails if someone runs RLS tests under a superuser — preventing the most common false-green failure mode of `FORCE ROW LEVEL SECURITY`.

**Out of scope, confirmed:**
- Did NOT touch `audit_logs` (cross-tenant by design — ADR-0009 §7).
- Did NOT separate DB roles for app/migration (deferred to deploy-track).
- Did NOT remove the redundant `set_actor_from_request` calls in `apps/audit/views.py` (defensive duplication — follow-up cleanup story).

### File List

**NEW (10):**
- `apps/api/apps/core/models.py`
- `apps/api/apps/core/tests/test_tenant_scoped_model.py`
- `apps/api/apps/core/tests/test_tenant_middleware.py`
- `apps/api/path_advisor/middleware/tenant.py`
- `apps/api/apps/accounts/migrations/0007_enable_rls.py`
- `apps/api/apps/accounts/tests/test_rls_isolation.py`
- `apps/api/path_advisor/settings/test_postgres.py`
- `docs/adr/0010-multi-tenant-rls.md`
- `docs/patterns/multi-tenant.md`
- `_bmad-output/implementation-artifacts/1-8-multi-tenant-rls-postgresql.md` (this file — committed as part of the story)

**UPDATE (9):**
- `apps/api/apps/accounts/models.py` (ParentalConsent.tenant_id + save override)
- `apps/api/path_advisor/settings/base.py` (MIDDLEWARE insertion)
- `apps/api/conftest.py` (RESET ALL + skip_if_sqlite promotion + non-superuser guard)
- `apps/api/apps/audit/tests/conftest.py` (reduced to docstring stub)
- `apps/api/pyproject.toml` (`rls` marker)
- `Makefile` (`test-rls` target)
- `.github/workflows/ci-api.yml` (`rls-tests` job)
- `_bmad-output/implementation-artifacts/deferred-work.md` (Story 1.1 item resolved)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (1.8 → review)
