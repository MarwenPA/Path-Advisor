---
stepsCompleted: ["step-01-init", "step-02-context", "step-03-starter", "step-04-decisions", "step-05-patterns", "step-06-structure", "step-07-validation", "step-08-complete"]
lastStep: 8
status: 'complete'
completedAt: '2026-05-13'
inputDocuments:
  - "prd.md"
  - "product-brief-Path-Advisor.md"
workflowType: 'architecture'
project_name: 'Path-Advisor'
user_name: 'Marwen'
date: '2026-05-13'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements — 52 FRs MVP + 5 FRs Fast-Follow** organisés en 8 zones de capacités :

| Zone | FRs | Implications architecturales clés |
|---|---|---|
| **A. Comptes, Rôles & Conformité** | FR1–FR12 (12 FRs) | Auth multi-rôle, RBAC 6 rôles, isolation multi-tenant, journal d'audit immuable, droits RGPD (export, suppression) |
| **B. Profil Élève & Onboarding** | FR13–FR19 (7 FRs) | OCR PDF + saisie manuelle assistée + stockage sécurisé bulletins, profil incrémental avec score de complétude |
| **C. Recommandation Vocationnelle** | FR20–FR26 (7 FRs) | Service IA séparé, scoring + explicabilité (RGPD art. 22), revue humaine, adaptation niveau scolaire |
| **D. Recommandation Parcours & Stats** | FR27–FR32 (6 FRs) | Graphe interactif côté front, moteur de prédiction admission basé open data Parcoursup, filtrage géographique/coût |
| **E. Envoi Anticipé & Espace École** | FR33–FR40 (8 FRs) | Workflow asynchrone biface, notification email/push, mise à jour stat sous 5 min, espace école isolé |
| **F. Espaces Tiers (Parent + Conseiller B2B)** | FR41–FR45 (5 FRs) | Liaisons inter-comptes avec consentement, vue restreinte par rôle, dashboard cohorte agrégé, exports |
| **G. Découverte & Engagement** | FR46–FR47 (2 FRs) | SSR pour SEO, sitemap, Schema.org, email transactionnel |
| **H. Administration & Modération** | FR48–FR52 (5 FRs) | Back-office CRUD référentiel, modération signalements/contenu, versioning modèles IA, métriques drift |

**Non-Functional Requirements — 7 catégories** dont 3 dominantes :

- **NFR-SC1–NFR-SC6 (Scalability)** : 500 MAU MVP → 10K growth, 500 concurrents sur pics saisonniers, auto-scaling x3 en < 10 min — **architecture doit prévoir scaling horizontal du service IA dès le départ**
- **NFR-S1–NFR-S9 (Security)** : chiffrement AES-256/TLS 1.3, MFA staff, journal audit immuable 3 ans, DPIA, RGPD < 72h CNIL — **sécurité by design, pas en couche tardive**
- **NFR-P1–NFR-P6 (Performance)** : reco vocationnelle < 3s P95 MVP, mises à jour stats < 5 min, TTFB SEO < 1s — **séparation service IA + cache stratégique nécessaires**

**Scale & Complexity :**

| Dimension | Évaluation |
|---|---|
| **Domaine technique primaire** | Full-stack web (front SSR + back API + service IA + queue async) |
| **Niveau de complexité** | **Medium-élevé** — multi-tenant, RBAC 6 rôles, service IA dédié, biface (élève ↔ école), conformité RGPD mineurs |
| **Composants architecturaux estimés** | ~8 modules logiques : Web (front), API (back), AI Service, Job Queue, OCR Service, Auth/RBAC, Data Layer (DB + cache + S3), Observability |
| **Cross-cutting concerns** | Auth & RBAC, audit trail, multi-tenant isolation, RGPD/consentement, observabilité, explicabilité IA, internationalisation (préparée pour francophonie) |

### Technical Constraints & Dependencies

**Contraintes structurelles (héritées du PRD) :**

1. **Hébergement UE obligatoire** (RGPD) — France ou UE, cible SecNumCloud en growth → AWS Paris/Frankfurt, Scaleway FR, OVH FR
2. **PoC local-first** (NFR-M1) — toute la stack lance en `docker-compose up < 5 min` → contraintes sur les choix d'intégration (Tesseract OCR au lieu de Textract en dev, Mailpit au lieu de SendGrid, PostHog self-hosted, MinIO au lieu de S3)
3. **Équipe 1-2 personnes** — favoriser monolithe modulaire vs microservices, stack connue de l'équipe, dev assisté IA intensif
4. **Multi-tenant hybride dès MVP** — Row-Level Security PostgreSQL obligatoire, tests d'isolation cross-tenant en CI
5. **Service IA séparé** — Python (FastAPI ou équivalent), scaling indépendant, versioning des modèles
6. **Pas de WebSocket en MVP** — asynchronisme via job queue (BullMQ/Sidekiq/Celery) + notifications email/push standard
7. **Stack frontend imposée** — SPA + SSR hybride (Next.js ou Nuxt) pour combiner SEO B2C et interactivité

**Dépendances externes obligatoires :**

| Dépendance | Production | PoC local | Critique |
|---|---|---|---|
| Stripe | API live | Sandbox local | Oui |
| OCR | Textract / Mindee | Tesseract Docker | Oui |
| Email | Postmark / SendGrid | Mailpit | Oui |
| Stockage objets | S3 EU | MinIO | Oui |
| Analytics | PostHog Cloud EU | PostHog self-hosted | Oui |
| Open data Parcoursup | CSV annuel MENJS | CSV fixture | Oui |
| Visio | Lien Whereby | Lien Jitsi | Souhaitable |

**Dépendances réglementaires :**

- **RGPD** + **Loi Informatique et Libertés** (CNIL) + **AI Act UE** (art. 22)
- **RGAA 4.1 niveau AA** sur parcours critiques en MVP
- **DPO** désigné (mutualisé externalisé) + **DPIA** avant production

### Cross-Cutting Concerns Identified

Concerns qui touchent plusieurs modules et requièrent des décisions transverses :

1. **Authentification & RBAC** — touche tous les modules, doit être centralisé (middleware/library partagée)
2. **Multi-tenant isolation** — tenant_id + user_id sur toutes les tables sensibles, RLS PostgreSQL, tests d'isolation en CI obligatoires
3. **Audit trail immuable** — journal de tous les accès aux données personnelles, append-only, conservation 3 ans → décision : table dédiée + write-only access + export régulier
4. **Versioning des modèles IA** — chaque déploiement de modèle versionné avec dataset + hyperparamètres + métriques d'éval, audit trail des décisions
5. **Explicabilité IA** — chaque score doit pouvoir être expliqué (signaux contributifs visibles) — implication forte sur le choix de techniques ML (favoriser modèles intrinsèquement interprétables au top niveau)
6. **Consentement granulaire** — par tiers (parent, conseiller, école), révocable, tracé — modèle de données dédié
7. **Saisonnalité forte (janvier-mars / mai-juillet)** — auto-scaling sur métriques de charge, capacity planning avant pic
8. **Internationalisation francophone** — i18n du jour 1 pour préparer Belgique/Maroc en growth (clés de traduction structurées, pas de strings hardcodés)
9. **Observabilité production** — logs centralisés + métriques + alerting + tracing, MTTR < 1h
10. **Mode dégradé** — chaque service tiers doit avoir un fallback (OCR → manuel, Stripe → file d'attente, email → retry async)
11. **Continuité local ↔ cloud** — interfaces abstraites (Hexagonal/Ports & Adapters) pour permettre PoC local et prod cloud avec mêmes contrats

## Starter Template Evaluation

### Primary Technology Domain

**Web full-stack hybride** — Next.js front + Django back + service IA Python séparé. Tous les composants serveur sont en Python (back + IA), le front est en TypeScript. Le contrat entre Next.js et Django passe par OpenAPI auto-généré.

### Options évaluées

| Option | Description | Verdict |
|---|---|---|
| ~~T3 Stack (Node.js)~~ | Next.js + tRPC + Prisma | ❌ Écarté — Node.js multiplie les langages serveur (TS back + Python IA) |
| **Django + DRF + Next.js (retenu)** | Django 5 batteries-included pour le back, DRF pour API, OpenAPI auto, Next.js pour front SSR | ✅ Recommandé |
| Django Ninja + Next.js | Plus moderne que DRF (type-hints, FastAPI-like) mais écosystème plus petit | Considéré |
| Django full-stack (templates + HTMX) | 1 seul stack mais interactivité graphe parcours limitée | Écarté — UX graphe trop limitée |

### Stack retenue : Django 5 + DRF + Next.js + FastAPI (AI service)

**Pourquoi ce mix pour Path-Advisor :**

1. **Python pour tout le serveur** — back + IA dans le même langage = pas de jonglage mental pour 1-2 personnes
2. **Django batteries-included** — le back-office admin gratuit couvre déjà 80 % des FR48–FR52 (CRUD référentiel, modération signalements). L'auth, les permissions, les migrations, le middleware sont matures et testés
3. **DRF + drf-spectacular** — OpenAPI auto-généré depuis les ViewSets DRF, schéma toujours à jour avec le code
4. **Next.js front** — gardé pour le SSR SEO + interactivité du graphe de parcours (Core Web Vitals au vert)
5. **Type-safety end-to-end** — TS client auto-généré depuis OpenAPI (via `openapi-typescript` ou Orval) → les types front sont toujours alignés avec les schémas back
6. **AI service Python séparé** — FastAPI minimaliste, scaling indépendant, versioning des modèles via MLflow

### Structure de projet recommandée

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

### Commandes d'initialisation

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

### Architectural Decisions Provided by Starter

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

### Briques explicitement ajoutées au-delà du starter

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

### Service IA Python — briques

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

## Core Architectural Decisions

### Decision Priority Analysis

**Already decided (locked) :**
- Stack : Next.js + Django + FastAPI (Python 3.12, TS strict, PostgreSQL + pgvector, Redis, MinIO/S3, Celery, Tailwind + shadcn/ui)
- Auth : django-allauth + dj-rest-auth + django-otp (MFA)
- Multi-tenant : hybride (data partagée + tenant_id + user_id)
- Hébergement : France/UE (SecNumCloud growth)
- OpenAPI auto-généré (drf-spectacular)

**Critical decisions tranchées (bloquantes implémentation) :**
- Pattern d'isolation multi-tenant exact : middleware Django custom + PostgreSQL RLS
- Type de token auth front↔back : session cookie httpOnly SameSite=Lax
- Hébergeur production : Scaleway (France)
- Container orchestration MVP : Docker Compose sur 1 VM + Caddy
- Bibliothèque rendu graphe de parcours : React Flow (`@xyflow/react`)

**Important decisions tranchées (forment l'architecture) :**
- Stratégie cache Redis : sessions + rate limiting + reco TTL 1h + pages SSR TTL 5min
- Format audit log : table dédiée append-only avec trigger immuable
- Communication Django ↔ AI service : hybride sync HTTP + async Celery
- Versioning API : URL `/api/v1/...`
- Soft-delete par défaut + hard-delete RGPD sous 30 jours

### Data Architecture

| Décision | Choix | Rationale |
|---|---|---|
| **Multi-tenant pattern** | Middleware Django custom + PostgreSQL RLS (pas django-tenants) | django-tenants force schema-per-tenant ; middleware + RLS = tenancy hybride exacte, isolation forte, simple à opérer |
| **Migrations** | Django migrations natifs + revue manuelle pour migrations destructives | Standard Django |
| **Audit log** | Table `audit_log` append-only : `actor_id`, `tenant_id`, `subject_id`, `action`, `metadata` (JSONB), `created_at` immuable (trigger PostgreSQL bloquant UPDATE/DELETE) + export S3 mensuel | RGPD + traçabilité, immutabilité au niveau DB |
| **Soft delete vs hard delete** | Hybride : soft delete par défaut (`deleted_at`) ; hard delete sous 30 jours sur demande RGPD (FR11) via job Celery planifié | RGPD : hard delete obligatoire ; soft delete utile pour ops |
| **Cache strategy** | Redis : sessions + rate limiting + cache reco (TTL 1h) + cache pages SSR Next.js (TTL 5min) | Multi-usage = 1 service à opérer |
| **Vector embeddings** | pgvector dans la DB principale | NFR : minimiser services à opérer |
| **Champ chiffré** | Bulletins chiffrés S3 (SSE) + `django-cryptography` (column-level AES-256) sur PII sensibles | Défense en profondeur |

### Authentication & Security

| Décision | Choix | Rationale |
|---|---|---|
| **Token type front↔back** | Session cookie httpOnly SameSite=Lax (pas JWT) | Stateful, révocation immédiate, plus simple, plus sécurisé pour browser app |
| **CSRF** | Token CSRF Django, injecté dans Next.js via cookie `csrftoken` + header `X-CSRFToken` | Standard Django |
| **MFA** | TOTP en MVP (django-otp) obligatoire pour conseiller/école/admin, optionnel B2C ; WebAuthn en growth pour admin | TOTP couvre 95 %, WebAuthn pour rôles très sensibles plus tard |
| **Encryption at rest** | AES-256 disk-level (cloud) + column-level (`django-cryptography`) sur PII sensibles | Défense en profondeur, NFR-S1 |
| **Token Django ↔ FastAPI** | JWT signé HS256, clé partagée, TTL 5 min, généré par Django à chaque appel | Service-to-service simple |
| **Rate limiting** | django-ratelimit : 100 req/min global IP, 10 req/min user authentifié sur endpoints sensibles | Anti-abus MVP |
| **Secrets** | Doppler (sync local + CI + prod) ou `.env` chiffré sops/age | Solo-friendly, gratuit |

### API & Communication Patterns

| Décision | Choix | Rationale |
|---|---|---|
| **API design** | REST avec DRF ViewSets + serializers | Standard, AI-friendly, OpenAPI auto |
| **API versioning** | URL : `/api/v1/...` | Explicite, simple côté ops |
| **Format erreur** | RFC 7807 Problem Details (`application/problem+json`) | Standard structuré, multilingue |
| **Communication Django ↔ AI service** | Hybride : sync HTTP pour scoring on-demand (`POST /score`) ; async Celery pour batch (réentraînement, recalcul cohorte) | Latence < 3s exige sync ; jobs lourds → async |
| **Schéma OpenAPI** | drf-spectacular autogen, exporté en CI, consommé par `openapi-typescript` front | Type-safety end-to-end |
| **Pagination** | Cursor-based (`CursorPagination` DRF) sur listes longues | Performance sur gros jeux |
| **Filtering** | `django-filter` + serializers DRF | Standard, AI-friendly |
| **Webhooks** | Pas en MVP. En growth : HMAC signés pour écoles partenaires | Reporté |

### Frontend Architecture

| Décision | Choix | Rationale |
|---|---|---|
| **Composants par défaut** | Server Components first (App Router) ; "use client" uniquement pour interactions | Performance SEO + moins de JS livré |
| **State management** | TanStack Query (data) + Zustand (UI complexe : multi-step onboarding) ; pas de Redux | Minimaliste solo, AI-friendly |
| **Formulaires** | React Hook Form + Zod (validation schéma partagé via OpenAPI types) | Standard moderne, accessible, perf |
| **Date handling** | `date-fns` (immutable, tree-shakable, i18n FR) | Plus léger que Moment, plus mature que Temporal |
| **Rendu graphe parcours** | React Flow (`@xyflow/react`) — interactif, zoom, drag, custom nodes, accessibilité native | Le plus mature pour RGAA AA |
| **Animations** | Tailwind `transition-*` + Framer Motion uniquement pour aha moments | Économe bundle |
| **Bundle optimization** | Code splitting natif + dynamic imports (React Flow, Stripe Elements) | LCP mobile < 2,5s (NFR-P3) |
| **i18n** | `next-intl` avec routing locale (`/fr/...` par défaut) | NFR cross-cutting n°8 |

### Infrastructure & Deployment

| Décision | Choix | Rationale |
|---|---|---|
| **Hébergeur production** | Scaleway (Paris) — support FR, prix solo-friendly, roadmap SecNumCloud | Souveraineté FR = argument B2B EN |
| **Container orchestration MVP** | Docker Compose sur 1 VM (Scaleway DEV1) + Caddy (HTTPS auto Let's Encrypt) | Solo : pas de K8s, simplicité |
| **Hosting services** | 1 VM Scaleway MVP : web + api + ai-service + PostgreSQL + Redis + MinIO. Migration vers managés en growth (RDS, ElastiCache) | Coût ~30 €/mois MVP |
| **CI/CD** | GitHub Actions — tests + build + lint + déploiement SSH | Free tier généreux, AI-friendly |
| **Deployment strategy** | Rolling docker-compose (down → pull → up) en MVP ; blue-green Caddy en growth | Simple MVP, robuste growth |
| **Secrets management** | Doppler (sync local + CI + prod) | Solo-friendly, gratuit < 5 users |
| **Domains & DNS** | Cloudflare DNS (free) + DDoS + CDN assets | Standard, gratuit, performance |
| **Backups** | `pg_dump` quotidien vers S3 (région différente), rétention 30j, test mensuel restauration | NFR-R2 |
| **Monitoring stack** | Sentry (errors) + Better Stack/Grafana Cloud (logs+métriques) + UptimeRobot (uptime checks) + alertes Slack/email | MTTR < 1h (NFR-R5) |
| **Tracing distribué** | OpenTelemetry → Grafana Tempo (self-hosted MVP, Grafana Cloud growth) | Multi-langue, standard ouvert |
| **Environments** | 3 : local (Docker Compose), staging (VM séparée, données fictives), production (VM dédiée) | Standard solo |

### Decision Impact Analysis

**Implementation Sequence :**

1. **Sprint 1 (fondations)** : VM Scaleway provisionnée, Docker Compose local + prod, CI GitHub Actions, secrets Doppler, schéma DB PostgreSQL avec RLS, middleware multi-tenant Django, audit log table immuable
2. **Sprint 2 (auth + sécurité)** : django-allauth, django-otp MFA, session cookies, CSRF, JWT service-to-service Django↔FastAPI
3. **Sprint 3 (profil)** : modèles élève/bulletin, upload S3/MinIO chiffré, OCR via service abstrait
4. **Sprint 4-5 (moteurs IA)** : service FastAPI avec endpoints scoring + embeddings, intégration Celery pour batch
5. **Sprints suivants** : features métier par capability area FRs A–H

**Cross-Component Dependencies :**
- Session cookie + CSRF + Next.js → exige que web et api soient sur le même domaine (ex : `api.path-advisor.fr` + `path-advisor.fr` avec cookie scope `.path-advisor.fr`) OU CORS configuré avec credentials
- Multi-tenant middleware doit être chargé AVANT tout autre middleware métier
- Audit log doit être appelé par décorateur transversal sur toutes les vues sensibles
- React Flow ne peut être SSR'd → wrappé dans Client Component avec dynamic import
- pgvector exige PostgreSQL ≥ 13 avec extension activée → migration en sprint 1

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified :** 9 zones où des agents IA pourraient diverger (naming Python vs TS, format API, organisation fichiers, gestion erreurs, etc.).

### Naming Patterns

**Database Naming (PostgreSQL — Django defaults) :**
- Tables : `snake_case` + pluriel → `students`, `recommendations`, `audit_logs`
- Colonnes : `snake_case` → `tenant_id`, `created_at`, `parental_consent_verified_at`
- Foreign keys : `<entity>_id` → `student_id`, `school_id`
- Index : `idx_<table>_<columns>` → `idx_students_tenant_id`, `idx_audit_logs_actor_id_created_at`
- Booléens : préfixe `is_` ou `has_` ou `_at` pour timestamps optionnels → `is_premium`, `has_completed_onboarding`, `deleted_at`
- Enums Django : `TextChoices` avec valeurs `SCREAMING_SNAKE_CASE` → `EducationLevel.HIGH_SCHOOL_GENERAL`

**API Naming (DRF — convention REST) :**
- Endpoints : kebab-case pluriel → `/api/v1/students`, `/api/v1/early-outreach-requests`, `/api/v1/recommendations/{id}/explainability`
- Path params : `{id}` style (OpenAPI standard) → `/api/v1/students/{student_id}/profile`
- Query params : `snake_case` → `?tenant_id=...&order_by=created_at`
- Headers custom : `X-` prefix + Title-Case → `X-Tenant-Id`, `X-Request-Id`
- Verbes HTTP : strictement REST (GET liste/détail, POST création, PATCH modif partielle, PUT remplacement complet rare, DELETE)

**JSON field naming (cross-cutting critique) :**
- `snake_case` partout (côté Django ET côté JSON exposé ET côté types TS générés) — pas de conversion camelCase
- Rationale : un seul format end-to-end, lisible dans logs, OpenAPI conforme, évite les bugs de mapping

**Code Naming :**

| Contexte | Convention | Exemple |
|---|---|---|
| Python classes | `PascalCase` | `class StudentProfile`, `class EarlyOutreachService` |
| Python fonctions | `snake_case` | `def calculate_admission_score()` |
| Python variables | `snake_case` | `student_id`, `recommendations_list` |
| Python constantes | `SCREAMING_SNAKE_CASE` | `MAX_BULLETIN_FILE_SIZE = 10 * 1024 * 1024` |
| TS composants React | `PascalCase` | `StudentProfileCard`, `RecommendationGraph` |
| TS fichiers composants | `kebab-case` | `student-profile-card.tsx`, `recommendation-graph.tsx` |
| TS fonctions/hooks | `camelCase` (préfixe `use` pour hooks) | `formatBulletinDate`, `useStudentProfile` |
| TS types/interfaces | `PascalCase` (pas de préfixe `I`) | `interface StudentProfile`, `type RecommendationScore` |
| TS variables | `camelCase` | `studentId`, `recommendationsList` |
| CSS classes (Tailwind) | utility-first, pas de classes custom sauf composants shadcn | `flex items-center gap-2` |

### Structure Patterns

**Project Organization (mapping FRs A–H) :**

Django apps par zone de capacité du PRD (pas par couche technique) :

```
apps/api/apps/
├── accounts/          # FR1–FR12 — Auth, RBAC, RGPD
├── profiles/          # FR13–FR19 — Profil élève, bulletins
├── recommendations/   # FR20–FR26 — Vocationnel
├── pathways/          # FR27–FR32 — Parcours + stats
├── outreach/          # FR33–FR40 — Envoi anticipé
├── schools/           # FR36–FR40 — Espace école
├── counselors/        # FR43–FR45 — B2B conseiller
├── parents/           # FR41–FR42 — Espace parent
├── moderation/        # FR48–FR52 — Admin + modération
├── audit/             # Cross-cutting — audit log
└── core/              # Cross-cutting — RBAC, tenant middleware, helpers
```

Chaque Django app contient (convention stricte) :
```
apps/<capability>/
├── __init__.py
├── apps.py
├── models.py          # Modèles Django (data layer)
├── serializers.py     # DRF serializers (validation + output)
├── views.py           # DRF ViewSets (HTTP layer, thin)
├── urls.py            # Routes locales (incluses dans urls.py global)
├── permissions.py     # Permissions DRF custom (RBAC)
├── services/          # Business logic (pas dans views)
│   └── __init__.py
├── tasks.py           # Tâches Celery async
├── selectors.py       # Lectures complexes (équivalent repository pattern)
├── tests/
│   ├── test_models.py
│   ├── test_views.py
│   ├── test_services.py
│   └── factories.py   # factory_boy fixtures
└── admin.py           # Django admin (back-office)
```

**Front Next.js — structure feature-based :**

```
apps/web/src/
├── app/                            # App Router (routes)
│   ├── (public)/                   # Routes non-authentifiées (SEO public)
│   │   ├── metiers/[slug]/page.tsx
│   │   ├── formations/[slug]/page.tsx
│   │   └── layout.tsx
│   ├── (authenticated)/            # Routes authentifiées
│   │   ├── onboarding/page.tsx
│   │   ├── recommendations/page.tsx
│   │   ├── pathways/[occupation_id]/page.tsx
│   │   └── layout.tsx
│   ├── api/                        # Routes API Next.js (proxies vers Django uniquement)
│   ├── layout.tsx
│   └── globals.css
├── components/
│   ├── ui/                         # Composants shadcn/ui (génériques)
│   ├── features/                   # Composants métier par feature
│   │   ├── onboarding/
│   │   ├── recommendations/
│   │   ├── pathways/
│   │   ├── outreach/
│   │   └── ...
│   └── layouts/                    # Composants de mise en page
├── lib/
│   ├── api/                        # Client API généré (OpenAPI) + wrappers
│   │   ├── generated/              # Auto-généré, ne pas éditer
│   │   ├── client.ts               # Wrapper avec auth + base URL
│   │   └── hooks.ts                # Hooks TanStack Query par endpoint
│   ├── auth/                       # Helpers auth (session, CSRF)
│   ├── i18n/                       # Config next-intl + messages FR
│   ├── utils.ts                    # Helpers généraux
│   └── types/                      # Types TS partagés (extension du généré)
├── hooks/                          # Hooks React custom
└── styles/
```

**Tests — convention :**
- Python : tests dans `apps/<app>/tests/` (pas co-located), un fichier par module
- TypeScript : tests co-located avec le code (`student-profile-card.tsx` + `student-profile-card.test.tsx`)
- E2E Playwright : `apps/web/e2e/` dans dossier dédié, organisé par parcours utilisateur du PRD

### Format Patterns

**API Response Format :**

Réponse succès : directe, sans wrapper (DRF convention).

Réponse liste paginée (DRF `CursorPagination`) :
```json
{
  "next": "https://api.path-advisor.fr/api/v1/students?cursor=cD0yMDIw...",
  "previous": null,
  "results": [ {...}, {...} ]
}
```

Réponse erreur : RFC 7807 Problem Details :
```json
{
  "type": "https://path-advisor.fr/errors/insufficient-permissions",
  "title": "Permission insuffisante",
  "status": 403,
  "detail": "Vous ne pouvez pas accéder au profil de cet élève sans son consentement explicite.",
  "instance": "/api/v1/students/stu_xyz/profile",
  "request_id": "req_abc123"
}
```

**Data Exchange Formats :**

| Type | Format |
|---|---|
| Dates | ISO 8601 UTC (`2026-05-13T14:30:00Z`) — jamais de timestamps Unix dans l'API |
| Identifiants | Préfixés par type + suffixe ULID/UUID → `stu_01HXJ...`, `sch_01HXK...`, `req_01HXL...` |
| Booléens | `true` / `false` (pas 1/0) |
| Null | `null` explicite (pas string vide ni 0) |
| Decimal | String (pas float) pour montants : `"10.99"` |
| Devise | ISO 4217 → `"EUR"`, `"MAD"`, `"XOF"` |
| Locale | BCP 47 → `"fr-FR"`, `"fr-BE"`, `"fr-MA"` |

### Communication Patterns

**Event/Task Naming (Celery + audit log) :**

Format `<domain>.<action>` (point-séparé, présent simple actif) :
- `student.profile_completed`
- `recommendation.computed`
- `outreach.profile_sent`
- `outreach.school_responded`
- `school.admission_stat_updated`
- `audit.access_granted`

Payload structuré (Pydantic) :
```python
class EventPayload:
    event_name: str
    event_version: int
    actor_id: str
    tenant_id: str | None
    subject_id: str
    occurred_at: datetime
    metadata: dict[str, Any]
    correlation_id: str
```

**State Management Front :**

| Type d'état | Outil | Exemple |
|---|---|---|
| Données serveur | TanStack Query (cache + invalidation) | profil élève, liste recos, graphe parcours |
| État UI complexe | Zustand (store par feature, pas global) | étape onboarding actuelle, filtres graphe |
| État UI local | `useState` / `useReducer` React | toggle panneau, valeur input non submit |

Pattern d'actions (Zustand) : noms d'actions au présent simple actif → `setCurrentStep`, `resetOnboarding`, `selectOccupation`.

### Process Patterns

**Error Handling :**

Côté Django :
- Toute erreur métier hérite de `domain.exceptions.DomainError`
- Handlers DRF custom convertissent → RFC 7807
- structlog log avec context + correlation_id
- Sentry capture automatique si 5xx
- Jamais d'`Exception` nue (toujours typée)

Côté Next.js :
- Erreurs API captées par TanStack Query, exposées via hook `.error`
- Composants utilisent `<ErrorBoundary>` par feature
- Erreurs critiques : notification toast + Sentry capture
- Erreurs validation form : React Hook Form `.formState.errors`
- Fallback global : `app/error.tsx` avec lien retour

**Loading States :**

3 modes consistants :
- Skeleton screens (shadcn/ui Skeleton) pour listes et fiches
- Spinner inline (composant `<Spinner />`) pour actions courtes (< 2s)
- Progress bar pour opérations longues identifiées (OCR bulletins) avec polling status Celery

Pattern TanStack Query :
```typescript
const { data, isLoading, error } = useStudentProfile(studentId)
if (isLoading) return <ProfileSkeleton />
if (error) return <ErrorState error={error} />
return <Profile data={data} />
```

**Auth Flow :**

1. Login : POST `/api/v1/auth/login/` → session cookie posée par Django, CSRF token retourné en header
2. Next.js stocke le CSRF en cookie côté client, ajoute `X-CSRFToken` à toutes les mutations
3. Logout : POST `/api/v1/auth/logout/` → invalide session
4. Refresh implicite via session cookie (pas de refresh token explicite)
5. MFA challenge : si requis, l'endpoint login retourne 200 avec `{"mfa_required": true, "mfa_session": "..."}` → flow MFA séparé

**Validation Timing :**
- Côté client : Zod (form submit + on-blur sur champs sensibles)
- Côté serveur : DRF serializers (validation systématique, jamais skip)
- Schémas partagés : OpenAPI génère des types TS, Zod schémas écrits à la main miroitent les contraintes Django

### Enforcement Guidelines

**Tous les agents IA d'implémentation DOIVENT :**

1. Suivre les conventions de naming par contexte (DB snake_case, API snake_case, Python snake_case/PascalCase, TS camelCase/PascalCase)
2. Mettre la business logic dans `services/` (Django) — jamais dans les ViewSets/views
3. Toute écriture de données sensibles déclenche un audit log via décorateur `@audit_action('action_name')`
4. Toute requête côté front passe par le client `lib/api/` — jamais d'appel `fetch` brut
5. Tout nouveau modèle Django avec données personnelles inclut `tenant_id` et passe par le middleware RLS
6. Tout endpoint sensible (mutation, données PII) a un test d'autorisation explicite
7. Tout texte utilisateur passe par i18n (`useTranslations` front, `gettext` Django) — pas de string en dur

**Pattern Enforcement (automatisé) :**
- CI checks : ruff (Python), eslint (TS), mypy (Python types), tsc strict (TS)
- Linters custom :
  - Plugin ruff custom : interdit `Exception` nue, force `DomainError` dans `apps/`
  - Plugin eslint custom : interdit `fetch` direct, force usage du client `lib/api/`
- Pre-commit hooks (Lefthook) : lint + format + type-check sur fichiers modifiés
- PR checklist automatique : `audit_log` ajouté ? `tenant_id` présent ? Tests d'autorisation ? i18n des strings ?

**Documentation des patterns :**
- `docs/adr/` — chaque écart au pattern requiert un ADR justificatif
- `docs/patterns/` — guide pour onboarder un nouveau dev ou un nouvel agent IA
- `README.md` — pointe vers tous les patterns + commande `make help` pour les workflows courants

### Pattern Examples

**Good Example — Création d'une ressource avec audit + permissions :**

```python
# apps/outreach/services/outreach_service.py
class OutreachService:
    @audit_action("outreach.profile_sent")
    def send_profile_to_school(
        self, student: Student, school: School, motivation: str
    ) -> EarlyOutreachRequest:
        if not student.is_premium:
            raise InsufficientPlanError(detail="Feature reserved for premium")
        request = EarlyOutreachRequest.objects.create(
            student=student, school=school, motivation=motivation,
            tenant_id=get_current_tenant_id(),
        )
        notify_school.delay(request.id)  # Celery
        return request
```

**Anti-Pattern à éviter :**

```python
# A NE PAS FAIRE
class OutreachViewSet(viewsets.ModelViewSet):
    def create(self, request):
        # Business logic dans la vue
        if not request.user.is_premium:
            return Response({"error": "premium required"}, status=403)
        # Pas d'audit, pas de tenant_id, format erreur non RFC 7807, business logic mélangée
        outreach = EarlyOutreachRequest.objects.create(student=request.user.student, ...)
        return Response({"id": outreach.id})
```

## Project Structure & Boundaries

### Complete Project Directory Structure

```
path-advisor/                                # Monorepo racine
├── README.md
├── Makefile
├── .gitignore
├── .editorconfig
├── lefthook.yml
├── .doppler.yaml
├── docker-compose.yml
├── docker-compose.prod.yml
├── .github/
│   ├── workflows/
│   │   ├── ci-web.yml
│   │   ├── ci-api.yml
│   │   ├── ci-ai-service.yml
│   │   ├── ci-types-generation.yml
│   │   └── deploy-prod.yml
│   └── pull_request_template.md
│
├── apps/
│   ├── web/                                 # Next.js 15 + TS
│   │   ├── package.json
│   │   ├── next.config.ts
│   │   ├── tailwind.config.ts
│   │   ├── tsconfig.json
│   │   ├── playwright.config.ts
│   │   ├── vitest.config.ts
│   │   ├── components.json                  # shadcn/ui
│   │   ├── public/
│   │   ├── messages/                        # i18n (next-intl)
│   │   │   ├── fr.json
│   │   │   ├── fr-BE.json
│   │   │   └── fr-MA.json
│   │   ├── src/
│   │   │   ├── middleware.ts
│   │   │   ├── app/
│   │   │   │   ├── [locale]/
│   │   │   │   │   ├── (public)/            # SEO public
│   │   │   │   │   │   ├── page.tsx
│   │   │   │   │   │   ├── metiers/[slug]/page.tsx       # FR46
│   │   │   │   │   │   ├── formations/[slug]/page.tsx    # FR46
│   │   │   │   │   │   ├── ecoles/[slug]/page.tsx        # FR46
│   │   │   │   │   │   └── auth/
│   │   │   │   │   │       ├── login/page.tsx
│   │   │   │   │   │       ├── signup/page.tsx           # FR1
│   │   │   │   │   │       ├── parental-consent/page.tsx # FR2
│   │   │   │   │   │       └── mfa/page.tsx              # FR4-FR6
│   │   │   │   │   ├── (authenticated)/     # Routes élève
│   │   │   │   │   │   ├── onboarding/                   # FR13-FR19
│   │   │   │   │   │   ├── recommendations/              # FR20-FR26
│   │   │   │   │   │   ├── parcours/                     # FR27-FR32
│   │   │   │   │   │   ├── envois-anticipes/             # FR39
│   │   │   │   │   │   ├── premium/page.tsx
│   │   │   │   │   │   └── parametres/
│   │   │   │   │   │       ├── confidentialite/page.tsx  # FR8-FR11
│   │   │   │   │   │       └── parent/page.tsx           # FR3
│   │   │   │   │   ├── (parent)/                         # FR41-FR42
│   │   │   │   │   ├── (counselor)/                      # FR43-FR45
│   │   │   │   │   ├── (school)/                         # FR35-FR40
│   │   │   │   │   └── layout.tsx
│   │   │   │   ├── api/
│   │   │   │   │   └── webhooks/stripe/route.ts
│   │   │   │   ├── error.tsx
│   │   │   │   ├── not-found.tsx
│   │   │   │   └── sitemap.ts
│   │   │   ├── components/
│   │   │   │   ├── ui/                      # shadcn/ui
│   │   │   │   ├── features/
│   │   │   │   │   ├── onboarding/
│   │   │   │   │   ├── recommendations/
│   │   │   │   │   ├── pathways/            # incl. pathway-graph.tsx (React Flow)
│   │   │   │   │   ├── outreach/
│   │   │   │   │   ├── parent/
│   │   │   │   │   ├── counselor/
│   │   │   │   │   └── school/
│   │   │   │   └── layouts/
│   │   │   ├── lib/
│   │   │   │   ├── api/
│   │   │   │   │   ├── generated/           # Auto-généré OpenAPI (gitignore)
│   │   │   │   │   ├── client.ts
│   │   │   │   │   ├── hooks.ts             # TanStack Query
│   │   │   │   │   └── errors.ts            # Parsing RFC 7807
│   │   │   │   ├── auth/
│   │   │   │   ├── i18n/
│   │   │   │   ├── analytics/posthog.ts
│   │   │   │   ├── stripe/client.ts
│   │   │   │   ├── seo/
│   │   │   │   │   ├── schema-org.ts
│   │   │   │   │   └── metadata.ts
│   │   │   │   └── utils.ts
│   │   │   ├── hooks/
│   │   │   ├── stores/                      # Zustand
│   │   │   └── styles/
│   │   ├── e2e/                             # Playwright (parcours PRD)
│   │   │   ├── parcours-1-sarah.spec.ts
│   │   │   ├── parcours-2-mehdi.spec.ts
│   │   │   ├── parcours-3-lea.spec.ts
│   │   │   ├── parcours-4-conseiller.spec.ts
│   │   │   ├── parcours-5-parent.spec.ts
│   │   │   └── parcours-6-ecole.spec.ts
│   │   ├── Dockerfile
│   │   └── Dockerfile.dev
│   │
│   ├── api/                                 # Django 5 + DRF
│   │   ├── pyproject.toml
│   │   ├── manage.py
│   │   ├── ruff.toml
│   │   ├── pytest.ini
│   │   ├── mypy.ini
│   │   ├── path_advisor/
│   │   │   ├── settings/
│   │   │   │   ├── base.py
│   │   │   │   ├── local.py
│   │   │   │   ├── staging.py
│   │   │   │   ├── prod.py
│   │   │   │   └── test.py
│   │   │   ├── urls.py
│   │   │   ├── celery.py
│   │   │   ├── asgi.py
│   │   │   ├── wsgi.py
│   │   │   └── middleware/
│   │   │       ├── tenant.py                # Injection tenant_id + RLS
│   │   │       ├── audit.py
│   │   │       ├── request_id.py
│   │   │       └── i18n.py
│   │   ├── apps/                            # Django apps par zone capacités
│   │   │   ├── core/                        # Cross-cutting
│   │   │   │   ├── models.py                # TenantScopedModel, AuditableModel, SoftDeleteModel
│   │   │   │   ├── managers.py
│   │   │   │   ├── permissions.py
│   │   │   │   ├── exceptions.py            # DomainError
│   │   │   │   ├── pagination.py
│   │   │   │   ├── ids.py                   # ULID préfixés
│   │   │   │   ├── encryption.py
│   │   │   │   └── tasks.py
│   │   │   ├── audit/                       # FR12 + cross-cutting
│   │   │   │   ├── models.py                # AuditLog (immutable)
│   │   │   │   ├── decorators.py            # @audit_action
│   │   │   │   ├── views.py                 # Endpoint DPO
│   │   │   │   ├── tasks.py                 # Export S3 mensuel
│   │   │   │   └── migrations/
│   │   │   │       └── 0001_audit_trigger.py # CREATE TRIGGER immuable
│   │   │   ├── accounts/                    # FR1-FR12
│   │   │   │   ├── models.py                # User, Tenant, Role, Consent
│   │   │   │   ├── serializers.py
│   │   │   │   ├── views.py
│   │   │   │   ├── permissions.py
│   │   │   │   ├── urls.py
│   │   │   │   ├── services/
│   │   │   │   │   ├── auth_service.py
│   │   │   │   │   ├── consent_service.py
│   │   │   │   │   ├── gdpr_service.py
│   │   │   │   │   └── parental_consent.py
│   │   │   │   ├── tasks.py
│   │   │   │   ├── admin.py
│   │   │   │   └── tests/
│   │   │   ├── profiles/                    # FR13-FR19
│   │   │   │   ├── models.py                # Student, Bulletin, Passion, Interest, Value
│   │   │   │   ├── services/
│   │   │   │   │   ├── profile_service.py
│   │   │   │   │   ├── bulletin_service.py
│   │   │   │   │   └── ocr_service.py       # Abstraction Tesseract/Mindee
│   │   │   │   └── tasks.py                 # OCR async
│   │   │   ├── recommendations/             # FR20-FR26
│   │   │   │   ├── models.py                # Occupation, RecommendationScore, ScoreExplanation
│   │   │   │   ├── services/
│   │   │   │   │   ├── recommendation_service.py
│   │   │   │   │   ├── ai_client.py         # Client HTTP vers ai-service (JWT)
│   │   │   │   │   └── explainability.py
│   │   │   │   └── tasks.py
│   │   │   ├── pathways/                    # FR27-FR32
│   │   │   │   ├── models.py                # Pathway, PathwayNode, Formation, AdmissionStat
│   │   │   │   ├── services/
│   │   │   │   │   ├── pathway_service.py
│   │   │   │   │   ├── admission_stat_service.py
│   │   │   │   │   └── parcoursup_data.py
│   │   │   │   └── tasks.py
│   │   │   ├── outreach/                    # FR33-FR40
│   │   │   │   ├── models.py                # EarlyOutreachRequest, OutreachResponse
│   │   │   │   ├── services/
│   │   │   │   │   ├── outreach_service.py
│   │   │   │   │   ├── notification_service.py
│   │   │   │   │   └── stat_update_service.py
│   │   │   │   └── tasks.py
│   │   │   ├── schools/                     # FR5, FR35-FR40
│   │   │   │   ├── models.py                # School, SchoolAdminUser
│   │   │   │   ├── permissions.py           # Isolation par école
│   │   │   │   └── services/
│   │   │   ├── counselors/                  # FR4, FR43-FR45
│   │   │   │   ├── models.py                # Counselor, Cohort, ConsentLink
│   │   │   │   └── services/
│   │   │   │       ├── cohort_service.py
│   │   │   │       └── reporting_service.py
│   │   │   ├── parents/                     # FR3, FR41-FR42
│   │   │   │   ├── models.py                # ParentStudentLink
│   │   │   │   ├── permissions.py           # Vue restreinte
│   │   │   │   └── services/
│   │   │   │       └── billing_service.py
│   │   │   ├── moderation/                  # FR48-FR52
│   │   │   │   ├── models.py                # Report, ModerationAction, MLModelVersion
│   │   │   │   ├── services/
│   │   │   │   │   ├── report_service.py
│   │   │   │   │   ├── content_moderation.py
│   │   │   │   │   └── ml_audit_service.py
│   │   │   │   └── admin.py                 # FR48-FR49 back-office
│   │   │   └── billing/                     # Stripe + abonnements
│   │   │       ├── models.py                # Subscription, Invoice, StripeEvent
│   │   │       ├── views.py                 # Webhook Stripe HMAC
│   │   │       └── services/
│   │   ├── fixtures/                        # Seeds dev
│   │   │   ├── seed_occupations.json        # 50 métiers MVP
│   │   │   ├── seed_formations.json         # 100 formations MVP
│   │   │   └── seed_users.json
│   │   ├── locale/                          # i18n Django
│   │   │   └── fr/LC_MESSAGES/django.po
│   │   ├── scripts/
│   │   │   ├── export_openapi.py
│   │   │   ├── seed_dev.py
│   │   │   └── load_parcoursup_data.py
│   │   ├── Dockerfile
│   │   └── Dockerfile.dev
│   │
│   └── ai-service/                          # FastAPI Service IA
│       ├── pyproject.toml
│       ├── uv.lock
│       ├── ruff.toml
│       ├── pytest.ini
│       ├── src/
│       │   ├── main.py                      # FastAPI app + middleware JWT
│       │   ├── config.py
│       │   ├── api/
│       │   │   ├── routes/
│       │   │   │   ├── scoring.py           # POST /score (FR20)
│       │   │   │   ├── embeddings.py
│       │   │   │   ├── admission.py         # POST /predict-admission (FR29)
│       │   │   │   └── health.py
│       │   │   ├── dependencies.py          # JWT verification
│       │   │   └── schemas.py
│       │   ├── domain/
│       │   │   ├── recommendation/
│       │   │   │   ├── statistical_scorer.py
│       │   │   │   ├── feature_extractor.py
│       │   │   │   └── explanation.py
│       │   │   ├── embeddings/
│       │   │   │   ├── profile_embedder.py
│       │   │   │   └── occupation_embedder.py
│       │   │   ├── admission/
│       │   │   │   ├── predictor.py
│       │   │   │   └── confidence_interval.py
│       │   │   └── nlp/
│       │   │       └── teacher_comments.py
│       │   ├── infrastructure/
│       │   │   ├── db.py                    # PostgreSQL asyncpg
│       │   │   ├── pgvector_repo.py
│       │   │   ├── model_registry.py        # MLflow
│       │   │   └── llm_client.py            # Mistral local / OpenAI
│       │   ├── pipelines/                   # Entraînement
│       │   ├── evaluation/                  # FR52 audit biais + drift
│       │   │   ├── bias_audit.py
│       │   │   ├── drift_detection.py
│       │   │   └── metrics.py
│       │   └── tests/
│       ├── models/                          # MLflow (gitignore)
│       ├── data/                            # Datasets (gitignore)
│       ├── Dockerfile
│       └── Dockerfile.dev
│
├── packages/
│   └── openapi/
│       ├── openapi.json                     # Généré par Django CI
│       └── scripts/
│           └── generate-ts-client.sh
│
├── infra/
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   ├── caddy/Caddyfile                      # Reverse proxy production
│   ├── postgres/
│   │   ├── init.sql                         # Extensions pgvector + pgcrypto
│   │   └── triggers/audit_log_immutable.sql
│   ├── prometheus/prometheus.yml
│   ├── grafana/
│   ├── scripts/
│   │   ├── backup.sh                        # pg_dump + push S3
│   │   ├── restore.sh
│   │   └── deploy.sh
│   └── terraform/                           # Optionnel : provisioning Scaleway
│
└── docs/
    ├── README.md
    ├── adr/                                 # Architecture Decision Records
    │   ├── 0001-monorepo-vs-multi-repo.md
    │   ├── 0002-django-vs-fastapi-main-back.md
    │   ├── 0003-multi-tenant-hybrid-rls.md
    │   ├── 0004-session-cookie-vs-jwt.md
    │   ├── 0005-react-flow-pathway-graph.md
    │   ├── 0006-snake-case-end-to-end.md
    │   ├── 0007-scaleway-hosting.md
    │   └── 0008-poc-local-first.md
    ├── patterns/
    ├── runbooks/
    │   ├── deploy.md
    │   ├── incident-response.md
    │   ├── backup-restore.md
    │   └── gdpr-request.md
    ├── api/openapi.json                     # Symlink vers packages/openapi/
    └── onboarding.md
```

### Architectural Boundaries

**API Boundaries (3 surfaces distinctes) :**

| Surface | Audience | Auth | Format |
|---|---|---|---|
| `/api/v1/...` (web) | Frontend Next.js + utilisateurs authentifiés | Session cookie + CSRF | REST + RFC 7807 erreurs |
| `/internal/...` (ai-service) | Communication interne Django ↔ FastAPI | JWT HS256 court TTL | REST JSON |
| `/admin/...` (Django admin) | Admin Path-Advisor | Session + MFA obligatoire | Django admin natif |
| `/webhooks/...` | Stripe + futurs (école growth) | HMAC signature vérifiée | REST JSON |

**Component Boundaries (Next.js) :**
- Server Components : pages publiques SEO, layouts, fetching initial (default)
- Client Components (`"use client"`) : graphes interactifs, formulaires React Hook Form, stores Zustand
- Communication enfant → parent : props uniquement (pas d'event bus global)
- Communication entre features : via stores Zustand dédiés OU via TanStack Query invalidation
- Pas d'import circulaire : `features/` peut importer de `ui/` et `lib/`, jamais l'inverse

**Service Boundaries (back-end) :**
- Django apps isolées : aucune app n'importe directement les modèles d'une autre — utiliser des services exposés (`from apps.profiles.services import profile_service`)
- `core/` est la seule app que toutes les autres peuvent importer
- `audit/` est appelée via décorateur uniquement, jamais en import direct
- Django ↔ FastAPI : Django ne connaît FastAPI que via `apps.recommendations.services.ai_client.AIClient` (façade unique)

**Data Boundaries :**
- PostgreSQL : DB unique partagée, isolation via `tenant_id` + RLS
- Tables sensibles (PII) : toutes avec `tenant_id`, `created_at`, `updated_at`, soft delete `deleted_at`
- Audit log : table dédiée immuable (trigger PostgreSQL), append-only
- S3 / MinIO : 3 buckets distincts — `bulletins-encrypted`, `exports-gdpr`, `audit-logs-archive`
- Redis : 3 namespaces — `sessions:*`, `cache:*`, `ratelimit:*`
- pgvector embeddings : table dédiée `vector_embeddings(subject_id, kind, vector, model_version, computed_at)`

### Requirements to Structure Mapping

**Feature/FR Mapping :**

| FR Zone | Apps Django | Composants Front | Endpoints API |
|---|---|---|---|
| **A. Comptes, Rôles & Conformité (FR1-FR12)** | `accounts/`, `core/`, `audit/` | `/auth/*`, `/parametres/confidentialite/` | `/api/v1/auth/*`, `/api/v1/me/consents`, `/api/v1/me/gdpr-export` |
| **B. Profil & Onboarding (FR13-FR19)** | `profiles/` | `/onboarding/*`, `features/onboarding/*` | `/api/v1/students/me/profile`, `/api/v1/students/me/bulletins` |
| **C. Reco Vocationnelle (FR20-FR26)** | `recommendations/` + `ai-service/api/scoring.py` | `/recommendations/*`, `features/recommendations/*` | `/api/v1/recommendations`, `/api/v1/recommendations/{id}/explanation` |
| **D. Parcours & Stats (FR27-FR32)** | `pathways/` + `ai-service/api/admission.py` | `/parcours/*`, `features/pathways/*` | `/api/v1/occupations/{id}/pathways`, `/api/v1/admission-stats` |
| **E. Envoi Anticipé & Écoles (FR33-FR40)** | `outreach/`, `schools/` | `/envois-anticipes/*`, `/(school)/*`, `features/outreach/*` | `/api/v1/early-outreach-requests`, `/api/v1/schools/me/inbox` |
| **F. Espaces Tiers (FR41-FR45)** | `parents/`, `counselors/`, `billing/` | `/(parent)/*`, `/(counselor)/*` | `/api/v1/parents/me/students`, `/api/v1/counselors/me/cohort` |
| **G. Découverte & Engagement (FR46-FR47)** | `pathways/` (data export public) | `/(public)/metiers/*`, `app/sitemap.ts` | `/api/v1/public/occupations`, `/api/v1/public/formations` |
| **H. Administration (FR48-FR52)** | `moderation/`, `audit/` | Django admin natif `/admin/*` | Django admin |

**Cross-Cutting Concerns Mapping :**

| Concern | Localisation |
|---|---|
| Authentication & RBAC | `apps/accounts/`, `apps/core/permissions.py`, middleware `tenant.py` |
| Multi-tenant isolation | `apps/core/models.py` (TenantScopedModel) + middleware `tenant.py` + RLS PostgreSQL |
| Audit trail | `apps/audit/`, décorateur `@audit_action`, trigger SQL immuable |
| Versioning IA | `apps/moderation/services/ml_audit_service.py` + `ai-service/src/infrastructure/model_registry.py` (MLflow) |
| Explicabilité IA | `apps/recommendations/services/explainability.py` + `ai-service/src/domain/recommendation/explanation.py` |
| Consentement granulaire | `apps/accounts/models.py` (Consent model) + `apps/accounts/services/consent_service.py` |
| Saisonnalité (auto-scaling) | `infra/terraform/` + alertes Prometheus |
| i18n | `apps/web/messages/`, `apps/api/locale/`, middleware `i18n.py` |
| Observabilité | structlog (toutes apps), Sentry SDK, OpenTelemetry exporters, `infra/grafana/` |
| Mode dégradé | Abstractions dans `apps/profiles/services/ocr_service.py`, `apps/outreach/services/notification_service.py` |
| Continuité local ↔ cloud | Variables d'env via Doppler, Dockerfiles dev/prod séparés, `docker-compose.yml` + override prod |

### Integration Points

**Internal Communication :**

```
Browser (user)
    │  HTTPS + session cookie + CSRF
    ▼
Next.js (apps/web)
    │  Server Components → fetch direct (SSR)
    │  Client Components → TanStack Query → /api/v1/...
    ▼
Django + DRF (apps/api)
    │
    │  apps/recommendations/services/ai_client.py
    │  HTTPS + JWT court TTL
    ▼
FastAPI ai-service (apps/ai-service)
    │
    └─── PostgreSQL (pgvector)
    └─── MLflow registry (S3-backed)

[Asynchrone]
Django → Celery task → Redis queue → Celery worker
    │
    ├─ Email (Postmark)
    ├─ OCR (Mindee API ou worker Tesseract)
    ├─ Notify école (email + push)
    ├─ Export RGPD (S3)
    └─ Recalcul cohorte conseiller
```

**External Integrations :**

| Service | Direction | Mode | Localisation |
|---|---|---|---|
| Stripe | Sortant + entrant (webhook) | HTTPS + HMAC signé | `apps/api/apps/billing/` |
| Postmark (email prod) | Sortant | API REST | `apps/api/apps/core/services/email.py` |
| Mailpit (email dev) | Sortant | SMTP | `infra/docker-compose.yml` |
| Mindee (OCR prod) | Sortant async | API REST + webhook | `apps/api/apps/profiles/services/ocr_service.py` |
| Tesseract (OCR dev) | Sortant async | gRPC/HTTP local | `infra/docker-compose.yml` |
| S3 / MinIO | Sortant | boto3 (django-storages) | `apps/api/apps/core/storage.py` |
| Sentry | Sortant async | Sentry SDK | Tous les services |
| PostHog | Sortant async | PostHog SDK | `apps/web/src/lib/analytics/posthog.ts` |
| Parcoursup open data | Entrant batch | CSV download annuel | `apps/api/apps/pathways/services/parcoursup_data.py` |
| ONISEP open data | Entrant batch | API REST + CSV | `apps/api/apps/pathways/services/onisep_data.py` |

**Data Flow — Parcours élève (Sarah, happy path) :**

```
1. Sarah s'inscrit                  → POST /api/v1/auth/signup → User créé, session cookie posée
2. Onboarding passions              → POST /api/v1/students/me/profile/interests
3. Upload bulletin PDF              → POST /api/v1/students/me/bulletins (file)
                                      → S3 chiffré, Celery task déclenchée
4. OCR async                        → ocr_service.extract() → bulletin lignes/notes en DB
5. Sarah voit page recos            → GET /api/v1/recommendations
                                      → recommendation_service → ai_client → ai-service.score()
                                      → réponse < 3s avec top 8 métiers + signaux
6. Sarah clique métier              → GET /api/v1/occupations/{id}/pathways
                                      → pathway_service → ai-service.predict_admission()
                                      → graphe React Flow rendu côté client
7. Sarah upgrade premium            → POST /api/v1/billing/subscriptions → Stripe Checkout
                                      → webhook Stripe → subscription.is_premium = True
8. Sarah déclenche envoi anticipé   → POST /api/v1/early-outreach-requests
                                      → outreach_service.send_profile_to_school()
                                      → audit_action('outreach.profile_sent')
                                      → Celery task notify_school
                                      → Postmark email + web push école
9. École répond "intéressant"       → POST /api/v1/schools/me/inbox/{request_id}/respond
                                      → outreach_service.handle_response()
                                      → stat_update_service → admission_stat +14 points
                                      → Celery task notify_student
                                      → Sarah reçoit email + push, stat à jour en < 5 min
```

### File Organization Patterns

**Configuration Files :**
- Racine : config orchestration (docker-compose, lefthook, .doppler)
- Par app : config technique (pyproject.toml, package.json, tsconfig.json, ruff.toml)
- Django settings : split par environnement (`base.py` + `local.py` / `staging.py` / `prod.py`)

**Source Organization :**
- Apps Django par capacité fonctionnelle (FRs A-H), pas par couche technique
- Next.js components par feature (sauf `ui/` qui est générique shadcn)
- Service IA par domaine (`domain/recommendation/`, `domain/admission/`, `domain/nlp/`)

**Test Organization :**
- Django : tests dans dossier `tests/` de chaque app, factories factory_boy
- Next.js unit : co-located (`.test.tsx` à côté du composant)
- E2E : `apps/web/e2e/` un fichier par parcours du PRD (traçabilité maximum)
- AI service : `apps/ai-service/src/tests/` avec property-based pour audit biais

**Asset Organization :**
- `apps/web/public/` : favicons, logo, robots.txt, OpenGraph images
- `apps/web/messages/` : traductions i18n par locale
- `apps/api/locale/` : traductions Django par locale
- `apps/api/fixtures/` : seeds métiers/formations
- Modèles ML : gitignore, persisté via MLflow → S3

### Development Workflow Integration

**Development Server Structure :**

```bash
# Méthode 1 : tout en Docker (recommandé)
docker-compose up
# → web sur 3000, api sur 8000, ai sur 8001, postgres sur 5432, redis 6379, mailpit 8025

# Méthode 2 : hybride (back en Docker, front local pour HMR rapide)
docker-compose up postgres redis minio mailpit posthog
cd apps/api && uv run python manage.py runserver 8000 &
cd apps/ai-service && uv run uvicorn src.main:app --reload --port 8001 &
cd apps/web && npm run dev

# Make targets de productivité
make dev          # Lance tout en mode hybride
make test         # Lance tous les tests (web + api + ai-service)
make lint         # Lint + format check tous langages
make seed         # Charge fixtures + crée user admin
make openapi      # Régénère openapi.json + types TS front
```

**Build Process Structure :**

```bash
# CI sur push
1. .github/workflows/ci-api.yml          → uv install, ruff, mypy, pytest, export openapi.json
2. .github/workflows/ci-types-generation.yml → openapi-typescript apps/web/src/lib/api/generated
3. .github/workflows/ci-web.yml          → npm install, tsc, eslint, vitest, playwright (smoke)
4. .github/workflows/ci-ai-service.yml   → uv install, ruff, pytest + bias audit gate
5. Build Docker images, push to GHCR
6. .github/workflows/deploy-prod.yml     → SSH Scaleway, docker-compose pull + up
```

**Deployment Structure :**

```bash
# Production (Scaleway VM)
/opt/path-advisor/
├── docker-compose.prod.yml       # Pulled from git
├── .env.prod                     # Doppler sync
├── data/
│   ├── postgres/                 # Volume mount
│   ├── redis/
│   └── minio/                    # Migration vers S3 Scaleway en growth
└── backups/                      # pg_dump quotidien avant push S3
```

## Architecture Validation Results

### Coherence Validation

**Decision Compatibility :**
- Next.js + Django via OpenAPI : compatible, contrat explicite via `drf-spectacular` + `openapi-typescript`
- Session cookie + CSRF + Next.js + Django : compatible si même domaine racine (`.path-advisor.fr`) — à acter dans la config DNS
- React Flow + RGAA AA : compatible (React Flow expose ARIA + navigation clavier nativement)
- Multi-tenant hybride + RLS PostgreSQL + middleware Django : cohérent, isolation forte au niveau DB + applicatif
- pgvector dans la DB principale : compatible (extension PostgreSQL), évite une DB vectorielle supplémentaire
- snake_case JSON end-to-end : élimine les bugs de mapping cross-stack
- Communication Django ↔ FastAPI via JWT court TTL : pattern service-to-service sain

**Pattern Consistency :**
- Conventions naming par langage (Python `snake_case`/`PascalCase`, TS `camelCase`/`PascalCase`) cohérentes avec leurs écosystèmes respectifs
- Architecture services Django (business logic dans `services/`, views thin) cohérente avec DRF + patterns Django modernes
- Server Components first Next.js cohérent avec SSR + SEO + perf goals

**Structure Alignment :**
- Mapping FRs A-H → Django apps : 1-pour-1, traçabilité totale
- Mapping parcours utilisateurs → fichiers e2e Playwright : 1-pour-1
- Cross-cutting concerns (RBAC, audit, tenant, RGPD) localisés dans `core/` et `audit/`, importables depuis toutes les apps

### Requirements Coverage Validation

**Functional Requirements Coverage (52 FRs MVP) :**

| Zone | FRs | Couverture |
|---|---|---|
| A. Comptes & RGPD | FR1-FR12 (12) | 100% — `accounts/`, `audit/`, `core/permissions.py` |
| B. Profil & Onboarding | FR13-FR19 (7) | 100% — `profiles/` + OCR service abstrait + saisie manuelle |
| C. Reco Vocationnelle | FR20-FR26 (7) | 100% — `recommendations/` + ai-service `domain/recommendation/` |
| D. Parcours & Stats | FR27-FR32 (6) | 100% — `pathways/` + `ai-service/admission/` + React Flow |
| E. Envoi Anticipé | FR33-FR40 (8) | 100% — `outreach/`, `schools/`, workflow Celery propagation < 5 min |
| F. Espaces Tiers | FR41-FR45 (5) | 100% — `parents/`, `counselors/`, `billing/` |
| G. Découverte & SEO | FR46-FR47 (2) | 100% — SSR + Schema.org + sitemap + email service |
| H. Administration | FR48-FR52 (5) | 100% — Django admin + `moderation/` + MLflow versioning |

**Non-Functional Requirements Coverage :**

| Catégorie | NFRs | Couverture |
|---|---|---|
| Performance | NFR-P1-P6 | Couvert — latences cibles documentées, Celery async pour OCR/notify |
| Security | NFR-S1-S9 | NFR-S7 (DPIA) = livrable documentaire, à ajouter dans `docs/compliance/` (gap mineur) |
| Scalability | NFR-SC1-SC6 | Couvert — scaling horizontal ai-service + plan Docker Compose → K8s growth |
| Reliability | NFR-R1-R5 | Couvert — backups, runbooks, observabilité, dégradation gracieuse |
| Accessibility | NFR-A1-A6 | NFR-A5 (alternative textuelle graphe) à expliciter dans `pathway-graph.tsx` (gap mineur) |
| Integration | NFR-I1-I7 | NFR-I5 (données ouvertes Etalab) = feature growth, non bloquante MVP |
| Maintenability | NFR-M1-M5 | NFR-M2 (coverage 70%) sans gate CI explicite (gap mineur) |

### Implementation Readiness Validation

**Decision Completeness :**
- Stack tranchée : Next.js + Django + FastAPI + PostgreSQL + Redis + MinIO + Stripe + Sentry + PostHog
- Versions à vérifier au moment de l'init (latest stable)
- 5 catégories de décisions documentées (Data, Auth, API, Frontend, Infrastructure)

**Structure Completeness :**
- Arbre projet complet avec ~150 fichiers/dossiers identifiés
- 11 Django apps mappées 1-pour-1 aux 8 zones FRs + 3 cross-cutting (`core/`, `audit/`, `billing/`)
- Structure Next.js feature-based avec routes nommées et groupées par rôle
- 6 fichiers e2e Playwright (un par parcours PRD)
- 8 ADRs initiaux identifiés

**Pattern Completeness :**
- Naming patterns couvrant DB, API, code (Python + TS)
- Format API : RFC 7807 erreurs + pagination cursor + Schema.org SEO
- Communication patterns : event naming, state management, auth flow
- Process patterns : error handling, loading states, validation
- Enforcement automatisé : ruff + eslint + mypy + tsc + lefthook + plugins custom

### Gap Analysis Results

**Critical Gaps :** Aucun. L'architecture est implémentable telle quelle.

**Important Gaps (à adresser en sprint 1) :**

| # | Gap | Action recommandée |
|---|---|---|
| 1 | NFR-A5 alternative textuelle graphe parcours non explicité | Ajouter composant `<PathwayTextAlternative />` dans `features/pathways/` rendant le graphe sous forme de liste hiérarchique pour lecteurs d'écran |
| 2 | NFR-S7 DPIA non livré côté tech | Créer `docs/compliance/dpia.md` (template CNIL) à remplir avant production — gate de déploiement |
| 3 | NFR-M2 coverage 70% sans gate CI | Ajouter check coverage dans `ci-api.yml` et `ci-web.yml` avec seuil 70% — fail si en-dessous |
| 4 | Stripe webhooks : potentiel doublon entre `apps/web/src/app/api/webhooks/stripe/` et `apps/api/apps/billing/views.py` | Trancher : tout côté Django (single source of truth). Supprimer la route Next.js |
| 5 | Domaine cookies cross-subdomain | Acter : `path-advisor.fr` (front) + `api.path-advisor.fr` (back) avec cookie scope `.path-advisor.fr` |
| 6 | Choix final secrets manager : Doppler vs sops/age | Trancher au sprint 1. Recommandation : Doppler pour solo |

**Nice-to-Have Gaps (post-MVP) :**

- Feature flags (rollout progressif) — PostHog feature flags ou Unleash en growth
- A/B testing produit — PostHog experiments pour valider conversion premium
- Cache layer applicatif (django-cachalot) — optimisation si latence DB devient problème
- Rate limiting fin par endpoint (au-delà de django-ratelimit global)

### Validation Issues Addressed

Les 6 important gaps ci-dessus n'ont pas été corrigés dans l'architecture parce qu'ils nécessitent soit des décisions externes (DPIA), soit de l'implémentation (composants), soit de la configuration runtime (cookies, coverage). Ils sont listés explicitement comme actions de sprint 1 dans le handoff ci-dessous.

### Architecture Completeness Checklist

**Requirements Analysis**
- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**Architectural Decisions**
- [x] Critical decisions documented (stack, multi-tenant, auth, hosting, framework choices)
- [x] Technology stack fully specified
- [x] Integration patterns defined (sync HTTP + async Celery + webhooks HMAC)
- [x] Performance considerations addressed (latences cibles documentées)

**Implementation Patterns**
- [x] Naming conventions established (DB, API, code)
- [x] Structure patterns defined (Django apps par capacité, Next.js feature-based)
- [x] Communication patterns specified (events, state, auth flow)
- [x] Process patterns documented (errors RFC 7807, loading states, validation)

**Project Structure**
- [x] Complete directory structure defined
- [x] Component boundaries established (API surfaces, Django apps isolation, frontières par rôle)
- [x] Integration points mapped (external deps + data flow Sarah end-to-end)
- [x] Requirements to structure mapping complete (table FR Zone → Apps Django → Front → Endpoints)

### Architecture Readiness Assessment

**Overall Status : READY WITH MINOR GAPS** — implémentation peut démarrer immédiatement (sprint 1 = fondations). Les 6 important gaps sont à traiter explicitement pendant les sprints 1-2 mais ne bloquent pas le démarrage.

**Confidence Level : High**

**Key Strengths :**
1. Traçabilité PRD → code maximale — chaque FR mappé à une Django app, chaque parcours mappé à un test e2e
2. Stack unifiée Python serveur + TS front — réduit la charge cognitive pour 1-2 personnes
3. Sécurité by design — multi-tenant + RLS + audit immuable + chiffrement multi-couche + MFA dès le sprint 2
4. PoC local-first — `docker-compose up` lance toute la stack, aucune dépendance cloud-only
5. AI service séparé proprement — scaling indépendant + MLflow versioning + audit biais natif
6. Patterns enforcement automatisés — lint + type-check + tests d'isolation en CI
7. Préparation francophonie dès le jour 1 — i18n configuré, locales préparées

**Areas for Future Enhancement :**
- Migration vers Kubernetes en growth (10K+ MAU) — actuellement Docker Compose sur 1 VM
- Feature flags & A/B testing — non critique en MVP solo, utile dès qu'il y a des choix produit à valider
- Modèle prédictif d'admission custom (DL) — actuellement open data Parcoursup en MVP, DL en growth
- Comité éthique trimestriel formalisé — reporté en growth (décision PRD)
- App mobile native — reporté en growth (PWA installable en MVP)

### Implementation Handoff

**AI Agent Guidelines :**
- Suivre exactement les conventions de naming définies (DB/API/code par langage)
- Mettre toute business logic dans `services/` côté Django, jamais dans les ViewSets
- Décorer toute action sensible avec `@audit_action('domain.action')`
- Passer toutes les requêtes front par `lib/api/` (jamais `fetch` direct)
- Hériter de `TenantScopedModel` pour toute table avec données utilisateur
- Créer un ADR pour toute décision qui dévie des patterns documentés
- Référer à ce document pour toute question architecturale ; en cas d'ambiguïté, demander clarification plutôt qu'improviser

**First Implementation Priorities (Sprint 1) :**

1. Provisionner la VM Scaleway (Paris) + Doppler + Cloudflare DNS
2. Initialiser le monorepo avec les 3 apps (`web`, `api`, `ai-service`) via les commandes du Starter Template Evaluation
3. Configurer `docker-compose.yml` complet (web + api + ai + postgres + redis + minio + mailpit + posthog + grafana)
4. Activer extensions PostgreSQL : `pgvector`, `pgcrypto`
5. Implémenter le middleware `tenant.py` + RLS PostgreSQL + base classes `core/models.py`
6. Implémenter la table `audit_log` immuable avec trigger SQL bloquant UPDATE/DELETE
7. Configurer GitHub Actions (4 workflows + déploiement)
8. Écrire les 8 ADRs initiaux (`docs/adr/0001-...` à `0008-...`)
9. Adresser les 6 important gaps identifiés ci-dessus
10. Charger fixtures dev (50 métiers + 100 formations en seeds bootstrap LLM)

**Commande de bootstrap initiale :**
```bash
git clone <repo> path-advisor && cd path-advisor
make install        # Installe deps web + api + ai-service
make seed           # Charge fixtures + crée admin
make dev            # Lance la stack complète
make test           # Vérifie que tout passe
make openapi        # Génère le contrat OpenAPI + types TS
```
