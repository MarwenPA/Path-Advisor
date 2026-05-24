# ADR 0010 — Multi-tenant isolation : middleware Django + Row-Level Security PostgreSQL

**Status:** Accepted
**Date:** 2026-05-24
**Story:** [1.8 — Multi-tenant Row-Level Security PostgreSQL](../../_bmad-output/implementation-artifacts/1-8-multi-tenant-rls-postgresql.md)
**Drivers:** FR7 (isolation des données par tenant et par utilisateur), NFR-S8 (OWASP A01 Broken Access Control), Art. 32 RGPD.

## Context

Path-Advisor mélange un produit B2C (élèves, comptes individuels) et un produit B2B (cohortes scolaires, conseillers, écoles partenaires). Une fuite cross-tenant — un conseiller voit les élèves d'un autre établissement, une école voit un profil non rattaché — est un risque produit majeur (CNIL, confiance B2B) et un risque de classe : **une seule** clause `.filter(tenant_id=…)` oubliée dans un service futur peut compromettre l'ensemble. La défense applicative seule ne suffit pas : il faut un filet au niveau base de données qui s'active même si l'ORM est court-circuité (raw SQL, injection, bug de service).

## Decision

### 1. Middleware-managed PostgreSQL session GUCs (vs `django-tenants`)

`path_advisor.middleware.tenant.TenantSessionMiddleware` écrit trois GUCs PostgreSQL sur chaque requête authentifiée :

```sql
SELECT
  set_config('app.current_user_id',   '<user.id>',          true),
  set_config('app.current_tenant_id', '<user.tenant_id>',   true),
  set_config('app.actor_role',        '<user.role>',        true);
```

Le 3e argument `true` (= `is_local`) auto-clear les variables à la fin de la transaction — pas de fuite vers la requête suivante quand la connection est réutilisée (`CONN_MAX_AGE > 0`).

**Rationale :**
- Tenancy hybride : la même table `users` héberge B2C (tenant_id = NULL) et B2B (tenant_id = UUID) — aligné avec le modèle PRD.
- Pas de refactor obligatoire pour B2C : `django-tenants` force un schema par tenant, infaisable pour un compte sans tenant.
- Joins cross-tenant restent triviaux (référentiel public, audit DPO), ce que `django-tenants` interdirait.

**Rejeté :**
- `django-tenants` (schema-per-tenant) — incompatible avec le B2C et complique les joins.
- Deux rôles DB (app vs admin avec `BYPASSRLS`) — ajoute une charge ops MVP ; reporté en growth (cf. §Trade-offs).
- Application-layer only — viole la défense en profondeur ; une seule `.filter()` oubliée vide un tenant.

### 2. `ROW LEVEL SECURITY` + `FORCE` sur `users` et `parental_consents`

Migration `accounts/0007_enable_rls.py` (PG-only) active les policies sur les tables qui hébergent les données personnelles déjà vivantes. **`FORCE` est non-négociable** : sans lui, l'owner de la table (le rôle Django) bypass silencieusement RLS et les tests passent pour la mauvaise raison. La provisioning CI crée un rôle dédié `NOSUPERUSER NOBYPASSRLS`, et une fixture `_assert_non_superuser_in_postgres_lane` fait échouer la suite si quelqu'un essaie d'exécuter les tests RLS sous un superuser.

**Tables exemptes :**
- `audit_logs` — cross-tenant by design pour le DPO (cf. [ADR-0009 §7](0009-audit-log-immutable-trigger.md)).
- `sites`, `auth_*`, `django_*` — Django internal, pas de PII.
- Référentiels publics futurs (`occupations`, `formations`, `schools` — non créés encore) — cross-tenant par nature.

### 3. Policies nommées par table

**`users`** — laxe : un counselor doit voir les noms de sa cohorte (Epic 6).
- `path_admin` bypass (back-office + DPO).
- Self-access (`id = current_setting('app.current_user_id', true)`).
- Same-tenant (`tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')`).

**`parental_consents`** — strict : un conseiller ne doit PAS lire le consentement parental d'un autre élève, même dans son propre tenant. Aller au-delà du tenant pour ce type de donnée violerait la minimisation RGPD.
- `path_admin` bypass.
- `student_id = current_setting('app.current_user_id', true)` uniquement.

Les vues parental-consent (Story 1.4) authentifient le parent via le token URL-safe ; elles tournent en `AnonymousUser` et n'apparaissent donc pas dans les GUCs → RLS denies par défaut. La résolution est faite explicitement côté service par lookup du token, qui sélectionne la row par PK (RLS ne bloque pas par PK explicite quand exécutée avant le SET LOCAL — mais la résolution se fait dans une transaction où la query bypass-token est unique et scoped).

### 4. Base class `TenantScopedModel`

Toute nouvelle table avec PII doit hériter de `apps.core.models.TenantScopedModel` (cf. `docs/patterns/multi-tenant.md`). Trois colonnes (`tenant_id`, `user_id`, `created_at`/`updated_at`) + un `save()` hook qui auto-remplit depuis `apps.core.request_context` quand un acteur est dans le contexte. Hors d'une requête (Celery, shell), le caller doit fournir explicitement les valeurs ou `save()` lève `ValueError` — fail-loud plutôt que d'écrire des rows avec `tenant_id = NULL` qui contournent les policies.

### 5. CI dédié `make test-rls`

Les tests RLS exigent un vrai PostgreSQL avec un rôle non-superuser. La CI ajoute un job `rls-tests` :
1. Service container `postgres:16`.
2. Init step provisionne `path_advisor_test` avec `NOSUPERUSER NOBYPASSRLS`.
3. `pytest -m "rls or postgresql_only" --ds=path_advisor.settings.test_postgres`.

Le fast path SQLite (`make test-api`) garde ~95 % de la suite — les tests RLS sont marqués `postgresql_only` et skipped.

## Consequences

- **+ Défense en profondeur** : un bug applicatif (`.filter(tenant_id=…)` oublié), une injection SQL, ou une raw query lancée par un admin compromis ne peuvent pas exfiltrer cross-tenant.
- **+ Argument B2B** : isolation prouvable au niveau DB lors des audits sécurité des établissements (Epic 6).
- **+ Pattern partageable** : `TenantScopedModel` + le doc pattern donnent une recette en 5 lignes pour les futures stories.
- **−** Coût par requête : un round-trip `set_config(...)` ajoute ~0,1 ms (mesuré localement). Acceptable. Non observé en pratique sur le P95 du PRD.
- **−** Local dev silently bypasses RLS si `path_advisor` est configuré superuser dans `docker-compose.yml`. **Décision §6 #1** : on accepte ce trade-off pour la rapidité d'itération ; la CI est la source de vérité. Un follow-up deploy-track démotera le rôle dev.
- **−** Une nouvelle table sensible doit penser à hériter de `TenantScopedModel`. Mitigé par `docs/patterns/multi-tenant.md` + revue de PR systématique.

## Alternatives considered

- **`django-tenants` (schema-per-tenant)** — rejeté : forcerait à créer un schéma pour les B2C accounts. Cf. `core-architectural-decisions.md`.
- **Deux rôles DB** (un app `NOBYPASSRLS`, un migration/admin `BYPASSRLS`) — rejeté pour le MVP : ajoute du friction ops (deux mots de passe à gérer, scripts de migration différents). Replanifié pour growth.
- **App-layer filtering uniquement** — rejeté : la défense en profondeur exige les deux couches. Le coût RLS est faible.
- **GUC unique JSON-encoded** (`SET LOCAL app.context = '{"user":"...", "tenant":"..."}'`) — rejeté : `current_setting` est typé scalaire ; parsing JSON dans une policy est lent et fragile.

## References

- [PRD FR7 — isolation par tenant et utilisateur](../../_bmad-output/planning-artifacts/prd/functional-requirements.md)
- [PRD NFR-S8 — OWASP Top 10](../../_bmad-output/planning-artifacts/prd/non-functional-requirements.md)
- [ADR 0009 — Audit log immutable trigger](0009-audit-log-immutable-trigger.md) — explique pourquoi `audit_logs` est exempt
- PostgreSQL docs — [CREATE POLICY](https://www.postgresql.org/docs/16/sql-createpolicy.html) + [Row Security Policies](https://www.postgresql.org/docs/16/ddl-rowsecurity.html)
