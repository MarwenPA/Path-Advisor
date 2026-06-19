# BulletinsMiniCTA

Story 2.5 AC5 — Contextual (non-dismissable) CTA for postponed users.

## Props

| Prop | Type | Required | Description |
|---|---|---|---|
| `context` | `"graph" \| "stat" \| "fiche_metier"` | yes | Determines copy variant |
| `metier_id` | `string` | no | For analytics payload |
| `onAddClick` | `() => void` | yes | Opens `BulletinsAddSheet` |

## Behaviour

- Renders only when `bulletins_status !== "completed"`
- Not dismissable — stays anchored in the page scroll (not sticky/floating)
- Uses `Card` shadcn with `bg-bg-2`, secondary CTA button (never primary)

## Accessibility

- `<aside role="complementary" aria-label="Compléter ton profil">`

## Copy rules

- graph: *"Tes stats deviendront personnalisées en moins d'une minute."*
- stat/fiche_metier: *"Affine ton estimation avec tes bulletins scolaires."*
- ❌ Never: "débloque", "vraies stats", "incomplet", "%"
