"""Story 9.1 — admin writes on the professions referential.

Every write goes through here so the three invariants hold at ONE place:
1. a `ProfessionRevision` snapshot is appended in the SAME transaction;
2. an `audit_log` row records who/what/when (joins the transaction too —
   1.13 semantics: a rolled-back write leaves no audit trace);
3. `status` drives `is_active` (`Profession.save()` enforces the sync).

"Delete" is deliberately ABSENT: a profession is referenced by `Parcours`,
reports and early-outreach requests — the destructive AC verb is fulfilled
by `archive` (instant disappearance from every public surface). Deviation
consigned in the story doc §2.3.
"""

from __future__ import annotations

from typing import Any

import structlog
from django.db import transaction

from apps.audit.decorators import record_audit

from ..models import Profession, ProfessionRevision, ProfessionStatus

log = structlog.get_logger(__name__)

#: The editorial fields a revision snapshots and a rollback restores.
#: `slug` is included (renames are edits); `id`/timestamps/`is_active`
#: (derived) are not.
EDITORIAL_FIELDS = (
    "slug",
    "name",
    "description",
    "daily_routine",
    "requirements_json",
    "prospects_text",
    "median_salary_eur",
    "salary_range_json",
    "signals_json",
    "level_compatibility",
    "sector",
    "rome_code",
    "sources_json",
    "status",
)


def snapshot_of(profession: Profession) -> dict[str, Any]:
    return {field: getattr(profession, field) for field in EDITORIAL_FIELDS}


def _record_revision(
    profession: Profession,
    *,
    action: str,
    editor,
    restored_from: ProfessionRevision | None = None,
) -> ProfessionRevision:
    return ProfessionRevision.objects.create(
        profession=profession,
        snapshot=snapshot_of(profession),
        action=action,
        editor=editor,
        restored_from=restored_from,
    )


def create_profession(*, editor, data: dict[str, Any]) -> Profession:
    with transaction.atomic():
        profession = Profession(**data)
        profession.save()
        _record_revision(profession, action=ProfessionRevision.Action.CREATED, editor=editor)
        record_audit(
            action="referential.profession_created",
            result="success",
            actor=editor,
            subject_id=profession.id,
            metadata={"slug": profession.slug, "status": profession.status},
        )
    return profession


def update_profession(*, profession: Profession, editor, data: dict[str, Any]) -> Profession:
    changed = sorted(field for field, value in data.items() if getattr(profession, field) != value)
    if not changed:
        return profession
    status_changed = "status" in changed
    with transaction.atomic():
        for field, value in data.items():
            setattr(profession, field, value)
        profession.save()
        _record_revision(
            profession,
            action=(
                ProfessionRevision.Action.STATUS_CHANGED
                if status_changed and changed == ["status"]
                else ProfessionRevision.Action.UPDATED
            ),
            editor=editor,
        )
        record_audit(
            action="referential.profession_updated",
            result="success",
            actor=editor,
            subject_id=profession.id,
            metadata={"slug": profession.slug, "changed_fields": changed},
        )
    return profession


def archive_profession(*, profession: Profession, editor) -> Profession:
    return update_profession(
        profession=profession, editor=editor, data={"status": ProfessionStatus.ARCHIVED}
    )


def rollback_profession(
    *, profession: Profession, editor, revision: ProfessionRevision
) -> Profession:
    """Re-apply `revision.snapshot` as a NEW revision (history is append-only)."""
    if revision.profession_id != profession.pk:
        raise ValueError("Revision does not belong to this profession.")
    with transaction.atomic():
        for field in EDITORIAL_FIELDS:
            if field in revision.snapshot:
                setattr(profession, field, revision.snapshot[field])
        profession.save()
        _record_revision(
            profession,
            action=ProfessionRevision.Action.ROLLED_BACK,
            editor=editor,
            restored_from=revision,
        )
        record_audit(
            action="referential.profession_rolled_back",
            result="success",
            actor=editor,
            subject_id=profession.id,
            metadata={"slug": profession.slug, "restored_from": revision.id},
        )
    return profession
