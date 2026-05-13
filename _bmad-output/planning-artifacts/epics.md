---
stepsCompleted: [1, 2, 3, 4]
lastStep: 4
status: 'complete'
completedAt: '2026-05-13'
inputDocuments:
  - "prd.md"
  - "architecture.md"
  - "ux-design-specification.md"
workflowType: 'epics-and-stories'
project_name: 'Path-Advisor'
user_name: 'Marwen.bendhahbia'
date: '2026-05-13'
scope: 'MVP + Fast-Follow'
---

# Path-Advisor — Epic Breakdown

## Overview

Ce document décompose les requirements du PRD, de la spécification UX et de l'architecture en épics et stories implémentables pour Path-Advisor. Périmètre : **52 FRs MVP + 5 FRs Fast-Follow + 35 NFRs + 11 contraintes Architecture + 35 UX Design Requirements**.

## Requirements Inventory

### Functional Requirements

#### A. Comptes, Rôles & Conformité

- **FR1** : Un élève (≥ 15 ans) peut créer un compte sans intervention parentale et accepter explicitement les conditions d'usage RGPD
- **FR2** : Un élève (< 15 ans) peut créer un compte via un consentement parental obtenu par opt-in email envoyé à un parent désigné
- **FR3** : Un parent peut créer un compte parent lié à un compte élève existant, après invitation explicite de l'élève
- **FR4** : Un conseiller d'orientation peut s'authentifier sur un espace B2B dédié avec MFA obligatoire
- **FR5** : Une école partenaire peut s'authentifier sur un espace admissions dédié avec MFA obligatoire
- **FR6** : Un admin Path-Advisor peut s'authentifier sur un back-office dédié avec MFA obligatoire
- **FR7** : Le système peut isoler les données par tenant (établissement B2B) et par utilisateur (élève) selon une matrice RBAC documentée
- **FR8** : Un élève peut consulter à tout moment la liste de tous les tiers ayant accès à son profil (parent, conseiller, école partenaire)
- **FR9** : Un élève peut révoquer à tout moment l'accès accordé à un tiers
- **FR10** : Un élève peut exporter l'intégralité de ses données personnelles (droit à la portabilité RGPD)
- **FR11** : Un élève peut demander la suppression complète de son compte et de toutes ses données (droit à l'oubli RGPD)
- **FR12** : Le système peut produire un journal d'audit de tous les accès aux données personnelles d'un élève, consultable par le DPO

#### B. Profil Élève & Onboarding

- **FR13** : Un élève peut déclarer ses passions, centres d'intérêt et valeurs via un questionnaire structuré
- **FR14** : Un élève peut importer ses bulletins scolaires en format PDF, et le système peut extraire automatiquement notes et appréciations enseignants par OCR
- **FR15** : Un élève peut saisir manuellement ses notes et appréciations dans un formulaire structuré lorsque l'OCR échoue ou est indisponible
- **FR16** : Un élève peut déclarer son niveau scolaire (3ème, 2nde, 1ère, Terminale, post-bac), sa filière (général, technologique, professionnel) et ses spécialités
- **FR17** : Un élève peut compléter son profil partiellement et accéder à une expérience dégradée tant que ses bulletins ne sont pas importés
- **FR18** : Un élève peut mettre à jour son profil à tout moment (bulletins, passions, changement de filière)
- **FR19** : Un élève peut visualiser un score de complétude de son profil et identifier les éléments manquants

#### C. Recommandation Vocationnelle

- **FR20** : Un élève peut recevoir une liste personnalisée de métiers recommandés, scorés sur une échelle de 0 à 100, dès la complétion du déclaratif
- **FR21** : Un élève peut consulter, pour chaque métier recommandé, une fiche détaillée (description, journée type, prérequis, débouchés, revenu médian)
- **FR22** : Un élève peut consulter, pour chaque métier recommandé, les signaux qui ont contribué à son score (explicabilité IA, RGPD art. 22)
- **FR23** : Un élève peut demander une revue humaine d'une recommandation qu'il juge incorrecte ou choquante
- **FR24** : Un élève peut signaler une erreur ou une information obsolète sur la fiche métier
- **FR25** : Le système peut adapter la nature des recommandations vocationnelles au niveau scolaire de l'élève (3ème → métiers compatibles bac pro ou général)
- **FR26** : Le système peut afficher un niveau de confiance sur chaque recommandation lorsque le profil est incomplet

#### D. Recommandation de Parcours & Stats d'Admission

- **FR27** : Un élève peut consulter, pour chaque métier sélectionné, un ou plusieurs graphes de parcours scolaires menant à ce métier
- **FR28** : Un élève peut consulter, pour chaque école / formation d'un graphe, une fiche détaillée (frais, durée, sélectivité, débouchés, dates de candidature)
- **FR29** : Un élève peut consulter une statistique d'admission personnalisée (probabilité ou fourchette) pour chaque école cible, basée sur son profil scolaire
- **FR30** : Un élève peut filtrer les graphes selon des critères (proximité géographique, coût maximum, niveau de sélectivité, alternance possible)
- **FR31** : Le système peut adapter le graphe au niveau scolaire de l'élève (graphe partant d'un lycée pro associé pour un élève de 3ème orienté bac pro)
- **FR32** : Un élève peut sauvegarder des écoles cibles dans une liste de favoris pour comparaison

#### E. Envoi Anticipé Écoles & Espace École

- **FR33** : Un élève premium peut déclencher un "envoi anticipé" de son profil à une école partenaire
- **FR34** : Un élève premium peut accompagner son envoi anticipé d'une motivation libre (texte modéré côté admin)
- **FR35** : Une école partenaire peut recevoir une notification (email + push) à chaque profil envoyé en anticipé
- **FR36** : Une école partenaire peut consulter une fiche profil élève synthétique (données scolaires, motivation, métier visé, parcours sélectionné), sans accès aux autres recos ou écoles ciblées
- **FR37** : Une école partenaire peut répondre à un envoi anticipé via 3 actions : *Profil intéressant — candidature encouragée* / *Profil non aligné* / *Demande d'entretien*
- **FR38** : Le système peut mettre à jour la statistique d'admission affichée à l'élève sous 5 minutes après une réponse école
- **FR39** : Un élève peut consulter le statut et l'historique de tous ses envois anticipés
- **FR40** : Une école partenaire peut consulter un reporting interne sur les profils reçus, les actions effectuées et les conversions de candidature

#### F. Espaces Tiers (Parent & Conseiller B2B)

- **FR41** : Un parent lié peut consulter les métiers explorés et les parcours sauvegardés de l'élève (sans accès aux bulletins détaillés ni aux appréciations enseignants)
- **FR42** : Un parent peut souscrire et payer un abonnement premium au bénéfice du compte élève lié
- **FR43** : Un conseiller d'orientation peut consulter un dashboard cohorte (élèves de son établissement) avec taux de complétion, métiers les plus explorés, distribution par filière
- **FR44** : Un conseiller d'orientation peut consulter le profil individuel d'un élève uniquement après consentement explicite de l'élève
- **FR45** : Un conseiller d'orientation peut exporter un reporting anonymisé de cohorte (CSV ou PDF) pour usage interne établissement

#### G. Découverte & Engagement

- **FR46** : Le système peut exposer des pages publiques indexables par les moteurs de recherche pour chaque métier, formation et école référencés (SEO)
- **FR47** : Le système peut envoyer des notifications par email à un élève lors d'événements clés (réponse école, nouvelle école référencée, échéance Parcoursup, rappel de complétion)

#### H. Administration & Modération

- **FR48** : Un admin Path-Advisor peut créer, modifier et supprimer des fiches du référentiel professions / formations / écoles
- **FR49** : Un admin Path-Advisor peut consulter et traiter les signalements d'élèves (erreur métier, école obsolète, contenu inapproprié)
- **FR50** : Un admin Path-Advisor peut modérer les motivations libres rédigées par les élèves dans le cadre des envois anticipés (a priori avant transmission)
- **FR51** : Un admin Path-Advisor peut versionner un modèle de recommandation IA et tracer le dataset d'entraînement associé
- **FR52** : Le système peut produire des métriques d'audit ML (distribution scores par sous-population, drift des prédictions) consultables par un admin

#### Fast-Follow (post-MVP immédiat mois 9-12)

- **FR-FF1** : Le système peut détecter des "profils à risque" (faible engagement, profil incohérent, signes de décrochage) et les remonter dans le dashboard conseiller
- **FR-FF2** : Le système peut envoyer des notifications push web (en plus de l'email) aux élèves et parents
- **FR-FF3** : Un admin peut consulter un tableau de bord de qualité du référentiel (couverture, fraîcheur, signalements en attente)
- **FR-FF4** : Le système peut proposer un module RDV visio intégré entre élève et école partenaire
- **FR-FF5** : Le système peut proposer un mécanisme de parrainage / partage permettant à un utilisateur d'inviter un pair via un lien traçable

### NonFunctional Requirements

#### Performance

- **NFR-P1** : Recommandation vocationnelle complète servie en < 3 s P95 MVP, < 1,5 s P95 growth
- **NFR-P2** : Graphe de parcours avec stats personnalisées affiché en < 2 s P95
- **NFR-P3** : Page publique métier/formation TTFB < 1 s, LCP mobile < 2,5 s
- **NFR-P4** : OCR d'un bulletin standard aboutit en < 30 s P95
- **NFR-P5** : MAJ statistique d'admission post-réponse école propagée à l'élève (push + email) en < 5 min
- **NFR-P6** : Authentification utilisateur aboutit en < 1 s P95

#### Security

- **NFR-S1** : Toutes données personnelles chiffrées AES-256 au repos + TLS 1.3 en transit
- **NFR-S2** : MFA obligatoire conseiller/école/admin, optionnelle B2C
- **NFR-S3** : Bulletins PDF stockés bucket S3-compatible chiffré région UE
- **NFR-S4** : Journal d'audit immuable de tout accès aux données personnelles, conservé 3 ans
- **NFR-S5** : Secrets applicatifs dans coffre dédié (Vault / Secrets Manager / self-hosted PoC)
- **NFR-S6** : Délais légaux RGPD respectés (incident CNIL < 72 h, accès/suppression < 30 j)
- **NFR-S7** : DPIA documentée et à jour avant déploiement production
- **NFR-S8** : Prévention attaques OWASP Top 10, audit interne MVP + pen-test annuel externe growth
- **NFR-S9** : Consentement parental email vérifié avant création compte < 15 ans, tracé avec horodatage immuable

#### Scalability

- **NFR-SC1** : 500 MAU MVP, 10 000 MAU growth sans refonte majeure
- **NFR-SC2** : 500 utilisateurs concurrents lors des pics saisonniers sans dégradation
- **NFR-SC3** : Auto-scaling x3 capacité en < 10 min sur déclencheur charge
- **NFR-SC4** : Moteur de recommandation déployable indépendamment du back applicatif
- **NFR-SC5** : Référentiel 50 → 500 entrées sans dégradation latence
- **NFR-SC6** : BDD supporte minimum 100 000 profils élèves

#### Reliability

- **NFR-R1** : Disponibilité ≥ 99 % MVP (downtime ≤ 7 h/mois), ≥ 99,5 % growth
- **NFR-R2** : Sauvegarde quotidienne données prod, rétention 30 jours, testée mensuellement par restauration partielle
- **NFR-R3** : RTO < 4 h, RPO < 1 h
- **NFR-R4** : Dégradation gracieuse en cas de panne tiers (OCR → manuel, Stripe → file, email → retry async)
- **NFR-R5** : Observabilité production complète (logs centralisés, métriques, alerting), MTTR < 1 h incident critique

#### Accessibility

- **NFR-A1** : Parcours utilisateurs critiques conformes RGAA 4.1 niveau AA dès MVP
- **NFR-A2** : Ensemble du produit RGAA 4.1 niveau AA en growth
- **NFR-A3** : Interface pleinement utilisable au clavier seul
- **NFR-A4** : Contrastes texte/fond ≥ 4,5:1 normal, ≥ 3:1 large
- **NFR-A5** : Graphes de parcours fournissent alternative textuelle structurée (tableau, liste séquentielle)
- **NFR-A6** : Produit utilisable sur écrans mobiles dès 320 px de largeur

#### Integration

- **NFR-I1** : Intégration Stripe supporte mode test local (sandbox) en PoC et production en cloud
- **NFR-I2** : Email transactionnel substituable par Mailpit local en PoC sans modification code applicatif (abstraction)
- **NFR-I3** : OCR substituable par Tesseract local en PoC avec dégradation acceptable
- **NFR-I4** : Analytique produit hébergement EU ou self-hosted (PostHog)
- **NFR-I5** : Système expose données ouvertes anonymisées (référentiel formations, tendances) sous licence Etalab en growth
- **NFR-I6** : Intégration ENT/Pronote en growth opt-in côté établissement et opt-in côté élève (double consentement RGPD)
- **NFR-I7** : Système consomme datasets open data Parcoursup (CSV annuel MENJS) pour stats d'admission

#### Maintainability

- **NFR-M1** : Stack complète lance localement par `docker-compose up` en < 5 min, avec données seed pour produit utilisable end-to-end
- **NFR-M2** : Couverture tests automatisés ≥ 70 % sur zones critiques (auth, RBAC, moteur reco, paiement, RGPD)
- **NFR-M3** : Modifications modèle de recommandation IA versionnées avec dataset, hyperparamètres et métriques d'évaluation tracés
- **NFR-M4** : Architecture documentée via Architecture Decision Records (ADR) versionnés en git
- **NFR-M5** : Système maintenable et opérable par 1-2 personnes — toute opération critique (déploiement, restauration, modération) documentée sous forme de runbook

### Additional Requirements

Requirements techniques transverses issus de l'Architecture Decision Document et impactant la décomposition en épics :

- **ADD-1 — Hébergement UE obligatoire** : France ou UE strict (Scaleway / OVH / AWS Paris/Frankfurt), cible SecNumCloud en growth pour B2B EN
- **ADD-2 — PoC local-first via Docker Compose** : toute la stack (front, back, IA, DB, cache, queue, OCR, mail, monitoring, analytics, stockage) lance en local < 5 min avec seeds — interfaces abstraites (Hexagonal / Ports & Adapters) pour permettre PoC local et prod cloud avec mêmes contrats
- **ADD-3 — Multi-tenant hybride dès MVP** : Row-Level Security PostgreSQL, colonnes `tenant_id` (établissement) + `user_id` (élève) sur toutes les tables sensibles, tests d'isolation cross-tenant en CI obligatoires
- **ADD-4 — Service IA séparé** : Python (FastAPI ou équivalent), scaling horizontal indépendant du back applicatif, versioning des modèles avec dataset + hyperparamètres + métriques tracés
- **ADD-5 — Architecture monolithique modulaire** : pas de microservices prématurés, monolithe Node/Python/Ruby selon stack équipe + service IA séparé
- **ADD-6 — Stack frontend imposée** : SPA + SSR hybride (Next.js ou Nuxt) pour combiner SEO B2C et interactivité, PWA installable comme fallback app mobile
- **ADD-7 — Stockage de données** : PostgreSQL transactionnel + pgvector pour embeddings ; S3-compatible chiffré région UE pour bulletins ; Redis pour cache + sessions + rate limiting + recos pré-calculées ; job queue (BullMQ / Sidekiq / Celery) pour OCR async, notifications, envoi anticipé, recalculs stats
- **ADD-8 — Pas de WebSocket MVP** : polling léger (30 s sur pages critiques) + notifications push standard suffisent — simplifie infra et coûts
- **ADD-9 — Audit trail immuable** : table dédiée append-only access-write, conservation 3 ans, export régulier
- **ADD-10 — Versioning modèles IA** : chaque déploiement de modèle versionné avec dataset + hyperparamètres + métriques d'éval, audit trail des décisions, monitoring drift en production
- **ADD-11 — Internationalisation francophone dès jour 1** : clés de traduction structurées (i18n), pas de strings hardcodés, préparation Belgique/Maroc en growth

### UX Design Requirements

Requirements actionnables issus de la spécification UX, organisés par catégorie d'implémentation. Chaque UX-DR est spec'd pour générer une story avec acceptance criteria testables.

#### Design Tokens & Foundation

- **UX-DR1 — Design tokens couleur (mode clair MVP uniquement)** : palette R1 Vermillon sobre + blanc cassé, 17 tokens nommés (`color-brand`, `color-bg`, `color-text`, `color-semantic-audacieux/realiste/sur`, `color-success/warning/danger`…), contrastes vérifiés AA+ sur tous couples, à porter dans `tokens.css` + `tailwind.config.ts`
- **UX-DR2 — Typography system Inter** : variable font weights 400-700, type scale 8 tokens (display-1 48-56 px à text-caption 12 px), body 16 px minimum, line-height 1.5 body / 1.2 display, max 2 poids par écran
- **UX-DR3 — Spacing system Tailwind 4 px** : 8 tokens (space-1 4 px à space-16 64 px), densité cible entre Doctolib et Revolut, grille 4 colonnes mobile / 8 desktop, container max 1200 px
- **UX-DR4 — Motion tokens** : 4 tokens (motion-instant 100 ms, motion-quick 200 ms, motion-standard 300 ms, motion-narrative 720-800 ms réservé `GraphParcours` uniquement), fallback `prefers-reduced-motion` partout

#### Composants Path-Advisor (Couche 3 du design system)

- **UX-DR5 — `ScoreVocationnel`** : composant score métier 0-100 avec phrase recopiable italic + tap-to-copy + chips signaux contributifs cliquables → drawer explicabilité ; variants compact/expanded/comparison ; ARIA + label vocalisé score
- **UX-DR6 — `GraphParcours`** : composant graphe-récit interactif central, animation séquentielle 720-800 ms en 5 phases (lycée → étapes → cible avec overshoot), hiérarchie visuelle stricte (nœud cible 64-72 px, intermédiaires 36-44 px, layout diagonal/arc), un seul chemin visible par défaut + bouton "Voir d'autres chemins (N)", alternative tabulaire RGAA AA obligatoire (NFR-A5), low-data mode (label "estimation indicative") visuellement indiscernable, animation ne se rejoue pas au retour sur le même métier, fallback `prefers-reduced-motion` fade 200 ms
- **UX-DR7 — `FicheEcole`** : fiche densité Doctolib avec proba personnalisée comme métadonnée première, métadonnées en pills (durée, statut, alternance, sélectivité, internat, distance), variants card/expanded/compare, low-data state
- **UX-DR8 — `CarteAdmission`** : composant atomique stat + cadrage qualitatif (audacieux/réaliste/sûr) + contexte ("moyenne admise X") + levier action ("+ 2 points en maths → 58 %"), variants large/medium/small/export, réutilisé dans `GraphParcours`, `FicheEcole`, `StoryExport`, `DeltaRecap`
- **UX-DR9 — `FicheMetier`** : page produit complète métier avec sections hero + C'est quoi + Pour qui + Comment y aller + Écoles cibles + Signaux contributifs, variants mobile-stack/desktop-tabs/print-friendly
- **UX-DR10 — `StoryExport`** : 3 variantes d'export par re-rendu serveur (pas screenshot) — Story ado PNG 9:16 (1080×1920) format Spotify Wrapped, Résumé parent PDF A4 ton pédagogique + glossaire, Fiche conseillère PDF imprimable A4 avec traçabilité (date + version modèle)
- **UX-DR11 — `ConsentDialog`** : modale consentement granulaire avec révocation accessible — 3 cas critiques MVP (parental < 15 ans, conseillère, école partenaire) + extension fast-follow
- **UX-DR12 — `ScenarioLoader`** : loading scénarisé > 1 s avec mini-narration (anti-spinner-nu) — usage computation reco, OCR async (30 s), génération export
- **UX-DR13 — `GracefulFallback`** : pattern erreur proposant alternative immédiate (OCR rate → saisie manuelle, parent absent → continuer mode limité, paiement échoue → retry)
- **UX-DR14 — `DeltaRecap`** : écran d'accueil retour J+N "voici ce qui a bougé" (style Spotify Wrapped léger), types delta supportés (réponse école envoi anticipé, nouvelles écoles, calendrier Parcoursup, état stable)
- **UX-DR15 — `PaywallContextuel`** : CTA premium déclenché sur action gated (envoi anticipé), contextuel pas modale agressive
- **UX-DR16 — `PermissionList`** : liste tiers ayant accès au profil + révocation 1-tap (parent, conseillère, école)
- **UX-DR17 — `CalendarNotification`** : notification calée sur calendrier Parcoursup, sans urgence fabriquée ("Parcoursup ouvre dans 18 jours" pas "DERNIÈRE CHANCE")
- **UX-DR18 — `SideFlow`** : side-flow non-bloquant pour confirmations critiques (consentement parental en attente, etc.) — ne bloque pas exploration en cours
- **UX-DR19 — `ParcoursCard`** : carte récap Strava-style pour "Mes paris" — synthèse parcours en card capturable
- **UX-DR20 — `StatPersonnelle`** : indicateur compatibilité additif optionnel sur fiche école (3 états qualitatifs : compatible / à renforcer / au-dessus)
- **UX-DR21 — `CohortDashboard`** : dashboard B2B conseillère Linear-like dense, vue agrégée cohorte (taux complétion, métiers explorés, distribution filière) + drill-down élève individuel avec consentement, raccourcis clavier first-class (`/`, `j/k`, `e`, `⌘K`)
- **UX-DR22 — `EcoleResponseFlow`** : vue école partenaire — réception profil + fiche profil élève synthétique + 3 actions de réponse + reporting interne

#### Patterns UX transverses

- **UX-DR23 — Pattern "Phrase recopiable"** : sous tout score, phrase défendable italic + brand accent + bouton copy tap (composant atomique réutilisé partout)
- **UX-DR24 — Pattern "Stat with context"** : tout chiffre accompagné de cadrage qualitatif + contexte + levier action — jamais un nombre nu (cf `CarteAdmission`)
- **UX-DR25 — Pattern "Mode normal = mode dégradé"** : même structure visuelle quel que soit le profil ; les contenus internes se densifient sans changer la grille (zéro marqueur visuel d'incomplet pour Léa)
- **UX-DR26 — Pattern "Consentement granulaire"** : aucun tiers n'accède aux données sans consentement explicite révocable 1-tap
- **UX-DR27 — Pattern "Anti-cirque"** : aucune animation ne se rejoue sur ouverture répétée du même contenu
- **UX-DR28 — Pattern "Calendrier sans urgence"** : notifications calées sur calendrier Parcoursup, jamais "DERNIÈRE CHANCE" ni urgence fabriquée
- **UX-DR29 — Pattern "Retour avec delta"** : toute session J+N s'ouvre sur "ce qui a bougé", pas sur écran neutre
- **UX-DR30 — Onboarding différencié par niveau scolaire** : 4 chemins (3ème / lycée général / lycée pro / sans bulletins) qui partagent la même structure, branching après step 2

#### Responsive & Accessibility

- **UX-DR31 — Navigation responsive** : bottom tab bar mobile 5 onglets max (Accueil / Métiers / Mes paris / Notifications / Profil) ; side nav fixed 224 px desktop ; pas de hamburger menu mobile
- **UX-DR32 — Search & filtering pattern Doctolib** : `Command` shadcn + filtres pills multi-select + sort dropdown + faceted search side panel desktop / `Sheet` bottom mobile
- **UX-DR33 — RGAA AA compliance** : axe-core en CI dès sprint 4, audit trimestriel manuel VoiceOver iOS + NVDA Windows sur 3 parcours critiques, test daltonisme mensuel, focus visible 2 px outline `color-brand`, skip links visibles au focus
- **UX-DR34 — Performance budget mobile** : TTI < 4 s sur 4G, LCP mobile < 2,5 s, < 200 ko JS critique par écran, body 16 px minimum partout, touch targets 44 × 44 px minimum, code-splitting agressif + lazy load `GraphParcours`
- **UX-DR35 — Test inclusif "téléphone fissuré"** : test mensuel scénario Sarah complet sur Android d'occasion fissuré (≤ 80 €) pour valider device cible plancher réel (animations, OCR appareil photo médiocre, touch targets)

### FR Coverage Map

Chaque FR est mappé à son épic primaire. Les FRs cross-cutting (auth des tiers) sont aussi consommés dans les épics dépendants.

| FR | Epic | Description courte |
|---|---|---|
| FR1 | Epic 1 | Compte élève ≥ 15 ans + consentement RGPD |
| FR2 | Epic 1 | Compte élève < 15 ans + consentement parental email |
| FR3 | Epic 1 (+ Epic 6) | Compte parent lié élève |
| FR4 | Epic 1 (+ Epic 6) | Auth conseiller B2B MFA |
| FR5 | Epic 1 (+ Epic 5) | Auth école partenaire MFA |
| FR6 | Epic 1 (+ Epic 9) | Auth admin Path-Advisor MFA |
| FR7 | Epic 1 | Multi-tenant + matrice RBAC |
| FR8 | Epic 1 | Liste des tiers ayant accès |
| FR9 | Epic 1 | Révocation accès tiers |
| FR10 | Epic 1 | Export portabilité RGPD |
| FR11 | Epic 1 | Suppression compte RGPD |
| FR12 | Epic 1 | Journal d'audit DPO |
| FR13 | Epic 2 | Déclaration passions/intérêts/valeurs |
| FR14 | Epic 2 | Import bulletins PDF + OCR |
| FR15 | Epic 2 | Saisie manuelle notes + appréciations |
| FR16 | Epic 2 | Déclaration niveau scolaire + filière + spés |
| FR17 | Epic 2 | Mode dégradé sans bulletins |
| FR18 | Epic 2 | Mise à jour profil à tout moment |
| FR19 | Epic 2 | Score de complétude profil |
| FR20 | Epic 3 | Liste métiers scorés 0-100 |
| FR21 | Epic 3 | Fiche métier détaillée |
| FR22 | Epic 3 | Signaux contributifs explicabilité IA |
| FR23 | Epic 3 | Revue humaine recommandation |
| FR24 | Epic 3 | Signaler erreur fiche métier |
| FR25 | Epic 3 | Adaptation reco par niveau scolaire |
| FR26 | Epic 3 | Niveau de confiance reco profil incomplet |
| FR27 | Epic 4 | Graphes de parcours par métier |
| FR28 | Epic 4 | Fiche école / formation détaillée |
| FR29 | Epic 4 | Stat admission personnalisée par école |
| FR30 | Epic 4 | Filtres graphes (proximité, coût, alternance…) |
| FR31 | Epic 4 | Graphe adapté niveau scolaire (3ème → lycée pro) |
| FR32 | Epic 4 | Favoris écoles cibles |
| FR33 | Epic 5 | Envoi anticipé profil élève premium |
| FR34 | Epic 5 | Motivation libre modérée |
| FR35 | Epic 5 | Notification école à chaque envoi |
| FR36 | Epic 5 | Fiche profil élève côté école |
| FR37 | Epic 5 | 3 actions de réponse école |
| FR38 | Epic 5 | MAJ stat admission < 5 min après réponse |
| FR39 | Epic 5 | Historique envois côté élève |
| FR40 | Epic 5 | Reporting interne école |
| FR41 | Epic 6 | Vue parent métiers + parcours (sans bulletins) |
| FR42 | Epic 6 | Parent paie premium au bénéfice élève |
| FR43 | Epic 6 | Dashboard cohorte conseillère B2B |
| FR44 | Epic 6 | Profil individuel élève avec consentement |
| FR45 | Epic 6 | Export reporting anonymisé cohorte |
| FR46 | Epic 7 | Pages publiques indexables SEO |
| FR47 | Epic 8 | Notifications email événements clés |
| FR48 | Epic 9 | CRUD référentiel professions / formations / écoles |
| FR49 | Epic 9 | Traitement signalements |
| FR50 | Epic 9 | Modération motivations a priori |
| FR51 | Epic 9 | Versioning modèles IA + dataset |
| FR52 | Epic 9 | Métriques audit ML (drift, biais) |
| FR-FF1 | Epic 10 | Détection profils à risque |
| FR-FF2 | Epic 10 | Push web notifications |
| FR-FF3 | Epic 10 | Tableau qualité référentiel admin |
| FR-FF4 | Epic 10 | RDV visio intégré école-élève |
| FR-FF5 | Epic 10 | Parrainage / partage lien traçable |

**Couverture : 100 % — 0 FR orphelin (52 MVP + 5 Fast-Follow tous mappés).**

## Epic List

### Epic 1 : Foundation — Auth multi-rôle, RBAC, Conformité RGPD & Infra technique

Permettre à tout utilisateur (élève / parent / conseiller / école / admin) de créer un compte sécurisé conforme RGPD avec accès isolés par rôle, et poser les fondations techniques du produit (Docker Compose, hébergement UE, tokens design system).

**FRs couverts** : FR1, FR2, FR3, FR4, FR5, FR6, FR7, FR8, FR9, FR10, FR11, FR12
**NFRs principaux** : NFR-S1 à NFR-S9 (sécurité), NFR-R1 à NFR-R5 (reliability), NFR-M1, NFR-M4, NFR-M5
**Additional Requirements** : ADD-1 hébergement UE, ADD-2 PoC local-first Docker, ADD-3 multi-tenant RLS, ADD-5 monolithe modulaire, ADD-6 Next.js SSR, ADD-7 PostgreSQL/Redis/S3, ADD-9 audit trail immuable, ADD-11 i18n jour 1
**UX-DRs** : UX-DR1 (tokens couleur R1), UX-DR2 (typo Inter), UX-DR3 (spacing), UX-DR4 (motion tokens), UX-DR11 (`ConsentDialog`), UX-DR16 (`PermissionList`), UX-DR31 (navigation responsive), UX-DR33 (RGAA AA setup), UX-DR34 (perf budget)

### Epic 2 : Profil Élève & Onboarding

Permettre à l'élève (Sarah Terminale, Mehdi 3ème, Léa sans bulletins) de compléter son profil en < 12 min (passions + bulletins OCR ou saisie manuelle) avec un onboarding différencié par niveau scolaire et un mode dégradé invisible.

**FRs couverts** : FR13, FR14, FR15, FR16, FR17, FR18, FR19
**NFRs principaux** : NFR-P4 (OCR < 30 s), NFR-A1 RGAA AA parcours critique, NFR-I3 OCR Tesseract local
**Additional Requirements** : ADD-7 stockage S3 chiffré bulletins, ADD-2 OCR local fallback
**UX-DRs** : UX-DR12 `ScenarioLoader` (OCR async narratif), UX-DR13 `GracefulFallback` (OCR rate → saisie manuelle), UX-DR25 Pattern mode normal = mode dégradé, UX-DR30 Onboarding différencié niveau scolaire, UX-DR35 Form pattern (labels above, validation on blur)

### Epic 3 : Recommandation Vocationnelle (Premier Aha)

Servir le PREMIER moment "aha" : l'élève reçoit 8 métiers scorés avec phrase recopiable défendable et explicabilité des signaux contributifs (RGPD art. 22).

**FRs couverts** : FR20, FR21, FR22, FR23, FR24, FR25, FR26
**NFRs principaux** : NFR-P1 reco < 3 s P95 MVP, NFR-SC4 service IA scaling indépendant, NFR-SC5 référentiel 50 → 500, NFR-M3 versioning modèles
**Additional Requirements** : ADD-4 service IA séparé Python/FastAPI, ADD-10 versioning modèles IA
**UX-DRs** : UX-DR5 `ScoreVocationnel`, UX-DR9 `FicheMetier`, UX-DR23 Pattern phrase recopiable

### Epic 4 : Graphe de Parcours & Stats d'Admission (Deuxième Aha)

Servir le DEUXIÈME moment "aha" et le différenciateur produit central : l'élève voit son graphe-récit interactif avec ses chances réelles d'admission par école, animation séquentielle 720-800 ms, alternative tabulaire RGAA AA.

**FRs couverts** : FR27, FR28, FR29, FR30, FR31, FR32
**NFRs principaux** : NFR-P2 graphe < 2 s P95, NFR-A5 alternative tabulaire graphe, NFR-I7 datasets open data Parcoursup
**Additional Requirements** : ADD-4 service IA pour stats, ADD-7 pgvector pour embeddings
**UX-DRs** : UX-DR6 `GraphParcours` (LE composant), UX-DR7 `FicheEcole`, UX-DR8 `CarteAdmission`, UX-DR19 `ParcoursCard`, UX-DR20 `StatPersonnelle`, UX-DR24 Test 3 mots Caravaggio, UX-DR32 Search & filtering Doctolib

### Epic 5 : Premium B2C & Envoi Anticipé Biface

Permettre à l'élève premium (10,99 €/mois via Stripe ou parent) d'envoyer son profil aux écoles partenaires, l'école répond en 3 actions, la stat d'admission se met à jour en < 5 min. Différenciateur premium clé.

**FRs couverts** : FR33, FR34, FR35, FR36, FR37, FR38, FR39, FR40 (+ FR5 auth école rappel)
**NFRs principaux** : NFR-P5 propagation stat < 5 min, NFR-I1 Stripe sandbox + prod, NFR-S2 MFA école obligatoire
**Additional Requirements** : ADD-8 polling + push (pas WebSocket MVP)
**UX-DRs** : UX-DR15 `PaywallContextuel`, UX-DR22 `EcoleResponseFlow`

### Epic 6 : Espaces Tiers — Parent & Conseillère B2B

Permettre aux parents (M. Martin) de voir les métiers explorés + payer le premium, et aux conseillères B2B (Mme Dupont, 5 pilotes MVP) d'utiliser le dashboard cohorte pour préparer leurs entretiens.

**FRs couverts** : FR41, FR42, FR43, FR44, FR45 (+ FR3 compte parent lié, FR4 auth conseillère rappel)
**NFRs principaux** : NFR-S4 audit accès tiers, NFR-A2 RGAA AA growth (B2B EN)
**Additional Requirements** : ADD-3 multi-tenant RLS (cohorte établissement)
**UX-DRs** : UX-DR21 `CohortDashboard` (Linear-like dense desktop), UX-DR16 `PermissionList`

### Epic 7 : Découverte Publique & SEO

Permettre l'acquisition organique : Sarah trouve Path-Advisor via Google sur une recherche "que faire après le bac" ou "devenir ingénieur biomédical" et arrive sur une page métier indexable, performante, conforme Core Web Vitals.

**FRs couverts** : FR46
**NFRs principaux** : NFR-P3 TTFB < 1 s + LCP mobile < 2,5 s
**Additional Requirements** : ADD-6 Next.js SSR pour SEO, ADD-11 i18n préparé francophonie
**UX-DRs** : UX-DR1/2 tokens publics réutilisés, UX-DR34 Perf budget mobile

### Epic 8 : Continuité Temporelle & Notifications

Servir le moat différenciant vs LLMs grand public : l'utilisateur revient à J+30 et voit "ce qui a bougé" (réponse école, nouvelles formations, calendrier Parcoursup) via un écran `DeltaRecap` style Spotify Wrapped léger et des notifications email calées sans urgence fabriquée.

**FRs couverts** : FR47
**NFRs principaux** : NFR-I2 email Mailpit local + Postmark prod, NFR-R4 dégradation gracieuse email
**UX-DRs** : UX-DR14 `DeltaRecap`, UX-DR17 `CalendarNotification`, UX-DR29 Pattern retour avec delta, UX-DR28 Pattern calendrier sans urgence

### Epic 9 : Back-office Administration & Modération

Permettre à Karim (admin Path-Advisor) de maintenir le référentiel professions/formations/écoles, traiter les signalements sous 7 jours, modérer les motivations libres a priori, versionner les modèles IA avec dataset, et auditer le drift ML.

**FRs couverts** : FR48, FR49, FR50, FR51, FR52 (+ FR6 auth admin rappel)
**NFRs principaux** : NFR-M3 versioning modèles IA, NFR-S4 audit accès admin
**Additional Requirements** : ADD-10 versioning modèles IA + audit trail
**UX-DRs** : (back-office utilisant principalement shadcn primitives + tokens, peu de composants Couche 3 dédiés)

### Epic 10 : Fast-Follow (5 features post-MVP immédiat)

Polish post-MVP (mois 9-12) : détection profils à risque dashboard conseillère, push web (en plus email), tableau qualité référentiel admin, RDV visio intégré école-élève, parrainage / partage lien traçable.

**FRs couverts** : FR-FF1, FR-FF2, FR-FF3, FR-FF4, FR-FF5
**NFRs principaux** : (héritage MVP)
**UX-DRs** : UX-DR18 `SideFlow` (peut servir au consentement parental en attente)

---

**Total : 10 épics, 100 % de couverture FRs, ordre d'implémentation suivant le chemin critique vers les 2 moments aha (Epic 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10).**

---

## Epic 1 : Foundation — Auth multi-rôle, RBAC, Conformité RGPD & Infra technique

Permettre à tout utilisateur (élève / parent / conseiller / école / admin) de créer un compte sécurisé conforme RGPD avec accès isolés par rôle, et poser les fondations techniques du produit (Docker Compose local-first, hébergement UE, tokens design system).

### Story 1.1 : Initialisation du projet Next.js avec stack technique cible

As a développeur Path-Advisor,
I want initialiser le repo avec Next.js 15 + TypeScript + Tailwind v4 + shadcn/ui + Docker Compose,
So that toute la stack tourne localement en `docker-compose up < 5 min` et l'équipe peut démarrer le développement sur des fondations propres.

**Acceptance Criteria :**

**Given** un repo Git vide
**When** je lance la commande d'initialisation projet
**Then** le projet contient une app Next.js 15 + TypeScript fonctionnelle avec linting (ESLint + Prettier), tests (Jest / Vitest), et CI minimale (GitHub Actions ou équivalent)
**And** Tailwind v4 est configuré avec `tailwind.config.ts` prêt à recevoir les tokens
**And** shadcn/ui CLI est installé et au moins 5 composants prioritaires copiés (Button, Card, Dialog, Form, Input)

**Given** la stack complète (front, postgres, redis, mailpit, minio, tesseract-ocr, posthog) est déclarée dans `docker-compose.yml`
**When** je lance `docker-compose up`
**Then** tous les services démarrent en < 5 minutes
**And** l'app Next.js est accessible sur `http://localhost:3000` avec une page d'accueil "Hello Path-Advisor"
**And** les données de seed sont injectées automatiquement (1 user admin de test)

**Given** la configuration multi-environnement (local / staging / production)
**When** je consulte la documentation README
**Then** un ADR #001 documente le choix Next.js + shadcn + Docker
**And** un runbook explique le setup pas-à-pas pour un nouveau dev

### Story 1.2 : Définition et publication du design system de tokens

As a développeur Path-Advisor,
I want les tokens couleur R1 Vermillon + typographie Inter + spacing 4 px + motion centralisés dans `tokens.css` et `tailwind.config.ts`,
So that tous les écrans futurs partagent une identité visuelle cohérente sans hardcoder de valeurs locales.

**Acceptance Criteria :**

**Given** la spec UX Step 8 (palette R1, type scale, spacing, motion)
**When** je consulte `tokens.css`
**Then** les 17 tokens couleur sont définis en CSS variables (`--color-brand: #C8312D`, `--color-bg: #FAFAF7`, etc.)
**And** les 8 tokens de type scale (`text-display-1` à `text-caption`) sont configurés dans Tailwind avec font Inter variable preloadée
**And** les 8 tokens de spacing (4 px à 64 px) sont alignés sur les défauts Tailwind
**And** les 4 tokens de motion (`motion-instant`, `motion-quick`, `motion-standard`, `motion-narrative`) sont accessibles via Tailwind utilities

**Given** un composant `Button` shadcn fraîchement installé
**When** je l'utilise dans une page
**Then** ses couleurs (background, hover, focus ring) reflètent automatiquement les tokens brand R1
**And** sa typographie utilise Inter via les tokens type scale

**Given** la conformité RGAA AA
**When** un audit de contraste est exécuté
**Then** tous les couples text / background sont conformes ≥ 4.5:1 (normal) ou ≥ 3:1 (large)

### Story 1.3 : Inscription élève ≥ 15 ans avec consentement RGPD direct

As a lycéen ≥ 15 ans,
I want créer mon compte avec mon email et mon mot de passe, en acceptant les CGU et la politique RGPD,
So that je peux accéder à Path-Advisor sans intervention parentale tout en étant pleinement informé de mes droits.

**Acceptance Criteria :**

**Given** je suis sur la page d'inscription et je saisis email + mot de passe + date de naissance (≥ 15 ans)
**When** je clique sur "Créer mon compte"
**Then** je dois explicitement cocher la case "J'accepte les CGU et la politique RGPD" (lien vers politique RGPD visible)
**And** un email de vérification d'adresse est envoyé via Mailpit local ou Postmark prod (selon environnement)
**And** mon compte est créé avec le rôle `student`, statut `email_unverified`

**Given** je clique sur le lien de vérification reçu
**When** je clique
**Then** mon compte passe au statut `active`
**And** je suis redirigé vers l'onboarding (Epic 2)

**Given** la conformité légale
**When** je consulte la politique RGPD
**Then** elle mentionne explicitement finalités du traitement, base légale, durée de conservation, mes droits (accès, portabilité, suppression, opposition)
**And** elle indique le DPO et la CNIL comme autorité de contrôle

### Story 1.4 : Inscription élève < 15 ans avec consentement parental email opt-in

As a collégien < 15 ans (Mehdi, 14 ans),
I want créer mon compte en fournissant l'email d'un parent qui validera mon inscription,
So that je puisse utiliser Path-Advisor en conformité avec la loi française tout en explorant en mode limité pendant la validation.

**Acceptance Criteria :**

**Given** je m'inscris avec une date de naissance < 15 ans
**When** je saisis email + mot de passe + email parent
**Then** mon compte est créé au statut `pending_parental_consent`
**And** un email de demande de consentement est envoyé à l'adresse parent fournie
**And** je peux continuer à explorer Path-Advisor en mode limité (features premium et envoi anticipé désactivés tant que consentement non validé)

**Given** mon parent reçoit l'email
**When** il clique sur le lien d'opt-in
**Then** il atterrit sur une page de validation expliquant le service, les bénéfices, les données collectées et ses droits parentaux
**And** il peut "J'autorise" ou "Je refuse"
**And** son action est horodatée et stockée dans le journal d'audit immuable

**Given** mon parent autorise
**When** la validation est enregistrée
**Then** mon compte passe au statut `active` avec tag `parental_consent_validated`
**And** je reçois une notification "Ton parent a validé ton inscription, tu as accès à toutes les features"

**Given** mon parent ne répond pas dans 30 jours
**When** le délai expire
**Then** un email de relance est envoyé
**And** si 60 jours sans réponse, mon compte est suspendu (mais non supprimé — je peux relancer)

### Story 1.5 : Connexion utilisateur avec email/mot de passe

As a utilisateur enregistré (élève, parent, conseiller, école, admin),
I want me connecter avec mon email et mot de passe,
So that j'accède à mon espace personnel selon mon rôle.

**Acceptance Criteria :**

**Given** je suis sur la page de connexion et je saisis des credentials valides
**When** je clique sur "Se connecter"
**Then** je suis authentifié en < 1 s (NFR-P6)
**And** je suis redirigé vers le dashboard approprié à mon rôle
**And** une session JWT ou cookie sécurisé est établie avec expiration 7 jours par défaut

**Given** des credentials invalides
**When** je clique sur "Se connecter"
**Then** un message d'erreur générique apparaît ("Email ou mot de passe incorrect") sans révéler si l'email existe
**And** après 5 échecs successifs en 15 minutes, mon compte est temporairement verrouillé 10 minutes (rate limiting)

**Given** j'ai oublié mon mot de passe
**When** je clique sur "Mot de passe oublié"
**Then** je saisis mon email, un lien de réinitialisation est envoyé (valide 1 h), je peux choisir un nouveau mot de passe

### Story 1.6 : MFA obligatoire pour les rôles staff (conseiller, école, admin)

As a utilisateur staff (conseiller, école partenaire, admin Path-Advisor),
I want activer une authentification multi-facteur (TOTP),
So that les comptes ayant accès à des données scolaires sensibles sont protégés conformément à NFR-S2.

**Acceptance Criteria :**

**Given** je suis un nouveau utilisateur staff
**When** je me connecte pour la première fois
**Then** je suis redirigé vers un flow d'enrollment MFA obligatoire
**And** je peux scanner un QR code TOTP avec une app authenticator
**And** je dois valider un code TOTP pour finaliser l'enrollment
**And** je reçois 8 codes de récupération à imprimer / sauvegarder

**Given** j'ai activé le MFA et je me connecte
**When** je saisis email + mot de passe
**Then** je suis invité à saisir mon code TOTP avant d'accéder au dashboard
**And** si je n'ai pas accès à mon authenticator, je peux utiliser un des 8 codes de récupération (chacun à usage unique)

**Given** je suis un utilisateur B2C (élève ou parent)
**When** je consulte les paramètres de sécurité
**Then** je peux activer MFA en option
**But** ce n'est pas obligatoire

### Story 1.7 : Matrice RBAC et middleware d'autorisation

As a système Path-Advisor,
I want appliquer la matrice RBAC documentée (6 rôles) sur toutes les routes API et toutes les pages applicatives,
So that chaque utilisateur n'accède qu'aux ressources autorisées par son rôle (FR7).

**Acceptance Criteria :**

**Given** la matrice RBAC du PRD (élève voit tout son profil ; parent voit métiers + parcours mais pas bulletins ; conseiller voit cohorte agrégée ; etc.)
**When** un utilisateur tente d'accéder à une ressource
**Then** un middleware d'autorisation centralisé vérifie son rôle + ses permissions granulaires
**And** l'accès est autorisé ou refusé selon la matrice
**And** chaque refus d'accès est loggué (détection de tentatives d'escalation)

**Given** la matrice est documentée dans le code et la doc
**When** un développeur ajoute une nouvelle route
**Then** il est forcé par convention / lint de déclarer le rôle ou la permission requise
**And** la CI échoue si une route est exposée sans déclaration de permission

**Given** un test d'intégration de la matrice RBAC
**When** la CI s'exécute
**Then** au moins 1 test par paire (rôle, ressource) vérifie l'autorisation correcte
**And** la couverture RBAC est ≥ 90 % (NFR-M2)

### Story 1.8 : Multi-tenant Row-Level Security PostgreSQL + tests d'isolation CI

As a système Path-Advisor,
I want isoler les données par tenant (établissement B2B) et par utilisateur (élève) via Row-Level Security PostgreSQL,
So that aucune fuite cross-tenant ou cross-user n'est possible au niveau database (FR7 + ADD-3).

**Acceptance Criteria :**

**Given** toutes les tables contenant des données utilisateur
**When** la migration de schéma est exécutée
**Then** chaque table sensible contient une colonne `tenant_id` (nullable pour B2C) + `user_id` (NOT NULL)
**And** une policy RLS PostgreSQL est définie pour filtrer automatiquement par tenant_id + user_id du contexte de session

**Given** un test d'isolation cross-tenant en CI
**When** un utilisateur du tenant A tente d'accéder à des données du tenant B (via injection directe SQL ou bypass middleware)
**Then** la requête retourne 0 ligne (filtrée par RLS au niveau DB)
**And** le test échoue si une seule ligne fuit

**Given** un test d'isolation cross-user en CI
**When** l'élève A tente d'accéder aux bulletins de l'élève B
**Then** la requête retourne 0 ligne
**And** le test échoue si fuite

**Given** la documentation
**When** un nouveau dev rejoint l'équipe
**Then** un ADR documente le choix RLS + tests d'isolation comme régression critique en CI

### Story 1.9 : Liste des tiers ayant accès au profil élève

As a élève (Sarah, Mehdi, Léa),
I want voir à tout moment la liste de tous les tiers ayant accès à mon profil (parent, conseillère, école partenaire),
So that j'ai un contrôle transparent sur mes données conformément à FR8 et NFR-S4.

**Acceptance Criteria :**

**Given** je suis connecté en tant qu'élève
**When** je vais dans Paramètres → "Accès tiers"
**Then** je vois la liste de tous les tiers ayant accès à mon profil
**And** pour chaque tier je vois : nom, type d'accès, date d'octroi, données visibles, données masquées

**Given** la liste est vide
**When** je consulte la page
**Then** un empty state explique "Aucun tiers n'a accès à ton profil pour le moment. Tu peux inviter un parent, accepter une demande de ta conseillère, ou envoyer ton profil à une école."

**Given** l'accessibilité RGAA AA
**When** un utilisateur de lecteur d'écran consulte la liste
**Then** chaque entrée est annoncée clairement avec son rôle, ses permissions, et l'action possible (révoquer)

### Story 1.10 : Révocation d'un accès tiers

As a élève,
I want révoquer à tout moment l'accès accordé à un tiers,
So that je garde le contrôle sur qui voit mon profil conformément à FR9.

**Acceptance Criteria :**

**Given** je suis sur la page "Accès tiers" et je vois mon parent dans la liste
**When** je tape sur le bouton "Révoquer" en face de l'entrée parent
**Then** une `ConsentDialog` de confirmation s'affiche m'expliquant ce qui se passera (le parent ne verra plus mes métiers explorés, mais ses paiements premium restent valides)
**And** je peux confirmer ou annuler

**Given** je confirme la révocation
**When** la révocation est appliquée
**Then** l'accès du tiers est immédiatement bloqué (même session en cours)
**And** un événement est loggué dans le journal d'audit (FR12)
**And** une notification est envoyée au tiers

**Given** je révoque l'accès d'une école partenaire à qui j'ai envoyé mon profil
**When** la révocation est appliquée
**Then** l'école perd l'accès à ma fiche profil mais conserve les réponses qu'elle a déjà émises (historique préservé)

### Story 1.11 : Export portabilité RGPD — toutes mes données personnelles

As a utilisateur (élève, parent, conseiller, école),
I want télécharger l'intégralité de mes données personnelles dans un format standard,
So that je peux exercer mon droit à la portabilité RGPD conformément à FR10 et NFR-S6.

**Acceptance Criteria :**

**Given** je suis dans Paramètres → "Mes données"
**When** je clique sur "Exporter mes données"
**Then** une demande d'export est créée (statut `pending`)
**And** un `ScenarioLoader` m'indique que l'export sera prêt sous 30 minutes max
**And** je reçois un email + une notification in-app dès que l'export est prêt

**Given** mon export est prêt
**When** je clique sur le lien de téléchargement (valide 7 jours)
**Then** je télécharge un ZIP contenant : profil JSON, bulletins PDFs originaux, recos JSON, parcours sauvegardés, historique envois, journal d'audit me concernant
**And** le fichier est chiffré avec un mot de passe envoyé séparément

**Given** la conformité RGPD
**When** l'export est généré
**Then** il est conforme au format Article 20 RGPD (structuré, machine-readable, communément utilisé)
**And** une trace de l'export est ajoutée au journal d'audit

### Story 1.12 : Suppression complète du compte (droit à l'oubli RGPD)

As a utilisateur,
I want demander la suppression complète de mon compte et de toutes mes données,
So that j'exerce mon droit à l'oubli RGPD conformément à FR11 et NFR-S6.

**Acceptance Criteria :**

**Given** je suis dans Paramètres → "Supprimer mon compte"
**When** je clique sur "Supprimer définitivement mon compte"
**Then** une `ConsentDialog` m'explique les conséquences (perte définitive irréversible, l'historique pseudonymisé d'audit reste 3 ans pour conformité)
**And** je dois saisir mon mot de passe pour confirmer

**Given** je confirme la suppression
**When** la demande est enregistrée
**Then** mon compte est immédiatement désactivé
**And** un délai de grâce de 30 jours est appliqué avant suppression effective (réversible pendant 30 jours par contact support)
**And** je reçois un email de confirmation

**Given** les 30 jours sont écoulés
**When** le job de suppression effective s'exécute
**Then** toutes mes données personnelles sont définitivement effacées
**But** le journal d'audit pseudonymisé reste 3 ans (obligation légale)
**And** la suppression est traçable et auditable

### Story 1.13 : Journal d'audit immuable des accès aux données personnelles

As a DPO Path-Advisor,
I want un journal d'audit immuable enregistrant tout accès aux données personnelles d'un élève par un tiers,
So that je peux répondre aux audits CNIL et démontrer la conformité RGPD conformément à FR12 et NFR-S4.

**Acceptance Criteria :**

**Given** un parent consulte les métiers explorés de son enfant
**When** la requête est exécutée
**Then** une entrée est créée dans la table `audit_log` avec : timestamp UTC, acteur (parent_id), action (`read_metiers_explored`), cible (student_id), résultat (success), durée requête

**Given** la table `audit_log` est append-only
**When** quelqu'un tente d'UPDATE ou DELETE une entrée
**Then** la base refuse l'opération (contrainte ou trigger)
**And** une alerte est envoyée (tentative de modification d'audit log = incident critique)

**Given** la conservation 3 ans
**When** une entrée a plus de 3 ans
**Then** elle est archivée (cold storage) mais reste consultable
**And** un job mensuel vérifie l'intégrité du journal (checksums)

**Given** le DPO consulte le journal
**When** il filtre par élève ou par tiers
**Then** il peut exporter un rapport CSV ou PDF horodaté
**And** son accès au journal est lui-même audité (méta-audit)

### Story 1.14 : Composant `ConsentDialog` réutilisable

As a développeur Path-Advisor,
I want un composant `ConsentDialog` standardisé pour toutes les demandes de consentement granulaire,
So that l'expérience consentement reste cohérente et non-culpabilisante dans toute l'app (UX-DR11 + UX-DR26).

**Acceptance Criteria :**

**Given** le composant `ConsentDialog` est implémenté en suivant les tokens design system
**When** je l'instancie avec props (titre, description, données concernées, durée, bénéficiaire)
**Then** il affiche une modale (desktop) ou un Sheet bottom (mobile) avec ces informations
**And** il propose 2 actions claires (Accepter / Refuser) sans dark pattern (boutons même poids visuel)

**Given** le composant est accessible
**When** un utilisateur de lecteur d'écran le rencontre
**Then** il est annoncé avec rôle dialog, focus piégé dans la modale, ESC ferme

**Given** un consentement est accordé
**When** l'utilisateur confirme
**Then** l'événement est loggué dans le journal d'audit (FR12) avec horodatage et hash du contenu accepté (preuve d'immuabilité)

**Given** les 3 cas critiques MVP (parental < 15 ans, conseillère, école partenaire)
**When** chacun est testé
**Then** le composant s'adapte avec les bons textes, les bonnes données mentionnées, les bons CTAs

## Epic 2 : Profil Élève & Onboarding

Permettre à l'élève (Sarah Terminale, Mehdi 3ème, Léa sans bulletins) de compléter son profil en < 12 min (passions + bulletins OCR ou saisie manuelle) avec un onboarding différencié par niveau scolaire et un mode dégradé invisible.

### Story 2.1 : Onboarding step 1 — Déclaration passions, intérêts et valeurs

As a élève (Sarah, Mehdi, Léa),
I want déclarer mes passions, centres d'intérêt et valeurs via un questionnaire structuré accessible,
So that le moteur de recommandation puisse croiser ces signaux déclaratifs avec mes bulletins pour produire des recos personnalisées (FR13).

**Acceptance Criteria :**

**Given** je viens de finir mon inscription (Epic 1)
**When** j'arrive sur l'onboarding step 1/3
**Then** je vois un écran avec un indicateur de progression discret (3 points : `● ○ ○`)
**And** je peux sélectionner mes passions parmi des chips multi-select (~20 catégories : sciences, arts, sport, social, tech, business, etc.) avec recherche
**And** je peux ajouter des passions libres (max 5 personnalisées) si rien ne me correspond

**Given** je sélectionne au moins 3 passions
**When** je continue
**Then** un second écran me propose des valeurs personnelles (liste curée : justice sociale, indépendance, sécurité, créativité, défi, contact humain, etc.) — multi-select 3-5 valeurs
**And** un troisième écran me demande mes centres d'intérêt (formats consommés : YouTube, podcasts, livres, expériences) en libre + suggestions

**Given** le copy s'adapte au niveau scolaire (UX-DR30)
**When** Mehdi (3ème) saisit ses passions
**Then** les exemples de chips utilisent un vocabulaire accessible ("ce qui te branche", "trucs qui te font kiffer") plutôt que jargon scolaire

**Given** je ferme l'app avant la fin
**When** je reviens plus tard
**Then** mes réponses sont sauvegardées automatiquement (save inter-step), je reprends où j'étais

### Story 2.2 : Onboarding step 2 — Niveau scolaire, filière et spécialités

As a élève,
I want déclarer mon niveau scolaire, ma filière et mes spécialités,
So that mes recos métiers et parcours soient cohérents avec ma trajectoire scolaire réelle (FR16 + FR25 + FR31).

**Acceptance Criteria :**

**Given** je suis sur l'onboarding step 2/3
**When** je sélectionne mon niveau scolaire
**Then** je vois 5 options claires : 3ème (collège), 2nde (lycée), 1ère (lycée), Terminale (lycée), Post-bac
**And** selon ma sélection, le formulaire branche dynamiquement (UX-DR30) : 3ème → question complémentaire général/techno/pro ; lycée → sélection filière + spés ; post-bac → année + type de formation

**Given** je suis en lycée général Terminale et je sélectionne mes spécialités
**When** je termine la sélection
**Then** mes spécialités (ex : Maths + SVT + HGGSP) sont enregistrées et utilisées pour le moteur de reco
**And** un récap visuel me montre ce que j'ai déclaré

**Given** Mehdi sélectionne "3ème → bac pro à confirmer"
**When** il continue
**Then** le système sait que ses recos métiers privilégieront des parcours bac pro tout en gardant général visible
**And** son onboarding bulletins (step 3) attend des bulletins collège (pas lycée)

### Story 2.3 : Import bulletins PDF avec OCR async (chemin principal)

As a élève,
I want importer mes bulletins scolaires en PDF et voir le système extraire automatiquement mes notes et appréciations,
So that mon profil scolaire objectif soit construit sans saisie manuelle laborieuse (FR14).

**Acceptance Criteria :**

**Given** je suis sur l'onboarding step 3/3 et je choisis "Scanner / importer mes bulletins"
**When** je sélectionne 1 à N PDFs (drag-and-drop desktop ou tap mobile → galerie / caméra)
**Then** les fichiers sont uploadés vers stockage S3-compatible chiffré (MinIO local en PoC, S3 EU prod)
**And** un job OCR async (Tesseract local en PoC, Mindee / AWS Textract prod) est lancé
**And** un `ScenarioLoader` m'indique la progression avec mini-narration

**Given** l'OCR aboutit en < 30 s (NFR-P4)
**When** l'extraction est terminée
**Then** je vois un récap éditable : matières + notes + appréciations enseignants par trimestre
**And** je peux corriger les erreurs (champs inline editable)
**And** je clique "Valider" pour confirmer

**Given** l'OCR rate (pattern non reconnu, image dégradée, format non standard)
**When** Tesseract retourne une confiance < seuil ou ne reconnaît rien
**Then** le système bascule automatiquement vers le `GracefulFallback` (Story 2.4)
**And** un message non-culpabilisant explique le fallback

**Given** je suis Mehdi (3ème) et je scanne mes bulletins collège
**When** l'OCR s'exécute
**Then** le système reconnaît les matières collège et adapte le formulaire de validation au niveau collège

### Story 2.4 : Saisie manuelle assistée des notes (chemin fallback)

As a élève (Léa qui refuse l'OCR, ou utilisateur dont l'OCR a raté),
I want saisir mes notes et appréciations dans un formulaire structuré simple,
So that je puisse compléter mon profil scolaire même sans OCR réussi (FR15).

**Acceptance Criteria :**

**Given** je choisis "Saisir manuellement" à l'onboarding step 3, OU je suis arrivé ici via fallback OCR raté
**When** j'arrive sur le formulaire
**Then** je vois un formulaire structuré pré-rempli avec la liste des matières correspondant à mon niveau scolaire
**And** je peux saisir pour chaque matière : moyenne trimestre 1, moyenne trimestre 2 (optionnelle), appréciation libre (optionnelle)

**Given** le formulaire respecte UX-DR35 (labels au-dessus, validation on blur, no asterisk)
**When** je saisis des valeurs invalides (note > 20, format non numérique)
**Then** une erreur contextuelle inline apparaît sous le champ
**And** la bordure passe en `color-danger`

**Given** je manque de temps
**When** je sauvegarde partiellement (5 matières renseignées sur 8)
**Then** mon profil est sauvegardé tel quel, le système me dit qu'il peut déjà produire des recos avec ce que j'ai

**Given** le formulaire est accessible RGAA AA
**When** un utilisateur de lecteur d'écran le parcourt
**Then** chaque champ a un label sémantique associé, les erreurs sont annoncées via `aria-describedby`

### Story 2.5 : Mode dégradé invisible — "Plus tard" sur les bulletins

As a élève Léa qui n'a pas envie de partager ses bulletins maintenant,
I want pouvoir cliquer "Plus tard" sur l'étape bulletins et accéder quand même à des recommandations,
So that je puisse découvrir le produit sans friction tout en sachant que mes stats seront indicatives (FR17).

**Acceptance Criteria :**

**Given** je suis sur l'onboarding step 3 (bulletins)
**When** je tape sur "Plus tard, je préfère explorer d'abord"
**Then** mon profil passe à `bulletins_status: postponed` (pas `incomplete` — distinction sémantique importante)
**And** un bandeau discret au pied de l'écran rappelle "Tu peux ajouter tes bulletins à tout moment pour des stats personnalisées"
**And** je continue vers les recos (Epic 3)

**Given** je consulte mes recos vocationnelles (Epic 3)
**When** elles s'affichent
**Then** elles ont la même structure visuelle que Sarah avec bulletins (pas de mode dégradé visuel — UX-DR25)
**And** le label sous les scores indique "indicatif" sans culpabilisation

**Given** je consulte un graphe de parcours (Epic 4)
**When** je vois les stats d'admission
**Then** elles sont affichées comme fourchettes larges avec label "estimation indicative — affine avec ton profil"
**And** un mini-CTA contextuel propose "Ajoute tes bulletins → stats personnalisées" (1 tap pour ouvrir le mini-flow)

**Given** je reviens 2 semaines plus tard et décide d'ajouter mes bulletins
**When** je clique sur le CTA contextuel
**Then** un mini-flow inline d'ajout bulletins s'ouvre (Sheet bottom mobile, drawer desktop) — pas un re-onboarding complet
**And** mes recos et stats sont recalculées en place, avec un badge "mis à jour" visible 24 h

### Story 2.6 : Mise à jour profil à tout moment

As a élève,
I want mettre à jour mon profil à tout moment (ajouter un nouveau bulletin de trimestre, modifier mes passions, changer de filière),
So that mon profil reste à jour au fil de l'année scolaire et les recos s'adaptent (FR18).

**Acceptance Criteria :**

**Given** je suis connecté et je vais dans Paramètres → "Mon profil"
**When** je consulte ma page profil
**Then** je vois 3 sections éditables : passions / intérêts / valeurs, niveau scolaire / filière / spés, bulletins
**And** chaque section a un bouton "Modifier" qui ouvre un mini-flow d'édition

**Given** j'ajoute un bulletin du trimestre 2
**When** je sauvegarde
**Then** mes recos vocationnelles et mes stats d'admission sont recalculées automatiquement (async, < 10 s)
**And** un toast m'informe "Profil mis à jour — nouvelles recos disponibles"

**Given** je change de filière (Bac général → Bac techno)
**When** je sauvegarde le changement
**Then** une `ConsentDialog` me prévient que mes recos vont être réinitialisées
**And** mes anciens parcours sauvegardés sont conservés en historique mais marqués "lié à ancien profil"

### Story 2.7 : Score de complétude profil + identification des éléments manquants

As a élève,
I want visualiser un score de complétude de mon profil et identifier les éléments manquants,
So that je sais ce qui débloque des features supplémentaires sans culpabilisation (FR19).

**Acceptance Criteria :**

**Given** je suis sur ma page profil
**When** je consulte ma "Maturité de profil"
**Then** je vois un indicateur qualitatif (3 états : Profil de base / Profil enrichi / Profil complet) — pas un pourcentage
**And** chaque état a une description claire ("Tu as l'essentiel pour des recos indicatives" / "Tu débloques les stats personnalisées" / "Tu profites de toutes les features")

**Given** je suis en "Profil de base" (passions seules, pas de bulletins)
**When** je clique sur "Voir comment enrichir"
**Then** je vois une liste contextuelle d'actions courtes : "Ajoute un bulletin pour débloquer les stats personnalisées" (lien direct vers le flow), "Précise tes spés pour adapter les parcours" (édition inline)
**And** chaque action est facultative — aucune n'est obligatoire

**Given** le ton respecte le principe émotionnel #2 (dignité avant positivité)
**When** je suis Léa en profil de base
**Then** je ne vois jamais de message "Allez, on continue !" ou "Tu y es presque !"
**And** le copy est factuel : "Voici ce qui s'ouvre quand tu complètes"

### Story 2.8 : Composant `ScenarioLoader` réutilisable

As a développeur Path-Advisor,
I want un composant `ScenarioLoader` standardisé pour toute attente > 1 s avec une mini-narration adaptée au contexte,
So that l'utilisateur n'a jamais un spinner nu et l'attente devient un moment scénarisé (UX-DR12).

**Acceptance Criteria :**

**Given** le composant est implémenté en suivant les tokens design
**When** je l'instancie avec props (`steps: string[]`, `estimatedDuration: number`, `context: 'reco' | 'ocr' | 'export'`)
**Then** il affiche une mini-narration séquentielle adaptée au contexte
**And** chaque étape apparaît en fade-in avec respect du `motion-quick` (200 ms)

**Given** je l'utilise pour l'OCR async (30 s max)
**When** Tesseract traite le bulletin
**Then** la narration affiche : "On lit ton bulletin..." → "On extrait tes notes..." → "On identifie les appréciations enseignants..." (toutes les ~8 s)

**Given** je l'utilise pour la computation reco (3-5 s)
**When** le moteur IA score les métiers
**Then** la narration affiche : "On croise tes passions avec ton profil scolaire..." → "On compare avec des milliers de profils similaires..." → "On te prépare une sélection..."

**Given** la conformité reduced-motion
**When** `prefers-reduced-motion: reduce` est actif
**Then** la narration s'affiche sans animation séquentielle (texte présent dès le début, mis à jour silencieusement)

### Story 2.9 : Composant `GracefulFallback` réutilisable

As a développeur Path-Advisor,
I want un composant `GracefulFallback` réutilisable pour tout pattern d'erreur qui propose une alternative immédiate,
So that aucune impasse ne casse l'expérience utilisateur, conformément à UX-DR13 et NFR-R4.

**Acceptance Criteria :**

**Given** le composant est implémenté
**When** je l'instancie avec props (titre, explication non-culpabilisante, action alternative, action secondaire optionnelle)
**Then** il affiche une carte (pas une alerte rouge agressive) avec ton bienveillant
**And** le CTA primary propose l'alternative immédiate en bouton solid brand
**And** un CTA secondary optionnel propose "Réessayer" ou "Plus tard"

**Given** un cas d'usage OCR raté
**When** le composant s'affiche
**Then** le copy est : "Ton bulletin a un format qu'on connaît pas encore. Pas grave — saisis à la main, 5 champs et c'est bon."
**And** le CTA primary "Saisir à la main" lance le flow Story 2.4

**Given** un cas d'usage paiement Stripe rejeté
**When** le composant s'affiche
**Then** le copy est factuel sans dramatiser : "Le paiement n'a pas abouti. Réessaie avec une autre carte ou contacte ta banque."
**And** les CTAs proposent "Réessayer" + "Utiliser une autre carte"

**Given** la conformité émotionnelle Step 4 (anxiété acknowledged, jamais amplifiée)
**When** un utilisateur rencontre un échec critique
**Then** le composant ne crie jamais ("ERREUR !!"), ne culpabilise jamais ("Tu as fait une erreur")
**And** il maintient un ton calme et propose une voie

## Epic 3 : Recommandation Vocationnelle (Premier Aha)

Servir le PREMIER moment "aha" : l'élève reçoit 8 métiers scorés avec phrase recopiable défendable et explicabilité des signaux contributifs (RGPD art. 22).

### Story 3.1 : Service IA séparé Python/FastAPI (foundation)

As a système Path-Advisor,
I want un service IA dédié en Python/FastAPI déployable indépendamment du back applicatif Next.js,
So that le moteur de recommandation peut scaler horizontalement de manière séparée et bénéficier des bibliothèques ML/DL natives Python (ADD-4 + NFR-SC4).

**Acceptance Criteria :**

**Given** un service Python FastAPI fraîchement créé
**When** je lance `docker-compose up`
**Then** le service IA démarre en local avec endpoints REST exposés (au moins `/health`, `/v1/score-metiers`)
**And** il communique avec le back Next.js via API interne (auth par token de service)

**Given** le service IA est versionné
**When** je consulte la documentation
**Then** un ADR documente le choix Python/FastAPI vs Node.js et la séparation de scaling
**And** un schéma d'architecture montre les flux Next.js → Service IA → DB

**Given** la conformité avec le PoC local-first (ADD-2)
**When** un dev installe le projet
**Then** le service IA tourne en local avec ses propres dépendances (scikit-learn, sentence-transformers, pandas)
**And** aucune dépendance cloud n'est requise pour le développement

**Given** le scaling indépendant
**When** la charge augmente sur le service IA (pics saisonniers janvier-mars)
**Then** le service peut scaler horizontalement (Docker Swarm / Kubernetes) sans toucher au back applicatif

### Story 3.2 : Référentiel professions MVP (50 métiers curés)

As a content / data ops Path-Advisor,
I want un référentiel de 50+ professions curées avec description, prérequis, débouchés, revenu médian, journée type,
So that le moteur de recommandation a une base de métiers crédible et utilisable dès le MVP (FR21).

**Acceptance Criteria :**

**Given** une table `professions` en PostgreSQL
**When** je consulte le schéma
**Then** elle contient `id`, `slug`, `name`, `description`, `daily_routine`, `requirements_json`, `prospects_text`, `median_salary_eur`, `signals_json` (mots-clés liés aux passions/valeurs/spés), `level_compatibility` (3ème / lycée général / lycée pro)

**Given** le seed initial du MVP
**When** la migration de seed s'exécute
**Then** au moins 50 métiers sont créés couvrant un panel diversifié (sciences, social, tech, arts, BTP, soin, business…)
**And** au moins 15 métiers sont compatibles bac pro / 3ème (pour servir Mehdi)
**And** la curation est documentée (sources : Onisep open data, fiches ROME, validations humaines)

**Given** la qualité des données
**When** je consulte une fiche métier seed
**Then** elle a au minimum : 100-300 mots de description, 5 prérequis, 3 débouchés, 1 fourchette salariale, 1 journée type narrative
**And** aucun métier n'a de champ vide critique

**Given** les contraintes éthiques (risque inégalité Step 2)
**When** la curation est revue
**Then** au moins 30 % des métiers servent les profils "Mehdi" (bac pro, voies techniques, moins valorisées par défaut)

### Story 3.3 : Moteur de scoring vocationnel statistique + content-based

As a service IA Path-Advisor,
I want un moteur de scoring qui produit un score 0-100 par couple (profil élève, métier) basé sur features explicites et filtrage content-based,
So that le scoring soit explicable nativement (RGPD art. 22) et fonctionne sans gros volume de données (cold-start MVP).

**Acceptance Criteria :**

**Given** un profil élève avec passions, valeurs, niveau scolaire, bulletins (ou pas)
**When** un appel `/v1/score-metiers` est effectué
**Then** le service IA retourne une liste de 50 métiers scorés (id + score + signals_contributifs)
**And** la latence est < 3 s P95 (NFR-P1) sur instance de référence

**Given** le calcul du score
**When** un métier est scoré pour un élève
**Then** le score est une somme pondérée de features explicites : recouvrement passions × signaux métier, alignement valeurs, compatibilité niveau scolaire, qualité du dossier scolaire (si bulletins disponibles)
**And** chaque feature contributive est tracée avec son poids dans la réponse (explicabilité)

**Given** un profil incomplet (sans bulletins)
**When** le score est calculé
**Then** le moteur dégrade gracieusement (pondération bulletins → 0, autres features compensent)
**And** un flag `confidence_level` est ajouté à la réponse (Story 3.10)

**Given** la conformité versioning (ADD-10 + NFR-M3)
**When** un déploiement est effectué
**Then** chaque version du modèle est tracée avec : dataset d'entraînement (hash), hyperparamètres, métriques d'évaluation, date de déploiement
**And** un endpoint admin `/v1/model-version` retourne ces infos

### Story 3.4 : Liste métiers scorés affichée à l'élève

As a élève (Sarah, Mehdi, Léa),
I want voir une liste personnalisée de 8 métiers recommandés avec leur score 0-100,
So that je découvre les métiers qui me correspondent dès la fin de l'onboarding (FR20 + premier moment aha).

**Acceptance Criteria :**

**Given** mon onboarding est terminé (passions + niveau + bulletins ou skip)
**When** j'arrive sur l'écran "Mes métiers"
**Then** je vois une liste de 8 cartes `ScoreVocationnel` (Top 8 métiers scorés)
**And** chaque carte affiche : nom métier, score 0-100, phrase recopiable défendable, 3-5 chips signaux contributifs
**And** la liste est affichée en < 3 s P95 (NFR-P1)

**Given** le moment du premier aha
**When** la liste apparaît pour la première fois
**Then** une animation discrète (fade-in séquentiel 100 ms par carte) accueille la révélation
**And** au moins 1 métier inattendu (mais plausible) est inclus dans le Top 8 pour produire la surprise (validation par le moteur)

**Given** un retour ultérieur sur la liste
**When** je reviens consulter mes métiers
**Then** je vois la liste sans animation (anti-cirque UX-DR27)
**And** un indicateur "mis à jour le X" est visible si les recos ont changé depuis ma dernière visite

**Given** je peux interagir avec la liste
**When** je tape sur une carte métier
**Then** j'accède à la fiche métier détaillée (Story 3.5)
**Or** je peux marquer un métier en favori (sauvegarde dans "Mes paris")

### Story 3.5 : Fiche métier détaillée

As a élève,
I want consulter une fiche détaillée par métier (description, journée type, prérequis, débouchés, revenu),
So that je comprenne concrètement ce qu'est un métier avant d'explorer son parcours (FR21).

**Acceptance Criteria :**

**Given** je tape sur une carte `ScoreVocationnel` dans la liste des recos
**When** la fiche s'ouvre
**Then** je vois le composant `FicheMetier` (UX-DR9) avec sections : Hero (nom + score + phrase recopiable) / "C'est quoi" / "Pour qui" / "Comment y aller" / "Écoles cibles" / "Signaux contributifs"

**Given** la fiche est responsive
**When** je la consulte sur mobile (320 px+)
**Then** les sections sont empilées et l'accordéon collapse les sections non-prioritaires
**When** je la consulte sur desktop (1024 px+)
**Then** une sidebar TOC sticky permet de naviguer entre sections, sections en tabs horizontaux

**Given** la conformité accessibilité
**When** un utilisateur de lecteur d'écran consulte la fiche
**Then** la hiérarchie h1 → h2 → h3 est stricte (1 h1 par page, pas de skip)
**And** les sections sont annoncées sémantiquement

### Story 3.6 : Explicabilité des signaux contributifs (RGPD art. 22)

As a élève,
I want comprendre quels signaux ont contribué au score d'un métier recommandé,
So that j'ai confiance dans la recommandation et je peux la défendre, conformément à RGPD art. 22 (FR22).

**Acceptance Criteria :**

**Given** je suis sur une carte `ScoreVocationnel` ou une `FicheMetier`
**When** je tape sur "Pourquoi ce score ?" ou sur un chip signal contributif
**Then** un drawer / popover s'ouvre montrant les signaux qui ont fait monter (ou descendre) ce score
**And** chaque signal est expliqué en langage naturel : "Ton 16 en SVT a fortement contribué (+12 pts)", "Ta passion pour le bénévolat hôpital (+8 pts)", "L'appréciation 'élève engagée' (+4 pts)"

**Given** la conformité art. 22 RGPD
**When** je consulte l'explicabilité
**Then** je vois aussi un lien "Demander une revue humaine" (Story 3.7)
**And** la méthodologie du scoring est accessible en 2 clics depuis n'importe quelle reco (lien "Comment ça marche")

**Given** l'explicabilité est intégrée au design UX
**When** je consulte le composant
**Then** il ne sent pas "explication légale obligatoire" mais "moment produit propre" (Step 4 — "explicabilité comme munition narrative")
**And** le copy est positif : "Voilà les ingrédients qui ont fait monter ce métier", pas "Justification du score"

### Story 3.7 : Demander une revue humaine d'une recommandation

As a élève,
I want demander une revue humaine d'une recommandation qui me semble incorrecte ou choquante,
So that je peux exercer mon droit RGPD art. 22 à l'intervention humaine et le système apprenne (FR23).

**Acceptance Criteria :**

**Given** je suis sur une fiche métier qui me paraît absurde
**When** je tape sur "Cette reco me dérange — demander une revue"
**Then** un formulaire court s'ouvre : raison (3 catégories : "Ne me correspond pas du tout" / "Métier choquant ou inapproprié" / "Autre") + commentaire libre optionnel

**Given** je soumets la demande
**When** la demande est enregistrée
**Then** elle apparaît dans la file d'attente admin (Epic 9)
**And** je reçois un email de confirmation "Ta demande est prise en compte, on te répondra sous 7 jours ouvrés"
**And** la reco contestée est marquée visuellement "en revue" jusqu'à réponse admin

**Given** la revue admin est traitée (Epic 9)
**When** l'admin répond
**Then** je reçois la réponse par email + notification in-app
**And** si la reco était correcte, le copy explique pourquoi sans paternalisme ; si la reco était mauvaise, le modèle est marqué pour ajustement

### Story 3.8 : Signaler une erreur ou information obsolète sur une fiche métier

As a élève ou utilisateur attentif,
I want signaler une erreur ou information obsolète sur une fiche métier,
So that le référentiel reste à jour grâce au community sourcing (FR24).

**Acceptance Criteria :**

**Given** je suis sur une fiche métier et je remarque une erreur
**When** je tape sur "Signaler une erreur" en pied de fiche
**Then** un formulaire compact s'ouvre demandant : type d'erreur (4 catégories : "Description inexacte" / "Débouchés périmés" / "Lien cassé" / "Autre"), localisation précise (champ optionnel pour pointer la section), commentaire libre

**Given** je soumets le signalement
**When** il est enregistré
**Then** il apparaît dans la file admin (Epic 9 — workflow modération sous 7 jours)
**And** je reçois un toast "Merci, ton signalement a été pris en compte"
**And** une trace est ajoutée au journal d'audit

**Given** l'admin traite mon signalement
**When** la fiche est mise à jour
**Then** je reçois (optionnellement, opt-in dans paramètres) une notification "La fiche que tu as signalée a été mise à jour"

### Story 3.9 : Adaptation des recommandations par niveau scolaire

As a élève (Mehdi 3ème ou Sarah Terminale),
I want que mes recos métiers soient adaptées à mon niveau scolaire et à la filière vers laquelle je suis orienté,
So that mes recos soient cohérentes et actionnables (FR25).

**Acceptance Criteria :**

**Given** je suis Mehdi (3ème, orientation bac pro à confirmer)
**When** le moteur me score
**Then** au moins 60 % de mon Top 8 est compatible avec un parcours bac pro
**And** les 40 % restants incluent des métiers généraux accessibles via bac général + études supérieures

**Given** je suis Sarah (Terminale spé Maths + SVT)
**When** le moteur me score
**Then** mon Top 8 privilégie les métiers compatibles avec mes spés (santé, ingénierie, sciences, environnement)
**And** les fiches métier mentionnent explicitement les spés requises

**Given** je change de niveau scolaire (Mehdi qui passe en 2nde Pro)
**When** je mets à jour mon profil (Story 2.6)
**Then** mes recos sont recalculées et la composition du Top 8 évolue en conséquence
**And** un message contextuel m'explique le changement : "Tes recos s'adaptent à ta nouvelle situation"

### Story 3.10 : Niveau de confiance affiché sur les recos en profil incomplet

As a élève Léa qui n'a pas encore ajouté ses bulletins,
I want comprendre que mes recos sont indicatives sans pour autant me sentir "cas spécial",
So that je peux explorer le produit avec dignité et savoir ce qui s'enrichira en complétant mon profil (FR26 + UX-DR25).

**Acceptance Criteria :**

**Given** mon profil est incomplet (sans bulletins)
**When** je consulte mes recos vocationnelles
**Then** la structure visuelle est strictement identique à celle d'un profil complet (mode normal = mode dégradé)
**And** chaque score affiche un label discret "indicatif" en `text-caption color-text-muted` (pas en rouge, pas en alerte)

**Given** je tape sur une carte métier
**When** je consulte l'explicabilité (Story 3.6)
**Then** je vois quels signaux ont contribué + un message factuel "Avec tes bulletins, on pourrait préciser ton score à ±5 pts près au lieu de ±15 actuellement"
**And** un CTA discret propose "Ajouter mes bulletins" (1 tap pour ouvrir le mini-flow)

**Given** la conformité émotionnelle Step 4
**When** je suis Léa
**Then** je ne vois JAMAIS de message culpabilisant ("Tu manques de données" / "Profil insuffisant")
**And** la posture est : voilà ce qu'on a, voilà ce qui s'ajouterait. Choix libre.

### Story 3.11 : Composant `ScoreVocationnel` réutilisable

As a développeur Path-Advisor,
I want un composant `ScoreVocationnel` standardisé affichant un score métier avec phrase recopiable et chips signaux,
So that la présentation des scores soit cohérente sur tous les écrans (UX-DR5 + UX-DR23 pattern phrase recopiable).

**Acceptance Criteria :**

**Given** le composant est implémenté en suivant les tokens design
**When** je l'instancie avec props (`metierId`, `score`, `phraseRecopiable`, `signals[]`, `variant`)
**Then** il affiche :
- Header : nom métier (h3 weight 600) + score 0-100 (chip droite, couleur sémantique selon score)
- Body : phrase recopiable italic + bouton "Copier" subtil (tap-to-copy)
- Footer : 3-5 chips signaux contributifs cliquables → drawer explicabilité (Story 3.6)

**Given** les variants `compact` / `expanded` / `comparison`
**When** je l'utilise dans différents contextes
**Then** `compact` (liste recos) : tout en card 360×160 px max ; `expanded` (drill-down) : sections détaillées ; `comparison` : 2 cartes côte à côte sur mobile (swipe) / desktop (grid)

**Given** l'accessibilité
**When** un lecteur d'écran lit le composant
**Then** le score est annoncé "Compatible à 78 % avec ce métier"
**And** la phrase recopiable a un `aria-label` clair, le bouton copier indique "Copier la phrase défendable"
**And** les chips signaux sont `role="button"` avec navigation clavier

**Given** le tap-to-copy
**When** je tape sur le bouton copier
**Then** la phrase est copiée dans le presse-papier
**And** un toast 3 s confirme "Phrase copiée — colle-la où tu veux"

### Story 3.12 : Composant `FicheMetier` réutilisable

As a développeur Path-Advisor,
I want un composant `FicheMetier` page produit complète avec sections structurées,
So that chaque métier ait une présentation cohérente et exhaustive (UX-DR9).

**Acceptance Criteria :**

**Given** le composant est implémenté
**When** je le rends pour un métier donné (Story 3.4)
**Then** il affiche 6 sections : Hero / C'est quoi / Pour qui / Comment y aller / Écoles cibles / Signaux contributifs

**Given** les variants responsive
**When** je consulte sur mobile (320 px+)
**Then** sections empilées avec accordéon (sections 3, 4, 5 collapsées par défaut)
**When** je consulte sur desktop (1024 px+)
**Then** TOC sticky à gauche + sections en tabs horizontaux

**Given** la variante `print-friendly` (pour artefact conseillère, Epic 5 export)
**When** je rends le composant en mode print
**Then** les sections sont linéarisées en 1 colonne sans CTAs interactifs
**And** une mise en page A4 propre est générée

**Given** l'accessibilité
**When** un lecteur d'écran parcourt la fiche
**Then** la hiérarchie h1 → h2 → h3 est stricte
**And** chaque section a un landmark sémantique (`<section aria-labelledby="...">`)

## Epic 4 : Graphe de Parcours & Stats d'Admission (Deuxième Aha)

Servir le DEUXIÈME moment "aha" et le différenciateur produit central : l'élève voit son graphe-récit interactif avec ses chances réelles d'admission par école. Animation séquentielle 720-800 ms, alternative tabulaire RGAA AA, low-data mode visuellement indiscernable.

### Story 4.1 : Référentiel formations / écoles / établissements MVP (100+ entrées)

As a content / data ops Path-Advisor,
I want un référentiel de 100+ formations et écoles curées (prépas, BTS, BUT, licences, écoles d'ingé, écoles de commerce, lycées pro),
So that les graphes de parcours puissent être construits avec des données crédibles et la carte scolaire respectée (FR28).

**Acceptance Criteria :**

**Given** une table `schools` et une table `formations` en PostgreSQL
**When** je consulte le schéma
**Then** chaque école contient : `id`, `slug`, `name`, `type`, `city`, `region`, `postal_code`, `lat/lon` (carte scolaire), `tuition_min_eur`, `tuition_max_eur`, `apprenticeship`, `internship`, `selectivity_index` (1-5), `public_private`
**And** chaque formation contient : `id`, `name`, `school_id`, `duration_years`, `parcoursup_open`, `affelnet_open`, `target_metiers` (relation many-to-many vers `professions`)

**Given** le seed initial du MVP
**When** la migration de seed s'exécute
**Then** au moins 100 formations + écoles sont créées (curation Onisep open data + Parcoursup CSV + community sourcing manuel)
**And** au moins 15 lycées pro avec leur option (avionique, ébénisterie, électromécanique…) pour servir Mehdi (FR31)
**And** la couverture géographique inclut au moins les 5 grandes métropoles + représentation rurale

**Given** la qualité éditoriale
**When** je consulte une fiche école seed
**Then** elle a au minimum description 100-200 mots, débouchés top 3, dates Parcoursup, frais réels, statut conventionné/internat, lien officiel

### Story 4.2 : Moteur de prédiction d'admission (open data Parcoursup + fourchettes)

As a service IA Path-Advisor,
I want un moteur de prédiction d'admission qui produit une proba ou fourchette par couple (profil élève, école) basé sur les datasets open data Parcoursup,
So that les élèves voient des stats d'admission crédibles sans nécessiter un modèle DL custom (FR29 + NFR-I7).

**Acceptance Criteria :**

**Given** les datasets open data Parcoursup (CSV annuels MENJS)
**When** un import batch est exécuté (job cron mensuel)
**Then** les statistiques d'admission par formation sont calculées et stockées en cache (Redis + table `admission_stats_history`)
**And** chaque formation a au minimum : taux d'admission global, distribution moyennes admises, distribution mentions admises

**Given** un appel `/v1/predict-admission` avec profil élève + école cible
**When** le moteur s'exécute
**Then** il retourne une fourchette (`min_proba`, `expected_proba`, `max_proba`) + cadrage qualitatif (audacieux / réaliste / sûr)
**And** la latence est < 2 s P95 (NFR-P2)

**Given** un profil sans bulletins (Léa)
**When** le moteur prédit
**Then** la fourchette est plus large (30-65 % au lieu de 38-45 %)
**And** le label qualitatif inclut "estimation indicative — affine avec ton profil"

**Given** la conformité éthique
**When** un profil rare ou un score bas est rencontré
**Then** le moteur ne retourne JAMAIS de probabilité < 5 % comme valeur ponctuelle (anti-humiliation)
**And** la garde-fou produit affiche plutôt "Pari très audacieux" sans chiffre cruel

### Story 4.3 : Affichage graphe de parcours par métier

As a élève,
I want voir un ou plusieurs graphes de parcours scolaires concrets menant à un métier sélectionné,
So that je comprenne comment y arriver depuis ma situation actuelle (FR27 + deuxième moment aha).

**Acceptance Criteria :**

**Given** je suis sur une fiche métier (Story 3.5) et je tape sur "Voir le parcours"
**When** la vue parcours s'ouvre
**Then** je vois 1 chemin principal par défaut (UX-DR6) avec 3-5 nœuds (lycée → étape intermédiaire 1 → étape 2 → école cible)
**And** le graphe est rendu en < 2 s P95 (NFR-P2) sur Android 3 Go RAM
**And** sous le graphe, une grille de fiches écoles (`FicheEcole` Story 4.4) est affichée

**Given** plusieurs chemins existent vers ce métier
**When** je consulte la vue
**Then** le chemin affiché par défaut est celui calculé comme le plus probable / accessible pour mon profil
**And** un bouton "Voir d'autres chemins (N)" m'affiche les alternatives

**Given** je suis Mehdi (3ème bac pro)
**When** je consulte le parcours pour "Technicien aéronautique"
**Then** le graphe commence par un lycée pro associé ("Bac Pro Aéronautique option Avionique") et non un lycée général
**And** les cartes écoles sont des lycées pro de ma carte scolaire (FR31)

### Story 4.4 : Fiche école / formation détaillée

As a élève,
I want consulter une fiche détaillée par école / formation (frais, durée, sélectivité, débouchés, dates de candidature),
So that j'aie toutes les infos pour décider d'inclure cette école dans mes vœux (FR28).

**Acceptance Criteria :**

**Given** je tape sur une fiche école dans la grille post-graphe
**When** la fiche complète s'ouvre
**Then** je vois le composant `FicheEcole` (densité Doctolib, UX-DR7) avec header (nom + ville + logo) ; métadonnée première (proba d'admission personnalisée — `CarteAdmission`) ; métadonnées secondaires en pills (durée, statut public/privé, alternance, sélectivité, internat, distance) ; body description ; débouchés top 3 ; dates Parcoursup ou Affelnet

**Given** la fiche est responsive
**When** je consulte sur mobile
**Then** card stacked full-width avec scroll
**When** je consulte sur desktop
**Then** layout deux colonnes (info + carte géographique optionnelle)

**Given** la fiche est partagée (école partenaire envoi anticipé, Epic 5)
**When** un CTA "Envoyer mon profil à cette école" est éligible
**Then** il apparaît visible (premium gating, Epic 5)

### Story 4.5 : Statistique d'admission personnalisée par école

As a élève,
I want voir, pour chaque école cible, ma probabilité personnalisée d'admission avec son cadrage qualitatif,
So that je peux faire des choix stratégiques pour Parcoursup en connaissant mes vraies chances (FR29).

**Acceptance Criteria :**

**Given** je consulte la grille d'écoles post-graphe ou une fiche école
**When** la stat d'admission s'affiche
**Then** je vois le composant `CarteAdmission` (UX-DR8) avec stat principale (display-1) + label qualitatif (audacieux / réaliste / sûr) + ligne de contexte ("moyenne admise dernière promo : 14,5") + levier d'action ("+ 2 points en maths → 58 %") + footnote si applicable

**Given** la conformité Step 7 (chiffre dominant collé au nœud cible dans le graphe)
**When** le graphe affiche le nœud école cible
**Then** la stat est rendue inline avec le nœud (display-1 48-56 px, couleur sémantique)
**And** le label qualitatif est visible directement sous le chiffre

**Given** je suis Léa (profil incomplet)
**When** je consulte mes stats
**Then** le label affiche "estimation indicative — affine avec ton profil" sans dramatiser
**And** la structure visuelle est strictement identique à un profil complet (UX-DR25 mode normal = mode dégradé)

### Story 4.6 : Filtres graphes — proximité, coût, sélectivité, alternance

As a élève,
I want filtrer les graphes de parcours selon des critères (proximité géographique, coût maximum, niveau de sélectivité, alternance possible),
So that les recommandations correspondent à mes contraintes personnelles (FR30).

**Acceptance Criteria :**

**Given** je suis sur la vue parcours d'un métier
**When** je consulte la barre de filtres persistante en haut
**Then** je vois des filtres pills multi-select : Proximité (≤ 50 km, ≤ 200 km, France entière), Coût (gratuit, < 5 000 €/an, < 10 000 €/an, sans limite), Sélectivité (très accessible, accessible, sélectif, très sélectif), Mode (alternance possible, internat)

**Given** je modifie un filtre
**When** le filtre est appliqué
**Then** la grille d'écoles se met à jour en < 1 s sans rechargement de page
**And** un compteur indique "N écoles cibles correspondent à tes filtres"
**And** "Effacer tout" est toujours visible

**Given** je teste une combinaison de filtres qui ne retourne aucune école
**When** la grille est vide
**Then** un empty state explique : "Aucune école ne correspond. Élargis tes critères, vois aussi les écoles privées ?"
**And** un CTA suggère de relâcher un filtre spécifique

**Given** l'accessibilité (UX-DR32 search & filtering pattern Doctolib)
**When** un utilisateur de lecteur d'écran navigue les filtres
**Then** chaque filtre annonce son état + le nombre de résultats appliqués

### Story 4.7 : Adaptation graphe par niveau scolaire (3ème → lycée pro)

As a élève Mehdi (3ème, bac pro),
I want que le graphe de parcours commence par un lycée pro associé à mon orientation (et non un lycée général),
So that mon parcours soit réaliste pour ma situation (FR31).

**Acceptance Criteria :**

**Given** je suis Mehdi (3ème, orientation bac pro à confirmer)
**When** je consulte le graphe pour "Technicien aéronautique"
**Then** le premier nœud est "Bac Pro Aéronautique option Avionique" (à un lycée pro spécifique de ma carte scolaire)
**And** le deuxième nœud est "BTS Aéronautique"
**And** un nœud terminal "option : poursuite école d'ingé en alternance" est inclus

**Given** je peux voir les lycées pro accessibles
**When** la grille d'écoles s'affiche pour le nœud "Bac Pro Aéronautique"
**Then** elle liste 2-3 lycées pro géographiquement accessibles depuis ma commune (carte scolaire intégrée)
**And** les ouvertures Affelnet (dates de candidature 3ème) sont visibles

**Given** je suis Sarah (Terminale)
**When** je consulte le même métier
**Then** le graphe commence par "Bac S / Spé Maths+SVT" (étape déjà accomplie)
**And** continue vers "Prépa BCPST" ou "PASS" ou "IUT Mesures Physiques"
**And** les dates Parcoursup sont affichées (pas Affelnet)

### Story 4.8 : Favoris écoles cibles + "Mes paris"

As a élève,
I want sauvegarder des écoles cibles dans une liste de favoris pour pouvoir les comparer et les retrouver,
So that je puisse construire ma stratégie Parcoursup au fil du temps (FR32).

**Acceptance Criteria :**

**Given** je suis sur une fiche école ou dans un graphe
**When** je tape sur "Ajouter à mes paris" (icône cœur ou bookmark)
**Then** l'école est ajoutée à ma liste "Mes paris" (sauvegarde immédiate, pas de validation)
**And** un toast confirme l'ajout

**Given** je consulte ma page "Mes paris"
**When** elle s'affiche
**Then** je vois toutes mes écoles cibles sous forme de `ParcoursCard` (Strava-style) regroupées par métier
**And** je peux comparer 2 écoles côte à côte en mode `compare`
**And** je peux retirer une école d'un tap

**Given** je n'ai encore aucun pari
**When** je consulte "Mes paris"
**Then** un empty state explique "Tu n'as pas encore exploré tes premiers paris. Va voir tes métiers recommandés et clique sur 'Voir le parcours'."
**And** un CTA me ramène vers la liste de métiers (Story 3.4)

### Story 4.9 : Composant `GraphParcours` (LE composant central)

As a développeur Path-Advisor,
I want un composant `GraphParcours` interactif qui rend un graphe-récit avec animation séquentielle 720-800 ms, hiérarchie visuelle stricte et alternative tabulaire RGAA AA,
So that le moment central de Path-Advisor soit servi avec qualité et conforme à toutes les contraintes (UX-DR6).

**Acceptance Criteria :**

**Given** le composant est implémenté avec react-flow ou SVG custom (décision tech à trancher au prototypage sprint 5)
**When** je l'instancie avec props (`nodes[]`, `edges[]`, `targetSchool`, `admissionStat`, `isFirstRender`)
**Then** il rend le graphe avec nœud cible 64-72 px en zone bas-droite (couleur sémantique selon proba), nœuds intermédiaires 36-44 px plus pâles, layout subtilement diagonal montant ou en arc, liens épaisseur variable plus épais sur segment final, pas d'icônes Lucide dans les nœuds, stat collée au nœud cible + label qualitatif

**Given** la première interaction de la session (`isFirstRender: true`)
**When** le composant se monte
**Then** une animation séquentielle 720-800 ms en 5 phases s'exécute (Nœud 1 lycée 120 ms + pause 60 ms + Lien 1→2 + Nœud 2 180 ms + Lien 2→3 + Nœud 3 180 ms + Lien 3→cible + Nœud cible 220 ms avec overshoot)
**And** labels intermédiaires apparaissent en fade après (+150 ms)
**And** grille écoles cibles apparaît en opacity 0.4→1 après (+200 ms hors séquence)

**Given** un retour ultérieur (`isFirstRender: false`)
**When** le composant se monte
**Then** l'animation NE se rejoue PAS (anti-cirque, UX-DR27)
**And** un très subtil highlight 100 ms sur le nœud cible peut éventuellement s'exécuter

**Given** la conformité `prefers-reduced-motion`
**When** l'utilisateur a activé reduced-motion
**Then** la séquence est remplacée par un fade global 200 ms (`motion-quick`)

**Given** la conformité RGAA AA (NFR-A5)
**When** un utilisateur navigue le composant
**Then** une alternative tabulaire est OBLIGATOIREMENT accessible via un toggle visible "Vue tableau"
**And** la table parallèle a étapes en ligne, écoles cibles en colonne, lisible au lecteur d'écran
**And** les nœuds sont focusables au clavier (tab order : lycée → étapes → cible → CTA)
**And** ARIA `role="img"` + `aria-label` descriptif du parcours est appliqué au SVG container

**Given** un profil incomplet (Léa, low-data mode)
**When** le composant se rend
**Then** la structure visuelle est strictement identique
**And** seule la stat label passe à "estimation indicative"

### Story 4.10 : Composant `FicheEcole` (densité Doctolib)

As a développeur Path-Advisor,
I want un composant `FicheEcole` densité Doctolib avec proba personnalisée comme métadonnée première,
So that les fiches écoles soient scannables en 3 secondes et cohérentes partout (UX-DR7).

**Acceptance Criteria :**

**Given** le composant est implémenté
**When** je l'instancie avec props (`schoolId`, `userProfile`, `variant`)
**Then** il rend header (logo / photo école + nom + ville) + métadonnée première `CarteAdmission` + métadonnées secondaires en pills + body (description + débouchés top 3) + footer (CTAs)

**Given** les variants `card` / `expanded` / `compare`
**When** je l'utilise dans différents contextes
**Then** `card` : grille mobile-friendly ; `expanded` : drill-down full page ; `compare` : deux écoles côte à côte

**Given** la conformité accessibilité
**When** un lecteur d'écran rencontre le composant
**Then** `role="article"` + headings hiérarchiques + métadonnées en `<dl><dt><dd>` sémantique + touch targets 44 × 44 px

**Given** un profil Léa (low-data state)
**When** le composant se rend
**Then** la `CarteAdmission` affiche "estimation indicative"
**But** la structure et toutes les métadonnées sont identiques (UX-DR25)

### Story 4.11 : Composant `CarteAdmission` (Revolut-style)

As a développeur Path-Advisor,
I want un composant atomique `CarteAdmission` réutilisable affichant stat + cadrage qualitatif + contexte + levier d'action,
So that chaque stat d'admission soit présentée de manière cohérente et défendable (UX-DR8 + UX-DR24).

**Acceptance Criteria :**

**Given** le composant est implémenté en suivant les tokens design
**When** je l'instancie avec props (`admissionStat`, `qualitativeLabel`, `contextLine`, `actionLever`, `variant`)
**Then** il rend stat principale en display-1 ou display-2 selon variant, couleur sémantique selon valeur, label qualitatif sous le chiffre + tag visuel, ligne de contexte, levier d'action calculé, footnote optionnelle

**Given** les variants `large` / `medium` / `small` / `export`
**When** utilisé dans différents contextes
**Then** `large` : graphe nœud cible ; `medium` : fiche école ; `small` : liste comparaison ; `export` : re-rendu PNG sans levier

**Given** l'accessibilité
**When** un lecteur d'écran lit le composant
**Then** annonce formatée : "38 % d'admission à INSA Lyon — pari audacieux. + 2 points en maths feraient passer à 58 %."
**And** la couleur sémantique est doublée par le label texte (color-blind safe, UX-DR33)

**Given** une stat récemment mise à jour (après réponse école envoi anticipé, Epic 5)
**When** le composant se rend
**Then** un badge "+ 14 pts" visible pendant 24 h indique le changement
**And** une animation discrète (200 ms fade-in) souligne l'évolution

### Story 4.12 : Composant `ParcoursCard` (Strava-style recap)

As a développeur Path-Advisor,
I want un composant `ParcoursCard` qui résume un parcours sauvegardé en carte capturable Strava-style,
So that la page "Mes paris" et les exports soient visuels et partageables (UX-DR19).

**Acceptance Criteria :**

**Given** le composant est implémenté
**When** je l'instancie avec props (`metier`, `parcours`, `targetSchool`, `admissionStat`)
**Then** il rend une card screenshot-friendly : header (métier visé h3) + mini-graphe (silhouette du parcours en 4-5 nœuds) + `CarteAdmission` variant `small` pour l'école cible + footer (phrase recopiable + bouton "Capturer")

**Given** la card est dense mais aérée
**When** je la rends dans "Mes paris" (Story 4.8)
**Then** elle est lisible en 3 s sans tap
**And** elle tient en 360 × 280 px max sur mobile

**Given** je consulte mes paris au retour J+30 (Epic 8 `DeltaRecap`)
**When** une stat a évolué
**Then** la `ParcoursCard` correspondante a un badge "+ 14 pts" 24 h
**And** est prioritaire en haut de liste

### Story 4.13 : Composant `StatPersonnelle` (indicateur compatibilité additif)

As a développeur Path-Advisor,
I want un composant `StatPersonnelle` optionnel et additif affichant un indicateur de compatibilité personnelle (3 états qualitatifs),
So that les utilisateurs avec bulletins voient une information enrichie sans humilier ceux qui n'en ont pas (UX-DR20).

**Acceptance Criteria :**

**Given** le composant est implémenté
**When** je l'instancie avec props (`compatibility: 'compatible' | 'a_renforcer' | 'au_dessus' | null`, `school`)
**Then** il rend un petit indicateur visuel (point coloré + label texte court "Profil compatible" / "À renforcer" / "Profil au-dessus") sous la `CarteAdmission`
**And** si `compatibility === null`, le composant ne rend RIEN (pas d'état "indisponible" — il disparaît)

**Given** un profil Sarah avec bulletins suffisants
**When** je consulte une fiche école
**Then** le composant affiche son état compatibilité ("Profil compatible" en vert sage discret)
**And** un tooltip optionnel explique en 1 phrase ce que ça veut dire

**Given** un profil Léa sans bulletins
**When** je consulte la même fiche école
**Then** le composant est strictement absent
**And** AUCUN message "Importe tes bulletins pour voir" ne stigmatise

**Given** la conformité UX-DR25 (mode normal = mode dégradé)
**When** Sarah voit son indicateur sur une école A mais pas sur une école B
**Then** l'absence sur l'école B passe inaperçue

## Epic 5 : Premium B2C & Envoi Anticipé Biface

Permettre à l'élève premium (10,99 €/mois via Stripe ou parent) d'envoyer son profil aux écoles partenaires. L'école répond en 3 actions, la stat d'admission se met à jour en < 5 min.

### Story 5.1 : Intégration Stripe (sandbox local + production)

As a système Path-Advisor,
I want une intégration Stripe abstraite supportant le mode test local (sandbox) en PoC et le mode production en cloud,
So that les paiements sont opérationnels en dev et prod sans modification du code applicatif (NFR-I1).

**Acceptance Criteria :**

**Given** la couche d'abstraction paiement
**When** je consulte le code
**Then** une interface `PaymentProvider` est définie avec méthodes (`createCheckoutSession`, `handleWebhook`, `cancelSubscription`, `getSubscriptionStatus`)
**And** une implémentation `StripeProvider` utilise les clés sandbox en dev, prod en production via env vars

**Given** un environnement local
**When** je lance `docker-compose up`
**Then** Stripe sandbox est configuré avec un webhook listener local (Stripe CLI ou ngrok-like)
**And** je peux tester un paiement end-to-end avec la carte test `4242 4242 4242 4242`

**Given** la conformité PCI-DSS
**When** un paiement est traité
**Then** AUCUNE donnée carte n'est stockée côté Path-Advisor (tokens Stripe uniquement)
**And** Stripe Checkout (hosted) ou Stripe Elements est utilisé (pas de form custom)

### Story 5.2 : Tiers d'abonnement freemium / premium + gating

As a système Path-Advisor,
I want gérer les 2 tiers B2C (Freemium gratuit / Premium 10,99 €/mois) avec gating de fonctionnalités,
So that les features premium sont accessibles uniquement aux abonnés.

**Acceptance Criteria :**

**Given** la table `subscriptions` en PostgreSQL
**When** je consulte le schéma
**Then** elle lie un user_id à un tier (`free` / `premium`), un statut (`active` / `cancelled` / `past_due`), une période (`current_period_end`)
**And** elle référence le `stripe_subscription_id` pour traçabilité

**Given** un user en tier `free`
**When** il tente d'accéder à une feature premium (envoi anticipé, vue parent étendue, notifs proactives)
**Then** le middleware d'autorisation bloque l'accès
**And** un `PaywallContextuel` (Story 5.11) s'affiche au lieu de la feature

**Given** un user en tier `premium` actif
**When** il accède aux features premium
**Then** l'accès est autorisé sans friction
**And** son statut est rafraîchi périodiquement via webhook Stripe

**Given** la dégradation gracieuse
**When** un user premium passe en `past_due` (paiement échoué)
**Then** un grace period de 7 jours est appliqué (features premium toujours accessibles)
**And** des emails de relance sont envoyés à J+0, J+3, J+7
**Then** après 7 jours sans paiement, le tier passe à `free` et les features premium se ferment proprement

### Story 5.3 : Souscription premium par l'élève

As a élève,
I want souscrire à l'abonnement premium 10,99 €/mois pour débloquer l'envoi anticipé et les autres features premium,
So that je puisse activer les leviers stratégiques pour mes vœux Parcoursup.

**Acceptance Criteria :**

**Given** je suis sur un écran déclenchant un `PaywallContextuel` (ex : "Envoyer mon profil à cette école")
**When** je clique sur "Passer en premium — 10,99 €/mois"
**Then** je suis redirigé vers Stripe Checkout (mode hosted)
**And** le checkout affiche : nom du plan, prix, ce que ça débloque, méthode de paiement (CB, Apple Pay, Google Pay)

**Given** je complète le paiement avec succès
**When** Stripe envoie le webhook `checkout.session.completed`
**Then** mon tier passe immédiatement à `premium` (avec rollback si webhook échoue)
**And** je suis redirigé vers la page d'origine avec la feature débloquée
**And** je reçois un email de confirmation

**Given** je veux annuler mon abonnement
**When** je vais dans Paramètres → "Abonnement" → "Annuler"
**Then** une `ConsentDialog` confirme l'annulation
**And** je conserve l'accès premium jusqu'à la fin de la période payée
**And** au-delà, mon tier passe à `free`

### Story 5.4 : Envoi anticipé d'un profil à une école partenaire

As a élève premium,
I want déclencher un envoi anticipé de mon profil à une école partenaire,
So that je puisse obtenir un signal d'admission précoce et augmenter mes chances Parcoursup (FR33).

**Acceptance Criteria :**

**Given** je suis premium et je consulte une fiche école partenaire (Story 4.4)
**When** je clique sur "Envoyer mon profil à cette école"
**Then** un Sheet bottom (mobile) ou modal (desktop) s'ouvre me demandant motivation libre optionnelle (Story 5.5) + confirmation des données partagées
**And** une `ConsentDialog` finale me liste ce que l'école verra (profil scolaire synthétique, motivation, métier visé, parcours sélectionné — pas autres recos)

**Given** je confirme l'envoi
**When** la demande est créée
**Then** un job async est mis en queue (notification email + push à l'école)
**And** je suis redirigé vers "Mes envois" avec mon envoi en statut `pending` (en attente de réponse école sous 7 jours)
**And** une trace est ajoutée au journal d'audit

**Given** je n'ai droit qu'à un nombre limité d'envois par mois (5 envois/mois en premium MVP)
**When** j'atteins la limite
**Then** un message m'informe sans urgence "Tu as utilisé tes 5 envois ce mois — ta limite repart le 1er du mois prochain"
**And** je peux toujours sauvegarder l'école en favori sans envoyer

### Story 5.5 : Motivation libre modérée a priori

As a élève premium,
I want accompagner mon envoi anticipé d'une motivation libre (200-500 mots),
So that je peux contextualiser mon profil au-delà des chiffres scolaires (FR34).

**Acceptance Criteria :**

**Given** je suis dans le flow d'envoi anticipé (Story 5.4)
**When** j'arrive à l'étape "Motivation"
**Then** je peux saisir un texte libre 200-500 mots dans un textarea
**And** un compteur de caractères m'aide à respecter la longueur
**And** un placeholder me donne 2-3 suggestions d'angles

**Given** je soumets ma motivation
**When** le texte est enregistré
**Then** il passe en statut `pending_moderation`
**And** l'envoi à l'école est temporairement bloqué (queue d'attente modération admin Story 9.4)
**And** un email m'informe : "Ta motivation est en cours de relecture (sous 24 h ouvrées)"

**Given** la modération admin approuve la motivation
**When** elle passe en statut `approved`
**Then** l'envoi à l'école est débloqué et le job de notification se déclenche
**And** je reçois une notification "Ton profil est en route vers l'école"

**Given** la modération admin refuse la motivation
**When** elle passe en statut `rejected`
**Then** je reçois un email expliquant le motif et la possibilité de réécrire
**And** l'envoi reste bloqué jusqu'à correction

### Story 5.6 : Espace école partenaire — auth + réception profils

As a école partenaire (Mme Garcia, Polytech Marseille),
I want m'authentifier sur un espace dédié et recevoir les profils élèves envoyés en anticipé,
So that je puisse traiter les candidatures précoces et identifier les profils intéressants (FR35 + FR36).

**Acceptance Criteria :**

**Given** je suis admin école partenaire et j'ai été onboardée par l'équipe Path-Advisor
**When** je me connecte à l'espace école
**Then** j'arrive sur un MFA enrollment au premier login (Story 1.6 — obligatoire NFR-S2)
**And** une fois MFA actif, j'arrive sur ma file de réception des profils

**Given** ma file de réception
**When** je consulte la liste
**Then** je vois les profils reçus en file (les plus récents en haut), avec nom élève, métier visé, parcours sélectionné, score compatibilité école, date réception, statut (`pending` / `responded` / `expired_7d`)
**And** je peux filtrer par statut, trier par date ou par score

**Given** je tape sur un profil
**When** la fiche détail s'ouvre
**Then** je vois `EcoleResponseFlow` (Story 5.12) avec profil scolaire synthétique + motivation déclarée + métier visé + parcours envisagé
**But** PAS les autres recos vocationnelles de l'élève, ni les autres écoles ciblées (frontière RBAC NFR-S4)

**Given** un envoi reçu il y a > 7 jours sans réponse
**When** le statut bascule à `expired_7d`
**Then** l'élève reçoit une notification "L'école n'a pas répondu — stat inchangée"
**And** l'école ne peut plus répondre (entrée archivée)

### Story 5.7 : 3 actions de réponse école

As a école partenaire,
I want répondre à un envoi anticipé via 3 actions explicites (Profil intéressant / Profil non aligné / Demande d'entretien),
So that je donne un signal clair à l'élève qui ajuste ses chances d'admission (FR37).

**Acceptance Criteria :**

**Given** je suis sur une fiche profil élève dans mon `EcoleResponseFlow`
**When** je veux répondre
**Then** je vois 3 boutons d'action distincts : "Profil intéressant — candidature encouragée" (primary), "Profil non aligné" (secondary), "Demande d'entretien" (tertiary avec icône calendrier)
**And** un champ optionnel "Commentaire pour l'élève" (max 200 mots, modéré)

**Given** je choisis "Profil intéressant"
**When** je confirme
**Then** la réponse est enregistrée + l'événement est mis en queue pour propagation (Story 5.8)
**And** un toast confirme "Réponse envoyée — l'élève reçoit la notification dans les 5 min"

**Given** je choisis "Profil non aligné"
**When** je confirme
**Then** une `ConsentDialog` me rappelle que le message à l'élève doit être respectueux et constructif
**And** un template diplomatique est suggéré ("Ton profil est intéressant mais ne correspond pas à nos critères cette année. Continue à explorer !")

**Given** je choisis "Demande d'entretien"
**When** je confirme
**Then** je propose 2-3 créneaux (visio externe en MVP — RDV intégré en fast-follow FR-FF4)
**And** l'élève reçoit la proposition et peut accepter / proposer un autre créneau

### Story 5.8 : Mise à jour stat admission < 5 min après réponse école

As a élève,
I want voir ma statistique d'admission se mettre à jour rapidement après que l'école a répondu à mon envoi anticipé,
So that mes décisions Parcoursup sont basées sur des données fraîches (FR38 + NFR-P5).

**Acceptance Criteria :**

**Given** une école a répondu à mon envoi anticipé
**When** l'événement est mis en queue
**Then** le job de propagation s'exécute en < 5 minutes (NFR-P5)
**And** ma stat d'admission pour cette école est recalculée : "Profil intéressant" → + 10 à + 20 points, "Demande d'entretien" → + 5 à + 10 points + flag entretien, "Profil non aligné" → - 10 à - 20 points

**Given** la stat a été mise à jour
**When** je vois ma fiche école ou mon graphe parcours
**Then** la nouvelle valeur s'affiche avec un badge "+ 14 pts" visible pendant 24 h
**And** une notification push (FR-FF2 fast-follow) ou email (MVP) m'informe : "INSA Lyon a répondu — voir le détail"

**Given** je suis en train de consulter la fiche école au moment de la mise à jour
**When** le polling 30 s (ADD-8 pas WebSocket MVP) détecte le changement
**Then** la valeur se met à jour en place avec une animation discrète 300 ms
**And** aucune action utilisateur n'est requise

### Story 5.9 : Historique des envois anticipés côté élève

As a élève,
I want consulter le statut et l'historique de tous mes envois anticipés,
So that je peux suivre mes démarches et planifier mes vœux Parcoursup (FR39).

**Acceptance Criteria :**

**Given** je vais sur "Mes envois" (depuis le menu profil ou bottom tab)
**When** la page s'affiche
**Then** je vois la liste de tous mes envois, regroupés par statut (En attente / Réponses positives / Réponses négatives / Entretiens demandés / Expirés)
**And** chaque envoi affiche école, métier visé, date d'envoi, statut, impact stat (badge "+ 14 pts" si applicable)

**Given** je tape sur un envoi
**When** la fiche détail s'ouvre
**Then** je vois ma motivation envoyée + la réponse de l'école (texte + action) + l'impact sur ma stat + un lien vers la fiche école

**Given** je n'ai aucun envoi
**When** je consulte la page
**Then** un empty state explique "Tu n'as pas encore envoyé ton profil à une école. C'est une feature premium qui peut booster tes chances d'admission."
**And** un CTA explore "Voir les écoles partenaires" liste les écoles éligibles

### Story 5.10 : Reporting interne école

As a école partenaire (Mme Garcia),
I want consulter un reporting interne sur les profils reçus, mes actions et les conversions,
So that je peux mesurer l'impact de Path-Advisor sur mon recrutement (FR40).

**Acceptance Criteria :**

**Given** je suis dans l'espace école et je vais sur "Reporting"
**When** la page s'affiche
**Then** je vois des KPIs : nombre profils reçus (mensuel + cumul année), répartition par métier visé, par région d'origine, par action prise (intéressant / non aligné / entretien), taux de conversion en candidature Parcoursup déclarée

**Given** je veux explorer en détail
**When** je drill down
**Then** je peux voir le détail par mois, par métier, par profil scolaire
**And** je peux exporter le reporting en CSV ou PDF

**Given** la conformité RGPD
**When** je consulte le reporting agrégé
**Then** aucune donnée nominative n'est visible (les profils sont anonymisés au niveau du reporting)
**And** je dois aller sur la fiche individuelle pour voir le nom (avec audit log)

### Story 5.11 : Composant `PaywallContextuel`

As a développeur Path-Advisor,
I want un composant `PaywallContextuel` qui s'affiche quand un user free tente d'accéder à une feature premium,
So that le passage premium soit déclenché de manière contextuelle, non agressive (UX-DR15).

**Acceptance Criteria :**

**Given** le composant est implémenté
**When** je l'instancie avec props (`feature`, `context`, `benefits[]`)
**Then** il rend une carte ou un Sheet avec titre contextuel "Cette feature est en premium", description (1-2 phrases), 2-3 bénéfices listés, CTA primary "Passer en premium — 10,99 €/mois", CTA secondary "Plus tard"

**Given** la conformité émotionnelle (anti-urgence-fabriquée, anti-FOMO)
**When** le composant s'affiche
**Then** il ne crie JAMAIS ("DERNIÈRE CHANCE !!", "Plus que 3 jours !!")
**And** il ne culpabilise pas (pas de "Tu rates des opportunités")
**And** le ton est factuel : "Voici ce que cette feature t'apporte. Choix libre."

**Given** un user free clique "Plus tard"
**When** le composant se ferme
**Then** il retourne sur sa navigation précédente sans pénalité
**And** un cooldown léger évite que le paywall réapparaisse à chaque tap (max 1×/session par feature)

### Story 5.12 : Composant `EcoleResponseFlow`

As a développeur Path-Advisor,
I want un composant `EcoleResponseFlow` qui affiche un profil élève + permet à l'école de répondre en 3 actions,
So that l'espace école soit cohérent et efficace pour Mme Garcia (UX-DR22).

**Acceptance Criteria :**

**Given** le composant est implémenté
**When** je l'instancie avec props (`studentProfile`, `motivation`, `targetMetier`, `targetSchool`, `parcours`)
**Then** il rend header (nom élève + score compatibilité école + date d'envoi) + section "Profil scolaire" (moyennes, spés, niveau, appréciations enseignants synthétique) + section "Motivation" + section "Métier & parcours visés" + footer (3 boutons d'action)

**Given** les frontières RBAC sont strictes
**When** je consulte un profil reçu
**Then** je ne vois PAS les autres écoles ciblées par l'élève
**And** je ne vois PAS les autres recos vocationnelles de l'élève
**And** un message rappelle "Tu vois uniquement ce que l'élève a choisi de partager avec toi"

**Given** la densité desktop (école = desktop primaire)
**When** je consulte le composant sur écran 1024+ px
**Then** layout en 2 colonnes (profil à gauche, actions à droite)
**And** raccourcis clavier supportés (`i` pour "intéressant", `n` pour "non aligné", `e` pour "entretien")

## Epic 6 : Espaces Tiers — Parent & Conseillère B2B

Permettre aux parents (M. Martin) de voir les métiers explorés + payer le premium ; aux conseillères B2B (Mme Dupont, 5 pilotes MVP) d'utiliser le dashboard cohorte pour préparer leurs entretiens.

### Story 6.1 : Invitation parent par l'élève → création compte parent lié

As a élève,
I want inviter un de mes parents à créer un compte lié à mon profil,
So that mon parent puisse suivre mon orientation et éventuellement souscrire au premium pour moi (FR3 cas d'usage parent).

**Acceptance Criteria :**

**Given** je suis dans Paramètres → "Mes proches"
**When** je clique sur "Inviter un parent"
**Then** je saisis email parent + lien de parenté (optionnel) + un message court personnalisable
**And** une `ConsentDialog` me liste explicitement ce que mon parent verra (métiers explorés, parcours sauvegardés, coûts) et ce qui restera privé (bulletins détaillés, appréciations enseignants)
**And** je confirme

**Given** un email d'invitation est envoyé au parent
**When** mon parent clique sur le lien
**Then** il atterrit sur une page de création compte parent
**And** il complète email + mdp + nom
**And** son compte est créé avec rôle `parent` lié à mon `user_id`

**Given** mon parent finalise l'inscription
**When** son compte est actif
**Then** je reçois une notification "Ton parent a rejoint Path-Advisor"
**And** je peux à tout moment révoquer son accès (Story 1.10)

### Story 6.2 : Vue parent — métiers explorés, parcours sauvegardés et coûts

As a parent (M. Martin) lié à un compte élève,
I want consulter les métiers que mon enfant a explorés et les parcours qu'il a sauvegardés avec leurs coûts,
So that je peux comprendre son cheminement et lui apporter un avis éclairé (FR41).

**Acceptance Criteria :**

**Given** je suis connecté en tant que parent et je consulte mon dashboard
**When** la page s'affiche
**Then** je vois les sections "Métiers explorés" (liste cartes `ScoreVocationnel` variant compact) + "Mes paris" de mon enfant (liste `ParcoursCard`) + "Coûts estimés des parcours sauvegardés" (somme + breakdown)

**Given** je tape sur un métier ou un parcours
**When** la vue détail s'ouvre
**Then** je vois la fiche métier / parcours avec les infos accessibles à mon rôle
**But** PAS les bulletins de mon enfant

**Given** la conformité avec la matrice RBAC (Story 1.7)
**When** je tente d'accéder à une URL contenant les bulletins de mon enfant
**Then** je reçois une 403 Forbidden et l'accès est loggué (NFR-S4)

### Story 6.3 : Frontières confidentialité parent (bulletins + appréciations masqués)

As a système Path-Advisor,
I want garantir que le compte parent n'a aucun accès aux bulletins détaillés ni aux appréciations enseignants de son enfant,
So that la confidentialité de l'élève soit protégée conformément à FR41 et la matrice RBAC.

**Acceptance Criteria :**

**Given** la matrice RBAC du PRD
**When** un endpoint API retourne des données élève
**Then** le filtre RBAC actif sur le rôle parent retire automatiquement : `bulletins_pdf_url`, `bulletins_extracted`, `teacher_appreciations`
**And** un test d'intégration vérifie l'absence de ces champs dans les réponses API parent

**Given** l'audit RGPD
**When** un parent accède au profil de son enfant
**Then** un événement est loggué dans `audit_log` avec champs précis

**Given** l'UX cohérente
**When** un parent voit une `CarteAdmission` (proba d'admission)
**Then** elle est affichée car elle est un résultat dérivé (pas une donnée brute bulletins)
**But** le levier d'action ("+ 2 points en maths → 58 %") est masqué côté parent (révèle indirectement les notes)

### Story 6.4 : Paiement premium par parent au bénéfice élève

As a parent,
I want souscrire à l'abonnement premium 10,99 €/mois au bénéfice de mon enfant,
So that mon enfant accède aux features premium sans avoir à payer lui-même (FR42).

**Acceptance Criteria :**

**Given** je suis sur mon dashboard parent et l'élève est en tier `free`
**When** je consulte la section "Abonnement de mon enfant"
**Then** je vois un CTA "Passer mon enfant en premium — 10,99 €/mois"
**And** une description claire de ce que ça débloque pour l'élève

**Given** je clique sur le CTA
**When** je suis redirigé vers Stripe Checkout
**Then** le paiement est associé à mon compte parent mais le bénéficiaire est l'`user_id` enfant
**And** après paiement, le tier de mon enfant passe à `premium`

**Given** je peux gérer l'abonnement
**When** je vais dans "Mes abonnements"
**Then** je vois l'historique des paiements + la date de prochaine échéance
**And** je peux annuler (avec impact uniquement sur l'enfant à la fin de la période payée)

**Given** la conformité audit
**When** un paiement parent → enfant est traité
**Then** une trace dans `audit_log` lie le `paying_user_id` (parent) au `beneficiary_user_id` (enfant)

### Story 6.5 : Onboarding établissement B2B + création cohorte

As a admin Path-Advisor (Karim) onboardant un établissement pilote,
I want créer un nouveau tenant établissement et générer ses accès conseillère,
So that les 5 pilotes B2B MVP soient opérationnels.

**Acceptance Criteria :**

**Given** je suis admin Path-Advisor et je vais dans Back-office → "Établissements"
**When** je crée un nouvel établissement
**Then** je saisis nom, type (lycée / collège), ville, UAI (code RNE), responsable contact, début / fin licence (pilote 12 mois gratuit ou payant 5 000 €/an)
**And** un `tenant_id` est créé en base avec isolation RLS (Story 1.8)

**Given** la cohorte initiale
**When** je crée la cohorte (Terminale 2025-2026)
**Then** je peux importer la liste élèves via CSV (UAI + nom + email parent pour < 15 ans)
**And** chaque élève reçoit un email d'invitation Path-Advisor pré-rempli

**Given** la création des comptes conseillère
**When** j'ajoute une conseillère (Mme Dupont)
**Then** elle reçoit un email d'invitation avec lien vers l'onboarding MFA (Story 1.6)
**And** son rôle est `counselor` lié au `tenant_id` établissement

### Story 6.6 : Dashboard cohorte conseillère B2B

As a conseillère d'orientation (Mme Dupont),
I want consulter un dashboard cohorte de mes élèves avec taux de complétion, métiers les plus explorés, distribution filière,
So that je puisse identifier les tendances et préparer mes entretiens (FR43).

**Acceptance Criteria :**

**Given** je suis connectée en tant que conseillère (MFA validé)
**When** j'arrive sur mon dashboard
**Then** je vois `CohortDashboard` (Story 6.10) avec KPIs en haut (nombre élèves cohorte, taux de complétion profil, nombre élèves en mode dégradé), section "Métiers les plus explorés" (top 10 histogramme), section "Distribution filière" (pie chart), section "Activité récente"

**Given** la densité desktop (Mme Dupont = écran 27")
**When** je consulte le dashboard
**Then** layout dense Linear-like avec tous les KPIs visibles sans scroll sur 1440 × 900 px
**And** raccourcis clavier supportés (`/` recherche élève, `j/k` navigation, `e` entretien, `⌘K` command palette)

**Given** je veux drill-down sur un élève
**When** je tape sur une entrée
**Then** je vais sur le profil individuel (Story 6.8), à condition d'avoir le consentement (Story 6.7)

### Story 6.7 : Consentement élève → conseillère pour vue profil individuel

As a système Path-Advisor,
I want exiger un consentement explicite de l'élève avant qu'une conseillère puisse voir son profil individuel détaillé,
So that la confidentialité élève soit respectée conformément à FR44.

**Acceptance Criteria :**

**Given** un élève appartient à la cohorte d'un établissement pilote
**When** la conseillère tente d'accéder au profil individuel
**Then** si pas de consentement → l'accès est bloqué (vue restreinte uniquement : nom + cohorte + flag "consentement requis")
**And** une option "Demander le consentement à l'élève" est proposée à la conseillère

**Given** la conseillère demande le consentement
**When** la demande est envoyée
**Then** l'élève reçoit une notification "Mme Dupont, ta conseillère, souhaite consulter ton profil pour préparer ton entretien"
**And** l'élève voit un `ConsentDialog` lui expliquant ce que la conseillère verra et ce qui restera privé

**Given** l'élève accepte
**When** le consentement est enregistré
**Then** la conseillère peut consulter le profil individuel
**And** l'accès est loggué (`audit_log`) et révocable à tout moment par l'élève

**Given** l'élève refuse
**When** le refus est enregistré
**Then** la conseillère ne peut pas accéder au profil individuel
**And** elle peut redemander une fois plus tard (cooldown 7 jours pour ne pas harceler)

### Story 6.8 : Vue profil individuel élève côté conseillère

As a conseillère avec consentement élève,
I want consulter le profil individuel d'un élève (recos vocationnelles, parcours explorés, vœux en construction),
So that je puisse préparer un entretien d'orientation ciblé en < 2 minutes (FR44).

**Acceptance Criteria :**

**Given** j'ai le consentement élève
**When** je consulte son profil
**Then** je vois son nom + sa cohorte, ses 8 métiers Top recos (variant compact), ses parcours sauvegardés ("Mes paris"), son activité récente (dernière visite, dernière action), ses voeux en construction si déclarés
**But** je ne vois PAS ses identifiants de connexion, ses données de paiement (NFR-S4 RBAC counselor)

**Given** la préparation d'entretien
**When** je consulte le profil
**Then** je peux mettre des notes privées (visible uniquement par moi, attachées à mon compte conseiller, pas à l'élève)
**And** je peux exporter une fiche entretien PDF (synthèse profil + mes notes) pour usage interne

**Given** la conformité B2B
**When** je consulte le profil
**Then** l'accès est tracé dans `audit_log` (NFR-S4)
**And** l'élève voit dans sa `PermissionList` (Story 6.11) que je l'ai consulté avec horodatage

### Story 6.9 : Export reporting anonymisé cohorte (CSV / PDF)

As a conseillère,
I want exporter un reporting anonymisé de ma cohorte en CSV ou PDF,
So that je puisse partager des stats internes à mon établissement sans exposer des données nominatives (FR45).

**Acceptance Criteria :**

**Given** je suis sur mon `CohortDashboard`
**When** je clique sur "Exporter le reporting"
**Then** je choisis le format (CSV, PDF) et la portée (cohorte entière, sous-ensemble filtré)
**And** un job async génère le fichier en < 30 s

**Given** le fichier est généré
**When** je le télécharge
**Then** il contient les stats agrégées SANS aucune donnée nominative
**And** les seuils anti-réidentification sont appliqués (ex : ne pas exposer une catégorie ayant moins de 5 élèves)

**Given** la traçabilité
**When** l'export est généré
**Then** une trace est ajoutée à `audit_log` (NFR-S4) avec horodatage et hash du contenu

### Story 6.10 : Composant `CohortDashboard` (desktop dense Linear-like)

As a développeur Path-Advisor,
I want un composant `CohortDashboard` desktop dense avec KPIs et drill-down,
So that Mme Dupont ait un dashboard pro efficace en < 2 min (UX-DR21).

**Acceptance Criteria :**

**Given** le composant est implémenté pour desktop primary (1024+ px)
**When** je l'instancie avec props (`cohortId`, `dateRange`)
**Then** il rend layout dense Linear-like avec sections KPIs / Top métiers / Distribution / Activité récente
**And** chaque section utilise les composants standards (Card, Table, BarChart via Recharts ou Visx)

**Given** la navigation clavier first-class
**When** je suis dans le dashboard
**Then** `/` ouvre la recherche élève, `j/k` navigue dans les listes, `e` ouvre la préparation entretien, `⌘K` ouvre la command palette globale

**Given** le responsive mobile (Mme Dupont peut consulter ponctuellement sur mobile)
**When** je consulte sur < 1024 px
**Then** un message explique : "Cette interface est optimisée pour desktop. Tu peux la consulter ici mais l'efficacité y est sur grand écran."
**And** le layout dégrade gracieusement

**Given** la conformité RGAA AA
**When** un utilisateur de lecteur d'écran navigue
**Then** les KPIs sont annoncés avec leur valeur + contexte
**And** les graphes ont une alternative tabulaire (NFR-A5)

### Story 6.11 : Composant `PermissionList` étendu (révocation 1-tap + audit visible)

As a élève,
I want un composant `PermissionList` enrichi qui montre tous mes accès tiers + dernière consultation + révocation 1-tap,
So that je garde un contrôle transparent et instantané sur qui voit mon profil (FR8 + FR9 + UX-DR16).

**Acceptance Criteria :**

**Given** le composant est implémenté
**When** je le consulte dans Paramètres → "Accès tiers"
**Then** chaque entrée affiche nom tiers + rôle + date d'octroi + **date dernière consultation** (visible côté élève — nouveauté vs Story 1.9 basique)
**And** un bouton "Révoquer" est visible 1-tap

**Given** je tape sur "Voir l'historique d'accès" d'un tier
**When** la modale s'ouvre
**Then** je vois la liste horodatée de toutes les consultations (date + données vues) sur les 90 derniers jours
**And** je peux exporter ce log en CSV (cf droit RGPD Story 1.11)

**Given** la révocation 1-tap
**When** je révoque un accès
**Then** une `ConsentDialog` courte confirme + l'accès est bloqué immédiatement (Story 1.10)
**And** le tier reçoit une notification de révocation

## Epic 7 : Découverte Publique & SEO

Permettre l'acquisition organique : Sarah trouve Path-Advisor via Google sur une recherche "que faire après le bac" ou "devenir ingénieure biomédicale" et arrive sur une page métier indexable, performante, conforme Core Web Vitals.

### Story 7.1 : Pages publiques SSR — fiches métier indexables

As a moteur de recherche (Google, Bing) et acquisition organique,
I want une URL canonique stable et indexable par métier (`/metiers/{slug}`),
So that les pages métiers Path-Advisor apparaissent sur les recherches "devenir X" (FR46 + ADD-6).

**Acceptance Criteria :**

**Given** une fiche métier seed (Story 3.2)
**When** je visite `/metiers/ingenieure-biomedicale` sans être connecté
**Then** la page est rendue en SSR (Next.js) avec contenu HTML complet visible avant JavaScript
**And** je vois description + journée type + revenu médian + prérequis + parcours types (variants publics anonymes des graphes)
**And** un CTA "Crée ton compte pour voir tes chances réelles" invite à l'inscription

**Given** la performance (NFR-P3)
**When** Google PageSpeed Insights audite la page
**Then** TTFB < 1 s, LCP mobile < 2,5 s, FID < 100 ms, CLS < 0,1 (Core Web Vitals au vert)
**And** le HTML est cachable côté CDN (TTL 1h, revalidation On-Demand sur signalement)

**Given** la conformité accessibilité publique
**When** un utilisateur sans compte consulte la page
**Then** elle est RGAA AA (NFR-A1)
**And** elle est lisible avec JavaScript désactivé

### Story 7.2 : Pages publiques SSR — fiches formation / école indexables

As a moteur de recherche et acquisition organique,
I want une URL canonique stable et indexable par école / formation (`/formations/{slug}` ou `/ecoles/{slug}`),
So that les pages formations apparaissent sur les recherches "INSA Lyon", "BUT MMI", "Prépa BCPST" (FR46).

**Acceptance Criteria :**

**Given** une fiche école seed (Story 4.1)
**When** je visite `/formations/insa-lyon-genie-biomedical` sans être connecté
**Then** la page est rendue en SSR avec : nom école + ville + photo + description + débouchés + frais + sélectivité brute (anonyme, pas personnalisée) + dates Parcoursup
**And** un CTA "Crée ton compte pour voir ta proba d'admission personnalisée" invite à l'inscription

**Given** des pages liées
**When** je consulte une fiche école
**Then** je vois des liens internes vers les métiers cible (`/metiers/{slug}`) et des écoles similaires (cross-linking)

**Given** la conformité Core Web Vitals
**When** auditée
**Then** mêmes critères que Story 7.1 (TTFB < 1 s, LCP < 2,5 s)

### Story 7.3 : Landing pages long-tail SEO

As a moteur de recherche et acquisition organique,
I want des pages SEO long-tail générées dynamiquement à partir du référentiel (`/devenir-{metier}`, `/{niveau}/quel-bac-pour-{metier}`, `/{niveau}/integrer-{ecole}`),
So that Path-Advisor capte les requêtes spécifiques d'orientation (FR46).

**Acceptance Criteria :**

**Given** le référentiel professions + écoles + formations
**When** je visite `/devenir-infirmiere`
**Then** la page combine la fiche métier + un panel "Quels bacs / formations choisir ?" + des liens vers les écoles cibles + un FAQ structuré

**Given** les variantes par niveau scolaire
**When** je visite `/3eme/quel-bac-pour-technicien-aero`
**Then** le contenu est adapté aux options 3ème (bac pro / général / techno) avec les lycées pro associés à Mehdi

**Given** la stratégie SEO
**When** ces pages sont indexées
**Then** elles utilisent Schema.org `Occupation`, `EducationalOrganization`, `Course`, `FAQPage` markup pour rich snippets
**And** chaque URL a un title + meta description optimisés

### Story 7.4 : Sitemap XML + robots.txt + Schema.org markup

As a moteur de recherche,
I want une sitemap XML auto-générée et un balisage Schema.org strict pour découvrir et indexer toutes les pages publiques,
So that Path-Advisor maximise son indexabilité (FR46).

**Acceptance Criteria :**

**Given** le contenu public (métiers + écoles + landing long-tail)
**When** un crawler accède à `/sitemap.xml`
**Then** la sitemap liste toutes les URLs publiques (métiers, formations, écoles, landings) avec `lastmod` et `priority`
**And** elle est segmentée par type si > 50 000 URLs (sitemap index)

**Given** `/robots.txt`
**When** un crawler le lit
**Then** il autorise l'indexation des pages publiques
**And** il interdit l'indexation des pages applicatives (`/app/*`, `/api/*`, `/admin/*`)

**Given** le balisage Schema.org
**When** un crawler analyse une fiche métier
**Then** le markup `<script type="application/ld+json">` contient un objet `Occupation` complet
**And** Google Rich Results Test valide le markup sans erreur

**Given** la soumission à Google
**When** la sitemap est publiée
**Then** elle est soumise à Google Search Console + Bing Webmaster Tools

### Story 7.5 : Open Graph + Twitter Cards + meta tags

As a réseau social (Instagram, WhatsApp, X, LinkedIn),
I want un preview riche quand un utilisateur partage une page Path-Advisor,
So that le partage social viralise correctement avec image + titre + description (FR46 et viralité organique).

**Acceptance Criteria :**

**Given** chaque page publique Path-Advisor
**When** son URL est partagée sur WhatsApp / Instagram Story / X / LinkedIn
**Then** un preview affiche : titre optimisé + description courte + image Open Graph 1200 × 630 px générée dynamiquement (incluant nom métier ou école)

**Given** la spec Open Graph
**When** je consulte le head HTML d'une page
**Then** je vois `og:title`, `og:description`, `og:image`, `og:url`, `og:type` + Twitter Card équivalents

**Given** des images dynamiques
**When** une page est servie
**Then** une image OG est générée à la volée (Next.js `ImageResponse` API) avec branding Path-Advisor sobre + texte contextuel

### Story 7.6 : Core Web Vitals au vert sur toutes les pages publiques

As a Path-Advisor,
I want des Core Web Vitals au vert sur 100 % des pages publiques indexables,
So that le SEO ne soit pas pénalisé et l'acquisition organique reste forte (NFR-P3 + UX-DR34).

**Acceptance Criteria :**

**Given** une page métier publique
**When** Google PageSpeed Insights audite mobile
**Then** LCP < 2,5 s, FID < 100 ms, CLS < 0,1
**And** Performance score ≥ 80, SEO score ≥ 95

**Given** la mesure continue
**When** la CI s'exécute sur chaque PR
**Then** un job Lighthouse vérifie les Core Web Vitals sur 5 pages publiques de référence
**And** le merge est bloqué si une métrique critique dégrade

**Given** les optimisations
**When** une page est servie
**Then** images en AVIF/WebP avec `srcset` responsive, polices preloadées + `font-display: swap`, JS critique < 200 ko, code-splitting par route Next.js

### Story 7.7 : i18n foundation (français MVP, préparation francophonie)

As a système Path-Advisor,
I want une foundation i18n structurée (clés de traduction extractibles, pas de strings hardcodés),
So that l'expansion francophonie (Belgique, Maroc, Tunisie, Sénégal) en growth soit faisable sans refactor majeur (ADD-11).

**Acceptance Criteria :**

**Given** la stack i18n (next-intl ou next-i18next ou similaire)
**When** je consulte le code
**Then** toutes les strings UI sont dans des fichiers `messages/fr.json` (français MVP unique)
**And** aucun string user-facing n'est hardcodé dans le JSX

**Given** la structure de namespaces
**When** je consulte `messages/fr.json`
**Then** les clés sont organisées par feature (`onboarding.*`, `recos.*`, `parcours.*`, `paywall.*`)
**And** une convention de naming est documentée

**Given** la préparation francophonie growth
**When** un nouveau pays est ajouté
**Then** il suffit de créer `messages/{locale}.json` (ex : `fr-BE`, `fr-MA`) avec les overrides spécifiques (ex : "Parcoursup" → "Equivalent local")
**And** aucun changement de code applicatif n'est requis

## Epic 8 : Continuité Temporelle & Notifications

Servir le moat différenciant vs LLMs grand public : l'utilisateur revient à J+30 et voit "ce qui a bougé" via un écran `DeltaRecap` style Spotify Wrapped léger et des notifications email calées sans urgence fabriquée.

### Story 8.1 : Email transactionnel — abstraction Mailpit local + Postmark prod

As a système Path-Advisor,
I want une couche d'abstraction email permettant Mailpit local en PoC et Postmark / SendGrid en production,
So that les notifications email sont opérationnelles partout sans modification de code (NFR-I2).

**Acceptance Criteria :**

**Given** la couche d'abstraction email
**When** je consulte le code
**Then** une interface `EmailProvider` est définie avec méthodes (`sendTransactional`, `sendBatch`)
**And** une implémentation `MailpitProvider` (local) + `PostmarkProvider` (prod) basculent via env var

**Given** un environnement local
**When** je lance `docker-compose up`
**Then** Mailpit est exposé sur un port (typiquement 8025) avec interface web
**And** tous les emails envoyés en dev arrivent dans Mailpit (vérifiable visuellement)

**Given** la dégradation gracieuse (NFR-R4)
**When** le service email est indisponible
**Then** les envois sont mis en queue avec retry exponentiel
**And** aucun email n'est perdu silencieusement

### Story 8.2 : Engine de notifications email avec templates et opt-in

As a élève / parent / conseillère / école,
I want recevoir des notifications email pertinentes que je peux contrôler (opt-in / opt-out par catégorie),
So that je suis informé sans être spammé (FR47).

**Acceptance Criteria :**

**Given** une table `notification_preferences` par user
**When** je vais dans Paramètres → "Notifications"
**Then** je peux activer / désactiver par catégorie (Calendrier Parcoursup, Réponses école, Nouvelles écoles pertinentes, Rappels de complétion profil)
**And** mes préférences sont sauvegardées immédiatement

**Given** les templates email
**When** un email est envoyé
**Then** il utilise un template MJML ou similaire (responsive mobile-friendly) avec branding Path-Advisor sobre
**And** il inclut un lien "Gérer mes notifications" + lien "Se désinscrire" (obligation légale)

**Given** la conformité RGPD
**When** un user se désinscrit
**Then** ses préférences sont mises à jour
**And** aucun email de cette catégorie n'est envoyé sans qu'un acte explicite ne réinscrive

### Story 8.3 : Notifications calendrier Parcoursup (sans urgence fabriquée)

As a élève (Sarah, Terminale),
I want recevoir des notifications email calées sur le calendrier Parcoursup (ouverture, J-30, résultats),
So that je sois préparée sans angoisse fabriquée (FR47 + UX-DR28 calendrier sans urgence).

**Acceptance Criteria :**

**Given** le calendrier Parcoursup (dates connues par avance, configuration admin)
**When** un jalon approche (ex : "Parcoursup ouvre dans 18 jours")
**Then** un email est envoyé aux élèves concernés (Terminale, post-bac) avec ton factuel
**And** le copy bannit toute urgence ("DERNIÈRE CHANCE", "Plus que 18 jours !!") — UX-DR28
**And** la posture est : "Voici où on en est. Voici ce que tu peux préparer d'ici là."

**Given** les jalons standards
**When** la config est en place
**Then** au moins 5 jalons sont notifiés : Ouverture Parcoursup, J-30 fermeture voeux, Fermeture voeux, Résultats phase principale, Résultats phase complémentaire
**And** chaque notification propose une checklist non-bloquante d'actions ("Voici ce que tu peux préparer")

**Given** la cohérence anti-urgence
**When** un utilisateur de lecteur d'écran consulte la notification
**Then** elle est annoncée sans alarmisme
**And** les CTAs sont calmes ("Revoir mes paris", "Compléter mon profil")

### Story 8.4 : Notification "réponse école" envoi anticipé

As a élève premium,
I want recevoir une notification email quand une école a répondu à mon envoi anticipé,
So that je puisse réagir rapidement (FR47 + lien avec Story 5.8).

**Acceptance Criteria :**

**Given** une école a répondu à mon envoi anticipé
**When** la stat est mise à jour (Story 5.8)
**Then** un email m'informe immédiatement : "INSA Lyon a répondu — voir le détail" + résumé en 1 phrase + CTA "Voir la réponse"

**Given** la conformité émotionnelle
**When** la réponse est "Profil non aligné"
**Then** le ton de l'email est diplomatique (pas "Mauvaise nouvelle !")
**And** il propose des alternatives ("Tu peux explorer d'autres écoles avec un profil similaire")

**Given** la conformité opt-in
**When** un utilisateur a désactivé cette catégorie de notification
**Then** aucun email n'est envoyé
**And** la notification reste visible in-app

### Story 8.5 : Notification "nouvelle école pertinente"

As a élève,
I want être notifié quand une nouvelle école / formation pertinente pour mon profil est ajoutée au référentiel,
So that mon graphe de parcours s'enrichit et je découvre de nouvelles opportunités (FR47).

**Acceptance Criteria :**

**Given** un admin ajoute une nouvelle école au référentiel (Story 9.2)
**When** le job de matching s'exécute (cron quotidien)
**Then** les élèves dont le profil correspond reçoivent une notification email "X écoles de plus correspondent à ton profil ingénieure biomédicale"
**And** le matching utilise les critères des recos vocationnelles (Story 3.3)

**Given** la fréquence d'envoi
**When** plusieurs écoles sont ajoutées en peu de temps
**Then** les notifications sont regroupées (digest hebdomadaire max) pour éviter le spam
**And** un compteur indique "5 nouvelles écoles correspondent à toi"

### Story 8.6 : Composant `DeltaRecap` — écran "voici ce qui a bougé"

As a élève qui revient à J+30,
I want voir un écran d'accueil qui me montre ce qui a bougé depuis ma dernière visite,
So that ma session démarre sur du delta, pas sur l'écran neutre (UX-DR14 + UX-DR29).

**Acceptance Criteria :**

**Given** le composant est implémenté (style Spotify Wrapped léger)
**When** je l'instancie pour un user au retour
**Then** il affiche les types de delta supportés :
- Carte "Réponse école envoi anticipé" : "INSA Lyon a répondu — profil intéressant" + stat avant/après
- Carte "Nouvelles écoles référencées" : "X écoles de plus correspondent à ton profil"
- Carte "Calendrier Parcoursup" : "Parcoursup ouvre dans 18 jours — voici ce que tu peux préparer"
- État stable (rien de neuf) : redirection silencieuse vers la home, pas d'écran vide

**Given** la conformité UX-DR29 (retour avec delta)
**When** je me connecte après J+1 ou plus
**Then** le DeltaRecap s'affiche en plein écran (1 carte par delta)
**And** chaque carte a un CTA primary unique ("Voir le parcours mis à jour", "Voir les nouvelles écoles", "Préparer mes vœux")
**And** un bouton "Tout vu, continuer" passe au dashboard normal

**Given** la conformité émotionnelle
**When** un delta est positif (réponse école positive, nouvelles écoles)
**Then** ton calme, pas confetti, pas "🎉" (anti-cirque)
**When** un delta est négatif (réponse école négative)
**Then** la carte est cadrée constructive ("INSA Lyon a refusé — voici 3 alternatives compatibles")

### Story 8.7 : Composant `CalendarNotification`

As a développeur Path-Advisor,
I want un composant `CalendarNotification` réutilisable pour toute notification calée sur calendrier Parcoursup,
So that le pattern "calendrier sans urgence" soit cohérent (UX-DR17 + UX-DR28).

**Acceptance Criteria :**

**Given** le composant est implémenté
**When** je l'instancie avec props (`jalon`, `daysUntil`, `recommendedActions[]`)
**Then** il affiche un titre factuel ("Parcoursup ouvre dans 18 jours"), une description calme, une checklist d'actions recommandées non-bloquantes
**And** AUCUN compte à rebours visuel agressif (pas de timer rouge clignotant)

**Given** la conformité émotionnelle UX-DR28
**When** je consulte le copy
**Then** il bannit "URGENT", "DERNIÈRE CHANCE", "Plus que X jours !!", "Ne rate pas"
**And** il utilise "Voici où on en est", "Voici ce que tu peux préparer"

**Given** la réutilisation
**When** je l'utilise dans email (Story 8.3) et dans `DeltaRecap` (Story 8.6)
**Then** le même composant alimente les deux contextes
**And** seul le rendering layer change (HTML email vs React app)

## Epic 9 : Back-office Administration & Modération

Permettre à Karim (admin Path-Advisor) de maintenir le référentiel professions/formations/écoles, traiter les signalements sous 7 jours, modérer les motivations libres a priori, versionner les modèles IA + dataset, et auditer le drift ML.

### Story 9.1 : CRUD référentiel professions

As a admin Path-Advisor (Karim),
I want créer, modifier et supprimer des fiches du référentiel professions,
So that je puisse maintenir la qualité éditoriale des 50 métiers MVP et étendre vers 500+ en growth (FR48 + NFR-SC5).

**Acceptance Criteria :**

**Given** je suis admin connecté (MFA validé)
**When** je vais dans Back-office → "Référentiel" → "Métiers"
**Then** je vois la liste des 50+ professions avec recherche, tri, filtre par statut (publié / brouillon / archivé)
**And** je peux créer un nouveau métier avec tous les champs (description, journée type, prérequis, débouchés, signaux, niveau compatibilité…)

**Given** je modifie une fiche existante
**When** je sauvegarde
**Then** un versionning de l'édition est tracé (historique consultable, rollback possible)
**And** un job background recalcule les recos vocationnelles impactées (lazy : seulement quand l'élève revient)

**Given** la conformité audit
**When** je modifie une fiche
**Then** une trace dans `audit_log` enregistre la modification (qui, quoi, quand)

### Story 9.2 : CRUD référentiel formations / écoles

As a admin Path-Advisor,
I want créer, modifier et supprimer des fiches du référentiel formations / écoles,
So that je puisse maintenir la qualité du référentiel 100+ formations MVP (FR48).

**Acceptance Criteria :**

**Given** je suis admin et je vais dans "Référentiel" → "Écoles"
**When** je consulte la liste
**Then** je peux filtrer par type (lycée pro / prépa / BTS / IUT / écoles d'ingé / commerce), par région, par statut
**And** je peux créer une école avec tous ses champs + lien vers formations associées

**Given** je peux importer en masse via CSV
**When** je télécharge un CSV d'écoles depuis open data Parcoursup
**Then** l'import valide chaque ligne + signale les conflits (école déjà existante)
**And** je peux drill-down pour résoudre les conflits manuellement

**Given** la traçabilité (NFR-S4)
**When** je modifie une école
**Then** l'historique est tracé + le job de recalcul des stats d'admission impactées s'exécute en background

### Story 9.3 : File de signalements + workflow modération sous 7 jours

As a admin Path-Advisor,
I want une file de signalements priorisée + workflow de traitement sous 7 jours,
So that les retours utilisateurs sont traités rapidement et la qualité du référentiel reste haute (FR49).

**Acceptance Criteria :**

**Given** des signalements ont été émis par les élèves (Story 3.8)
**When** je vais dans Back-office → "Signalements"
**Then** je vois la file ordonnée par âge + priorité (jalon : alerter si signalement > 7 jours non traité)
**And** je peux filtrer par type (erreur métier / école obsolète / contenu inapproprié)

**Given** je traite un signalement
**When** je l'ouvre
**Then** je vois la fiche concernée + le contexte + le message utilisateur
**And** je peux : corriger la fiche (lien direct vers Story 9.1 ou 9.2), rejeter le signalement (avec motif), demander des précisions à l'élève (via notification)

**Given** la résolution
**When** je marque le signalement résolu
**Then** l'élève signaleur reçoit une notification "La fiche que tu as signalée a été mise à jour" (si opt-in)
**And** la file se met à jour

### Story 9.4 : Modération a priori des motivations libres (envoi anticipé)

As a admin Path-Advisor,
I want modérer les motivations libres rédigées par les élèves a priori (avant transmission à l'école),
So that les contenus inappropriés / discriminatoires / les données personnelles tierces soient filtrés (FR50).

**Acceptance Criteria :**

**Given** un élève a soumis une motivation (Story 5.5)
**When** je vais dans Back-office → "Modération motivations"
**Then** je vois la file de motivations en attente (statut `pending_moderation`)
**And** je peux ouvrir une motivation et la consulter en plein écran

**Given** je modère une motivation
**When** je décide
**Then** je peux Approuver (statut `approved` → l'envoi se débloque, Story 5.5) ou Refuser (statut `rejected` avec catégorie : contenu inapproprié, données tierces, discrimination, autre + commentaire)

**Given** la SLA
**When** une motivation est dans la file
**Then** elle doit être traitée en < 24 h ouvrées
**And** un compteur d'âge alerte si > 24 h

**Given** l'aide à la modération
**When** je consulte une motivation
**Then** un pré-screening automatique (mots-clés à risque, données personnelles détectées) m'aide à prioriser
**But** la décision finale est toujours humaine (pas d'auto-refus)

### Story 9.5 : Versioning modèles IA + audit trail dataset

As a admin Path-Advisor,
I want versionner chaque modèle de recommandation IA avec son dataset d'entraînement et ses hyperparamètres,
So that les décisions IA soient auditables (RGPD art. 22 + NFR-M3 + ADD-10).

**Acceptance Criteria :**

**Given** un nouveau modèle est déployé
**When** le déploiement est traçé
**Then** la table `model_versions` enregistre : `id`, `name`, `version`, `dataset_hash` (SHA256 du dataset d'entraînement), `hyperparameters_json`, `evaluation_metrics_json`, `deployed_at`, `deployed_by`
**And** l'ancien modèle reste accessible en lecture (rollback possible)

**Given** un score IA produit pour un élève
**When** la décision est tracée
**Then** chaque scoring inclut le `model_version_id` utilisé
**And** je peux rejouer la décision à partir du modèle archivé (audit reproductibilité)

**Given** la conformité éthique (audit biais)
**When** je consulte les métriques d'évaluation d'un modèle
**Then** je vois les performance disaggregées par sous-population (genre, région, type d'établissement)
**And** un écart > 10 % inter-groupes déclenche une alerte avant déploiement

### Story 9.6 : Métriques audit ML (drift, biais)

As a admin Path-Advisor,
I want consulter les métriques d'audit ML (drift des prédictions, biais par sous-population, distribution des scores),
So that je détecte les dégradations du modèle en production (FR52).

**Acceptance Criteria :**

**Given** la production envoie des décisions de scoring
**When** je vais dans Back-office → "Audit ML"
**Then** je vois des métriques temps réel : distribution des scores vocationnels par mois, drift par rapport au baseline, distribution par sous-population (genre, région, niveau scolaire)

**Given** un drift est détecté (KS-test ou similaire au-dessus du seuil)
**When** la métrique devient critique
**Then** une alerte est envoyée à l'admin (email + Slack si configuré)
**And** un workflow de revue est proposé (réentraîner ? rollback ?)

**Given** les biais inter-groupes
**When** un écart > 10 % est détecté sur une métrique critique (score moyen par genre par exemple)
**Then** une alerte est envoyée + le modèle est marqué pour revue éthique

## Epic 10 : Fast-Follow (post-MVP immédiat mois 9-12)

Polish post-MVP : détection profils à risque dashboard conseillère, push web, tableau qualité référentiel admin, RDV visio intégré, parrainage / partage lien traçable.

### Story 10.1 : Détection profils à risque dashboard conseillère

As a conseillère B2B (Mme Dupont),
I want voir dans mon dashboard la liste des élèves "profils à risque" (faible engagement, profil incohérent, signes de décrochage),
So that je puisse intervenir proactivement (FR-FF1).

**Acceptance Criteria :**

**Given** des règles de détection sont définies (faible engagement = pas d'activité depuis 30 jours, profil incohérent = passions très divergentes des spés, décrochage = baisse moyenne > 2 points)
**When** un élève remplit un ou plusieurs critères
**Then** il apparaît dans la liste "Profils à risque" de son conseiller
**And** le motif est expliqué (pas opaque)

**Given** je consulte la liste
**When** je tape sur un profil
**Then** je vois le détail des signaux à risque + propositions d'action ("Suggérer un entretien")
**And** je peux marquer le profil comme "intervention en cours" pour éviter les doublons d'alertes

**Given** la conformité RGPD + dignité
**When** la liste est affichée
**Then** la formulation est constructive ("nécessite ton attention"), pas stigmatisante ("élève en échec")
**And** l'élève ne voit pas qu'il est marqué "à risque" (information conseillère uniquement)

### Story 10.2 : Push web notifications

As a élève / parent / conseillère / école,
I want recevoir des push web notifications en plus des emails,
So that je sois informé instantanément des événements critiques (FR-FF2).

**Acceptance Criteria :**

**Given** la stack Web Push (Service Worker + VAPID keys)
**When** un utilisateur active les push notifications
**Then** son navigateur enregistre l'abonnement et stocke le token
**And** les événements critiques (réponse école, calendrier Parcoursup) déclenchent un push

**Given** la conformité opt-in
**When** un user souhaite désactiver les push
**Then** il peut le faire dans Paramètres + révoque l'abonnement navigateur
**And** aucun push n'est envoyé après désactivation

**Given** la dégradation gracieuse
**When** un user n'a pas activé les push
**Then** seuls les emails sont envoyés (NFR-R4)

### Story 10.3 : Tableau qualité référentiel admin

As a admin Path-Advisor,
I want un tableau de bord de qualité du référentiel (couverture, fraîcheur, signalements en attente),
So that je gouverne la qualité éditoriale en continu (FR-FF3).

**Acceptance Criteria :**

**Given** je vais dans Back-office → "Qualité référentiel"
**When** la page s'affiche
**Then** je vois des KPIs : nombre de métiers (50/500), nombre de formations (100/1000), fraîcheur (% mis à jour ces 12 derniers mois), signalements ouverts, motivations en attente de modération
**And** des graphes de tendance sur 6 mois

**Given** des seuils d'alerte
**When** un KPI dépasse un seuil (ex : > 20 signalements ouverts, fraîcheur < 60 %)
**Then** une alerte visible me prévient
**And** un CTA me redirige vers la file à traiter

### Story 10.4 : RDV visio intégré école-élève

As a élève premium recevant une demande d'entretien d'une école,
I want pouvoir prendre un RDV visio directement dans Path-Advisor (calendrier + lien visio),
So that je n'ai pas à jongler entre apps externes (FR-FF4).

**Acceptance Criteria :**

**Given** une école a déclenché "Demande d'entretien" (Story 5.7)
**When** je reçois la proposition de RDV
**Then** je vois un mini-calendrier avec les 3 créneaux proposés par l'école
**And** je peux confirmer un créneau ou en proposer un autre

**Given** un créneau confirmé
**When** le RDV approche
**Then** un lien visio est généré (intégration Whereby / Daily.co / Jitsi self-hosted)
**And** un rappel email + push est envoyé J-1 et 1 h avant

**Given** la conformité RGPD
**When** le RDV se termine
**Then** aucune capture vidéo n'est conservée par Path-Advisor (transit only)

### Story 10.5 : Parrainage / partage avec lien traçable

As a élève satisfait de Path-Advisor,
I want partager le produit à un pair via un lien traçable,
So that la viralité organique se développe (FR-FF5).

**Acceptance Criteria :**

**Given** je vais dans Paramètres → "Parrainer un pote"
**When** je clique sur "Inviter"
**Then** un lien personnalisé est généré (ex : `pathadvisor.fr/r/{my_id}`)
**And** je peux le partager via WhatsApp / Instagram / SMS (share natif)

**Given** un pair clique sur mon lien
**When** il s'inscrit
**Then** son inscription est attribuée à mon parrainage
**And** je reçois une notification "Ton pote vient de rejoindre Path-Advisor"

**Given** des incentives éventuels (V2)
**When** N parrainages réussis (à définir post-MVP)
**Then** une récompense optionnelle pourrait être proposée (mois gratuit premium par exemple)
**But** sans dark pattern et sans urgence fabriquée

### Story 10.6 : Composant `SideFlow` (consentement parental en attente, etc.)

As a développeur Path-Advisor,
I want un composant `SideFlow` réutilisable pour les confirmations critiques qui ne bloquent pas l'exploration en cours,
So that les flow non-bloquants soient gérés proprement (UX-DR18).

**Acceptance Criteria :**

**Given** le composant est implémenté
**When** je l'instancie pour un cas (ex : consentement parental en attente Story 1.4)
**Then** un bandeau persistant non-bloquant apparaît en bas / haut de l'app
**And** l'exploration utilisateur reste possible sans validation immédiate

**Given** la conformité émotionnelle
**When** le bandeau s'affiche
**Then** il informe sans culpabiliser ("Ton parent reçoit l'email — tu peux continuer pendant qu'on vérifie")
**And** il a un CTA secondaire optionnel ("Relancer mon parent")

**Given** la résolution
**When** la condition se débloque (parent valide)
**Then** le bandeau disparaît + un toast confirme ("Ton compte est entièrement actif maintenant")
