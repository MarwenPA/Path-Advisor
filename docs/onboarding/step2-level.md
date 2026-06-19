# Onboarding step 2 — Niveau scolaire, filière & spécialités

> Story 2.2 reference doc. For the full BDD spec see
> [`_bmad-output/implementation-artifacts/2-2-onboarding-niveau-filiere-specialites.md`](../../_bmad-output/implementation-artifacts/2-2-onboarding-niveau-filiere-specialites.md).

## Flow

```
/onboarding/step-1 ──► /onboarding/step-2
                            │
                            ├─ NiveauPicker    (5 options)
                            │       │
                            │       ├─ college_3eme ──► Branche3eme (intended_track)
                            │       ├─ lycee_2nde  ──► BrancheLycee (filière → spés si applicable)
                            │       ├─ lycee_1ere  ──► BrancheLycee
                            │       ├─ lycee_terminale ──► BrancheLycee
                            │       └─ postbac ──► BranchePostbac (year + formation_type)
                            │
                            ├─ "Continuer" ──► RecapCard (recap view)
                            │       └─ "Continuer vers les bulletins" ──► PATCH commit=True ──► /step-3
                            │
                            └─ "Plus tard" ──► SkipDialog ──► PATCH skip=True ──► /step-3
```

Each commit sends `PATCH /api/v1/students/me/onboarding/level` with `commit=True`.
Drafts auto-persist to localStorage (debounce 500ms) keyed by userId.

## Branching matrix

| Level | Required fields | Spec count |
|---|---|---|
| `college_3eme` | `intended_track` | — |
| `lycee_2nde` général/techno | `filiere` | 0 (pas encore) |
| `lycee_2nde` pro | `filiere` | 1 |
| `lycee_1ere` général | `filiere` + `specialites` | 3 |
| `lycee_1ere` techno | `filiere` + `sous_filiere_techno` | 0 |
| `lycee_terminale` général | `filiere` + `specialites` | 2 |
| `lycee_terminale` techno | `filiere` + `sous_filiere_techno` | 0 |
| `postbac` | `postbac_year` + `postbac_formation_type` | — |

`pause` + `aucune` is a valid combination for Léa (dignity constraint — no guilt copy).

## Referential

Frontend: `apps/web/src/lib/onboarding/levels.ts`
Backend mirror: `apps/api/apps/students/onboarding/levels.py`

`REF_VERSION = "2026-05-v1"` stored in DB for longitudinal audit.

## Persona constraints

- **Mehdi anti-stigma**: `bac pro` visually identical to `bac général` — no special CSS, badge, or encouragement copy.
- **Léa dignité**: `pause` + `aucune` accepted without error or guilt-inducing text.
- **Sarah efficacité**: Terminale général path completable in ≤ 3 taps + recap.

## API

```
GET  /api/v1/students/me/onboarding/level
PATCH /api/v1/students/me/onboarding/level
```

**Partial PATCH** (draft save) — validates present fields only, sets status `in_progress`.

**Commit PATCH** (`commit: true`) — validates full matrix (§4.5), sets status `completed`, emits `student_level_declared` Celery event.

**Skip PATCH** (`skip: true`) — sets status `skipped`, no matrix validation.

## Components

| Component | File | Purpose |
|---|---|---|
| `OnboardingStep2` | `onboarding-step-2.tsx` | Orchestrator, view state machine |
| `NiveauPicker` | `niveau-picker.tsx` | RadioGroup 5 niveaux |
| `Branche3eme` | `branche-3eme.tsx` | RadioGroup 4 tracks |
| `BrancheLycee` | `branche-lycee.tsx` | Filière + sous-filière + spés |
| `BranchePostbac` | `branche-postbac.tsx` | Year + formation type |
| `SpecialitesPicker` | `specialites-picker.tsx` | Chip multi-select with cap |
| `RecapCard` | `recap-card.tsx` | Recap before commit |
| `SkipDialog` | `skip-dialog-step2.tsx` | "Plus tard" confirmation |

## Tests

- Backend: `apps/api/apps/students/tests/test_onboarding_step2.py` — 23 tests
- Frontend referentials: `apps/web/src/lib/onboarding/levels.test.ts` — 32 tests
- Frontend components: `apps/web/src/components/features/onboarding/onboarding-step-2.test.tsx` — 20 tests
