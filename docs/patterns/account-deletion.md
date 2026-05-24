# Account Deletion — The Cascade Contract (Story 1.12)

**Audience :** every dev (and AI agent) adding a model that stores personal data.

This page defines the **load-bearing contract** that lets Path-Advisor honour the
GDPR Article 17 "right to erasure". If you break it, the right-to-erasure
pipeline starts leaking data and we fail the next CNIL inspection.

---

## The contract in one sentence

> Every `ForeignKey` / `OneToOneField` pointing at `accounts.User` MUST use
> `on_delete=models.CASCADE` or `on_delete=models.SET_NULL`. Anything else
> (`PROTECT`, `RESTRICT`, `DO_NOTHING`, `SET_DEFAULT`) is refused by the CI
> guardrail and breaks the production deletion sweep.

The two valid policies map to two intents:

| Policy | When to use | Example |
|---|---|---|
| `CASCADE` | The dependent row is **personal data** that must vanish with the user. | `Bulletin.student` (Story 2.3 will add this). |
| `SET_NULL` | The dependent row is an **audit artifact** that must persist post-erasure for the 3-year retention obligation (NFR-S4). | `AccountDeletionRequest.user` (Story 1.12). |

A third option exists for tables that are **not FK-linked to User**: pseudonymise
the row at write time by storing the user's ULID as a plain `CharField`. The
audit log (`AuditLog.actor_id` / `subject_id`) and the GDPR export request
(`GdprExportRequest.user_id`) both follow this pattern.

> **Pseudonymisation scope.** The ULID stored in audit/export rows is
> pseudonymised *de facto by the absence of the originating User row* after
> hard-delete — it is no longer linkable to a person inside Path-Advisor's
> systems. It is **not** cryptographically pseudonymised (no hash applied).
> A stable ULID is a direct identifier in the GDPR Article 4(1) sense; only
> the deletion of the linking row makes it functionally anonymous within
> the platform. This design requires explicit DPO sign-off before
> production launch, recorded in `deferred-work.md`. A re-link attack via
> a backup snapshot taken pre-deletion remains theoretically possible —
> backup retention policy mitigates this orthogonally.

---

## How the sweep works

```
┌─────────────────────────────────┐
│ User clicks "Supprimer mon …"   │
│   ↓ (re-auth with password)     │
│ POST /me/account-deletion/      │
└─────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────┐
│ Soft-delete (single transaction):                   │
│   • User.status = DELETED                           │
│   • User.is_active = False                          │
│   • Django sessions for this user → deleted         │
│   • AccountDeletionRequest row inserted             │
│   • Confirmation email sent (synchronous)           │
│   • Audit row gdpr.account_deletion_requested       │
└─────────────────────────────────────────────────────┘
        │
        │  30-day grace window
        ▼
┌─────────────────────────────────┐       ┌──────────────────────────────┐
│ User clicks cancel link in mail │   OR  │ Celery beat sweep fires      │
│   ↓ (re-auth)                   │       │ (daily, 03:45 Paris)         │
│ POST /account-deletion/<token>/ │       │  • Re-fetch under FOR UPDATE │
│      /cancel/                   │       │  • _purge_s3_prefixes(...)   │
│   ↓                             │       │  • audit row written FIRST   │
│ User restored, audit row,       │       │  • user.delete() — CASCADE   │
│ "compte restauré" email         │       │  • AccountDeletionRequest    │
└─────────────────────────────────┘       │    .hard_deleted_at = now()  │
                                          │  • Best-effort closure email │
                                          └──────────────────────────────┘
```

---

## CI enforcement

`apps/api/scripts/assert_user_cascade.py` walks every installed app, finds every
FK to `accounts.User`, and exits 1 if any policy is not in
`{CASCADE, SET_NULL}`. The `.github/workflows/ci-api.yml` runs the script after
pytest. If the gate fires:

```
✗ assert_user_cascade: violations detected
  - profiles.Bulletin.student: on_delete=PROTECT (expected one of ['CASCADE', 'SET_NULL'])
```

Fix the migration — either flip the `on_delete` to one of the allowed policies,
or remove the FK and switch to a logical-FK CharField (and re-read this doc
before you do).

---

## When you add a new personal-data model

1. **Decide your cascade policy** using the table above.
2. **Add the FK** with the chosen `on_delete=...`.
3. **Run the CI gate locally** before opening the PR: `python scripts/assert_user_cascade.py`.
4. **If your model survives the cascade (SET_NULL)** : add a `*_id_snapshot` CharField
   so post-cascade rows still know who the row was about. See
   `AccountDeletionRequest.user_id_snapshot` for the pattern.
5. **If your model owns an S3 prefix scoped to the user**, register it in
   `settings.GDPR_USER_OWNED_S3_PREFIXES` so the sweep purges it. Example:
   ```python
   GDPR_USER_OWNED_S3_PREFIXES = [
       ("GDPR_EXPORTS_BUCKET", "gdpr-exports/{user_id}/"),
       ("BULLETINS_BUCKET",    "bulletins-encrypted/{user_id}/"),  # Story 2.3
   ]
   ```

---

## Anti-patterns

- ❌ **`on_delete=models.PROTECT` on a User FK** — the cascade raises
  `ProtectedError` mid-sweep; the user ends up half-deleted. CI gate refuses it.
- ❌ **Reading `request.user` inside a CASCADE-triggered `pre_delete` signal handler** — under cascade, the user FK is being torn down; `request.user` is undefined for the sweep's system actor. Use the audit metadata instead.
- ❌ **Storing PII in a third-party SaaS (Stripe, Postmark…) without a clean-up hook** — the sweep can't reach external systems. Each integration MUST own a `cancel_subscription_on_user_delete` hook OR explicitly document the residual data.
- ❌ **`audit_logs.actor_id = ForeignKey(User)`** — would force CASCADE/SET_NULL and either lose audit rows (CASCADE) or null-out the actor (SET_NULL, weakens the chain proof). The CharField pseudonymises naturally.

---

## Related stories

- Story 1.11 — GDPR Article 20 export pipeline (uses the same S3 bucket; deletion sweep purges `gdpr-exports/<user_id>/`).
- Story 1.13 — Audit log immutable hash chain (rows survive the cascade; chain integrity preserved by `subject_id` being a CharField).
- Story 1.14 — `ConsentDialog` UI primitive (consumed by the settings-page deletion confirmation, with `isAcceptDestructive={true}`).
