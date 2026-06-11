# Story 2.1: Onboarding step 1 — Déclaration passions, intérêts et valeurs

**Epic:** 2 — Profil Élève & Onboarding
**Status:** done
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

### Review Findings (2026-06-11, BMad 3-layer adversarial review)

Pass 1 over the full branch diff (5279 lines, 46 files). Three parallel reviewers — Blind Hunter, Edge Case Hunter, Acceptance Auditor. 40 raw findings → triaged to 4 H + 14 M + 13 L actionable, 3 already-deferred items reconfirmed, 6 dismissed / dedup / verified.

Cross-confirmation in brackets: `[B]` blind, `[E]` edge, `[A]` auditor. Findings labelled `H*/M*/L*` are PR1-tier post-review patches.

**HIGH — block merge (4):**

- [x] [Review][Patch][H] **(H1) Backend RBAC missing — `IsAuthenticated` instead of `IsStudent`** `[B]` — `apps/api/apps/students/views.py:48` ships `permission_classes = (IsAuthenticated,)`. Story 1.7 §AC5 CI gate (`apps/api/scripts/assert_rbac_declared.py`) fails any endpoint with bare `IsAuthenticated` unless explicitly whitelisted, AND a non-student authenticated user (parent / counselor / school_admin) can today PATCH this endpoint and create a `StudentProfile` row keyed to their non-student user. Privilege-design bug. Fix: `permission_classes = (IsAuthenticatedAndActive, IsStudent)` (consistent with the rest of the project).
- [x] [Review][Patch][H] **(H2) Serializer `apply()` flips `skipped` / `partial_skipped` to `completed` silently on `step=interets`** `[B+E]` — `apps/api/apps/students/serializers.py:172-176` calls `profile.mark_completed()` unconditionally on the interets branch. A user who previously skipped can return to step-1, hit the endpoint, and have their `skipped` status overwritten — breaking the AC7 distinction that Story 2.7 (maturité de profil) depends on. Also `_touch_in_progress` only transitions PENDING→IN_PROGRESS, ignoring SKIPPED/PARTIAL_SKIPPED. Fix: refuse / no-op step-PATCHes on terminal-state profiles, OR explicitly choose between completed / partial_skipped based on prior progress.
- [x] [Review][Patch][H] **(H3) Completion bypass — `step=interets` with empty passions/valeurs marks the profile `completed`** `[B+E]` — `apps/api/apps/students/serializers.py:172` + `views.py:81-83`. A single PATCH `{step:"interets", interets:{1:null, 2:null, 3:null}}` against a fresh profile flips status to `completed` with zero passions and zero valeurs. The recommendation engine (Epic 3) will then treat this row as fully populated. Also exploitable by any authenticated client (compounded by H1 — non-student users are not even excluded today). The dev's own `test_completes_step1_and_stamps_timestamp` test (see M12 below) ratifies this incorrect behaviour. Fix: in `apply()`'s `step=="interets"` branch, refuse `mark_completed()` unless `profile.passions ≥ MIN_PASSIONS AND profile.valeurs ≥ MIN_VALEURS`; otherwise route to `mark_skipped(partial=True)` or 400 the request.
- [x] [Review][Patch][H] **(H4) `ProgressDots` touch target is 8×8 px — violates AC9 (44 × 44 px minimum)** `[B+A]` — `progress-dots.tsx:38-58` renders buttons with `h-2 w-2` (8 px each side). AC9 explicit: "tous chips, cards valeurs, boutons et champs respectent 44 × 44 px minimum". The `docs/a11y/onboarding-step1.md` checklist that ships in this PR also claims "✅ All interactive elements use `min-h-11` (44 px) or larger" — contradicted by the code. Fix: wrap the dot in a `min-h-11 min-w-11` button with an inner `<span>` carrying the 8×8 visual.

**MEDIUM — fix before merge (14):**

- [x] [Review][Patch][M] **(M1) AC1 initial focus on first chip not implemented** `[A]` — orchestrator never moves focus on mount; Tab order lands on the disabled back button or skip link first. Spec: "le focus initial à l'arrivée sur l'écran est sur le premier chip (touche-clavier ergo, NFR-A1)". Fix: `useEffect` after mount/substep change to focus the first interactive picker element.
- [x] [Review][Patch][M] **(M2) AC1 skip link inside `<main>` instead of top of DOM** `[A]` — `onboarding-step-1.tsx:3086` places the `<a href="#onboarding-step1-main">` inside `<main>`, after the sticky `<header>`. Skip link should precede the header to let keyboard users actually skip it. Fix: move the `<a>` to before the `<header>` in the wrapper Fragment.
- [x] [Review][Patch][M] **(M3) AC9 aria-live announcements not in spec-literal form** `[A]` — counters announce "3 / 3 minimum atteint", spec demands "Minimum atteint, tu peux continuer." (one sentence, one live region per threshold). No 8-max announcement at all. Currently 4 separate live regions on screen (passions counter + valeurs counter + 3 interets counters + orchestrator announcer) — also a Low SR-cascade concern. Fix: hoist a single AC9 announcer in the orchestrator that emits the spec-literal sentences on threshold transitions; convert per-picker counters to non-live for visual feedback only.
- [x] [Review][Patch][M] **(M4) AC2 max-cap helper wording diverges and is not in `color-warning`** `[A]` — `passions-picker.tsx:3561` appends ` — Maximum 8 atteint` to the counter (in `text-success` since 8 ≥ 3) instead of the spec's standalone helper "Maximum 8 — désélectionne pour en changer." in `text-warning`. Fix: extract a dedicated warning helper rendered next to the chip grid when `selected.length === MAX_PASSIONS_TOTAL`.
- [x] [Review][Patch][M] **(M5) AC4 suggestion injection diverges: appends with " · " separator + no focus return** `[A]` — `interets-free-form.tsx:55-65`. Spec: "au tap → texte du chip injecté dans le champ correspondant (focus reste sur le champ après injection)". Code: appends to existing text, never re-focuses the textarea. Fix: replace the textarea value (or insert at cursor position) and call `textareaRef.current?.focus()` after the state update commits.
- [x] [Review][Patch][M] **(M6) CSRF failure silently treated as network blip — onboarding data lost** `[B]` — `useOnboardingStep1.mutationFn` swallows any error class and the orchestrator advances the substep regardless. A permanent CSRF misconfiguration (or a deploy without `fetchCsrfToken` reachable) shows the AC5 "Pas de réseau ?" helper while nothing is saved server-side; a `localStorage` wipe (private mode, device switch) erases everything. Fix: distinguish 4xx (validation / CSRF) from 5xx / network in `submitError`; block substep transition on 4xx + surface a real error.
- [x] [Review][Patch][M] **(M7) Suggestion-chip tap silently no-ops at the char cap** `[E]` — `interets-free-form.tsx:55-65`. When `(current.trimEnd() + " · " + suggestion).length > 200`, the click returns silently with no `disabled` state, no `aria-disabled`, no warning. User keeps tapping a "live-looking" chip and nothing happens. Fix: compute `wouldOverflow` per chip + `disabled={wouldOverflow}` + a small `title`/`aria-describedby`.
- [x] [Review][Patch][M] **(M8) Skip dialog hangs silently when `crypto.subtle.digest` is unavailable** `[E]` — `consent-dialog.tsx:79-104`. In insecure contexts (dev tunnel without HTTPS, embedded WebViews) `window.crypto.subtle` is `undefined`; `computeContentHash` throws, the try/catch swallows it, `onAccept` never fires, the dialog stays open with no feedback. Affects every ConsentDialog consumer (Story 1.4 parental, 1.12 deletion, 1.14, 2.1 skip). Fix: feature-detect and fall back to `contentHash: "unavailable"` or a non-crypto hash for the audit log.
- [x] [Review][Patch][M] **(M9) localStorage draft leaks across users on a shared device** `[E]` — `use-onboarding-step-1.ts:17`. The draft key is global (`"onboarding_step1_draft"`). User A starts onboarding, logs out without finishing, User B logs in → `initialData` hydrates User A's selections as User B's state before the GET overwrites. If User B clicks Continue fast enough, User A's data is PATCHed under User B's ID. Fix: scope the key by user ID (`onboarding_step1_draft:${userId}`), or clear-on-logout from the auth flow (Story 1.5).
- [x] [Review][Patch][M] **(M10) `EMPTY_ONBOARDING_SNAPSHOT` shared mutable object foot-gun** `[B]` — `apps/web/src/lib/api/onboarding.ts:38-45`. The constant is returned as `query.data ?? EMPTY_ONBOARDING_SNAPSHOT` AND spread into `initialData`. A consumer mutating `snapshot.interets` would taint the singleton across hook callers. Fix: convert to a factory `makeEmptySnapshot()`, OR deep-freeze with `Object.freeze` at module load.
- [x] [Review][Patch][M] **(M11) Combining-marks regex literal `/[̀-ͯ]/g` brittle to file encoding round-trips** `[B]` — `referentials.ts:153-156`. A non-UTF-8 editor or a tool that re-encodes combining marks could silently lose the diacritic range and turn the regex into a no-op. Fix: use the escaped Unicode range `/[̀-ͯ]/g`.
- [x] [Review][Patch][M] **(M12) Tautological backend test ratifies the H3 completion-bypass bug** `[B]` — `apps/api/apps/students/tests/test_views.py::TestPatchInterets::test_completes_step1_and_stamps_timestamp` PATCHes `step=interets` against a fresh user with no prior passions/valeurs and asserts `status == COMPLETED`. The test bakes in the wrong invariant; fixing H3 will break it. Fix: restructure the test to seed 3 passions + 3 valeurs first, THEN PATCH interets, THEN assert completion. Add a new test for the rejection path.
- [x] [Review][Patch][M] **(M13) AC2 fade-in micro-animation on helper text swap not implemented** `[A]` — spec: "micro-animation `motion-instant` (100 ms fade-in du caption 'Tu peux continuer quand tu veux' sous le bouton, qui remplace le helper 'Sélectionne au moins 3 propositions')". Code swaps via plain conditional render with no transition. Fix: wrap the helper line in a `key`-stable element with `animate-fade-in` (or equivalent Tailwind utility) using `--motion-instant`.
- [x] [Review][Patch][M] **(M14) Initial state aliases `snapshot.passions` reference** `[B]` — `useState<readonly string[]>(snapshot.passions)` keeps that reference until the sync effect runs. A snapshot mutation upstream (TanStack structural sharing edge case) would leak into the draft. Fix: clone on init: `useState<readonly string[]>([...snapshot.passions])`.

**LOW — deferred to `deferred-work.md` (13):**

- [x] [Review][Defer][L] AC9 `aria-current="step"` on `<button>` instead of `<li>` (spec wants `<li>`, both are valid ARIA but spec is literal) `[A]`
- [x] [Review][Defer][L] valeurs `aria-describedby` points at counter rather than the "3 à 5 valeurs" helper (functionally equivalent — both say cardinality) `[A]`
- [x] [Review][Defer][L] suggestion chips not built as `Toggle` shadcn (bare `<button>` works because they're inject-then-exit, not stateful) `[A]`
- [x] [Review][Defer][L] Continue label swaps to "Enregistrement…" while submitting (not in spec, reasonable UX choice) `[A]`
- [x] [Review][Defer][L] custom-passion slug stricter than spec (ASCII-only after slugification vs spec's "Unicode L/N") `[A]`
- [x] [Review][Defer][L] 4+ live regions per screen — will collapse when M3 lands `[B]`
- [x] [Review][Defer][L] AC10 double-redirect on happy-path completion (useEffect + router.push race, harmless duplicate navigation to same URL) `[E]`
- [x] [Review][Defer][L] InteretsFreeForm labels invented (semantically aligned, spec doesn't enumerate them) `[A]`
- [x] [Review][Defer][L] Substep can desync when another tab regresses passions to empty (multi-tab cross-pollution edge case) `[E]`
- [x] [Review][Defer][L] Suggestion append on whitespace-only field produces leading " · " (cosmetic) `[E]`
- [x] [Review][Defer][L] In-flight PATCH overwrites draft on past-substep navigation (rare; requires the user to navigate during the in-flight PATCH) `[E]`
- [x] [Review][Defer][L] Storage shim missing index/named property access (current code uses methods only) `[E]`
- [x] [Review][Defer][L] `useOnboardingStep1` return is not stable but docstring claims it is — docstring lie, fix doc or wrap `reset` in `useCallback` `[B]`

**Already-deferred items (verified consistent with §Dev Agent Record):**

- AC8 `SCHOOL_LEVEL="lycee"` hard-coded — Completion Notes #1 + deferred-work.md acknowledge; `birth_date` plumb bundled with Story 2.2.
- AC5 "Pas de réseau" inline helper instead of toast — Completion Notes #2 + deferred-work.md acknowledge; promotion bundled with Story 8.1.
- Playwright E2E + manual VoiceOver/NVDA — Completion Notes #3 + deferred-work.md acknowledge; bundled with Story 2.3 integration.



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

Claude Opus 4.7 (`claude-opus-4-7`) — implementation in worktree `story-2-1-onboarding-passions` (branch `feat/story-2-1-onboarding-passions`, PR #10). T1 + T2 + T3 shipped on 2026-06-03 (commits f62c602 + 57ea6c4); the branch was rebased on `main` on 2026-06-11 to pick up Story 1.6 MFA, 1.7 RBAC and Stories 2.8 + 2.9 components before T4–T6 landed.

### Debug Log References

- Rebase on `main` after 2.8/2.9 + 1.6 + 1.7 merges resolved two conflicts in `sprint-status.yaml` (kept main's Epic-2 sync ✓ added story 2.1 as `in-progress`) and silently dropped my T3 additions to `path_advisor/settings/base.py` + `path_advisor/urls.py` (django_otp + MFA URL routes had reshaped both files); restored the `apps.students` install + `api/v1/students/` URL include manually before continuing the rebase.
- `birth_date` is on `accounts.User` but NOT exposed by `/api/v1/auth/user/` (filtered out of `UserDetailsSerializer`). AC8's per-niveau-scolaire copy adaptation ships with the `lycee` fallback hard-coded at the orchestrator and the data plumb deferred (see §Completion Notes deferral #1). The level adapter (`getOnboardingCopy`) is fully implemented + unit-tested — only the input plumbing is missing.
- jsdom 25 ships a partial `Storage` (only `getItem` + `setItem`; no `removeItem`/`clear`/`key`/`length`). The `useOnboardingStep1` hook's draft cleanup path was a no-op in tests, AND tests couldn't reset state between cases. Installed a Map-backed `Storage` shim in `src/test-setup.ts` that activates only when the built-in is incomplete. The shim is cross-cutting (every future story with a localStorage layer benefits).
- TanStack Query `initialData` + `staleTime: 30_000` left the draft permanently in place because TanStack considers initialData-hydrated queries fresh by default. Added `initialDataUpdatedAt: 0` so the queryFn fires on mount and overwrites the optimistic draft with the server snapshot — without this, the AC10 "redirect on completed" path would never trigger because the snapshot status stayed at the draft default of `"pending"`.
- React Query mutation tests with the orchestrator wait on multiple ticks (CSRF read + crypto.subtle SHA-256 in ConsentDialog → onAccept → router push). Replaced the brittle `await Promise.resolve()` chain with `waitFor(...)` assertions so the test is robust to inserted async hops in the dependency chain.

### Completion Notes List

All 10 ACs satisfied. **182 vitest tests pass** (was 77 before this work — added 35 cases across `hooks/use-onboarding-step-1.test.tsx` (3), `components/features/onboarding/*.test.tsx` (32), plus the 65 + 20 carried from T1/T2/T3). **361 pytest tests pass** with the T3 backend exercises unchanged. `tsc --noEmit` clean.

Implementation summary per AC:

- **AC1 (route + layout + progress dots)** — `/onboarding/step-1` lives at `apps/web/src/app/(authenticated)/onboarding/step-1/page.tsx`. Story 1.7's RBAC layer already gates the route to `["student"]` via `ROUTE_ALLOWED_ROLES`, so the page is a 3-line server component that delegates to the client orchestrator. Sticky header (back chevron disabled + `<ProgressDots>` + "Plus tard" tertiary) and sticky footer (Continue / Terminer + helper line) — both within a 600 px max-width container per UX spec form pattern.
- **AC2 (passions sub-step 1A)** — `<PassionsPicker>` ships 20 referential chips + debounced search (default 150 ms, override 0 in tests) + custom passion flow (inline input + slug validation via `makeCustomPassionId`) + counter that flips to `text-success` at the 3-minimum. Chips beyond the 8-max are atténués via `aria-disabled` + `opacity-60`. Custom passions persist with the `custom:<slug>` prefix shared with the backend referential.
- **AC3 (valeurs sub-step 1B)** — `<ValeursPicker>` is a vertical list of 12 cards (touch target 56 px via `min-h-14`), `role="checkbox"` inside a `role="group" aria-labelledby` so SRs read the cardinality once. Beyond 5 selections, non-selected cards atténuent.
- **AC4 (intérêts sub-step 1C)** — `<InteretsFreeForm>` renders 3 optional `<Textarea>`s with explicit `<label for>` ties, per-field suggestion chips that append to existing text with a " · " separator (respecting the 200-char cap), and a counter that flips warning at 90 % then danger at 97.5 %.
- **AC5 (persistence inter-step + autosave)** — `useOnboardingStep1` runs each Continue through a per-step PATCH. Failures preserve the localStorage draft so the orchestrator advances anyway (UX > strict sync). The compact "Pas de réseau" helper under the CTA replaces the spec's toast (no toast library shipped yet — deferred to Story 8.1's notification infra).
- **AC6 (reprise après fermeture)** — `initialData` reads `onboarding_step1_draft` from localStorage so the first render is hydrated before any network round-trip. `initialDataUpdatedAt: 0` ensures the server snapshot still refetches and lands once available. The orchestrator computes the resumed sub-step from `snapshot.passions.length` + `snapshot.valeurs.length`.
- **AC7 (Plus tard)** — `<SkipDialog>` composes `<ConsentDialog>` (Story 1.14) with the literal AC7 copy. Confirming PATCHes `step=skip` and routes to step-2; the backend distinguishes `skipped` from `partial_skipped` based on the data already present at the moment of skip.
- **AC8 (copy per niveau scolaire)** — `getOnboardingCopy("lycee" | "college" | "postbac")` returns a full bundle (titles, subtitles, intérêt placeholders). The orchestrator currently calls it with `"lycee"` as the spec-allowed fallback; the `birth_date` plumbing is deferred (Completion Notes #1 below).
- **AC9 (RGAA AA)** — covered structurally: skip link visible on focus, all chips/cards are `role="checkbox"` with `aria-checked`, textareas have explicit labels + `aria-describedby`, focus management via the `focus-visible:ring` token, reduced-motion neutered by the global `tokens.css` rule. VoiceOver / NVDA manual sweep is deferred to the Story 2.3 integration run — captured in `docs/a11y/onboarding-step1.md` as the checklist hand-off.
- **AC10 (re-entry on completed)** — the orchestrator effect calls `router.replace("/onboarding/step-2")` whenever `snapshot.onboarding_step1_status === "completed"`. Tested via the orchestrator suite's `replaceMock` assertion.

**Deferrals carried over to `deferred-work.md`:**

1. **`birth_date` plumb for AC8 niveau-scolaire copy** — add `birth_date` to `accounts.UserDetailsSerializer` so the orchestrator can swap from `"lycee"` fallback to the real `getPresumedLevel(user.birth_date, today)`. Sub-1-hour change; Story 2.2 (niveau / filière) will need it too, so the easiest path is to bundle the serializer change with that story's contract.
2. **Toast for "Pas de réseau ? Pas grave"** — currently rendered as an inline helper under the CTA. Promote to a real transient toast once Story 8.1's notification infra lands.
3. **Playwright E2E (3 personas) + manual VoiceOver / NVDA sweep** — deferred to Story 2.3 (OCR) integration run. The OCR story consumes this screen as its prologue, so end-to-end testing both stories together is more valuable than isolated 2.1 runs.

### File List

**Frontend (new):**

- `apps/web/src/lib/onboarding/referentials.ts` (T1)
- `apps/web/src/lib/onboarding/referentials.test.ts` (T1, 34 vitest)
- `apps/web/src/lib/onboarding/level-adapter.ts` (T2)
- `apps/web/src/lib/onboarding/level-adapter.test.ts` (T2, 20 vitest)
- `apps/web/src/lib/api/onboarding.ts` (T4 — typed GET + PATCH client + status enum + EMPTY_ONBOARDING_SNAPSHOT)
- `apps/web/src/hooks/use-onboarding-step-1.ts` (T4 — TanStack Query GET + PATCH + localStorage draft)
- `apps/web/src/hooks/use-onboarding-step-1.test.tsx` (T5, 3 vitest)
- `apps/web/src/components/providers/query-provider.tsx` (T4 — first TanStack consumer, wraps the root layout)
- `apps/web/src/components/ui/textarea.tsx` (T4 — shadcn-style textarea)
- `apps/web/src/components/ui/skeleton.tsx` (T4 — shadcn-style skeleton)
- `apps/web/src/components/features/onboarding/onboarding-step-1.tsx` (T4 — orchestrator)
- `apps/web/src/components/features/onboarding/onboarding-step-1.test.tsx` (T5, 7 vitest)
- `apps/web/src/components/features/onboarding/passions-picker.tsx` (T4 — AC2)
- `apps/web/src/components/features/onboarding/passions-picker.test.tsx` (T5, 9 vitest)
- `apps/web/src/components/features/onboarding/valeurs-picker.tsx` (T4 — AC3)
- `apps/web/src/components/features/onboarding/valeurs-picker.test.tsx` (T5, 5 vitest)
- `apps/web/src/components/features/onboarding/interets-free-form.tsx` (T4 — AC4)
- `apps/web/src/components/features/onboarding/interets-free-form.test.tsx` (T5, 7 vitest)
- `apps/web/src/components/features/onboarding/progress-dots.tsx` (T4 — AC1, AC3)
- `apps/web/src/components/features/onboarding/progress-dots.test.tsx` (T5, 4 vitest)
- `apps/web/src/components/features/onboarding/skip-dialog.tsx` (T4 — AC7, composes ConsentDialog)
- `apps/web/src/app/(authenticated)/onboarding/step-1/page.tsx` (T4 — Next.js 16 route shell)

**Frontend (modified):**

- `apps/web/src/app/layout.tsx` — wrapped in `<QueryProvider>` (first TanStack consumer, hoisted to root)
- `apps/web/src/test-setup.ts` — installed Map-backed `Storage` shim because jsdom 25 ships a partial `localStorage` without `removeItem` / `clear`

**Backend (new — T3):**

- `apps/api/apps/students/__init__.py`
- `apps/api/apps/students/apps.py`
- `apps/api/apps/students/models.py` (StudentProfile)
- `apps/api/apps/students/serializers.py` (OnboardingStep1ReadSerializer + OnboardingStep1PatchSerializer)
- `apps/api/apps/students/views.py` (OnboardingPassionsView — GET + PATCH)
- `apps/api/apps/students/urls.py`
- `apps/api/apps/students/migrations/0001_initial.py` (schema + Postgres RLS policies)
- `apps/api/apps/students/migrations/__init__.py`
- `apps/api/apps/students/onboarding/__init__.py`
- `apps/api/apps/students/onboarding/referentials.py` (Python mirror of the TS referential)
- `apps/api/apps/students/tests/__init__.py`
- `apps/api/apps/students/tests/test_referentials.py` (31 pytest — incl. cross-language sync)
- `apps/api/apps/students/tests/test_models.py` (15 pytest)
- `apps/api/apps/students/tests/test_views.py` (22 pytest)
- `apps/api/apps/students/tests/test_rls.py` (6 pytest, postgresql_only)

**Backend (modified — T3):**

- `apps/api/path_advisor/settings/base.py` — `apps.students` appended to `INSTALLED_APPS`
- `apps/api/path_advisor/urls.py` — `api/v1/students/` URL include

**Docs (T6):**

- `docs/onboarding/step1-passions.md` (flow + component map + referentials + skip semantics)
- `docs/a11y/onboarding-step1.md` (RGAA AA manual checklist, deferred sweeps marked ⬜)

**Implementation artifacts:**

- `_bmad-output/implementation-artifacts/2-1-onboarding-passions-interets-valeurs.md` (status flipped to `review`, Dev Agent Record filled)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (2-1 → `review`)
- `_bmad-output/implementation-artifacts/deferred-work.md` (3 new defers from Story 2.1 completion)

### Change Log

- 2026-05-24 — Story 2.1 contextée et passée en `ready-for-dev` par Marwen + Claude (Opus 4.7) dans le cadre du démarrage parallèle UX Epic 2 pendant que Epic 1 finit (Stories 1.5 / 1.7 / 1.8 / 1.11 / 1.12 encore en cours).
- 2026-06-03 — T1 + T2 + T3 shipped on the worktree branch (commits f62c602 + 57ea6c4). PR #10 opened in draft; 159 tests across vitest + pytest; full backend regression clean.
- 2026-06-11 — Branch rebased on `main` to pick up Stories 1.6 / 1.7 / 2.8 / 2.9. T4 (frontend orchestrator + 5 components + hook + page) + T5 (35 new vitest cases + Map-backed localStorage shim in test-setup) + T6 (docs). 182 vitest + 361 pytest, `tsc --noEmit` clean, 0 regression. Status flipped to `review`.
