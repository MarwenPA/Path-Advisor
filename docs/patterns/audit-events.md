# Audit events catalog

Source canonique des événements `<domain>.<action>` persistés dans `audit_logs` (cf. [ADR 0009](../adr/0009-audit-log-immutable-trigger.md)).

**Règle d'or :** quand tu touches des données personnelles d'un élève (lecture sensible, mutation, refus RBAC), tu **dois** décorer le service avec `@audit_action("ton.event")` et **ajouter ton event ici** dans la même PR.

## Convention de nommage

- Format : `<domain>.<action>` au **présent simple actif** (ex. `outreach.profile_sent` — pas `outreach.profile_sending` ni `outreach.profile_sent_event`).
- `domain` = capacité fonctionnelle du PRD (accounts → `user.`, outreach → `outreach.`, etc.).
- `action` = verbe au passé/présent décrivant ce qui s'est passé côté système.
- Un event = une action atomique (pas de "user.signed_up_and_verified" — c'est 2 events).

## Convention de `metadata`

`metadata` est un `JSONField` libre. Règles :

- **Aucune PII brute** : pas de `password`, `email`, `birth_date`, `bulletin_raw`. Si tu as besoin de référer un user → `actor_id` / `subject_id` (déjà ULID préfixé non-PII).
- **Snake_case** end-to-end (cohérent avec le reste de l'API).
- **JSON-sérialisable** : pas de `datetime` ou `Decimal` brut — ISO 8601 string + `default=str` dans `compute_row_hash`.
- **Whitelisté par event** : pour chaque event, documente ci-dessous le schéma exact de metadata. Pas d'ajout silencieux.

## Catalog (MVP — Stories 1.3 + 1.13)

### `user.signed_up`
- **Posé par :** Story 1.3, `apps.accounts.services.auth_service.record_signup_event`.
- **Subject :** `user.id` (l'élève qui s'inscrit).
- **Metadata :** `{"role": str, "status": str, "consent_cgu_version": str}`.

### `user.email_verified`
- **Posé par :** Story 1.3, `apps.accounts.services.auth_service.mark_email_verified`.
- **Subject :** `user.id`.
- **Metadata :** `{"role": str}`.

### `audit.log_queried`
- **Posé par :** Story 1.13, `apps.audit.views.AuditLogListView.list`.
- **Subject :** `null` (méta-audit cross-cutting).
- **Metadata :** `{"filters": {"subject_id"?: str, "actor_id"?: str, "action"?: str, "from"?: ISO8601, "to"?: ISO8601, ...}, "result_count": int}`.

### `audit.log_query_denied`
- **Posé par :** Story 1.13, `apps.audit.permissions.IsPathAdmin.has_permission`.
- **Result :** `denied`.
- **Subject :** `null`.
- **Metadata :** `{"reason": "not_path_admin", "user_role": str, "view": str}`.

### `audit.log_exported`
- **Posé par :** Story 1.13, `apps.audit.views.audit_log_export_csv`.
- **Subject :** `null`.
- **Metadata :** `{"format": "csv", "filters": dict, "row_count": int, "synchronous": bool}`.

### `audit.integrity_check_completed`
- **Posé par :** Story 1.13, Celery task `apps.audit.tasks.verify_chain_integrity`.
- **Subject :** `null`.
- **Result :** `success` si chaîne intacte, `failure` sinon.
- **Metadata :** `{"verified_rows": int, "broken_rows": list[str]}`.

## Catalog (planned — à ajouter par les stories futures)

- `auth.login_succeeded` / `auth.login_failed` — Story 1.5.
- `auth.mfa_challenge_passed` / `auth.mfa_challenge_failed` — Story 1.6.
- `consent.granted` / `consent.revoked` — Stories 1.4, 1.9, 1.10, 1.14.
- `gdpr.export_requested` / `gdpr.export_generated` — Story 1.11.
- `gdpr.account_deletion_requested` / `gdpr.account_deleted` — Story 1.12.
- `parental.consent_requested` / `parental.consent_granted` / `parental.consent_refused` — Story 1.4.
- `profile.bulletin_uploaded` / `profile.bulletin_ocr_completed` — Epic 2.
- `recommendation.computed` / `recommendation.explanation_viewed` — Epic 3.
- `outreach.profile_sent` / `outreach.school_responded` — Epic 5.
- `school.dashboard_accessed` — Epic 5/6.
- `counselor.cohort_dashboard_accessed` — Epic 6.

Ce catalog est non-exhaustif et grandit story par story.

## Anti-patterns

- ❌ `metadata = {"password_hash": user.password}` — jamais de hash sensitive non plus.
- ❌ `metadata = {"birth_date": user.birth_date.isoformat()}` — PII directe ; préférer `{"age_group": "15-18"}` si tu as besoin du contexte.
- ❌ `@audit_action("user.signed_up_and_role_set")` — combiner 2 actions → 1 event.
- ❌ Décorer un endpoint à très haut throughput (ex. `/api/v1/health/`) — le SELECT FOR UPDATE sérialise les writers, ça pue.
- ❌ Importer `apps.audit.models.AuditLog` depuis un autre app — pass through `@audit_action` ou `record_audit`. Le seul import direct autorisé est dans `apps.audit.` lui-même.
