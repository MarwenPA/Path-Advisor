"""factory_boy fixtures for the establishments app — Story 6.5."""

from __future__ import annotations

from datetime import date

import factory

from apps.establishments.models import Establishment, EstablishmentType, LicenseType


class EstablishmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Establishment

    name = factory.Sequence(lambda n: f"Lycée Test {n}")
    type = EstablishmentType.LYCEE
    city = "Paris"
    uai = factory.Sequence(lambda n: f"075000{n:03d}")
    contact_name = "Karim Admin"
    contact_email = factory.Sequence(lambda n: f"contact{n}@etablissement.test")
    license_start = date(2026, 9, 1)
    license_end = date(2027, 8, 31)
    license_type = LicenseType.PILOTE_GRATUIT
