# Story 4.12: Composant `ParcoursCard` (Strava-style recap)

**Epic:** 4 — Graphe de Parcours & Stats d'Admission (Deuxième Aha)
**Status:** ready-for-dev
**Sprint:** 7 (Graphe parcours)
**Story Key:** `4-12-composant-parcours-card`
**Estimation:** S

---

## 1. User Story

**As a** Path-Advisor developer
**I want** a `ParcoursCard` component that summarizes a saved pathway as a Strava-style card with a mini-graph silhouette and a capturable layout
**So that** the "Mes paris" page is visually engaging and each saved school/pathway can eventually be shared or exported as a screenshot (UX-DR19)

---

## 2. Acceptance Criteria (BDD)

### AC1 — Full component rendering

**Given** `ParcoursCard` receives `metier` (`{ name, slug }`), `parcours` (`ParcoursNode[]`), `targetSchool` (`School`), and `admissionStat` (`AdmissionStat`)
**When** it renders
**Then** a card header displays the `metier.name` as an `<h3>` element
**And** a mini-graph SVG silhouette is rendered (see AC5 for details)
**And** `<CarteAdmission variant="small" admissionStat={admissionStat} schoolName={targetSchool.name} />` is rendered below the silhouette
**And** a footer displays a copyable summary text: `"Mon objectif : {targetSchool.name} — {expected_proba} % de chances d'admission"`
**And** a "Capturer" button is visible in the footer

### AC2 — Mobile dimensions constraint

**Given** `ParcoursCard` is rendered on a mobile viewport (360px width)
**When** it renders
**Then** the card's total rendered height does not exceed 280px
**And** the card width is 100% of its container, max 360px
**And** all content (header, SVG, CarteAdmission small, footer) is readable without horizontal scroll

### AC3 — Badge from recent stat update + sort priority in "Mes paris"

**Given** the `admissionStat.updated_at` is within the last 24 hours AND `previousProba` is passed as a prop
**When** `ParcoursCard` renders
**Then** `CarteAdmission` shows the `+ N pts` badge (delegated to `CarteAdmission`'s own badge logic — do not re-implement here)
**And** in `MesParisClient`, cards with `updated_at` within the last 24 hours are sorted to the top of their métier group

### AC4 — "Capturer" button: prepare content for screenshot

**Given** a student taps the "Capturer" button
**When** the `onClick` fires
**Then** the card root element gets a `data-capture="true"` attribute toggled on
**And** the "Capturer" button itself is visually hidden (add class `opacity-0 pointer-events-none` via state) so it does not appear in the capture
**And** the footer's copyable text remains visible (it is part of the capture content)
**And** a console note or `TODO` comment marks the future `html2canvas` integration point
**And** after 2 seconds (simulated capture delay), `data-capture` is removed and the button returns to its normal state (cleanup via `setTimeout`)

### AC5 — Mini-graph SVG silhouette

**Given** `parcours` contains 3–5 `ParcoursNode` items
**When** the SVG silhouette renders
**Then** it is an inline SVG with `width="200"` `height="60"` `viewBox="0 0 200 60"`
**And** each intermediate node is a circle with `r="4"` (8px diameter), `fill` set to `#CBD5E1` (slate-300)
**And** the target node (last node) is a circle with `r="6"` (12px diameter), `fill` matching the semantic color from `admissionStat.expected_proba` (red/orange/neutral/green — same thresholds as `CarteAdmission`)
**And** edges between nodes are `<line>` elements with `stroke="#CBD5E1"` and `strokeWidth="1.5"`
**And** nodes are evenly spaced horizontally within the 200px viewport, vertically centered at y=30
**And** the SVG has `role="img"` and `aria-label="Parcours en {n} étapes vers {targetSchool.name}"`
**And** the SVG is `aria-hidden="false"` — screen readers should get the aria-label

---

## 3. Tasks / Subtasks

### T1 — TypeScript types and component scaffold

- [ ] Create `apps/web/src/components/parcours/ParcoursCard.tsx`
- [ ] Props interface:
  ```typescript
  import { AdmissionStat } from '@/lib/api/schools'  // or types/schools.ts

  interface ParcoursCardProps {
    metier: { name: string; slug: string }
    parcours: ParcoursNode[]      // reuse type from GraphParcours (Story 4.9)
    targetSchool: {
      name: string
      slug: string
      city: string
    }
    admissionStat: AdmissionStat
    previousProba?: number        // for CarteAdmission delta badge
    className?: string
  }
  ```
- [ ] Import `ParcoursNode` from `apps/web/src/components/parcours/GraphParcours.tsx` or `apps/web/src/lib/api/types/pathways.ts` if the type was extracted there by Story 4.9. Do NOT re-define the type.
- [ ] Import `CarteAdmission` from `../schools/CarteAdmission`.

### T2 — Full `ParcoursCard` component implementation

- [ ] Card wrapper: `<article className="relative flex flex-col gap-2 rounded-xl border bg-white p-4 max-w-[360px] max-h-[280px] overflow-hidden">` with `role="article"`
- [ ] Header: `<h3 className="text-base font-semibold truncate">{metier.name}</h3>`
- [ ] SVG mini-graph (see AC5):
  ```typescript
  function MiniGraphSilhouette({
    nodes, targetSchool, admissionProba
  }: { nodes: ParcoursNode[]; targetSchool: { name: string }; admissionProba: number }) {
    const total = nodes.length
    const xStep = 200 / (total + 1)
    // compute semantic fill color for target node based on admissionProba
    // same thresholds as getSemanticColor in CarteAdmission but returns hex colors
    return (
      <svg width="200" height="60" viewBox="0 0 200 60"
        role="img"
        aria-label={`Parcours en ${total} étapes vers ${targetSchool.name}`}
      >
        {/* edges first (rendered behind nodes) */}
        {nodes.map((_, i) => i < total - 1 && (
          <line
            key={`edge-${i}`}
            x1={(i + 1) * xStep} y1={30}
            x2={(i + 2) * xStep} y2={30}
            stroke="#CBD5E1" strokeWidth="1.5"
          />
        ))}
        {/* nodes */}
        {nodes.map((node, i) => {
          const isTarget = i === total - 1
          return (
            <circle
              key={`node-${i}`}
              cx={(i + 1) * xStep} cy={30}
              r={isTarget ? 6 : 4}
              fill={isTarget ? targetFillColor : "#CBD5E1"}
            />
          )
        })}
      </svg>
    )
  }
  ```
  Note: `MiniGraphSilhouette` must be a standalone internal component (not inline JSX in `ParcoursCard`) so it is testable.
- [ ] `CarteAdmission` block: `<CarteAdmission variant="small" admissionStat={admissionStat} schoolName={targetSchool.name} schoolSlug={targetSchool.slug} previousProba={previousProba} />`
- [ ] Footer:
  ```jsx
  <footer className="flex items-center justify-between mt-auto pt-2 border-t">
    <p className="text-xs text-slate-500 truncate">
      Mon objectif : {targetSchool.name} — {admissionStat.expected_proba} % de chances d'admission
    </p>
    <button
      onClick={handleCapture}
      className={cn(
        "text-xs font-medium text-slate-600 hover:text-slate-900 ml-2",
        isCapturing && "opacity-0 pointer-events-none"
      )}
      aria-label="Capturer cette carte"
    >
      Capturer
    </button>
  </footer>
  ```
- [ ] Capture state:
  ```typescript
  const [isCapturing, setIsCapturing] = useState(false)
  const cardRef = useRef<HTMLElement>(null)

  function handleCapture() {
    setIsCapturing(true)
    cardRef.current?.setAttribute('data-capture', 'true')
    // TODO(story-5-export): wire html2canvas here
    setTimeout(() => {
      setIsCapturing(false)
      cardRef.current?.removeAttribute('data-capture')
    }, 2000)
  }
  ```

### T3 — Integration in `MesParisClient` (Story 4.8 component)

- [ ] Locate `MesParisClient` component (created in Story 4.8 — likely in `apps/web/src/components/parcours/MesParisClient.tsx` or `apps/web/src/(authenticated)/mes-paris/page.tsx`). Read the full file before modifying.
- [ ] Replace the interim `FicheEcole variant="card"` placeholder (mentioned in Story 4.8 AC2) with `<ParcoursCard>`.
- [ ] Sort order logic: within each métier group, sort `ParcoursCard` items such that cards with `admissionStat.updated_at` within the last 24h appear first. Use this comparator:
  ```typescript
  function isRecentlyUpdated(updatedAt?: string): boolean {
    if (!updatedAt) return false
    return Date.now() - new Date(updatedAt).getTime() < 24 * 60 * 60 * 1000
  }

  const sortedFavorites = favorites.sort((a, b) => {
    const aRecent = isRecentlyUpdated(a.admissionStat?.updated_at) ? -1 : 1
    const bRecent = isRecentlyUpdated(b.admissionStat?.updated_at) ? -1 : 1
    return aRecent - bRecent
  })
  ```
- [ ] Do NOT change remove-favorite logic, toast behavior, empty state, or compare button from Story 4.8.

### T4 — Tests: `apps/web/src/components/parcours/__tests__/ParcoursCard.test.tsx`

- [ ] Card renders `<h3>` with `metier.name`
- [ ] `<svg>` is present with `role="img"` and `aria-label` containing `targetSchool.name`
- [ ] `CarteAdmission` with `variant="small"` is rendered (check for `text-2xl` class or `data-variant="small"` attribute if added)
- [ ] Card max-width is 360px (check `max-w-[360px]` class or `style` attribute)
- [ ] "Capturer" button is visible; clicking it sets `data-capture="true"` on the article and hides the button (check `opacity-0` class); after 2000ms mock timer the attribute is removed
- [ ] `admissionStat.updated_at` within 24h → `CarteAdmission` badge area is present (integration check)
- [ ] Sort test in `MesParisClient`: given 2 favorites, one with `updated_at` 1h ago and one 48h ago, the recent one appears first in the rendered list

---

## 4. Dev Notes

### Key constraint: do NOT reuse `GraphParcours` for the mini silhouette

The `GraphParcours` component (Story 4.9) is the full-featured graph with animations, react-flow layout, keyboard navigation, and ARIA table alternative. It is far too heavy (bundle size, complexity) for a summary card. `ParcoursCard` has its own `MiniGraphSilhouette` — a minimal 200×60px SVG with no dependencies beyond React. This distinction is intentional and must not be collapsed.

### Semantic color in SVG (hex required)

The SVG `fill` attribute cannot use Tailwind class names. Use hex values that match the Tailwind palette:
- `audacieux` / `expected_proba < 30` → `#DC2626` (red-600)
- `realiste` / `30–50` → `#F97316` (orange-500)
- neutral / `50–70` → `#94A3B8` (slate-400)
- `sur` / `> 70` → `#16A34A` (green-600)

Define a helper `getSemanticFillColor(proba: number): string` in `ParcoursCard.tsx` using these hex values. This is separate from the Tailwind class helper in `CarteAdmission.tsx`.

### Story 4.8 integration boundary

Story 4.8 (`MesParisClient`) explicitly states: "each school is rendered as a `ParcoursCard` (Story 4.12 placeholder used until 4.12 ships — use `FicheEcole variant="card"` as interim)". This story (4.12) is where that placeholder gets replaced. Read `MesParisClient` fully before modifying — preserve all existing interactions (remove, compare, empty state, toast).

### Reference files

- `apps/web/src/components/parcours/GraphParcours.tsx` (Story 4.9) — for `ParcoursNode` type import
- `apps/web/src/components/schools/CarteAdmission.tsx` (Story 4.11) — imported here
- `MesParisClient` component location (look in `apps/web/src/app/(authenticated)/mes-paris/` or `apps/web/src/components/parcours/`)
- `apps/web/src/components/professions/FicheMetier.tsx` — reference for card layout patterns

### TypeScript strictness

- Never use `any`. If `ParcoursNode` type is not yet extracted to a shared types file, import it directly from `GraphParcours.tsx` using a named export.
- All props are required except `previousProba` and `className`.

---

## 5. Dev Agent Record

### Agent Model Used
_À remplir_

### Completion Notes List
_À remplir_

### File List
_À remplir_

### Change Log
- 2026-06-21 — Story 4.12 créée.
