# ADR 0003 — Tokenised anonymous parental consent for minors

**Status:** Accepted
**Date:** 2026-05-17
**Story:** 1.4 — Inscription élève < 15 ans avec opt-in parental
**Supersedes:** none

## Context

French law (Loi Informatique et Libertés art. 7-1) and EU GDPR art. 8 require parental authorisation
for users under 15 who consent to the processing of personal data by an online service. Path-Advisor's
MVP needs to:

1. Let the child start using the product (in "limited mode") without blocking on the parent.
2. Provide the parent a clear, low-pressure path to grant or refuse — measurable on a single email.
3. Hold a forensic record of the decision sufficient for a CNIL audit, without re-collecting
   personal data already minimised.
4. Survive the case where the parent never answers (no permanent purgatory).

The UX-design specification (§Defining Principle #6) explicitly elevates this from "legal workflow"
to "design problem" — refusing to make the child the user who pays the cost of an absent parent.

## Decision

The parent has **no Path-Advisor account at decision time**. Authentication for the single decision
moment is the URL-safe `secrets.token_urlsafe(32)` (≈ 256 bits of entropy) embedded in the consent
email. The token lives in the `parental_consents` table with:

- `parent_email` (plain) — needed to send reminders + the final expiry email.
- `expires_at = requested_at + 60 days` — denormalised to keep the suspension query indexable.
- `decision` NULL until the parent picks one (`granted`/`refused`), `decided_at` mirrors.
- `content_hash` (SHA-256 hex, 8-field canonical JSON from the ConsentDialog of Story 1.14)
  — stored as the parent's immutable proof of what they saw.

The audit log row `parental_consent.decided` carries the **hashed** parent email, decision, and
content hash. The audit table retains entries 3 years; the consent row only stays effectively
useful for the 60-day window. Plain PII therefore exists in only one place at a time.

Two Celery beat jobs (daily 04:00/04:15 UTC, pull-based queries) handle the timeline:

- `accounts.send_parental_consent_reminders` — sends one reminder per row past day 30.
- `accounts.suspend_unresolved_parental_consents` — suspends the linked user at day 60 and
  sends a final email to the child explaining the pause + the reactivation paths.

## Alternatives considered

### A — Force the parent to create an account before authorising

Rejected. 4-5 minutes of friction at the worst possible moment (a busy parent receiving an out-of-band
email). Doubles the email volume (verify parent email + then authorise) → measurably increases the
"parent ignores it" failure rate. Persona M. Martin doesn't necessarily want a Path-Advisor account —
he might never log in again after authorising. Epic 6 will offer a Parent Space later for parents
who do want one; the existing ParentalConsent row will then be linked via `parent_user_id`.

### B — Single-use token

Rejected. The parent often re-opens the email a few times before deciding (close the tab to think,
come back, read more). Single-use tokens force a "demand another email" flow which is hostile UX
and adds support load. We check `decision IS NULL` server-side instead: multi-use is fine as long
as the decision itself is single-write.

### C — Counselor / tiers autorisé fallback at MVP

Rejected for MVP. UX spec calls for "consentement par tiers autorisé" when no parent is available
(counsellor, association). Deferred to growth — adds significant scope (a separate identity model
for non-parent third parties, distinct legal opinion required) and the MVP target persona (Mehdi,
3ème) has access to at least one parental email in ≥ 95% of the funnel.

## Consequences

### Positive

- One click + ConsentDialog from the parent's side, < 2 minutes including reading.
- Audit trail is forensically complete (hash chain + content_hash) without duplicating plain PII.
- The child continues using the product (limited mode) without the parent on the critical path.
- No new infrastructure: reuses the existing email transport, allauth signal flow, audit decorator,
  and Story 1.14 ConsentDialog.

### Negative

- A 60-day TTL means a parent who answers on day 61 sees the same 409 as a malicious replay. The
  child can self-re-request via `/resend/` (Story 1.4 §AC7).
- The `parental_consents` table grows monotonically — no purge in MVP. At ~30% sub-15 signups
  the steady-state row count stays under ~10k for the first year; revisit when partitioning the
  table becomes worth it.
- The audit row's `parent_email_hash` is not a salted hash — it's reproducible across rows, which
  is intentional (parent linkage across multiple kids must be detectable from the audit table).
  This is documented in the data minimisation review and is acceptable for the 3-year retention.

## Legal references

- **France LIL art. 7-1** — parental authorisation for minors under 15 processing personal data.
- **GDPR art. 8** — EU-wide minimum age threshold; LIL transposes to 15 (down from the regulation's
  16) per French derogation.
- **CNIL référentiel relatif aux traitements de données personnelles mis en œuvre dans le cadre
  des activités sociales et médico-sociales** (2018) — recognises email-based parental opt-in as
  a sufficient consent vector when the audit trail is preserved.
