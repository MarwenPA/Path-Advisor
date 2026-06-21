# Story 4.7: Adaptation graphe par niveau scolaire (3ème → lycée pro)

**Epic:** 4 — Graphe de Parcours & Stats d'Admission (Deuxième Aha)
**Status:** ready-for-dev
**Sprint:** 7 (Graphe parcours)
**Story Key:** `4-7-adaptation-graphe-par-niveau`
**Estimation:** M

---

## 1. User Story

**As a** student (Mehdi, 3ème, bac pro track)
**I want** the pathway graph to start from a vocational high school (lycée pro) appropriate to my school level
**So that** my pathway is realistic for my actual situation and not built for a student in Terminale générale

---

## 2. Acceptance Criteria (BDD)

### AC1 — Mehdi (3ème, bac pro) sees a lycée pro as first node

**Given** an authenticated student with `niveau_scolaire="troisieme_bac_pro"`
**When** `GET /api/v1/metiers/technicien-aeronautique/parcours/` is called
**Then** the first parcours returned has `niveau_scolaire="troisieme_bac_pro"` and `is_default=True`
**And** the first node is of type `"diplome"` labelled "Bac Pro Aéronautique option Avionique"
**And** the second node is a `"diplome"` labelled "BTS Aéronautique"
**And** one terminal node mentions "poursuite école d'ingé en alternance"

### AC2 — Mehdi sees geographically accessible lycées pro

**Given** Mehdi is on the pathway view for "Technicien aéronautique"
**When** the school grid renders
**Then** it lists lycée pro schools with `type="lycee_pro"` that have `affelnet_open=True`
**And** the `affelnet_dates` (open/close/results) are visible on each school card

### AC3 — Sarah (Terminale générale) sees the standard pathway

**Given** an authenticated student with `niveau_scolaire="terminale_generale"`
**When** `GET /api/v1/metiers/technicien-aeronautique/parcours/` is called
**Then** the first parcours returned has `niveau_scolaire="terminale_generale"` or `is_default=True` for terminale
**And** the first node is of type `"diplome"` labelled "Bac S / Spé Maths" (already accomplished step)
**And** subsequent nodes include "Prépa BCPST" or "IUT Mesures Physiques" or "PASS"
**And** `parcoursup_dates` are visible on school cards (not `affelnet_dates`)

### AC4 — Fallback to terminale_generale if no exact niveau match

**Given** a student with `niveau_scolaire="terminale_technologique"`
**When** `GET /api/v1/metiers/{slug}/parcours/` is called for a métier with no terminale_technologique parcours
**Then** the parcours with `niveau_scolaire="terminale_generale"` is returned as the default
**And** no 404 or error is raised

### AC5 — Niveau badge displayed per parcours alternative

**Given** a pathway view showing 3 parcours alternatives
**When** the student taps "Voir d'autres chemins (2)"
**Then** each alternative shows a badge indicating its niveau: "Bac Pro", "Terminale", "Première", etc.
**And** the badge is visible without expanding the alternative

### AC6 — Seed has at least 4 bac pro parcours

**Given** the seeded database
**When** `Parcours.objects.filter(niveau_scolaire="troisieme_bac_pro").count()` is queried
**Then** the result is >= 4 (one per: technicien aéronautique, cuisinier, électricien, mécanicien auto)

---

## 3. Tasks / Subtasks

### T1 — Enrich Parcours model with niveau_scolaire choices

- [ ] In `apps/api/apps/schools/models.py`, update the `Parcours` model (created in Story 4.3 T1): add/update `niveau_scolaire` field as `CharField(max_length=30, choices=[("troisieme_bac_pro","3ème → Bac Pro"),("terminale_generale","Terminale Générale"),("terminale_technologique","Terminale Technologique"),("terminale_pro","Terminale Pro"),("autre","Autre")], default="terminale_generale")`
- [ ] Check if field already exists from Story 4.3 (Story 4.3 T1 uses `choices: troisieme, premiere, terminale` — these are different). Migration will need to rename or replace the field. **If field exists with different choices**: create an alembic/Django migration that ALTERs the column (rename values via `RunPython` if rows already exist, else drop and re-add)
- [ ] Create migration `0XXX_parcours_niveau_scolaire_choices.py`
- [ ] Update seed: in `apps/api/apps/schools/fixtures/parcours_seed.json` (Story 4.3 T1), add 4 bac pro parcours:
  - technicien-aeronautique / troisieme_bac_pro / is_default=False: nodes [3ème (type=diplome) → Bac Pro Aéronautique option Avionique (type=diplome, school_slug=lycee-metiers-aeronautique-toulouse) → BTS Aéronautique (type=diplome, school_slug=iut-toulouse-aero) → Option école ingé alternance (type=diplome, school_slug=null)]
  - cuisinier / troisieme_bac_pro / is_default=False: nodes [3ème → CAP Cuisine (type=diplome) → Bac Pro Cuisine (type=diplome)]
  - electricien / troisieme_bac_pro / is_default=False: nodes [3ème → Bac Pro Électrotechnique → BTS Électrotechnique]
  - mecanicien-auto / troisieme_bac_pro / is_default=False: nodes [3ème → Bac Pro Maintenance Auto → BTS MAVA]
- [ ] Update `seed_parcours` management command to include these new entries (idempotent)

### T2 — Adapt GET /api/v1/metiers/{slug}/parcours/ to prioritize by student niveau

- [ ] In `apps/api/apps/schools/views.py`, update `ParcoursByMetierView`:
  - Fetch `student_niveau = request.user.student_profile.niveau_scolaire` (or `None` if unauthenticated/profile absent)
  - Build queryset ordering: `Parcours.objects.filter(metier__slug=slug).annotate(niveau_match=Case(When(niveau_scolaire=student_niveau, then=Value(0)), default=Value(1), output_field=IntegerField())).order_by("niveau_match", "-is_default", "niveau_scolaire")`
  - This puts exact match first, then `is_default=True`, then others
  - Fallback: if no parcours with `niveau_scolaire=student_niveau` exists, the ordering naturally falls through to terminale_generale
- [ ] Alternatively accept optional `?niveau_scolaire=` query param to override profile value (useful for front-end testing)
- [ ] No schema changes to response — just ordering change

### T3 — Show niveau badge in ParcoursList alternatives

- [ ] In `apps/web/src/components/parcours/ParcoursList.tsx` (Story 4.3), add a niveau badge to each parcours header row (default and alternatives)
- [ ] Mapping for badge label: `{ troisieme_bac_pro: "Bac Pro", terminale_generale: "Terminale", terminale_technologique: "Terminale Techno", terminale_pro: "Terminale Pro", autre: "Autre" }`
- [ ] Badge style: small rounded pill, Tailwind `bg-orange-100 text-orange-700 text-xs px-2 py-0.5 rounded-full`
- [ ] Badge always visible even when parcours is collapsed (in the "Voir d'autres chemins" button row)
- [ ] Update `Parcours` TypeScript type in `apps/web/src/lib/api/types/schools.ts`: add `niveau_scolaire: "troisieme_bac_pro" | "terminale_generale" | "terminale_technologique" | "terminale_pro" | "autre"` and `niveau_label?: string` (optional, from API if serializer adds it)

### T4 — Add niveau_scolaire to StudentProfile model (if absent)

- [ ] Check `apps/api/apps/students/models.py` for existing `niveau_scolaire` field on `StudentProfile`
- [ ] If absent: add `niveau_scolaire = CharField(max_length=30, choices=[("troisieme_bac_pro","3ème → Bac Pro"),("terminale_generale","Terminale Générale"),("terminale_technologique","Terminale Technologique"),("terminale_pro","Terminale Pro"),("autre","Autre")], null=True, blank=True)` to `StudentProfile`
- [ ] Create migration `0XXX_studentprofile_add_niveau_scolaire.py`
- [ ] Update `StudentProfileSerializer` to include `niveau_scolaire` field (check `apps/api/apps/students/serializers.py`)
- [ ] **Do not break existing tests** — field is nullable, existing rows get `null`

### T5 — Tests

- [ ] `apps/api/apps/schools/tests/test_parcours_niveau.py`: `@pytest.mark.django_db @pytest.mark.postgresql_only`
  - Create student with `niveau_scolaire="troisieme_bac_pro"`, create 2 parcours for same métier (one terminale_generale, one troisieme_bac_pro) → GET returns bac pro parcours first
  - Create student with `niveau_scolaire="terminale_generale"` → GET returns terminale_generale parcours first
  - Student with `niveau_scolaire="terminale_technologique"` and no matching parcours → returns terminale_generale as fallback (no error)
- [ ] `apps/api/apps/schools/tests/test_parcours_seed.py`:
  - Run `seed_parcours` command, assert `Parcours.objects.filter(niveau_scolaire="troisieme_bac_pro").count() >= 4`
- [ ] `apps/web/src/components/parcours/__tests__/ParcoursList.test.tsx` (extend):
  - Render with parcours having `niveau_scolaire="troisieme_bac_pro"` → badge "Bac Pro" visible
  - Render with `niveau_scolaire="terminale_generale"` → badge "Terminale" visible

---

## 4. Dev Notes

- **Migration caution**: Story 4.3 T1 defines `niveau_scolaire` with choices `(troisieme, premiere, terminale)`. This story redefines them as `(troisieme_bac_pro, terminale_generale, ...)`. Before writing the migration, read the actual migration file created by Story 4.3 to check the current state. If Story 4.3 is not yet implemented, use the new choices from this story directly. If already implemented, write a `RunPython` migration to rename existing values.
- **Ordering with Case/When**: Django ORM pattern — `annotate(niveau_match=Case(When(..., then=0), default=1))` then `order_by("niveau_match", "-is_default")`. This is tested at `@pytest.mark.postgresql_only` because `CASE/WHEN` with custom ordering behaves differently in SQLite.
- **StudentProfile field check**: before adding `niveau_scolaire` to `StudentProfile`, grep `apps/api/apps/students/models.py` for `niveau`. Story 2.2 (onboarding niveau/filière) may have already added a similar field — do not duplicate. If a `filiere` or `level` field already tracks this, map it to the new choices via a property instead of a new column.
- **Affelnet vs Parcoursup dates**: Story 4.1 seed stores both `affelnet_dates` and `parcoursup_dates` on `School`. For lycée pro nodes (troisieme_bac_pro parcours), display `affelnet_dates`. For terminale parcours, display `parcoursup_dates`. Logic in `FicheEcole` / school node card: check `node.niveau_scolaire` or `school.affelnet_open` to decide which dates to show.
- **is_default constraint**: the DB-level partial unique index `UniqueConstraint(fields=["metier","niveau_scolaire"], condition=Q(is_default=True))` from Story 4.3 ensures only one default per `(metier, niveau_scolaire)` pair. When seeding, set `is_default=True` on one terminale_generale parcours per métier and `is_default=False` on troisieme_bac_pro (it becomes default only for users with that niveau via ordering logic).
- Reference seed data from Story 4.3: `parcours_seed.json` already has terminale parcours. Add bac pro parcours as additional entries without modifying existing ones.
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
- 2026-06-21 — Story 4.7 créée.
