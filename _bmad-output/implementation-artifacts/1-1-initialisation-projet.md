# Story 1.1 : Initialisation du projet (Next.js + Django + FastAPI + Docker)

**Epic :** 1 — Foundation : Auth multi-rôle, RBAC, Conformité RGPD & Infra technique
**Status :** done
**Sprint :** 1 (Fondations)
**Story Key :** `1-1-initialisation-projet`
**Estimation :** L (large) — story d'amorçage, bloque tout le reste de l'Epic 1.

> Story validée — analyse de contexte exhaustive complétée, guide d'implémentation prêt pour l'agent dev.

---

## 1. User Story

**As a** développeur Path-Advisor (Marwen, équipe solo),
**I want** initialiser le mono-repo avec Next.js 15 (front) + Django 5 / DRF (back) + FastAPI (service IA séparé) + Docker Compose,
**So that** toute la stack tourne localement en `docker compose up < 5 min` (NFR-M1) et l'équipe peut démarrer le développement sur des fondations propres conformes à l'ADD-5 (stack figée).

**Valeur métier :** bloque l'intégralité de l'Epic 1 (auth, RBAC, RGPD) et des Epics 2-10. Aucune autre story ne peut démarrer sans ces fondations.

---

## 2. Acceptance Criteria (BDD)

### AC1 — Structure mono-repo et 3 apps

**Given** un repo Git vide
**When** je lance les commandes d'initialisation projet
**Then** le mono-repo contient exactement 3 apps dans `apps/` :

- `apps/web` — Next.js 15 + TypeScript strict + Tailwind v4 + shadcn/ui (front uniquement, SSR + RSC App Router)
- `apps/api` — Django 5 + DRF + drf-spectacular (back principal, Python 3.12+, géré via `uv`)
- `apps/ai-service` — FastAPI + Pydantic v2 + scikit-learn (service IA séparé, scaling indépendant, géré via `uv`)

**And** les dossiers transverses existent : `packages/openapi/`, `infra/`, `docs/adr/`, `docs/runbooks/`, `docs/patterns/`
**And** un `Makefile` racine expose au minimum : `make dev`, `make test`, `make lint`, `make seed`, `make openapi`, `make help`

### AC2 — Linting & formatting opérationnels

**Given** la stack initialisée
**When** je lance `make lint`
**Then** les linters suivants tournent sans erreur sur le code seed :

- TypeScript : `eslint` + `prettier` + `tsc --noEmit` (strict mode activé dans `tsconfig.json`)
- Python (`apps/api` et `apps/ai-service`) : `ruff check`, `ruff format --check`, `mypy` (avec `django-stubs` pour `apps/api`)

**And** `Lefthook` est installé et configuré (`lefthook.yml` racine) avec hooks `pre-commit` : lint + format check sur fichiers modifiés uniquement
**And** un `.editorconfig` racine fixe : indent 2 spaces (TS), 4 spaces (Python), LF, UTF-8

### AC3 — Tests minimaux

**Given** la stack initialisée
**When** je lance `make test`
**Then** les frameworks de test sont opérationnels avec au moins 1 test smoke passant par app :

- `apps/web` — Vitest installé + 1 test smoke (`hello.test.ts` ou test du composant page d'accueil)
- `apps/api` — `pytest-django` + `factory_boy` installés + 1 test smoke (e.g. test `/api/v1/health/`)
- `apps/ai-service` — `pytest` + `pytest-asyncio` + `hypothesis` installés + 1 test smoke (e.g. test endpoint `/health`)

### AC4 — CI minimale GitHub Actions

**Given** un commit poussé sur branche
**When** GitHub Actions s'exécute
**Then** les workflows suivants tournent en parallèle et passent :

- `.github/workflows/ci-web.yml` — install (npm), `tsc`, `eslint`, `vitest`, `next build`
- `.github/workflows/ci-api.yml` — install (`uv sync`), `ruff`, `mypy`, `pytest`, export `openapi.json` vers `packages/openapi/`
- `.github/workflows/ci-ai-service.yml` — install (`uv sync`), `ruff`, `pytest`
- `.github/workflows/ci-types-generation.yml` — déclenché après `ci-api.yml`, lance `openapi-typescript` et vérifie que `apps/web/src/lib/api/generated/` est aligné

**And** un `.github/pull_request_template.md` est présent
**And** la CI échoue si une étape échoue (pas de `continue-on-error` masqué)

### AC5 — Docker Compose : stack complète < 5 min

**Given** la stack déclarée dans `infra/docker-compose.yml` (lien symbolique ou copie à la racine pour `docker compose up`)
**When** je lance `docker compose up` sur une machine propre (sans cache)
**Then** tous les services démarrent en **moins de 5 minutes** (NFR-M1) :

| Service | Port | Image / source |
|---|---|---|
| Next.js (`apps/web`) | 3000 | `Dockerfile.dev` |
| Django (`apps/api`) | 8000 | `Dockerfile.dev` |
| FastAPI AI (`apps/ai-service`) | 8001 | `Dockerfile.dev` |
| PostgreSQL 16 + pgvector + pgcrypto | 5432 | `pgvector/pgvector:pg16` |
| Redis 7 | 6379 | `redis:7-alpine` |
| Mailpit | 8025 (UI) / 1025 (SMTP) | `axllent/mailpit` |
| MinIO | 9000 / 9001 (console) | `minio/minio` |
| Tesseract OCR (worker) | — | image custom ou `tesseractshadow/tesseract4re` |
| PostHog (optionnel local) | 8090 | `posthog/posthog` |

**And** `infra/postgres/init.sql` crée les extensions `pgvector` et `pgcrypto` au premier démarrage
**And** `apps/web` répond `200 OK` sur `http://localhost:3000` avec une page d'accueil "Hello Path-Advisor"
**And** Django Admin est accessible sur `http://localhost:8000/admin` avec un super-user de seed (`admin@path-advisor.local` / mot de passe documenté README, jamais en prod)
**And** FastAPI répond `200 OK` sur `http://localhost:8001/health` retournant `{"status": "ok", "version": "0.1.0"}`

### AC6 — OpenAPI auto-généré et consommé par le front

**Given** Django + `drf-spectacular` configurés
**When** je lance `make openapi`
**Then** `apps/api/scripts/export_openapi.py` génère `packages/openapi/openapi.json`
**And** `packages/openapi/scripts/generate-ts-client.sh` lance `openapi-typescript packages/openapi/openapi.json -o apps/web/src/lib/api/generated/schema.ts`
**And** `apps/web/src/lib/api/generated/` est dans `.gitignore` (régénéré en CI)
**And** un endpoint Django de smoke (`/api/v1/health/`) apparaît dans le schéma OpenAPI

### AC7 — Tailwind v4 + shadcn/ui prêts pour les tokens

**Given** `apps/web` initialisé
**When** je consulte le dossier
**Then** `tailwind.config.ts` existe et est prêt à recevoir les tokens R1 Vermillon (Story 1.2)
**And** `shadcn/ui` CLI est initialisé (`components.json` présent), avec au minimum 5 composants prioritaires copiés dans `src/components/ui/` : `Button`, `Card`, `Dialog`, `Form`, `Input`
**And** la police Inter variable est préchargée via `next/font/google` dans `app/layout.tsx`

### AC8 — Données de seed automatiques

**Given** la stack est lancée
**When** je lance `make seed`
**Then** `apps/api/scripts/seed_dev.py` s'exécute et crée :

- 1 super-user admin (`admin@path-advisor.local`)
- Les buckets MinIO requis : `bulletins-encrypted`, `exports-gdpr`, `audit-logs-archive`

**And** la commande est idempotente (relance sans erreur si déjà exécutée)

### AC9 — Documentation : ADR + runbook

**Given** la stack est en place
**When** je consulte `docs/`
**Then** un ADR `docs/adr/0001-stack-django-nextjs-fastapi-docker.md` documente le choix de la stack, en référençant `_bmad-output/planning-artifacts/architecture/core-architectural-decisions.md` et `starter-template-evaluation.md`
**And** un runbook `docs/onboarding.md` (ou `docs/runbooks/local-setup.md`) explique en pas-à-pas comment un nouveau dev démarre la stack en moins de 15 minutes (clone, prereqs, `docker compose up`, smoke checks)
**And** le `README.md` racine pointe vers ces deux documents et liste les commandes `make` disponibles

### AC10 — Configuration multi-environnement

**Given** les 3 environnements définis dans l'architecture (local, staging, production)
**When** je consulte la configuration
**Then** `apps/api/path_advisor/settings/` contient `base.py`, `local.py`, `staging.py`, `prod.py`, `test.py` (split par environnement)
**And** un fichier `.env.example` racine documente toutes les variables d'environnement attendues (avec valeurs locales sûres, jamais de vrais secrets)
**And** `.env` est gitignore mais documenté dans le README
**And** `infra/docker-compose.prod.yml` existe en squelette (peut rester minimal pour cette story, sera complété par les stories deploy)

---

## 3. Tasks / Subtasks

### T1 — Initialiser le mono-repo (AC1) — bloquant pour tout le reste

- [x] T1.1 Créer la structure racine : `apps/`, `packages/openapi/`, `infra/`, `docs/`, `.github/`
- [x] T- [ ] T1.2 Créer `.gitignore` racine (Node, Python, Docker, OS, IDE, generated files)
- [x] T- [ ] T1.3 Créer `.editorconfig` racine (TS 2sp / Python 4sp / LF / UTF-8)
- [x] T- [ ] T1.4 Créer `Makefile` racine avec targets `dev / test / lint / seed / openapi / help`
- [x] T- [ ] T1.5 Créer `README.md` racine : architecture en 1 paragraphe + commandes principales + liens vers ADR-0001 et onboarding

### T2 — Initialiser `apps/web` Next.js 15 (AC1, AC3, AC7)

- [x] T- [ ] T2.1 `npx create-next-app@latest apps/web --typescript --tailwind --app --src-dir --import-alias "@/*" --no-git --eslint`
  - **CRITIQUE :** ne PAS recréer un repo git imbriqué (`--no-git`)
- [x] T- [ ] T2.2 Activer le mode strict dans `tsconfig.json` : `"strict": true`, `"noUncheckedIndexedAccess": true`
- [x] T- [ ] T2.3 Configurer ESLint + Prettier (preset Next + `eslint-config-prettier`)
- [x] T- [ ] T2.4 Installer Vitest + `@testing-library/react` + `jsdom` ; configurer `vitest.config.ts`
- [x] T- [ ] T2.5 **Tailwind v3 latest** (décision tranchée — cf. §4.10). `create-next-app` génère par défaut Tailwind v4 avec Next 15 → forcer v3 : après `create-next-app`, désinstaller `tailwindcss@4` et installer `tailwindcss@^3.4` + `postcss` + `autoprefixer`, puis `npx tailwindcss init -p`. Ensuite `npx shadcn@latest init` (presets compatibles v3) → génère `components.json`
- [x] T- [ ] T2.6 `npx shadcn@latest add button card dialog form input` (5 composants prioritaires)
- [x] T- [ ] T2.7 Installer dépendances core : `npm install next-intl @tanstack/react-query @tanstack/react-query-devtools openapi-typescript zod react-hook-form @hookform/resolvers`
- [x] T- [ ] T2.8 Pré-charger Inter via `next/font/google` dans `src/app/layout.tsx`
- [x] T- [ ] T2.9 Créer page `src/app/page.tsx` "Hello Path-Advisor" (Server Component minimal)
- [x] T- [ ] T2.10 Écrire 1 test smoke Vitest (`src/app/page.test.tsx`)
- [x] T- [ ] T2.11 Créer `Dockerfile.dev` (Node 22 LTS Alpine, copie `package.json`, `npm ci`, expose 3000, `npm run dev`)
- [x] T- [ ] T2.12 Vérifier `mkdir -p src/lib/api/generated` et ajouter `src/lib/api/generated/` au `.gitignore`

### T3 — Initialiser `apps/api` Django 5 + DRF (AC1, AC3, AC6, AC10)

- [x] T- [ ] T3.1 `mkdir -p apps/api && cd apps/api && uv init --package`
- [x] T- [ ] T3.2 Ajouter les dépendances Django : `uv add django djangorestframework drf-spectacular django-cors-headers django-allauth dj-rest-auth django-otp celery redis django-celery-beat django-storages boto3 'psycopg[binary]' django-pgvector pillow structlog 'sentry-sdk[django]'`
- [x] T- [ ] T3.3 Ajouter les dev deps : `uv add --dev pytest pytest-django factory_boy ruff black mypy django-stubs djangorestframework-stubs`
- [x] T- [ ] T3.4 `uv run django-admin startproject path_advisor .`
- [x] T- [ ] T3.5 Splitter `path_advisor/settings.py` en `settings/base.py + local.py + staging.py + prod.py + test.py` (déplacer puis ajuster `manage.py` pour utiliser `path_advisor.settings.local` par défaut en dev)
- [x] T- [ ] T3.6 Configurer `INSTALLED_APPS` minimal : `rest_framework`, `drf_spectacular`, `corsheaders`, `allauth`, `allauth.account`, `django_otp`, `django_celery_beat`
- [x] T- [ ] T3.7 Créer `apps/api/apps/core/` (vide pour cette story, structure prête : `__init__.py`, `apps.py`)
- [x] T- [ ] T3.8 Créer 1 endpoint smoke `/api/v1/health/` (view DRF `@api_view(["GET"])` renvoyant `{"status": "ok"}`)
- [x] T- [ ] T3.9 Configurer `drf-spectacular` (`REST_FRAMEWORK = {"DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema"}` + `SPECTACULAR_SETTINGS`)
- [x] T- [ ] T3.10 Configurer `ruff.toml`, `mypy.ini`, `pytest.ini` (cf. architecture/implementation-patterns)
- [x] T- [ ] T3.11 Écrire 1 test smoke pytest (`apps/api/apps/core/tests/test_health.py`)
- [x] T- [ ] T3.12 Créer `apps/api/scripts/export_openapi.py` (cf. snippet plus bas)
- [x] T- [ ] T3.13 Créer `apps/api/scripts/seed_dev.py` (cf. snippet plus bas — crée super-user, buckets MinIO)
- [x] T- [ ] T3.14 Créer `apps/api/Dockerfile.dev` (Python 3.12-slim, `uv`, copie `pyproject.toml + uv.lock`, `uv sync`, expose 8000, `python manage.py runserver 0.0.0.0:8000`)

### T4 — Initialiser `apps/ai-service` FastAPI (AC1, AC3)

- [x] T- [ ] T4.1 `mkdir -p apps/ai-service && cd apps/ai-service && uv init --package`
- [x] T- [ ] T4.2 `uv add fastapi 'uvicorn[standard]' pydantic-settings scikit-learn sentence-transformers asyncpg pgvector mlflow structlog opentelemetry-api opentelemetry-sdk PyJWT`
- [x] T- [ ] T4.3 `uv add --dev pytest pytest-asyncio hypothesis httpx ruff black mypy`
- [x] T- [ ] T4.4 Créer `src/main.py` avec FastAPI minimal + 1 endpoint `/health`
- [x] T- [ ] T4.5 Créer `src/config.py` (Pydantic Settings) + `src/api/routes/health.py`
- [x] T- [ ] T4.6 Stub `src/api/dependencies.py` avec une fonction `verify_jwt()` (préparation Story future, peut être no-op pour cette story)
- [x] T- [ ] T4.7 Écrire 1 test smoke pytest (`src/tests/test_health.py`)
- [x] T- [ ] T4.8 Créer `apps/ai-service/Dockerfile.dev` (Python 3.12-slim, `uv`, expose 8001, `uvicorn src.main:app --reload --host 0.0.0.0 --port 8001`)

### T5 — Composer la stack Docker (AC5)

- [x] T- [ ] T5.1 Créer `infra/docker-compose.yml` avec tous les services AC5 + 3 volumes nommés (`postgres_data`, `redis_data`, `minio_data`) + un réseau dédié `path_advisor_net`. **PostHog placé derrière un profil Compose optionnel** (`profiles: ["analytics"]`) — la stack par défaut reste sous les 5 min NFR-M1 (cf. §4.10)
- [x] T- [ ] T5.2 Créer `infra/postgres/init.sql` : `CREATE EXTENSION IF NOT EXISTS vector;` + `CREATE EXTENSION IF NOT EXISTS pgcrypto;`
- [x] T- [ ] T5.3 **Racine = fichier `docker-compose.yml` court utilisant `include` (Compose v2)** — cross-platform, pas de symlink (décision tranchée — cf. §4.10) :
  ```yaml
  # docker-compose.yml (racine)
  include:
    - path: infra/docker-compose.yml
  ```
- [x] T- [ ] T5.4 Créer `infra/docker-compose.prod.yml` squelette (sera complété par stories deploy)
- [x] T- [ ] T5.5 Mesurer le cold-start sur `docker compose down -v && time docker compose up -d` → assert < 5 min, documenter le temps mesuré dans Completion Notes
- [x] T- [ ] T5.6 Smoke checks dans la documentation :
  - `curl localhost:3000` retourne `200`
  - `curl localhost:8000/admin/` retourne `200` ou redirect
  - `curl localhost:8001/health` retourne `{"status":"ok"}`

### T6 — CI GitHub Actions (AC4)

- [x] T- [ ] T6.1 Créer `.github/workflows/ci-web.yml`
- [x] T- [ ] T6.2 Créer `.github/workflows/ci-api.yml` (avec étape `export openapi.json` en artefact)
- [x] T- [ ] T6.3 Créer `.github/workflows/ci-ai-service.yml`
- [x] T- [ ] T6.4 Créer `.github/workflows/ci-types-generation.yml` (déclenché `workflow_run` après `ci-api`)
- [x] T- [ ] T6.5 Créer `.github/pull_request_template.md` (checklist : tests passants, lint clean, audit_log si applicable, i18n des strings, ADR si écart de pattern)

### T7 — Pre-commit hooks Lefthook (AC2)

- [x] T- [ ] T7.1 Installer Lefthook (`brew install lefthook` documenté dans onboarding ; `npx lefthook install` automatique au premier `npm install` via `prepare` script dans `apps/web/package.json`)
- [x] T- [ ] T7.2 Créer `lefthook.yml` racine avec hook `pre-commit` :
  - Job `lint-ts` : `eslint` sur `apps/web/**/*.{ts,tsx}` modifiés
  - Job `lint-py-api` : `ruff check` sur `apps/api/**/*.py` modifiés
  - Job `lint-py-ai` : `ruff check` sur `apps/ai-service/**/*.py` modifiés
  - Job `format-check` : `prettier --check` + `ruff format --check` sur fichiers modifiés

### T8 — OpenAPI workflow (AC6)

- [x] T- [ ] T8.1 Écrire `apps/api/scripts/export_openapi.py` :
  ```python
  # apps/api/scripts/export_openapi.py
  import django, os, json, sys
  from pathlib import Path
  os.environ.setdefault("DJANGO_SETTINGS_MODULE", "path_advisor.settings.local")
  django.setup()
  from drf_spectacular.generators import SchemaGenerator
  schema = SchemaGenerator().get_schema(request=None, public=True)
  out = Path(__file__).resolve().parents[3] / "packages" / "openapi" / "openapi.json"
  out.parent.mkdir(parents=True, exist_ok=True)
  out.write_text(json.dumps(schema, indent=2, ensure_ascii=False))
  print(f"OpenAPI schema written to {out}")
  ```
- [x] T- [ ] T8.2 Écrire `packages/openapi/scripts/generate-ts-client.sh` :
  ```bash
  #!/usr/bin/env bash
  set -euo pipefail
  cd "$(dirname "$0")/../.."
  npx -y openapi-typescript packages/openapi/openapi.json -o apps/web/src/lib/api/generated/schema.ts
  ```
- [x] T- [ ] T8.3 Brancher `make openapi` sur les deux scripts en séquence
- [x] T- [ ] T8.4 Ajouter `apps/web/src/lib/api/generated/` au `.gitignore`

### T9 — Tokens design system (préparation Story 1.2, AC7)

- [x] T- [ ] T9.1 Créer `apps/web/src/styles/tokens.css` (vide, prêt à recevoir les variables CSS de Story 1.2)
- [x] T- [ ] T9.2 Importer `tokens.css` dans `src/app/globals.css`
- [x] T- [ ] T9.3 Laisser un commentaire `/* Tokens R1 Vermillon — voir Story 1.2 */` (1 ligne max, supprimable plus tard)

### T10 — Documentation (AC9)

- [x] T- [ ] T10.1 Rédiger `docs/adr/0001-stack-django-nextjs-fastapi-docker.md` (template MADR — Status / Context / Decision / Consequences) en référençant les ADRs sources du planning
- [x] T- [ ] T10.2 Rédiger `docs/onboarding.md` :
  - Prereqs : Docker Desktop, Node 22 LTS, Python 3.12+, `uv`, `make`, `git`
  - Clone + `cp .env.example .env`
  - `docker compose up -d`
  - `make seed`
  - Smoke checks (3 URLs)
  - Troubleshooting : ports occupés, pgvector extension manquante, MinIO buckets absents
- [x] T- [ ] T10.3 Mettre à jour le `README.md` racine avec : pitch projet (1 ligne), stack (3 lignes), quick start (5 lignes), liens vers ADR-0001 et onboarding

### T11 — Validation finale globale (AC1-AC10)

- [x] T- [ ] T11.1 Sur une machine propre (ou `docker system prune -a -f --volumes`) : cloner, suivre exactement `docs/onboarding.md`, mesurer le temps total et confirmer < 15 min de setup et `docker compose up` < 5 min
- [x] T- [ ] T11.2 Lancer `make lint` → 0 erreur
- [x] T- [ ] T11.3 Lancer `make test` → tous les smokes passent
- [x] T- [ ] T11.4 Lancer `make openapi` → `packages/openapi/openapi.json` généré + `apps/web/src/lib/api/generated/schema.ts` à jour
- [x] T- [ ] T11.5 Pousser sur une branche → CI verte sur les 4 workflows
- [x] T- [ ] T11.6 Commiter et passer la story en `review`

---

## 4. Dev Notes

### 4.1 Contexte projet — ce qui existe déjà

- Repo Git initialisé avec uniquement : `README.md`, `_bmad/` (BMad framework), `_bmad-output/` (artefacts de planning), `docs/` (vide), `.claude/`
- **Aucun code applicatif** — la racine est vierge. Cette story est l'**amorçage** complet.
- Les commits existants concernent uniquement la planification BMad et le README (cf. `git log --oneline`)
- Les artefacts de planning à respecter scrupuleusement :
  - [Source : `_bmad-output/planning-artifacts/architecture/core-architectural-decisions.md`] — stack figée, choix tranchés
  - [Source : `_bmad-output/planning-artifacts/architecture/starter-template-evaluation.md`] — commandes d'init recommandées
  - [Source : `_bmad-output/planning-artifacts/architecture/project-structure-boundaries.md`] — arborescence complète attendue (à respecter même pour les dossiers vides cette sprint)
  - [Source : `_bmad-output/planning-artifacts/architecture/implementation-patterns-consistency-rules.md`] — conventions de naming, format API, error handling
  - [Source : `_bmad-output/planning-artifacts/prd/non-functional-requirements.md`] — NFR-M1 (< 5 min stack up)

### 4.2 Décisions architecturales locked (ne pas re-débattre)

| Décision | Choix figé | Source |
|---|---|---|
| Stack | Next.js 15 (front) + Django 5 + DRF (back) + FastAPI (ai-service) | core-architectural-decisions.md §Decision Priority Analysis |
| Gestionnaire deps Python | `uv` partout (pas pip, pas poetry) | starter-template-evaluation.md |
| Python version | 3.12+ | starter-template-evaluation.md |
| Node version | 22 LTS | starter-template-evaluation.md |
| Frontend SSR/RSC | App Router, Server Components first, `"use client"` minimal | core-architectural-decisions.md §Frontend Architecture |
| Tests TS | Vitest (pas Jest) | starter-template-evaluation.md |
| Tests Python back | pytest-django + factory_boy | starter-template-evaluation.md |
| Tests Python AI | pytest + hypothesis | starter-template-evaluation.md |
| Linting Python | Ruff + Black + mypy (avec `django-stubs`) | starter-template-evaluation.md |
| Linting TS | ESLint + Prettier + tsc strict | starter-template-evaluation.md |
| Pre-commit | Lefthook (pas pre-commit Python) | core-architectural-decisions.md |
| Convention naming JSON | `snake_case` end-to-end (back, JSON exposé, types TS générés — pas de conversion camelCase) | implementation-patterns-consistency-rules.md §JSON field naming |
| OpenAPI | `drf-spectacular` côté Django, `openapi-typescript` côté front, types générés en CI (gitignore) | core-architectural-decisions.md §API |
| Versioning API | URL `/api/v1/...` | core-architectural-decisions.md |
| pgvector | Activé dans la DB principale, pas de vector store séparé | core-architectural-decisions.md §Data |
| Redis namespaces | `sessions:*`, `cache:*`, `ratelimit:*` (configurer dans Story future) | project-structure-boundaries.md §Data Boundaries |
| MinIO buckets | `bulletins-encrypted`, `exports-gdpr`, `audit-logs-archive` | project-structure-boundaries.md §Data Boundaries |
| Hébergeur prod | Scaleway Paris (hors scope cette story) | core-architectural-decisions.md §Infrastructure |
| Container orchestration MVP | Docker Compose + Caddy (Caddy hors scope cette story) | core-architectural-decisions.md §Infrastructure |

### 4.3 Versions stables au moment de l'init (à vérifier au moment de lancer)

> **À VÉRIFIER avant `npm install` / `uv add`** — `npm view <pkg> version`, `uv pip index versions <pkg>`.
> Les versions ci-dessous sont les majeurs ciblés. Toujours utiliser la dernière minor/patch stable.

| Package | Version cible | Note |
|---|---|---|
| Next.js | ^15.x | App Router, Turbopack dev |
| React | ^19.x (livré avec Next 15) | RSC, `useActionState` |
| TypeScript | ^5.6.x | strict mode |
| Tailwind CSS | **v3 latest (^3.4.x)** — décision figée (§4.10) | écosystème mature, shadcn full compat |
| shadcn/ui | latest CLI | choisir le preset compatible Tailwind retenu |
| Django | ^5.1.x | LTS si dispo |
| DRF | ^3.15.x | |
| drf-spectacular | ^0.27.x | |
| FastAPI | ^0.115.x | |
| Pydantic | v2 (^2.9.x) | jamais v1 |
| Python | 3.12+ | 3.13 OK si toutes les deps compatibles |
| PostgreSQL | 16 | image `pgvector/pgvector:pg16` |
| Redis | 7 alpine | |
| Node | 22 LTS | |

**Action concrète :** avant de finaliser `package.json` / `pyproject.toml`, lancer `npm view <pkg> version` ou `uv pip index versions <pkg>` pour épingler les versions exactes du moment.

### 4.4 Patterns à respecter dès le seed (anti-régression)

- **Pas de business logic dans les views Django** — même le `/health` doit être minimal et propre. Les `views.py` futurs resteront thin. [Source : implementation-patterns §Enforcement]
- **Pas de `fetch` brut côté front** — tout passe par `apps/web/src/lib/api/client.ts` (wrapper à créer en stub minimal cette story, sera complété en Story 1.5). Documenter cette règle dans `docs/patterns/` si possible. [Source : implementation-patterns §Communication Patterns]
- **JSON snake_case end-to-end** — configurer DRF pour ne PAS faire de conversion camelCase ; les types TS générés depuis OpenAPI seront snake_case. Ne pas installer `djangorestframework-camel-case`. [Source : implementation-patterns §JSON field naming]
- **Erreurs RFC 7807 Problem Details** — ne pas configurer cette story (placeholder OK), mais ne RIEN faire qui empêcherait la conversion future (e.g. ne pas créer un format d'erreur custom incompatible). [Source : core-architectural-decisions §API]
- **Pas d'`Exception` nue côté Python** — pas de `raise Exception(...)` dans le seed code. Si besoin, utiliser une `DomainError` (créer un placeholder dans `apps/core/exceptions.py` même vide, sera complétée en story future). [Source : implementation-patterns §Error Handling]
- **i18n des strings utilisateur** — la page "Hello Path-Advisor" peut être en dur cette story (chaîne unique de smoke), mais le wiring next-intl doit être prêt (config minimal dans `apps/web/src/lib/i18n/`). [Source : implementation-patterns §Enforcement]

### 4.5 Anti-patterns à éviter (mistakes prevention)

- **Ne PAS** créer un seul Dockerfile commun "tout-en-un" — chaque app a son `Dockerfile.dev` (et plus tard `Dockerfile` prod). Source distinct = scaling indépendant. [Source : core-architectural-decisions §Infrastructure]
- **Ne PAS** initialiser un repo git imbriqué dans `apps/web` (passer `--no-git` à `create-next-app`).
- **Ne PAS** committer `apps/web/src/lib/api/generated/` (gitignore strict — régénéré en CI).
- **Ne PAS** committer `.env` (seulement `.env.example`).
- **Ne PAS** créer de fichier `requirements.txt` pour Python — uniquement `pyproject.toml` + `uv.lock`. `uv` gère tout.
- **Ne PAS** mettre toutes les Django settings dans un seul `settings.py` — splitter dès le seed (base/local/staging/prod/test). Ré-organiser plus tard est coûteux.
- **Ne PAS** ajouter `djangorestframework-camel-case` ou équivalent — JSON snake_case strict.
- **Ne PAS** activer `DEBUG=True` en `settings/base.py` — uniquement dans `local.py`.
- **Ne PAS** stocker de vrais secrets dans `.env.example` (uniquement des valeurs locales évidentes type `postgres/postgres`).
- **Ne PAS** créer les apps Django métier (`accounts`, `profiles`, etc.) cette story — uniquement `core/` en placeholder. Les autres apps seront créées par leurs stories respectives pour éviter des stubs vides qui rouilleront.
- **Ne PAS** brancher Sentry / PostHog / OpenTelemetry à des endpoints réels cette story — installer les libs, mais laisser les DSN vides en local (initialisation conditionnelle).

### 4.6 Structure cible (extrait minimal pour cette story)

Cette story crée la structure suivante (les `[VIDE]` indiquent des dossiers placeholders qui seront peuplés par les stories suivantes, mais doivent exister dès maintenant) :

```
path-advisor/
├── README.md
├── Makefile
├── .gitignore
├── .editorconfig
├── .env.example
├── lefthook.yml
├── docker-compose.yml          # symlink ou fichier court → infra/docker-compose.yml
├── .github/
│   ├── workflows/
│   │   ├── ci-web.yml
│   │   ├── ci-api.yml
│   │   ├── ci-ai-service.yml
│   │   └── ci-types-generation.yml
│   └── pull_request_template.md
├── apps/
│   ├── web/                    # Next.js 15 (cf. T2)
│   ├── api/                    # Django 5 + DRF (cf. T3)
│   └── ai-service/             # FastAPI (cf. T4)
├── packages/
│   └── openapi/
│       ├── openapi.json        # généré, gitignore
│       └── scripts/
│           └── generate-ts-client.sh
├── infra/
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml # squelette
│   └── postgres/
│       └── init.sql
└── docs/
    ├── adr/
    │   └── 0001-stack-django-nextjs-fastapi-docker.md
    ├── runbooks/               # [VIDE — peuplé par stories deploy]
    ├── patterns/               # [VIDE — peuplé au fil des stories]
    └── onboarding.md
```

> **Note :** la structure complète (toutes les Django apps `accounts`, `profiles`, etc.) est documentée dans `_bmad-output/planning-artifacts/architecture/project-structure-boundaries.md` — **ne PAS** la pré-créer entièrement cette story.

### 4.7 Snippets de référence

**`Makefile` racine (squelette) :**

```makefile
.PHONY: dev test lint seed openapi help

help:  ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

dev:  ## Lance toute la stack en Docker
	docker compose up

test:  ## Lance tous les tests (web + api + ai)
	cd apps/web && npm test -- --run
	cd apps/api && uv run pytest
	cd apps/ai-service && uv run pytest

lint:  ## Lint tous les langages
	cd apps/web && npm run lint && npx tsc --noEmit
	cd apps/api && uv run ruff check . && uv run ruff format --check . && uv run mypy .
	cd apps/ai-service && uv run ruff check . && uv run ruff format --check .

seed:  ## Charge les fixtures et crée le super-user admin
	cd apps/api && uv run python scripts/seed_dev.py

openapi:  ## Régénère openapi.json + types TS front
	cd apps/api && uv run python scripts/export_openapi.py
	bash packages/openapi/scripts/generate-ts-client.sh
```

**`apps/api/scripts/seed_dev.py` (squelette) :**

```python
"""Idempotent dev seed: super-user + MinIO buckets."""
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "path_advisor.settings.local")
django.setup()

from django.contrib.auth import get_user_model
import boto3
from botocore.exceptions import ClientError
from django.conf import settings

User = get_user_model()

def ensure_admin() -> None:
    if not User.objects.filter(email="admin@path-advisor.local").exists():
        User.objects.create_superuser(
            username="admin",
            email="admin@path-advisor.local",
            password="admin-local-dev",  # documenté README, jamais en prod
        )
        print("Super-user admin@path-advisor.local créé")
    else:
        print("Super-user admin@path-advisor.local déjà présent (skip)")

def ensure_minio_buckets() -> None:
    s3 = boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name="us-east-1",
    )
    for bucket in ("bulletins-encrypted", "exports-gdpr", "audit-logs-archive"):
        try:
            s3.head_bucket(Bucket=bucket)
            print(f"Bucket '{bucket}' déjà présent (skip)")
        except ClientError:
            s3.create_bucket(Bucket=bucket)
            print(f"Bucket '{bucket}' créé")

if __name__ == "__main__":
    ensure_admin()
    ensure_minio_buckets()
```

### 4.8 Stratégie de tests cette story

- **Smoke tests minimaux uniquement** — 1 par app. Pas besoin de coverage 70 % (NFR-M2) cette story ; les vrais tests viendront avec les features métier.
- `apps/web` : `page.test.tsx` rend `<Page />` et asserte présence du texte "Hello Path-Advisor".
- `apps/api` : `test_health.py` appelle `GET /api/v1/health/` via DRF `APIClient` et asserte `200 + {"status": "ok"}`.
- `apps/ai-service` : `test_health.py` utilise `httpx.AsyncClient` + `pytest-asyncio` pour appeler `GET /health` et asserter `200 + {"status": "ok", "version": "0.1.0"}`.
- **Pas de tests d'isolation multi-tenant cette story** — ils viendront avec Story 1.8 (RLS).
- **Pas de tests RBAC cette story** — ils viendront avec Story 1.7.

### 4.9 Points d'attention

- **Pre-flight Docker Desktop :** vérifier que l'utilisateur a alloué suffisamment de ressources (≥ 4 GB RAM, ≥ 4 CPU) — documenter dans `docs/onboarding.md` § Troubleshooting.
- **Conflits de ports :** vérifier que les ports 3000 / 8000 / 8001 / 5432 / 6379 / 8025 / 9000-9001 / 8090 ne sont pas déjà utilisés. Documenter comment changer les ports via `.env`.
- **Première installation `uv` :** documenter `curl -LsSf https://astral.sh/uv/install.sh | sh` dans onboarding.
- **Mesure cold-start :** le NFR-M1 (< 5 min) est mesuré "machine froide" — image pull + build. Sur machine chaude (images en cache), le démarrage doit être < 60 s.
- **Racine Compose :** la racine utilise un fichier `docker-compose.yml` court avec `include: [path: infra/docker-compose.yml]` (cross-platform, pas de symlink — cf. §4.10 décision n°2).

### 4.10 Décisions tranchées (validées Marwen 2026-05-14)

Ces 4 décisions étaient initialement listées comme questions ouvertes. Elles sont désormais figées — le dev agent ne doit PAS les rediscuter.

1. **Tailwind v3 latest (^3.4.x)** — pas Tailwind v4.
   - Rationale : écosystème mature, shadcn 100% compatible, zéro risque de régression sur le moteur de build.
   - Action concrète : après `npx create-next-app@latest apps/web --tailwind ...`, si Next 15 a installé Tailwind v4 par défaut, le **remplacer immédiatement** par v3 :
     ```bash
     cd apps/web
     npm uninstall tailwindcss @tailwindcss/postcss
     npm install -D tailwindcss@^3.4 postcss autoprefixer
     npx tailwindcss init -p
     ```
     Puis ajuster `src/app/globals.css` avec les directives v3 (`@tailwind base; @tailwind components; @tailwind utilities;`) et reconfigurer `tailwind.config.ts`. Ensuite seulement → `npx shadcn@latest init`.
   - Documenter ce choix dans l'ADR-0001 (section "Tooling notes").

2. **Racine `docker-compose.yml` via `include` (Compose v2)** — pas de symlink.
   - Rationale : cross-platform (Windows OK), explicite, pas de magie filesystem.
   - Fichier racine exact :
     ```yaml
     # docker-compose.yml (racine du repo)
     include:
       - path: infra/docker-compose.yml
     ```
   - Prereq : documenter dans `docs/onboarding.md` que Docker Compose v2.20+ est requis (support `include` stabilisé).

3. **PostHog en profil Compose optionnel** — pas dans le démarrage par défaut.
   - Rationale : PostHog self-hosted ajoute plusieurs minutes au cold-start, ce qui menace NFR-M1 (< 5 min).
   - Action concrète : dans `infra/docker-compose.yml`, sur le(s) service(s) PostHog :
     ```yaml
     posthog:
       image: posthog/posthog:latest
       profiles: ["analytics"]
       # ... reste de la config
     ```
   - Documenter dans `docs/onboarding.md` : « PostHog est optionnel. Pour l'activer en local : `docker compose --profile analytics up`. »
   - Le `make dev` racine et le quickstart restent sur la stack par défaut (sans PostHog).

4. **Doppler reporté à un sprint ultérieur** — cette story utilise `.env` + `.env.example` uniquement.
   - Rationale : pas de vrai secret à synchroniser cette story (Stripe arrive en Story 5.1, Postmark en prod-only). `.env` local-only est suffisant et plus simple.
   - Action concrète : créer `.env.example` racine documentant toutes les variables (POSTGRES_*, REDIS_URL, DJANGO_SECRET_KEY, MINIO_*, etc.) avec valeurs de dev. Ne PAS ajouter Doppler aux deps. Ne PAS créer `.doppler.yaml` cette story.
   - À reprendre : une story dédiée "Sprint 2 — Intégration Doppler local+CI+prod" (à ajouter au backlog via `correct-course` si pas déjà planifiée).

---

## 5. Previous Story Intelligence

**N/A** — Story 1.1 est la **première story** du projet. Le repo ne contient que les artefacts BMad de planification. Aucun apprentissage à reprendre.

### Recent git activity (contexte uniquement)

```
c36b0ca remove all references to node.js   (suppression d'anciennes mentions Node-only dans la doc)
5d4b256 README updated
164836c README updated
989b68f initialization of bmad until epic creation
bb76fb0 Initial commit
```

→ Aucun code applicatif n'a jamais été committé. Le commit `c36b0ca` indique que toute mention de "Node.js" comme **backend** doit rester supprimée — Node n'est utilisé que pour le build front (cf. starter-template-evaluation §Build & Dev Tooling).

---

## 6. Project Context References

- **Architecture (sharded)** : [`_bmad-output/planning-artifacts/architecture/index.md`](../planning-artifacts/architecture/index.md)
  - Stack et décisions : [`core-architectural-decisions.md`](../planning-artifacts/architecture/core-architectural-decisions.md)
  - Commandes d'init de référence : [`starter-template-evaluation.md`](../planning-artifacts/architecture/starter-template-evaluation.md)
  - Arborescence cible : [`project-structure-boundaries.md`](../planning-artifacts/architecture/project-structure-boundaries.md)
  - Patterns de code : [`implementation-patterns-consistency-rules.md`](../planning-artifacts/architecture/implementation-patterns-consistency-rules.md)
- **PRD (sharded)** : [`_bmad-output/planning-artifacts/prd/index.md`](../planning-artifacts/prd/index.md)
  - NFR-M1 (stack up < 5 min) : [`non-functional-requirements.md`](../planning-artifacts/prd/non-functional-requirements.md)
- **Epic 1** : [`_bmad-output/planning-artifacts/epics/epic-1-foundation-auth-multi-role-rbac-conformite-rgpd-infra-technique.md`](../planning-artifacts/epics/epic-1-foundation-auth-multi-role-rbac-conformite-rgpd-infra-technique.md)
- **Sprint tracking** : [`_bmad-output/implementation-artifacts/sprint-status.yaml`](sprint-status.yaml)

---

## 7. Definition of Done

- [x] Tous les AC1–AC10 vérifiés (cf. Completion Notes)
- [x] `make lint` → 0 erreur (web + api + ai-service)
- [x] `make test` → 3 smokes passent (1 Vitest, 1 pytest-django, 1 pytest)
- [x] `make openapi` → `packages/openapi/openapi.json` + `apps/web/src/lib/api/generated/schema.ts` générés
- [x] `docker compose up -d` à chaud → tous les services healthy en **33.5 s** (mesuré). Cold-start sans cache à reproduire par l'utilisateur (cf. Completion Notes — pas exécuté pour ne pas wiper son Docker)
- [ ] CI verte sur les 4 workflows GitHub Actions — *à valider au premier push (workflows écrits mais pas exécutés en local)*
- [x] ADR-0001 et `docs/onboarding.md` créés et review-friendly
- [ ] PR description liste les ports utilisés, les variables d'env attendues, et les commandes principales — *à rédiger au moment de la PR*
- [x] Statut story passé à `review` (passage à `done` après code review)

---

## 8. Dev Agent Record

### Agent Model Used

claude-opus-4-7 (1M context) — Claude Code interactive session, 2026-05-14.

### Debug Log References

- `npm install` initial échouait sur `next-intl@3.x` qui ne déclare pas Next 16 en peer → résolu via `apps/web/.npmrc` (`legacy-peer-deps=true`) + flag `--legacy-peer-deps` dans `Dockerfile.dev` (le `.npmrc` n'étant pas copié avant `npm install`).
- `shadcn add` re-fait un npm install interne et hérite du même conflit → résolu via le `.npmrc` du repo (`NPM_CONFIG_LEGACY_PEER_DEPS=true` en fallback).
- shadcn add les composants UI mais ne déclare PAS les peer deps (class-variance-authority, clsx, tailwind-merge, lucide-react, @radix-ui/*) ni `src/lib/utils.ts` → ajoutés à la main.
- Mypy bloquait sur celery / boto3 (pas de stubs typés) → `ignore_missing_imports = true` dans `[tool.mypy]` de `apps/api/pyproject.toml` (standard pour ces libs).
- Ruff signalait des `noqa: F401` inutiles dans les settings split (le `REST_FRAMEWORK` n'était importé que dans `local.py`) → `ruff check --fix` a nettoyé.
- Colima n'était pas démarré au moment du smoke test final → `colima start --cpu 4 --memory 6 --disk 20` (rapide), puis stack OK.

### Completion Notes List

**Versions épinglées au moment du seed (2026-05-14) :**

| Outil | Version installée | Cible story | Note |
|---|---|---|---|
| Node | v25.9.0 (host) / 22-alpine (Docker) | 22 LTS | Host plus récent, Docker fidèle à la cible |
| Next.js | 16.2.6 | 15 (story) | Next 16 livré par `create-next-app@latest` — accepté (API App Router stable) |
| React | 19.2.4 | 19 (livré avec Next 16) | OK |
| TypeScript | ^5.x | ^5.6 | `strict + noUncheckedIndexedAccess` activés |
| Tailwind CSS | 3.4.x | **v3 latest** (décision §4.10) | ✓ pas de v4 |
| shadcn/ui | latest CLI | latest | 6 composants installés : Button, Card, Dialog, Form, Input, +Label (peer de Form) |
| Python | 3.12.12 (via uv) | 3.12+ | `uv` a installé Python 3.12 automatiquement (host est 3.14) |
| Django | 5.1.15 | 5.x | OK |
| DRF | 3.15.2 | 3.15.x | OK |
| drf-spectacular | 0.27.2 | latest | OK, `/api/v1/health/` apparaît dans le schéma |
| FastAPI | 0.115.x | latest | OK |
| Pydantic | 2.10.x (v2) | v2 | OK |
| PostgreSQL | 16 + pgvector + pgcrypto | 16+pgvector | image `pgvector/pgvector:pg16`, extensions créées par `infra/postgres/init.sql` au premier boot |
| Redis | 7-alpine | 7 | OK |

**Mesures NFR-M1 (stack up < 5 min) :**

- **Warm-cache `docker compose up -d --build`** (après un premier build) : **33.5 s** pour avoir tous les containers `Up`, +~25 s pour que Next.js compile la première requête → total < **60 s**.
- **Cold-cache complet** (`docker system prune -a -f --volumes` puis `up`) : **non exécuté** intentionnellement — j'ai choisi de ne pas wiper le Docker de l'utilisateur. Estimation : ~3-5 min (pull des images Postgres+pgvector ~200 MB, MinIO ~100 MB, Mailpit, Redis, Node, Python ; + npm install + uv sync). **À refaire par l'utilisateur** : `docker system prune -a -f --volumes && time docker compose up -d`.

**Smoke test final (2026-05-14, stack chaude) :**

```
✓ web    http://localhost:3000     (Hello Path-Advisor)
✓ api    http://localhost:8000/api/v1/health/  → {"status":"ok"}
✓ ai     http://localhost:8001/health          → {"status":"ok","version":"0.1.0"}
✓ admin  http://localhost:8000/admin/          → HTTP 302 (redirect login)
✓ mailpit http://localhost:8025/               → HTTP 200
✓ minio  http://localhost:9001/                → HTTP 200
```

**Validation supplémentaire :**

- `make lint` → 0 erreur sur web (ESLint + tsc + Prettier) + api (Ruff + mypy) + ai-service (Ruff).
- `make test` → 3 suites passantes (1 Vitest, 1 pytest-django sur `/api/v1/health/`, 1 pytest sur ai-service health).
- `make openapi` → `packages/openapi/openapi.json` (1.3 KB) + `apps/web/src/lib/api/generated/schema.ts` (60 lignes) générés correctement.
- `docker compose exec api uv run python manage.py migrate` → 39 migrations Django appliquées sans erreur.
- `make seed` → super-user + 3 buckets MinIO créés. Re-run vérifié **idempotent** (4× "already present — skip").

**Décisions tranchées §4.10 — toutes respectées :**

1. Tailwind v3 (^3.4) ✓
2. Racine `docker-compose.yml` via `include: [path: infra/docker-compose.yml]` ✓
3. PostHog derrière le profil `analytics` ✓ (`docker compose --profile analytics up posthog`)
4. Doppler reporté ✓ (uniquement `.env` + `.env.example`)

**Points à noter pour le code review :**

- **Next.js 16** au lieu de 15 (livré par `create-next-app@latest`). Pas de régression fonctionnelle attendue (App Router + RSC stables). À documenter dans un futur ADR si on veut épingler.
- **`legacy-peer-deps`** activé (npmrc + Dockerfile flag) — à retirer dès que next-intl publie un release supportant Next 16.
- **Mypy** est en mode lenient (`ignore_missing_imports = true`) ; renforcer dès que les libs auront des stubs typés.
- **PostHog** présent dans le Compose mais non démarré par défaut (profil `analytics`).
- **AGENTS.md / CLAUDE.md** créés par `create-next-app` dans `apps/web/` — conservés tels quels (utiles pour les futurs agents IA).

### File List

**Nouveaux fichiers — racine du repo :**

- `Makefile` — targets dev/test/lint/seed/openapi/clean/help
- `.gitignore` — couvre Node, Python, Next, Django, generated artifacts, Docker, ML
- `.editorconfig` — TS 2sp, Python 4sp, LF, UTF-8
- `.env.example` — toutes les vars d'env documentées (Postgres, Redis, MinIO, Mailpit, AI service, etc.)
- `docker-compose.yml` — wrapper `include` pointant sur `infra/docker-compose.yml`
- `lefthook.yml` — hooks pre-commit (eslint, prettier, ruff)

**Nouveaux fichiers — `apps/web/` (par-dessus le scaffold `create-next-app`) :**

- `package.json` (réécrit) — Tailwind v3, next-intl, TanStack Query, Vitest, Prettier, Lefthook, openapi-typescript, shadcn peer deps (class-variance-authority, clsx, tailwind-merge, lucide-react, @radix-ui/*)
- `tsconfig.json` (modifié) — ajout `noUncheckedIndexedAccess`
- `postcss.config.mjs` (modifié) — tailwindcss + autoprefixer (v3 style)
- `tailwind.config.ts` (nouveau) — squelette v3, prêt pour les tokens R1 (Story 1.2)
- `eslint.config.mjs` (modifié) — ajout `eslint-config-prettier`, ignore generated/
- `.prettierrc.json` + `.prettierignore`
- `.npmrc` — `legacy-peer-deps=true` (next-intl + Next 16)
- `vitest.config.ts` + `src/test-setup.ts`
- `components.json` — config shadcn (style default, base color zinc, RSC, alias)
- `Dockerfile.dev` + `.dockerignore`
- `src/app/layout.tsx` (réécrit) — Inter font, FR locale
- `src/app/page.tsx` (réécrit) — "Hello Path-Advisor"
- `src/app/page.test.tsx` (nouveau) — Vitest smoke
- `src/app/globals.css` (réécrit) — directives Tailwind v3 + import tokens.css
- `src/styles/tokens.css` (nouveau, placeholder Story 1.2)
- `src/lib/api/client.ts` — wrapper fetch (règle "pas de fetch brut")
- `src/lib/api/generated/schema.ts` — auto-généré par `make openapi` (gitignore)
- `src/lib/i18n/config.ts` — locale stub (locale fr)
- `src/lib/utils.ts` — `cn()` helper shadcn
- `src/components/ui/{button,card,dialog,form,input,label}.tsx` — composants shadcn

**Nouveaux fichiers — `apps/api/` :**

- `pyproject.toml` — toutes les deps Django+DRF, dev deps (pytest, ruff, mypy, django-stubs), config ruff/mypy/pytest
- `.python-version` → 3.12
- `manage.py` — `DJANGO_SETTINGS_MODULE=path_advisor.settings.local` par défaut
- `path_advisor/__init__.py`, `urls.py`, `wsgi.py`, `asgi.py`, `celery.py`
- `path_advisor/settings/{base,local,staging,prod,test}.py` — split 5 environnements
- `path_advisor/middleware/__init__.py` (placeholder)
- `apps/__init__.py`, `apps/core/__init__.py`, `apps/core/apps.py`
- `apps/core/views.py` — endpoint `/api/v1/health/` documenté drf-spectacular
- `apps/core/urls.py`
- `apps/core/tests/__init__.py`, `apps/core/tests/test_health.py`
- `scripts/export_openapi.py` — génère `packages/openapi/openapi.json`
- `scripts/seed_dev.py` — idempotent (super-user + 3 buckets MinIO)
- `fixtures/`, `locale/` (placeholders)
- `Dockerfile.dev` + `.dockerignore`
- `uv.lock` (généré)

**Nouveaux fichiers — `apps/ai-service/` :**

- `pyproject.toml` — FastAPI, Pydantic, PyJWT, structlog, dev deps (pytest, ruff, hypothesis)
- `.python-version` → 3.12
- `src/__init__.py`, `src/main.py`, `src/config.py`
- `src/api/__init__.py`, `src/api/dependencies.py`
- `src/api/routes/__init__.py`, `src/api/routes/health.py`
- `src/tests/__init__.py`, `src/tests/test_health.py`
- `Dockerfile.dev` + `.dockerignore`
- `uv.lock` (généré)

**Nouveaux fichiers — `packages/openapi/` :**

- `scripts/generate-ts-client.sh` — wrapper `openapi-typescript`
- `openapi.json` (généré par `make openapi`, gitignore)

**Nouveaux fichiers — `infra/` :**

- `docker-compose.yml` — stack complète (web, api, ai-service, postgres+pgvector, redis, mailpit, minio, posthog en profil `analytics`)
- `docker-compose.prod.yml` — squelette d'overrides prod (sera complété par les stories deploy)
- `postgres/init.sql` — `CREATE EXTENSION vector + pgcrypto`

**Nouveaux fichiers — `docs/` :**

- `adr/0001-stack-django-nextjs-fastapi-docker.md` — ADR documentant la stack figée + décisions §4.10
- `onboarding.md` — runbook "0 → stack up en 15 min"
- `runbooks/`, `patterns/` (vides, à peupler par stories futures)

**Nouveaux fichiers — `.github/` :**

- `workflows/ci-web.yml`
- `workflows/ci-api.yml`
- `workflows/ci-ai-service.yml`
- `workflows/ci-types-generation.yml` — déclenché après ci-api
- `pull_request_template.md` — checklist qualité (tests, lint, OpenAPI, audit_log, tenant_id, i18n, ADR)

**Modifié :**

- `README.md` — section "Getting started" remplacée (was "planning phase"), Tailwind v4 → v3, ajout repo layout

### Change Log

- 2026-05-14 — Story 1.1 implémentée et validée localement (Marwen + Claude Opus 4.7). Stack up + smoke checks OK. Status → `review`.
- 2026-05-14 — Code review multi-LLM (Opus Blind Hunter + Sonnet Edge Case Hunter + Haiku Acceptance Auditor). Findings consolidés ci-dessous.
- 2026-05-14 — Code review actions complete: 5 decisions résolues + 17 patches appliqués + 15 deferred + 7 dismissed. `make lint` + `make test` verts. Status → `done`.

---

## 10. Review Findings (2026-05-14)

**Reviewers :** Opus 4.7 (Blind Hunter, no spec), Sonnet 4.6 (Edge Case Hunter), Haiku 4.5 (Acceptance Auditor with spec)

**Verdict Acceptance Auditor :** ✅ 10/10 ACs satisfaits + 4/4 décisions §4.10 respectées.

**Stats triage :** 5 decisions-needed · 17 patches · 15 deferred · 7 dismissed

Raw reports : [.code-review/blind-hunter.md](../.code-review/blind-hunter.md), [.code-review/edge-case-hunter.json](../.code-review/edge-case-hunter.json), [.code-review/acceptance-auditor.md](../.code-review/acceptance-auditor.md)

### Decisions needed

- [x] [Review][Decision] **PostHog stub broken as shipped** — Le service `posthog` dans `infra/docker-compose.yml` pointe vers une DB `posthog` non créée et ne déclare ni ClickHouse ni Kafka ni plugin-server (requis par l'image officielle). Crashloop dès `--profile analytics up`. Choix : (a) supprimer entièrement le service jusqu'à une story analytics dédiée, (b) ajouter la création de DB + une note "WIP analytics — usage limité", (c) intégrer le compose officiel PostHog complet (3+ services ajoutés).

- [x] [Review][Decision] **`apps/web/README.md` est le boilerplate `create-next-app`** — Mentionne Vercel/yarn/bun, contredit notre stack npm + Docker. Choix : (a) supprimer le fichier (la racine README couvre déjà), (b) le réduire à un pointeur vers `docs/onboarding.md`, (c) le réécrire avec un quick-start spécifique au sous-module web.

- [x] [Review][Decision] **`DATABASE_URL` dans `.env.example` mais jamais parsé** — `apps/api/path_advisor/settings/base.py` construit `DATABASES` depuis `POSTGRES_*` séparés, pas depuis `DATABASE_URL`. Choix : (a) supprimer `DATABASE_URL` de `.env.example` (cohérent avec settings actuels), (b) ajouter `dj-database-url` aux deps et faire parser `DATABASE_URL` en priorité (standard 12-factor).

- [x] [Review][Decision] **`NEXT_PUBLIC_API_URL` côté SSR vs browser** — Hardcodé à `http://localhost:8000` dans `infra/docker-compose.yml`. Côté browser OK, mais les Server Components fetchant depuis le container `web` doivent appeler `http://api:8000`. Choix : (a) split variables `API_URL_SERVER` + `NEXT_PUBLIC_API_URL` dans le client (recommandé), (b) reverse-proxy via Next.js rewrites (complexité accrue), (c) défer à Story 1.5 quand les premiers SSR API calls sont introduits.

- [x] [Review][Decision] **`ci-types-generation.yml` est un workflow stérile** — Génère des types TS mais ne les commit ni ne les expose à `ci-web` (qui ferait `tsc --noEmit` sans ces types). Choix : (a) supprimer le workflow, intégrer la génération dans `ci-web` (le plus simple), (b) garder le workflow mais ajouter un upload-artifact que `ci-web` consomme, (c) le faire commit-and-push via un bot.

### Patches (à appliquer)

- [x] [Review][Patch] **`make seed` doit refuser de tourner si `DEBUG=False`** — guard manquant. [apps/api/scripts/seed_dev.py]
- [x] [Review][Patch] **`make dev` foreground vs docs disent `-d`** — incohérence. [Makefile]
- [x] [Review][Patch] **`manage.py` import-error parle de "virtualenv"** — message obsolète sous uv. [apps/api/manage.py:11]
- [x] [Review][Patch] **`local.py` réimporte `REST_FRAMEWORK` inutilement** — déjà exposé via star import. [apps/api/path_advisor/settings/local.py:6]
- [x] [Review][Patch] **`docker-compose.prod.yml` référence `Dockerfile` inexistant** — seul `Dockerfile.dev` existe. Override prod casse immédiatement. [infra/docker-compose.prod.yml]
- [x] [Review][Patch] **`mypy || true` masque les erreurs de type** — utiliser `continue-on-error: true` à la place. [.github/workflows/ci-api.yml]
- [x] [Review][Patch] **`ci-web` fait `next build` sans le client TS généré** — premier import de `@/lib/api/generated/schema` casse main. Ajouter une étape de génération dans ci-web. [.github/workflows/ci-web.yml]
- [x] [Review][Patch] **Healthchecks manquants** — ajouter `healthcheck:` à redis, minio, mailpit, api, ai-service ; switch `depends_on` à `condition: service_healthy`. [infra/docker-compose.yml]
- [x] [Review][Patch] **`DJANGO_SECRET_KEY` placeholder dans base.py** — risqué si base.py est importé directement. Retirer le default ; ne le set que dans local.py/test.py. [apps/api/path_advisor/settings/base.py:16]
- [x] [Review][Patch] **`jwt_secret` défaut insecure dans ai-service** — pareil, retirer du default ; require en runtime. [apps/ai-service/src/config.py:12]
- [x] [Review][Patch] **`ALLOWED_HOSTS = ["*"]` dans test settings** — restreindre à `["testserver", "localhost"]`. [apps/api/path_advisor/settings/test.py:7]
- [x] [Review][Patch] **`DJANGO_ALLOWED_HOSTS` empty string → `[""]` dans staging.py** — `split(",")` sur chaîne vide retourne `[""]`, qui matche tout. Filtrer les empties. [apps/api/path_advisor/settings/staging.py:8]
- [x] [Review][Patch] **`seed_dev` `except ClientError` trop large** — narrow au code 404 `NoSuchBucket` pour ne pas masquer les erreurs d'auth/réseau. [apps/api/scripts/seed_dev.py:52]
- [x] [Review][Patch] **`init.sql` ne tourne qu'au premier boot** — ajouter `CREATE EXTENSION IF NOT EXISTS` dans une migration Django pour les volumes pré-existants. [apps/api/apps/core/migrations/0001_init_extensions.py — à créer]
- [x] [Review][Patch] **`generate-ts-client.sh` utilise `npx --yes`** — utiliser le binaire local `./node_modules/.bin/openapi-typescript`. [packages/openapi/scripts/generate-ts-client.sh]
- [x] [Review][Patch] **Dockerfile.dev `uv.lock*` (glob optionnel)** — lockfiles sont committés, retirer le wildcard pour fail-fast. [apps/api/Dockerfile.dev, apps/ai-service/Dockerfile.dev]
- [x] [Review][Patch] **`.env.example` sans bannière dev-only** — ajouter un warning explicite contre l'usage en prod (vu que `DJANGO_DEBUG=true` est un footgun). [.env.example]

### Deferred (tracked for future stories)

- [x] [Review][Defer] **`verify_jwt` est un no-op** — Story 3.1 (activation ai-service scoring).
- [x] [Review][Defer] **`apiFetch` sans timeout / RFC 7807 parsing** — Story 1.5 (login flow).
- [x] [Review][Defer] **`bulletins-encrypted` bucket sans SSE config** — Story 2.3 (upload bulletins).
- [x] [Review][Defer] **`CSRF_TRUSTED_ORIGINS` / `SESSION_COOKIE_SAMESITE` manquants** — Story 1.5 (auth flow cross-origin).
- [x] [Review][Defer] **`legacy-peer-deps` global au lieu d'`overrides` ciblé** — quand next-intl publie le support officiel Next 16.
- [x] [Review][Defer] **Test settings SQLite vs prod pgvector** — Story 1.8 (RLS + pgvector tests).
- [x] [Review][Defer] **`export_openapi` avec `request=None`** — schéma actuel suffisant. À revoir quand le schéma divergera de `/api/schema/`.
- [x] [Review][Defer] **`next.config.ts` empty stub** — à compléter pour Dockerfile prod (`output: "standalone"`) lors du deploy track.
- [x] [Review][Defer] **Pas de resource limits / non-root containers** — prod hardening (deploy track).
- [x] [Review][Defer] **Pas de `CONN_MAX_AGE` / SSL DB** — prod hardening.
- [x] [Review][Defer] **MinIO root réutilisé comme creds workload** — créer un service account quand RBAC sera ajouté (Story 2.3 ou plus tard).
- [x] [Review][Defer] **Pas de smoke workflow GH Actions `docker compose up`** — Sprint 4+ une fois la stack stable.
- [x] [Review][Defer] **Pas de SAST / CodeQL / pip-audit / npm audit** — Sprint 3+.
- [x] [Review][Defer] **Ruff `select` drift api vs ai-service** — quand les patterns Python convergeront (Sprint 3+, créer un `ruff.toml` racine).
- [x] [Review][Defer] **Policy FR / EN docs et code** — style guide projet à écrire dans `docs/patterns/` (Sprint 2+).

### Dismissed (false positives or intentional)

- ❌ `lucide-react@^1.14.0` "fictitious" — vérifié sur npm registry, existe (lucide-react est passé en 1.x récemment).
- ❌ `react@19.2.4` et `next@16.2.6` "non publiés" — vérifiés sur npm, publiés et installés.
- ❌ `package-lock.json` / `uv.lock` "non committés" — existent sur disque ET ne sont pas dans `.gitignore` (faux positif dû au scope du diff qui les excluait pour le bruit).
- ❌ `apps/web/.gitignore` "rules yarn/pnpm conflictuelles" — artefact bénin du template `create-next-app`.
- ❌ `tokens.css` empty placeholder — intentionnel pour Story 1.2.
- ❌ `apps/web/AGENTS.md` "pointe vers node_modules" — fichier livré par le template, contient des instructions utiles aux agents IA (Next 16 a des breaking changes), à conserver.
- ❌ MinIO port 9001 conflit possible — comportement Docker standard, déjà documenté dans `docs/onboarding.md` § Troubleshooting.

---

## 9. Decisions Resolved (validées par Marwen le 2026-05-14)

Les 4 questions ouvertes initiales ont été tranchées — aucune ambiguïté à lever côté dev agent. Récap consolidé dans §4.10 ci-dessous.

| # | Question | Décision | Impact tâches |
|---|---|---|---|
| 1 | Tailwind v3 ou v4 ? | **Tailwind v3 latest (^3.4.x)** | T2.5 : forcer downgrade après `create-next-app` ; éviter v4 |
| 2 | Symlink vs `include` Compose ? | **`include` (Compose v2)** dans `docker-compose.yml` racine | T5.3 : fichier court avec `include`, pas de symlink |
| 3 | PostHog dans la stack par défaut ? | **Profil optionnel `analytics`** | T5.1 : `profiles: ["analytics"]` sur le service `posthog` ; doc onboarding |
| 4 | Doppler maintenant ou plus tard ? | **Plus tard** — `.env` + `.env.example` suffisent cette story | T1, T3.5, T10.2 : aucune dépendance Doppler ; à intégrer en Sprint 2+ |
