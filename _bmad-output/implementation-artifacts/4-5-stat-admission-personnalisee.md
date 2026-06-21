# Story 4.5: Statistique d'admission personnalisée par école

**Epic:** 4 — Graphe de Parcours & Stats d'Admission (Deuxième Aha)
**Status:** ready-for-dev
**Sprint:** 7 (Graphe parcours)
**Story Key:** `4-5-stat-admission-personnalisee`
**Estimation:** M

---

## 1. User Story

**As a** student consulting a school detail page or the pathway graph
**I want** to see my personalized admission probability with its qualitative label, contextual line, and action lever
**So that** I can make strategic Parcoursup choices knowing my real chances

---

## 2. Acceptance Criteria (BDD)

### AC1 — FicheEcole shows full admission stat block

**Given** an authenticated student with a complete profile consulting a school detail page
**When** `GET /api/v1/schools/{slug}/` is called (optionally with `?formation_id=`)
**Then** the response includes an `admission_stat` object with: `label` (audacieux/realiste/sur), `context_line` (e.g. "moyenne admise dernière promo : 14,5"), `action_lever` (e.g. "+ 2 pts en maths → 58 %"), `min_proba`, `expected_proba`, `max_proba`
**And** the `FicheEcole` component renders a structured stat block replacing the plain text fallback (Story 4.4 AC4)
**And** the label badge, context line and action lever are all visible

### AC2 — Inline stat in parcours graph node

**Given** an authenticated student consulting a pathway view
**When** `GET /api/v1/metiers/{slug}/parcours/` is called
**Then** each node of type `"ecole"` with a `school_slug` includes an `admission_stat` object
**And** the `ParcoursList` component displays the `label` and `expected_proba` inline under the school name in the node card

### AC3 — Incomplete profile (Léa) — indicative label

**Given** a student with `has_bulletins=False`
**When** the admission stat is displayed in `FicheEcole` or in the graph node
**Then** the label reads "estimation indicative — affine avec ton profil" (verbatim from `context_line` suffix)
**And** the visual structure is strictly identical to a complete profile (UX-DR25: normal mode = degraded mode)
**And** no drama or stigmatising message is shown

### AC4 — Recently updated stat badge

**Given** an `AdmissionStat` row whose `updated_at` is within the last 24 hours
**When** `CarteAdmission` (placeholder in this story) renders the stat
**Then** a badge "+ N pts" is visible (where N = delta relative to previous expected_proba if available, or a hardcoded positive delta from seed)
**And** the badge fades in with a 200 ms opacity animation

### AC5 — No admission stat available — graceful degradation

**Given** a school with no `AdmissionStat` row
**When** the detail page loads
**Then** the `FicheEcole` admission section renders "Données d'admission non disponibles"
**And** no error is thrown
**And** the rest of the school detail is fully visible

---

## 3. Tasks / Subtasks

### T1 — Wire AdmissionPredictionService into GET /api/v1/schools/{slug}/

- [ ] In `apps/api/apps/schools/serializers.py`, extend `SchoolDetailSerializer` with a `SerializerMethodField admission_stat`
- [ ] In `get_admission_stat(self, obj)`: read `self.context.get("request")`, if authenticated → fetch student profile (`request.user.student_profile` or `request.user.profile` — check existing pattern), call `AdmissionPredictionService.predict(student_profile_dict, school_slug=obj.slug, formation_id=context.get("formation_id"))`, return dict or `None`
- [ ] Wrap entire call in `try/except Exception` → log and return `None` (defensive — service may not exist yet)
- [ ] In `SchoolDetailView.get_serializer_context()`: inject `formation_id` from `request.query_params.get("formation_id")` and `request`
- [ ] Confirm existing `GET /api/v1/schools/{slug}/` already accepts `?formation_id=` (Story 4.4 T1) — add if missing

### T2 — Wire admission_stat into GET /api/v1/metiers/{slug}/parcours/

- [ ] In `apps/api/apps/schools/serializers.py`, create `NodeWithAdmissionSerializer` or enrich `ParcoursSerializer` node rendering
- [ ] For each node in `parcours.nodes` where `type == "ecole"` and `school_slug` is not null: call `AdmissionPredictionService.predict()` with student profile + `school_slug`; attach result as `admission_stat` key on the node dict
- [ ] In `ParcoursByMetierView` (Story 4.3), pass `request` in serializer context so the enrichment can access the logged-in student
- [ ] No N+1: batch-fetch `AdmissionStat` rows for all school_slugs in the parcours nodes before iterating (use `School.objects.filter(slug__in=[...]).prefetch_related(...)`)
- [ ] Fallback: if service raises or school not found, set `admission_stat: null` for that node

### T3 — Integrate stat block in FicheEcole component (Story 4.4)

- [ ] In `apps/web/src/components/schools/FicheEcole.tsx`, replace the plain text admission fallback (`// TODO(story-4-11): replace with <CarteAdmission>`) with a structured interim block named `<CarteAdmissionPlaceholder>`
- [ ] Create `apps/web/src/components/schools/CarteAdmissionPlaceholder.tsx` with props: `admissionStat: AdmissionPrediction | null`
- [ ] When `admissionStat` is non-null: render `expected_proba` as large number (text-4xl font-bold), label badge (color-coded: audacieux=amber, realiste=blue, sur=green), `context_line` as small gray text, `action_lever` as italic text
- [ ] When `admissionStat` has `expected_proba === null` (anti-humiliation guard): render only `context_line` ("Pari très audacieux") without any number
- [ ] When `admissionStat` is `null`: render `<p>Données d'admission non disponibles</p>`
- [ ] Badge "+ N pts": add `delta_pts` optional field to `AdmissionPrediction` type; if `delta_pts` present and `updated_recently=true`, render badge with CSS `animate-fade-in` (200 ms)
- [ ] Keep `// TODO(story-4-11): replace with <CarteAdmission variant="medium">` comment at top of component
- [ ] Update `AdmissionPrediction` type in `apps/web/src/lib/api/types/schools.ts`: add `delta_pts?: number | null`, `updated_recently?: boolean`

### T4 — Integrate stat inline in ParcoursList node card

- [ ] In `apps/web/src/components/parcours/ParcoursList.tsx` (Story 4.3), update `GraphParcoursPlaceholder` node rendering for nodes of type `"ecole"`:
- [ ] If `node.admission_stat` present: render below school name a row with label badge + `expected_proba`% (e.g. "38 % · audacieux")
- [ ] If `node.admission_stat === null`: render nothing (UX-DR25)
- [ ] Update `ParcoursNode` TypeScript type (in `apps/web/src/lib/api/types/schools.ts` or inline): add `admission_stat?: AdmissionPrediction | null`
- [ ] Tailwind: use `text-sm text-gray-600` for inline stat, badge color consistent with CarteAdmissionPlaceholder

### T5 — Tests

- [ ] `apps/api/apps/schools/tests/test_school_detail_admission.py`: `@pytest.mark.django_db @pytest.mark.postgresql_only` — GET `/schools/{slug}/` authenticated → response has `admission_stat.label` in ["audacieux","realiste","sur"]; student with `has_bulletins=False` → `context_line` contains "indicative"; no AdmissionStat row → `admission_stat` is null
- [ ] `apps/api/apps/schools/tests/test_parcours_admission.py`: `@pytest.mark.django_db @pytest.mark.postgresql_only` — GET `/metiers/{slug}/parcours/` → each ecole node has `admission_stat` key; batched query (use `django.test.utils.CaptureQueriesContext` to assert query count ≤ 5)
- [ ] `apps/web/src/components/schools/__tests__/CarteAdmissionPlaceholder.test.tsx`: render with full stat → proba number, label badge, context_line, action_lever visible; render with null → fallback text; render with `expected_proba=null` (anti-humiliation) → no number visible, context_line "Pari très audacieux" shown
- [ ] `apps/web/src/components/schools/__tests__/FicheEcole.test.tsx` (extend Story 4.4 tests): FicheEcole with stat → CarteAdmissionPlaceholder renders, label badge visible; FicheEcole with null stat → "Données d'admission non disponibles"

---

## 4. Dev Notes

- `AdmissionPredictionService` is in `apps/api/apps/schools/services/prediction_service.py` (Story 4.2). Import defensively: `try: from apps.schools.services.prediction_service import AdmissionPredictionService; except ImportError: AdmissionPredictionService = None`
- Student profile access pattern: check `apps/api/apps/students/models.py` for the FK from `User` to `StudentProfile`. Likely `request.user.student_profile`. Build `student_profile_dict` as `{"has_bulletins": profile.has_bulletins}` (Story 4.2 requires this key).
- UX-DR25 compliance: `CarteAdmissionPlaceholder` must render the same DOM skeleton whether profile is complete or not — only text content changes.
- Anti-humiliation guard (Story 4.2): when `expected_proba` is `null` in the returned dict, **never** render a number. Render only `context_line`.
- `ParcoursNode` JSON nodes are stored as `JSONField` in `Parcours.nodes` — the serializer already returns them as-is. Enrichment happens in the view/serializer layer, not at model level.
- No N+1 for parcours nodes: use `AdmissionStat.objects.filter(school__slug__in=school_slugs).select_related("school")` to batch-load stats.
- `delta_pts` / `updated_recently` for badge: compute in serializer using `AdmissionStat.updated_at > timezone.now() - timedelta(hours=24)`. `delta_pts` can be a hardcoded +5 in MVP if no previous stat snapshot exists.
- Reference components: `apps/web/src/components/professions/SignauxDrawer.tsx` (pattern for conditional rendering + Tailwind color tokens).
- All backend test files: `@pytest.mark.django_db @pytest.mark.postgresql_only`.

---

## 5. Dev Agent Record

### Agent Model Used
_À remplir_

### Completion Notes List
_À remplir_

### File List
_À remplir_

### Change Log
- 2026-06-21 — Story 4.5 créée.
