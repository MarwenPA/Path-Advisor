# Architecture Validation Results

## Coherence Validation

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

## Requirements Coverage Validation

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

## Implementation Readiness Validation

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

## Gap Analysis Results

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

## Validation Issues Addressed

Les 6 important gaps ci-dessus n'ont pas été corrigés dans l'architecture parce qu'ils nécessitent soit des décisions externes (DPIA), soit de l'implémentation (composants), soit de la configuration runtime (cookies, coverage). Ils sont listés explicitement comme actions de sprint 1 dans le handoff ci-dessous.

## Architecture Completeness Checklist

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

## Architecture Readiness Assessment

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

## Implementation Handoff

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
