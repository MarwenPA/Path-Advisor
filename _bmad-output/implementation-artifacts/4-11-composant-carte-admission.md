# Story 4.11: Composant `CarteAdmission` (Revolut-style)

**Epic:** 4 — Graphe de Parcours & Stats d'Admission (Deuxième Aha)
**Status:** ready-for-dev
**Sprint:** 7 (Graphe parcours)
**Story Key:** `4-11-composant-carte-admission`
**Estimation:** M

---

## 1. User Story

**As a** Path-Advisor developer
**I want** a reusable atomic `CarteAdmission` component that displays an admission stat with qualitative framing, context line, and action lever
**So that** every admission stat displayed across the app (graph node, school card, comparison list, PNG export) is consistent, accessible, and defensible (UX-DR8 + UX-DR24)

---

## 2. Acceptance Criteria (BDD)

### AC1 — Core rendering with all 4 variants

**Given** the component receives `admissionStat` (with `min_proba`, `expected_proba`, `max_proba`, `label`, `context_line`, `action_lever`) and a `variant` prop
**When** it renders
**Then** `variant="large"` renders `expected_proba` as `display-1` (48–56px), used for the graph target node
**And** `variant="medium"` renders `expected_proba` as `display-2` (32–40px), used inside `FicheEcole`
**And** `variant="small"` renders `expected_proba` as a compact badge (text-2xl), used in comparison lists and `ParcoursCard`
**And** `variant="export"` renders identical to `medium` but with no hover states, no `action_lever` section, `pointer-events-none`, and a `data-export` attribute on the wrapper div

### AC2 — Semantic color coding

**Given** an `admissionStat.expected_proba` value is provided
**When** the component renders the stat
**Then** `expected_proba < 30` → text color `text-red-600` and label badge `bg-red-50 text-red-700`
**And** `30 ≤ expected_proba < 50` → text color `text-orange-500` and label badge `bg-orange-50 text-orange-700`
**And** `50 ≤ expected_proba ≤ 70` → text color `text-text-muted` (neutral) and label badge `bg-slate-50 text-slate-700`
**And** `expected_proba > 70` → text color `text-green-600` and label badge `bg-green-50 text-green-700`
**And** the semantic color is always doubled by the visible text label (color-blind safe, UX-DR33)

### AC3 — Accessibility — screen reader announcement

**Given** the component receives `schoolName` and `admissionStat` props
**When** a screen reader encounters the component
**Then** the root element has an `aria-label` computed as: `"{expected_proba} % d'admission à {schoolName} — {qualitativeLabel}. {action_lever if not null}"`
**And** the example for `expected_proba=38`, `schoolName="INSA Lyon"`, `label="audacieux"`, `action_lever="+ 2 points en maths feraient passer à 58 %"` produces: `"38 % d'admission à INSA Lyon — pari audacieux. + 2 points en maths feraient passer à 58 %."`
**And** decorative color indicators are `aria-hidden="true"`

### AC4 — Update badge: "+ N pts" when stat changed in last 24h

**Given** the component receives `admissionStat.updated_at` (ISO 8601) and optionally `previousProba: number`
**When** `updated_at` is within the last 24 hours AND `previousProba` is provided
**Then** a badge `"+ {delta} pts"` (where `delta = expected_proba - previousProba`) is displayed absolutely positioned top-right of the stat block
**And** the badge enters with a 200ms `fade-in` animation (CSS: `opacity 0 → 1, transition: opacity 200ms`)
**And** the badge is only shown once per session (use `sessionStorage` key `carte_admission_badge_seen_{schoolSlug}` to suppress after first view)
**And** when `updated_at` is older than 24 hours or `previousProba` is absent, no badge is rendered

### AC5 — Incomplete profile (Léa): indicative footnote without stigma

**Given** `admissionStat.label === "estimation_indicative"`
**When** the component renders
**Then** a footnote line is shown below `action_lever`: `"Estimation basée sur ton profil actuel — ajoute tes bulletins pour affiner."`
**And** the footnote uses `text-xs text-slate-500` styling (subdued, not alarming)
**And** the overall visual layout, dimensions, and color scheme are strictly identical to a complete-profile rendering (UX-DR25)
**And** `label="estimation_indicative"` maps to the qualitative display text `"estimation indicative"` (lowercase, no quotes)

---

## 3. Tasks / Subtasks

### T1 — TypeScript type `AdmissionStat` in `apps/web/src/lib/api/schools.ts`

- [ ] Create or update `apps/web/src/lib/api/schools.ts` with:
  ```typescript
  export interface AdmissionStat {
    min_proba: number            // 0–100, percentage
    expected_proba: number       // 0–100, percentage (primary display value)
    max_proba: number            // 0–100, percentage
    label: "audacieux" | "realiste" | "sur" | "estimation_indicative"
    context_line: string         // e.g. "Moyenne admise 2024 : 14,5"
    action_lever: string | null  // e.g. "+ 2 points en maths feraient passer à 58 %"
    updated_at?: string          // ISO 8601 UTC, optional
    compatibility?: "compatible" | "a_renforcer" | "au_dessus" | null  // Added by Story 4.13
  }

  export async function fetchAdmissionStat(schoolSlug: string): Promise<AdmissionStat> {
    const { apiClient } = await import('./client')
    return apiClient.post<AdmissionStat>('/api/v1/schools/predict-admission/', {
      school_slug: schoolSlug,
    })
  }
  ```
- [ ] If `apps/web/src/lib/api/types/schools.ts` already exists (from Story 4.4), consolidate the `AdmissionStat` type there rather than duplicating. Check for existing `SchoolDetail` type and import from it.
- [ ] All JSON field names stay `snake_case` (project-wide convention — no camelCase conversion).

### T2 — Component `CarteAdmission` in `apps/web/src/components/schools/CarteAdmission.tsx`

- [ ] Create `apps/web/src/components/schools/CarteAdmission.tsx`:
  ```typescript
  interface CarteAdmissionProps {
    admissionStat: AdmissionStat
    variant: "large" | "medium" | "small" | "export"
    schoolName: string           // required for aria-label
    schoolSlug?: string          // used for sessionStorage badge key
    previousProba?: number       // used for delta badge (AC4)
    className?: string
  }
  ```
- [ ] Semantic color helper (pure function, exported for tests):
  ```typescript
  export function getSemanticColor(proba: number): {
    text: string; badge: string; bgBadge: string
  }
  ```
  - Returns Tailwind class strings for each threshold (see AC2)
- [ ] `aria-label` computation helper (pure function, exported for tests):
  ```typescript
  export function buildAriaLabel(
    proba: number, schoolName: string,
    label: AdmissionStat["label"], actionLever: string | null
  ): string
  ```
- [ ] Qualitative label display map:
  ```typescript
  const LABEL_DISPLAY: Record<AdmissionStat["label"], string> = {
    audacieux: "pari audacieux",
    realiste: "pari réaliste",
    sur: "pari sûr",
    estimation_indicative: "estimation indicative",
  }
  ```
- [ ] Font size per variant:
  - `large`: `text-5xl font-bold` (≈48px)
  - `medium`: `text-3xl font-bold` (≈32px)
  - `small`: `text-2xl font-semibold`
  - `export`: same as `medium`, but wrapper has `pointer-events-none` and `data-export` attribute
- [ ] Structure:
  ```jsx
  <div
    aria-label={buildAriaLabel(...)}
    className={cn("relative", variant === "export" && "pointer-events-none")}
    data-export={variant === "export" ? true : undefined}
  >
    {/* Stat line */}
    <span className={cn(probaSizeClass, semanticColor.text)} aria-hidden="true">
      {expected_proba}%
    </span>
    {/* Qualitative label badge */}
    <span className={cn("text-xs px-2 py-0.5 rounded-full", semanticColor.bgBadge, semanticColor.badge)}>
      {LABEL_DISPLAY[label]}
    </span>
    {/* Context line */}
    <p className="text-sm text-slate-500 mt-1">{context_line}</p>
    {/* Action lever — hidden in export variant */}
    {action_lever && variant !== "export" && (
      <p className="text-sm text-slate-700 mt-1">{action_lever}</p>
    )}
    {/* Indicative footnote (AC5) */}
    {label === "estimation_indicative" && (
      <p className="text-xs text-slate-500 mt-2">
        Estimation basée sur ton profil actuel — ajoute tes bulletins pour affiner.
      </p>
    )}
    {/* Update badge (AC4) — rendered by sub-component below */}
    <UpdateBadge updatedAt={updated_at} previousProba={previousProba} schoolSlug={schoolSlug} />
  </div>
  ```

### T3 — Badge `UpdateBadge` sub-component (AC4)

- [ ] Add `UpdateBadge` as an internal component (not exported) in `CarteAdmission.tsx`:
  ```typescript
  function UpdateBadge({ updatedAt, previousProba, schoolSlug }: {
    updatedAt?: string
    previousProba?: number
    schoolSlug?: string
  })
  ```
- [ ] Logic:
  1. If `!updatedAt` or `!previousProba` → return `null`
  2. Check `Date.now() - new Date(updatedAt).getTime() < 24 * 60 * 60 * 1000`
  3. Check sessionStorage for key `carte_admission_badge_seen_${schoolSlug}` — if set, return `null`
  4. If all conditions pass: render badge, set sessionStorage key on mount (`useEffect`)
- [ ] Badge rendering:
  ```jsx
  <span className="absolute top-0 right-0 text-xs font-bold bg-green-500 text-white px-2 py-0.5 rounded-full animate-fade-in">
    + {delta} pts
  </span>
  ```
- [ ] CSS animation: add `animate-fade-in` class to Tailwind config if not present:
  ```javascript
  // tailwind.config.ts — keyframes section
  'fade-in': { from: { opacity: '0' }, to: { opacity: '1' } }
  // animation section
  'fade-in': 'fade-in 200ms ease-in forwards'
  ```

### T4 — Variant `export` for future screenshot integration

- [ ] The `export` variant wrapper must:
  - Have `data-export="true"` attribute for html2canvas targeting
  - Have `pointer-events-none` class
  - Remove all `hover:` Tailwind modifiers (use `cn()` conditional)
  - Not render `action_lever` section (AC1)
- [ ] No actual screenshot API call in this story — the wrapper is the only deliverable here. Future story (Epic 5) will wire html2canvas.

### T5 — Replace `CarteAdmission` placeholders in `FicheEcole` (Story 4.10) and `ParcoursList` (Story 4.3/4.5)

- [ ] In `apps/web/src/components/schools/FicheEcole.tsx`, find `// TODO(story-4-11): replace with <CarteAdmission>` comment (placed by Story 4.10):
  - Replace the admission block with `<CarteAdmission admissionStat={admissionStat} variant="medium" schoolName={school.name} schoolSlug={school.slug} />`
  - Import `CarteAdmission` from `./CarteAdmission`
- [ ] In `GraphParcours.tsx` target node rendering (Story 4.9), replace the inline stat text with `<CarteAdmission variant="large" .../>`.
- [ ] In any comparison grid (Story 4.5 or `SchoolCompare`), use `variant="small"`.
- [ ] Do NOT change any other FicheEcole behavior — this is a drop-in replacement only.

### T6 — Tests: `apps/web/src/components/schools/__tests__/CarteAdmission.test.tsx`

- [ ] `variant="large"` renders `text-5xl` class; `variant="small"` renders `text-2xl` class
- [ ] `expected_proba=25` → `text-red-600` class on stat; `expected_proba=40` → `text-orange-500`; `expected_proba=80` → `text-green-600`
- [ ] `buildAriaLabel(38, "INSA Lyon", "audacieux", "+ 2 points en maths feraient passer à 58 %")` → exact expected string (unit test of pure function)
- [ ] `label="estimation_indicative"` → footnote text "Estimation basée sur ton profil actuel — ajoute tes bulletins pour affiner." is present
- [ ] `label="estimation_indicative"` → visual structure identical to `label="realiste"` (same DOM structure, same wrapper class)
- [ ] `variant="export"` → no `action_lever` section rendered, `data-export="true"` attribute present
- [ ] `updatedAt` = ISO string within last 24h + `previousProba=24` + `expected_proba=38` → badge "+14 pts" visible
- [ ] `updatedAt` = ISO string 25h ago → no badge rendered
- [ ] `getSemanticColor` unit tests: 0 → red, 29 → red, 30 → orange, 50 → neutral, 71 → green, 100 → green

---

## 4. Dev Notes

### Architecture context

- **File location**: `apps/web/src/components/schools/CarteAdmission.tsx` — co-located with `FicheEcole.tsx` (established pattern from Story 4.10).
- **Type file**: check `apps/web/src/lib/api/types/schools.ts` (Story 4.4). If `AdmissionStat` is already partially defined there, extend it in place. Do not create a duplicate type in `lib/api/schools.ts` if it already exists.
- **Tailwind** only — no inline styles except for dynamically computed values (e.g., width/height percentages impossible with Tailwind). Use `cn()` (from `lib/utils.ts`) for conditional classes.
- **No new dependencies** — this is a pure Tailwind + React component. Do not introduce chart libraries.

### Reference patterns from existing codebase

- `apps/web/src/components/features/auth/login-form.tsx` — observe how conditional Tailwind classes are applied with `cn()`.
- `apps/web/src/components/professions/FicheMetier.tsx` — reference for pill/badge styling, spacing, and semantic text hierarchy.
- `apps/web/src/components/schools/FicheEcole.tsx` (Story 4.10) — contains the `// TODO(story-4-11)` comment to replace.
- `apps/web/src/components/parcours/GraphParcours.tsx` (Story 4.9) — target node where `variant="large"` is used.

### UX Design Rules to enforce

- **UX-DR25**: Mode normal = mode dégradé. The `estimation_indicative` variant must have an identical visual structure to complete-profile variants. Only the footnote text and label badge text differ.
- **UX-DR33**: Color-blind safety. Every semantic color must be paired with a text label — never convey meaning through color alone.
- **UX-DR8**: `CarteAdmission` is the primary admission stat display pattern. Once this story merges, all other stories must use this component (no raw percentage text).

### Anti-patterns to avoid

- Do NOT use hover-only states to convey the action lever — it must be always visible (mobile-first).
- Do NOT compute `delta` from `max_proba - min_proba`; delta is `expected_proba - previousProba` (the change since last session, not the probability range).
- Do NOT use `localStorage` for the badge seen state — use `sessionStorage` (badge should reappear in a new browser session so students can notice real updates).

---

## 5. Dev Agent Record

### Agent Model Used
_À remplir_

### Completion Notes List
_À remplir_

### File List
_À remplir_

### Change Log
- 2026-06-21 — Story 4.11 créée.
