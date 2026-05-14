---
stepsCompleted: [1, 2, 3, 4, 5, 6]
lastStep: 6
status: 'complete'
completedAt: '2026-05-14'
readinessStatus: 'READY'
inputDocuments:
  - "prd.md"
  - "architecture.md"
  - "ux-design-specification.md"
  - "epics.md"
contextDocuments:
  - "product-brief-Path-Advisor.md"
  - "product-ideas-backlog.md"
workflowType: 'implementation-readiness'
project_name: 'Path-Advisor'
user_name: 'Marwen.bendhahbia'
date: '2026-05-14'
---

# Implementation Readiness Assessment Report

**Date:** 2026-05-14
**Project:** Path-Advisor
**Assessor:** Marwen.bendhahbia (auto-validation BMAD workflow)

## 1. Document Inventory

### Documents found (all whole files, no sharding detected)

| Document | Path | Lines | Status |
|---|---|---|---|
| **PRD** | `_bmad-output/planning-artifacts/prd.md` | 929 | ✅ Complete (status: complete in frontmatter) |
| **Architecture** | `_bmad-output/planning-artifacts/architecture.md` | 1420 | ✅ Complete (status: complete in frontmatter) |
| **UX Design Spec** | `_bmad-output/planning-artifacts/ux-design-specification.md` | 1548 | ✅ Complete (status: complete in frontmatter, 14/14 steps) |
| **Epics & Stories** | `_bmad-output/planning-artifacts/epics.md` | 2829 | ✅ Complete (status: complete in frontmatter, 10 epics × 97 stories) |

### Context documents (not assessed, used as input)

| Document | Path | Rôle |
|---|---|---|
| Product Brief | `product-brief-Path-Advisor.md` | Vision produit (input PRD) |
| Product Ideas Backlog | `product-ideas-backlog.md` | Parking lot d'idées différées (4 entrées : moteur inverse, proba comme export, soutien scolaire, dark mode) |

### Issues détectés

- ✅ **Aucun duplicate** (whole vs sharded) — tous les documents existent en version unique whole
- ✅ **Aucun document requis manquant** — PRD + Architecture + UX + Epics présents
- ✅ Toutes les versions sont à jour suite à l'alignement Django/FastAPI du 2026-05-14

## 2. PRD Analysis

PRD lu intégralement (929 lignes), tous les requirements extraits.

### Functional Requirements (FRs) — 57 au total (52 MVP + 5 Fast-Follow)

**A. Comptes, Rôles & Conformité (12 FRs)**
- FR1 : Inscription élève ≥ 15 ans avec consentement RGPD direct
- FR2 : Inscription élève < 15 ans avec consentement parental email opt-in
- FR3 : Compte parent lié à un compte élève
- FR4 : Auth conseiller B2B MFA obligatoire
- FR5 : Auth école partenaire MFA obligatoire
- FR6 : Auth admin Path-Advisor MFA obligatoire
- FR7 : Isolation multi-tenant + matrice RBAC 6 rôles
- FR8 : Consulter liste des tiers ayant accès au profil
- FR9 : Révoquer accès tiers à tout moment
- FR10 : Export portabilité RGPD
- FR11 : Suppression compte (droit à l'oubli RGPD)
- FR12 : Journal d'audit consultable par DPO

**B. Profil Élève & Onboarding (7 FRs)**
- FR13 : Déclaration passions / intérêts / valeurs
- FR14 : Import bulletins PDF + OCR
- FR15 : Saisie manuelle notes en fallback OCR
- FR16 : Déclaration niveau scolaire + filière + spécialités
- FR17 : Mode dégradé profil incomplet sans bulletins
- FR18 : Mise à jour profil à tout moment
- FR19 : Score de complétude profil

**C. Recommandation Vocationnelle (7 FRs)**
- FR20 : Liste de métiers scorés 0-100
- FR21 : Fiche détaillée par métier
- FR22 : Signaux contributifs explicabilité IA (RGPD art. 22)
- FR23 : Demander revue humaine d'une reco
- FR24 : Signaler erreur sur fiche métier
- FR25 : Adaptation reco par niveau scolaire
- FR26 : Niveau de confiance reco profil incomplet

**D. Recommandation Parcours & Stats Admission (6 FRs)**
- FR27 : Graphes de parcours par métier
- FR28 : Fiche détaillée école / formation
- FR29 : Stat admission personnalisée par école
- FR30 : Filtres graphes (proximité, coût, sélectivité, alternance)
- FR31 : Adaptation graphe par niveau scolaire (3ème → lycée pro)
- FR32 : Favoris écoles cibles

**E. Envoi Anticipé & Espace École (8 FRs)**
- FR33 : Envoi anticipé profil élève premium
- FR34 : Motivation libre modérée
- FR35 : Notification école à chaque envoi
- FR36 : Fiche profil élève côté école (synthétique)
- FR37 : 3 actions de réponse école (intéressant / non aligné / RDV)
- FR38 : MAJ stat admission < 5 min après réponse
- FR39 : Historique envois côté élève
- FR40 : Reporting interne école

**F. Espaces Tiers Parent + Conseiller B2B (5 FRs)**
- FR41 : Vue parent métiers + parcours (sans bulletins détaillés)
- FR42 : Parent paie premium au bénéfice élève
- FR43 : Dashboard cohorte conseillère
- FR44 : Profil individuel élève côté conseillère avec consentement
- FR45 : Export reporting anonymisé cohorte

**G. Découverte & Engagement (2 FRs)**
- FR46 : Pages publiques indexables SEO
- FR47 : Notifications email événements clés

**H. Administration & Modération (5 FRs)**
- FR48 : CRUD référentiel professions / formations / écoles
- FR49 : Traitement signalements
- FR50 : Modération a priori motivations libres
- FR51 : Versioning modèles IA + dataset
- FR52 : Métriques audit ML (drift, biais)

**Fast-Follow (5 FRs — post-MVP mois 9-12)**
- FR-FF1 : Détection profils à risque dashboard conseillère
- FR-FF2 : Push web notifications
- FR-FF3 : Tableau qualité référentiel admin
- FR-FF4 : RDV visio intégré école-élève
- FR-FF5 : Parrainage / partage lien traçable

**Total FRs : 57**

### Non-Functional Requirements (NFRs) — 35 au total

**Performance (6 NFRs)** : NFR-P1 reco < 3s P95, NFR-P2 graphe < 2s P95, NFR-P3 TTFB < 1s + LCP < 2,5s, NFR-P4 OCR < 30s, NFR-P5 propagation stat < 5 min, NFR-P6 auth < 1s

**Security (9 NFRs)** : NFR-S1 chiffrement AES-256/TLS 1.3, NFR-S2 MFA staff, NFR-S3 bulletins S3 chiffré UE, NFR-S4 journal audit 3 ans, NFR-S5 secrets coffre, NFR-S6 délais RGPD, NFR-S7 DPIA, NFR-S8 OWASP + pen-test, NFR-S9 consentement parental horodaté

**Scalability (6 NFRs)** : NFR-SC1 500→10K MAU, NFR-SC2 500 concurrents, NFR-SC3 auto-scaling x3, NFR-SC4 IA déployable séparément, NFR-SC5 référentiel 50→500, NFR-SC6 100K profils

**Reliability (5 NFRs)** : NFR-R1 99% MVP, NFR-R2 sauvegarde quotidienne, NFR-R3 RTO < 4h / RPO < 1h, NFR-R4 dégradation gracieuse, NFR-R5 MTTR < 1h

**Accessibility (6 NFRs)** : NFR-A1 RGAA AA parcours critiques, NFR-A2 RGAA AA complet growth, NFR-A3 navigation clavier, NFR-A4 contraste 4.5:1, NFR-A5 alt tabulaire graphes, NFR-A6 mobile 320 px

**Integration (7 NFRs)** : NFR-I1 Stripe sandbox + prod, NFR-I2 email Mailpit/Postmark, NFR-I3 OCR Tesseract/Mindee, NFR-I4 analytics EU, NFR-I5 Etalab growth, NFR-I6 ENT/Pronote double consentement, NFR-I7 datasets Parcoursup

**Maintainability (5 NFRs)** : NFR-M1 Docker < 5 min, NFR-M2 couverture tests ≥ 70%, NFR-M3 modèles IA versionnés, NFR-M4 ADR git, NFR-M5 runbooks 1-2 personnes

**Total NFRs : 35**

### Additional Requirements (Architecture cross-cutting) — 11 ADDs

- ADD-1 Hébergement UE obligatoire ; ADD-2 PoC local-first Docker ; ADD-3 Multi-tenant RLS dès MVP ; ADD-4 Service IA séparé FastAPI ; ADD-5 Stack figée Django 5 + DRF + FastAPI ; ADD-6 Next.js SPA+SSR ; ADD-7 PostgreSQL+pgvector+Redis+S3+Celery ; ADD-8 Pas WebSocket MVP ; ADD-9 Audit trail immuable ; ADD-10 Versioning modèles IA ; ADD-11 i18n dès jour 1

### PRD Completeness Assessment

✅ **PRD complet et bien structuré** :
- Structure claire : Executive Summary + Project Classification + Success Criteria + 7 User Journeys + Domain-Specific Requirements + Innovation & Novel Patterns + Web App SaaS Spec + Project Scoping + 57 FRs + 35 NFRs
- Numérotation cohérente (FR1-FR52, FR-FF1-FF5, NFR par catégorie)
- Chaque FR a une intention claire et testable
- Chaque NFR a une cible mesurable (latence en s, %, ratio)
- Domain-specific requirements (RGPD, RGAA, EdTech) bien identifiés
- Risques produit identifiés avec mitigations
- Tableau de bord MVP vs Growth distinct

✅ **Cohérence post-mise-à-jour Django/FastAPI** :
- Mention Django 5 + DRF + FastAPI confirmée dans "Technical Architecture" (ligne 484)
- Mention Celery + Redis confirmée dans "Implementation Considerations" (ligne 498)
- Aucune référence à Node.js ou BullMQ / Sidekiq résiduelle

⚠️ **Point d'attention mineur** :
- Le PRD utilise encore le terme "monolithe modulaire" en mentionnant Django + FastAPI déployés séparément. Vocabulaire à harmoniser : strictement, on a un monolithe modulaire Django + un service séparé FastAPI (donc 2 services). Non bloquant pour l'implémentation, juste une rigueur sémantique.

## 3. Epic Coverage Validation

`epics.md` lu intégralement (2 829 lignes, 10 épics × 97 stories). Coverage map extrait et croisé avec les 57 FRs du PRD.

### Coverage Matrix (extrait du document epics.md)

| FR | Epic primaire | Story principale | Status |
|---|---|---|---|
| **FR1** Inscription élève ≥ 15 | Epic 1 | Story 1.3 | ✅ |
| **FR2** Inscription élève < 15 + consentement parental | Epic 1 | Story 1.4 | ✅ |
| **FR3** Compte parent lié | Epic 1 + Epic 6 | Story 1.4 + Story 6.1 | ✅ |
| **FR4** Auth conseiller MFA | Epic 1 | Stories 1.5 + 1.6 | ✅ |
| **FR5** Auth école MFA | Epic 1 + Epic 5 | Stories 1.5 + 1.6 + 5.6 | ✅ |
| **FR6** Auth admin MFA | Epic 1 | Stories 1.5 + 1.6 | ✅ |
| **FR7** Multi-tenant + RBAC | Epic 1 | Stories 1.7 + 1.8 | ✅ |
| **FR8** Liste tiers ayant accès | Epic 1 + Epic 6 | Story 1.9 + 6.11 | ✅ |
| **FR9** Révocation accès tiers | Epic 1 + Epic 6 | Story 1.10 + 6.11 | ✅ |
| **FR10** Export portabilité RGPD | Epic 1 | Story 1.11 | ✅ |
| **FR11** Suppression compte | Epic 1 | Story 1.12 | ✅ |
| **FR12** Journal audit DPO | Epic 1 | Story 1.13 | ✅ |
| **FR13** Passions / intérêts / valeurs | Epic 2 | Story 2.1 | ✅ |
| **FR14** Import bulletins OCR | Epic 2 | Story 2.3 | ✅ |
| **FR15** Saisie manuelle fallback | Epic 2 | Story 2.4 | ✅ |
| **FR16** Niveau scolaire + filière + spés | Epic 2 | Story 2.2 | ✅ |
| **FR17** Mode dégradé sans bulletins | Epic 2 | Story 2.5 | ✅ |
| **FR18** Mise à jour profil | Epic 2 | Story 2.6 | ✅ |
| **FR19** Score de complétude | Epic 2 | Story 2.7 | ✅ |
| **FR20** Liste métiers scorés | Epic 3 | Story 3.4 | ✅ |
| **FR21** Fiche métier détaillée | Epic 3 | Story 3.5 | ✅ |
| **FR22** Explicabilité IA (RGPD art. 22) | Epic 3 | Story 3.6 | ✅ |
| **FR23** Revue humaine reco | Epic 3 | Story 3.7 | ✅ |
| **FR24** Signaler erreur métier | Epic 3 | Story 3.8 | ✅ |
| **FR25** Adaptation reco niveau scolaire | Epic 3 | Story 3.9 | ✅ |
| **FR26** Niveau confiance profil incomplet | Epic 3 | Story 3.10 | ✅ |
| **FR27** Graphes parcours | Epic 4 | Story 4.3 | ✅ |
| **FR28** Fiche école / formation | Epic 4 | Story 4.4 | ✅ |
| **FR29** Stat admission personnalisée | Epic 4 | Story 4.5 | ✅ |
| **FR30** Filtres graphes | Epic 4 | Story 4.6 | ✅ |
| **FR31** Graphe niveau scolaire (3ème → lycée pro) | Epic 4 | Story 4.7 | ✅ |
| **FR32** Favoris écoles cibles | Epic 4 | Story 4.8 | ✅ |
| **FR33** Envoi anticipé premium | Epic 5 | Story 5.4 | ✅ |
| **FR34** Motivation libre modérée | Epic 5 | Story 5.5 | ✅ |
| **FR35** Notification école envoi | Epic 5 | Story 5.6 | ✅ |
| **FR36** Fiche profil élève côté école | Epic 5 | Story 5.6 | ✅ |
| **FR37** 3 actions réponse école | Epic 5 | Story 5.7 | ✅ |
| **FR38** MAJ stat admission < 5 min | Epic 5 | Story 5.8 | ✅ |
| **FR39** Historique envois élève | Epic 5 | Story 5.9 | ✅ |
| **FR40** Reporting interne école | Epic 5 | Story 5.10 | ✅ |
| **FR41** Vue parent (sans bulletins détaillés) | Epic 6 | Stories 6.2 + 6.3 | ✅ |
| **FR42** Parent paie premium | Epic 6 | Story 6.4 | ✅ |
| **FR43** Dashboard cohorte conseillère | Epic 6 | Story 6.6 | ✅ |
| **FR44** Profil individuel élève côté conseillère | Epic 6 | Stories 6.7 + 6.8 | ✅ |
| **FR45** Export reporting anonymisé | Epic 6 | Story 6.9 | ✅ |
| **FR46** Pages publiques SEO | Epic 7 | Stories 7.1-7.6 | ✅ |
| **FR47** Notifications email | Epic 8 | Stories 8.2-8.5 | ✅ |
| **FR48** CRUD référentiel | Epic 9 | Stories 9.1 + 9.2 | ✅ |
| **FR49** Traitement signalements | Epic 9 | Story 9.3 | ✅ |
| **FR50** Modération motivations | Epic 9 | Story 9.4 | ✅ |
| **FR51** Versioning modèles IA | Epic 9 | Story 9.5 | ✅ |
| **FR52** Métriques audit ML | Epic 9 | Story 9.6 | ✅ |
| **FR-FF1** Profils à risque | Epic 10 | Story 10.1 | ✅ |
| **FR-FF2** Push web | Epic 10 | Story 10.2 | ✅ |
| **FR-FF3** Tableau qualité référentiel | Epic 10 | Story 10.3 | ✅ |
| **FR-FF4** RDV visio intégré | Epic 10 | Story 10.4 | ✅ |
| **FR-FF5** Parrainage / partage | Epic 10 | Story 10.5 | ✅ |

### Missing Requirements

**Aucun FR manquant.** Tous les 57 FRs sont mappés à au moins une story avec acceptance criteria adressant l'exigence.

### Coverage Statistics

| Métrique | Valeur |
|---|---|
| **Total PRD FRs (MVP)** | 52 |
| **Total PRD FRs (Fast-Follow)** | 5 |
| **Total FRs requis** | 57 |
| **FRs couverts en epics** | 57 |
| **Coverage percentage** | **100 %** |
| **FRs in epics but NOT in PRD** | 0 (aucune story orpheline) |
| **FRs in PRD but NOT in epics** | 0 (aucune lacune) |

### FRs cross-epics (multi-coverage)

Certains FRs sont couverts dans plusieurs épics — cela reflète des préoccupations cross-cutting (auth + RBAC) plutôt qu'une duplication problématique :

- **FR3** (compte parent lié) : Epic 1 (compte créé) + Epic 6 (workflow invitation)
- **FR5** (auth école) : Epic 1 (auth + MFA générique) + Epic 5 (espace école et workflow réception)
- **FR8, FR9** (tiers / révocation) : Epic 1 (composant `PermissionList` basique) + Epic 6 (composant étendu avec dernière consultation + audit visible)

✅ **Pas de redondance problématique** — chaque mention cross-epics apporte une couche additionnelle, pas une duplication.

### Coverage Validation Verdict

✅ **100 % de couverture FRs avec traçabilité claire** — tous les FRs sont mappés à un epic primaire + story principale + AC testables. La matrice est exhaustive et auditable.

## 4. UX Alignment

UX Design Specification trouvé : `ux-design-specification.md` (1 548 lignes, 14/14 steps complets, status: complete).

### UX ↔ PRD Alignment

| Aspect | UX Spec | PRD | Verdict |
|---|---|---|---|
| **Personas** | Hiérarchie 3 tiroirs : Sarah Protagoniste 🎬 / Mehdi+Léa+Dupont Témoins 🧪 / Martin+Garcia+Karim Promesses 📦 | 7 user journeys (Sarah, Mehdi, Léa, Dupont, Martin, Garcia, Karim) | ✅ Cohérent — UX spec priorise les personas du PRD pour le design MVP |
| **Deux moments aha** | Step 7 "Defining Experience" : verbe partageable "Voir ton chemin et tes chances" | Innovation #1 Architecture en double moteur articulé | ✅ Aligné |
| **Job dominant** | Job narratif-défensif (Step 4 émotion + party mode John) | "Sarah formule ses vœux Parcoursup avec clarté" (journey 1) | ✅ Enrichit le PRD — UX explicite la dimension narrative-défensive |
| **Mode dégradé** | Pattern "Mode normal = mode dégradé" (UX-DR25) | FR17 expérience dégradée sans bulletins | ✅ Aligné — UX raffine en mode visuellement indiscernable |
| **Explicabilité IA** | "Explicabilité comme munition narrative" (Step 7 + party mode) | FR22 + RGPD art. 22 | ✅ Aligné |
| **Continuité temporelle** | Pattern UX-DR29 "Retour avec delta" + composant `DeltaRecap` | Vision 3 ans : "compagnon d'orientation de référence" + FR47 notifications | ✅ Aligné |
| **Neutralité commerciale** | Pattern "Neutralité comme propriété émergente de l'UI" (Step 5) | Différenciateur structurel du PRD | ✅ Aligné — UX matérialise la promesse |

### UX ↔ Architecture Alignment

| Aspect | UX Spec | Architecture | Verdict |
|---|---|---|---|
| **Stack frontend** | shadcn/ui + Tailwind v4 + Radix UI (Step 6) | Next.js + TypeScript + Tailwind v4 (apps/web) | ✅ Aligné |
| **Stack backend** | Mentions Next.js seul implicite (UX = frontend focus) | Django 5 + DRF + drf-spectacular + FastAPI séparé | ✅ Compatible (UX ne contraint pas le back) |
| **Performance budget mobile** | TTI < 4 s 4G, LCP < 2,5 s, < 200 ko JS critique par écran (UX-DR34) | Core Web Vitals au vert + Lighthouse CI | ✅ Aligné avec NFR-P3 |
| **RGAA AA** | Audit axe-core en CI + VoiceOver/NVDA trimestriel (UX-DR33) | RGAA AA niveau cible (Architecture) | ✅ Aligné avec NFR-A1 |
| **Animation graphe** | 720-800 ms en 5 phases, anti-cirque sur retour (Step 7) | react-flow ou SVG custom — décision différée prototypage sprint 5 | ✅ Aligné — décision tech ouverte mais cadrée |
| **Multi-tenant + RBAC** | Composant `PermissionList` + `ConsentDialog` cadrent 6 rôles | Multi-tenant RLS + RBAC 6 rôles documenté | ✅ Aligné |
| **Mode sombre** | Reporté en backlog post-MVP (UX update 2026-05-13) | Architecture ne mentionne pas dark mode obligatoire | ✅ Cohérent — décision Marwen propagée correctement |

### UX additions au-delà du PRD (non-contradictoires)

L'UX spec apporte des spécifications détaillées qui *enrichissent* le PRD sans le contredire :

- **35 UX Design Requirements** (UX-DR1 à UX-DR35) — couvrent tokens (couleur R1 Vermillon + Inter + spacing 4 px + motion), 18 composants Couche 3, patterns transverses, accessibilité, responsive
- **Test 3 mots Caravaggio** (test de hiérarchie visuelle pour l'écran graphe-récit) — pas mentionné dans PRD mais opérationnalise NFR-P2
- **Pattern phrase recopiable** (italic + brand accent + tap-to-copy) — ressort du job narratif-défensif identifié en party mode
- **Animation séquentielle 720-800 ms** en 5 phases pour le graphe — opérationnalise NFR-P2 et "deuxième aha"
- **Idées différées au backlog** : 3 idées produits captées en cours d'UX (moteur inverse, proba comme export, soutien scolaire) + dark mode

✅ **Aucune contradiction détectée.** L'UX spec est cohérente avec le PRD et l'Architecture.

### Alignment Issues

**Aucun écart problématique.**

### Warnings

⚠️ **1 warning mineur (non-bloquant)** :

L'UX spec mentionne 5 entretiens utilisateurs Sarah + 3 conseillères en 6 semaines (validation terrain Maya, party Step 2) comme **work stream parallèle obligatoire** avant que le design system MVP soit gelé. Ce n'est pas un *requirement* PRD ou Architecture, mais c'est un **engagement méthodologique pris dans la documentation UX**.

→ **Action recommandée avant Sprint 5** (premier sprint touchant les composants UX critiques `ScoreVocationnel`, `GraphParcours`) : lancer la validation terrain pour passer Sarah et Mme Dupont au statut 🟢 Validée. Sinon le risque "personas en carton-pâte" (Maya party mode Step 2) reste ouvert.

### UX Alignment Verdict

✅ **UX, PRD et Architecture sont alignés.** L'UX spec enrichit sans contredire. La cohérence post-mise-à-jour Django/FastAPI est confirmée (UX ne dépend pas du choix backend).

## 5. Epic Quality Review

Audit rigoureux des 10 épics × 97 stories contre les standards BMAD.

### Epic-par-Epic Quality Check

| Epic | User value focus | Standalone | Story sizing | Forward deps | DB creation incremental | ACs G/W/T | Verdict |
|---|---|---|---|---|---|---|---|
| **Epic 1** Foundation | ✅ "L'utilisateur crée un compte sécurisé conforme RGPD" | ✅ Foundation autonome | ✅ 14 stories de 1-4 j | ⚠️ 1 mineur (Story 1.10 utilise `ConsentDialog` Story 1.14) | ✅ Incremental (1.7, 1.8, 1.13) | ✅ | ✅ Pass |
| **Epic 2** Profil & Onboarding | ✅ "L'élève complète son profil en < 12 min" | ✅ Dépend Epic 1, autonome dans son domaine | ✅ 9 stories de 1-4 j | ✅ Aucune | ✅ Tables ajoutées par story | ✅ | ✅ Pass |
| **Epic 3** Recommandation Vocationnelle | ✅ "L'élève reçoit 8 métiers scorés — premier aha" | ✅ Dépend Epic 2, autonome | ⚠️ Story 3.2 (référentiel 50 métiers) = 5-8 j de curation (admissible, explicite) | ✅ Aucune | ✅ Story 3.2 crée table `professions` | ✅ | ✅ Pass |
| **Epic 4** Graphe & Stats | ✅ "L'élève voit son graphe-récit — deuxième aha" | ✅ Dépend Epic 3, autonome | ⚠️ Story 4.9 `GraphParcours` = 8-12 j (note risque, à splitter en sous-jalons au sprint 5) — déjà documenté | ✅ Aucune | ✅ Stories 4.1 + 4.2 créent tables | ✅ | ✅ Pass |
| **Epic 5** Premium & Envoi Anticipé | ✅ "L'élève premium envoie son profil — l'école répond" | ✅ Dépend Epic 4, autonome | ✅ 12 stories de 1-4 j | ✅ Aucune | ✅ Story 5.2 crée table `subscriptions` | ✅ | ✅ Pass |
| **Epic 6** Espaces Tiers | ✅ "Parent voit, conseillère utilise dashboard cohorte" | ✅ Dépend Epic 1-3, autonome | ✅ 11 stories de 1-4 j | ✅ Aucune | ✅ Story 6.5 crée tenant établissement | ✅ | ✅ Pass |
| **Epic 7** SEO | ✅ "Sarah trouve via Google et arrive sur page indexable" | ✅ Parallélisable | ✅ 7 stories de 2-3 j | ✅ Aucune | ✅ Pas de nouvelles tables (lecture seule du référentiel existant) | ✅ | ✅ Pass |
| **Epic 8** Continuité & Notifications | ✅ "Utilisateur revient et voit ce qui a bougé" | ⚠️ Dépend de tous pour avoir du contenu — intentionnel, c'est une couche d'engagement | ✅ 7 stories de 1-3 j | ✅ Aucune | ✅ Story 8.2 crée table `notification_preferences` | ✅ | ✅ Pass |
| **Epic 9** Back-office Admin | ✅ Karim maintient référentiel + modère | ✅ Dépend Epic 3+4 (référentiel à curer) | ✅ 6 stories de 2-4 j | ✅ Aucune | ✅ Story 9.5 crée table `model_versions` | ✅ | ✅ Pass |
| **Epic 10** Fast-Follow | ✅ Features post-MVP (profils à risque, push, parrainage, RDV visio, parrainage) | ✅ Indépendant, post-MVP | ✅ 6 stories de 2-3 j | ✅ Aucune | ✅ Pas de tables core nouvelles | ✅ | ✅ Pass |

### Story Sizing Analysis

Distribution effort par story :

| Effort | Nombre de stories | % | Statut |
|---|---|---|---|
| 1-2 jours | ~25 | 26 % | Idéal pour single dev session |
| 2-3 jours | ~40 | 41 % | Idéal pour single dev session |
| 3-4 jours | ~25 | 26 % | Plage haute, dans la norme |
| 5-8 jours | 5 | 5 % | À surveiller (curation content / complexité) |
| 8-12 jours | 2 | 2 % | **Trop grand** — à splitter |

### Stories problématiques identifiées (mineur, non-bloquant)

| Story | Effort | Issue | Recommandation |
|---|---|---|---|
| **Story 4.9 `GraphParcours`** | 8-12 j | Composant le plus complexe (animation séquentielle 5 phases + alternative tabulaire + low-data + comparaison) | ⚠️ **À splitter en 4 sous-jalons** au prototypage Sprint 5 : MVP graph statique → animation → comparaison → low-data mode. *Déjà documenté en Epic 4 risques.* |
| **Story 4.1 Référentiel 100+ formations** | 8-12 j | Curation content/data ops (pas du dev) | Admissible — explicitement noté comme curation. Peut être parallélisé avec un freelance rédacteur orientation. |
| **Story 3.2 Référentiel 50 métiers MVP** | 5-8 j | Idem, curation content | Admissible. |

### Forward Dependencies — Catch List

**Une seule micro-incohérence détectée** :

| Story consommatrice | Composant utilisé | Story créatrice | Risque |
|---|---|---|---|
| Story 1.10 (Révocation accès tiers) | `ConsentDialog` | Story 1.14 (créée en fin d'Epic 1) | 🟡 Mineur |
| Story 1.12 (Suppression compte) | `ConsentDialog` | Story 1.14 | 🟡 Mineur |
| Story 6.6, 6.7, 6.8 (B2B) | `ConsentDialog`, `CohortDashboard` | Stories 6.10, 6.11 (créées plus tard dans Epic 6) | 🟡 Mineur (intra-epic) |

**Recommandation** : ré-ordonner l'implémentation de Story 1.14 (`ConsentDialog`) **avant** les Stories 1.9-1.13 dans Epic 1, ou implémenter une version stub minimale qui sera enrichie ensuite. **Aucun blocage** — c'est un détail de séquencement dev qu'un dev senior tranchera trivialement. À noter en planning de sprint.

### Database / Entity Creation Validation

✅ **Pattern incremental respecté** — aucune story ne crée toutes les tables upfront.

Inventaire des stories créant de nouvelles tables :

- Story 1.7 → tables `rbac_roles`, `rbac_permissions`
- Story 1.8 → ajout colonnes `tenant_id` + RLS policies sur tables sensibles
- Story 1.13 → table `audit_log` (append-only)
- Story 2.3 → stockage S3 chiffré bulletins (table `bulletin_uploads`)
- Story 3.2 → table `professions`
- Story 4.1 → tables `schools` + `formations`
- Story 4.2 → table `admission_stats_history`
- Story 5.2 → table `subscriptions`
- Story 6.5 → `tenant_id` établissement (réutilise structure existante)
- Story 8.2 → table `notification_preferences`
- Story 9.5 → table `model_versions`

Chaque story crée seulement ce dont elle a besoin. Pattern conforme BMAD.

### Starter Template Validation

✅ **Conformité greenfield** :

- Projet greenfield (pas de starter spécifique)
- **Story 1.1** = "Initialisation du projet (Next.js + Django + FastAPI + Docker)" — couvre l'initialisation complète du mono-repo avec les 3 apps Python/TS, conforme à l'Architecture Decision Document
- CI/CD setup minimal inclus dans Story 1.1 (GitHub Actions, lint, tests)
- Setup CI étendu (axe-core, Lighthouse) au sprint 4 (cf NFR-A1 et UX-DR33)

### Best Practices Compliance Checklist Final

| Critère | Score | Note |
|---|---|---|
| ✅ Tous les épics délivrent du user value | 10/10 | Aucun "Setup Database" ou épic technique sans user value |
| ✅ Tous les épics fonctionnent indépendamment dans leur domaine | 10/10 | Epic 8 dépend des autres pour avoir du contenu — intentionnel |
| ✅ Stories appropriées (< 4 j idéal, 8-12 j max documenté) | 95/97 | 2 stories à splitter au prototypage (4.9, 4.1) — déjà documenté |
| ⚠️ Forward dependencies | 4 cas mineurs détectés | Tous intra-epic, contournables par ré-ordonnancement ou stub. Aucun cross-epic. |
| ✅ DB tables créées quand nécessaires | 11/11 | Pattern incremental respecté partout |
| ✅ Acceptance Criteria Given/When/Then | 97/97 | Tous testables et spécifiques |
| ✅ Traceability FR → Epic → Story | 57/57 | 100 % coverage |

### Quality Findings by Severity

#### 🔴 Critical Violations

**Aucune.** Pas d'épic technique sans user value, pas de dépendance circulaire, pas de story épic-sized impossible.

#### 🟠 Major Issues

**Aucune.** Tous les épics et stories respectent les standards.

#### 🟡 Minor Concerns (4)

1. **Story 4.9 `GraphParcours` 8-12 j** — à splitter en sous-jalons au sprint 5 (déjà documenté dans Epic 4 risques)
2. **Stories 4.1 + 3.2 (curation référentiels) 5-8 et 8-12 j** — curation content/data ops, admissible si parallélisé avec un freelance rédacteur
3. **Ré-ordonnancement intra-epic recommandé** : Story 1.14 (`ConsentDialog`) avant Stories 1.10/1.12 ; Stories 6.10/6.11 (`CohortDashboard`, `PermissionList`) avant Stories 6.6-6.8. Décision de planning sprint.
4. **Engagement validation terrain** (5 entretiens Sarah + 3 conseillères, cf UX Step 4) — pas une violation d'epic quality mais un work stream parallèle à lancer avant sprint 5.

### Epic Quality Verdict

✅ **Tous les épics passent le quality review.** 0 critical, 0 major, 4 mineurs non-bloquants. Le découpage en 10 épics × 97 stories est cohérent avec les standards BMAD : organisation par user value, indépendance, DB incremental, ACs testables, traceability 100 %.

## 6. Summary and Recommendations

### Overall Readiness Status

# ✅ **READY**

Path-Advisor est **prêt à entrer en Phase 4 — Implementation**. Aucun blocage critique ou majeur n'a été détecté à travers les 4 documents de planification (PRD, Architecture, UX Spec, Epics & Stories). La cohérence post-mise-à-jour Django/FastAPI est confirmée.

### Synthèse globale

| Dimension | Verdict | Score |
|---|---|---|
| **Document Discovery** | Tous documents présents, aucun duplicate, aucun fichier manquant | ✅ Pass |
| **PRD Analysis** | 57 FRs + 35 NFRs + 11 ADDs, structure rigoureuse, alignement Django/FastAPI confirmé | ✅ Pass |
| **Epic Coverage** | 100 % FRs couverts (57/57), 0 orphelin, 0 lacune | ✅ Pass |
| **UX Alignment** | UX cohérent avec PRD + Architecture, enrichissements non-contradictoires | ✅ Pass + 1 warning méthodologique non-bloquant |
| **Epic Quality** | 0 critical, 0 major, 4 minor non-bloquants documentés | ✅ Pass |

**Score global : 5/5 critères passés** — aucune zone rouge ni orange.

### Critical Issues Requiring Immediate Action

**Aucune.** Aucun problème critique ou majeur identifié dans l'ensemble du dossier de planification.

### Issues mineures à anticiper (non-bloquantes)

1. **Validation terrain utilisateurs à lancer** *avant* Sprint 5 (engagement UX Step 4 / party Maya) — 5 entretiens Sarah + 3 conseillères en 6 semaines pour passer les personas en statut 🟢 Validée. Sinon risque "personas en carton-pâte".
2. **Splitter Story 4.9 `GraphParcours`** au moment du prototypage Sprint 5 — découper en 4 sous-jalons : (a) MVP graph statique, (b) ajout animation 720-800 ms, (c) comparaison 2 chemins, (d) low-data mode.
3. **Ré-ordonnancer intra-Epic 1** : implémenter Story 1.14 (`ConsentDialog`) *avant* Stories 1.10 / 1.12 qui le consomment. Idem ré-ordonner Stories 6.10 / 6.11 avant 6.6-6.8.
4. **Stories de curation référentiels** (3.2 métiers + 4.1 formations) — 5-8 j et 8-12 j respectivement. Identifier un freelance rédacteur orientation pour paralléliser avec le dev.
5. **Vocabulaire PRD** : harmoniser "monolithe modulaire" — strictement, on a *monolithe Django + service séparé FastAPI* (2 services). Détail sémantique non-bloquant.

### Recommended Next Steps

**Immédiat (cette semaine)** :

1. ✅ **Activer `/bmad-sprint-planning`** — c'est l'étape **required** suivante en Phase 4 (Implementation). Elle produit le plan d'exécution sprint-par-sprint à partir des 97 stories validées.
2. 🚨 **Lancer le recrutement utilisateurs testeurs** en work stream parallèle : 5 lycéens Sarah-like + 3 conseillères d'orientation. Cible : finir les entretiens avant le Sprint 5 (semaine 10-12 du MVP).
3. ✅ **Acheter le téléphone fissuré** (Android d'occasion ≤ 80 €) mentionné dans UX Step 13 — device cible plancher pour tests mensuels.
4. **Identifier un freelance rédacteur orientation** pour la curation parallèle des référentiels (Stories 3.2 + 4.1).

**Sprint 1 (semaines 1-2)** :

1. **Exécuter Epic 1 stories 1.1 + 1.2** — Initialisation Next.js + Django + FastAPI + Docker + tokens design R1 Vermillon.
2. **Setup CI / CD complet** — GitHub Actions + axe-core + Lighthouse + bundle budget.
3. **Mini-audit Niche.com** (2 h, 10 screenshots annotés) — différé Step 8 UX, à boucler avant le prototypage `GraphParcours` au sprint 5.

**À reprendre en cours de MVP (jalons décisionnels)** :

1. **Sprint 5 — Prototypage `GraphParcours`** : décision finale react-flow vs SVG custom + splitting de la Story 4.9 en sous-jalons.
2. **Mi-MVP (~Sprint 7-8)** — Si premium B2C ne converti pas à 5 % à mi-parcours, reconsidérer pivot business infrastructure institutionnelle B2B2C (Victor party Step 2).
3. **Backlog post-MVP** — Reprendre les 4 idées différées (`product-ideas-backlog.md`) : moteur inverse, proba comme export first-class, soutien scolaire (piste A diagnostic seul), dark mode.

### Workflows BMAD à enchaîner

| Workflow | Quand | Description |
|---|---|---|
| **`/bmad-sprint-planning`** | **MAINTENANT** | Required — produit le plan d'exécution sprint-par-sprint à partir des 97 stories |
| **`/bmad-testarch-test-design`** | Optionnel, recommandé avant Sprint 5 | Plan de test basé sur les risques pour Epic 1 (RGPD / auth) et Epic 4 (`GraphParcours`) |
| **`/bmad-testarch-framework`** | Sprint 1-2 | Setup Playwright + pytest-django (déjà mentionné Story 1.1) |
| **`/bmad-testarch-ci`** | Sprint 1-2 | Pipeline qualité (axe-core + Lighthouse + bundle budget) |
| **`/bmad-create-story`** | Avant chaque sprint dev | Story enrichie avec contexte complet d'implémentation, 1 story à la fois (cible : Story 1.1 d'abord) |
| **`/bmad-dev-story`** | Pour chaque story | Exécution avec agent dev (Amelia) |

### Final Note

Cette évaluation a identifié **0 issues critiques + 4 issues mineures non-bloquantes** à travers 5 catégories de validation. **Aucune correction préalable n'est requise** avant de démarrer l'implémentation.

Les 4 issues mineures sont des **points d'attention de planning de sprint** plutôt que des défauts de planification. Elles peuvent être adressées en cours de route :
- Le ré-ordonnancement intra-epic est trivial à gérer au sprint planning
- Le splitting de Story 4.9 se fera naturellement au prototypage
- La validation terrain et la curation parallèle nécessitent simplement d'être lancées tôt

**Verdict final : Path-Advisor est prêt pour Phase 4 — Implementation. Marwen peut sereinement enchaîner avec `/bmad-sprint-planning` pour produire le plan d'exécution.**

---

**Assessment terminé : 2026-05-14**
**Assessor : Marwen Ben Dhahbia (auto-validation BMAD workflow)**
**Méthodologie : BMad Method v6 — bmad-check-implementation-readiness**
