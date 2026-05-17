# Consent capture pattern

When to use `<ConsentDialog />` vs an inline `<Checkbox>` for GDPR / parental / third-party consent.

## Decision table

| Situation | Use | Why |
|---|---|---|
| Signup CGU + RGPD acceptance | inline `<Checkbox>` + link to policy | the user is already in a deliberate flow ("create my account"); a modal here would be friction theatre |
| Granting a parent / counselor / partner school access to your profile | `<ConsentDialog />` | the user is **interrupted** to take a deliberate decision about a third party; structural fields (data mentioned, duration, beneficiary) make the scope auditable |
| Revoking access already granted | `<ConsentDialog />` with `isAcceptDestructive` if the revocation is irreversible from the third-party side | confirmation pattern, GDPR Art. 7 ("withdrawing must be as easy as giving") |
| Account deletion (right to be forgotten, FR11) | `<ConsentDialog />` with `isAcceptDestructive` | irreversible; explicit consequences must be shown before the click |
| Premium gating / upsell | `<PaywallContextuel />` (Story 5.11) — NOT ConsentDialog | not a consent capture; it's a purchase intent |
| Cookies / analytics opt-in | banner + checkbox (RGPD CNIL guideline) | regulator expects banner, not modal |

## Anti-patterns

- Do **not** use `ConsentDialog` to confirm a benign action (save, undo). Confirm-everywhere fatigue erodes the trust signal of the actual consent dialogs.
- Do **not** add a third button ("Decide later"). Two equal-weight buttons only; deferring is the absence of acceptance and is already covered by closing without accepting.
- Do **not** dim or hide the refuse button. The Vitest test in `consent-dialog.test.tsx` enforces equal `size="default"` classes on the default-rendered pair; non-default callers must keep `size="default"` on both buttons by convention (the test does not iterate over every variant combination).
- Do **not** persist the dialog state to localStorage. The component is stateless; persistence belongs to the consuming feature and ultimately to the audit log (Story 1.13).

## Audit log wiring (deferred)

`ConsentDialog` emits a `ConsentMeta` `{ acceptedAt, contentHash }` to the consumer's `onAccept` handler. Each consumer is responsible for POSTing this metadata to the audit endpoint when Story 1.13 ships it. Until then, log to the browser console for visual smoke-testing.

The `contentHash` is a SHA-256 digest of the canonical JSON of the dialog content (sorted keys, `dataMentioned` order preserved). It is the proof that "the user accepted *this exact* content" — if policy text or beneficiary lists later change in code, old audit entries reference the original hash and remain forensically defendable.
