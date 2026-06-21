# Story 4.4: Fiche école/formation détaillée

**Epic:** 4 — Graphe de Parcours & Stats d'Admission (Deuxième Aha)
**Status:** ready-for-dev
**Sprint:** 7 (Graphe parcours)
**Story Key:** `4-4-fiche-ecole-formation`
**Estimation:** M

---

## 1. User Story

**As a** student who has identified a school in their pathway
**I want** to view a detailed school/program page
**So that** I can assess whether it matches my expectations in terms of selectivity, cost, location, and available programs before applying

---

## 2. Acceptance Criteria (BDD)

### AC1 — Header renders correctly

**Given** a school slug
**When** I navigate to `/schools/{slug}`
**Then** the school name, city, and type badge are visible in the header

### AC2 — Formations list shown

**Given** a school with 3 seeded formations
**When** the page loads
**Then** all 3 formations are listed with name and duration

### AC3 — Metadata pills rendered

**Given** a school with `apprenticeship=True`, `selectivity_index=2`, `public_private="public"`
**When** the page loads
**Then** pills for "Alternance disponible", "Public", and selectivity 2/5 stars are visible

### AC4 — Admission stat shown as text

**Given** a school with an `AdmissionStat` (Story 4.2 data)
**When** the page loads with `?formation_id={id}` query param
**Then** the admission stat section shows `context_line` text (no CarteAdmission component yet — plain text fallback)

### AC5 — No admission stat graceful

**Given** a school with no `AdmissionStat`
**When** the page loads
**Then** no error is shown
**And** admission section renders "Données d'admission non disponibles"

### AC6 — Back CTA present

**When** the page loads
**Then** a "Retour au parcours" button/link is visible in the footer
**And** it links back to `/metiers` (or browser history if referrer available)

### AC7 — Responsive layout

**Given** a mobile viewport (375px)
**When** the page renders
**Then** the layout is stacked (single column)
**And** all content is readable without horizontal scroll

### AC8 — 404 on unknown slug

**Given** `slug="unknown-school"`
**When** navigating to `/schools/unknown-school`
**Then** Next.js 404 page is shown

---

## 3. Tasks / Subtasks

### T1 — Extend GET /api/v1/schools/{slug}/ to include formations and admission_stat

- [ ] Update `SchoolDetailSerializer` to include `formations` via `FormationInlineSerializer` (already planned in 4.1 — verify it is implemented, add if missing)
- [ ] Add `admission_stat` computed field to `SchoolDetailSerializer`: call `AdmissionPredictionService.predict(student_profile, school_slug, formation_id)` if `AdmissionStat` exists for that school, else return null
- [ ] `SchoolDetailView`: accept optional `?formation_id=` query param, pass to serializer context
- [ ] `FormationInlineSerializer` fields: `id`, `name`, `duration_years`, `parcoursup_open`, `affelnet_open`, `target_metiers` (list of `{slug, name}`)
- [ ] Handle ImportError gracefully: if `AdmissionPredictionService` not yet available, `admission_stat=null` (defensive import)

### T2 — Next.js page /schools/[slug]/page.tsx

- [ ] Create `apps/web/src/app/(authenticated)/schools/[slug]/page.tsx` as server component
- [ ] Accept `searchParams`: `formation_id` (optional UUID string)
- [ ] Fetch school detail from `GET /api/v1/schools/{slug}/?formation_id={...}` using `apiClient`
- [ ] Handle API 404 → Next.js `notFound()`
- [ ] Pass school data + `admission_stat` to `<FicheEcole>` client component
- [ ] Two-column desktop layout (school info left, admission stat right), single-column mobile
- [ ] Page title: `"{school.name} — {school.city}"`
- [ ] Add Suspense boundary with skeleton loader

### T3 — FicheEcole component

- [ ] Create `apps/web/src/components/schools/FicheEcole.tsx`
- [ ] Props: `school: SchoolDetail`, `admissionStat: AdmissionPrediction | null`
- [ ] Header section: school name (h1), city + region (subtitle), type badge (colored pill using `school.type`, e.g. "BTS" badge in blue, "Lycée Pro" in green)
- [ ] Metadata pills row: public/privé badge, "Alternance" pill if `apprenticeship=True`, "Stage" pill if `internship=True`, selectivity stars (1–5, filled/empty ★), Parcoursup badge if any formation has `parcoursup_open=True`, Affelnet badge if any formation has `affelnet_open=True`
- [ ] Tuition info: if `tuition_min_eur`/`tuition_max_eur` not null → show "Frais : {min}–{max} €/an"; if both 0 or null → "Gratuit (établissement public)"
- [ ] Body: description text (show first 300 chars with "Lire la suite" expand if > 300 chars)
- [ ] Top débouchés: `top_debouches` array, render as chip list (max 3 visible)
- [ ] Dates section: `parcoursup_dates` and `affelnet_dates` if non-empty, show open/close/results dates
- [ ] Formations list: render all formations from `school.formations[]` with name, duration, parcoursup/affelnet badges
- [ ] Admission stat section: if `admissionStat !== null` → render `context_line` + label badge + range text "Probabilité estimée : {min}–{max}%"; else → `<p>Données d'admission non disponibles</p>`; add `// TODO(story-4-11): replace with <CarteAdmission>` comment
- [ ] Footer CTA: `<Link href="/metiers">← Retour au parcours</Link>` styled as secondary button
- [ ] Full Tailwind responsive: `flex flex-col md:flex-row` for two-column layout

### T4 — Vitest tests

- [ ] `__tests__/FicheEcole.test.tsx`: render with full school data → header name/city/type visible, pills rendered (alternance, public, stars), description visible, CTA present
- [ ] `__tests__/FicheEcole.test.tsx`: render with `admissionStat=null` → "Données d'admission non disponibles" shown, no error
- [ ] `__tests__/FicheEcole.test.tsx`: render with `admissionStat` data → `context_line` and range text visible
- [ ] `__tests__/FicheEcole.test.tsx`: formations list renders all 3 formation names

---

## 4. Dev Notes

- Follow `apps/web/src/components/professions/FicheMetier.tsx` for component structure, Tailwind class patterns, and test setup
- `apiClient` is in `apps/web/src/lib/api/client.ts` — use existing fetch wrapper, do not create a new one
- Type definitions: create `apps/web/src/lib/api/types/schools.ts` for `SchoolDetail`, `Formation`, `AdmissionPrediction` interfaces (follow pattern of existing type files)
- `CarteAdmission` placeholder comment is mandatory — Story 4.11 will replace the plain text block
- Selectivity stars: 1=most selective (display 1 filled star out of 5), 5=least selective (5 filled stars) — include `aria-label` for accessibility (RGAA AA)
- UX-DR25: `admission_stat` section must look identical whether data comes from a complete or incomplete profile — only `context_line` text differs
- `@pytest.mark.django_db @pytest.mark.postgresql_only` on backend tests (T1 serializer tests if added)
- School type badge colors (Tailwind): `lycee_pro`=green, `bts`/`but`/`iut`=blue, `prepa`=purple, `licence`/`licence_pro`=indigo, `ecole_ingenieur`=orange, `ecole_commerce`=amber, `ecole_sante`=red, `universite`=slate, `autre`=gray

---

## 5. Dev Agent Record

### Agent Model Used
_À remplir_

### Completion Notes List
_À remplir_

### File List
_À remplir_

### Change Log
- 2026-06-21 — Story 4.4 créée.
