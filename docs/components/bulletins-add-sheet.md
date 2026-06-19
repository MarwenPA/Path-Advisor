# BulletinsAddSheet

Story 2.5 AC6 — Mini-flow for adding bulletins without a full re-onboarding.

## Props

| Prop | Type | Required | Description |
|---|---|---|---|
| `open` | `boolean` | yes | Sheet visibility |
| `onClose` | `() => void` | yes | Called on cancel or close |
| `onSuccess` | `() => void` | yes | Called after successful commit |

## Behaviour

- `Sheet` bottom (mobile) / right (desktop) via `@radix-ui/react-dialog`
- Focus trap active when open; Échap closes
- Two equal-weight action buttons (no dark pattern — Story 1.14 principle)
  - Scanner / importer → delegates to `FilePickerSheet` (Story 2.3)
  - Saisir à la main → delegates to `MatiereInputRow` mini-form (Story 2.4)
- "Annuler" tertiary button closes the sheet without any state change

## On commit success (wired by parent)

1. Invalidate `["student-profile"]` TanStack Query cache
2. Toast: *"Profil mis à jour — stats en cours de recalcul…"*
3. Emit `bulletins_added_via_mini_flow` analytics event
4. Close sheet

## Accessibility

- `aria-modal="true"`, `aria-labelledby` pointing to SheetTitle
- Focus initially on first action button
