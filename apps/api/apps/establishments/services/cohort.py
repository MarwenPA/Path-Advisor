"""Cohort service — Story 6.5 §T2.2 (AC2)."""

from __future__ import annotations

from django.db import IntegrityError, transaction

from apps.audit.decorators import audit_action
from apps.establishments.exceptions import CohortAlreadyExists
from apps.establishments.models import Cohort, Establishment


@audit_action(
    "cohort.created",
    subject_from=lambda kwargs, ret: ret.id if ret else str(kwargs["establishment"].id),
    metadata_from=lambda kwargs, ret: {
        "establishment_id": str(kwargs["establishment"].id),
        "name": ret.name,
        "school_year": ret.school_year,
    },
)
def create_cohort(*, establishment: Establishment, name: str, school_year: str) -> Cohort:
    """AC2 — `tenant_id` is denormalized from `establishment.id` (story §2)."""
    try:
        with transaction.atomic():
            cohort = Cohort.objects.create(
                establishment=establishment,
                name=name,
                school_year=school_year,
                tenant_id=establishment.id,
            )
    except IntegrityError as exc:
        # Code-review fix (2026-09): migration 0004's uniqueness constraint
        # on (establishment, name, school_year) — surface as a typed 409,
        # not an opaque 500.
        raise CohortAlreadyExists() from exc
    return cohort
