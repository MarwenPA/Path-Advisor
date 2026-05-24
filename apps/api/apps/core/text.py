"""Text helpers used across services."""

from __future__ import annotations


def mask_email(email: str) -> str:
    """Return a privacy-preserving rendering of an email address.

    Format: `<first-char>***@<first-char-of-domain>**.<tld>`.
    Used on the parental-consent landing page (Story 1.4 §AC4) so the parent
    can recognise their child by context without the API revealing the full
    address. Edge cases:

    - Empty / missing `@` → returns `***` (defensive — never crash for the UI).
    - Local part of length 1 → preserves the single char then `***`.
    - Domain without `.` → returns `<char>***@<char>**` (no TLD branch).

    Examples:
        >>> mask_email("mehdi.l@gmail.com")
        'm***@g**.com'
        >>> mask_email("a@b.fr")
        'a***@b**.fr'
        >>> mask_email("alice@example.co.uk")
        'a***@e**.co.uk'
    """
    if not email or "@" not in email:
        return "***"

    local, _, domain = email.partition("@")
    if not local or not domain:
        return "***"

    local_mask = f"{local[0]}***"

    if "." in domain:
        host, _, tld = domain.partition(".")
        if not host:
            return f"{local_mask}@***.{tld}"
        return f"{local_mask}@{host[0]}**.{tld}"
    return f"{local_mask}@{domain[0]}**"
