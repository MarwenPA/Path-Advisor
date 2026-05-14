# Project Context Analysis

## Requirements Overview

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

## Technical Constraints & Dependencies

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

## Cross-Cutting Concerns Identified

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
