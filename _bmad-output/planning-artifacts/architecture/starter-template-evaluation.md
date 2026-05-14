# Starter Template Evaluation

## Primary Technology Domain

**Web full-stack hybride** — Next.js front + Django back + service IA Python séparé. Tous les composants serveur sont en Python (back + IA), le front est en TypeScript. Le contrat entre Next.js et Django passe par OpenAPI auto-généré.

## Options évaluées

| Option | Description | Verdict |
|---|---|---|
| ~~T3 Stack (Node.js)~~ | Next.js + tRPC + Prisma | ❌ Écarté — Node.js multiplie les langages serveur (TS back + Python IA) |
| **Django + DRF + Next.js (retenu)** | Django 5 batteries-included pour le back, DRF pour API, OpenAPI auto, Next.js pour front SSR | ✅ Recommandé |
| Django Ninja + Next.js | Plus moderne que DRF (type-hints, FastAPI-like) mais écosystème plus petit | Considéré |
| Django full-stack (templates + HTMX) | 1 seul stack mais interactivité graphe parcours limitée | Écarté — UX graphe trop limitée |

## Stack retenue : Django 5 + DRF + Next.js + FastAPI (AI service)

**Pourquoi ce mix pour Path-Advisor :**

1. **Python pour tout le serveur** — back + IA dans le même langage = pas de jonglage mental pour 1-2 personnes
2. **Django batteries-included** — le back-office admin gratuit couvre déjà 80 % des FR48–FR52 (CRUD référentiel, modération signalements). L'auth, les permissions, les migrations, le middleware sont matures et testés
3. **DRF + drf-spectacular** — OpenAPI auto-généré depuis les ViewSets DRF, schéma toujours à jour avec le code
4. **Next.js front** — gardé pour le SSR SEO + interactivité du graphe de parcours (Core Web Vitals au vert)
5. **Type-safety end-to-end** — TS client auto-généré depuis OpenAPI (via `openapi-typescript` ou Orval) → les types front sont toujours alignés avec les schémas back
6. **AI service Python séparé** — FastAPI minimaliste, scaling indépendant, versioning des modèles via MLflow

## Structure de projet recommandée

```
path-advisor/
├── apps/
│   ├── web/                          # Next.js (front uniquement)
│   │   ├── src/
│   │   │   ├── app/                  # App Router (SSR + RSC)
│   │   │   ├── components/           # shadcn/ui + custom
│   │   │   ├── lib/
│   │   │   │   ├── api/              # Client TS auto-généré depuis OpenAPI
│   │   │   │   └── i18n/             # next-intl config
│   │   │   └── styles/
│   │   └── package.json
│   │
│   ├── api/                          # Django + DRF (back principal)
│   │   ├── path_advisor/             # Django project settings
│   │   │   ├── settings/
│   │   │   │   ├── base.py
│   │   │   │   ├── local.py
│   │   │   │   └── prod.py
│   │   │   └── urls.py
│   │   ├── apps/                     # Django apps par zone de capacités (FRs A–H)
│   │   │   ├── accounts/             # FR1–FR12 (Auth, RBAC, RGPD)
│   │   │   ├── profiles/             # FR13–FR19 (Profil + OCR)
│   │   │   ├── recommendations/      # FR20–FR26 (Vocationnel, proxy vers ai-service)
│   │   │   ├── pathways/             # FR27–FR32 (Graphe parcours + stats)
│   │   │   ├── outreach/             # FR33–FR40 (Envoi anticipé)
│   │   │   ├── schools/              # FR36–FR40 (Espace école)
│   │   │   ├── counselors/           # FR43–FR45 (B2B conseillers)
│   │   │   ├── parents/              # FR41–FR42 (Espace parent)
│   │   │   ├── moderation/           # FR48–FR52 (Admin + modération)
│   │   │   ├── audit/                # Cross-cutting : journal audit
│   │   │   └── core/                 # Cross-cutting : RBAC, tenant, helpers
│   │   ├── manage.py
│   │   └── pyproject.toml
│   │
│   └── ai-service/                   # FastAPI (modèles IA)
│       ├── src/
│       │   ├── api/                  # Endpoints scoring + embeddings
│       │   ├── models/               # Modèles ML versionnés
│       │   ├── pipelines/            # Pipelines d'entraînement
│       │   ├── evaluation/           # Métriques + audit biais
│       │   └── nlp/                  # NLP appréciations enseignants
│       └── pyproject.toml
│
├── packages/
│   └── openapi/                      # Schéma OpenAPI exporté + scripts génération client TS
│
├── infra/
│   ├── docker-compose.yml            # Stack locale complète
│   ├── docker-compose.prod.yml       # Overrides production
│   └── nginx/                        # Reverse proxy local (optionnel)
│
├── docs/
│   └── adr/                          # Architecture Decision Records
│
└── README.md
```

## Commandes d'initialisation

```bash
# 1. Initialiser le repo
mkdir path-advisor && cd path-advisor
git init

# 2. Initialiser la web app Next.js
npx create-next-app@latest apps/web \
  --typescript \
  --tailwind \
  --app \
  --src-dir \
  --import-alias "@/*" \
  --no-git \
  --eslint

# 2b. Ajouter shadcn/ui + next-intl + tanstack-query
cd apps/web
npx shadcn@latest init
npm install next-intl @tanstack/react-query @tanstack/react-query-devtools openapi-typescript zod
cd ../..

# 3. Initialiser le back Django avec uv
mkdir -p apps/api && cd apps/api
uv init --package
uv add django djangorestframework drf-spectacular django-cors-headers
uv add django-allauth django-otp           # auth + MFA
uv add celery redis django-celery-beat     # job queue async
uv add django-storages boto3               # S3/MinIO storage
uv add psycopg[binary]                     # PostgreSQL driver
uv add django-pgvector                     # pgvector via Django
uv add pillow                              # image processing pour bulletins
uv add structlog                           # logs structurés
uv add sentry-sdk                          # error tracking
uv add --dev pytest pytest-django factory_boy ruff black mypy django-stubs
uv run django-admin startproject path_advisor .
cd ../..

# 4. Initialiser le service IA FastAPI
mkdir -p apps/ai-service && cd apps/ai-service
uv init --package
uv add fastapi uvicorn pydantic-settings
uv add scikit-learn sentence-transformers
uv add asyncpg pgvector                    # accès direct DB pour embeddings
uv add mlflow                              # versioning expérimentations
uv add structlog opentelemetry-api opentelemetry-sdk
uv add --dev pytest pytest-asyncio hypothesis httpx ruff black
cd ../..

# 5. Vérifier en local
docker-compose -f infra/docker-compose.yml up
```

**Note :** vérifier les versions courantes au moment de l'init via `npm view next version`, `uv pip show django`, etc.

## Architectural Decisions Provided by Starter

**Language & Runtime :**
- **TypeScript strict** pour `apps/web` (Next.js)
- **Python 3.12+** pour `apps/api` et `apps/ai-service`
- **Node.js LTS** uniquement pour la phase build front (pas en runtime serveur)

**Styling Solution :**
- Tailwind CSS + shadcn/ui (composants copiés dans le projet) — contrôle total, AI-friendly, RGAA AA atteignable

**Build & Dev Tooling :**
- Front : Next.js Turbopack (dev) + SWC (prod)
- Back / AI : `uv` (gestionnaire de dépendances moderne, ultra rapide)
- Linting : ESLint + Prettier (TS) / Ruff + Black + mypy (Python)
- Pre-commit hooks via Lefthook (multi-langue)

**Testing Framework :**
- Front : Vitest (unit) + Playwright (e2e parcours critiques)
- Back : pytest-django + factory_boy (fixtures)
- AI : pytest + hypothesis (property-based pour audit biais)

**Code Organization :**
- Next.js App Router avec composants serveur (RSC) par défaut, "use client" uniquement où nécessaire
- Django apps par **zone de capacités** (mapping direct aux 8 zones FR A–H du PRD) — facilite la traçabilité PRD → code
- Service IA structuré par responsabilité : routes API / modèles / pipelines / évaluation

**Communication front ↔ back :**
- Schéma OpenAPI auto-généré par drf-spectacular depuis Django
- Client TS auto-généré par `openapi-typescript` au build (CI)
- TanStack Query pour le data fetching côté front (cache + retry + invalidation)

## Briques explicitement ajoutées au-delà du starter

| Brique | Choix | Justification |
|---|---|---|
| **Auth** | django-allauth + dj-rest-auth + django-otp | Auth + MFA + magic links + email verification natifs |
| **Multi-tenant** | Approche custom : `tenant_id` sur modèles sensibles + PostgreSQL RLS + middleware Django pour injection contexte | Tenancy hybride MVP |
| **Job queue** | Celery + Redis | Standard Python, mature, scaling clair |
| **Email transactionnel** | Django `EmailBackend` configurable (Mailpit dev / Postmark prod) | NFR-I2 |
| **OCR** | Service séparé wrappant Tesseract (dev) / Mindee (prod) | NFR-I3 |
| **Stockage objets** | django-storages + boto3 endpoint configurable (MinIO local, S3 prod) | NFR-I1, NFR-S3 |
| **Observabilité** | Sentry (errors) + OpenTelemetry → Grafana Cloud / Tempo + structlog | Multi-langue (TS + Python) |
| **Analytics produit** | PostHog (self-hosted dev, Cloud EU prod) | NFR-I4 |
| **Validation schémas** | Pydantic v2 (back + AI) + Zod (front) | Validation cross-stack |
| **i18n** | next-intl côté front + django.utils.translation côté back | NFR cross-cutting n°8 |
| **CSRF** | django.middleware.csrf + tokens injectés dans Next.js | Sécurité OWASP |
| **Rate limiting** | django-ratelimit | Anti-abus envoi anticipé |

## Service IA Python — briques

| Brique | Choix |
|---|---|
| Framework web | FastAPI + Pydantic v2 |
| ML statistique | scikit-learn |
| Embeddings | sentence-transformers (CamemBERT FR ou MiniLM multilingue) |
| NLP appréciations | spaCy (FR) + Mistral 7B local via Ollama pour dev, OpenAI/Mistral API en prod |
| Vector store | pgvector (réutilise PostgreSQL principal — pas de DB supplémentaire à opérer) |
| Tracking expérimentations | MLflow self-hosted (versioning modèles + métriques + dataset hashes) |
| Tests | pytest + hypothesis (property-based pour audit biais) |

**Note :** initialiser le projet complet (Next.js + Django + FastAPI + Docker Compose + ADR initial) doit être la **première story d'implémentation** — sprint 1 du PRD.
