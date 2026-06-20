# Story 3.1: Service IA `apps/ai-service` activé pour le scoring vocationnel

**Epic:** 3 — Recommandation Vocationnelle (Premier Aha)
**Status:** review
**Sprint:** 7 (Moteur de recommandation — fondations IA)
**Story Key:** `3-1-ai-service-scoring-vocationnel`
**Estimation:** M (medium) — activation JWT réelle + 2 nouveaux endpoints REST (`/v1/score-metiers`, `/v1/model-version`) + schémas Pydantic + client Django `ai_client.py` + ADR + tests. Sized ~1.5 j focused work.

> **Contexte :** L'`ai-service` FastAPI a été initialisé en Story 1.1 avec uniquement `/health` et un stub `verify_jwt` qui n'authentifie pas vraiment. Cette story **active le service pour le MVP** : JWT HS256 réel, deux premiers endpoints de scoring vocationnel, et le client Django qui l'orchestre. C'est la fondation sur laquelle Stories 3.3, 3.4 etc. vont construire la logique métier.

---

## 1. User Story

**As a** système Path-Advisor,
**I want** activer le service IA FastAPI (initialisé en Story 1.1) avec ses premiers endpoints de scoring vocationnel, distinct du back Django principal,
**So that** le moteur de recommandation scale horizontalement de manière séparée (NFR-SC4) et bénéficie de l'écosystème ML/DL natif Python (ADD-4), et que les stories 3.3+ puissent s'appuyer sur des contrats d'API stables.

---

## 2. Acceptance Criteria (BDD)

### AC1 — Endpoint `/health` amélioré (déjà existant, à compléter)

**Given** le service `apps/ai-service` tourne (local ou conteneur)
**When** je GET `/health`
**Then** il retourne `{"status": "ok", "version": "<semver>", "model_version": "<str>"}` (200)
**And** l'endpoint ne requiert **pas** d'authentification JWT

### AC2 — Authentification JWT HS256 réelle activée

**Given** un appel entrant vers un endpoint protégé (ex: `/v1/score-metiers`)
**When** le header `Authorization: Bearer <token>` est absent ou invalide (signature incorrecte, TTL expiré)
**Then** le service répond 401 avec body `{"detail": "Invalid or missing JWT token"}`

**Given** un token JWT valide (signé HS256, `AI_SERVICE_JWT_SECRET` partagé, `exp` dans le futur)
**When** je POST `/v1/score-metiers` avec ce token
**Then** la dépendance `verify_jwt` retourne les claims décodés (pas un dict vide comme dans Story 1.1)

### AC3 — Endpoint `POST /v1/score-metiers` exposé avec contrat stable

**Given** le service tourne et le token JWT est valide
**When** je POST `/v1/score-metiers` avec le body :
```json
{
  "student_id": "stu_01HXJ...",
  "profile": {
    "passions": ["biologie", "bénévolat"],
    "valeurs": ["utilité_sociale", "autonomie"],
    "niveau": "terminale_generale",
    "specialites": ["SVT", "Maths"],
    "has_bulletins": true,
    "bulletin_summary": {"average": 14.2, "appreciation_keywords": ["engagée"]}
  },
  "occupation_ids": ["occ_01...", "occ_02...", ...]
}
```
**Then** le service retourne (200) une liste de scores :
```json
{
  "student_id": "stu_01HXJ...",
  "model_version": "0.1.0-statistical",
  "scored_occupations": [
    {
      "occupation_id": "occ_01...",
      "score": 78,
      "signals_contributifs": [
        {"signal": "passion_biologie", "weight": 0.35, "contribution": 27},
        {"signal": "valeur_utilite_sociale", "weight": 0.25, "contribution": 19}
      ],
      "confidence_level": "medium"
    }
  ],
  "computation_time_ms": 120
}
```
**And** la latence est < 500 ms P95 sur instance locale
**And** si `occupation_ids` est vide, retourne liste vide sans erreur

**Given** un profil sans bulletins (`has_bulletins: false`, `bulletin_summary: null`)
**When** je POST `/v1/score-metiers`
**Then** le service retourne des scores valides
**And** `confidence_level` est `"low"` au lieu de `"medium"` ou `"high"`

### AC4 — Endpoint `GET /v1/model-version` exposé

**Given** le service tourne (pas de JWT requis sur cet endpoint)
**When** je GET `/v1/model-version`
**Then** il retourne :
```json
{
  "model_version": "0.1.0-statistical",
  "model_type": "statistical_content_based",
  "deployed_at": "2026-06-20T00:00:00Z",
  "features": ["passions_overlap", "valeurs_alignment", "niveau_compatibility", "bulletin_quality"]
}
```

### AC5 — Communication Django → ai-service via JWT (client `ai_client.py`)

**Given** Django reçoit un appel de scoring
**When** la `AIClient.score_metiers()` est appelée
**Then** le client génère un JWT signé HS256 avec claims `{"sub": "django-api", "iat": ..., "exp": ...}`
**And** il fait un `POST http://ai-service:8001/v1/score-metiers` avec `Authorization: Bearer <token>`
**And** en cas de timeout ou erreur 5xx, il lève une `AIServiceUnavailableError`

### AC6 — Séparation physique : 2 conteneurs Docker distincts

**Given** `docker-compose up` depuis la racine
**Then** `ai-service` tourne dans son propre conteneur `pa-ai` sur port 8001
**And** les 2 services communiquent via réseau Docker interne `path_advisor_net`

### AC7 — ADR documenté

**Given** la séparation Django (app) vs FastAPI (IA)
**When** je consulte `docs/adr/0011-django-vs-fastapi-scoring-separation.md`
**Then** il documente rationale, protocole JWT, contrat d'API, limitations MVP

### AC8 — Tests passants

**When** `uv run pytest` dans `apps/ai-service/`
**Then** 12 tests passent (JWT valide, JWT invalide, smoke scoring, model-version)

**When** `uv run pytest apps/recommendations/` dans `apps/api/`
**Then** 8 tests passent (génération JWT, score_metiers mock, timeout/5xx)

---

## 3. Technical Context & Developer Guardrails

[Voir contenu original — conservé pour référence]

---

## 4. Definition of Done

- [x] `POST /v1/score-metiers` avec JWT valide → 200 + réponse conforme au schéma
- [x] `POST /v1/score-metiers` sans JWT ou JWT invalide → 401
- [x] `GET /v1/model-version` → 200 sans auth
- [x] `GET /health` → 200 avec champ `model_version` ajouté
- [x] `AIClient.score_metiers()` dans Django génère un JWT valide et appelle le ai-service
- [x] `AIServiceUnavailableError` levée sur timeout/5xx
- [x] Variables d'env `AI_SERVICE_URL`, `AI_SERVICE_JWT_SECRET`, `AI_SERVICE_JWT_TTL_SECONDS` documentées dans `.env.example`
- [x] ADR `0011-django-vs-fastapi-scoring-separation.md` créé
- [x] `uv run pytest` dans `apps/ai-service/` → 12 tests passent
- [x] Pas de régression sur `test_health.py`
- [x] `ruff` propre sur les nouveaux fichiers ai-service et Django
- [x] `apps.recommendations` ajouté à `INSTALLED_APPS`

---

## 5. Dev Agent Record

### Implementation Notes

**Fichiers créés :**
- `apps/ai-service/src/api/schemas.py` — Pydantic v2 schemas pour les contrats d'API
- `apps/ai-service/src/domain/__init__.py`
- `apps/ai-service/src/domain/recommendation/__init__.py`
- `apps/ai-service/src/domain/recommendation/statistical_scorer.py` — stub scorer (scores aléatoires, remplacé en Story 3.3)
- `apps/ai-service/src/api/routes/scoring.py` — POST /v1/score-metiers
- `apps/ai-service/src/api/routes/model_info.py` — GET /v1/model-version
- `apps/ai-service/src/tests/test_scoring.py` — 8 tests scoring
- `apps/ai-service/src/tests/test_model_info.py` — 3 tests model-version
- `apps/ai-service/.env.example` — variables env ai-service
- `apps/api/apps/recommendations/__init__.py`
- `apps/api/apps/recommendations/apps.py`
- `apps/api/apps/recommendations/models.py` — scaffold vide
- `apps/api/apps/recommendations/services/__init__.py`
- `apps/api/apps/recommendations/services/ai_client.py` — façade unique Django → ai-service
- `apps/api/apps/recommendations/tests/__init__.py`
- `apps/api/apps/recommendations/tests/test_ai_client.py` — 8 tests unitaires avec mock httpx
- `docs/adr/0011-django-vs-fastapi-scoring-separation.md`

**Fichiers modifiés :**
- `apps/ai-service/src/main.py` — ajout routers scoring + model_info
- `apps/ai-service/src/config.py` — ajout `model_version`
- `apps/ai-service/src/api/dependencies.py` — activation JWT HS256 réel (vs stub Story 1.1)
- `apps/ai-service/src/api/routes/health.py` — ajout `model_version` dans réponse
- `apps/ai-service/src/tests/conftest.py` — ajout fixtures `client`, `auth_client`, `expired_token`
- `apps/api/pyproject.toml` — ajout `pyjwt>=2.10,<3.0` et `httpx>=0.27,<1.0`
- `apps/api/path_advisor/settings/base.py` — ajout `AI_SERVICE_URL`, `AI_SERVICE_JWT_SECRET`, `AI_SERVICE_JWT_TTL_SECONDS` + `apps.recommendations` dans INSTALLED_APPS
- `apps/api/path_advisor/settings/test.py` — ajout variables AI_SERVICE pour les tests

### Completion Notes

- 12 tests ai-service + 8 tests Django = 20 tests, tous verts
- Ruff propre sur les deux côtés
- Régression pré-existante `test_clean_fixture_succeeds` et 3 tests upload confirmée sur `main` avant cette story — non introduite par Story 3.1
- Le stub scorer retourne des scores aléatoires intentionnellement — Story 3.3 le remplacera
- ADR numéroté 0011 (0009 et 0010 étaient déjà pris par des ADRs existants)

---

## File List

### New Files
- `apps/ai-service/src/api/schemas.py`
- `apps/ai-service/src/api/routes/scoring.py`
- `apps/ai-service/src/api/routes/model_info.py`
- `apps/ai-service/src/domain/__init__.py`
- `apps/ai-service/src/domain/recommendation/__init__.py`
- `apps/ai-service/src/domain/recommendation/statistical_scorer.py`
- `apps/ai-service/src/tests/test_scoring.py`
- `apps/ai-service/src/tests/test_model_info.py`
- `apps/ai-service/.env.example`
- `apps/api/apps/recommendations/__init__.py`
- `apps/api/apps/recommendations/apps.py`
- `apps/api/apps/recommendations/models.py`
- `apps/api/apps/recommendations/services/__init__.py`
- `apps/api/apps/recommendations/services/ai_client.py`
- `apps/api/apps/recommendations/tests/__init__.py`
- `apps/api/apps/recommendations/tests/test_ai_client.py`
- `docs/adr/0011-django-vs-fastapi-scoring-separation.md`

### Modified Files
- `apps/ai-service/src/main.py`
- `apps/ai-service/src/config.py`
- `apps/ai-service/src/api/dependencies.py`
- `apps/ai-service/src/api/routes/health.py`
- `apps/ai-service/src/tests/conftest.py`
- `apps/api/pyproject.toml`
- `apps/api/uv.lock`
- `apps/api/path_advisor/settings/base.py`
- `apps/api/path_advisor/settings/test.py`

---

## Change Log

- 2026-06-20: Story 3.1 implémentée — JWT HS256 réel activé, endpoints `/v1/score-metiers` + `/v1/model-version`, client Django `AIClient`, app `recommendations` scaffoldée, ADR 0011, 20 tests verts (12 ai-service + 8 Django)
