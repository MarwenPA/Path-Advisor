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


def mask_local_part(email: str) -> str:
    """Return a privacy-preserving stand-in for a "first name" derived from
    an email's local-part, for display on UNAUTHENTICATED / public surfaces.

    Code-review finding (Story 6.1, 2026-08): `parent_invitation_status` (a
    public, token-only endpoint) used to return the RAW local-part
    (`email.split("@")[0]`, e.g. "lea.martin") as `student_first_name`,
    completely defeating the `mask_email` masking applied to
    `student_masked_email` in the very same response. A leaked/forwarded
    token would reveal the student's real identity. This helper applies the
    same `<first-char>***` masking style as `mask_email` so a partial visual
    cue survives without leaking the identifiable string.

    Internal-only surfaces (email templates sent directly to the invited
    parent's or student's own inbox — the legitimate, already-known
    recipient) intentionally keep using the raw local-part; only the public
    API response needs masking.

    Examples:
        >>> mask_local_part("lea.martin@example.com")
        'l***'
        >>> mask_local_part("a@b.fr")
        'a***'
    """
    if not email or "@" not in email:
        return "***"
    local = email.split("@", 1)[0]
    if not local:
        return "***"
    return f"{local[0]}***"
