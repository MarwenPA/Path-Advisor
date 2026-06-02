# Story 2.1: Onboarding step 1 — Déclaration passions, intérêts et valeurs

**Epic:** 2 — Profil Élève & Onboarding
**Status:** in-progress
**Sprint:** 4 (Onboarding & Profil)
**Story Key:** `2-1-onboarding-passions-interets-valeurs`
**Estimation:** M (medium) — 3 sous-écrans front-end + endpoint POST/PATCH profil + persistence inter-step + adaptation copy par niveau scolaire. Pas de modèle IA, pas de batch, pas de migration lourde. Sized ~1.5–2 j focused work.

> Premier écran post-inscription. Sarah (Terminale), Mehdi (3ème) et Léa (sans bulletins) arrivent ici avec un **état émotionnel d'entrée fragile** : doute, fatigue, parfois honte ("je sais pas ce qui me plaît"). Le job de cet écran n'est pas de "collecter des passions" — c'est de **transformer un blanc anxiogène en énumération qu'on peut faire au feeling, sans se sentir testé**. Trois sous-étapes courtes (passions → valeurs → centres d'intérêt) plutôt qu'un grand questionnaire psy. Vocabulaire qui s'adapte au niveau scolaire (UX-DR30). Persistence automatique : on peut fermer l'app à tout moment, on revient pile où on s'est arrêté.

---

## 1. User Story

**As an** élève (Sarah Terminale / Mehdi 3ème / Léa sans bulletins),
**I want** déclarer mes passions, mes valeurs personnelles et mes centres d'intérêt dans un mini-questionnaire de 3 écrans courts, à mon rythme, dans un vocabulaire qui me parle,
**So that** le moteur de recommandation vocationnelle (Epic 3) ait des signaux déclaratifs propres à croiser avec mes bulletins (Epic 2 step 3), et **so that** je sorte de cet onboarding avec le sentiment d'avoir été *entendue*, pas *testée*.

**Business value :** sans signaux déclaratifs, le moteur de scoring (FR13) n'a que les notes — il produit des recos plausibles statistiquement mais sans propriété narrative. Avec passions + valeurs + intérêts, chaque reco peut produire la **phrase recopiable** (principe expérience #1) : *"Avec ton goût pour la justice sociale et tes maths, le droit fiscal est un objectif réaliste."* Cet écran est aussi le **premier contact réel avec le ton produit** post-inscription : si on rate la dignité ici (jargon, condescendance, gamification de complétion), on a perdu Mehdi et Léa pour toujours.

**Garde-fous personas activés sur cet écran :**

- **Mehdi (3ème, anti-stigma)** — aucun jargon scolaire ("disciplines", "matières"), vocabulaire ado direct ("ce qui te branche", "trucs qui te font kiffer") MAIS jamais condescendant ni "djeun's de pub". Validation lexicale en sprint review.
- **Léa (sans bulletins, dignité)** — aucun champ obligatoire à plus que 3 entrées ; pas de message "Tu y es presque !" ni "Profil à X %". Si Léa survole et clique "Suivant" avec le minimum, l'écran suivant l'accueille sans culpabilisation.
- **Sarah (Protagoniste, mobile soir 21-23h)** — chaque sous-étape doit être complétable au pouce en moins de 60 s en condition fatiguée. Pas de scroll long, pas de champ libre obligatoire.

---

## 2. Acceptance Criteria (BDD)

### AC1 — Route, layout, indicateur de progression discret

**Given** je viens de finir l'inscription (Stories 1.3 ou 1.4) et de cliquer "Continuer"
**When** je suis redirigé vers `/onboarding/step-1` (ou `/onboarding/profil/passions` — slug final tranché au sprint)
**Then** je vois un écran avec :

- En **header sticky** : back chevron (`<`) à gauche désactivé (pas de retour vers signup) + **indicateur de progression** centré au format `● ○ ○` (3 dots, taille 8 px, gap 4 px, dot actif `color-brand`, dots inactifs `color-border-strong`) + bouton text-tertiary "Plus tard" à droite (cf AC9)
- En **main** : titre h2 (`text-h2`) + sous-titre `text-body` `color-text-muted` + zone de sélection (chips ou liste selon sous-étape) + helper inline si applicable
- En **footer sticky mobile** : bouton primary "Continuer" (full-width mobile, right-aligned desktop, `lg` size) + état désactivé `text-caption` *"Sélectionne au moins 3 propositions"* sous le bouton tant que < 3 (cf AC2)

**And** le layout respecte les tokens : container `max-width: 600 px` sur desktop (form pattern, UX spec §Form Patterns), padding `space-4` mobile / `space-6` desktop, fond `color-bg`
**And** le focus initial à l'arrivée sur l'écran est sur le **premier chip** (touche-clavier ergo, NFR-A1), **pas** sur le bouton "Plus tard" (anti-skip accidentel)
**And** un **skip link** "Aller au contenu principal" est rendu en haut du DOM, visible au focus (RGAA NFR-A1)

### AC2 — Sous-étape 1A : Passions (chips multi-select avec recherche)

**Given** je suis sur l'écran 1/3 sous-étape "Passions"
**When** je consulte la zone de sélection
**Then** je vois :

- Un titre `text-h2` : *"Qu'est-ce qui te plaît, vraiment ?"* (Sarah/Léa) — variante Mehdi (3ème, AC8) : *"Ce qui te branche, en vrai"*
- Un sous-titre `text-body` `color-text-muted` : *"Choisis-en au moins 3. T'inquiète, tu pourras changer."*
- Un **champ de recherche** (composant `Input` shadcn) au-dessus de la grille, avec placeholder *"Cherche par mot-clé (ex. cinéma, sport, code…)"*, icône loupe Lucide à gauche, croix de clear à droite quand non vide
- Une **grille de ~20 chips de catégories pré-définies** (références ci-dessous), affichées en flex-wrap, gap `space-2`, taille `sm` (32 px hauteur) ; chaque chip = composant `Toggle` shadcn customisé (label texte + check icon Lucide 16 px qui apparaît à l'état sélectionné)
- Sous la grille : un **bouton tertiary** `+ Ajouter une passion à toi` qui ouvre un mini-champ inline (chip pill éditable) — max 5 chips libres, validation côté front (max 30 caractères, pas de caractères spéciaux > Unicode L/N)
- En bas de la zone : un **compteur discret** `text-caption` `color-text-subtle` aligné à droite : `3 / 3 minimum atteint` (passe en `color-success` quand atteint), ou `2 / 3 minimum` avant le seuil

**And** les 20 catégories MVP sont (à valider sprint review avec Mehdi/Léa proxies) :

```
Sciences & nature · Tech & code · Arts & création · Sport & corps · Aider les autres · Musique · Cinéma & séries · Lecture & écriture · Voyage & cultures · Cuisine · Mode & style · Business & argent · Jeux vidéo · Animaux · Éducation & transmission · Santé & soin · Politique & société · Bricolage & mains · Communication & média · Spiritualité & sens
```

**And** la **recherche filtre la grille en temps réel** (debounce 150 ms), match case-insensitive sur le label + un alias caché (ex. "code" matche "Tech & code", "ciné" matche "Cinéma & séries"). Pas de résultat trouvé → message inline `text-body-sm` `color-text-muted` *"Pas dans la liste ? Ajoute-le toi-même via + Ajouter."*
**And** un chip déjà sélectionné affiche un **check** Lucide à gauche du label, fond `color-brand` `text-bg`, et reste cliquable pour désélectionner
**And** le bouton "Continuer" reste **désactivé** (state `disabled` cf UX spec §Button Hierarchy : 60 % opacity, `cursor-not-allowed`, **pas grisé au point d'être invisible**) tant que `selectedCount < 3`
**And** dès que `selectedCount >= 3`, le bouton "Continuer" passe en `enabled` avec micro-animation `motion-instant` (100 ms fade-in du caption "Tu peux continuer quand tu veux" sous le bouton, qui remplace le helper "Sélectionne au moins 3 propositions")

**And** la limite maximum est **8 chips totaux** (catégories + custom confondues) — au-delà, les chips non-sélectionnés deviennent visuellement "atténués" (60 % opacity, `aria-disabled="true"`) + helper inline `text-caption` `color-warning` *"Maximum 8 — désélectionne pour en changer."* Limite choisie pour éviter la dispersion vocationnelle (qualité signal > quantité).

### AC3 — Sous-étape 1B : Valeurs (radio list curée 3-5)

**Given** je suis passé(e) sur l'écran 2/3 sous-étape "Valeurs"
**When** je consulte la zone de sélection
**Then** l'indicateur de progression header passe à `● ● ○`, **avec animation `motion-quick` (200 ms) sur le dot 2 qui transitionne de inactif à actif** (pas d'autre animation, anti-cirque)
**And** je vois :

- Titre `text-h2` : *"Ce qui compte le plus pour toi"* (Sarah/Léa) — variante Mehdi : *"Ce qui te tient à cœur"*
- Sous-titre `text-body` `color-text-muted` : *"Choisis 3 à 5 valeurs. Y'a pas de bonne réponse."*
- Une **liste verticale de ~12 valeurs**, format **card cliquable** (taille `lg`, touch target 56 px hauteur minimum, fond `color-bg-2`, border `color-border`, radius `--radius-md`), chacune avec :
  - Label `text-body` weight 500 (ex. *Justice sociale*)
  - Description courte `text-body-sm` `color-text-muted` (ex. *Que les choses soient justes pour tout le monde*)
  - Icône check Lucide 20 px à droite, visible uniquement à l'état sélectionné

**And** les 12 valeurs MVP sont (curation curée, à itérer avec Mehdi/Léa proxies) :

```
Justice sociale      — Que les choses soient justes pour tout le monde
Indépendance         — Pouvoir bosser à ton rythme, à ta façon
Sécurité             — Un cadre stable, prévisible
Créativité           — Inventer, créer, faire des trucs nouveaux
Défi                 — Te dépasser, viser haut
Contact humain       — Bosser avec les gens, pour les gens
Reconnaissance       — Que ton boulot soit vu et respecté
Argent & confort     — Bien gagner ta vie, sans culpabiliser
Apprendre           — Comprendre, te former toute ta vie
Nature & vivant      — Travailler avec / pour le vivant
Aventure             — Bouger, découvrir, voir du pays
Sens & utilité       — Faire quelque chose qui sert vraiment
```

**And** la sélection est **3 à 5** : tant que < 3, bouton "Continuer" désactivé avec helper *"Choisis-en au moins 3"* ; à partir de 5, les valeurs non-sélectionnées passent atténuées (60 % opacity) avec helper *"Maximum 5 — désélectionne pour en changer."*
**And** la liste est **scrollable en single column** (mobile et desktop), aucun layout 2-colonnes (lisibilité + accessibilité)

### AC4 — Sous-étape 1C : Centres d'intérêt (champs libres + suggestions)

**Given** je suis passé(e) sur l'écran 3/3 sous-étape "Centres d'intérêt"
**When** je consulte la zone
**Then** l'indicateur passe à `● ● ●` (toujours `motion-quick` 200 ms sur le dot final)
**And** je vois :

- Titre `text-h2` : *"Ce que tu suis, écoutes, regardes"* (toutes personas)
- Sous-titre `text-body` `color-text-muted` : *"3 lignes max, format libre. Une chaîne YouTube, un podcast, un livre, une matière qui t'a marqué — ce que tu veux."*
- **3 champs `Textarea` shadcn** (1 ligne hauteur, growable jusqu'à 3 lignes), label au-dessus en `text-body-sm` weight 500 (RGAA), placeholder évocateur différencié :
  - Champ 1 : *"Ex. La chaîne YouTube de Marie Lopez sur la chimie, ou un podcast Choses à savoir…"*
  - Champ 2 : *"Ex. Le bouquin Sapiens, un film comme Hidden Figures, la série Mr Robot…"*
  - Champ 3 : *"Ex. La séquence sur la photosynthèse en 2nde, un débat en HGGSP, un TP de SVT…"*
- Une **rangée de chips de suggestion** sous chaque champ (taille `sm`, `Toggle` shadcn), 4-5 suggestions par champ, au tap → texte du chip injecté dans le champ correspondant (focus reste sur le champ après injection)

**And** les 3 champs sont **tous optionnels** — l'élève peut tout laisser vide. Bouton "Terminer" **toujours enabled** sur ce dernier écran (différent des deux précédents). Helper sous le bouton si tous les champs vides : `text-caption` *"Tu pourras compléter plus tard depuis ton profil."*
**And** longueur max par champ : **200 caractères** (validation côté front + back), compteur discret `text-caption` aligné à droite sous le champ (passe en `color-warning` à 180, en `color-danger` à 195)
**And** chaque champ a un `aria-label` explicite + `aria-describedby` pointant vers son placeholder/helper (RGAA)

### AC5 — Persistence inter-step (autosave après chaque sous-étape)

**Given** je suis sur n'importe quelle sous-étape 1A/1B/1C
**When** je clique "Continuer" (ou "Terminer" sur 1C)
**Then** un **PATCH** est envoyé vers `/api/v1/students/me/onboarding/passions` (ou route similaire — finalisée au sprint), avec le payload partiel pour la sous-étape concernée :

```json
{
  "step": "passions" | "valeurs" | "interets",
  "passions": ["sciences-nature", "cinema-series", "code-tech-libre:GraphQL"],
  "valeurs": ["justice-sociale", "creativite", "sens-utilite"],
  "interets": { "1": "...", "2": "...", "3": "" }
}
```

**And** la requête a un **timeout de 5 s** côté client ; si elle échoue (réseau, 5xx), l'app **garde l'état en localStorage** sous clé `onboarding_step1_draft` et l'utilisateur passe quand même à la sous-étape suivante (UX > sync stricte). Un **toast `info`** discret apparaît : *"Pas de réseau ? Pas grave, on enregistre quand tu reviens."* (durée 3 s, dismissible).
**And** la prochaine requête réussie depuis cet onglet **flush le draft localStorage**. Si l'élève revient sur l'écran (cf AC6) sans avoir flushé, le draft est rechargé en priorité sur la réponse serveur (last-write-wins côté client jusqu'au flush).
**And** entre `onMount` et le premier rendu, un appel **GET** `/api/v1/students/me/onboarding/passions` récupère l'état serveur précédent (s'il existe) et **pré-remplit la sélection**. Skeleton shadcn (`motion-quick`) pendant le fetch (< 500 ms cible).

### AC6 — Reprise après fermeture / changement d'écran

**Given** j'ai sélectionné 2 passions sur 1A (donc pas encore validé) puis j'ai fermé l'onglet
**When** je rouvre l'app et reviens sur `/onboarding/step-1`
**Then** mes 2 passions sont **toujours sélectionnées** (état pris du localStorage draft + serveur si présent)
**And** je suis sur la **dernière sous-étape atteinte** : si j'avais validé 1A et 1B mais quitté pendant 1C avec 1 champ rempli, je reviens en 1C avec ce champ pré-rempli et l'indicateur `● ● ●`
**And** **aucun message** "Reprise de l'onboarding" n'apparaît — la continuité est silencieuse (principe expérience #5 : *"chaque session commence où la précédente s'est arrêtée"*, sans cérémonie)
**And** si la session serveur a expiré (401 sur GET), l'utilisateur est redirigé vers `/login` avec un `?return_to=/onboarding/step-1` ; au retour, son draft localStorage est réappliqué

### AC7 — Bouton "Plus tard" (skip global sur cet écran)

**Given** je suis sur n'importe laquelle des sous-étapes
**When** je tape sur le **bouton text-tertiary "Plus tard"** dans le header droit
**Then** une **`ConsentDialog`** (composant Story 1.14) s'ouvre avec :

- Title : *"Tu veux remettre ça à plus tard ?"*
- Description : *"Pas de souci. Tu pourras déclarer tes passions, valeurs et centres d'intérêt à tout moment depuis ton profil. Tes recos seront un peu plus génériques pour l'instant, mais elles s'affineront dès que tu reviendras compléter."*
- `dataMentioned` : `["Tes passions et valeurs sont utilisées pour adapter tes recos métiers"]`
- `duration` : *"Tu peux compléter à tout moment depuis ton profil"*
- `beneficiary` : *"Toi — ce sont tes données, tu décides"*
- `acceptLabel` : *"Oui, plus tard"* (pas `isAcceptDestructive` — c'est un choix neutre, pas une suppression)
- `refuseLabel` : *"Je continue"*

**And** si l'élève confirme "Oui, plus tard" :

- Les sélections en cours sont **persistées telles quelles** côté serveur (le draft n'est pas perdu)
- L'élève est redirigé vers `/onboarding/step-2` (Story 2.2)
- Le `profile.onboarding_status` côté serveur passe à `step1_skipped` (sémantique distincte de `step1_completed` — important pour Story 2.7 Maturité de profil)

**And** si l'élève clique "Je continue", la dialog se ferme, focus revient sur le chip / champ où il était (focus management RGAA)

### AC8 — Adaptation copy par niveau scolaire (UX-DR30)

**Given** mon âge a été saisi à l'inscription (Story 1.3 ou 1.4)
**When** je charge l'écran 2.1
**Then** le **vocabulaire des titres, sous-titres, placeholders et chips** s'adapte selon mon niveau scolaire **présumé** (calculé à partir de la date de naissance, anonymement côté front via util `getPresumedLevel(birthDate, today)`) :

| Niveau présumé | Variante copy `passions` titre | Variante copy `interets` placeholder champ 3 |
|---|---|---|
| **Collège (< 15 ans, Mehdi)** | *"Ce qui te branche, en vrai"* | *"Ex. La leçon où tu t'es pas ennuyé(e), un débat en cours…"* |
| **Lycée (15-18 ans, Sarah/Léa)** | *"Qu'est-ce qui te plaît, vraiment ?"* | *"Ex. La séquence sur la photosynthèse en 2nde, un débat en HGGSP, un TP de SVT…"* |
| **Post-bac (18+, B2C élargi)** | *"Ce qui t'inspire en ce moment"* | *"Ex. Un cours marquant en L1, un projet de stage, une lecture pro…"* |

**And** la **liste des chips de passions et valeurs reste identique** entre niveaux (universalité du référentiel) — seul le copy enveloppant change
**And** la fonction `getPresumedLevel` est **side-effect-free, testable, isolée** dans `packages/copy/levelAdapter.ts` (ou équivalent selon structure du repo) avec test unitaire snapshot des 3 variantes
**And** le **fallback** si la date de naissance est manquante ou invalide est la variante **lycée** (la plus neutre statistiquement)

### AC9 — Accessibilité RGAA AA (touch, keyboard, screen reader, reduced motion)

**Given** l'écran 2.1 et ses 3 sous-étapes
**When** je teste avec clavier seul, lecteur d'écran, et `prefers-reduced-motion: reduce`
**Then** **tout est navigable au clavier** :

- `Tab` traverse dans l'ordre : skip link → back chevron → indicateur progression (focusable mais non actionnable, juste annoncé) → bouton "Plus tard" → recherche → chips dans l'ordre source DOM → bouton "+ Ajouter une passion" → champ libre éventuel → bouton "Continuer"
- `Espace` et `Entrée` togglent un chip ; pour le bouton "Continuer", `Entrée` valide ; pour le bouton "Plus tard", `Entrée` ouvre la dialog
- `Esc` sur la dialog "Plus tard" la ferme + appelle `onRefuse` (cf Story 1.14)
- **Focus visible** : outline 2 px `color-brand` + offset 2 px sur tout élément focusable (token `--focus-ring`, déjà shippé Story 1.2)

**And** **HTML sémantique** :

- L'indicateur de progression est un `<nav aria-label="Progression onboarding">` contenant `<ol>` avec 3 `<li>` (1er `aria-current="step"`), labels SR-only *"Étape 1 sur 3 : passions"* / *"Étape 2 sur 3 : valeurs (à venir)"* / etc.
- Les chips sont des `<button type="button" role="checkbox" aria-checked="true|false">` (ou `<input type="checkbox">` visuellement caché si la lib préfère), groupés dans un `<div role="group" aria-labelledby="passions-heading">`
- Les valeurs (1B) sont aussi un `role="group"` avec `aria-describedby` pointant vers le helper "3 à 5 valeurs"
- Les `Textarea` (1C) ont `<label for="...">` explicite (RGAA strict, pas juste `aria-label`)

**And** **annonces dynamiques** :

- Quand `selectedCount` atteint 3 (seuil mini), une zone `aria-live="polite"` SR-only annonce *"Minimum atteint, tu peux continuer."*
- Quand l'utilisateur dépasse 8 chips passions (max), `aria-live="polite"` annonce *"Maximum 8 passions atteint, désélectionne pour en changer."*
- Le changement de sous-étape (1A → 1B → 1C) annonce *"Étape 2 sur 3 : valeurs"* via la même zone `aria-live`

**And** **reduced motion** :

- Les transitions de dot de progression (`motion-quick` 200 ms) collapsent à ~0 ms via la règle globale `@media (prefers-reduced-motion: reduce)` shippée par Story 1.2
- L'animation de check-icon sur sélection de chip (déjà `motion-instant` 100 ms) reste perceptible mais raccourcie
- Aucune autre animation sur cet écran (pas de cirque)

**And** **touch targets** : tous chips, cards valeurs, boutons et champs respectent **44 × 44 px minimum** (chips `sm` 32 px hauteur sont augmentés à 44 px via padding vertical + zone tactile étendue par `::before`)

**And** **zoom 200 %** : aucun overflow horizontal, layout reflow correct, header et footer sticky restent fonctionnels (testé à 320 px × 200 %)

### AC10 — État vide ré-entrée + état terminé

**Given** je reviens sur `/onboarding/step-1` alors que j'ai **déjà complété les 3 sous-étapes** (`profile.onboarding_step1_status === "completed"`)
**When** la page se charge
**Then** je suis **redirigé directement vers `/onboarding/step-2`** (Story 2.2) sans re-afficher cet écran. Pas de message "Tu as déjà complété cette étape", pas de re-validation requise.
**And** si je veux modifier mes passions plus tard, le **point d'entrée canonique** est `/profile/edit/passions` (Story 2.6), pas un re-passage par l'onboarding

---

## 3. Tasks / Subtasks

### T1 — Référentiels passions / valeurs / suggestions (AC2, AC3, AC4)

- Créer `packages/copy/onboarding/passions.ts` exportant `PASSIONS_CATEGORIES: ReadonlyArray<{ id: string; label: string; aliases: string[] }>` (20 entrées) + `VALEURS: ReadonlyArray<{ id: string; label: string; description: string }>` (12 entrées) + `INTERETS_SUGGESTIONS: Record<1|2|3, string[]>` (~5 suggestions par champ)
- IDs en **kebab-case stable** (ex. `sciences-nature`) — ces IDs sont stockés en base, le label peut évoluer sans migration
- Validation Zod côté serveur : `passions` et `valeurs` doivent appartenir au référentiel OU être un custom (préfixe `custom:` + slug)
- Test unitaire : référentiel non-vide, IDs uniques, label < 30 chars, description valeurs < 80 chars

### T2 — `getPresumedLevel(birthDate, today): "college" | "lycee" | "postbac"` (AC8)

- Util pure dans `packages/copy/levelAdapter.ts`
- Bornes : < 15 ans civils → `college` ; 15-18 → `lycee` ; > 18 → `postbac` ; date invalide / manquante → `lycee` (fallback)
- Snapshot tests des 3 variantes copy `getOnboardingCopy(level)` retournant le bundle complet `{ passionsTitle, passionsSubtitle, valeursTitle, interetsPlaceholders: [string, string, string], … }`

### T3 — API backend : GET + PATCH `/api/v1/students/me/onboarding/passions` (AC5, AC6)

- Modèle `StudentProfile` étendu (ou modèle dédié `OnboardingStep1` si la séparation logique le justifie — décision dev) avec colonnes :
  - `passions JSONB NOT NULL DEFAULT '[]'` (array de string IDs, max 8 entrées validées en check constraint)
  - `valeurs JSONB NOT NULL DEFAULT '[]'` (array de string IDs, 3-5 entrées en validation applicative — pas check constraint car peut être incomplet entre sous-étapes)
  - `interets JSONB NOT NULL DEFAULT '{"1":null,"2":null,"3":null}'`
  - `onboarding_step1_status VARCHAR NOT NULL DEFAULT 'pending'` (`pending | in_progress | completed | skipped`)
  - `onboarding_step1_completed_at TIMESTAMPTZ`
- Migration Alembic avec backfill `'pending'` pour les comptes existants
- Endpoint `PATCH` accepte payload partiel (sous-étape unique) + valide le référentiel
- Endpoint `GET` retourne l'état complet + `onboarding_step1_status`
- RLS appliqué via Story 1.8 (un élève ne lit / écrit que son propre profil) — test multi-tenant requis

### T4 — Frontend : écran `OnboardingStep1` (AC1-AC10)

- Route Next.js : `apps/web/app/(auth)/onboarding/step-1/page.tsx` (segment protégé par middleware Story 1.7)
- Composant racine `<OnboardingStep1 />` orchestre les 3 sous-étapes en state local (`substep: 1 | 2 | 3`) + appelle PATCH entre chaque
- Sous-composants : `<PassionsPicker />`, `<ValeursPicker />`, `<InteretsFreeForm />`, `<ProgressDots />`, `<SkipDialog />` (compose `ConsentDialog` Story 1.14)
- React Hook Form + Zod resolver pour validation 1C
- `useLocalStorageDraft('onboarding_step1_draft', { sync: 'on-blur' })` pour persistence offline (AC5)
- Pré-fetch GET au mount + skeleton (`<Skeleton />` shadcn) pendant le chargement
- Redirection vers step-2 si `onboarding_step1_status === "completed"` (AC10)

### T5 — Tests (front + back)

- **Backend (pytest)** : GET retourne état initial vide, PATCH valide référentiel et rejette IDs inconnus, PATCH partiel ne wipe pas les autres champs, RLS bloque accès cross-tenant
- **Frontend (Vitest + React Testing Library)** :
  - Render 1A → sélection 3 chips active le bouton "Continuer"
  - Saisie dans recherche filtre la grille (debounce respecté)
  - Skip dialog confirme → PATCH avec `step1_skipped` + redirect step-2
  - Reduced-motion : transitions dot < 50 ms (vérifie l'application de `prefers-reduced-motion`)
  - Snapshot copy 3 personas (college / lycee / postbac)
- **E2E (Playwright)** : happy path Sarah Terminale (3 sous-étapes en < 90 s simulées) + path Mehdi (vérifie variante copy) + path Léa (skip step → step-2)
- **A11y (axe-core)** : chaque sous-étape passe axe sans nouvelle violation critique ; touch target audit visuel sur la grille de chips
- **Manuel** : VoiceOver iOS + NVDA Windows sur les 3 sous-étapes (cf NFR-A1) — checklist documentée dans `docs/a11y/onboarding-step1.md`

### T6 — Documentation

- `docs/onboarding/step1-passions.md` : flow visuel + référentiel + copy variants
- Mise à jour `_bmad-output/planning-artifacts/ux-design-specification.md` § Components — `OnboardingStep1` ajouté à la liste des composants Couche 3 sprint 4
- Ajout à `docs/a11y/index.md` (si existant) avec checklist VoiceOver

---

## 4. Dev Notes

### 4.1 Wireframes ASCII — sous-étape 1A (Passions), mobile 375 px

```
┌─────────────────────────────────────────┐ ← header sticky (56 px h)
│ <  ● ○ ○                       Plus tard │
├─────────────────────────────────────────┤
│                                          │ ← space-6 padding top
│  Qu'est-ce qui te plaît, vraiment ?     │ ← text-h2, weight 600
│  Choisis-en au moins 3. T'inquiète,     │ ← text-body, color-text-muted
│  tu pourras changer.                     │
│                                          │
│  ┌─────────────────────────────────────┐│ ← Input shadcn, h 40
│  │ 🔍 Cherche par mot-clé (ex. ciné…) ││
│  └─────────────────────────────────────┘│
│                                          │
│  ┌─────────┐ ┌─────────┐ ┌──────────┐  │ ← chips flex-wrap, gap space-2
│  │Sciences │ │ Tech &  │ │  Arts &  │  │   chacun h 44 (touch target)
│  │& nature │ │  code   │ │ création │  │
│  └─────────┘ └─────────┘ └──────────┘  │
│  ┌─────────┐ ┌─────────────┐ ┌──────┐  │
│  │✓ Sport &│ │ Aider les   │ │Musique│ │ ← ✓ = chip sélectionné
│  │  corps  │ │   autres    │ │       │ │   fond color-brand
│  └─────────┘ └─────────────┘ └──────┘  │
│  ┌──────────┐ ┌──────────┐ ┌────────┐  │
│  │✓ Cinéma  │ │ Lecture &│ │Voyage &│  │
│  │ & séries │ │ écriture │ │cultures│  │
│  └──────────┘ └──────────┘ └────────┘  │
│  … (10 autres chips, scroll vertical) … │
│                                          │
│  + Ajouter une passion à toi             │ ← bouton tertiary
│                                          │
│  ✓ Sport & corps   ✓ Cinéma & séries    │ ← compteur visuel
│  ✓ Justice clima (custom)            3/3 │   color-success quand atteint
│                                          │
│                          (scroll)        │
├─────────────────────────────────────────┤
│  ┌────────────────────────────────────┐ │ ← footer sticky (72 px h)
│  │         Continuer            →     │ │ ← primary, lg, full-width mobile
│  └────────────────────────────────────┘ │   enabled (vert) quand ≥ 3
│  Tu peux continuer quand tu veux         │ ← caption sous bouton
└─────────────────────────────────────────┘
```

### 4.2 Wireframes ASCII — sous-étape 1B (Valeurs), mobile 375 px

```
┌─────────────────────────────────────────┐
│ <  ● ● ○                       Plus tard │
├─────────────────────────────────────────┤
│                                          │
│  Ce qui compte le plus pour toi          │
│  Choisis 3 à 5 valeurs. Y'a pas de       │
│  bonne réponse.                          │
│                                          │
│  ┌─────────────────────────────────────┐│ ← card, h 56 minimum
│  │ Justice sociale                    ✓││   fond color-bg-2
│  │ Que les choses soient justes pour   ││   border color-border
│  │ tout le monde                       ││   ✓ visible si sélectionné
│  └─────────────────────────────────────┘│
│  ┌─────────────────────────────────────┐│
│  │ Indépendance                         ││
│  │ Pouvoir bosser à ton rythme,         ││
│  │ à ta façon                          ││
│  └─────────────────────────────────────┘│
│  ┌─────────────────────────────────────┐│
│  │ Sécurité                             ││
│  │ Un cadre stable, prévisible          ││
│  └─────────────────────────────────────┘│
│  ┌─────────────────────────────────────┐│
│  │ Créativité                         ✓ ││
│  │ Inventer, créer, faire des trucs    ││
│  │ nouveaux                            ││
│  └─────────────────────────────────────┘│
│  … (8 autres cards, scroll vertical) …  │
│                                          │
├─────────────────────────────────────────┤
│  ┌────────────────────────────────────┐ │
│  │         Continuer            →     │ │
│  └────────────────────────────────────┘ │
│  Choisis-en au moins 3   ← 2/3 sélection│
└─────────────────────────────────────────┘
```

### 4.3 Wireframes ASCII — sous-étape 1C (Centres d'intérêt), mobile 375 px

```
┌─────────────────────────────────────────┐
│ <  ● ● ●                       Plus tard │
├─────────────────────────────────────────┤
│                                          │
│  Ce que tu suis, écoutes, regardes       │
│  3 lignes max, format libre. Une chaîne  │
│  YouTube, un podcast, un livre, une      │
│  matière qui t'a marqué — ce que tu veux.│
│                                          │
│  Champ 1                                 │ ← label text-body-sm
│  ┌─────────────────────────────────────┐│
│  │ Ex. La chaîne YouTube de Marie     ││ ← Textarea shadcn
│  │ Lopez sur la chimie, ou un podcast ││   placeholder italic muted
│  │ Choses à savoir…                   ││
│  └─────────────────────────────────────┘│
│  ┌YouTube ┐ ┌ Podcast ┐ ┌  Livre  ┐    │ ← chips suggestion sm
│  └────────┘ └─────────┘ └─────────┘    │   tap → injecte texte
│                                          │
│  Champ 2                                 │
│  ┌─────────────────────────────────────┐│
│  │ Ex. Le bouquin Sapiens, un film…   ││
│  └─────────────────────────────────────┘│
│  ┌  Film  ┐ ┌ Série ┐ ┌ Documentaire ┐ │
│                                          │
│  Champ 3                                 │
│  ┌─────────────────────────────────────┐│
│  │ Ex. La séquence sur la photo-      ││
│  │ synthèse en 2nde, un débat en      ││
│  │ HGGSP…                             ││
│  └─────────────────────────────────────┘│
│  ┌Matière┐ ┌  TP  ┐ ┌  Projet de classe┐│
│                                          │
├─────────────────────────────────────────┤
│  ┌────────────────────────────────────┐ │
│  │         Terminer             ✓     │ │ ← TOUJOURS enabled
│  └────────────────────────────────────┘ │
│  Tu pourras compléter plus tard depuis  │ ← caption discret
│  ton profil.                             │
└─────────────────────────────────────────┘
```

### 4.4 Wireframes ASCII — desktop 1024 px (sous-étape 1A typique)

```
┌──────────────────────────────────────────────────────────────────────┐
│ Path-Advisor                                              ● ○ ○      │ ← top header, no back ici
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│                                                       [Plus tard →]   │ ← bouton tertiary
│                                                                       │
│              Qu'est-ce qui te plaît, vraiment ?                       │ ← centered, max-w 600
│              Choisis-en au moins 3. T'inquiète, tu pourras changer.   │
│                                                                       │
│              ┌────────────────────────────────────────────────────┐  │
│              │ 🔍 Cherche par mot-clé (ex. cinéma, sport, code…) │  │
│              └────────────────────────────────────────────────────┘  │
│                                                                       │
│              ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │ ← grille 4 col desktop
│              │ Sciences │ │  Tech &  │ │  Arts &  │ │ ✓ Sport &│    │
│              │ & nature │ │   code   │ │ création │ │   corps  │    │
│              └──────────┘ └──────────┘ └──────────┘ └──────────┘    │
│              … (16 chips au total, 4 lignes) …                       │
│                                                                       │
│              + Ajouter une passion à toi                              │
│                                                                       │
│              ✓ Sport & corps   ✓ Cinéma & séries           3/3 ✓     │
│                                                                       │
│                                                                       │
│                                            [    Continuer    →    ]  │ ← right-aligned primary
│                                            Tu peux continuer…         │
└──────────────────────────────────────────────────────────────────────┘
```

### 4.5 État émotionnel à chaque sous-étape — référentiel pour copy review

Synthèse condensée du § Emotional Journey Mapping de l'UX spec, appliquée à cet écran. Toute évolution de copy doit passer ce filtre.

| Sous-étape | État d'entrée probable Sarah | Cible émotionnelle | Triggers à bannir |
|---|---|---|---|
| 1A Passions | Doute ("Je sais pas trop ce qui me plaît") | Petite légèreté ("Ah ouais en fait y'a des trucs") | "Tu y es presque !", "Allez !", confettis, tests psychos |
| 1B Valeurs | Self-doubt amplifié, peur du jugement | Calme + agentivité ("C'est mes choix") | "Bonne réponse", scoring de valeur, ranking |
| 1C Intérêts | Soulagement (champs libres = pas d'examen) | Expression libre + zéro stress sortie | Champs obligatoires, "Profil enrichi !" |

**Test sortie écran (à appliquer en sprint review)** : à la fin de l'écran 2.1, Sarah ferme l'app et pense quoi ? Cible : *"OK, c'était court et ça m'a pas pris la tête."* — pas *"J'espère que j'ai bien répondu."*

### 4.6 Anti-patterns proscrits sur cet écran (rappel critique)

Issus du § Anti-patterns proscrits — récapitulatif global de l'UX spec, focus sur ceux qui menacent **spécifiquement** cet écran :

- ❌ **Score sans phrase recopiable** — N/A ici (pas de score), mais à anticiper pour Epic 3
- ❌ **"Profil complété à X %"** — interdit nominalement ; même la wording "Étape 1/3 complétée à 100 %" est proscrite. Utiliser uniquement les dots `● ● ○`.
- ❌ **Confettis / célébrations** — aucune célébration à la fin de l'écran. Transition silencieuse vers step-2.
- ❌ **Validation à chaque keystroke** — recherche debounce 150 ms OK, mais pas de "Tu as bien rempli ✓" qui apparaît caractère par caractère
- ❌ **Toast d'erreur pour erreur de champ** — si validation échoue côté serveur sur PATCH (référentiel inconnu), erreur inline `text-caption` `color-danger` sous la zone concernée, pas de toast ambient
- ❌ **Hamburger menu** — N/A sur cet écran (pas de nav globale visible)
- ❌ **Hover required pour découvrir une fonctionnalité** — toutes les chips de suggestion 1C ont leur label visible au repos sans hover

### 4.7 Edge cases et failures explicites

| Edge case | Comportement attendu | AC ref |
|---|---|---|
| Élève sélectionne 1 chip puis désélectionne tout, reste à 0 | Bouton Continuer disabled, helper "Sélectionne au moins 3" | AC2 |
| Élève tape 100 chips passions (custom string) — flood | Validation client max 5 customs, refus avec helper inline `color-warning` *"Maximum 5 propositions à toi"* + API rejette aussi (defense in depth) | AC2 |
| Réseau coupe pile pendant le PATCH 1A → 1B | Draft localStorage conservé, transition vers 1B OK, toast info *"Pas de réseau ? Pas grave…"*, retry PATCH au reconnect via SWR / TanStack Query | AC5 |
| Élève change l'orientation device pendant 1B | Layout reflow, pas de perte d'état (state React local + draft sync) | AC9 |
| Session JWT expire pendant onboarding | Redirect `/login?return_to=/onboarding/step-1`, draft réappliqué au retour | AC6 |
| Élève < 13 ans (impossible théoriquement à cause de Story 1.4) | Si on arrive ici quand même : copy collège, mais flag log warning "underage_onboarding_step1_reached" pour audit Story 1.13 | AC8 |
| Date de naissance manquante / corrompue | Fallback variante lycée + log warning silent | AC8 |
| `motion-reduced` actif | Transitions dots ~0 ms, anim check icon ~0 ms, écran reste pleinement fonctionnel | AC9 |
| Zoom navigateur 200 % à 320 px | Pas d'overflow horizontal, header et footer sticky toujours en place | AC9 |
| Lecteur d'écran en cours, sélection chip | Annonce *"Sciences et nature, sélectionné, 3 sur 3 minimum atteint, tu peux continuer"* | AC9 |
| Élève fait "page refresh" pendant 1C avec champ 1 rempli localement (non encore PATCH) | Champ 1 restauré depuis localStorage draft, pas de prompt "Voulez-vous quitter ?" (anti-friction) | AC5, AC6 |
| Élève complète 1A et 1B, clique "Plus tard" sur 1C | Dialog confirme → 1A et 1B sont marqués `completed` côté serveur, 1C reste `pending`, `onboarding_step1_status = "partial_skipped"` (nuance à valider sprint review) | AC7 |

### 4.8 Décisions design verrouillées

- **3 sous-étapes, pas 1 grand questionnaire** — décision UX confirmée par § Form Patterns (*"Multi-step : progress indicator visible (3 points discrets), persistence auto entre étapes"*). Réduit la charge cognitive perçue, autorise interruption sans perte.
- **Chips multi-select pour passions, cards radio-list pour valeurs, textarea libre pour intérêts** — 3 patterns volontairement différents pour signaler 3 types de signaux différents. Le mix réduit la lassitude perceptive.
- **Aucun astérisque "obligatoire"** sur les champs — convention UX spec §Form Patterns. Le caractère obligatoire est exprimé par le helper et l'état disabled du CTA, jamais par un astérisque rouge.
- **"Plus tard" toujours accessible** dans le header — anti-piège utilisateur, conforme principe émotionnel dignité.
- **Pas de bouton "Précédent" entre sous-étapes** — décision : si Sarah veut modifier 1A après être passée sur 1B, elle clique sur le dot `● ○ ○` qui revient à l'étape correspondante (focusable + actionable via Entrée). Économise un bouton et un cas focus.
- **Pas de mode "essai" / "preview reco partielle"** sur cet écran — tentation à résister. La reco vient seulement après step-3.
- **Référentiel de 20 + 12 valeurs en MVP**, pas plus. Curation > exhaustivité (anti-paralysie de choix).

### 4.9 Versions et libraries à utiliser

(Cohérent avec l'écosystème Story 1.1 / 1.2 / 1.14)

- React 19, Next.js 15, TypeScript 5.x
- shadcn/ui composants : `Button`, `Input`, `Textarea`, `Toggle`, `Card`, `Dialog` (via `ConsentDialog` Story 1.14), `Skeleton`, `Toast`, `Label`
- React Hook Form 7.x + Zod 3.x pour 1C
- TanStack Query 5.x (déjà setup Story 1.3) pour fetch / mutate / cache
- Lucide React 0.4xx (déjà setup Story 1.2) — icônes `Check`, `Search`, `X`, `ChevronLeft`, `Plus`
- Vitest 2.x + React Testing Library 16.x pour tests unitaires
- Playwright 1.4x pour E2E (réutilise harness Story 1.3)
- axe-core react 4.x pour a11y CI

### 4.10 Items à différer (`deferred-work.md` post-merge)

- Système de **traduction multi-langue** des référentiels (passions / valeurs) — i18n shippé seulement en sprint 11 (Epic 7), MVP est FR uniquement
- **Édition différée** des passions / valeurs depuis le profil — Story 2.6 dédiée
- **Reco partielle "preview"** après step-1 seul — pas en MVP, le moteur reco veut le min step-1 + step-2 + step-3 (ou step-3 skipped) pour scorer correctement
- **Recommandation de valeurs basée sur les passions sélectionnées** (cross-suggestion) — backlog, pas MVP
- **Animation séquentielle "ta sélection a été enregistrée"** entre sous-étapes — anti-cirque, on n'en met pas

---

## 5. Project Structure Notes

**Files à créer/modifier (estimation indicative) :**

```
apps/web/
  app/(auth)/onboarding/step-1/
    page.tsx                       ← entrée Next.js, server component fetch initial
    OnboardingStep1.tsx            ← client component orchestrateur (3 sous-étapes)
    PassionsPicker.tsx             ← AC2
    ValeursPicker.tsx              ← AC3
    InteretsFreeForm.tsx           ← AC4
    ProgressDots.tsx               ← AC1
    SkipDialog.tsx                 ← AC7 (compose ConsentDialog)
    useOnboardingStep1.ts          ← hook query + mutation + draft localStorage
    __tests__/
      OnboardingStep1.test.tsx
      PassionsPicker.test.tsx
      ValeursPicker.test.tsx
      a11y.spec.ts
  e2e/
    onboarding-step1.spec.ts       ← Playwright

packages/
  copy/
    onboarding/
      passions.ts                  ← référentiels (T1)
      valeurs.ts
      interets-suggestions.ts
      copy-variants.ts             ← getOnboardingCopy(level) (T2)
      __tests__/snapshots.test.ts

apps/api/apps/students/            ← (ou équivalent selon structure réelle, à confirmer post-Story 1.8)
  models.py                        ← extension StudentProfile (T3)
  views_onboarding.py              ← GET + PATCH endpoints
  serializers_onboarding.py
  migrations/
    NNNN_onboarding_step1_fields.py
  tests/
    test_onboarding_step1.py

docs/onboarding/
  step1-passions.md                ← documentation UX (T6)
docs/a11y/
  onboarding-step1.md              ← checklist VoiceOver/NVDA
```

**Conventions à respecter (déjà actées) :**

- Tokens CSS uniquement, jamais de valeurs hex inline (Story 1.2)
- Pas de `useEffect` pour data fetching → TanStack Query (cf Story 1.3)
- HTML sémantique d'abord, ARIA en dernier recours (UX spec §Accessibility)
- Test names en français OK pour les snapshots de copy (testabilité humaine)

---

## 6. References

- **UX spec globale** : `_bmad-output/planning-artifacts/ux-design-specification.md`
  - § Experience Principles (5 principes)
  - § Form Patterns (multi-step, labels, validation)
  - § Button Hierarchy (primary / secondary / tertiary / disabled)
  - § Motion System (`motion-quick`, `motion-instant`)
  - § Accessibility Strategy (RGAA AA cible)
  - § Anti-patterns proscrits — récapitulatif global
- **Epic 2 detail** : `_bmad-output/planning-artifacts/epics/epic-2-profil-eleve-onboarding.md` § Story 2.1
- **Story 1.2 (design tokens)** : `_bmad-output/implementation-artifacts/1-2-design-system-tokens.md` — tokens couleur / type / spacing / motion
- **Story 1.14 (ConsentDialog)** : `_bmad-output/implementation-artifacts/1-14-composant-consent-dialog.md` — utilisé pour SkipDialog
- **Story 1.8 (RLS)** : `_bmad-output/implementation-artifacts/1-8-multi-tenant-rls-postgresql.md` — isolation profil
- **Story 1.13 (audit log)** : `_bmad-output/implementation-artifacts/1-13-journal-audit-acces.md` — pour le flag underage warning (AC8 edge case)
- **PRD** : `_bmad-output/planning-artifacts/prd/` — FR13 (signaux déclaratifs), UX-DR30 (vocab par niveau)

---

## 7. Dev Agent Record

### Agent Model Used
_(à remplir par dev agent)_

### Debug Log References
_(à remplir)_

### Completion Notes List
_(à remplir)_

### File List
_(à remplir)_

### Change Log

- 2026-05-24 — Story 2.1 contextée et passée en `ready-for-dev` par Marwen + Claude (Opus 4.7) dans le cadre du démarrage parallèle UX Epic 2 pendant que Epic 1 finit (Stories 1.5 / 1.7 / 1.8 / 1.11 / 1.12 encore en cours).
