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

## Story 1.12 — Account deletion (GDPR Article 17, right to erasure)

### `gdpr.account_deletion_requested`
- **Posé par :** `apps.accounts.services.account_deletion.request_deletion` (via `@audit_action`).
- **Actor :** the user themselves.
- **Subject :** the user.
- **Metadata :** `{"deletion_request_id": "adr_…", "hard_delete_after": "ISO 8601"}`.
- **Side-effect tracked :** soft-delete + session teardown + confirmation email.

### `gdpr.account_deletion_cancelled`
- **Posé par :** `cancel_deletion` (self-service via token OR DPO admin override).
- **Actor :** the user (self-service path) OR the DPO user (admin override).
- **Subject :** the deletion request's `user_id_snapshot`.
- **Metadata :** `{"deletion_request_id": "adr_…", "via": "user_self_service" | "dpo_override", "cancel_reason": "<prefixed string>"}`.

### `gdpr.account_hard_deleted`
- **Posé par :** `hard_delete` from the Celery sweep `accounts.sweep_account_deletions`.
- **Actor :** `actor_id=NULL`, `actor_role="system"`.
- **Subject :** the user (written BEFORE `user.delete()` so the FK cascade does not affect the row — `subject_id` is a CharField).
- **Metadata :** `{"deletion_request_id": "adr_…", "s3_keys_deleted": int, "s3_prefixes": [...], "cascade_row_counts": {<model_label>: int}}`.

### `gdpr.account_hard_delete_failed`
- **Posé par :** sweep task on a per-row exception (S3 outage, lock contention, …).
- **Subject :** the deletion request's `user_id_snapshot`.
- **Metadata :** `{"deletion_request_id": "adr_…", "error_code": "<class_name>", "attempt": int}`.

### `gdpr.account_hard_delete_giving_up`
- **Posé par :** sweep task when `attempt_count >= GDPR_ACCOUNT_DELETION_MAX_HARD_DELETE_ATTEMPTS` (default 7).
- **Subject :** the deletion request's `user_id_snapshot`.
- **Metadata :** `{"deletion_request_id": "adr_…", "max_attempts": int, "last_failure_code": "<class_name>"}`.
- **DPO action required :** row is frozen until manual investigation; see `docs/runbooks/gdpr-request.md`.

## Story 1.5 — Login + per-account lockout + password reset

### `auth.login_succeeded`
- **Posé par :** `ThrottledLoginView.post` after `super().post()` returns 200.
- **Actor :** the user themselves (from `self.user` set by dj-rest-auth's `login()`).
- **Subject :** the user.
- **Metadata :** `{"email_hashed": "<sha256>", "ip_truncated": "<…/24 or …/48>", "user_agent": "<truncated 200>"}`.

### `auth.login_failed`
- **Posé par :** `ThrottledLoginView.post` on any rejection (wrong password, unknown email, suspended/unverified/deleted).
- **Actor :** `None`.
- **Subject :** the user `id` if the email matched a real user, otherwise `None` (NEVER reflected in the HTTP response — internal DPO signal for enumeration detection).
- **Metadata :** `{"email_hashed": "<sha256>", "ip_truncated": "<…>", "user_agent": "<truncated>", "reason": "invalid_credentials_or_unknown_email" | "AccountSuspended" | "EmailNotVerified" | "AccountDeleted" | "unknown_email"}`.
- **Note :** the unknown-email branch is auto-flagged via `metadata.reason = "unknown_email"` so DPO filtering can spot enumeration sweeps without changing the public 400 shape.

### `auth.login_blocked_locked`
- **Posé par :** `ThrottledLoginView.post` when the serializer's `is_account_locked` check fires (user already locked, password not even checked).
- **Subject :** the user.
- **Metadata :** same shape as `auth.login_failed`.
- **DPO action :** patterns of `login_blocked_locked` from the same `ip_truncated` against many `subject_id`s = credential-stuffing probe.

### `auth.account_locked`
- **Posé par :** `login_security.record_failed_attempt` when the N-th failure (default 5) trips the lockout column.
- **Subject :** the user.
- **Metadata :** `{"window_seconds": 900, "lock_duration_seconds": 600, "unlock_at": "<ISO>", "ip_truncated": "<…>"}`.

### `auth.password_reset_requested`
- **Posé par :** `ThrottledPasswordResetView.post` for KNOWN emails.
- **Subject :** the user.
- **Metadata :** `{"email_hashed": "<sha256>", "ip_truncated": "<…>"}`.

### `auth.password_reset_requested_unknown`
- **Posé par :** `ThrottledPasswordResetView.post` for UNKNOWN emails.
- **Subject :** `None`.
- **Metadata :** `{"email_hashed": "<sha256>", "ip_truncated": "<…>"}`.
- **Note :** distinct action name (not just metadata.reason) so the DPO enumeration query is a single `WHERE action = 'auth.password_reset_requested_unknown'` — no body parsing needed.

### `auth.password_reset_completed`
- **Posé par :** `ThrottledPasswordResetConfirmView.post` after `super().post()` returns 200 + side-effects (sessions purged, lockout cleared, completion email sent).
- **Subject :** the user.
- **Metadata :** `{"sessions_killed": int, "ip_truncated": "<…>"}`.

## Story 1.6 — MFA TOTP (mandatory for staff, opt-in for B2C)

### `auth.mfa_enrollment_started`
- **Posé par :** `apps.accounts.services.mfa.start_enrollment` — fires on every QR-code generation (the user might iterate before scanning successfully).
- **Actor :** the user themselves.
- **Subject :** the user.
- **Metadata :** `{"ip_truncated": "<…>"}`.

### `auth.mfa_enrolled`
- **Posé par :** `mfa.confirm_enrollment` after the first TOTP code is verified.
- **Actor :** the user themselves.
- **Subject :** the user.
- **Metadata :** `{"device_type": "totp", "recovery_codes_count": 8, "ip_truncated": "<…>"}`.

### `auth.mfa_challenge_passed`
- **Posé par :** `mfa.verify_challenge` on a successful TOTP code (`method="totp"`). The recovery-code path uses a dedicated action `auth.mfa_recovery_code_used` instead of this one.
- **Actor :** the user themselves.
- **Subject :** the user.
- **Metadata :** `{"method": "totp", "ip_truncated": "<…>"}`.

### `auth.mfa_challenge_failed`
- **Posé par :** `mfa.verify_challenge` on invalid code (TOTP or recovery) — also written by the enrollment-confirm view on a wrong first code with `reason="invalid_enrollment_code"`.
- **Actor :** the user themselves (when known).
- **Subject :** the user.
- **Metadata :** `{"method": "totp"|"recovery", "ip_truncated": "<…>", "reason": "invalid_code"|"invalid_enrollment_code"}`.
- **DPO action :** patterns of `mfa_challenge_failed` from the same `ip_truncated` against many `subject_id`s = credential-stuffing probe (the attacker has the password and is trying random TOTP codes).

### `auth.mfa_recovery_code_used`
- **Posé par :** `mfa.verify_challenge` on a successful `method="recovery"` consumption.
- **Subject :** the user.
- **Metadata :** `{"method": "recovery", "remaining_codes": int, "ip_truncated": "<…>"}`.
- **DPO action :** an unusually fast drain of recovery codes (3+ used in a week) is suspicious — could indicate the user's authenticator was lost AND a phisher is using the recovery codes.

### `auth.mfa_recovery_codes_regenerated`
- **Posé par :** `mfa.regenerate_recovery_codes` after the user re-auths with password + TOTP.
- **Actor :** the user themselves.
- **Subject :** the user.
- **Metadata :** `{"count": int, "ip_truncated": "<…>"}`.

### `auth.mfa_disabled`
- **Posé par :** `mfa.disable` (B2C self-service path — staff refused upstream).
- **Actor :** the user themselves.
- **Subject :** the user.
- **Metadata :** `{"trigger": "user_self_service", "ip_truncated": "<…>"}`.

### `auth.mfa_reset_by_dpo`
- **Posé par :** `mfa.reset_by_dpo` (DPO override — manage.py shell after identity verification).
- **Actor :** the DPO user.
- **Subject :** the target user.
- **Metadata :** `{"reason": "<free-text justification>"}`.
- **DPO note :** this is the "break-glass" trail. Every entry must have a meaningful `reason` so reviewers can audit the decision later. See `docs/runbooks/mfa-lost-device.md`.

## Story 1.7 — RBAC middleware

### `rbac.access_denied`
- **Posé par :** `apps.core.permissions._record_rbac_denial` from any `PathAdvisorPermission` subclass (or `IsOwner.has_object_permission`) when it returns `False`.
- **Result :** `denied`.
- **Actor :** the user attempting the action (may be `None` for anonymous).
- **Subject :** `None` (RBAC denial is an actor-side event — DPO queries `WHERE actor_id = X` to spot escalation patterns).
- **Metadata :** `{"endpoint": "<request.path>", "method": "GET|POST|...", "required_roles": [...], "actor_role": "<role or empty>", "reason": "not_authenticated"|"wrong_role"|"not_mfa_verified"|"not_fully_active"|"not_owner", "view": "<view class name>"}`.
- **Object-level only :** also carries `{"target_user_id": "...", "actor_user_id": "..."}` when `reason="not_owner"`.
- **Dedup :** ONE row per request (DRF calls `has_permission` 2-3× per request — list view + filter backends — so the helper sets `request._rbac_denial_recorded = True` to collapse).
- **DPO action :** patterns of `rbac.access_denied` from the same `actor_id` against many `endpoint`s = active escalation probe ; from the same `ip_address_hash` across many `actor_id`s = credential-stuffing post-login. See `docs/patterns/rbac-matrix.md` §7 for canonical triage queries.

## Story 1.9 — Access-list (FR8, NFR-S4)

### `profile.access_list_read`
- **Posé par :** `apps.profiles.views.access_list` on every successful `GET /api/v1/profile/access-list/`.
- **Result :** `success`.
- **Actor :** the student reading their own access list.
- **Subject :** `request.user.id` (self-read — the student is reading data ABOUT their own profile access).
- **Metadata :** `{"count": <int>}` — number of entries returned. Helps the DPO spot anomalies (e.g., a student suddenly seeing 0 entries after recently granting consent = bug in a source adapter).
- **Dedup :** ONE row per request via `request._access_list_audit_recorded`. The dev page + React StrictMode double-mount must NOT amplify.
- **DPO action :** the metric `count_distinct(actor_id) WHERE action='profile.access_list_read' BY DAY` is the "users exercising their RGPD Article 15 right to know" KPI. Drops in this metric over time may signal UX regressions on the Settings entry point.

## Story 1.10 — Access revocation (FR9)

### `profile.access_revoked`
- **Posé par :** `apps.profiles.access_list.revoker.revoke_entry` on every successful `POST /api/v1/profile/access-list/<id>/revoke/`.
- **Result :** `success`.
- **Actor :** the student who revoked.
- **Subject :** the composite entry id `<source_name>:<source_pk>` — grep by this directly without joining to the source table.
- **Metadata :** `{"source_name": "parental_consent|school_partnership|counselor_consent", "source_pk": "<uuid>", "content_hash": "<sha256-hex>"}` — `content_hash` is forensic proof of WHAT the user saw at revoke time (Story 1.14 pattern), present iff the client provided one.
- **DPO action :** the metric `count(action='profile.access_revoked') BY DAY` is the inverse of `profile.access_list_read` — a healthy product has a moderate steady stream ; spikes deserve investigation (UX regression making students panic-revoke, or a fraud campaign forcing mass revocations).

### `profile.access_revoke_attempted`
- **Posé par :** `apps.profiles.access_list.revoker._audit_attempt` (and the view's "unknown source" path) on every FAILED revoke (404, malformed id, wrong owner).
- **Result :** `failure`.
- **Actor :** the calling student.
- **Subject :** the composite entry id as received.
- **Metadata :** `{"reason": "malformed_id|unknown_source|not_found_or_wrong_owner"}`.
- **DPO action :** patterns of `wrong_owner` from the same actor_id over time = active probing for other students' grants. Combined with `rbac.access_denied` from the same actor = escalation campaign.

## Catalog (planned — à ajouter par les stories futures)

- `consent.granted` / `consent.revoked` — Stories 1.4, 1.9, 1.10, 1.14.
- `gdpr.export_requested` / `gdpr.export_generated` — Story 1.11.
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
