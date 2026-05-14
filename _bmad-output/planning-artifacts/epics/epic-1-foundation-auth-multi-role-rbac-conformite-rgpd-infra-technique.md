# Epic 1 : Foundation — Auth multi-rôle, RBAC, Conformité RGPD & Infra technique

Permettre à tout utilisateur (élève / parent / conseiller / école / admin) de créer un compte sécurisé conforme RGPD avec accès isolés par rôle, et poser les fondations techniques du produit (Docker Compose local-first, hébergement UE, tokens design system).

## Story 1.1 : Initialisation du projet (Next.js + Django + FastAPI + Docker)

As a développeur Path-Advisor,
I want initialiser le mono-repo avec Next.js 15 (front) + Django 5 / DRF (back) + FastAPI (service IA séparé) + Docker Compose,
So that toute la stack tourne localement en `docker-compose up < 5 min` et l'équipe peut démarrer le développement sur des fondations propres (ADD-5 stack figée).

**Acceptance Criteria :**

**Given** un repo Git vide
**When** je lance la commande d'initialisation projet
**Then** le mono-repo contient 3 apps Python/TS dans `apps/`:
- `apps/web` : Next.js 15 + TypeScript + Tailwind v4 + shadcn/ui (front uniquement, SSR + RSC)
- `apps/api` : Django 5 + DRF + drf-spectacular (back principal, Python 3.12+, géré via `uv`)
- `apps/ai-service` : FastAPI + Pydantic v2 + scikit-learn (service IA séparé, scaling indépendant)
**And** linting actif : ESLint + Prettier (TS) / Ruff + Black + mypy (Python) + pre-commit hooks via Lefthook
**And** tests minimal : Vitest (TS), pytest-django + factory_boy (Django), pytest + hypothesis (AI)
**And** CI minimale (GitHub Actions) : lint + tests + build front + génération OpenAPI Django → client TS

**Given** la stack complète déclarée dans `docker-compose.yml`
**When** je lance `docker-compose up`
**Then** tous les services démarrent en < 5 minutes (NFR-M1) : Next.js (port 3000) + Django (port 8000) + FastAPI AI (port 8001) + PostgreSQL + Redis + Mailpit + MinIO + Tesseract OCR + PostHog
**And** Next.js est accessible sur `http://localhost:3000` avec une page d'accueil "Hello Path-Advisor"
**And** Django Admin est accessible sur `http://localhost:8000/admin` (auth super-user de seed)
**And** OpenAPI schema Django est généré automatiquement et consommé par Next.js (TS types auto via `openapi-typescript`)
**And** données de seed injectées automatiquement (1 user admin de test)

**Given** Tailwind v4 et shadcn/ui sont opérationnels
**When** je consulte `apps/web`
**Then** `tailwind.config.ts` est prêt à recevoir les tokens (Story 1.2)
**And** shadcn/ui CLI est installé et au moins 5 composants prioritaires copiés (Button, Card, Dialog, Form, Input)

**Given** la configuration multi-environnement (local / staging / production)
**When** je consulte la documentation README
**Then** un ADR #001 documente le choix Django + Next.js + FastAPI + Docker (stack architecture.md figée)
**And** un runbook explique le setup pas-à-pas pour un nouveau dev

## Story 1.2 : Définition et publication du design system de tokens

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

## Story 1.3 : Inscription élève ≥ 15 ans avec consentement RGPD direct

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

## Story 1.4 : Inscription élève < 15 ans avec consentement parental email opt-in

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

## Story 1.5 : Connexion utilisateur avec email/mot de passe

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

## Story 1.6 : MFA obligatoire pour les rôles staff (conseiller, école, admin)

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

## Story 1.7 : Matrice RBAC et middleware d'autorisation

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

## Story 1.8 : Multi-tenant Row-Level Security PostgreSQL + tests d'isolation CI

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

## Story 1.9 : Liste des tiers ayant accès au profil élève

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

## Story 1.10 : Révocation d'un accès tiers

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

## Story 1.11 : Export portabilité RGPD — toutes mes données personnelles

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

## Story 1.12 : Suppression complète du compte (droit à l'oubli RGPD)

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

## Story 1.13 : Journal d'audit immuable des accès aux données personnelles

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

## Story 1.14 : Composant `ConsentDialog` réutilisable

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
