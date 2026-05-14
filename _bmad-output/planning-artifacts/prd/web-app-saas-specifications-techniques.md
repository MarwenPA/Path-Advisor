# Web App SaaS — Spécifications techniques

## Project-Type Overview

Path-Advisor est une **Web App SaaS hybride** combinant un produit grand public B2C (lycéens, parents) et une offre B2B (établissements scolaires, écoles partenaires). Architecture monolithique modulaire en MVP — pas de microservices prématurés — avec une séparation claire du moteur de recommandation (service IA dédié, scaling indépendant).

**Décisions architecturales structurantes :**
- Front : **SPA + SSR hybride** (Next.js ou équivalent) — pour combiner expérience interactive (graphe de parcours, dashboard) et SEO B2C (pages métiers/formations indexables)
- Back : monolithe modulaire **Django 5 + DRF + drf-spectacular (Python 3.12+)** avec service IA séparé **FastAPI** (bibliothèques ML/DL natives Python) — choix figé en Architecture Decision Document
- Stockage : PostgreSQL (transactionnel + vector store pour embeddings via pgvector) + S3 (bulletins chiffrés)
- Architecture **PoC-local-first** : tout doit pouvoir tourner sur machine de dev avec Docker Compose avant tout déploiement cloud

## Technical Architecture Considerations

**Front-end :**
- **SPA + SSR** via Next.js (ou Nuxt si écosystème Vue) — SSR pour pages métiers/formations indexables, CSR pour zones interactives (graphe parcours, dashboard conseiller)
- Responsive design mobile-first (cible primaire = lycéens sur mobile)
- Pas d'app mobile native MVP — PWA installable comme fallback

**Back-end :**
- API REST + couche GraphQL optionnelle si besoin de jointures complexes côté dashboard B2B
- Service IA séparé exposé en API interne (FastAPI ou équivalent) — versionnement modèles indépendant du back applicatif
- Job queue **Celery + Redis** (Python-native, mature, scaling clair) pour : OCR async, génération de notifications, envoi anticipé, recalculs de stats

**Données :**
- **PostgreSQL** : tables transactionnelles + référentiels (professions, formations, établissements)
- **pgvector** (extension PostgreSQL) : embeddings élèves + métiers + formations pour similarités vectorielles
- **S3-compatible (chiffré, région EU)** : bulletins PDF + exports
- Cache **Redis** : sessions, rate limiting, recos pré-calculées

**Hébergement :**
- Cible : France ou UE obligatoire (RGPD + B2B EN)
- Recommandé : Scaleway (FR), OVH (FR), AWS Paris/Frankfurt (EU)
- Cibler **SecNumCloud** en growth (argument B2B EN)

## Modèle Multi-Tenant (Hybride dès le MVP)

Choix : **tenancy hybride (option c)** dès le MVP, pas de migration risquée plus tard.

**Données partagées (cross-tenant) :**
- Référentiel professions (50+ MVP, 500+ growth)
- Référentiel formations / établissements (100+ MVP)
- Modèles de recommandation IA versionnés
- Logs d'audit et téléimétrie produit anonymisée

**Données tenant (isolées par établissement B2B) :**
- Cohorte d'élèves rattachés (relations établissement ↔ élève)
- Dashboard conseiller + reporting
- Configuration pédagogique (curriculum spécifique, périmètre métiers conseillés)

**Données utilisateur (isolées par élève) :**
- Profil personnel, bulletins, recos, parcours explorés
- Envoi anticipé : isolation forte par élève, l'école partenaire ne voit que les profils qui lui ont été envoyés

**Mécanique d'isolation :**
- Colonnes `tenant_id` (établissement) + `user_id` (élève) sur toutes les tables sensibles
- Row-Level Security PostgreSQL (RLS) pour empêcher les fuites cross-tenant au niveau DB
- Tests d'intégration de l'isolation en CI (régression critique)

## Matrice RBAC (Permissions par Rôle)

| Rôle | Scope | Permissions clés | Restrictions |
|---|---|---|---|
| **Élève** | Self | CRUD profil • vues recos/parcours • déclencher envoi anticipé (premium) • inviter parent • inviter conseiller (consentement) | — |
| **Parent** (lié) | Élève lié | Vue métiers explorés + parcours + coûts • paiement premium au profit élève | Pas d'accès bulletins détaillés, pas d'accès aux appréciations enseignants |
| **Conseiller B2B** | Cohorte établissement | Vue cohorte agrégée • vue élève individuelle (si consentement) • exports anonymisés | Pas d'écriture sur profil élève • pas d'accès identifiants/paiement |
| **École partenaire** | Profils reçus | Vue profil scolaire synthétique + motivation • 3 actions de réponse (intéressant / non aligné / RDV) • reporting interne | Pas d'accès aux autres écoles ciblées par l'élève • pas d'accès aux recos vocationnelles non liées à elle |
| **Admin Path-Advisor** | Plateforme | CRUD référentiel professions/formations • modération signalements & contenu • versioning modèles IA | Pas d'accès données personnelles élèves sauf workflow incident (escalade DPO, journal d'audit) |
| **Support utilisateur** | Tickets ouverts | Vue masquée profil + journal activité élève • répondre aux tickets | Pas d'accès bulletins sans escalade DPO + consentement élève |

## Tiers d'Abonnement

| Tier | Audience | Prix | Inclus | Limites |
|---|---|---|---|---|
| **Freemium B2C** | Lycéens, parents | Gratuit | Profil • Recos vocationnelles • 1 graphe de parcours par mois • Stats top 3 écoles | Pas d'envoi anticipé • Pas de vue parent • Pas de notifications proactives |
| **Premium B2C** | Lycéens, parents | 10,99 €/mois | Tout Freemium + graphes illimités • Stats toutes écoles • Envoi anticipé • Vue parent • Notifs proactives • RDV visio écoles | — |
| **Pilote B2B** | 5 établissements MVP | Gratuit 12 mois | Dashboard conseiller complet • Cohorte jusqu'à 250 élèves • Support email | Durée 12 mois, conversion payante ou abandon |
| **Licence B2B Standard** | Établissements (growth) | 5 000 €/an | Dashboard conseiller • Cohorte 100 utilisateurs • Support prioritaire • Exports reporting | Au-delà : palier supplémentaire |
| **Licence B2B Enterprise** | Multi-établissements / collectivités (vision) | Sur devis | Tenancy dédiée option • SLA renforcé • API exports • Audit annuel | — |

## Performance & Browser Support

**Performance MVP :**
- Latence moteur de recommandation : **< 3 s** (synchrone)
- TTFB pages publiques (SEO) : **< 1 s**
- LCP (Largest Contentful Paint) mobile : **< 2,5 s**
- Disponibilité : **99 % MVP, 99,5 % growth**

**Saisonnalité :**
- Pics **janvier-mars** (préparation Parcoursup) et **mai-juillet** (vœux + réponses)
- Auto-scaling configuré sur ces périodes (multiplier x3 la capacité de base)

**Browsers supportés :**

| Navigateur | Versions cibles |
|---|---|
| Chrome | ≥ 100 (desktop + Android) |
| Safari | ≥ 15 (macOS + iOS) |
| Firefox | ≥ 100 |
| Edge | ≥ 100 |
| Internet Explorer | Non supporté |

**Accessibilité :** RGAA 4.1 niveau AA sur parcours critiques en MVP (full RGAA en growth — cf. domain requirements).

## Stratégie SEO (B2C critique)

**Pages indexables (SSR) :**
- Pages métier : `/metiers/{slug}` — fiche profession + parcours types + écoles
- Pages formation : `/formations/{slug}` — fiche école/formation + débouchés + stats publiques
- Landing pages long-tail : `/devenir-{metier}`, `/{niveau}/quel-bac-pour-{metier}`, `/{niveau}/integrer-{ecole}`
- Pages éditoriales : guides Parcoursup, articles orientation

**Optimisations techniques :**
- Sitemap XML auto-généré et soumis à Search Console
- Balisage Schema.org : `Occupation`, `EducationalOrganization`, `Course`, `FAQPage`
- Open Graph + Twitter Cards pour partage social (canal de viralité)
- Core Web Vitals au vert (LCP, FID, CLS)
- Pas de contenu derrière JavaScript only (SSR garantit l'indexabilité)

## Stratégie Temps Réel & Asynchronisme

| Cas d'usage | Mode | Justification |
|---|---|---|
| **Recommandation vocationnelle (génération)** | Synchrone, < 3 s | Cœur de l'expérience aha — pas d'attente |
| **Graphe de parcours + stats admission** | Synchrone | Affichage immédiat après clic métier |
| **Envoi anticipé du profil à l'école** | Asynchrone (queue) | Email + push, pas critique en temps réel |
| **Réponse école → MAJ stat élève** | Asynchrone, propagation < 5 min | Notification push + email, pas de WebSocket nécessaire |
| **Import OCR bulletins** | Asynchrone, < 30 s | Traitement lourd, UX avec indicateur de progression |
| **Recalcul cohorte (dashboard conseiller)** | Asynchrone planifié (toutes les heures) | Pas de besoin temps réel |

**Décision :** **pas de WebSocket en MVP**. Le polling léger (toutes les 30s sur les pages critiques) + notifications push suffisent. Simplifie infra et coûts.

## Intégrations & Outils

**Principe directeur : PoC local first.** Tous les choix d'intégration doivent permettre un environnement de développement local complet via Docker Compose, sans dépendance dure à un service cloud. On bascule en cloud à la mise en production, mais le code reste portable.

| Type | Outil production | Équivalent PoC local | Critique en MVP ? |
|---|---|---|---|
| **Paiement B2C** | Stripe | Stripe test mode (clés sandbox locales) | Oui |
| **Email transactionnel** | Postmark ou SendGrid | **Mailpit** (capture mail local) | Oui |
| **Push notifications** | Web Push standard + OneSignal | Web Push standard local (clés VAPID dev) | Oui |
| **OCR bulletins** | AWS Textract ou Mindee | **Tesseract OCR** open source en Docker | Oui |
| **Analytics produit** | PostHog Cloud EU (Frankfurt) ou Amplitude | **PostHog self-hosted** en Docker | Oui |
| **Visio RDV école** | Lien Whereby / Daily.co | Liens jitsi.org self-hosted | Souhaitable |
| **CRM B2B** | HubSpot ou Pipedrive | Pas requis pour PoC | Préférable, peut attendre |
| **Stockage objets** | S3 EU (Scaleway, AWS Paris) | **MinIO** S3-compatible en Docker | Oui |
| **Base de données** | PostgreSQL managé (RDS, Scaleway) | PostgreSQL 16 + extension pgvector en Docker | Oui |
| **Cache / Queue** | Redis managé | Redis en Docker | Oui |
| **Modèles ML** | API service interne (FastAPI) | Même service en Docker, modèles locaux (HuggingFace) | Oui |
| **LLM (NLP appréciations enseignants)** | OpenAI / Mistral API EU | Modèle local (Mistral 7B via Ollama) pour PoC | Oui |
| **Monitoring** | Grafana Cloud + Sentry | Prometheus + Grafana + Sentry self-hosted en Docker | Oui |

**Environnement PoC local cible :**
- `docker-compose up` lance toute la stack (front, back, IA, DB, cache, queue, OCR, mail, monitoring, analytics, stockage objets)
- Seeds de référentiel professions/formations injectés au boot pour avoir un produit utilisable end-to-end sans appel cloud
- Variables d'environnement clairement séparées local / staging / production

## Implementation Considerations

**Ordre de mise en place recommandé MVP (12 sprints estimés) :**

1. **Sprints 1-2 — Fondations** : auth multi-rôle, RBAC, multi-tenant hybride, stockage chiffré bulletins, RGPD/DPIA, consentement parental email
2. **Sprints 3-4 — Onboarding élève** : profil + import bulletins (PDF + OCR + saisie manuelle assistée fallback) + déclaratif (passions, intérêts, valeurs)
3. **Sprints 5-6 — Moteur vocationnel** : architecture statistique + content-based + 50 professions référencées + UI recos avec explicabilité
4. **Sprints 7-8 — Moteur parcours** : graphe interactif + 100 formations référencées + stats admission (basées open data Parcoursup) + carte scolaire (Affelnet 3ème, Parcoursup lycéen)
5. **Sprint 9 — Premium + Stripe** : tiers freemium/premium, paiement, gating de fonctionnalités
6. **Sprint 10 — Envoi anticipé écoles** : flux complet école (auth, réception profil, 3 actions, MAJ stat), email/push, intégration aux pilotes B2B
7. **Sprint 11 — Dashboard conseiller B2B** : cohorte, vue élève (consentement), détection profils à risque, exports
8. **Sprint 12 — Polish, RGAA AA, perfs, monitoring, lancement bêta** : SEO setup, accessibilité critique, observabilité, plan incident

**Risques techniques majeurs :**
- **OCR bulletins** : formats hétérogènes selon établissements → fallback manuel essentiel + collecte de patterns pour amélioration
- **Pré-calcul stats admission** : sans modèle prédictif fin en MVP → fourchettes basées open data Parcoursup, indication explicite de l'incertitude
- **Performance moteur reco sous charge** : tests de charge sur cohorte 500 utilisateurs simultanés (= 5 % d'usage simultané sur 10K MAU growth)
- **Compatibilité PoC local ↔ cloud production** : maintenir une CI qui teste les deux modes pour détecter les divergences précoces
