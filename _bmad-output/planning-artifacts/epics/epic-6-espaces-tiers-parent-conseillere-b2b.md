# Epic 6 : Espaces Tiers — Parent & Conseillère B2B

Permettre aux parents (M. Martin) de voir les métiers explorés + payer le premium ; aux conseillères B2B (Mme Dupont, 5 pilotes MVP) d'utiliser le dashboard cohorte pour préparer leurs entretiens.

## Story 6.1 : Invitation parent par l'élève → création compte parent lié

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

## Story 6.2 : Vue parent — métiers explorés, parcours sauvegardés et coûts

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

## Story 6.3 : Frontières confidentialité parent (bulletins + appréciations masqués)

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

## Story 6.4 : Paiement premium par parent au bénéfice élève

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

## Story 6.5 : Onboarding établissement B2B + création cohorte

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

## Story 6.6 : Dashboard cohorte conseillère B2B

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

## Story 6.7 : Consentement élève → conseillère pour vue profil individuel

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

## Story 6.8 : Vue profil individuel élève côté conseillère

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

## Story 6.9 : Export reporting anonymisé cohorte (CSV / PDF)

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

## Story 6.10 : Composant `CohortDashboard` (desktop dense Linear-like)

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

## Story 6.11 : Composant `PermissionList` étendu (révocation 1-tap + audit visible)

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
