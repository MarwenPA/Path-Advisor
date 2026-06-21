# Story 4.9: Composant `GraphParcours` (LE composant central)

**Epic:** 4 — Graphe de Parcours & Stats d'Admission (Deuxième Aha)
**Status:** ready-for-dev
**Sprint:** 7 (Graphe parcours)
**Story Key:** `4-9-composant-graph-parcours`
**Estimation:** L

---

## 1. User Story

**As a** student exploring their pathway to a target profession
**I want** to see an animated visual graph of the pathway steps from my current school level to the target school
**So that** I immediately grasp the full journey in an engaging, memorable way (the "Deuxième Aha" moment)

---

## 2. Acceptance Criteria (BDD)

### AC1 — Correct rendering of nodes and edges

**Given** `GraphParcours` receives `nodes`, `edges`, `targetSchool`, `admissionStat`, and `isFirstRender` props
**When** the component mounts
**Then** the target school node is rendered 64–72px diameter in the bottom-right area with a semantic color based on `admissionStat.label` (green=sur, orange=realiste, red=audacieux, gray=null)
**And** intermediate nodes are rendered 36–44px diameter in a paler version of the color palette
**And** edges are rendered as SVG path/line elements with thickness proportional to `edge.weight` (heavier = thicker, range 1–4px)
**And** the final segment edge (last node → target) is rendered thicker than intermediate edges
**And** the `admissionStat` label and `expected_proba` percentage are rendered as a text label attached to the target node
**And** a qualitative label (e.g. "Réaliste — 62 %") is visible beside the target node

### AC2 — First-render animation sequence (720–800 ms total)

**Given** `isFirstRender={true}`
**When** the component mounts
**Then** the animation plays in this exact sequence:
  - t=0ms: Node 1 (lycée origin) fades/scales in over 120ms
  - t=180ms: Edge 1→2 draws in + Node 2 appears over 180ms
  - t=360ms: Edge 2→3 draws in + Node 3 appears over 180ms
  - t=540ms: Edge 3→target draws in + Target node appears over 220ms with a subtle overshoot scale (scale 1.1 → 1.0)
  - t=+150ms after target: labels fade in
  - Independently, the school grid below the graph transitions from opacity 0.4 to 1 over 200ms at t=+200ms after the sequence start (not blocking)
**And** the total sequence completes in 720–800ms

### AC3 — Return visit — no animation

**Given** `isFirstRender={false}`
**When** the component mounts
**Then** no animation sequence plays
**And** a 100ms subtle highlight pulse runs on the target node only
**And** all nodes and edges are immediately visible at full opacity

### AC4 — Reduced motion accessibility

**Given** the user has `prefers-reduced-motion: reduce` set in their OS
**When** the component mounts with `isFirstRender={true}`
**Then** the animation sequence is replaced by a single 200ms opacity fade-in of the entire graph
**And** no transform/scale animations run

### AC5 — A11y RGAA AA compliance

**Given** the `GraphParcours` component is rendered
**When** a screen reader or keyboard user interacts with it
**Then** the SVG container has `role="img"` and `aria-label="Parcours pour {metier}: {n} étapes"` (e.g. "Parcours pour Infirmier : 4 étapes")
**And** each node is a `<button>` element with `aria-label="{node.label} — étape {index + 1} sur {total}"` (e.g. "IUT Informatique — étape 2 sur 4")
**And** pressing Tab cycles through nodes in order: origin → intermediate nodes → target node → CTA
**And** a "Vue tableau" toggle button is visible and focusable before the graph
**And** clicking "Vue tableau" shows the accessible table alternative and hides the graph
**And** clicking "Vue graphe" restores the graph

---

## 3. Tasks / Subtasks

### T1 — Component `GraphParcours` with SVG layout

- [ ] Create `apps/web/src/components/parcours/GraphParcours.tsx`
- [ ] Props interface:
  ```typescript
  interface ParcoursNode {
    id: string
    label: string
    type: "diplome" | "ecole" | "stage" | "concours"
    school_slug?: string | null
    duration_label?: string | null
    admission_stat?: AdmissionStat | null
  }
  interface ParcoursEdge {
    source: string  // node id
    target: string  // node id
    weight: number  // 0–1
  }
  interface AdmissionStat {
    label: "audacieux" | "realiste" | "sur"
    expected_proba: number
    context_line?: string
  }
  interface GraphParcoursProps {
    nodes: ParcoursNode[]
    edges: ParcoursEdge[]
    targetSchool: string     // school slug for the final node
    admissionStat: AdmissionStat | null
    isFirstRender: boolean
    metierName: string       // for aria-label
    parcoursId: string       // for localStorage key
  }
  ```
- [ ] SVG layout: position nodes along an ascending diagonal arc from bottom-left to bottom-right. Approximate positions for N nodes: evenly distribute horizontally with a slight upward curve (quadratic bezier path reference). Use a fixed SVG viewBox (e.g. `0 0 400 220`) with `preserveAspectRatio="xMidYMid meet"` — fully responsive via `width="100%" height="auto"`.
- [ ] Node rendering: `<g>` containing `<circle>` + `<text>` label below. Target node: larger circle, semantic fill color. Intermediate nodes: smaller circle, 60% opacity version of same color palette.
- [ ] Edge rendering: `<line>` or `<path>` elements. `strokeWidth` = `1 + edge.weight * 3` (maps 0→1 to 1→4px). Last edge (to target node) always at `strokeWidth=4`. Color: `#CBD5E1` (slate-300) for intermediate, `#64748B` (slate-500) for final.
- [ ] Semantic colors for target node fill: `audacieux=#EF4444` (red-500), `realiste=#F97316` (orange-500), `sur=#22C55E` (green-500), null=`#94A3B8` (slate-400).
- [ ] Admission label: `<text>` positioned to the right of the target node, rendering `{label} — {expected_proba}%` (e.g. "Réaliste — 62 %").
- [ ] Add type definition to `apps/web/src/lib/api/types/schools.ts`

### T2 — Animation system

- [ ] Create hook `usePrefersReducedMotion()` in `apps/web/src/hooks/usePrefersReducedMotion.ts` (if not already present — grep first: `grep -r "usePrefersReducedMotion\|prefers-reduced-motion" apps/web/src`)
- [ ] In `GraphParcours`, use `useRef` for each node and each edge element. Assign refs to corresponding SVG elements.
- [ ] On mount with `isFirstRender=true` and `!prefersReducedMotion`: sequence via `setTimeout` chain:
  - Set all nodes/edges to `opacity: 0`
  - t=0: node[0].style.opacity=1, transition `opacity 120ms ease-out`
  - t=180: edge[0].style.opacity=1 (80ms) + node[1].style.opacity=1 (180ms)
  - t=360: edge[1].style.opacity=1 + node[2].style.opacity=1 (180ms)
  - t=540: edge[last].style.opacity=1 + targetNode scale 1.1→1.0 via CSS transform (220ms, overshoot: `cubic-bezier(0.34, 1.56, 0.64, 1)`)
  - t=690: labels fade in (150ms)
  - t=200: `schoolGrid` ref (passed via callback prop `onSequenceProgress`) gets opacity 1
- [ ] On mount with `isFirstRender=true` and `prefersReducedMotion=true`: single `transition: opacity 200ms` on the root SVG `<g>`, no individual node transitions
- [ ] On mount with `isFirstRender=false`: skip sequence, target node gets a brief `scale(1.05)→scale(1)` highlight at 100ms
- [ ] `localStorage` persistence: on first render completion, write `localStorage.setItem("parcours_seen_${parcoursId}", "true")`. The parent component (`ParcoursList`) should read this key and pass `isFirstRender={!localStorage.getItem("parcours_seen_${parcoursId}")}` on subsequent renders.
- [ ] All animation is CSS-transition-based (no external animation library). Use `requestAnimationFrame` only for the overshoot target node if CSS cubic-bezier is insufficient.

### T3 — Accessible table alternative

- [ ] Inside `GraphParcours`, add state `showTable: boolean` (default `false`)
- [ ] Toggle button: `<button onClick={() => setShowTable(!showTable)}>` labelled "Vue tableau" or "Vue graphe" depending on state. Position above the SVG, always visible and focusable.
- [ ] When `showTable=true`: hide SVG (`display:none` or `aria-hidden="true"`), show:
  ```html
  <table>
    <caption>Parcours pour {metierName} — {nodes.length} étapes</caption>
    <thead>
      <tr>
        <th scope="col">Étape</th>
        <th scope="col">Formation / École</th>
        <th scope="col">Durée</th>
        <th scope="col">Type</th>
        <!-- One column per school in the grid if needed -->
      </tr>
    </thead>
    <tbody>
      {nodes.map((node, i) => (
        <tr>
          <th scope="row">{i + 1}</th>
          <td>{node.label}</td>
          <td>{node.duration_label ?? "—"}</td>
          <td>{node.type}</td>
        </tr>
      ))}
    </tbody>
  </table>
  ```
- [ ] Table styling: `w-full text-sm`, alternating row background (`even:bg-slate-50`), cell padding `px-3 py-2`, caption `text-left font-semibold mb-2`.

### T4 — Accessibility (RGAA AA)

- [ ] SVG root `<svg>`: add `role="img"` and `aria-label={"Parcours pour " + metierName + " : " + nodes.length + " étapes"}`. Add `<title>` child element with same text for broader screen reader support.
- [ ] Each node `<g>` must be wrapped in or contain a `<button>` (use `<foreignObject>` if needed, or overlay transparent `<rect tabIndex={0} role="button">` with `aria-label="{node.label} — étape {i+1} sur {total}"`). Ensure focus ring via `outline: 2px solid #3B82F6` (blue-500) on focus.
- [ ] Tab order: `tabIndex` set to natural order (0 for all, rely on DOM order — nodes in SVG must be in order in the DOM).
- [ ] The toggle button "Vue tableau" must receive focus before the SVG (place it before the `<svg>` in DOM).

### T5 — Replace `GraphParcoursPlaceholder` in `ParcoursList`

- [ ] In `apps/web/src/components/parcours/ParcoursList.tsx` (Story 4.3 T4), replace the `<GraphParcoursPlaceholder>` usage with `<GraphParcours>`.
- [ ] Pass correct props: `nodes`, `edges` from the parcours data, `targetSchool` from the last node's `school_slug`, `admissionStat` from the last node's `admission_stat` (Story 4.5 wired data), `isFirstRender` computed from `localStorage`, `metierName` from page context (add as prop to `ParcoursList`), `parcoursId={parcours.id}`.
- [ ] Keep `GraphParcoursPlaceholder` component in codebase but mark it `@deprecated` — it may still be used as fallback in tests.
- [ ] Pass `onSequenceProgress` callback: when sequence reaches t=200, trigger opacity transition on the school grid section (`ref` to the grid container).

### T6 — Tests

- [ ] `apps/web/src/components/parcours/__tests__/GraphParcours.test.tsx` (Vitest + RTL):
  - Renders correct number of node elements from `nodes` prop
  - Renders correct number of edge elements from `edges` prop
  - `admissionStat.label="realiste"` → target circle fill color is orange (check inline style or class)
  - `admissionStat=null` → target circle fill color is gray
  - Toggle "Vue tableau" → table is shown, SVG has `aria-hidden="true"`
  - Toggle "Vue graphe" → SVG visible, table hidden
  - Each node has correct `aria-label` with étape number
  - SVG has `role="img"` and `aria-label` containing `metierName`
  - `isFirstRender=false` → no setTimeout called (spy on `window.setTimeout` or check immediate full opacity)
  - `prefersReducedMotion=true` (mock `window.matchMedia`) + `isFirstRender=true` → no individual node transitions set

---

## 4. Dev Notes

- **No external graph lib**: do NOT use D3, vis.js, react-flow, or any similar library. Pure SVG + React. This is intentional for bundle size and RGAA control.
- **SVG in Next.js**: `<svg>` renders server-side fine. Animation logic in `useEffect` only (client-side). Wrap animation code in `if (typeof window !== "undefined")` guard.
- **GraphParcoursPlaceholder continuity**: Story 4.3 created `GraphParcoursPlaceholder` in `ParcoursList.tsx` with a `// TODO(story-4-9): replace with GraphParcours` comment. This story fulfills that TODO.
- **localStorage key convention**: `parcours_seen_${parcoursId}` where `parcoursId` is the UUID from the `Parcours` model. Read on client side only (`useEffect` or inside event handler).
- **AdmissionStat integration**: Story 4.5 wired `admission_stat` into parcours node data. If a node has `admission_stat`, pass it as `admissionStat` to `GraphParcours`. If multiple nodes have stats, use only the final target node's stat for the main label display.
- **usePrefersReducedMotion**: before creating, grep `apps/web/src/hooks/` for any existing reduced-motion hook. Story 2.8 (`ScenarioLoader`) may have introduced one.
- **CSS overshoot**: use `cubic-bezier(0.34, 1.56, 0.64, 1)` for the target node scale overshoot — this is a "back-ease" curve that produces a natural spring effect without a JS animation library.
- **Responsive SVG**: use `viewBox="0 0 400 220"` with `width="100%"` and `height="auto"`. This makes the graph fill its container width and scale proportionally on mobile.
- Reference files: `apps/web/src/components/parcours/ParcoursList.tsx` (Story 4.3), `apps/web/src/components/features/professions/FicheMetier.tsx` (component structure pattern).
- All frontend tests: Vitest + RTL, `__tests__/` co-located.

---

## 5. Dev Agent Record

### Agent Model Used
_À remplir_

### Completion Notes List
_À remplir_

### File List
_À remplir_

### Change Log
- 2026-06-21 — Story 4.9 créée.
