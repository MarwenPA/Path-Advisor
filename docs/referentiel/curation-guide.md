# Curation Guide — Professions Referential

## Purpose

This guide governs the editorial and ethical standards for every profession added to the Path-Advisor referential. Any new profession (MVP or future batch) MUST pass this checklist before merge.

---

## 1. Mandatory Quality Checklist

### 1.1 Content quality

- [ ] **`description`**: 100–300 words, written in plain language accessible to a 15–18 year old. No internal jargon ("Path-Advisor scoring", "vector embedding", etc.)
- [ ] **`daily_routine`**: 80–200 words, written in second person ("Tu commences ta matinée en…"). Must describe a realistic day, not a job posting.
- [ ] **`requirements_json`**: At least 5 items covering at least 2 of the 3 types (`studies`, `skill`, `quality`).
- [ ] **`prospects_text`**: At least 3 distinct career evolution paths or transitions.
- [ ] **`median_salary_eur`**: Filled for at least 80% of professions in a batch. Source must be cited in `sources_json`.
- [ ] **`signals_json`**: At least 8 total keywords across `passions`, `valeurs`, `specialites`, `keywords`. All 4 keys must be present.
- [ ] **`level_compatibility`**: At least 1 level. Values must come from the enum: `college_3eme`, `lycee_2nde`, `lycee_1ere_tle_general`, `lycee_1ere_tle_techno`, `lycee_1ere_tle_pro`, `postbac`.
- [ ] **`sources_json`**: At least 1 source from the recognised set (Onisep, ROME v4, Apec, France Travail, "validation humaine YYYY-MM").

### 1.2 Slug stability

- [ ] **Slug is unique** and in `kebab-case` (no accents, no uppercase).
- [ ] **Once published, the slug NEVER changes.** If the profession name evolves, add an alias — do not rename the slug.

---

## 2. Ethical Curation Checklist

### 2.1 Gender equity

- [ ] **No gendered job title** in `name` unless the inclusive form is used (e.g., "Infirmier·ère" not "Infirmier").
- [ ] **`description` and `daily_routine` use gender-neutral pronouns and forms** ("Tu", second person throughout).
- [ ] **No gender stereotypes** in descriptions:
  - Avoid: "un métier très masculin / très féminin", "comme pour les hommes", "parfait pour les femmes".
  - Avoid: assigning nurturing roles only to women, technical roles only to men.
  - When reviewing: would the sentence feel odd if the reader's gender was different from the "expected" one? If yes, rewrite.
- [ ] **Photos and visuals** (when added later): must include diverse gender representations.

### 2.2 Level equity (anti-elitism)

- [ ] **At least 30% of professions in the batch are compatible with `lycee_1ere_tle_pro`.** This is checked automatically by `test_schema.py::TestEthicalCuration`.
- [ ] **At least 30% of professions in the batch are compatible with `college_3eme`.** Same automated check.
- [ ] **Bac-pro compatible professions span at least 5 different sectors.** Automated check.
- [ ] **Do not describe technical/vocational training as "inferior"**: "accessible sans bac" is neutral, "pour ceux qui ne peuvent pas aller en terminale" is prohibited.

### 2.3 Socioeconomic representation

- [ ] **Salary data is presented without value judgement.** "Ce métier est accessible et bien rémunéré" is fine. "Ce métier est mal payé" is not (state facts, not verdicts).
- [ ] **Career paths include realistic upward mobility** for all starting levels, not only for postbac entrants.

---

## 3. Update Process

### Adding a new profession

1. Copy the template below into the appropriate `_seed_data_partN.py` file.
2. Fill all required fields.
3. Run the automated curation tests: `pytest apps/professions/tests/test_schema.py -v`
4. Pass the human curation checklist (sections 1 and 2 above).
5. Run `python manage.py seed_professions` on a dev environment to verify it loads cleanly.
6. Open a PR with the title `feat(referentiel): add <slug> profession`.

### Updating an existing profession

1. Never change the `slug`.
2. Update the data in `_seed_data_partN.py` and re-run the seed command with `--clear` on dev only.
3. For production: `python manage.py seed_professions` (uses `update_or_create` — idempotent).
4. Update `sources_json` to add the new human validation date.

### Deactivating a profession

1. Set `"is_active": False` in the seed data OR run a targeted DB update.
2. Do NOT delete the record — recommendations referencing this profession may exist.

---

## 4. Template for New Profession

```python
{
    "slug": "mon-metier-slug",
    "name": "Mon·Ma Métier·ère",
    "sector": "santé|tech|btp|business|arts|environnement|enseignement|securite|transport|social|sciences|industrie",
    "description": (
        "Description de 100 à 300 mots, à la 2e personne ou neutre, "
        "accessible à un ado de 15-18 ans. Pas de jargon."
    ),
    "daily_routine": (
        "Tu commences ta matinée en… (80-200 mots, 2e personne)"
    ),
    "requirements_json": [
        {"type": "studies", "label": "Formation requise — niveau et durée"},
        {"type": "studies", "label": "Alternative de formation"},
        {"type": "skill", "label": "Compétence technique 1"},
        {"type": "skill", "label": "Compétence technique 2"},
        {"type": "quality", "label": "Qualité personnelle 1"},
        {"type": "quality", "label": "Qualité personnelle 2"},
    ],
    "prospects_text": (
        "1. Évolution 1. "
        "2. Évolution 2. "
        "3. Reconversion possible."
    ),
    "median_salary_eur": 30000,  # NULL si vraiment inconnu
    "salary_range_json": {"min": 24000, "max": 45000, "source": "Onisep 2025"},
    "signals_json": {
        "passions": ["passion1", "passion2", "passion3"],
        "valeurs": ["valeur1", "valeur2", "valeur3"],
        "specialites": ["maths", "svt"],  # matières scolaires associées
        "keywords": ["mot1", "mot2", "mot3", "mot4"],
    },
    "level_compatibility": ["lycee_1ere_tle_general", "postbac"],
    "rome_code": "X0000",  # NULL si non disponible
    "sources_json": ["Onisep 2025", "validation humaine 2026-06"],
}
```
