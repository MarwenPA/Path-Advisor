# Story 4.10: Composant `FicheEcole` — enrichissement densité Doctolib

**Epic:** 4 — Graphe de Parcours & Stats d'Admission (Deuxième Aha)
**Status:** ready-for-dev
**Sprint:** 7 (Graphe parcours)
**Story Key:** `4-10-composant-fiche-ecole`
**Estimation:** M

---

## 1. User Story

**As a** student viewing school information across different contexts (list, detail page, comparison)
**I want** `FicheEcole` to adapt its density and layout to its rendering context with full a11y compliance
**So that** I can quickly scan schools in a list, drill into details on a full page, or compare two schools side-by-side without losing information

---

## 2. Acceptance Criteria (BDD)

### AC1 — Three variants render correctly

**Given** the `FicheEcole` component is rendered with `variant="card"`, `variant="expanded"`, or `variant="compare"`
**When** it mounts
**Then** `variant="card"` renders a compact grid-friendly layout with: school name, city+type badge, `CarteAdmission` placeholder (or stat), and exactly 3 metadata pills (selectivity, public/privé, alternance)
**And** `variant="expanded"` renders all fields: header, full metadata `<dl>`, description text with expand toggle, all formations list, full dates section, and admission stat block
**And** `variant="compare"` renders a compact column layout (no extra padding, no "Retour" CTA) suitable for embedding in a 2-column side-by-side view

### AC2 — A11y semantic structure

**Given** any variant of `FicheEcole`
**When** a screen reader navigates the component
**Then** the container has `role="article"`
**And** `variant="card"` uses `<h2>` for school name (assuming it is within a list under a page `<h1>`)
**And** `variant="expanded"` uses `<h1>` for school name (it is the main page heading)
**And** all metadata (durée, statut, alternance, internat, coût, sélectivité) is structured as `<dl>` with `<dt>` label and `<dd>` value pairs
**And** all interactive buttons have a minimum touch target of 44×44px

### AC3 — Selectivity displayed as accessible stars

**Given** a school with `selectivity_index=3`
**When** `FicheEcole` renders the sélectivité field
**Then** the `SelectivityStars` component shows 3 filled stars and 2 empty stars out of 5
**And** the stars container has `aria-label="Sélectivité: 3 sur 5"` (exact string)
**And** the stars are purely decorative SVG/emoji (not interactive, `aria-hidden` on individual stars)
**And** the scale is inverted for display clarity: 1 star = most selective (grande école), 5 stars = least selective (open access) — documented in component JSDoc

### AC4 — Léa profile (incomplete data) — indicative state

**Given** a student with `has_bulletins=False` (Léa scenario)
**When** `FicheEcole` renders with `admissionStat` having `label="indicative"`
**Then** the `CarteAdmission` section renders the label "estimation indicative — affine avec ton profil"
**And** the visual structure is strictly identical to a complete-profile rendering (same layout, same dimensions, same color palette)
**And** no additional warning, disclaimer, or stigmatizing message is shown (UX-DR25: normal mode = degraded mode)

### AC5 — Variant `compare` integrates correctly in `SchoolCompare`

**Given** `SchoolCompare` receives `school1` and `school2` props
**When** it renders
**Then** two `FicheEcole variant="compare"` columns are displayed side-by-side
**And** on mobile (< 640px) the two columns stack vertically
**And** corresponding metadata rows are visually aligned between the two columns

---

## 3. Tasks / Subtasks

### T1 — Refactor `FicheEcole` to support 3 variants

- [ ] Update `apps/web/src/components/schools/FicheEcole.tsx` (created in Story 4.4):
  - Add `variant: "card" | "expanded" | "compare"` prop (required, no default — force explicit choice)
  - `variant="card"`: compact layout. Structure:
    ```
    <article role="article" class="rounded-xl border p-4 ...">
      <header>
        <h2>{name}</h2>
        <span>{city}</span>
        <TypeBadge type={school.type} />
        <FavoriteButton ... />  {/* Story 4.8 */}
      </header>
      <div class="pills-row">
        <SelectivityStars index={selectivity_index} />
        <Pill>{public_private}</Pill>
        {apprenticeship && <Pill>Alternance</Pill>}
      </div>
      {/* CarteAdmission placeholder */}
      <div class="admission-block">
        {admissionStat ? renderAdmissionStat() : <p>Données non disponibles</p>}
        {/* TODO(story-4-11): replace with <CarteAdmission> */}
      </div>
    </article>
    ```
  - `variant="expanded"`: full layout. All card content + `<dl>` metadata + description + formations list + dates + "Retour" CTA. Use `<h1>` instead of `<h2>` for school name.
  - `variant="compare"`: same as `card` but `p-0` (no padding) and no "Retour" CTA — intended to be wrapped by `SchoolCompare`.
- [ ] Ensure `variant` prop is passed through to all internal sub-components (e.g. heading level, CTA visibility).

### T2 — A11y semantic refactor

- [ ] Replace top-level `<div>` wrapper with `<article role="article">` in all variants.
- [ ] Replace metadata key-value `<div>` pairs with `<dl>`:
  ```html
  <dl class="grid grid-cols-2 gap-2 text-sm">
    <dt class="text-slate-500">Durée</dt>
    <dd class="font-medium">{duration}</dd>
    <dt class="text-slate-500">Statut</dt>
    <dd>{public_private_label}</dd>
    <dt class="text-slate-500">Alternance</dt>
    <dd>{apprenticeship ? "Oui" : "Non"}</dd>
    <dt class="text-slate-500">Internat</dt>
    <dd>{internship ? "Disponible" : "Non"}</dd>
    <dt class="text-slate-500">Coût annuel</dt>
    <dd>{tuitionText}</dd>
    <dt class="text-slate-500">Sélectivité</dt>
    <dd><SelectivityStars index={selectivity_index} /></dd>
  </dl>
  ```
  Note: in `variant="card"`, show only the 3 priority pills (not the full `<dl>`). In `variant="expanded"` and `variant="compare"`, show the full `<dl>`.
- [ ] Touch targets: all buttons (`FavoriteButton`, "Lire la suite", remove button from Story 4.8) must have `min-w-[44px] min-h-[44px]` enforced via Tailwind or inline style. Audit existing buttons in FicheEcole for compliance.

### T3 — `SelectivityStars` component

- [ ] Create `apps/web/src/components/schools/SelectivityStars.tsx`:
  ```typescript
  interface SelectivityStarsProps {
    index: number  // 1–5, where 1 = most selective, 5 = least selective
    className?: string
  }
  ```
- [ ] Render 5 star glyphs. Stars 1 through `index` are filled (★), stars `index+1` through 5 are empty (☆). Use SVG or Unicode — if SVG, use `aria-hidden="true"` on each SVG.
- [ ] Container: `<span aria-label={"Sélectivité: " + index + " sur 5"} role="img">`. The `role="img"` with `aria-label` makes the group semantically a single icon with a text alternative.
- [ ] Add JSDoc comment explaining the inverted scale: `/** 1 star = very selective (grandes écoles), 5 stars = open access. Displayed filled stars = index. */`
- [ ] Colors: filled star `text-amber-400`, empty star `text-slate-200`. Tailwind class-based (no inline color).
- [ ] Size: default `text-lg` (18px), accept `className` override.

### T4 — `SchoolCompare` component

- [ ] Create `apps/web/src/components/schools/SchoolCompare.tsx`:
  ```typescript
  interface SchoolCompareProps {
    school1: SchoolDetail
    admissionStat1: AdmissionStat | null
    school2: SchoolDetail
    admissionStat2: AdmissionStat | null
  }
  ```
- [ ] Layout: `<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">`:
  - Column 1: `<FicheEcole variant="compare" school={school1} admissionStat={admissionStat1} />`
  - Column 2: `<FicheEcole variant="compare" school={school2} admissionStat={admissionStat2} />`
- [ ] Add a sticky header row above the two columns showing just the school names for quick reference on scroll:
  ```html
  <div class="sticky top-0 bg-white z-10 grid grid-cols-2 border-b py-2 px-4 sm:px-0">
    <span class="font-semibold truncate">{school1.name}</span>
    <span class="font-semibold truncate">{school2.name}</span>
  </div>
  ```
- [ ] The `variant="compare"` FicheEcole instances use the full `<dl>` metadata structure (same as expanded) so corresponding rows align between columns.
- [ ] Export `SchoolCompare` from `apps/web/src/components/schools/index.ts` (create barrel file if not present).

### T5 — Tests

- [ ] `apps/web/src/components/schools/__tests__/FicheEcole.test.tsx` (Vitest + RTL) — extend/replace existing Story 4.4 tests:
  - `variant="card"`: renders school name as `<h2>`, `role="article"` present, exactly 3 pills visible
  - `variant="expanded"`: renders school name as `<h1>`, full `<dl>` with all metadata terms present (`dt` containing "Durée", "Statut", "Alternance", "Internat", "Coût annuel", "Sélectivité")
  - `variant="compare"`: no "Retour au parcours" CTA rendered
  - All variants: `role="article"` present; `<dl>`, `<dt>`, `<dd>` present in expanded/compare
  - Touch targets: query the favorite button, assert `offsetWidth >= 44 || className includes 'min-w-[44px]'`
  - `admissionStat` with `label="indicative"` → "estimation indicative" text visible, no extra warning text
- [ ] `apps/web/src/components/schools/__tests__/SelectivityStars.test.tsx` (Vitest + RTL):
  - `index=1` → 1 filled star, 4 empty stars; `aria-label="Sélectivité: 1 sur 5"`
  - `index=3` → 3 filled stars, 2 empty stars; `aria-label="Sélectivité: 3 sur 5"`
  - `index=5` → 5 filled stars, 0 empty stars
  - Container has `role="img"`
- [ ] `apps/web/src/components/schools/__tests__/SchoolCompare.test.tsx` (Vitest + RTL):
  - Renders 2 `FicheEcole` instances (check for 2 elements with `role="article"`)
  - Both school names appear in the document
  - Sticky header contains both school names
  - Snapshot or class check for `grid-cols-2` layout

---

## 4. Dev Notes

- **Story 4.4 dependency**: this story is a pure enrichment of `FicheEcole` created in Story 4.4. Read the full file `apps/web/src/components/schools/FicheEcole.tsx` before making changes to understand its current state, props, and existing tests.
- **Do NOT break Story 4.4 tests**: extend `FicheEcole.test.tsx` rather than replacing it. All existing ACs from 4.4 must still pass.
- **CarteAdmission placeholder**: Story 4.11 will introduce `CarteAdmission`. Until merged, keep the plain text admission block with `// TODO(story-4-11): replace with <CarteAdmission>` comment. This story must NOT attempt to implement `CarteAdmission`.
- **heading level contract**: `<h2>` in card variant assumes `FicheEcole` is embedded in a page that already has an `<h1>`. In expanded variant, FicheEcole IS the page, so `<h1>` is correct. `SchoolCompare` uses `variant="compare"` which has no heading at all — the sticky header outside `FicheEcole` provides the visual label.
- **Tailwind patterns**: follow `apps/web/src/components/professions/FicheMetier.tsx` for class patterns, responsive breakpoints, and pill/badge styles. Do not introduce new design tokens.
- **Type file**: `SchoolDetail`, `AdmissionStat`, `Formation` types are in `apps/web/src/lib/api/types/schools.ts` (created in Story 4.4). Add any missing fields needed for new props without breaking existing type consumers.
- **Barrel export**: if `apps/web/src/components/schools/index.ts` does not exist, create it and export `FicheEcole`, `SelectivityStars`, `SchoolCompare`.
- Reference files: `apps/web/src/components/schools/FicheEcole.tsx`, `apps/web/src/lib/api/types/schools.ts`, `apps/web/src/components/professions/FicheMetier.tsx`.
- All frontend tests: Vitest + RTL, `__tests__/` co-located with component files.

---

## 5. Dev Agent Record

### Agent Model Used
_À remplir_

### Completion Notes List
_À remplir_

### File List
_À remplir_

### Change Log
- 2026-06-21 — Story 4.10 créée.
