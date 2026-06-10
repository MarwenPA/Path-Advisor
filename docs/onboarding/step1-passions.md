# Onboarding step 1 — Passions, valeurs & centres d'intérêt

> Story 2.1 reference doc. Captures the user flow, component map,
> referential structure, and copy variants. For the full BDD spec see
> [`_bmad-output/implementation-artifacts/2-1-onboarding-passions-interets-valeurs.md`](../../_bmad-output/implementation-artifacts/2-1-onboarding-passions-interets-valeurs.md).

## Flow

```
signup → email-verify → /onboarding/step-1
                            │
                            ├─ 1A passions    (≥ 3, ≤ 8 incl. ≤ 5 custom)
                            ├─ 1B valeurs     (≥ 3, ≤ 5)
                            └─ 1C intérêts    (3 optional free-form fields)
                            │
                            └─ "Plus tard" header button → SkipDialog → /step-2
```

Each sub-step ends in a `PATCH /api/v1/students/me/onboarding/passions`
with the corresponding `step` discriminator. The hook keeps a
localStorage draft so a network blip never costs the user their input:
the screen continues to the next sub-step, and the draft re-applies on
the next page load (AC5 / AC6).

The orchestrator redirects to `/onboarding/step-2` when:
- The user completes 1C (PATCH `step=interets` succeeds OR fails — UX
  beats strict sync).
- The user confirms "Plus tard" in the SkipDialog (PATCH `step=skip`).
- The page is opened while the server reports
  `onboarding_step1_status === "completed"` (AC10 — re-entry guard).

## Component map

| Component | Spec ref | Responsibility |
|---|---|---|
| `OnboardingStep1` | AC1, orchestration | Substep state machine, Continue / Terminer gating, header + footer, SR announcer, AC10 redirect |
| `ProgressDots` | AC1, AC3 | `● ○ ○` indicator, jump-back via clicks on past dots |
| `PassionsPicker` | AC2 | 20 referential chips + debounced search + custom: passions (up to 5, max 8 total) |
| `ValeursPicker` | AC3 | 12 large cards, multi-select 3 ≤ N ≤ 5 |
| `InteretsFreeForm` | AC4 | 3 optional textareas, 200-char cap, suggestion chips |
| `SkipDialog` | AC7 | Composes `<ConsentDialog>` (Story 1.14) for the Plus tard flow |
| `useOnboardingStep1` | AC5, AC6 | TanStack Query GET + PATCH + localStorage draft |

## Referentials

Source of truth: [`apps/web/src/lib/onboarding/referentials.ts`](../../apps/web/src/lib/onboarding/referentials.ts).
Python mirror: [`apps/api/apps/students/onboarding/referentials.py`](../../apps/api/apps/students/onboarding/referentials.py).
Cross-language sync enforced by `apps/api/apps/students/tests/test_referentials.py::TestCrossLanguageSync`.

- **20 passions** (curated MVP) — IDs are kebab-case ASCII, stable across
  label changes. `custom:<slug>` accepted up to 5 per user (slug = lower-case
  letters/digits/hyphens, 1-30 chars, no leading/trailing hyphen).
- **12 valeurs** (curated, no custom). Each carries a short FR description.
- **3 × 5 intérêt suggestions** — clicked chips append to the current field
  (separator " · ") respecting the 200-char cap.

## Copy variants (AC8 — UX-DR30)

`getOnboardingCopy(level)` returns a bundle per `SchoolLevel`:

| Level | Trigger | Passions title | Intérêt placeholder #3 |
|---|---|---|---|
| `college` | < 15 yo | *Ce qui te branche, en vrai* | *Ex. La leçon où tu t'es pas ennuyé(e), un débat en cours…* |
| `lycee` | 15–17 yo (fallback) | *Qu'est-ce qui te plaît, vraiment ?* | *Ex. La séquence sur la photosynthèse en 2nde, un débat en HGGSP, un TP de SVT…* |
| `postbac` | ≥ 18 yo | *Ce qui t'inspire en ce moment* | *Ex. Un cours marquant en L1, un projet de stage, une lecture pro…* |

**Story 2.1 ships with the `lycee` fallback hard-coded** at the orchestrator
level — `birth_date` is not yet exposed by the `/auth/user/` API surface (it
lives on `accounts.User.birth_date` but is filtered out of
`UserDetailsSerializer`). Surfacing it is a follow-up item tracked in
`deferred-work.md` — adding it to the user serializer is a sub-1-hour change
when Story 2.2 brings the niveau/filière screen online and consumes it too.

## Persistence model

- **GET** returns the merged state ; if the row doesn't exist (a user that
  hasn't started yet), the endpoint shapes an empty payload with
  `onboarding_step1_status: "pending"` — the orchestrator treats this as the
  start state. The row is created lazily by the first **PATCH**.
- **PATCH** is discriminated by `step`: a single payload only carries the
  fields tied to that sub-step (`passions: [...]` for `step=passions`,
  `valeurs: [...]` for `step=valeurs`, `interets: {1, 2, 3}` for
  `step=interets`, no body for `step=skip`). Mixed payloads are 400'd by
  the serializer.
- **localStorage** key `onboarding_step1_draft` mirrors the snapshot's
  `passions`, `valeurs`, `interets` between PATCHes. The hook writes on
  every snapshot change and clears once the server confirms
  `onboarding_step1_status === "completed"`. PATCH failures (network /
  5xx) keep the draft intact so the orchestrator can move on with no data
  loss.

## Skip semantics

`SkipDialog` PATCHes `step=skip`. The backend decides between two
post-skip statuses based on whether the profile already carries partial
data when the skip lands:

- **`skipped`** — no passion / no valeur / no intérêt at the time of skip.
- **`partial_skipped`** — at least one sub-step had been validated already.

This split lets the future Story 2.7 (maturité de profil) weight a hard
skip differently from a partial completion — the user who finished 1A + 1B
then bailed on 1C carries more signal than a user who skipped from 1A
without entering anything.

## Tests

| Layer | File | Coverage |
|---|---|---|
| Hook | `apps/web/src/hooks/use-onboarding-step-1.test.tsx` | Initial draft hydration, snapshot persistence, draft clear on completed |
| Components | `apps/web/src/components/features/onboarding/*.test.tsx` | One file per component, ARIA roles, controlled props contract |
| Backend | `apps/api/apps/students/tests/test_views.py` | GET defaults, PATCH per step, mixed-step rejection, RLS-aware partial preservation |
| Cross-lang | `apps/api/apps/students/tests/test_referentials.py::TestCrossLanguageSync` | Asserts the FE referential matches the BE referential ID-for-ID |

E2E (Playwright 3-personas) and manual VoiceOver / NVDA validation are
**deferred to Story 2.3 integration** — the OCR story consumes this screen
as the prologue to its own flow, and validating both together makes more
sense than testing 2.1 in isolation. The deferral is tracked in
`_bmad-output/implementation-artifacts/deferred-work.md`.
