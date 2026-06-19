# BulletinsPostponedBanner

Story 2.5 AC3 — Discrete banner for users with `bulletins_status === "postponed"`.

## Props

| Prop | Type | Default | Description |
|---|---|---|---|
| `position` | `"footer-fixed" \| "sidebar"` | `"footer-fixed"` | Layout variant |
| `onAddClick` | `() => void` | required | Opens `BulletinsAddSheet` |

## Visibility logic

Rendered only when ALL conditions hold:
1. `profile.bulletins_status === "postponed"`
2. `isBannerVisible(profile)` — `bulletins_postponed_banner_dismissed_until` is null or in the past

Disappears permanently when `bulletins_status === "completed"`.

## Dismiss

Click `✕` → `POST /api/v1/students/me/bulletins/banner/dismiss` → sets 7-day TTL.
`aria-live="polite"` announces *"Suggestion masquée pour 7 jours."*

## Accessibility

- `<aside role="complementary" aria-label="Suggestion d'ajout bulletins">`
- Tab order: text → Ajouter button → ✕ button
- Échap closes banner when focused

## Copy rules (immutable)

- ✅ *"Tu peux ajouter tes bulletins à tout moment pour des stats personnalisées."*
- ❌ Never: "incomplet", "manque", "débloque", "%", "profil dégradé"
