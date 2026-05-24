"""CI guardrail — every FK to User MUST use on_delete=CASCADE or SET_NULL.

Rationale (Story 1.12 §AC6, §4.5 #6): the right-to-erasure pipeline relies on
`user.delete()` cascading every dependent row. A `PROTECT` / `RESTRICT` /
`DO_NOTHING` FK on User would raise an IntegrityError mid-cascade, leaving
the user partially deleted and breaking the GDPR Article 17 guarantee.

Two valid policies:
  - CASCADE: dependent rows die with the user (most data tables).
  - SET_NULL: dependent rows survive (audit-style records — e.g. the
    AccountDeletionRequest row itself, which must persist for the 3-year
    audit retention).

Any other policy fails the build. Run via:
    DJANGO_SETTINGS_MODULE=path_advisor.settings.local python scripts/assert_user_cascade.py

Wired in .github/workflows/ci-api.yml as a post-pytest gate.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Allow running from anywhere — bootstrap settings if not already present.
if "DJANGO_SETTINGS_MODULE" not in os.environ:
    os.environ["DJANGO_SETTINGS_MODULE"] = "path_advisor.settings.local"

# Make sure `apps/api` is on sys.path so `manage.py`-equivalent imports resolve
# even when this script is invoked from the repo root.
_HERE = Path(__file__).resolve().parent
_API_ROOT = _HERE.parent  # apps/api
sys.path.insert(0, str(_API_ROOT))

import django  # noqa: E402

django.setup()

from django.apps import apps  # noqa: E402
from django.conf import settings as django_settings  # noqa: E402
from django.db import models  # noqa: E402

_ALLOWED = (models.CASCADE, models.SET_NULL)
_ALLOWED_NAMES = {"CASCADE", "SET_NULL"}


def _on_delete_name(callable_) -> str:
    """Resolve the on_delete callable to its public name (Django stores callables, not enums)."""
    return getattr(callable_, "__name__", repr(callable_))


def find_violations() -> list[tuple[str, str, str]]:
    """Return list of (model_label, field_name, on_delete_name) for any FK to User
    whose on_delete policy is not in the allowed set.
    """
    user_label = django_settings.AUTH_USER_MODEL  # e.g. "accounts.User"
    user_app, user_model = user_label.split(".")
    user_cls = apps.get_model(user_app, user_model)

    violations: list[tuple[str, str, str]] = []
    for model_class in apps.get_models():
        for field in model_class._meta.get_fields():
            if not isinstance(field, (models.ForeignKey, models.OneToOneField)):
                continue
            target = field.related_model
            if target is None:
                continue
            if target is not user_cls:
                continue
            on_delete = field.remote_field.on_delete
            if on_delete in _ALLOWED:
                continue
            violations.append(
                (
                    model_class._meta.label,
                    field.name,
                    _on_delete_name(on_delete),
                )
            )
    return violations


def main() -> int:
    violations = find_violations()
    if not violations:
        print("✓ assert_user_cascade: every FK to User uses CASCADE or SET_NULL.")
        return 0

    print(
        "✗ assert_user_cascade: violations detected — these FKs break the right-to-erasure pipeline:"
    )
    print()
    for model_label, field_name, policy in violations:
        print(
            f"  - {model_label}.{field_name}: on_delete={policy} (expected one of {sorted(_ALLOWED_NAMES)})"
        )
    print()
    print(
        "Pick CASCADE (data dies with user) or SET_NULL (audit row, FK cleared). "
        "See docs/patterns/account-deletion.md for the contract."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
