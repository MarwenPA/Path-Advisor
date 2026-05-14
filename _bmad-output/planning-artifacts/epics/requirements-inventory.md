# Requirements Inventory

## Functional Requirements

### A. Comptes, Rôles & Conformité

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

### B. Profil Élève & Onboarding

- **FR13** : Un élève peut déclarer ses passions, centres d'intérêt et valeurs via un questionnaire structuré
- **FR14** : Un élève peut importer ses bulletins scolaires en format PDF, et le système peut extraire automatiquement notes et appréciations enseignants par OCR
- **FR15** : Un élève peut saisir manuellement ses notes et appréciations dans un formulaire structuré lorsque l'OCR échoue ou est indisponible
- **FR16** : Un élève peut déclarer son niveau scolaire (3ème, 2nde, 1ère, Terminale, post-bac), sa filière (général, technologique, professionnel) et ses spécialités
- **FR17** : Un élève peut compléter son profil partiellement et accéder à une expérience dégradée tant que ses bulletins ne sont pas importés
- **FR18** : Un élève peut mettre à jour son profil à tout moment (bulletins, passions, changement de filière)
- **FR19** : Un élève peut visualiser un score de complétude de son profil et identifier les éléments manquants

### C. Recommandation Vocationnelle

- **FR20** : Un élève peut recevoir une liste personnalisée de métiers recommandés, scorés sur une échelle de 0 à 100, dès la complétion du déclaratif
- **FR21** : Un élève peut consulter, pour chaque métier recommandé, une fiche détaillée (description, journée type, prérequis, débouchés, revenu médian)
- **FR22** : Un élève peut consulter, pour chaque métier recommandé, les signaux qui ont contribué à son score (explicabilité IA, RGPD art. 22)
- **FR23** : Un élève peut demander une revue humaine d'une recommandation qu'il juge incorrecte ou choquante
- **FR24** : Un élève peut signaler une erreur ou une information obsolète sur la fiche métier
- **FR25** : Le système peut adapter la nature des recommandations vocationnelles au niveau scolaire de l'élève (3ème → métiers compatibles bac pro ou général)
- **FR26** : Le système peut afficher un niveau de confiance sur chaque recommandation lorsque le profil est incomplet

### D. Recommandation de Parcours & Stats d'Admission

- **FR27** : Un élève peut consulter, pour chaque métier sélectionné, un ou plusieurs graphes de parcours scolaires menant à ce métier
- **FR28** : Un élève peut consulter, pour chaque école / formation d'un graphe, une fiche détaillée (frais, durée, sélectivité, débouchés, dates de candidature)
- **FR29** : Un élève peut consulter une statistique d'admission personnalisée (probabilité ou fourchette) pour chaque école cible, basée sur son profil scolaire
- **FR30** : Un élève peut filtrer les graphes selon des critères (proximité géographique, coût maximum, niveau de sélectivité, alternance possible)
- **FR31** : Le système peut adapter le graphe au niveau scolaire de l'élève (graphe partant d'un lycée pro associé pour un élève de 3ème orienté bac pro)
- **FR32** : Un élève peut sauvegarder des écoles cibles dans une liste de favoris pour comparaison

### E. Envoi Anticipé Écoles & Espace École

- **FR33** : Un élève premium peut déclencher un "envoi anticipé" de son profil à une école partenaire
- **FR34** : Un élève premium peut accompagner son envoi anticipé d'une motivation libre (texte modéré côté admin)
- **FR35** : Une école partenaire peut recevoir une notification (email + push) à chaque profil envoyé en anticipé
- **FR36** : Une école partenaire peut consulter une fiche profil élève synthétique (données scolaires, motivation, métier visé, parcours sélectionné), sans accès aux autres recos ou écoles ciblées
- **FR37** : Une école partenaire peut répondre à un envoi anticipé via 3 actions : *Profil intéressant — candidature encouragée* / *Profil non aligné* / *Demande d'entretien*
- **FR38** : Le système peut mettre à jour la statistique d'admission affichée à l'élève sous 5 minutes après une réponse école
- **FR39** : Un élève peut consulter le statut et l'historique de tous ses envois anticipés
- **FR40** : Une école partenaire peut consulter un reporting interne sur les profils reçus, les actions effectuées et les conversions de candidature

### F. Espaces Tiers (Parent & Conseiller B2B)

- **FR41** : Un parent lié peut consulter les métiers explorés et les parcours sauvegardés de l'élève (sans accès aux bulletins détaillés ni aux appréciations enseignants)
- **FR42** : Un parent peut souscrire et payer un abonnement premium au bénéfice du compte élève lié
- **FR43** : Un conseiller d'orientation peut consulter un dashboard cohorte (élèves de son établissement) avec taux de complétion, métiers les plus explorés, distribution par filière
- **FR44** : Un conseiller d'orientation peut consulter le profil individuel d'un élève uniquement après consentement explicite de l'élève
- **FR45** : Un conseiller d'orientation peut exporter un reporting anonymisé de cohorte (CSV ou PDF) pour usage interne établissement

### G. Découverte & Engagement

- **FR46** : Le système peut exposer des pages publiques indexables par les moteurs de recherche pour chaque métier, formation et école référencés (SEO)
- **FR47** : Le système peut envoyer des notifications par email à un élève lors d'événements clés (réponse école, nouvelle école référencée, échéance Parcoursup, rappel de complétion)

### H. Administration & Modération

- **FR48** : Un admin Path-Advisor peut créer, modifier et supprimer des fiches du référentiel professions / formations / écoles
- **FR49** : Un admin Path-Advisor peut consulter et traiter les signalements d'élèves (erreur métier, école obsolète, contenu inapproprié)
- **FR50** : Un admin Path-Advisor peut modérer les motivations libres rédigées par les élèves dans le cadre des envois anticipés (a priori avant transmission)
- **FR51** : Un admin Path-Advisor peut versionner un modèle de recommandation IA et tracer le dataset d'entraînement associé
- **FR52** : Le système peut produire des métriques d'audit ML (distribution scores par sous-population, drift des prédictions) consultables par un admin

### Fast-Follow (post-MVP immédiat mois 9-12)

- **FR-FF1** : Le système peut détecter des "profils à risque" (faible engagement, profil incohérent, signes de décrochage) et les remonter dans le dashboard conseiller
- **FR-FF2** : Le système peut envoyer des notifications push web (en plus de l'email) aux élèves et parents
- **FR-FF3** : Un admin peut consulter un tableau de bord de qualité du référentiel (couverture, fraîcheur, signalements en attente)
- **FR-FF4** : Le système peut proposer un module RDV visio intégré entre élève et école partenaire
- **FR-FF5** : Le système peut proposer un mécanisme de parrainage / partage permettant à un utilisateur d'inviter un pair via un lien traçable

## NonFunctional Requirements

### Performance

- **NFR-P1** : Recommandation vocationnelle complète servie en < 3 s P95 MVP, < 1,5 s P95 growth
- **NFR-P2** : Graphe de parcours avec stats personnalisées affiché en < 2 s P95
- **NFR-P3** : Page publique métier/formation TTFB < 1 s, LCP mobile < 2,5 s
- **NFR-P4** : OCR d'un bulletin standard aboutit en < 30 s P95
- **NFR-P5** : MAJ statistique d'admission post-réponse école propagée à l'élève (push + email) en < 5 min
- **NFR-P6** : Authentification utilisateur aboutit en < 1 s P95

### Security

- **NFR-S1** : Toutes données personnelles chiffrées AES-256 au repos + TLS 1.3 en transit
- **NFR-S2** : MFA obligatoire conseiller/école/admin, optionnelle B2C
- **NFR-S3** : Bulletins PDF stockés bucket S3-compatible chiffré région UE
- **NFR-S4** : Journal d'audit immuable de tout accès aux données personnelles, conservé 3 ans
- **NFR-S5** : Secrets applicatifs dans coffre dédié (Vault / Secrets Manager / self-hosted PoC)
- **NFR-S6** : Délais légaux RGPD respectés (incident CNIL < 72 h, accès/suppression < 30 j)
- **NFR-S7** : DPIA documentée et à jour avant déploiement production
- **NFR-S8** : Prévention attaques OWASP Top 10, audit interne MVP + pen-test annuel externe growth
- **NFR-S9** : Consentement parental email vérifié avant création compte < 15 ans, tracé avec horodatage immuable

### Scalability

- **NFR-SC1** : 500 MAU MVP, 10 000 MAU growth sans refonte majeure
- **NFR-SC2** : 500 utilisateurs concurrents lors des pics saisonniers sans dégradation
- **NFR-SC3** : Auto-scaling x3 capacité en < 10 min sur déclencheur charge
- **NFR-SC4** : Moteur de recommandation déployable indépendamment du back applicatif
- **NFR-SC5** : Référentiel 50 → 500 entrées sans dégradation latence
- **NFR-SC6** : BDD supporte minimum 100 000 profils élèves

### Reliability

- **NFR-R1** : Disponibilité ≥ 99 % MVP (downtime ≤ 7 h/mois), ≥ 99,5 % growth
- **NFR-R2** : Sauvegarde quotidienne données prod, rétention 30 jours, testée mensuellement par restauration partielle
- **NFR-R3** : RTO < 4 h, RPO < 1 h
- **NFR-R4** : Dégradation gracieuse en cas de panne tiers (OCR → manuel, Stripe → file, email → retry async)
- **NFR-R5** : Observabilité production complète (logs centralisés, métriques, alerting), MTTR < 1 h incident critique

### Accessibility

- **NFR-A1** : Parcours utilisateurs critiques conformes RGAA 4.1 niveau AA dès MVP
- **NFR-A2** : Ensemble du produit RGAA 4.1 niveau AA en growth
- **NFR-A3** : Interface pleinement utilisable au clavier seul
- **NFR-A4** : Contrastes texte/fond ≥ 4,5:1 normal, ≥ 3:1 large
- **NFR-A5** : Graphes de parcours fournissent alternative textuelle structurée (tableau, liste séquentielle)
- **NFR-A6** : Produit utilisable sur écrans mobiles dès 320 px de largeur

### Integration

- **NFR-I1** : Intégration Stripe supporte mode test local (sandbox) en PoC et production en cloud
- **NFR-I2** : Email transactionnel substituable par Mailpit local en PoC sans modification code applicatif (abstraction)
- **NFR-I3** : OCR substituable par Tesseract local en PoC avec dégradation acceptable
- **NFR-I4** : Analytique produit hébergement EU ou self-hosted (PostHog)
- **NFR-I5** : Système expose données ouvertes anonymisées (référentiel formations, tendances) sous licence Etalab en growth
- **NFR-I6** : Intégration ENT/Pronote en growth opt-in côté établissement et opt-in côté élève (double consentement RGPD)
- **NFR-I7** : Système consomme datasets open data Parcoursup (CSV annuel MENJS) pour stats d'admission

### Maintainability

- **NFR-M1** : Stack complète lance localement par `docker-compose up` en < 5 min, avec données seed pour produit utilisable end-to-end
- **NFR-M2** : Couverture tests automatisés ≥ 70 % sur zones critiques (auth, RBAC, moteur reco, paiement, RGPD)
- **NFR-M3** : Modifications modèle de recommandation IA versionnées avec dataset, hyperparamètres et métriques d'évaluation tracés
- **NFR-M4** : Architecture documentée via Architecture Decision Records (ADR) versionnés en git
- **NFR-M5** : Système maintenable et opérable par 1-2 personnes — toute opération critique (déploiement, restauration, modération) documentée sous forme de runbook

## Additional Requirements

Requirements techniques transverses issus de l'Architecture Decision Document et impactant la décomposition en épics :

- **ADD-1 — Hébergement UE obligatoire** : France ou UE strict (Scaleway / OVH / AWS Paris/Frankfurt), cible SecNumCloud en growth pour B2B EN
- **ADD-2 — PoC local-first via Docker Compose** : toute la stack (front, back, IA, DB, cache, queue, OCR, mail, monitoring, analytics, stockage) lance en local < 5 min avec seeds — interfaces abstraites (Hexagonal / Ports & Adapters) pour permettre PoC local et prod cloud avec mêmes contrats
- **ADD-3 — Multi-tenant hybride dès MVP** : Row-Level Security PostgreSQL, colonnes `tenant_id` (établissement) + `user_id` (élève) sur toutes les tables sensibles, tests d'isolation cross-tenant en CI obligatoires
- **ADD-4 — Service IA séparé** : Python (FastAPI ou équivalent), scaling horizontal indépendant du back applicatif, versioning des modèles avec dataset + hyperparamètres + métriques tracés
- **ADD-5 — Architecture monolithique modulaire** : pas de microservices prématurés. Stack figée : **Django 5 + DRF + drf-spectacular (Python 3.12+)** pour le back principal + **FastAPI** pour le service IA séparé (scaling indépendant)
- **ADD-6 — Stack frontend imposée** : SPA + SSR hybride (Next.js ou Nuxt) pour combiner SEO B2C et interactivité, PWA installable comme fallback app mobile
- **ADD-7 — Stockage de données** : PostgreSQL transactionnel + pgvector pour embeddings ; S3-compatible chiffré région UE pour bulletins ; Redis pour cache + sessions + rate limiting + recos pré-calculées ; job queue **Celery + Redis** (Python-native) pour OCR async, notifications, envoi anticipé, recalculs stats
- **ADD-8 — Pas de WebSocket MVP** : polling léger (30 s sur pages critiques) + notifications push standard suffisent — simplifie infra et coûts
- **ADD-9 — Audit trail immuable** : table dédiée append-only access-write, conservation 3 ans, export régulier
- **ADD-10 — Versioning modèles IA** : chaque déploiement de modèle versionné avec dataset + hyperparamètres + métriques d'éval, audit trail des décisions, monitoring drift en production
- **ADD-11 — Internationalisation francophone dès jour 1** : clés de traduction structurées (i18n), pas de strings hardcodés, préparation Belgique/Maroc en growth

## UX Design Requirements

Requirements actionnables issus de la spécification UX, organisés par catégorie d'implémentation. Chaque UX-DR est spec'd pour générer une story avec acceptance criteria testables.

### Design Tokens & Foundation

- **UX-DR1 — Design tokens couleur (mode clair MVP uniquement)** : palette R1 Vermillon sobre + blanc cassé, 17 tokens nommés (`color-brand`, `color-bg`, `color-text`, `color-semantic-audacieux/realiste/sur`, `color-success/warning/danger`…), contrastes vérifiés AA+ sur tous couples, à porter dans `tokens.css` + `tailwind.config.ts`
- **UX-DR2 — Typography system Inter** : variable font weights 400-700, type scale 8 tokens (display-1 48-56 px à text-caption 12 px), body 16 px minimum, line-height 1.5 body / 1.2 display, max 2 poids par écran
- **UX-DR3 — Spacing system Tailwind 4 px** : 8 tokens (space-1 4 px à space-16 64 px), densité cible entre Doctolib et Revolut, grille 4 colonnes mobile / 8 desktop, container max 1200 px
- **UX-DR4 — Motion tokens** : 4 tokens (motion-instant 100 ms, motion-quick 200 ms, motion-standard 300 ms, motion-narrative 720-800 ms réservé `GraphParcours` uniquement), fallback `prefers-reduced-motion` partout

### Composants Path-Advisor (Couche 3 du design system)

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

### Patterns UX transverses

- **UX-DR23 — Pattern "Phrase recopiable"** : sous tout score, phrase défendable italic + brand accent + bouton copy tap (composant atomique réutilisé partout)
- **UX-DR24 — Pattern "Stat with context"** : tout chiffre accompagné de cadrage qualitatif + contexte + levier action — jamais un nombre nu (cf `CarteAdmission`)
- **UX-DR25 — Pattern "Mode normal = mode dégradé"** : même structure visuelle quel que soit le profil ; les contenus internes se densifient sans changer la grille (zéro marqueur visuel d'incomplet pour Léa)
- **UX-DR26 — Pattern "Consentement granulaire"** : aucun tiers n'accède aux données sans consentement explicite révocable 1-tap
- **UX-DR27 — Pattern "Anti-cirque"** : aucune animation ne se rejoue sur ouverture répétée du même contenu
- **UX-DR28 — Pattern "Calendrier sans urgence"** : notifications calées sur calendrier Parcoursup, jamais "DERNIÈRE CHANCE" ni urgence fabriquée
- **UX-DR29 — Pattern "Retour avec delta"** : toute session J+N s'ouvre sur "ce qui a bougé", pas sur écran neutre
- **UX-DR30 — Onboarding différencié par niveau scolaire** : 4 chemins (3ème / lycée général / lycée pro / sans bulletins) qui partagent la même structure, branching après step 2

### Responsive & Accessibility

- **UX-DR31 — Navigation responsive** : bottom tab bar mobile 5 onglets max (Accueil / Métiers / Mes paris / Notifications / Profil) ; side nav fixed 224 px desktop ; pas de hamburger menu mobile
- **UX-DR32 — Search & filtering pattern Doctolib** : `Command` shadcn + filtres pills multi-select + sort dropdown + faceted search side panel desktop / `Sheet` bottom mobile
- **UX-DR33 — RGAA AA compliance** : axe-core en CI dès sprint 4, audit trimestriel manuel VoiceOver iOS + NVDA Windows sur 3 parcours critiques, test daltonisme mensuel, focus visible 2 px outline `color-brand`, skip links visibles au focus
- **UX-DR34 — Performance budget mobile** : TTI < 4 s sur 4G, LCP mobile < 2,5 s, < 200 ko JS critique par écran, body 16 px minimum partout, touch targets 44 × 44 px minimum, code-splitting agressif + lazy load `GraphParcours`
- **UX-DR35 — Test inclusif "téléphone fissuré"** : test mensuel scénario Sarah complet sur Android d'occasion fissuré (≤ 80 €) pour valider device cible plancher réel (animations, OCR appareil photo médiocre, touch targets)

## FR Coverage Map

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
