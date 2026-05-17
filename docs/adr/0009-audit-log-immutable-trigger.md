# ADR 0009 — Audit log : table dédiée append-only + trigger PostgreSQL + chaîne SHA-256

**Status:** Accepted
**Date:** 2026-05-17
**Story:** [1.13 — Journal d'audit immuable](../../_bmad-output/implementation-artifacts/1-13-journal-audit-acces.md)
**Drivers:** FR12 (journal consultable par DPO), NFR-S4 (immuable, 3 ans), Art. 30 + Art. 32 RGPD.

## Context

Tout accès aux données personnelles d'un élève par un tiers (parent, conseiller, école, admin) doit être traçable, immuable, et conservé 3 ans. Le DPO doit pouvoir consulter et exporter ces accès pour répondre aux audits CNIL.

## Decision

### 1. Table dédiée `audit_logs` (vs event log généraliste)

Une table SQL dédiée — pas un event log type `outbox` ou Kafka. Rationale :
- Une seule technologie à opérer (PostgreSQL déjà en stack).
- Indexable nativement par `subject_id`, `actor_id`, `action`, `created_at`.
- Requêtes DPO en SQL standard (export CSV trivial).
- Pas de problème de delivery semantics (at-least-once vs exactly-once) d'une queue.

Rejeté : Kafka / event store dédié (over-engineering MVP), append-only file OS-level (audit côté ops, pas côté produit).

### 2. Trigger PostgreSQL `BEFORE UPDATE/DELETE … RAISE EXCEPTION`

L'immuabilité est garantie au niveau base de données par deux triggers PL/pgSQL qui lèvent `P0001` sur toute mutation. Cf. `apps/api/apps/audit/migrations/0002_audit_trigger.py`.

Rationale :
- Source de vérité au niveau le plus bas — un attaquant qui obtient `psql` ne peut pas modifier l'historique sans bypasser explicitement le mécanisme.
- Aucun chemin Django ne peut le contourner (l'UPDATE issue par l'ORM échoue avec `IntegrityError`).
- Trigger réversible via migration `revert_trigger` si on doit refactorer.

Rejeté : pas de trigger (compte sur Django uniquement → trop fragile, manager peut être bypassé via raw SQL).

### 3. Défense en profondeur : manager Python refuse les mutations

`AuditLogQuerySet.update()` et `.delete()` lèvent `AuditLogImmutable(DomainError)` **avant** d'atteindre la DB. `AuditLog.save()` refuse les re-saves sur PK existante. Cf. `apps/api/apps/audit/models.py`.

Rationale :
- Erreur typée (Problem Details RFC 7807) plutôt qu'un `IntegrityError` opaque.
- Aide les devs à voir leur erreur tôt (tests SQLite passent les mêmes vérifs).
- Le trigger PG reste la source de vérité ; le manager est un garde-fou pédagogique.

### 4. Chaîne SHA-256 par row (`prev_hash` + `row_hash`)

Chaque entrée stocke le SHA-256 de `actor_id | action | subject_id | metadata | created_at | prev_hash`. La première entrée a `prev_hash = NULL`. Une tâche Celery mensuelle (`audit.verify_chain_integrity`) recalcule la chaîne et alerte Sentry sur toute rupture.

Rationale :
- Détection d'altération **même si le trigger a été désactivé** (ex. `SET LOCAL session_replication_role = 'replica'`).
- `SELECT … FOR UPDATE` autour de la lookup `prev_hash` sérialise les writers concurrents → chaîne linéaire garantie.
- Hash JSON-stable (`sort_keys=True`) → reproductible.

Rejeté : Merkle tree (over-engineering MVP — single chain suffit pour 100k rows/an), HMAC avec rotation de clé (complexifie la vérification a posteriori).

### 5. IP hashée à l'écriture (vs IP raw + anonymisation différée)

`ip_address_hash = sha256(salt | tenant_id | ip)`. **Jamais d'IP raw stockée.**

Rationale :
- NFR-S6 (purge PII) exige d'anonymiser après 90 jours, mais le trigger immuable empêche tout UPDATE. Hash dès l'écriture résout le dilemme.
- 2 IPs identiques → même hash → on garde la valeur forensique (détecter "même attaquant tente N fois").
- Salt en env var (Doppler prod) — ne jamais rotater post-deploy sans plan de migration.

Cf. `apps/api/apps/core/request_context.py::_hash_ip`.

### 6. Décorateur `@audit_action(...)` comme point d'écriture unique

Toute écriture audit passe par le décorateur (sur services) ou son helper `record_audit(...)` (pour permission classes). **Aucun endpoint POST direct sur `audit_logs`** — surface d'attaque inutile.

Le décorateur ne bloque jamais l'action métier : si la DB audit est down, l'événement est loggué (structlog + Sentry) puis swallowed. Décision pragmatique §9 #4 de la Story 1.13 — la conformité préfère une perte minoritaire d'événements à un blocage produit.

### 7. RLS PostgreSQL **n'est PAS appliquée** sur `audit_logs`

L'audit log est cross-tenant by design : le DPO Path-Advisor a accès à tout. Story 1.8 (RLS) ne touche pas cette table. En growth, un mode "DPO tenant-scoped" sera ajouté côté serializer, pas RLS.

## Consequences

- **+ Conformité légale** : Art. 30 RGPD (registre des traitements) et Art. 32 (mesures de sécurité) couverts.
- **+ Argument B2B** : traçabilité opposable aux établissements scolaires (Epic 6).
- **+ Pattern réutilisable** : le décorateur `@audit_action` est utilisable par toutes les stories sensibles (1.4, 1.10, 1.11, 1.12, 1.14, Epic 3, 5, 6).
- **− Coût en écriture** : 1 INSERT + 1 SELECT FOR UPDATE par event sensible. À surveiller en growth si certains endpoints à très haut throughput utilisent le décorateur.
- **− Volume table** : la rétention 3 ans + non-suppression post-archive donne ~1M rows en growth. À reconsidérer (partitioning `pg_partman`) si >5M.
- **− Salt IP non-rotatable** : compromis assumé — invalidé si on change le salt sans migration.

## Alternatives considered

- **OpenSearch/Elasticsearch dédié audit** — rejeté pour MVP (1 service de plus à opérer, coût > valeur).
- **Append-only Postgres logical replication slot lu par un service externe** — over-engineering MVP.
- **HMAC chain au lieu de SHA-256 simple** — n'apporte pas plus côté détection (le secret HMAC doit aussi être stable), complique la vérification a posteriori.
