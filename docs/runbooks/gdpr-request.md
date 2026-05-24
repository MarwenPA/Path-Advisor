# GDPR Articles 17 & 20 — Erasure + Portability Runbook

**Owners:** DPO / Engineering on-call
**Stories:** 1.11 (portability), 1.12 (erasure), 1.13 (audit log).

Two related but distinct flows are documented here:
- **Article 20** (portability — data export) — §1-3 below. Story 1.11.
- **Article 17** (right to erasure — account deletion) — §7-9 below. Story 1.12.

---

## 1. User-facing flow

A user goes to **Paramètres → Confidentialité → Mes données personnelles** and
clicks **Demander un export**. The frontend POSTs to
`/api/v1/me/gdpr-exports/`. The backend:

1. Validates rate limit (1 per 24 h, see `GDPR_EXPORT_RATE_LIMIT_HOURS`).
2. Creates a `GdprExportRequest` row with `status=pending`.
3. Schedules the Celery task `gdpr.build_export` post-commit.

The Celery worker then:

1. Iterates the exporter registry (`apps.accounts.exporters` plus every other
   app's `exporters.py` discovered at startup).
2. Builds an AES-256 ZIP via `pyzipper`, content: `README.txt`,
   `profile/profile.json`, `audit/audit-log.jsonl`, and a `manifest.json`.
3. Uploads to S3 at `s3://<GDPR_EXPORTS_BUCKET>/gdpr-exports/{user_id}/{export_id}.zip`
   with `ServerSideEncryption=AES256`.
4. Transitions to `status=ready`, sets `expires_at = ready_at + 7 days`.
5. Sends two emails:
   - `gdpr_export_ready` with the in-app link (no password).
   - `gdpr_export_password` 30 s later, with the cleartext password.

The user clicks the link in email 1, lands on `/parametres/confidentialite/mes-donnees`,
clicks **Télécharger l'archive**. The endpoint
`/api/v1/me/gdpr-exports/{id}/download/` increments `download_count`, emits an
audit row, then 302-redirects to a 5-minute presigned S3 URL.

A nightly Celery beat task (`gdpr.expire_old_exports`, 04:00 UTC) deletes
expired objects from S3 and flips rows to `status=expired`.

---

## 2. Common user issues

### "I lost the password"

Path-Advisor only stores an **Argon2 hash** of the archive password. There is
no way to recover it. Tell the user to **request a new export** — the previous
one will still expire on schedule and be cleaned up by the nightly job.

### "I can't open the ZIP on Windows"

Native Windows Explorer ZIP does **not** support AES-256 (only the broken
ZipCrypto). Recommend: 7-Zip, WinRAR, or `unzip` from WSL. macOS Archive
Utility also struggles — Keka or The Unarchiver are reliable.

### "The 2nd email never arrived"

Check Mailpit (local) or Postmark (prod) bounce log. The password email is a
Celery task with `autoretry_for=Exception` (3 retries, 60s/300s/1800s
back-off). If the user's mailbox blocks the message, you can extract the
password from the worker logs ONLY if you set `LOG_LEVEL=DEBUG` BEFORE the
task ran — we deliberately do not log passwords at INFO. In that case the
operationally safe path is **request a fresh export** (the user retains the
right to do so even within the 24 h window if the previous one failed —
`failed` rows do not consume quota).

### "My export contains less than I expected"

Each Django app contributes via `@register_exporter("<domain>")`. Until a
story lands its exporter, the corresponding section is missing from the ZIP.
Story 1.11 ships `accounts` + `audit`. As of writing, bulletins (Story 2.3),
recommendations (Epic 3), pathways (Epic 4), outreach (Epic 5) are NOT yet in
the export. Mention this transparently to users.

### "I see an `errors/<domain>.error.txt` file in my ZIP"

This means one exporter raised during build. The export still succeeded — the
other domains were preserved. Check structlog for the matching
`gdpr.exporter_failed` event and Sentry for the exception. Fix the exporter
and ask the user to request a fresh export.

---

## 3. Manual export (user can't self-serve)

When a user has lost access to their account (failed MFA, support-locked
account, etc.) but is otherwise authenticated by other means (legal ID,
support call):

```bash
# On the API container
DJANGO_SETTINGS_MODULE=path_advisor.settings.prod \
  python manage.py shell -c "
from apps.accounts.models import User
from apps.accounts.services.gdpr_service import GdprExportService

user = User.objects.get(email='user@example.com')
export = GdprExportService.request_export(user=user)
print('export_id:', export.id)
"
```

The worker will email the user as usual. If the user's email is also lost,
hand the password and link to them through whatever out-of-band channel
support has validated.

**Do NOT** generate exports for a user without an authenticated request from
that user — this would be a CWE-285 (improper authorization) and a
NF-S4 (audit) incident. Always log the manual export reason in the support
ticket.

---

## 4. Operational tasks

### Force-expire an export (incident response)

If a leaked download link is reported:

```python
from apps.accounts.models import GdprExportRequest, GdprExportStatus
from apps.accounts.services.gdpr_service import gdpr_s3_client
from django.conf import settings

export = GdprExportRequest.objects.get(pk='gex_...')
gdpr_s3_client().delete_object(
    Bucket=settings.GDPR_EXPORTS_BUCKET,
    Key=export.archive_s3_key,
)
export.status = GdprExportStatus.EXPIRED
export.archive_s3_key = None
export.archive_size_bytes = None
export.save()
```

This is what `gdpr.expire_old_exports` does, just immediately. Log the
override in the incident channel.

### Re-run a failed export

```python
from apps.accounts.models import GdprExportRequest, GdprExportStatus
from apps.accounts.tasks import build_export

export = GdprExportRequest.objects.get(pk='gex_...')
export.status = GdprExportStatus.PENDING
export.error_code = None
export.error_message = None
export.save()
build_export.delay(export_id=export.id)
```

### Inspect a ZIP locally

```bash
aws s3 cp \
  s3://exports-gdpr/gdpr-exports/usr_.../gex_....zip \
  /tmp/export.zip \
  --endpoint-url $AWS_S3_ENDPOINT_URL

# Then open with 7-Zip / Keka and provide the password.
```

Pyzipper CLI:

```bash
uv run python -c "
import pyzipper
with pyzipper.AESZipFile('/tmp/export.zip') as zf:
    zf.setpassword(b'PASSWORD_FROM_USER')
    print(zf.namelist())
"
```

---

## 5. Audit + compliance trail

Every step is audited via Story 1.13:

| Event | Where it fires |
|---|---|
| `gdpr.export_requested` | `GdprExportService.request_export` (decorator) |
| `gdpr.export_ready` | `build_export` task on success |
| `gdpr.export_downloaded` | `GdprExportViewSet.download` view |
| `gdpr.export_expired` | `expire_old_exports` task |
| `gdpr.export_failed` | `build_export` task on exception |

Query the audit log via `/api/v1/audit/logs/?action=gdpr.` (DPO endpoint,
Story 1.13). For a single user, append `&subject_id=usr_...`.

---

## 6. Open items (deferred)

- Notification in-app (instead of email-only) — Story 8.x notifications.
- Multi-language exports — the manifest/README are FR-only in MVP. en-US lands
  when the i18n surface is needed (Epic 7+).
- Password recovery / re-issuance for an already-built ZIP — explicitly out of
  scope. We re-issue a new export rather than the old password (security).

---

## 7. Article 17 — Account deletion lifecycle (Story 1.12)

The right-to-erasure pipeline runs in **two phases** with a 30-day grace
window separating them:

1. **Soft-delete (instant on user click)** — `User.status = DELETED`,
   `User.is_active = False`, Django sessions terminated, confirmation email
   with a cancel link sent synchronously. The user receives the cancel link
   valid 30 days; the audit row `gdpr.account_deletion_requested` is written
   inside the same transaction.
2. **Hard-delete (Celery beat, daily at 03:45 Paris)** — for every row where
   `cancelled_at IS NULL AND hard_deleted_at IS NULL AND hard_delete_after <= now()`:
   purge S3 prefixes registered in `GDPR_USER_OWNED_S3_PREFIXES`, write the
   audit row `gdpr.account_hard_deleted`, then `user.delete()` which cascades
   `parental_consents` (and any other FK with `on_delete=CASCADE`). The
   `AccountDeletionRequest` row itself survives via `SET_NULL` — it is part
   of the audit story (3-year retention per NFR-S4).

State machine on the request row:

```
   pending  ──── user/DPO cancel ────►  cancelled (terminal)
      │
      ▼
   pending past grace ────► sweep ────► hard_deleted (terminal)
                                │
                                └─── failed (attempt < 7) ──► retried next day
                                └─── attempt == 7 ──► giving_up audit row, row frozen
```

---

## 8. Helping a user who can't find the cancel email

The 30-day grace window is meant exactly for this. The recovery paths, in order
of preference:

1. **Re-fetch the cancel link** from the Mailpit / Postmark inbox-events
   (Mailpit UI at `:8025` in dev; Postmark dashboard in prod). The link has the
   form `https://path-advisor.fr/auth/cancel-deletion/<token>`.
2. **DPO override via Django admin** — covered in §9 below. Requires the
   `accounts.cancel_deletion_request` permission.
3. **If the 30 days are up**, the row is `hard_deleted`. Data is gone. Inform
   the user politely that the deletion is irreversible past day 30 and they can
   create a new account if they wish. **DO NOT promise restoration** —
   there is nothing to restore.

---

## 9. DPO override cancel (admin action)

When a user contacts support claiming they did not request the deletion or
cannot find the cancel email:

1. Verify the user's identity through the support callback procedure
   (out-of-band; the support team owns the playbook). At minimum: cross-check
   email + birth-date + a piece of profile data only the legitimate user
   would know.
2. Open Django admin → "Account deletion requests" → click the row → click
   **"Cancel (DPO)"** in the action column. The action is only visible on
   rows still in the grace window.
3. Fill the **mandatory** `cancel_reason` text — be specific:
   - `"support callback 2026-05-30 — verified identity via birth-date + last login IP"`
   - `"user reported phishing on 2026-05-29; account hijack ruled out — see incident PA-2026-031"`
4. Submit. The action:
   - Writes `cancel_reason = "dpo_override:<your_user_id>:<your_text>"`.
   - Restores the user (`status=ACTIVE`, `is_active=True`, `deleted_at=NULL`).
   - Sends the "Suppression annulée" email.
   - Writes `gdpr.account_deletion_cancelled` with `actor_id=<your_user_id>`
     and `metadata.via = "dpo_override"`.

**Permission gate:** without the explicit `accounts.cancel_deletion_request`
permission, the action returns an error. Grant the perm to DPO users via Django
admin → Users → user → "User permissions" — DO NOT add the user to
`is_superuser` solely for this purpose.

---

## 10. Frozen rows (max-attempts cap fired)

If you see `gdpr.account_hard_delete_giving_up` audit rows, the sweep has
given up on a particular deletion (default cap: 7 daily attempts). The row
stays in `account_deletion_requests` with `hard_deleted_at IS NULL` and
`hard_delete_attempt_count >= 7`. To recover:

1. Identify the blocker via `last_failure_code` on the row (typically
   `BotoCoreError` or `ClientError` — an S3 issue).
2. Fix the upstream issue (bucket policy, network ACL, credentials, …).
3. **Manually reset the attempt counter via Django shell**:
   ```python
   from apps.accounts.models import AccountDeletionRequest
   AccountDeletionRequest.objects.filter(pk="adr_…").update(hard_delete_attempt_count=0)
   ```
4. The next sweep run (or manual trigger via `python manage.py shell -c
   "from apps.accounts.tasks import sweep_account_deletions; sweep_account_deletions.delay()"`)
   will retry.

---

## 11. Article 17 / Article 20 interaction

When a user requests **both** an Article 20 export AND an Article 17 deletion:

- The export legally precedes the deletion (the user is asking for *their copy*
  before we wipe ours). Let the export finish and deliver before the sweep
  fires.
- The sweep purges the entire `gdpr-exports/<user_id>/` prefix, so any
  pending/in-flight export ZIPs are cleaned up alongside the user data.
- The user's confirmation email mentions the still-valid export link (up to 7
  days even after the user account is gone — by design, see Story 1.11's
  comment on `GdprExportRequest.user_id` being a logical FK).
