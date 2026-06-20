# Story 3.3: Moteur de scoring statistique content-based

**Epic:** 3 — Recommandation Vocationnelle (Premier Aha)
**Status:** review
**Sprint:** 6 (Recommandation vocationnelle)
**Story Key:** `3-3-moteur-scoring-statistique-content-based`
**Estimation:** M (medium) — pure domain logic replacement inside existing service skeleton. No new endpoints, no new schema, no infrastructure. Sized ~1.5 j focused work.

> This story replaces the stub `statistical_scorer.py` (which returns random scores) with real content-based filtering logic. All API contracts, schemas, JWT auth, Django client, and Profession data model are stable from Stories 3.1 and 3.2. This is a pure domain layer implementation.

---

## 1. User Story

**As a** Path-Advisor student,
**I want** my vocational recommendations to reflect my actual profile (passions, values, academic level, subjects, grades),
**So that** the top-ranked professions are genuinely aligned with who I am — not random noise.

---

## 2. Acceptance Criteria (BDD)

### AC1 — Scoring API contract respected

**Given** a valid `ScoreMeRequest` with `student_id`, `profile`, and `occupation_ids`
**When** `POST /v1/score-metiers` is called with a valid JWT
**Then** the response matches the `ScoreMeResponse` schema:
- `scored_occupations` contains one entry per `occupation_id` (same order not required)
- Each `OccupationScore.score` is an integer in `[0, 100]`
- Each `OccupationScore.signals_contributifs` contains **at least 2** `SignalContributif` entries
- Each `SignalContributif.weight` is a float in `(0, 1]` and all weights sum to 1.0 (±0.001)
- `OccupationScore.confidence_level` is one of `"low"`, `"medium"`, `"high"`
- `ScoreMeResponse.computation_time_ms` reflects actual elapsed time

### AC2 — Scoring algorithm: 4 weighted features

**Given** a student profile and a profession's signals
**When** the scorer computes the score
**Then** it uses exactly these 4 weighted components:

| Feature | Weight | Signal source |
|---------|--------|---------------|
| `passion_overlap` | 35% | Jaccard-based match: `student.passions` ∩ `profession.signals_json.passions` |
| `valeur_alignment` | 25% | Jaccard-based match: `student.valeurs` ∩ `profession.signals_json.valeurs` |
| `niveau_compatibility` | 20% | Binary: `student.niveau` ∈ `profession.level_compatibility` → 1.0 else 0.0 |
| `bulletin_quality` | 20% | 0.0 if `has_bulletins=false`; else `min(bulletin_summary.average / 20, 1.0)` |

**And** the final score is:
```
score = int(round(
    passion_overlap   * 0.35 * 100 +
    valeur_alignment  * 0.25 * 100 +
    niveau_compat     * 0.20 * 100 +
    bulletin_quality  * 0.20 * 100
))
```
clamped to `[0, 100]`.

**And** each `SignalContributif` has:
- `signal`: a descriptive key (e.g. `"passion_overlap"`, `"valeur_alignment"`, `"niveau_compatibility"`, `"bulletin_quality"`)
- `weight`: the feature weight (0.35, 0.25, 0.20, 0.20)
- `contribution`: `int(round(raw_score * weight * 100))` for that feature

### AC3 — Graceful degradation for incomplete profiles

**Given** a student profile missing optional fields
**When** the scorer runs
**Then**:
- Missing `passions` or `valeurs` → treats them as empty lists (overlap = 0, not an error)
- Missing `niveau` → `niveau_compatibility = 0.0`
- `has_bulletins = false` → `bulletin_quality = 0.0`, `confidence_level = "low"`
- `has_bulletins = true` and `bulletin_summary` missing or `average` is None → `bulletin_quality = 0.5` (neutral fallback), `confidence_level = "medium"`
- Empty `occupation_ids` → returns `[]` immediately, `computation_time_ms` reflects early exit

**And** no exception is raised for any missing-field combination.

### AC4 — Confidence level determination

**Given** a scored occupation
**When** the confidence level is assigned
**Then**:
- `"low"` if `has_bulletins = false`
- `"medium"` if `has_bulletins = true` and `bulletin_summary.average < 14.0` (or average is missing)
- `"high"` if `has_bulletins = true` and `bulletin_summary.average >= 14.0`

### AC5 — Jaccard similarity normalization

**Given** student passions `["biologie", "soins", "sport"]` and profession passions `["biologie", "aider les autres", "travail en équipe"]`
**When** passion overlap is computed
**Then** the result uses **normalized Jaccard** (case-insensitive, stripped):
```
normalized_a = {s.lower().strip() for s in student_set}
normalized_b = {s.lower().strip() for s in profession_set}
jaccard = len(intersection) / len(union)  # 0.0 if union is empty
```
Result: `1/5 = 0.20` for the example above.

### AC6 — Model version updated

**Given** the real scorer is deployed
**When** `GET /v1/model-version` is called
**Then** `model_version` returns `"0.2.0-statistical"` (bumped from 0.1.0-statistical)
**And** `features` lists all 4 feature names: `["passion_overlap", "valeur_alignment", "niveau_compatibility", "bulletin_quality"]`

### AC7 — Latency budget

**Given** a request scoring 52 professions
**When** the scorer runs in the ai-service process
**Then** `computation_time_ms ≤ 500` (P95 target, no external I/O in scorer)

### AC8 — Tests: ≥ 15 unit tests, all passing

**Given** the scorer implementation
**When** the test suite runs
**Then** all existing tests still pass AND new scorer tests cover:
- Correct score formula with known inputs
- Each feature independently (passion-only, valeur-only, niveau-only, bulletin-only)
- Empty occupation_ids → empty list
- Missing/null fields → graceful degradation
- Confidence level transitions (low / medium / high)
- Jaccard edge cases (empty sets, full overlap, no overlap)
- Score clamped to [0, 100]

---

## 3. Tasks / Subtasks

- [x] T1 — Implement real `statistical_scorer.py` (replace stub)
  - [x] T1.1 — Implement `_jaccard(a: set, b: set) -> float` helper (normalized, case-insensitive)
  - [x] T1.2 — Implement `_passion_overlap(profile, profession_signals) -> float`
  - [x] T1.3 — Implement `_valeur_alignment(profile, profession_signals) -> float`
  - [x] T1.4 — Implement `_niveau_compatibility(profile, level_compatibility) -> float`
  - [x] T1.5 — Implement `_bulletin_quality(profile) -> float`
  - [x] T1.6 — Implement `_confidence_level(profile) -> Literal["low", "medium", "high"]`
  - [x] T1.7 — Implement `score_occupations(profile, occupation_ids, professions_data)` main function assembling all features
  - [x] T1.8 — Bump `MODEL_VERSION = "0.2.0-statistical"` constant

- [x] T2 — Write unit tests for scorer
  - [x] T2.1 — Test `_jaccard`: empty sets, full overlap, partial overlap, case-insensitivity
  - [x] T2.2 — Test each feature helper independently with known inputs
  - [x] T2.3 — Test `score_occupations` end-to-end with a fully specified profile
  - [x] T2.4 — Test graceful degradation: all optional fields missing
  - [x] T2.5 — Test confidence levels: low / medium / high transitions
  - [x] T2.6 — Test empty occupation_ids → returns []
  - [x] T2.7 — Test score clamped to [0, 100]

- [x] T3 — Update `model_info.py` route constants
  - [x] T3.1 — Set `MODEL_VERSION = "0.2.0-statistical"` in `config.py`
  - [x] T3.2 — Update `FEATURES` list to `["passion_overlap", "valeur_alignment", "niveau_compatibility", "bulletin_quality"]`
  - [x] T3.3 — Update existing `test_model_info.py` assertions to match new version string

- [x] T4 — Update existing `test_scoring.py` (remove random-score assertions, add real ones)
  - [x] T4.1 — Updated model_version assertion to `"0.2.0-statistical"`
  - [x] T4.2 — Updated confidence level test: average=14.2 → "high" (not "medium")

- [x] T5 — Run full test suite and verify no regressions

---

## 4. Dev Notes

### 4.1 File to replace (the ONLY file with real changes)

**Target:** `apps/ai-service/src/domain/recommendation/statistical_scorer.py`

Current state (stub):
```python
MODEL_VERSION = "0.1.0-statistical"
MODEL_TYPE = "statistical_content_based"
FEATURES = ["passions_overlap", "valeurs_alignment", "niveau_compatibility", "bulletin_quality"]

def score_occupations(profile: dict, occupation_ids: list[str]) -> list[OccupationScore]:
    """STUB — returns random scores. Story 3.3 replaces with real logic."""
    has_bulletins = profile.get("has_bulletins", False)
    confidence: str = "medium" if has_bulletins else "low"
    results = []
    for occ_id in occupation_ids:
        score = random.randint(20, 95)
        results.append(OccupationScore(...))
    return results
```

**What to preserve:**
- Same function signature: `score_occupations(profile: dict, occupation_ids: list[str]) -> list[OccupationScore]`
- Same imports from `src.api.schemas`: `OccupationScore`, `SignalContributif`
- `MODEL_VERSION`, `MODEL_TYPE`, `FEATURES` module-level constants (update version to 0.2.0)

**Do NOT touch:**
- `src/api/routes/scoring.py` — calls `score_occupations`, no change needed
- `src/api/schemas.py` — contracts are stable
- `src/api/dependencies.py` — JWT unchanged
- Any Django-side file — ai_client.py unchanged

### 4.2 Model info route update

**Target:** `apps/ai-service/src/api/routes/model_info.py`

Update `MODEL_VERSION` constant to `"0.2.0-statistical"`. The `FEATURES` list may need renaming (current stub uses `"passions_overlap"` with an `s` — normalize to `"passion_overlap"` without `s` per AC6).

### 4.3 Scoring algorithm reference implementation

```python
import math
from src.api.schemas import OccupationScore, SignalContributif

WEIGHTS = {
    "passion_overlap":      0.35,
    "valeur_alignment":     0.25,
    "niveau_compatibility": 0.20,
    "bulletin_quality":     0.20,
}

def _jaccard(a: set[str], b: set[str]) -> float:
    na = {s.lower().strip() for s in a}
    nb = {s.lower().strip() for s in b}
    union = na | nb
    if not union:
        return 0.0
    return len(na & nb) / len(union)

def _passion_overlap(profile: dict, signals: dict) -> float:
    return _jaccard(
        set(profile.get("passions") or []),
        set(signals.get("passions") or []),
    )

def _valeur_alignment(profile: dict, signals: dict) -> float:
    return _jaccard(
        set(profile.get("valeurs") or []),
        set(signals.get("valeurs") or []),
    )

def _niveau_compatibility(profile: dict, level_compatibility: list[str]) -> float:
    niveau = (profile.get("niveau") or "").strip()
    if not niveau:
        return 0.0
    return 1.0 if niveau in level_compatibility else 0.0

def _bulletin_quality(profile: dict) -> float:
    if not profile.get("has_bulletins"):
        return 0.0
    bs = profile.get("bulletin_summary") or {}
    avg = bs.get("average")
    if avg is None:
        return 0.5  # neutral fallback
    return min(float(avg) / 20.0, 1.0)

def _confidence_level(profile: dict) -> str:
    if not profile.get("has_bulletins"):
        return "low"
    bs = profile.get("bulletin_summary") or {}
    avg = bs.get("average")
    if avg is None or float(avg) < 14.0:
        return "medium"
    return "high"
```

### 4.4 The `occupation_ids` param is opaque in the scorer

The scorer receives `occupation_ids: list[str]` as opaque strings — it does NOT call Django or any DB. The profession signals are passed via `profile` at call time. **Wait** — re-reading the existing schema:

```python
# ScoreMeRequest
student_id: str
profile: StudentProfile
occupation_ids: list[str]
```

The `occupation_ids` list in the current stub is treated as opaque IDs — the scorer doesn't fetch profession data; it just returns a score per ID with random values.

**Problem:** to implement real content-based scoring, the scorer needs the **profession signals** for each `occupation_id`. There are two architectural options:

**Option A (preferred — no DB in ai-service):** Django fetches profession signals and passes them embedded in the request. Requires schema change.

**Option B (simpler — use existing schema):** ai-service calls Django API to resolve occupation signals. Adds network round-trip.

**Option C (compromise — pass signals inline):** Extend `ScoreMeRequest` to include a `professions` field with signals, keeping `occupation_ids` for ordering.

**Decision:** The epic spec says "scoring engine reçoit le profil + liste des metiers à scorer". Looking at the AI service contract from 3.1, `occupation_ids` was designed as slug/id list. For the MVP scorer to be self-contained (< 500ms, no DB), **the scorer must receive profession data** either inline or the Django caller must pass it.

**Resolution for this story:** Extend `ScoreMeRequest` schema to accept optional `professions_data: list[ProfessionSignals] | None`. If provided, use for real scoring. If not (legacy call), fall back to a low-confidence score of 50 with confidence="low". Django's `ai_client.py` will be updated to pass profession signals.

**`ProfessionSignals` Pydantic model (new):**
```python
class ProfessionSignals(BaseModel):
    occupation_id: str
    signals_json: dict  # {"passions": [...], "valeurs": [...], "specialites": [...]}
    level_compatibility: list[str]
```

This is a **backward-compatible** schema extension (optional field with default `None`).

### 4.5 Django ai_client.py — must pass profession data

`apps/api/apps/recommendations/services/ai_client.py` must be updated to:
1. Fetch `Profession` objects by ID/slug from the DB
2. Serialize `signals_json` + `level_compatibility` per profession
3. Pass `professions_data` in the request body

This is a required change alongside the scorer. The Django `recommendations` app needs a service method to assemble profession data.

### 4.6 Tests location

- ai-service scorer tests: `apps/ai-service/src/tests/test_scoring.py` (update existing)
- New scorer unit tests: `apps/ai-service/src/tests/test_statistical_scorer.py` (new file)
- Django integration: `apps/api/apps/recommendations/tests/test_ai_client.py` (update mocks)

### 4.7 Tech stack reminders

- **Python 3.12** in ai-service (FastAPI 0.115, Pydantic v2)
- **pytest** with `httpx.AsyncClient` for route tests
- No `math.random` — scorer is now deterministic (no random imports needed)
- Pydantic v2: use `model_dump()` not `.dict()`, use `model_validate()` not `parse_obj()`
- All test fixtures in `conftest.py` use `@pytest.fixture`

### 4.8 Previous story learnings

From **Story 3.1** dev notes:
- JWT HS256 secret must be set via `AI_SERVICE_JWT_SECRET` env var — no hardcoded defaults in prod
- FastAPI route tests use `TestClient` from `fastapi.testclient`, not `httpx` directly
- `conftest.py` in `src/tests/` already has a `client` fixture

From **Story 3.2** dev notes:
- Profession `signals_json` always has `passions`, `valeurs`, `specialites`, `keywords` keys (never null, may be empty lists)
- `level_compatibility` is a Postgres ArrayField — serializes as a plain Python list in JSON
- `ProfessionPublicSerializer` already exposes `signals_json` and `level_compatibility`

---

## 5. Dev Agent Record

### Implementation Plan

Content-based scoring implemented as pure domain logic in `statistical_scorer.py`.
Extended `ScoreMeRequest` with optional `professions_data` (backward-compatible).
4 feature helpers + Jaccard + confidence level, all testable in isolation.

### Debug Log

- `score_occupations` signature extended with `professions_data: list[dict] | None = None` — backward compatible, existing call sites work without change.
- `config.py` bumped to `"0.2.0-statistical"` — model_info route reads from settings.
- `test_score_metiers_medium_confidence_with_bulletins` renamed to `_high_confidence` — average=14.2 ≥ 14.0 → "high" with real scorer.

### Completion Notes

- 53 tests passing, 0 regressions.
- Scorer is deterministic (no random imports).
- All 4 features independently tested with known values.
- `professions_data=None` graceful fallback verified (niveau + bulletin only scoring).
- Django `ai_client.py` updated to accept and forward `professions_data`.

---

## 6. File List

**Modified:**
- `apps/ai-service/src/domain/recommendation/statistical_scorer.py`
- `apps/ai-service/src/api/schemas.py`
- `apps/ai-service/src/api/routes/scoring.py`
- `apps/ai-service/src/config.py`
- `apps/ai-service/src/tests/test_scoring.py`
- `apps/ai-service/src/tests/test_model_info.py`
- `apps/api/apps/recommendations/services/ai_client.py`

**Created:**
- `apps/ai-service/src/tests/test_statistical_scorer.py`

---

## 7. Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-06-20 | Story created | bmad-create-story |
| 2026-06-20 | Implementation complete — 53 tests passing | bmad-dev-story |
