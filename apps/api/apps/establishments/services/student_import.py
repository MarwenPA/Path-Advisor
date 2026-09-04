"""CSV student-import parsing + per-row processing — Story 6.5 §T2.4 (AC3).

Two entry points:
- `parse_csv_rows(raw_bytes)` — decode (utf-8-sig, fallback latin-1) + parse
  CSV columns `nom,prenom,date_naissance,email,email_parent` into a list of
  dicts. Never raises on a malformed row (it's still counted, but reported
  as an error string) — the CALLER (Celery task) decides what "malformed"
  means for the job's own error-count bookkeeping (§4.5 risk table).
- `import_row(cohort, row)` — process ONE already-parsed row (create the
  User + invitation, or skip with a typed reason). Never raises for
  business-rule rejections (duplicate email, missing email_parent under 15)
  — those come back as an `ImportRowResult(skipped=True, reason=...)` so one
  bad row never aborts the whole CSV (§AC3 last clause).
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import date, datetime

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts.models import User, UserRole, UserStatus
from apps.accounts.services.parental_consent import create_parental_consent_request
from apps.accounts.services.parental_consent_email import send_request_to_parent
from apps.establishments.models import Cohort, StudentImportInvitation
from apps.establishments.services.student_import_invitation import generate_token

_MINOR_AGE_THRESHOLD = 15
_EXPECTED_COLUMNS = {"nom", "prenom", "date_naissance", "email", "email_parent"}


def _decode(raw_bytes: bytes) -> str:
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            return raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    # Last resort: never raise — replace undecodable bytes so at least the
    # decodable rows survive (§4.5 risk table).
    return raw_bytes.decode("utf-8", errors="replace")


def parse_csv_rows(raw_bytes: bytes) -> list[dict]:
    """Decode + parse the CSV into a list of row dicts (string values, not
    yet validated). Missing expected columns simply come back as `None` per
    `DictReader` semantics — validated downstream by `import_row`.
    """
    text = _decode(raw_bytes)
    reader = csv.DictReader(io.StringIO(text))
    return [dict(row) for row in reader]


def _age_at(birth_date: date, at: date) -> int:
    years = at.year - birth_date.year
    if (at.month, at.day) < (birth_date.month, birth_date.day):
        years -= 1
    return years


def _parse_birth_date(raw: str | None) -> date | None:
    if not raw:
        return None
    try:
        return datetime.strptime(raw.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


@dataclass
class ImportRowResult:
    skipped: bool
    reason: str | None = None
    user: User | None = None
    invitation: StudentImportInvitation | None = None


def import_row(*, cohort: Cohort, row: dict) -> ImportRowResult:
    """AC3 — process a single parsed CSV row.

    Skip reasons (never raise): `email_manquant`, `date_naissance_invalide`,
    `email_deja_utilise`, `email_parent_requis_moins_15_ans`.
    """
    email = (row.get("email") or "").strip()
    if not email:
        return ImportRowResult(skipped=True, reason="email_manquant")

    birth_date = _parse_birth_date(row.get("date_naissance"))
    if birth_date is None:
        return ImportRowResult(skipped=True, reason="date_naissance_invalide")

    if User.objects.filter(email__iexact=email).exists():
        return ImportRowResult(skipped=True, reason="email_deja_utilise")

    age = _age_at(birth_date, timezone.now().date())
    parent_email = (row.get("email_parent") or "").strip() or None
    is_minor = age < _MINOR_AGE_THRESHOLD

    if is_minor and not parent_email:
        return ImportRowResult(skipped=True, reason="email_parent_requis_moins_15_ans")

    status = UserStatus.PENDING_PARENTAL_CONSENT if is_minor else UserStatus.EMAIL_UNVERIFIED

    try:
        # Code-review fix (2026-09): the User/consent/invitation writes used
        # to be three independent autocommit statements — if the 2nd or 3rd
        # failed, the User row from the 1st stayed committed with no
        # invitation and no way to activate it (an orphaned account only
        # fixable by manual SQL). One atomic block per row makes each row
        # genuinely all-or-nothing, on top of the per-row try/except the
        # Celery task already has for isolating rows from each other.
        with transaction.atomic():
            user = User.objects.create(
                email=User.objects.normalize_email(email).lower(),
                role=UserRole.STUDENT,
                birth_date=birth_date,
                status=status,
                tenant_id=cohort.tenant_id,
            )
            user.set_unusable_password()
            user.save(update_fields=["password"])

            consent = None
            if is_minor:
                # Reuse the existing service TEL QUEL — no consent logic duplicated here.
                consent = create_parental_consent_request(student=user, parent_email=parent_email)

            invitation = StudentImportInvitation.objects.create(
                cohort=cohort,
                user=user,
                token=generate_token(),
            )
    except IntegrityError:
        # Code-review fix (2026-09): the `.exists()` check above + this
        # `create()` is a TOCTOU race — two concurrent imports (or a
        # double-click retry) targeting the same email both pass the check.
        # The loser must resolve to the same typed `email_deja_utilise`
        # skip the story promises, not bubble up as an opaque
        # `erreur_inattendue:IntegrityError` in the job's error report.
        return ImportRowResult(skipped=True, reason="email_deja_utilise")

    if is_minor:
        # Code-review fix (2026-09): `create_parental_consent_request` alone
        # only writes the `ParentalConsent` row — the ONLY other caller in
        # the repo (`accounts/signals.py`, the B2C under-15 signup path)
        # always follows it with `send_request_to_parent(consent)`. Without
        # it, the parent never receives the consent link and the student
        # stays in `pending_parental_consent` forever (no reminder sweep
        # covers CSV-imported minors — see Story 6.5 §6 Out of Scope).
        # Dispatched after the atomic block commits, same reasoning as
        # `signals.py`: an SMTP failure must not roll back the consent row.
        send_request_to_parent(consent)

    return ImportRowResult(skipped=False, user=user, invitation=invitation)
