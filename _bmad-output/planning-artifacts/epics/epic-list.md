# Epic List

## Epic 1 : Foundation — Auth multi-rôle, RBAC, Conformité RGPD & Infra technique

Permettre à tout utilisateur (élève / parent / conseiller / école / admin) de créer un compte sécurisé conforme RGPD avec accès isolés par rôle, et poser les fondations techniques du produit (Docker Compose, hébergement UE, tokens design system).

**FRs couverts** : FR1, FR2, FR3, FR4, FR5, FR6, FR7, FR8, FR9, FR10, FR11, FR12
**NFRs principaux** : NFR-S1 à NFR-S9 (sécurité), NFR-R1 à NFR-R5 (reliability), NFR-M1, NFR-M4, NFR-M5
**Additional Requirements** : ADD-1 hébergement UE, ADD-2 PoC local-first Docker, ADD-3 multi-tenant RLS, ADD-5 monolithe modulaire, ADD-6 Next.js SSR, ADD-7 PostgreSQL/Redis/S3, ADD-9 audit trail immuable, ADD-11 i18n jour 1
**UX-DRs** : UX-DR1 (tokens couleur R1), UX-DR2 (typo Inter), UX-DR3 (spacing), UX-DR4 (motion tokens), UX-DR11 (`ConsentDialog`), UX-DR16 (`PermissionList`), UX-DR31 (navigation responsive), UX-DR33 (RGAA AA setup), UX-DR34 (perf budget)

## Epic 2 : Profil Élève & Onboarding

Permettre à l'élève (Sarah Terminale, Mehdi 3ème, Léa sans bulletins) de compléter son profil en < 12 min (passions + bulletins OCR ou saisie manuelle) avec un onboarding différencié par niveau scolaire et un mode dégradé invisible.

**FRs couverts** : FR13, FR14, FR15, FR16, FR17, FR18, FR19
**NFRs principaux** : NFR-P4 (OCR < 30 s), NFR-A1 RGAA AA parcours critique, NFR-I3 OCR Tesseract local
**Additional Requirements** : ADD-7 stockage S3 chiffré bulletins, ADD-2 OCR local fallback
**UX-DRs** : UX-DR12 `ScenarioLoader` (OCR async narratif), UX-DR13 `GracefulFallback` (OCR rate → saisie manuelle), UX-DR25 Pattern mode normal = mode dégradé, UX-DR30 Onboarding différencié niveau scolaire, UX-DR35 Form pattern (labels above, validation on blur)

## Epic 3 : Recommandation Vocationnelle (Premier Aha)

Servir le PREMIER moment "aha" : l'élève reçoit 8 métiers scorés avec phrase recopiable défendable et explicabilité des signaux contributifs (RGPD art. 22).

**FRs couverts** : FR20, FR21, FR22, FR23, FR24, FR25, FR26
**NFRs principaux** : NFR-P1 reco < 3 s P95 MVP, NFR-SC4 service IA scaling indépendant, NFR-SC5 référentiel 50 → 500, NFR-M3 versioning modèles
**Additional Requirements** : ADD-4 service IA séparé Python/FastAPI, ADD-10 versioning modèles IA
**UX-DRs** : UX-DR5 `ScoreVocationnel`, UX-DR9 `FicheMetier`, UX-DR23 Pattern phrase recopiable

## Epic 4 : Graphe de Parcours & Stats d'Admission (Deuxième Aha)

Servir le DEUXIÈME moment "aha" et le différenciateur produit central : l'élève voit son graphe-récit interactif avec ses chances réelles d'admission par école, animation séquentielle 720-800 ms, alternative tabulaire RGAA AA.

**FRs couverts** : FR27, FR28, FR29, FR30, FR31, FR32
**NFRs principaux** : NFR-P2 graphe < 2 s P95, NFR-A5 alternative tabulaire graphe, NFR-I7 datasets open data Parcoursup
**Additional Requirements** : ADD-4 service IA pour stats, ADD-7 pgvector pour embeddings
**UX-DRs** : UX-DR6 `GraphParcours` (LE composant), UX-DR7 `FicheEcole`, UX-DR8 `CarteAdmission`, UX-DR19 `ParcoursCard`, UX-DR20 `StatPersonnelle`, UX-DR24 Test 3 mots Caravaggio, UX-DR32 Search & filtering Doctolib

## Epic 5 : Premium B2C & Envoi Anticipé Biface

Permettre à l'élève premium (10,99 €/mois via Stripe ou parent) d'envoyer son profil aux écoles partenaires, l'école répond en 3 actions, la stat d'admission se met à jour en < 5 min. Différenciateur premium clé.

**FRs couverts** : FR33, FR34, FR35, FR36, FR37, FR38, FR39, FR40 (+ FR5 auth école rappel)
**NFRs principaux** : NFR-P5 propagation stat < 5 min, NFR-I1 Stripe sandbox + prod, NFR-S2 MFA école obligatoire
**Additional Requirements** : ADD-8 polling + push (pas WebSocket MVP)
**UX-DRs** : UX-DR15 `PaywallContextuel`, UX-DR22 `EcoleResponseFlow`

## Epic 6 : Espaces Tiers — Parent & Conseillère B2B

Permettre aux parents (M. Martin) de voir les métiers explorés + payer le premium, et aux conseillères B2B (Mme Dupont, 5 pilotes MVP) d'utiliser le dashboard cohorte pour préparer leurs entretiens.

**FRs couverts** : FR41, FR42, FR43, FR44, FR45 (+ FR3 compte parent lié, FR4 auth conseillère rappel)
**NFRs principaux** : NFR-S4 audit accès tiers, NFR-A2 RGAA AA growth (B2B EN)
**Additional Requirements** : ADD-3 multi-tenant RLS (cohorte établissement)
**UX-DRs** : UX-DR21 `CohortDashboard` (Linear-like dense desktop), UX-DR16 `PermissionList`

## Epic 7 : Découverte Publique & SEO

Permettre l'acquisition organique : Sarah trouve Path-Advisor via Google sur une recherche "que faire après le bac" ou "devenir ingénieur biomédical" et arrive sur une page métier indexable, performante, conforme Core Web Vitals.

**FRs couverts** : FR46
**NFRs principaux** : NFR-P3 TTFB < 1 s + LCP mobile < 2,5 s
**Additional Requirements** : ADD-6 Next.js SSR pour SEO, ADD-11 i18n préparé francophonie
**UX-DRs** : UX-DR1/2 tokens publics réutilisés, UX-DR34 Perf budget mobile

## Epic 8 : Continuité Temporelle & Notifications

Servir le moat différenciant vs LLMs grand public : l'utilisateur revient à J+30 et voit "ce qui a bougé" (réponse école, nouvelles formations, calendrier Parcoursup) via un écran `DeltaRecap` style Spotify Wrapped léger et des notifications email calées sans urgence fabriquée.

**FRs couverts** : FR47
**NFRs principaux** : NFR-I2 email Mailpit local + Postmark prod, NFR-R4 dégradation gracieuse email
**UX-DRs** : UX-DR14 `DeltaRecap`, UX-DR17 `CalendarNotification`, UX-DR29 Pattern retour avec delta, UX-DR28 Pattern calendrier sans urgence

## Epic 9 : Back-office Administration & Modération

Permettre à Karim (admin Path-Advisor) de maintenir le référentiel professions/formations/écoles, traiter les signalements sous 7 jours, modérer les motivations libres a priori, versionner les modèles IA avec dataset, et auditer le drift ML.

**FRs couverts** : FR48, FR49, FR50, FR51, FR52 (+ FR6 auth admin rappel)
**NFRs principaux** : NFR-M3 versioning modèles IA, NFR-S4 audit accès admin
**Additional Requirements** : ADD-10 versioning modèles IA + audit trail
**UX-DRs** : (back-office utilisant principalement shadcn primitives + tokens, peu de composants Couche 3 dédiés)

## Epic 10 : Fast-Follow (5 features post-MVP immédiat)

Polish post-MVP (mois 9-12) : détection profils à risque dashboard conseillère, push web (en plus email), tableau qualité référentiel admin, RDV visio intégré école-élève, parrainage / partage lien traçable.

**FRs couverts** : FR-FF1, FR-FF2, FR-FF3, FR-FF4, FR-FF5
**NFRs principaux** : (héritage MVP)
**UX-DRs** : UX-DR18 `SideFlow` (peut servir au consentement parental en attente)

---

**Total : 10 épics, 100 % de couverture FRs, ordre d'implémentation suivant le chemin critique vers les 2 moments aha (Epic 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10).**

---
