# Project Structure & Boundaries

## Complete Project Directory Structure

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

## Architectural Boundaries

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

## Requirements to Structure Mapping

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

## Integration Points

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

## File Organization Patterns

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

## Development Workflow Integration

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
