# Story 4.3: Affichage graphe de parcours par métier

**Epic:** 4 — Graphe de Parcours & Stats d'Admission (Deuxième Aha)
**Status:** ready-for-dev
**Sprint:** 7 (Graphe parcours)
**Story Key:** `4-3-graphe-parcours-par-metier`
**Estimation:** M

---

## 1. User Story

**As a** student exploring a profession on Path-Advisor
**I want** to see a visual pathway (parcours) from my current school level to that profession
**So that** I understand the concrete steps and schools I need to go through

---

## 2. Acceptance Criteria (BDD)

### AC1 — Default parcours shown

**Given** a profession slug with seeded parcours data
**When** I navigate to `/metiers/{slug}/parcours`
**Then** the default parcours (`is_default=True`) is displayed first
**And** nodes are listed in order

### AC2 — Alternative paths button

**Given** a profession with 3 seeded parcours
**When** the page loads
**Then** a button "Voir d'autres chemins (2)" is visible
**And** clicking it reveals the 2 alternative parcours

### AC3 — School grid under graph

**Given** nodes with `school_id` references
**When** the parcours renders
**Then** a grid of school cards appears below the graph placeholder
**And** each card links to `/schools/{slug}`

### AC4 — Placeholder when GraphParcours not available

**Given** Story 4.9 is not yet merged
**When** `ParcoursList` renders
**Then** a `GraphParcoursPlaceholder` component is rendered showing nodes as a vertical list
**And** no JS error is thrown

### AC5 — Level selection

**Given** a student at `niveau=terminale`
**When** the API returns parcours for that métier
**Then** the parcours matching `niveau_scolaire=terminale` appears first (or `is_default=True` wins if same level)

### AC6 — Empty state

**Given** a profession with no seeded parcours
**When** I navigate to `/metiers/{slug}/parcours`
**Then** a friendly empty state message is shown: "Aucun parcours disponible pour ce métier pour l'instant."

### AC7 — Unauthenticated redirect

**Given** an unauthenticated user
**When** navigating to `/metiers/{slug}/parcours`
**Then** they are redirected to `/login`

---

## 3. Tasks / Subtasks

### T1 — Parcours model + seed data

- [ ] Create `Parcours` model in `apps/api/apps/schools/models.py`: `id` (UUIDField pk), `metier` (FK professions.Profession, on_delete=CASCADE, related_name=parcours), `niveau_scolaire` (CharField choices: troisieme, premiere, terminale), `nodes` (JSONField, list of `{id: str, label: str, type: "diplome"|"ecole"|"stage"|"concours", school_slug: str|null, duration_label: str|null}`), `edges` (JSONField, list of `{source: str, target: str, weight: float 0-1}`), `is_default` (BooleanField default False), `created_at`
- [ ] Add constraint: only one `is_default=True` per `(metier, niveau_scolaire)` pair
- [ ] Create migration
- [ ] Create `apps/api/apps/schools/fixtures/parcours_seed.json` with 10+ parcours covering 5 professions: infirmier (terminale: bac→IFSI→diplôme état), technicien aéronautique (terminale: bac pro avionique→BTS aéronautique→emploi; troisieme: 3ème→lycée pro avionique→BTS), développeur (terminale: bac général→BUT informatique→alternance), cuisinier (terminale: bac pro cuisine→BTS management hôtellerie, troisieme: CAP cuisine→bac pro), commercial (terminale: BTS NDRC→licence pro)
- [ ] Create management command `seed_parcours` (idempotent, runs after `seed_schools`)

### T2 — GET /api/v1/metiers/{slug}/parcours/ endpoint

- [ ] Create `ParcoursSerializer`: all Parcours fields + nested school data for nodes with `school_slug` (fetch School name+city for display)
- [ ] Create `ParcoursByMetierView` (ListAPIView, permission_classes=[IsAuthenticated]): filter `Parcours` by `metier__slug`, order by `is_default DESC` then `niveau_scolaire`
- [ ] Wire url under professions router or schools router: `GET /api/v1/metiers/{slug}/parcours/`
- [ ] Return 404 if metier slug not found

### T3 — Next.js page /metiers/[slug]/parcours/page.tsx

- [ ] Create `apps/web/src/app/(authenticated)/metiers/[slug]/parcours/page.tsx` as a server component
- [ ] Fetch parcours list from API using existing `apiClient` pattern (see `apps/web/src/lib/api/client.ts`)
- [ ] Pass data as props to `ParcoursList` client component
- [ ] Handle loading state with Suspense boundary
- [ ] Add page title: "{Profession name} — Parcours"
- [ ] Handle 404 from API → Next.js `notFound()`

### T4 — ParcoursList client component

- [ ] Create `apps/web/src/components/parcours/ParcoursList.tsx`
- [ ] Props: `parcours: Parcours[]`, `defaultIndex: number` (index of `is_default`)
- [ ] Show default parcours expanded; render `<GraphParcoursPlaceholder nodes={parcours[defaultIndex].nodes} />` as placeholder until Story 4.9
- [ ] Create `GraphParcoursPlaceholder` in same file or `GraphParcoursPlaceholder.tsx`: renders nodes as vertical ordered list with type badge (diplôme/école/stage/concours), connected by arrows (CSS border-left dashed line)
- [ ] Below placeholder, render school grid: for each node with `school_slug`, render a card linking to `/schools/{school_slug}`
- [ ] "Voir d'autres chemins (N)" button: N = `parcours.length - 1`, hidden if N=0, toggles visibility of alternative parcours list
- [ ] Empty state: if `parcours.length === 0`, render `<p>Aucun parcours disponible pour ce métier pour l'instant.</p>`
- [ ] Tailwind styling consistent with existing `FicheMetier` component

### T5 — Vitest tests

- [ ] `__tests__/ParcoursList.test.tsx`: render with 3 parcours → default shown, button "Voir d'autres chemins (2)" present, click → alternatives visible
- [ ] `__tests__/ParcoursList.test.tsx`: render with 0 parcours → empty state message visible
- [ ] `__tests__/GraphParcoursPlaceholder.test.tsx`: renders all nodes in order, no JS errors
- [ ] `__tests__/ParcoursList.test.tsx`: school grid renders cards with `href=/schools/{slug}`

---

## 4. Dev Notes

- Follow `apps/web/src/components/professions/FicheMetier.tsx` for component structure and Tailwind patterns
- Server component data fetching pattern: see existing `(authenticated)/layout.tsx` and any existing metier pages
- `GraphParcoursPlaceholder` is a TEMPORARY component — mark with `// TODO(story-4-9): replace with GraphParcours` comment
- The `is_default` constraint must be enforced at DB level: use `UniqueConstraint` with condition `Q(is_default=True)` (PostgreSQL partial unique index)
- `niveau_scolaire` ordering in API: terminale first (most common), then premiere, troisieme — use `Case/When` or explicit ordering
- `@pytest.mark.django_db @pytest.mark.postgresql_only` required on all backend tests
- UX-DR25: placeholder and real graph must be visually indistinguishable in terms of information density

---

## 5. Dev Agent Record

### Agent Model Used
_À remplir_

### Completion Notes List
_À remplir_

### File List
_À remplir_

### Change Log
- 2026-06-21 — Story 4.3 créée.
