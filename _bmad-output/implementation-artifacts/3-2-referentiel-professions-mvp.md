# Story 3.2: Référentiel professions MVP (50 métiers curés)

**Epic:** 3 — Recommandation Vocationnelle (Premier Aha)
**Status:** review
**Sprint:** 6 (Recommandation vocationnelle)
**Story Key:** `3-2-referentiel-professions-mvp`
**Estimation:** M (medium) — schema PostgreSQL + seed data 50+ métiers + validation curation éthique. Pas de IA, pas de front. Sized ~1.5–2 j focused work.

> Fondation données de l'Epic 3 : sans ce référentiel, aucun scoring vocationnel (Story 3.3), aucune fiche métier (Story 3.5), aucune adaptation par niveau (Story 3.9) ne peut fonctionner. La curation éthique est non-négociable dès le seed : au moins 30 % des métiers doivent servir les profils "Mehdi" (bac pro / voies techniques) pour éviter de reproduire les biais de valorisation par défaut.

---

## 1. User Story

**As a** content / data ops Path-Advisor,
**I want** un référentiel de 50+ professions curées avec description, prérequis, débouchés, revenu médian, journée type,
**So that** le moteur de recommandation (Story 3.3) ait une base de métiers crédible et utilisable dès le MVP (FR21), et que les fiches métier (Story 3.5) soient riches et actionnables.

**Business value :** le référentiel est la matière première du premier moment "aha". Un seed pauvre ou biaisé (trop grandes écoles, trop de métiers valorisés par défaut) invalide l'expérience dès le MVP. La curation humaine du seed est un acte éditorial et éthique, pas seulement technique.

---

## 2. Acceptance Criteria (BDD)

### AC1 — Schéma table `professions` en PostgreSQL

**Given** la migration de schéma s'exécute
**When** je consulte la table `professions`
**Then** elle contient les colonnes suivantes :
- `id` UUID PK
- `slug` VARCHAR(120) UNIQUE NOT NULL (ex. `infirmier-de-bloc-operatoire`)
- `name` VARCHAR(200) NOT NULL (ex. `Infirmier·ère de bloc opératoire`)
- `description` TEXT NOT NULL (100–300 mots)
- `daily_routine` TEXT NOT NULL (1 journée type narrative, 80–200 mots)
- `requirements_json` JSONB NOT NULL (liste de prérequis : études, compétences, qualités)
- `prospects_text` TEXT NOT NULL (3 débouchés minimum)
- `median_salary_eur` INTEGER (salaire médian brut annuel en €, NULL si inconnu)
- `salary_range_json` JSONB (ex. `{"min": 22000, "max": 55000, "source": "Onisep 2025"}`)
- `signals_json` JSONB NOT NULL (mots-clés liés aux passions / valeurs / spés pour le moteur de scoring)
- `level_compatibility` VARCHAR[] NOT NULL (valeurs : `college_3eme`, `lycee_2nde`, `lycee_1ere_tle_general`, `lycee_1ere_tle_techno`, `lycee_1ere_tle_pro`, `postbac`)
- `sector` VARCHAR(80) (ex. `santé`, `tech`, `social`, `btp`, `arts`, `business`, `environnement`)
- `rome_code` VARCHAR(10) NULL (code ROME si disponible)
- `sources_json` JSONB (ex. `["Onisep", "ROME v4.0", "validation humaine 2026-06"]`)
- `is_active` BOOLEAN DEFAULT TRUE
- `created_at`, `updated_at` TIMESTAMP

**And** un index `GIN` sur `signals_json` pour les recherches de scoring

**And** un index sur `level_compatibility` (array GIN) pour les filtres par niveau

### AC2 — Seed initial : 50+ métiers diversifiés

**Given** la migration de seed s'exécute (`python manage.py seed_professions` ou fixture Django)
**When** je compte les professions actives
**Then** au moins **50 métiers** sont présents, couvrant un panel diversifié :

| Secteur | Nb min |
|---|---|
| Santé / social / médico-social | 8 |
| Sciences / ingénierie / tech | 8 |
| BTP / industrie / artisanat | 6 |
| Business / commerce / gestion | 6 |
| Arts / culture / communication | 6 |
| Environnement / agriculture | 4 |
| Enseignement / formation | 4 |
| Sécurité / défense / juridique | 4 |
| Autres (transport, logistique…) | 4 |

**And** au moins **15 métiers** sont compatibles avec `college_3eme` ou `lycee_1ere_tle_pro` (pour Mehdi)

**And** au moins **30 %** des métiers (≥15) servent les profils "Mehdi" (bac pro, voies techniques, voies moins valorisées par défaut) — cet indicateur est vérifié par un test automatique

### AC3 — Qualité des données par fiche

**Given** je consulte n'importe quelle profession du seed
**When** je valide le contenu
**Then** :
- `description` : 100–300 mots, pas de jargon interne Path-Advisor, rédigé en langage accessible 15–18 ans
- `daily_routine` : 1 journée type narrative à la 2e personne (ex. "Tu commences ta matinée en…"), 80–200 mots
- `requirements_json` : au moins 5 items (`{ "type": "studies|skill|quality", "label": "..." }`)
- `prospects_text` : au moins 3 débouchés (évolutions de poste ou passerelles)
- `median_salary_eur` : renseigné pour au moins 80 % des professions (source Onisep / Apec / France Travail 2024–2025)
- `signals_json` : au moins 8 mots-clés (`{ "passions": [...], "valeurs": [...], "specialites": [...] }`)
- `level_compatibility` : au moins 1 niveau renseigné
- Aucun champ critique vide (`name`, `description`, `daily_routine`, `signals_json`, `level_compatibility`)

**And** un test automatique (pytest) vérifie ces invariants sur chaque profession du seed

### AC4 — Curation éthique : équité des profils

**Given** le seed est chargé
**When** je calcule la répartition des niveaux de compatibilité
**Then** :
- Au moins **30 %** des professions ont `lycee_1ere_tle_pro` dans `level_compatibility`
- Au moins **30 %** des professions ont `college_3eme` dans `level_compatibility`
- Les professions compatibles bac pro couvrent au moins 5 secteurs différents (pas seulement santé + artisanat)

**And** aucune profession dans le seed ne véhicule de stéréotypes de genre explicites dans sa description ou sa journée type (validé humainement + checklist dans `docs/referentiel/curation-guide.md`)

### AC5 — Sources et traçabilité

**Given** je consulte `sources_json` d'une profession
**When** je vérifie la traçabilité
**Then** chaque profession référence au moins 1 source parmi :
- Onisep (fiches métiers open data)
- ROME v4 (Pôle Emploi / France Travail)
- Apec
- Validation humaine interne (`"validation humaine 2026-06"`)

**And** un fichier `docs/referentiel/sources.md` documente les sources utilisées, les dates d'extraction, et la méthodologie de sélection des 50 métiers

### AC6 — Endpoint admin lecture seule

**Given** l'API Django est déployée
**When** un admin authentifié appelle `GET /api/v1/admin/professions/`
**Then** il reçoit la liste paginée des professions (50 items/page) avec tous les champs

**When** il appelle `GET /api/v1/admin/professions/{slug}/`
**Then** il reçoit la fiche complète

**And** ces endpoints sont protégés `IsAdminUser` (pas accessibles aux élèves en lecture directe — les recos passent par le moteur Story 3.3)

**And** un endpoint `GET /api/v1/professions/{slug}/` accessible aux élèves authentifiés retourne les champs publics (sans `sources_json`, `rome_code` brut, `is_active`)

---

## 3. Tasks / Subtasks

### T1 — Migration schéma PostgreSQL

- [x] Créer le modèle Django `Profession` dans `apps/api/apps/professions/models.py`
- [x] Migration Django : `0001_profession_initial.py`
- [x] Index GIN sur `signals_json` et `level_compatibility`
- [x] Serializers DRF : `ProfessionAdminSerializer` (complet) + `ProfessionPublicSerializer` (champs publics)

### T2 — Seed data 50+ métiers

- [x] Créer management command `seed_professions` (idempotent via `update_or_create`)
- [x] Rédiger 52 fiches (parts 1/2/3 + extensions) en respectant AC2, AC3, AC4
- [x] Sources prioritaires : Onisep open data, fiches ROME v4, complétées par rédaction interne
- [x] Checklist curation éthique (genre, niveau) vérifiée avant merge

### T3 — API endpoints

- [x] `GET /api/v1/admin/professions/` + `GET /api/v1/admin/professions/{slug}/` (admin only)
- [x] `GET /api/v1/professions/{slug}/` (élève authentifié — champs publics)
- [x] Appliquer RLS Story 1.8 + audit log Story 1.13 (`profession_viewed`)
- [x] URLs dans `apps/api/apps/professions/urls.py`

### T4 — Tests

**Backend (pytest) :**
- [x] Migration appliquée → table créée avec bons colonnes + index
- [x] Seed chargé → 50+ professions présentes
- [x] Au moins 30 % des professions compatibles bac pro (test automatique AC4)
- [x] Chaque profession : description ≥ 100 mots, signals_json ≥ 8 items, level_compatibility non vide (test AC3)
- [x] `GET /api/v1/admin/professions/` → 403 pour élève, 200 pour admin
- [x] `GET /api/v1/professions/{slug}/` → 200 pour élève authentifié, `sources_json` absent de la réponse

### T5 — Documentation

- [x] `docs/referentiel/sources.md` : sources, dates, méthodologie sélection
- [x] `docs/referentiel/curation-guide.md` : checklist éthique genre + niveau + processus de mise à jour

---

## 4. Dev Notes

### 4.1 Structure `signals_json`

```json
{
  "passions": ["biologie", "aider les autres", "travail en équipe"],
  "valeurs": ["utilité sociale", "contact humain", "stabilité"],
  "specialites": ["svt", "chimie", "physique"],
  "keywords": ["soin", "hôpital", "patient", "médecine"]
}
```

Le moteur de scoring (Story 3.3) utilisera ces signaux pour le calcul de recouvrement avec le profil élève.

### 4.2 Exemples de métiers par profil cible

**Mehdi (bac pro / 3ème) — exemples à inclure :**
- Électrotechnicien·ne, Carrossier·ère, Aide-soignant·e, Agent·e de sécurité, Cuisinier·ère, Mécanicien·ne auto, Technicien·ne de maintenance industrielle, Coiffeur·euse, Plombier·ère chauffagiste

**Sarah (Terminale général spés Maths+SVT) — exemples à inclure :**
- Médecin généraliste, Ingénieur·e en biotechnologies, Pharmacien·ne, Vétérinaire, Data scientist, Biologiste

**Léa (profil polyvalent) — exemples à inclure :**
- Designer UX/UI, Journaliste, Chef·fe de projet digital, Chargé·e de communication, Ergothérapeute

### 4.3 Format `requirements_json`

```json
[
  { "type": "studies", "label": "BTS Électrotechnique ou BAC Pro MELEC" },
  { "type": "studies", "label": "Bac pro suivi d'un BTS ou DUT possible" },
  { "type": "skill", "label": "Lecture de schémas électriques" },
  { "type": "skill", "label": "Habilitations électriques (B1, H1...)" },
  { "type": "quality", "label": "Rigueur et sens des responsabilités" },
  { "type": "quality", "label": "Travail en hauteur sans vertige" }
]
```

### 4.4 Décisions design verrouillées

- **Pas d'embeddings vectoriels dans ce seed** — les `signals_json` sont des mots-clés explicites (content-based filtering Story 3.3). Les embeddings éventuels sont générés à la volée par le service IA.
- **`level_compatibility` est un tableau** — un métier peut être compatible avec plusieurs niveaux (ex. aide-soignant·e : bac pro ASSP + terminale général + 3ème via CAP AEPE).
- **Slug stable** — le slug ne change pas après création (référencé dans les recos stockées). Toute modification de nom passe par un alias, pas un changement de slug.
- **50 métiers = MVP strict** — pas de tentative d'aller à 100 en sprint 6. La montée à 500 est couverte par NFR-SC5 (scaling référentiel), pas par ce sprint.

### 4.5 Items à différer

- Import automatique depuis Onisep API (V2)
- Interface admin CRUD professions (Epic 9)
- Traductions (EN, AR) — hors MVP
- Embeddings vectoriels pré-calculés — Story 3.3 si besoin

---

## 5. Project Structure Notes

```
apps/api/apps/professions/
  models.py                          ← Profession model (T1)
  serializers.py                     ← Public + Admin serializers (T3)
  views.py                           ← Admin list/detail + Public detail (T3)
  urls.py                            ← Routes (T3)
  migrations/
    0001_profession_initial.py       ← Schema migration (T1)
  fixtures/
    professions_seed.json            ← 50+ métiers curés (T2)
  management/commands/
    seed_professions.py              ← Management command (T2)
  tests/
    test_schema.py                   ← Migration + invariants seed (T4)
    test_endpoints.py                ← API access control (T4)

docs/referentiel/
  sources.md                         ← T5
  curation-guide.md                  ← T5
```

**Conventions à respecter :**
- RLS Story 1.8 sur tous les endpoints
- Audit log Story 1.13 sur `profession_viewed`
- Pas de données PHI dans ce modèle (données publiques de description métier uniquement)

---

## 6. References

- **Epic 3 detail** : `_bmad-output/planning-artifacts/epics/epic-3-recommandation-vocationnelle-premier-aha.md` § Story 3.2
- **Story 3.3** : moteur scoring — consomme `signals_json` + `level_compatibility`
- **Story 3.5** : fiche métier détaillée — consomme tous les champs publics
- **Story 3.9** : adaptation par niveau — filtre sur `level_compatibility`
- **NFR-SC5** : scaling référentiel 50 → 500 professions
- **PRD** : FR21 (fiche métier détaillée)
- **Story 1.8** : RLS PostgreSQL
- **Story 1.13** : journal audit

---

## 7. Dev Agent Record

### Agent Model Used
claude-sonnet-4-6

### Completion Notes List

- **T1**: Modèle `Profession` créé avec `ArrayField` (level_compatibility) et `JSONField` (signals_json, requirements_json, salary_range_json, sources_json). Migration 0001 (schéma initial) + migration 0002 (GIN indexes sur signals_json et level_compatibility via `django.contrib.postgres.indexes.GinIndex`).
- **T1**: Deux serializers DRF : `ProfessionPublicSerializer` (14 champs publics, exclut sources_json/rome_code) et `ProfessionAdminSerializer` (tous les champs + created_at/updated_at).
- **T2**: 52 professions curées réparties en 3 fichiers de données (`_seed_data_part1/2/3.py`) + fichier d'extensions (`_seed_extensions.py`) pour patcher les entrées sous les seuils de mots AC3. Management command `seed_professions` avec `update_or_create` idempotent + flag `--clear`.
- **T3**: 3 vues DRF (AdminProfessionListView, AdminProfessionDetailView, PublicProfessionDetailView), permissions `IsAuthenticatedAndActive + IsPathAdmin` / `IsStudent`, pagination 50/page, audit log `profession_viewed` sur l'endpoint public.
- **T4**: 576 tests non-DB passent en 0.33s avec SQLite settings. Tests DB (endpoints + GIN indexes + loaded_seed) marqués `@pytest.mark.postgresql_only` — s'exécutent uniquement sur PostgreSQL.
- **AC4**: bac-pro = 34/52 (65 %), college_3eme = 34/52 (65 %), 9 secteurs couverts par bac-pro.
- **AC2**: secteurs tous au-dessus des minimums (santé=9, sciences=9, btp=7, business=6, arts=7, environnement=4, enseignement=5, securite=4, transport=4 → total 55 entrées pour 52 professions uniques car un slug peut couvrir 2 secteurs sémantiques).

### File List

- `apps/api/apps/professions/models.py` (modèle Profession, existant — vérifié conforme)
- `apps/api/apps/professions/migrations/0002_profession_gin_indexes.py` (créé)
- `apps/api/apps/professions/serializers.py` (créé)
- `apps/api/apps/professions/views.py` (créé)
- `apps/api/apps/professions/urls.py` (créé)
- `apps/api/path_advisor/urls.py` (modifié — ajout include professions)
- `apps/api/apps/professions/management/commands/_seed_data_part1.py` (créé)
- `apps/api/apps/professions/management/commands/_seed_data_part2.py` (créé)
- `apps/api/apps/professions/management/commands/_seed_data_part3.py` (créé)
- `apps/api/apps/professions/management/commands/_seed_extensions.py` (créé)
- `apps/api/apps/professions/management/commands/seed_professions.py` (créé)
- `apps/api/apps/professions/tests/test_schema.py` (créé)
- `apps/api/apps/professions/tests/test_endpoints.py` (créé)
- `docs/referentiel/sources.md` (créé)
- `docs/referentiel/curation-guide.md` (créé)

### Change Log

- 2026-06-20 — Story 3.2 créée (Epic 3 launch). Fondation données pour moteur scoring Story 3.3 + fiches Story 3.5.
- 2026-06-20 — Implémentation complète : migration GIN, 52 professions curées, 3 endpoints DRF, 576 tests non-DB verts, documentation curation. Status → review.
