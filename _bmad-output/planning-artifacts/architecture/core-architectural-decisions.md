# Core Architectural Decisions

## Decision Priority Analysis

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

## Data Architecture

| Décision | Choix | Rationale |
|---|---|---|
| **Multi-tenant pattern** | Middleware Django custom + PostgreSQL RLS (pas django-tenants) | django-tenants force schema-per-tenant ; middleware + RLS = tenancy hybride exacte, isolation forte, simple à opérer |
| **Migrations** | Django migrations natifs + revue manuelle pour migrations destructives | Standard Django |
| **Audit log** | Table `audit_log` append-only : `actor_id`, `tenant_id`, `subject_id`, `action`, `metadata` (JSONB), `created_at` immuable (trigger PostgreSQL bloquant UPDATE/DELETE) + export S3 mensuel | RGPD + traçabilité, immutabilité au niveau DB |
| **Soft delete vs hard delete** | Hybride : soft delete par défaut (`deleted_at`) ; hard delete sous 30 jours sur demande RGPD (FR11) via job Celery planifié | RGPD : hard delete obligatoire ; soft delete utile pour ops |
| **Cache strategy** | Redis : sessions + rate limiting + cache reco (TTL 1h) + cache pages SSR Next.js (TTL 5min) | Multi-usage = 1 service à opérer |
| **Vector embeddings** | pgvector dans la DB principale | NFR : minimiser services à opérer |
| **Champ chiffré** | Bulletins chiffrés S3 (SSE) + `django-cryptography` (column-level AES-256) sur PII sensibles | Défense en profondeur |

## Authentication & Security

| Décision | Choix | Rationale |
|---|---|---|
| **Token type front↔back** | Session cookie httpOnly SameSite=Lax (pas JWT) | Stateful, révocation immédiate, plus simple, plus sécurisé pour browser app |
| **CSRF** | Token CSRF Django, injecté dans Next.js via cookie `csrftoken` + header `X-CSRFToken` | Standard Django |
| **MFA** | TOTP en MVP (django-otp) obligatoire pour conseiller/école/admin, optionnel B2C ; WebAuthn en growth pour admin | TOTP couvre 95 %, WebAuthn pour rôles très sensibles plus tard |
| **Encryption at rest** | AES-256 disk-level (cloud) + column-level (`django-cryptography`) sur PII sensibles | Défense en profondeur, NFR-S1 |
| **Token Django ↔ FastAPI** | JWT signé HS256, clé partagée, TTL 5 min, généré par Django à chaque appel | Service-to-service simple |
| **Rate limiting** | django-ratelimit : 100 req/min global IP, 10 req/min user authentifié sur endpoints sensibles | Anti-abus MVP |
| **Secrets** | Doppler (sync local + CI + prod) ou `.env` chiffré sops/age | Solo-friendly, gratuit |

## API & Communication Patterns

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

## Frontend Architecture

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

## Infrastructure & Deployment

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

## Decision Impact Analysis

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
