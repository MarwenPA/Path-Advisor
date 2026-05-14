# Epic 2 : Profil Élève & Onboarding

Permettre à l'élève (Sarah Terminale, Mehdi 3ème, Léa sans bulletins) de compléter son profil en < 12 min (passions + bulletins OCR ou saisie manuelle) avec un onboarding différencié par niveau scolaire et un mode dégradé invisible.

## Story 2.1 : Onboarding step 1 — Déclaration passions, intérêts et valeurs

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

## Story 2.2 : Onboarding step 2 — Niveau scolaire, filière et spécialités

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

## Story 2.3 : Import bulletins PDF avec OCR async (chemin principal)

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

## Story 2.4 : Saisie manuelle assistée des notes (chemin fallback)

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

## Story 2.5 : Mode dégradé invisible — "Plus tard" sur les bulletins

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

## Story 2.6 : Mise à jour profil à tout moment

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

## Story 2.7 : Score de complétude profil + identification des éléments manquants

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

## Story 2.8 : Composant `ScenarioLoader` réutilisable

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

## Story 2.9 : Composant `GracefulFallback` réutilisable

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
