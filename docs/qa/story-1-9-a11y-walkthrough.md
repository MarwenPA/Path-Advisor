# Story 1.9 — Accessibility walkthrough (RGAA AA)

## Source-level audit (dev-side)

| RGAA AA criterion | How Story 1.9 satisfies it | Code reference |
|---|---|---|
| Each region announced by a screen reader | `<main aria-labelledby="tier-access-list-title">` + visible `<h1 id="tier-access-list-title">` | `acces-tiers/page.tsx` |
| Live region for dynamic content | `<section aria-live="polite">` wraps the list | `acces-tiers/page.tsx` |
| Each card has an accessible name | `<article aria-labelledby={titleId}>` referencing the display-name `<h3>` | `tier-access-card.tsx` |
| Disabled controls explain what they do | Disabled `<Button>` has `aria-describedby={visibilityListId}` + `aria-label="Révocation à venir"` | `tier-access-card.tsx` |
| Badge conveys semantic info | `<span aria-label="Type d'accès : Parent">` | `tier-access-card.tsx` |
| Dates exposed in both relative + absolute form | `<time datetime={iso} title={absoluteFR}>il y a 3 semaines</time>` | `tier-access-card.tsx` |
| Keyboard focus visible | `:focus-visible` outline via design tokens | `tokens.css` (Story 1.2) |
| Empty state has discoverable copy | `data-testid="access-list-empty"` ; copy is FR-localized full sentence | `access-list-empty-state.tsx` |

## Manual walkthrough — PENDING

The Story 1.9 spec calls for a NVDA + VoiceOver walkthrough captured here. The dev environment does not have access to those tools ; this section is reserved for the QA pass.

When you run the walkthrough, capture :

1. **NVDA reading order** through the page : title → description → first card title → tier badge → granted date → visible list → masked list → revoke button (announced as disabled + with the describedby reference).
2. **VoiceOver focus ring visibility** : tab from the page header into the first card and out — every interactive element must show a visible focus ring.
3. **Empty state** : navigate to the page when no tier has been granted — the empty-state copy must be the SOLE focused content, no spurious skeletons or loading indicators.

Append your findings to this file with timestamps.
