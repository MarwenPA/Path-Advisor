# Story 4.1: Référentiel formations/écoles MVP

**Epic:** 4 — Graphe de Parcours & Stats d'Admission (Deuxième Aha)
**Status:** ready-for-dev
**Sprint:** 7 (Graphe parcours)
**Story Key:** `4-1-referentiel-formations-ecoles`
**Estimation:** L

---

## 1. User Story

**As a** student using Path-Advisor
**I want** to browse a rich catalogue of schools and training programs
**So that** I can discover concrete post-bac pathways relevant to my target profession

---

## 2. Acceptance Criteria (BDD)

### AC1 — School model persisted

**Given** the database is migrated
**When** I query `School.objects.count()`
**Then** count >= 100
**And** at least 15 are type `lycee_pro`

### AC2 — Unique slug

**Given** two schools with the same name in different cities
**When** both are seeded
**Then** each has a distinct slug
**And** `GET /api/v1/schools/{slug}/` returns the correct one

### AC3 — Admin list endpoint

**Given** an authenticated superuser
**When** `GET /api/v1/admin/schools/?page=1`
**Then** returns a paginated list (page_size=100)
**And** each item includes `id`, `slug`, `name`, `type`, `city`

### AC4 — Admin formations endpoint

**Given** an authenticated superuser
**When** `GET /api/v1/admin/formations/?page=1`
**Then** returns paginated formations with `school` nested

### AC5 — Public school detail

**Given** an authenticated user
**When** `GET /api/v1/schools/{slug}/`
**Then** returns 200 with full school data including `formations[]`

### AC6 — 404 on unknown slug

**Given** an authenticated user
**When** `GET /api/v1/schools/unknown-slug/`
**Then** returns 404

### AC7 — Non-admin blocked on admin endpoints

**Given** a regular authenticated user (not superuser)
**When** `GET /api/v1/admin/schools/`
**Then** returns 403

---

## 3. Tasks / Subtasks

### T1 — Django models School + Formation in apps/api/apps/schools/

- [ ] Create Django app `schools` in `apps/api/apps/schools/` following `apps/professions/` structure
- [ ] Create `School` model: `id` (UUIDField, primary_key, default=uuid4), `slug` (SlugField, unique, max_length=120), `name` (CharField 200), `type` (CharField choices: lycee_pro, bts, but, iut, prepa, licence, licence_pro, ecole_ingenieur, ecole_commerce, ecole_sante, universite, autre), `city` (CharField 100), `region` (CharField 100), `postal_code` (CharField 10), `lat` (DecimalField 9,6, null/blank), `lon` (DecimalField 9,6, null/blank), `tuition_min_eur` (IntegerField null/blank), `tuition_max_eur` (IntegerField null/blank), `apprenticeship` (BooleanField default False), `internship` (BooleanField default False), `selectivity_index` (IntegerField 1-5, default 3), `public_private` (CharField choices: public, prive_sous_contrat, prive_hors_contrat), `description` (TextField blank), `top_debouches` (JSONField default=list), `parcoursup_dates` (JSONField default=dict), `affelnet_dates` (JSONField default=dict), `official_url` (URLField blank), `created_at`, `updated_at`
- [ ] Create `Formation` model: `id` (UUIDField pk), `name` (CharField 200), `school` (FK School, related_name=formations, on_delete=CASCADE), `duration_years` (IntegerField), `parcoursup_open` (BooleanField default False), `affelnet_open` (BooleanField default False), `target_metiers` (M2M to professions.Profession, blank=True), `created_at`
- [ ] Register app in `INSTALLED_APPS` and create migrations
- [ ] Register models in `admin.py`

### T2 — Seed data JSON 100+ schools + management command seed_schools

- [ ] Create `apps/api/apps/schools/fixtures/schools_seed.json` with 100+ entries covering: 15+ lycées pro (avionique, ébénisterie, électromécanique, informatique, carrosserie, cuisine, coiffure, commerce, aide à la personne, maçonnerie, chaudronnerie, mécanique auto, maintenance industrielle, electrotechnique, boulangerie), 20+ BTS/BUT/IUT/licences/prépas, 15+ écoles ingé/commerce/santé; cities: Paris, Lyon, Marseille, Bordeaux, Lille + Clermont-Ferrand, Limoges, Brest
- [ ] Create `apps/api/apps/schools/fixtures/formations_seed.json` with 2–4 formations per school (50+ total)
- [ ] Create management command `seed_schools` in `apps/api/apps/schools/management/commands/seed_schools.py` — idempotent (update_or_create on slug), loads schools then formations fixtures
- [ ] Add `make seed-schools` target or document in Dev Notes

### T3 — Admin API endpoints (IsPathAdmin)

- [ ] Create `SchoolAdminSerializer` with all fields
- [ ] Create `FormationAdminSerializer` with nested school (id, slug, name)
- [ ] Create `SchoolAdminViewSet` (ReadOnlyModelViewSet, permission_classes=[IsPathAdmin], pagination page_size=100)
- [ ] Create `FormationAdminViewSet` (ReadOnlyModelViewSet, permission_classes=[IsPathAdmin], pagination page_size=100)
- [ ] Wire urls: `GET /api/v1/admin/schools/` and `GET /api/v1/admin/formations/`

### T4 — Public API GET /api/v1/schools/{slug}/

- [ ] Create `FormationInlineSerializer` (id, name, duration_years, parcoursup_open, affelnet_open)
- [ ] Create `SchoolDetailSerializer` with all School fields + `formations` (FormationInlineSerializer many=True)
- [ ] Create `SchoolDetailView` (RetrieveAPIView, lookup_field=slug, permission_classes=[IsAuthenticated], returns 404 on unknown slug)
- [ ] Wire url: `GET /api/v1/schools/{slug}/`

### T5 — Pytest tests

- [ ] `tests/test_models.py`: `@pytest.mark.django_db @pytest.mark.postgresql_only` — test School + Formation creation, slug uniqueness
- [ ] `tests/test_seed.py`: call `seed_schools` command, assert `School.objects.count() >= 100`, filter type=lycee_pro count >= 15
- [ ] `tests/test_views_admin.py`: superuser gets 200 on `/admin/schools/` and `/admin/formations/`, regular user gets 403
- [ ] `tests/test_views_public.py`: authenticated user gets 200 + `formations[]` on `/schools/{slug}/`, 404 on unknown slug

---

## 4. Dev Notes

- Follow `apps/api/apps/professions/` structure exactly for app layout: `models.py`, `serializers.py`, `views.py`, `urls.py`, `admin.py`, `tests/`, `management/commands/`
- `IsPathAdmin` is in `apps/api/apps/audit/permissions.py` — requires `is_superuser=True` in test user setup
- All DB tests must have `@pytest.mark.django_db` and `@pytest.mark.postgresql_only`
- Slug generation: use `django.utils.text.slugify(f"{name}-{city}")`, handle collisions with a numeric suffix
- JSONField default must be a callable (`default=list`, `default=dict`), not a literal
- Seed data must use realistic French school names (e.g. "Lycée des Métiers de l'Aéronautique Pierre Guillaumat", "IUT de Bordeaux - Département Informatique")
- `selectivity_index`: 1 = très sélectif (grandes écoles), 5 = non sélectif (université ouverte)
- Parcoursup/Affelnet dates format: `{"open": "2026-01-15", "close": "2026-03-10", "results": "2026-06-05"}`

---

## 5. Dev Agent Record

### Agent Model Used
_À remplir_

### Completion Notes List
_À remplir_

### File List
_À remplir_

### Change Log
- 2026-06-21 — Story 4.1 créée.
