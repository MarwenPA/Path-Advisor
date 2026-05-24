"""GDPR Article 20 exporter registry (Story 1.11).

Each domain (accounts, audit, profiles, recommendations, …) contributes its
slice of the user's personal data via a function decorated with
`@register_exporter("<domain>")`. The export task iterates the registry in
a deterministic order and streams each `ExporterEntry` into the encrypted ZIP.

Adding a new domain to the export is intentionally local: drop an
`exporters.py` (or `exporters/__init__.py`) module under your Django app and
declare the decorator. `AccountsConfig.ready()` (apps.py) auto-imports every
app's `exporters` module at startup so the decorators run.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.accounts.models import User


@dataclass(frozen=True)
class ExporterEntry:
    """One artifact in the final ZIP archive."""

    archive_path: str  # e.g. "profile/profile.json"
    content: bytes
    content_type: str  # e.g. "application/json"


ExporterFn = Callable[["User"], Iterable[ExporterEntry]]


_REGISTRY: dict[str, ExporterFn] = {}


def register_exporter(domain: str) -> Callable[[ExporterFn], ExporterFn]:
    """Decorate a function as the exporter for `domain`.

    Raises ValueError if the domain is already registered — duplicate
    registration usually means a copy/paste bug and silently shadowing
    the first registration would silently lose data.
    """

    def decorator(fn: ExporterFn) -> ExporterFn:
        if domain in _REGISTRY:
            raise ValueError(
                f"Exporter for domain '{domain}' is already registered "
                f"(by {_REGISTRY[domain].__module__}.{_REGISTRY[domain].__name__})."
            )
        _REGISTRY[domain] = fn
        return fn

    return decorator


def iter_exporters() -> tuple[tuple[str, ExporterFn], ...]:
    """Yield `(domain, fn)` pairs in deterministic alphabetical order.

    Stable iteration makes the resulting ZIP byte-reproducible for a given
    user state, which simplifies test assertions and audit reproducibility.
    """
    return tuple(sorted(_REGISTRY.items()))


def reset_registry_for_tests() -> None:
    """Clear the registry. Test-only — production code must not call this."""
    _REGISTRY.clear()


# Import the built-in exporters so their @register_exporter decorators run.
# These imports MUST live at the bottom of the module (after the decorator is
# defined) and are intentionally `noqa: F401, E402` — they exist for side
# effects, not for re-export. Story 1.11 ships these two; future stories add
# more from their own apps via `AccountsConfig.ready()` autoloader.
from apps.accounts.exporters import accounts as _accounts  # noqa: F401, E402
from apps.accounts.exporters import audit as _audit  # noqa: F401, E402
