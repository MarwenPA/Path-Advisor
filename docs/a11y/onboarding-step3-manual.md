# A11y Checklist — Onboarding Step 3 Manual (Story 2.4)

RGAA AA target. VoiceOver iOS + keyboard-only + axe-core.

## HTML Semantics

- `<form aria-label="Saisie manuelle des notes">` — wraps all subject rows
- Each subject: `<fieldset>` + `<legend class="sr-only">{subject}</legend>`
- Note input: `<input aria-label>` with explicit `<label for>` or aria-label
- Errors: `<span role="alert" aria-live="polite">` — announced on blur only
- Tabs: `role="tablist"`, `role="tab"`, `aria-selected`

## Keyboard Navigation Order

1. Back chevron (`<`)
2. Trimestre tabs (arrow keys within tablist)
3. Bulletin label edit (if editable)
4. For each subject: note input → "Ajouter appréciation" button → delete (X) button
5. "+ Ajouter une matière manquante" button
6. "Valider et continuer" (primary)
7. "⏭ Plus tard" link

## Dynamic Announcements (aria-live)

- Note saved: `"Note Mathématiques, 14.5 sur 20, enregistrée."`
- Error: `"Erreur Mathématiques : note entre 0 et 20."`
- Subject removed: `"Matière supprimée. Bouton Annuler disponible."`

## Reduced Motion

- Expand/collapse appreciation: height transition → 0ms under `prefers-reduced-motion: reduce`
- No other animations on this screen

## Touch Targets

All interactive elements ≥ 44×44 px touch area (via padding if needed).

## Zoom 200%

Tested at 320px viewport × 200% — no horizontal overflow, layout reflows correctly.

## Manual VoiceOver Test Script

1. Open page with VoiceOver on iPhone/iPad
2. Swipe through header → tabs → first subject
3. Type "14" in Mathématiques note field → swipe right → verify announcement
4. Navigate to "Ajouter une appréciation" → tap → verify Textarea announced
5. Navigate to X button → tap → verify removal announcement
6. Navigate to footer → tap "Valider et continuer" with 0 subjects filled → verify helper
7. Tap "Plus tard" link → verify navigation
