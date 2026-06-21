# Story 4.2: Moteur prédiction admission (Parcoursup open data)

**Epic:** 4 — Graphe de Parcours & Stats d'Admission (Deuxième Aha)
**Status:** ready-for-dev
**Sprint:** 7 (Graphe parcours)
**Story Key:** `4-2-moteur-prediction-admission`
**Estimation:** L

---

## 1. User Story

**As a** student using Path-Advisor
**I want** to see a realistic admission probability range for a school or program
**So that** I can calibrate my application strategy without feeling discouraged by overly harsh predictions

---

## 2. Acceptance Criteria (BDD)

### AC1 — Label audacieux

**Given** a student profile and a school with historical `taux_admission=30%`
**When** `POST /api/v1/schools/predict-admission/` with that `school_slug`
**Then** response `label == "audacieux"`
**And** `min_proba`, `expected_proba`, `max_proba` are returned

### AC2 — Label sûr

**Given** a student profile and a school with `taux_admission=75%`
**When** `POST /api/v1/schools/predict-admission/`
**Then** response `label == "sur"`

### AC3 — Label réaliste

**Given** a school with `taux_admission=55%`
**When** `POST /api/v1/schools/predict-admission/`
**Then** `label == "realiste"`

### AC4 — Anti-humiliation guard

**Given** any school/student combination
**When** predicted probability would be < 5%
**Then** the response does NOT include a numeric probability
**And** `context_line` contains "Pari très audacieux"
**And** `label == "audacieux"`

### AC5 — Wider range without bulletins

**Given** a student with `has_bulletins=False`
**When** `POST /api/v1/schools/predict-admission/`
**Then** `max_proba - min_proba >= 30` (at least 30 pp range)
**And** `context_line` mentions "estimation indicative"

### AC6 — Latency

**Given** 10 concurrent requests
**When** all POST to `predict-admission/`
**Then** P95 response time < 2000ms

### AC7 — Unknown school returns 404

**Given** `school_slug="does-not-exist"`
**When** `POST /api/v1/schools/predict-admission/`
**Then** 404

---

## 3. Tasks / Subtasks

### T1 — AdmissionStat model + import_parcoursup_stats command

- [ ] Create `AdmissionStat` model in `apps/api/apps/schools/models.py`: `id` (UUIDField pk), `school` (FK School, on_delete=CASCADE), `formation` (FK Formation, null/blank, on_delete=SET_NULL), `annee` (IntegerField), `taux_admission` (FloatField, 0.0–100.0), `moyenne_admis_min` (FloatField, null/blank), `moyenne_admis_max` (FloatField, null/blank), `mentions_json` (JSONField default=dict, e.g. `{"TB": 0.12, "B": 0.35, "AB": 0.38, "P": 0.15}`), `updated_at` (auto_now). Unique constraint: `(school, formation, annee)`.
- [ ] Create migration
- [ ] Create management command `import_parcoursup_stats` generating synthetic but realistic stats for all seeded schools: `taux_admission` between 8–95% based on `selectivity_index` (index=1 → 8–25%, index=2 → 25–45%, index=3 → 45–65%, index=4 → 65–80%, index=5 → 80–95%). Idempotent (`update_or_create`).

### T2 — AdmissionPredictionService

- [ ] Create `apps/api/apps/schools/services/__init__.py` and `prediction_service.py`
- [ ] Implement `AdmissionPredictionService.predict(student_profile: dict, school_slug: str, formation_id: str | None = None) -> dict`
- [ ] Logic: fetch latest `AdmissionStat` for school/formation, compute `base_proba = taux_admission`, apply ±10 pp range (`min=base-10`, `max=base+10`, `expected=base`), clamp all to [0, 100]
- [ ] Label assignment: `proba < 40%` → `"audacieux"`, `40–70%` → `"realiste"`, `> 70%` → `"sur"`
- [ ] Anti-humiliation guard: if `expected_proba < 5` → return `{"label": "audacieux", "context_line": "Pari très audacieux — nous ne calculons pas de probabilité dans ce cas.", "action_lever": "Contactez le lycée pour un entretien de motivation.", "min_proba": null, "expected_proba": null, "max_proba": null}`
- [ ] If `has_bulletins=False` (`student_profile.get("has_bulletins", True)` is False): widen range by +15 pp on each side (`min -= 15`, `max += 15`, clamp), append `" (estimation indicative — bulletins non fournis)"` to `context_line`
- [ ] `context_line` examples: `"audacieux"` → `"Ce choix est ambitieux — {school_name} affiche {taux}% d'admis."`, `"realiste"` → `"{school_name} correspond bien à votre profil."`, `"sur"` → `"Très bon niveau de confiance pour {school_name}."`
- [ ] `action_lever`: for `"audacieux"` suggest contacting admissions; for `"realiste"`/`"sur"` suggest applying early

### T3 — POST /api/v1/schools/predict-admission/ endpoint

- [ ] Create `AdmissionPredictionInputSerializer`: `school_slug` (CharField required), `formation_id` (UUIDField optional, allow_null=True)
- [ ] Create `AdmissionPredictionView` (APIView, permission_classes=[IsAuthenticated], methods=[POST])
- [ ] View: validate input, fetch requesting user's `student_profile` (`has_bulletins` field), call `AdmissionPredictionService.predict()`, return 200 with prediction dict
- [ ] Return 404 if `school_slug` not found
- [ ] Wire url: `POST /api/v1/schools/predict-admission/`

### T4 — Profile-aware range widening (incomplete profile)

- [ ] Ensure `student_profile` is fetched from `request.user` (via related StudentProfile model or user attributes)
- [ ] `has_bulletins=False` triggers wider range AND `context_line` suffix; label determination is based on `expected_proba` before widening
- [ ] Document in service docstring: "UX-DR25 compliant — no visual difference between complete/incomplete profile beyond context_line"

### T5 — Pytest tests

- [ ] `tests/test_admission_stat.py`: model creation, unique constraint
- [ ] `tests/test_prediction_service.py`: `@pytest.mark.django_db @pytest.mark.postgresql_only` — test `label=audacieux` for taux<40%, `label=sur` for taux>70%, anti-humiliation guard (taux=2% → no numeric proba), wider range when `has_bulletins=False`
- [ ] `tests/test_predict_endpoint.py`: authenticated POST returns 200 with label, unauthenticated → 401, unknown slug → 404

---

## 4. Dev Notes

- `AdmissionPredictionService` must NOT call any external API in MVP — pure computation on `AdmissionStat` rows
- Keep service in `apps/schools/services/prediction_service.py` (follow pattern of `apps/professions/services/` if it exists, otherwise create `services/` package)
- Student profile access: check if `request.user.student_profile` or `request.user.profile` exists in codebase before implementing; reuse existing FK pattern
- `@pytest.mark.postgresql_only` is required on all tests using JSONField or FloatField aggregations
- Latency < 2s P95: service must do a single DB query (`select_related` school + latest AdmissionStat). No N+1.
- The anti-humiliation guard is a hard product requirement — tests MUST verify it

---

## 5. Dev Agent Record

### Agent Model Used
_À remplir_

### Completion Notes List
_À remplir_

### File List
_À remplir_

### Change Log
- 2026-06-21 — Story 4.2 créée.
