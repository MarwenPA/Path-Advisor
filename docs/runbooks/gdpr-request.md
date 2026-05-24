# GDPR Article 20 — Data Portability Export

**Owners:** DPO / Engineering on-call
**Stories:** 1.11 (build), 1.13 (audit), future 1.12 (account deletion).

This runbook describes how a Path-Advisor GDPR export works end-to-end, how to
help users in trouble, and how to issue a manual export when the self-service
flow is not usable (e.g. account lockout).

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
