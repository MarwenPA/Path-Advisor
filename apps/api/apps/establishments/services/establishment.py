"""Establishment service — Story 6.5 §T2.1 (AC1)."""

from __future__ import annotations

from django.db import transaction

from apps.audit.decorators import audit_action
from apps.establishments.exceptions import EstablishmentUaiAlreadyTaken
from apps.establishments.models import Establishment


@audit_action(
    "establishment.created",
    subject_from=lambda kwargs, ret: str(ret.id) if ret else None,
    metadata_from=lambda kwargs, ret: {"name": ret.name, "uai": ret.uai},
)
def create_establishment(
    *,
    name: str,
    type: str,
    city: str,
    uai: str,
    contact_name: str,
    contact_email: str,
    license_start,
    license_end,
    license_type: str,
) -> Establishment:
    """AC1 — create a new tenant. Raises `EstablishmentUaiAlreadyTaken` (409)
    if `uai` is already taken by another establishment (double-onboarding
    guard).
    """
    if Establishment.objects.filter(uai=uai).exists():
        raise EstablishmentUaiAlreadyTaken()

    with transaction.atomic():
        establishment = Establishment.objects.create(
            name=name,
            type=type,
            city=city,
            uai=uai,
            contact_name=contact_name,
            contact_email=contact_email,
            license_start=license_start,
            license_end=license_end,
            license_type=license_type,
        )
    return establishment
