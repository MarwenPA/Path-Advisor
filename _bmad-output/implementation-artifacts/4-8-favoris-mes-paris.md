# Story 4.8: Favoris écoles cibles + "Mes paris"

**Epic:** 4 — Graphe de Parcours & Stats d'Admission (Deuxième Aha)
**Status:** ready-for-dev
**Sprint:** 7 (Graphe parcours)
**Story Key:** `4-8-favoris-mes-paris`
**Estimation:** M

---

## 1. User Story

**As a** student who has identified target schools in their pathway
**I want** to save schools as favorites ("mes paris") and view them grouped by target profession
**So that** I can track my target schools in one place, compare options, and make strategic application choices

---

## 2. Acceptance Criteria (BDD)

### AC1 — Add school to favorites from FicheEcole or graph node

**Given** an authenticated student viewing a school detail page (`/schools/{slug}`) or a graph node in `ParcoursList`
**When** the student taps the heart/bookmark "Ajouter à mes paris" icon button
**Then** the school is saved immediately as a favorite
**And** a toast confirmation "École ajoutée à tes paris" is shown
**And** the icon toggles to filled/active state

### AC2 — Page "Mes paris" shows grouped school cards

**Given** an authenticated student with at least one saved favorite
**When** navigating to `/mes-paris`
**Then** all favorited schools are listed, grouped by the `metier` they were bookmarked under
**And** each school is rendered as a `ParcoursCard` (Story 4.12 placeholder used until 4.12 ships — use `FicheEcole variant="card"` as interim)
**And** a "Comparer 2 écoles" button is visible allowing side-by-side comparison via `SchoolCompare` (Story 4.10)
**And** a remove button is visible on each school card

### AC3 — Empty state on /mes-paris

**Given** an authenticated student with no saved favorites
**When** navigating to `/mes-paris`
**Then** the empty state message reads: "Tu n'as pas encore exploré tes premiers paris. Va voir tes métiers recommandés et clique sur 'Voir le parcours'."
**And** a CTA button "Voir mes métiers" links to `/mes-metiers`

### AC4 — Remove favorite with toast

**Given** an authenticated student viewing `/mes-paris`
**When** the student taps the remove button on a school card
**Then** the school is removed immediately from the list (optimistic UI)
**And** a toast "École retirée" is shown
**And** no confirmation dialog is shown (action is reversible by re-adding)
**And** if the métier group becomes empty after removal, the group heading disappears

---

## 3. Tasks / Subtasks

### T1 — Model `FavoriteSchool` in `apps/api/apps/schools/`

- [ ] Add `FavoriteSchool` model to `apps/api/apps/schools/models.py`:
  - `id` (UUIDField, primary_key, default=uuid4)
  - `student` (FK `students.StudentProfile`, on_delete=CASCADE, related_name=`favorite_schools`)
  - `school` (FK `School`, on_delete=CASCADE, related_name=`favorited_by`)
  - `metier` (FK `professions.Profession`, on_delete=SET_NULL, null=True, blank=True, related_name=`favorited_school_set`) — the métier context under which the school was bookmarked
  - `added_at` (DateTimeField, auto_now_add=True)
  - `UniqueConstraint(fields=["student", "school"], name="unique_favorite_per_student_school")`
- [ ] Register in `admin.py`
- [ ] Create migration `0XXX_add_favoriteschool.py`

### T2 — Endpoints: POST/DELETE favorite + `is_favorited` in SchoolDetailSerializer

- [ ] Create `FavoriteSchoolView` in `apps/api/apps/schools/views.py`:
  - `POST /api/v1/schools/{slug}/favorite/` — resolve school by slug, get or create `FavoriteSchool(student=request.user.student_profile, school=school)`. Accept optional `metier_slug` in request body. Return 201 if created, 200 if already present. Permission: `IsAuthenticated`.
  - `DELETE /api/v1/schools/{slug}/favorite/` — delete the `FavoriteSchool` row if it exists, return 204. Silently ignore if not found (204 anyway).
- [ ] Add `is_favorited` boolean field to `SchoolDetailSerializer` in `apps/api/apps/schools/serializers.py`: `SerializerMethodField` that checks `FavoriteSchool.objects.filter(student=request.user.student_profile, school=obj).exists()` — handle unauthenticated gracefully (return `False`).
- [ ] Wire URLs in `apps/api/apps/schools/urls.py`:
  - `POST   api/v1/schools/<slug:slug>/favorite/`
  - `DELETE api/v1/schools/<slug:slug>/favorite/`

### T3 — Endpoint GET /api/v1/students/me/favorites/ — grouped by métier

- [ ] Create `StudentFavoritesView` (ListAPIView, `IsAuthenticated`) in `apps/api/apps/students/views.py` (or students app equivalently):
  - Fetch `FavoriteSchool.objects.filter(student=request.user.student_profile).select_related("school", "metier").order_by("metier__name", "added_at")`
  - Group in Python by `metier`: build list `[{metier: {id, name, slug} | null, schools: [SchoolDetailSerializer data]}]`
  - Métier `null` group for favorites bookmarked without a métier context — label it `"Sans métier"` on front-end
- [ ] Wire URL: `GET /api/v1/students/me/favorites/`
- [ ] Response shape:
  ```json
  [
    {
      "metier": {"id": "uuid", "name": "Infirmier", "slug": "infirmier"},
      "schools": [/* SchoolDetail objects with is_favorited: true */]
    }
  ]
  ```

### T4 — Next.js page `/mes-paris/page.tsx` + navigation entry

- [ ] Create `apps/web/src/app/(authenticated)/mes-paris/page.tsx` as a server component:
  - Fetch `GET /api/v1/students/me/favorites/` using `apiClient`
  - Pass grouped data to `<MesParisClient groups={data} />`
  - Page title: "Mes paris — Path-Advisor"
  - Suspense boundary with skeleton
- [ ] Add "Mes paris" navigation entry in `apps/web/src/app/(authenticated)/layout.tsx` (sidebar/bottom nav — follow existing nav item pattern, use bookmark/heart icon from existing icon set)

### T5 — Component `MesParisClient`

- [ ] Create `apps/web/src/components/schools/MesParisClient.tsx` (client component, `"use client"`):
  - Props: `groups: FavoriteGroup[]` where `FavoriteGroup = { metier: {id: string, name: string, slug: string} | null, schools: SchoolDetail[] }`
  - Renders each group as a section: `<h2>{metier.name}</h2>` heading + school cards grid
  - School cards: use `<FicheEcole variant="card" school={school} admissionStat={school.admission_stat ?? null} />` — add `// TODO(story-4-12): replace with <ParcoursCard>` comment
  - Remove button on each card: calls `DELETE /api/v1/schools/{slug}/favorite/` via `apiClient`, optimistic removal from local state, shows toast "École retirée" via existing toaster
  - Compare mode: "Comparer" checkbox on each card, max 2 selectable. When 2 selected, show `<SchoolCompare school1={...} school2={...} />` (Story 4.10) in a modal/drawer below the grid. Disable further selection when 2 are already selected.
  - Empty state (when `groups.length === 0`): render the empty state message and CTA per AC3
  - Group cleanup: remove group heading when its school list becomes empty after removal
- [ ] Add TypeScript type `FavoriteGroup` to `apps/web/src/lib/api/types/schools.ts`

### T6 — Favorite button in `FicheEcole`

- [ ] Update `apps/web/src/components/schools/FicheEcole.tsx` (Story 4.4):
  - Accept new optional props: `isFavorited?: boolean`, `onFavoriteToggle?: (slug: string, newState: boolean) => void`
  - Render a heart icon button in the header (top-right corner): filled heart if `isFavorited=true`, outline heart otherwise
  - On click: call `POST` or `DELETE` `/api/v1/schools/{slug}/favorite/` via `apiClient`, toggle local `isFavorited` state optimistically, show toast "École ajoutée à tes paris" or "École retirée" via existing toaster
  - Accept optional `metierSlug?: string` prop to send in the POST body for correct grouping
  - Touch target: button must be at least 44×44px (Tailwind `p-3` or `min-w-[44px] min-h-[44px]`)
  - `aria-label`: "Ajouter à mes paris" / "Retirer de mes paris" depending on state
  - If `onFavoriteToggle` is provided, call it after successful API toggle (for `MesParisClient` optimistic sync)

### T7 — Tests

- [ ] `apps/api/apps/schools/tests/test_favorite_school.py` (`@pytest.mark.django_db @pytest.mark.postgresql_only`):
  - POST favorite → 201, `FavoriteSchool` row created, `is_favorited=True` in school detail
  - POST favorite duplicate → 200 (no duplicate row created), count still 1
  - DELETE favorite → 204, row deleted
  - DELETE non-existent favorite → 204 (silent)
  - GET `/students/me/favorites/` → returns correct grouping, `metier` field populated
  - GET `/students/me/favorites/` with multiple métiers → returns multiple groups in correct order
  - Unauthenticated POST favorite → 401
- [ ] `apps/web/src/components/schools/__tests__/MesParisClient.test.tsx` (Vitest + RTL):
  - Renders groups with headings and school cards
  - Remove button triggers DELETE and removes card from DOM (mock fetch)
  - Compare mode: selecting 2 schools shows `SchoolCompare`; 3rd checkbox disabled
  - Empty state renders when `groups=[]`
- [ ] `apps/web/src/components/schools/__tests__/FicheEcole.test.tsx` (extend existing):
  - Renders heart button with `aria-label="Ajouter à mes paris"` when `isFavorited=false`
  - Heart toggles to filled and shows toast on click (mock fetch 201)

---

## 4. Dev Notes

- **Existing toaster**: look for `useToast` or similar in `apps/web/src/components/` — follow the same pattern used in `FicheMetier.tsx` or auth flows. Do NOT introduce a new toast library.
- **apiClient pattern**: all fetch calls must go through `apps/web/src/lib/api/client.ts`. Never use raw `fetch` in components.
- **StudentProfile access**: on backend, get profile via `request.user.student_profile` — this pattern is established in Story 4.2 (`AdmissionPredictionService`) and Story 4.5. If `student_profile` does not exist, return 403 or handle gracefully.
- **SchoolDetailSerializer context**: `is_favorited` requires `request` in serializer context. Ensure `SchoolDetailView` passes `context={"request": request}` to serializer (it should already for DRF).
- **Optimistic UI**: `MesParisClient` should remove the card immediately on remove-button click, then fire the DELETE. If DELETE fails (network error), re-add the card and show error toast. This prevents perceived latency.
- **ParcoursCard placeholder**: Story 4.12 will introduce `ParcoursCard`. Until merged, use `FicheEcole variant="card"`. Add `// TODO(story-4-12): replace with <ParcoursCard>` comment in `MesParisClient`.
- **SchoolCompare**: Story 4.10 introduces `SchoolCompare`. If 4.10 is not yet merged, render a simple two-column layout directly in `MesParisClient` as temporary — add `// TODO(story-4-10): replace with <SchoolCompare>` comment.
- **Navigation icon**: use a bookmark or heart SVG from the existing Heroicons or Lucide set already present in the project (grep `apps/web/src` for existing icon imports before adding new ones).
- Reference files: `apps/web/src/components/schools/FicheEcole.tsx` (Story 4.4), `apps/api/apps/schools/models.py`, `apps/api/apps/students/views.py`.
- All backend tests: `@pytest.mark.django_db @pytest.mark.postgresql_only`.

---

## 5. Dev Agent Record

### Agent Model Used
_À remplir_

### Completion Notes List
_À remplir_

### File List
_À remplir_

### Change Log
- 2026-06-21 — Story 4.8 créée.
