"""Story 9.2 — admin writes on the schools referential + CSV import.

Exact mirror of `apps/professions/services/referential_admin.py` (9.1):
revision snapshot + `record_audit` in the SAME transaction as every write;
`status` drives `is_active` via `School.save()`; "delete" = archive (7.10
already gave the student-side UX for a deactivated school).

CSV import (AC): semicolon-separated, documented headers. A line whose slug
already exists NEVER overwrites — it lands in `conflicts[]` with both
states side by side; resolution is a manual PATCH from the fiche (the AC
asks for manual drill-down, not an auto-merge). Created rows arrive as
DRAFTS in one all-or-nothing transaction: a mass import must never publish
to students directly (editorial gate), and a half-imported file is worse
than a failed one.
"""

from __future__ import annotations

import csv
import io
from typing import Any

import structlog
from django.db import transaction

from apps.audit.decorators import record_audit

from .models import School, SchoolRevision, SchoolStatus

log = structlog.get_logger(__name__)

EDITORIAL_FIELDS = (
    "slug",
    "name",
    "type",
    "city",
    "region",
    "postal_code",
    "lat",
    "lon",
    "tuition_min_eur",
    "tuition_max_eur",
    "apprenticeship",
    "internship",
    "selectivity_index",
    "public_private",
    "description",
    "top_debouches",
    "parcoursup_dates",
    "affelnet_dates",
    "official_url",
    "school_type",
    "status",
)

#: Import CSV — colonnes attendues (sous-ensemble utile de l'open data
#: Parcoursup, délimiteur `;`). Toute autre colonne est ignorée.
CSV_REQUIRED_COLUMNS = ("slug", "name", "type", "city", "region", "postal_code", "public_private")
CSV_OPTIONAL_COLUMNS = ("selectivity_index", "official_url", "description")
CSV_MAX_ROWS = 2000


def snapshot_of(school: School) -> dict[str, Any]:
    snapshot = {}
    for field in EDITORIAL_FIELDS:
        value = getattr(school, field)
        # Decimal lat/lon → str for JSON storage.
        snapshot[field] = str(value) if value.__class__.__name__ == "Decimal" else value
    return snapshot


def _record_revision(school, *, action, editor, restored_from=None) -> SchoolRevision:
    return SchoolRevision.objects.create(
        school=school,
        snapshot=snapshot_of(school),
        action=action,
        editor=editor,
        restored_from=restored_from,
    )


def create_school(*, editor, data: dict[str, Any], action=SchoolRevision.Action.CREATED) -> School:
    with transaction.atomic():
        school = School(**data)
        school.save()
        _record_revision(school, action=action, editor=editor)
        record_audit(
            action="referential.school_created",
            result="success",
            actor=editor,
            subject_id=str(school.id),
            metadata={"slug": school.slug, "status": school.status, "via": action},
        )
    return school


def update_school(*, school: School, editor, data: dict[str, Any]) -> School:
    changed = sorted(field for field, value in data.items() if getattr(school, field) != value)
    if not changed:
        return school
    with transaction.atomic():
        for field, value in data.items():
            setattr(school, field, value)
        school.save()
        _record_revision(
            school,
            action=(
                SchoolRevision.Action.STATUS_CHANGED
                if changed == ["status"]
                else SchoolRevision.Action.UPDATED
            ),
            editor=editor,
        )
        record_audit(
            action="referential.school_updated",
            result="success",
            actor=editor,
            subject_id=str(school.id),
            metadata={"slug": school.slug, "changed_fields": changed},
        )
    return school


def archive_school(*, school: School, editor) -> School:
    return update_school(school=school, editor=editor, data={"status": SchoolStatus.ARCHIVED})


def rollback_school(*, school: School, editor, revision: SchoolRevision) -> School:
    if revision.school_id != school.pk:
        raise ValueError("Revision does not belong to this school.")
    with transaction.atomic():
        for field in EDITORIAL_FIELDS:
            if field in revision.snapshot:
                setattr(school, field, revision.snapshot[field])
        school.save()
        _record_revision(
            school,
            action=SchoolRevision.Action.ROLLED_BACK,
            editor=editor,
            restored_from=revision,
        )
        record_audit(
            action="referential.school_rolled_back",
            result="success",
            actor=editor,
            subject_id=str(school.id),
            metadata={"slug": school.slug, "restored_from": str(revision.id)},
        )
    return school


def import_schools_csv(*, editor, content: str) -> dict[str, Any]:
    """Validate + import an open-data CSV. Returns the drill-down report.

    - created: slugs created (as DRAFTS, one all-or-nothing transaction);
    - conflicts: lines whose slug already exists (existing vs incoming);
    - errors: lines that fail validation (per-field messages).
    """
    from .serializers import SchoolAdminWriteSerializer

    reader = csv.DictReader(io.StringIO(content), delimiter=";")
    header = set(reader.fieldnames or [])
    missing = [column for column in CSV_REQUIRED_COLUMNS if column not in header]
    if missing:
        return {
            "created": [],
            "conflicts": [],
            "errors": [
                {"line": 1, "errors": {"__all__": [f"Colonnes manquantes : {', '.join(missing)}"]}}
            ],
        }

    created: list[str] = []
    conflicts: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    to_create: list[dict[str, Any]] = []
    seen_slugs: set[str] = set()

    existing = {
        s.slug: s
        for s in School.objects.filter(
            slug__in=[  # one query for conflict detection
                (row.get("slug") or "").strip()
                for row in csv.DictReader(io.StringIO(content), delimiter=";")
            ]
        )
    }

    for line_number, row in enumerate(reader, start=2):
        if line_number - 1 > CSV_MAX_ROWS:
            errors.append(
                {
                    "line": line_number,
                    "errors": {"__all__": ["Fichier trop long (max 2000 lignes)."]},
                }
            )
            break
        payload = {
            column: (row.get(column) or "").strip()
            for column in CSV_REQUIRED_COLUMNS + CSV_OPTIONAL_COLUMNS
            if (row.get(column) or "").strip()
        }
        slug = payload.get("slug", "")
        if slug in seen_slugs:
            errors.append({"line": line_number, "errors": {"slug": ["Doublon dans le fichier."]}})
            continue
        seen_slugs.add(slug)
        if slug in existing:
            current = existing[slug]
            conflicts.append(
                {
                    "line": line_number,
                    "slug": slug,
                    "existing": {
                        "name": current.name,
                        "city": current.city,
                        "status": current.status,
                    },
                    "incoming": payload,
                }
            )
            continue
        serializer = SchoolAdminWriteSerializer(data={**payload, "status": SchoolStatus.DRAFT})
        if not serializer.is_valid():
            errors.append({"line": line_number, "errors": serializer.errors})
            continue
        to_create.append(serializer.validated_data)

    with transaction.atomic():
        for data in to_create:
            school = create_school(editor=editor, data=data, action=SchoolRevision.Action.IMPORTED)
            created.append(school.slug)
        record_audit(
            action="referential.schools_csv_imported",
            result="success",
            actor=editor,
            metadata={
                "created": len(created),
                "conflicts": len(conflicts),
                "errors": len(errors),
            },
        )

    log.info(
        "referential.csv_import",
        created=len(created),
        conflicts=len(conflicts),
        errors=len(errors),
    )
    return {"created": created, "conflicts": conflicts, "errors": errors}
