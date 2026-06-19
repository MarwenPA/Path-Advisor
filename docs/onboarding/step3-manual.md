# Step 3 — Saisie manuelle des notes

Story 2.4 — Dignité Mehdi : "c'était pas si long en fait."

## Entry points (3 origins)

| Origin | URL param | Subtitle variant |
|---|---|---|
| Card 2 direct | `?origin=cards` | Standard |
| OCR GracefulFallback | `?origin=ocr_fallback` | "Pas grave, on continue à la main..." |
| ScenarioLoader opt-in > 30s | `?origin=ocr_optin` | Standard |

## Route

`/onboarding/step-3/manual` (Next.js App Router, auth-protected)

## Components

- `OnboardingStep3Manual` — orchestrator (state: activeTrim, drafts, removedIds)
- `MatiereInputRow` — core form row (note + appreciation + remove)
- `TrimestreTabs` — tab switcher (1-4 trimestres)
- `useManualBulletinDraft(trimestreId)` — localStorage debounce 500ms
- `useCommitManualBulletin()` — TanStack Query mutation, retry 3x

## Validation rules (UX-DR35 strict)

- **On blur only** — no keystroke validation
- Empty field = "non renseigné" (valid, no error)
- Note range: [0, 20] inclusive, max 2 decimal places
- Comma (`,`) normalized to dot (`.`) client-side
- Appreciation max 500 chars

## Commit semantics

- Minimum 1 matière required; otherwise show inline helper
- Partial commit accepted → `bulletins_status = "partial"`
- Toast: "On a ce qu'il faut pour démarrer — tu pourras compléter à tout moment."

## "Plus tard" exit

Footer secondary link triggers Story 2.5 postpone flow without returning to AC1 screen.

## Persona states

| Persona | Level | Subjects count |
|---|---|---|
| Sarah Terminale général | `lycee_terminale` / `general` + 3 spés | 10 |
| Mehdi 3ème | `college_3eme` | 12 |
| Léa post-bac | `postbac` | 0 (empty form + add-first button) |

## Anti-patterns

- ❌ "Tu n'as rempli que 5/10 matières !"
- ❌ "Et si tu essayais le scan ?"
- ❌ Astérisque obligatoire sur un champ
- ❌ Validation à chaque keystroke
- ❌ Confettis / célébration
