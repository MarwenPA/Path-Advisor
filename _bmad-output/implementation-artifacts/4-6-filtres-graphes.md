# Story 4.6: Filtres graphes (proximité, coût, sélectivité, alternance)

**Epic:** 4 — Graphe de Parcours & Stats d'Admission (Deuxième Aha)
**Status:** ready-for-dev
**Sprint:** 7 (Graphe parcours)
**Story Key:** `4-6-filtres-graphes`
**Estimation:** M

---

## 1. User Story

**As a** student browsing a profession's pathway view
**I want** to filter the school grid by proximity, cost, selectivity, and apprenticeship/internship availability
**So that** the recommendations match my personal constraints (geography, budget, level)

---

## 2. Acceptance Criteria (BDD)

### AC1 — Filter bar visible on pathway view

**Given** an authenticated student on `/metiers/{slug}/parcours`
**When** the page renders
**Then** a persistent filter bar is visible above the school grid
**And** it contains pill groups: Proximité (≤ 50 km / ≤ 200 km / France entière), Coût (gratuit / < 5 000 €/an / < 10 000 €/an / sans limite), Sélectivité (très accessible [5] / accessible [4] / sélectif [2–3] / très sélectif [1]), Mode (alternance / internat)
**And** the bar includes an "Effacer tout" button always visible

### AC2 — Filters update school grid without page reload

**Given** the student selects "≤ 50 km" and "alternance"
**When** filters are applied
**Then** the school grid updates in < 1 s without a full page reload
**And** a counter reads "N école(s) cible(s) correspondent à tes filtres"
**And** "Effacer tout" is still visible

### AC3 — Empty state when no schools match

**Given** a very restrictive filter combination (e.g. gratuit + ≤ 50 km + très sélectif)
**When** the resulting school list is empty
**Then** an empty state message shows: "Aucune école ne correspond. Élargis tes critères, vois aussi les écoles privées ?"
**And** a CTA button reads "Relâcher un filtre" and removes the most restrictive active filter

### AC4 — Accessibility (UX-DR32)

**Given** a screen reader user navigating the filter bar
**When** they interact with a filter pill
**Then** the pill has `role="checkbox"` and `aria-checked="true|false"`
**And** the filter group has `role="group"` with `aria-label` describing the filter category
**And** after filtering, the results count is announced via `aria-live="polite"` region

### AC5 — "France entière" is the default (no filter active)

**Given** no filters are selected
**When** the page first loads
**Then** all schools are shown with no proximity restriction
**And** the counter reads the total number of matching schools

---

## 3. Tasks / Subtasks

### T1 — Extend GET /api/v1/metiers/{slug}/parcours/ with server-side filter query params

- [ ] In `apps/api/apps/schools/views.py`, update `ParcoursByMetierView` to read optional query params: `proximity_km` (int, choices: 50, 200, null=no limit), `max_cost` (int, choices: 0, 5000, 10000, null=no limit), `selectivity_max` (int 1–5, null=all), `apprenticeship` (bool string "true"/"false"), `internship` (bool string "true"/"false")
- [ ] Create `ParcoursFilterSerializer` (DRF Serializer, not model-based) to validate these query params cleanly
- [ ] In view: after fetching parcours nodes with school_slugs, apply filter to the set of `School` objects. Build `school_filter_qs = School.objects.filter(slug__in=all_node_school_slugs)`, then chain filters:
  - `proximity_km=50`: filter `schools` within 50 km of `request.user.student_profile.commune_lat/lon` (use `geopy.distance.distance` or simple bounding box if geopy not available — see Dev Notes)
  - `max_cost=0`: filter `tuition_min_eur=0 OR tuition_min_eur__isnull=True`
  - `max_cost=5000`: filter `tuition_min_eur__lte=5000`
  - `max_cost=10000`: filter `tuition_min_eur__lte=10000`
  - `selectivity_max`: filter `selectivity_index__lte=selectivity_max` (remember: lower index = more selective, so selectivity_max=4 means "accessible + non-selective")
  - `apprenticeship=true`: filter `apprenticeship=True`
  - `internship=true`: filter `internship=True`
- [ ] Return filtered `school_slugs_set`; annotate each `school_slug` node as `filtered_out=True` if not in set (so front-end can hide them without re-fetching)
- [ ] Add `total_schools_matching` count to the response envelope (top-level key alongside `parcours` list)

### T2 — ParcoursFilters component

- [ ] Create `apps/web/src/components/parcours/ParcoursFilters.tsx`
- [ ] Props: `onFiltersChange: (filters: ParcoursFilters) => void`, `totalMatching: number`
- [ ] TypeScript type `ParcoursFilters`: `{ proximity_km: 50 | 200 | null; max_cost: 0 | 5000 | 10000 | null; selectivity_max: 1 | 2 | 3 | 4 | 5 | null; apprenticeship: boolean; internship: boolean }`
- [ ] State: local `useState<ParcoursFilters>` initialized with all nulls/false
- [ ] Pill groups rendered as `<fieldset role="group" aria-label="Proximité">` etc. Each pill is `<button role="checkbox" aria-checked={active}>` with Tailwind `bg-blue-600 text-white` when active, `bg-gray-100 text-gray-700` when inactive
- [ ] Counter: `<p aria-live="polite">{totalMatching} école(s) cible(s) correspondent à tes filtres</p>`
- [ ] "Effacer tout" button: always visible, resets state to all nulls/false, calls `onFiltersChange` with empty filters
- [ ] Each pill click: toggle single-select within its group (Proximité and Coût and Sélectivité are single-select; Mode pills are independent checkboxes)
- [ ] On any state change: call `onFiltersChange(currentFilters)` via `useEffect` or directly in handler

### T3 — Integrate ParcoursFilters into ParcoursList (Story 4.3)

- [ ] In `apps/web/src/components/parcours/ParcoursList.tsx`, import and render `<ParcoursFilters onFiltersChange={handleFiltersChange} totalMatching={filteredCount} />` above the school grid
- [ ] Implement `handleFiltersChange`: build query string from filters, re-fetch `GET /api/v1/metiers/{slug}/parcours/?{filters}` using `useCallback` + `useState` for loading state
- [ ] On response: update school nodes displayed (filter out nodes where `filtered_out=true`), update `filteredCount` from `total_schools_matching`
- [ ] Empty state: when `filteredCount === 0`, render empty state component: `<ParcoursEmptyState onRelaxFilter={handleRelaxMostRestrictiveFilter} />`
- [ ] `ParcoursEmptyState` component (can be in same file): renders message "Aucune école ne correspond. Élargis tes critères, vois aussi les écoles privées ?" + CTA button "Relâcher un filtre" that calls `onRelaxFilter`
- [ ] `handleRelaxMostRestrictiveFilter`: remove the most restrictive active filter (priority: selectivity_max first, then proximity_km, then max_cost, then apprenticeship/internship)
- [ ] Loading state during re-fetch: show a skeleton overlay on the school grid (opacity-50 + spinner), not a full page reload

### T4 — Vitest tests

- [ ] `apps/web/src/components/parcours/__tests__/ParcoursFilters.test.tsx`:
  - Render → all pill groups visible (Proximité, Coût, Sélectivité, Mode)
  - Click "≤ 50 km" pill → `onFiltersChange` called with `proximity_km=50`, pill has `aria-checked="true"`
  - Click same pill again (toggle off) → `onFiltersChange` called with `proximity_km=null`
  - Click "Effacer tout" → `onFiltersChange` called with all-null filters, all pills `aria-checked="false"`
  - Counter text reads `"{totalMatching} école(s) cible(s)"`
  - `aria-live` region present
- [ ] `apps/web/src/components/parcours/__tests__/ParcoursList.test.tsx` (extend):
  - Render with `filteredCount=0` → empty state message visible
  - "Relâcher un filtre" button present in empty state → click → `onFiltersChange` called with relaxed filters

---

## 4. Dev Notes

- **Proximity calculation**: check if `geopy` is already in `apps/api/requirements.txt`. If not, implement a bounding-box approximation: `lat ± (km/111)` and `lon ± (km / (111 * cos(lat)))`. Store student's lat/lon from `StudentProfile.commune_lat` / `commune_lon` (check existing model in `apps/api/apps/students/models.py`). If fields absent, proximity filter is a no-op (graceful degradation).
- **Selectivity direction**: `selectivity_index=1` = très sélectif (grande école), `5` = très accessible. User-facing labels: "très sélectif" → `selectivity_max=2` (index ≤ 2), "sélectif" → `selectivity_max=3`, "accessible" → `selectivity_max=4`, "très accessible" → `selectivity_max=5`.
- **Single-select vs multi-select**: Proximité, Coût, Sélectivité are single-select (one value at a time). Mode (alternance, internat) are independent boolean toggles — both can be active simultaneously.
- **No client-side filtering**: always re-fetch from API on filter change. This ensures server-side proximity logic is applied and count is accurate. Debounce re-fetch by 300 ms to avoid rapid requests.
- **`filtered_out` node annotation**: the API returns all parcours nodes but marks school nodes not matching filters with `filtered_out: true`. The front-end simply hides them. This avoids restructuring the parcours graph.
- Follow `apps/web/src/components/professions/SignauxDrawer.tsx` for pill/chip component patterns and Tailwind color tokens.
- `@pytest.mark.django_db @pytest.mark.postgresql_only` on all backend tests.
- The `total_schools_matching` response key is added at the serializer level (annotate `ParcoursByMetierView` response as `{"parcours": [...], "total_schools_matching": N}`).

---

## 5. Dev Agent Record

### Agent Model Used
_À remplir_

### Completion Notes List
_À remplir_

### File List
_À remplir_

### Change Log
- 2026-06-21 — Story 4.6 créée.
