# Story 2.2: Onboarding step 2 — Niveau scolaire, filière et spécialités

**Epic:** 2 — Profil Élève & Onboarding
**Status:** review (post-review patches + all decisions applied 2026-06-20)
**Sprint:** 4 (Onboarding & Profil)
**Story Key:** `2-2-onboarding-niveau-filiere-specialites`
**Estimation:** M (medium) — branching dynamique côté front + référentiel filières/spés versionné + endpoint PATCH + adaptation downstream du moteur de reco. Pas d'OCR, pas de modèle ML. Sized ~1.5–2 j focused work, **avec un sous-risque** sur la justesse du référentiel bac pro (couverture Mehdi — à valider sprint review).

> Étape 2/3 de l'onboarding. C'est l'écran qui **détermine quel jeu de référentiels** (formations, métiers cibles, calendrier Parcoursup vs Affelnet) sera servi à l'élève. Décision design centrale **UX-DR30** : *branching dynamique selon le niveau scolaire* (3ème → bac pro/général/techno à confirmer ; lycée → spés à préciser ; post-bac → type de formation). **Pas un wizard imposant** : Sarah finit en 30 s, Mehdi finit en 60 s (branche supplémentaire), Léa finit en 30 s. Le récap visuel à la fin sert de **confirmation calme**, pas de validation cérémonieuse.

---

## 1. User Story

**As an** élève (Sarah Terminale lycée général / Mehdi 3ème à orientation bac pro / Léa post-bac ré-orientation),
**I want** déclarer mon niveau scolaire, ma filière et mes spécialités via un formulaire qui **branche intelligemment** selon mes réponses sans m'imposer de wizard, **et voir un récap clair** de ce que j'ai déclaré,
**So that** mes recos vocationnelles (Epic 3) et mes parcours (Epic 4) soient cohérents avec ma trajectoire scolaire réelle (FR16 + FR25 + FR31), et **so that** le calendrier de notifications (Epic 8 Parcoursup vs Affelnet) soit appliqué automatiquement.

**Business value :** sans ce step, le moteur reco produit des suggestions hors-sol (suggérer un BUT à un 3ème, ou ignorer les spécialités d'un Terminale général). Cette étape pose aussi la **première brique du "mode dégradé invisible"** (principe #4 UX spec) : Mehdi (3ème bac pro) et Sarah (Terminale général) voient **strictement le même layout, le même header, les mêmes patterns** — seul le contenu de leur formulaire change après détection du niveau. C'est sur cet écran que se joue **le test anti-stigma Mehdi** : si en saisissant "3ème → bac pro", il voit un bandeau "encouragement" ou une couleur différente, on a échoué.

**Garde-fous personas activés sur cet écran :**

- **Mehdi (anti-stigma)** — branche bac pro / général / techno traitée *visuellement identique* à celle d'un Terminale. Aucun copy *"Voie pro = aussi bien !"*, aucun ribbon "Spécifique bac pro", aucune icône d'encouragement. Test sprint review : un screenshot de l'écran Mehdi vs Sarah doit être **indiscernable** au premier coup d'œil.
- **Léa (dignité)** — peut être post-bac en ré-orientation après une L1 abandonnée. Aucun champ "Pourquoi tu changes ?" intrusif. L'option "Année sabbatique / Recherche" est traitée comme une réponse normale.
- **Sarah (efficacité mobile soir)** — chemin happy path lycée Terminale ≤ 30 s : sélection niveau (1 tap) → sélection filière (1 tap) → sélection spés (3 taps + récap). Pas de scroll long sur mobile.

---

## 2. Acceptance Criteria (BDD)

### AC1 — Route, layout, progression `● ● ○`

**Given** je viens de valider l'écran 1/3 (Story 2.1) ou j'ai cliqué "Plus tard" sur step-1
**When** je suis redirigé vers `/onboarding/step-2`
**Then** je vois un écran avec :

- En **header sticky** : back chevron (`<`) à gauche **enabled** (retour vers step-1, mais avec confirmation `ConsentDialog` light si modifications non sauvegardées en cours — anti-perte) + **indicateur de progression** centré `● ● ○` (dot 1 et 2 actifs `color-brand`, dot 3 inactif `color-border-strong`) + bouton text-tertiary "Plus tard" à droite (cf AC8)
- En **main** : titre h2 + sous-titre + zone de sélection (forme s'adapte au branching, cf AC2-AC5)
- En **footer sticky mobile** : bouton primary "Continuer" (full-width mobile, right-aligned desktop, `lg` size, **disabled tant que la branche en cours n'est pas complète**, cf AC2-AC5) + caption explicative sous le bouton

**And** le layout respecte les mêmes tokens que Story 2.1 (container `max-width: 600 px` desktop, padding `space-4` mobile / `space-6` desktop, fond `color-bg`) — cohérence stricte avec step-1 pour ancrer la perception "je suis dans le même tunnel calme"
**And** le focus initial est sur le **premier RadioGroup item** (sélection niveau scolaire — cf AC2)
**And** un **skip link** "Aller au contenu principal" est rendu en haut du DOM (NFR-A1)

### AC2 — Sélection du niveau scolaire (5 options claires, déclenche branching)

**Given** je suis sur l'écran 2/3 et la sélection niveau n'a pas encore été faite
**When** je consulte la zone de sélection niveau
**Then** je vois :

- Titre `text-h2` : *"Où tu en es, scolairement ?"*
- Sous-titre `text-body` `color-text-muted` : *"Pour qu'on t'envoie les bonnes infos au bon moment."*
- Une **liste de 5 RadioGroup items** (composant shadcn `RadioGroup`, format **card cliquable** taille `lg`, touch target 56 px hauteur minimum, fond `color-bg-2`, border `color-border`, radius `--radius-md`), chacune avec :
  - Label `text-body` weight 500 (ex. *Terminale*)
  - Description courte `text-body-sm` `color-text-muted` (ex. *Année de Parcoursup*)
  - Radio dot Lucide 20 px à droite, visible plein quand sélectionné

**And** les 5 options MVP sont exactement (ordre intentionnel : du plus tôt au plus tard) :

```
3ème                — Année d'orientation (Affelnet, choix lycée)
2nde                — Découverte des matières, choix de spés à venir
1ère                — Première année de spés, Bac Français
Terminale           — Année de Parcoursup, Bac complet
Post-bac            — Tu as déjà ton bac, tu cherches une (ré)orientation
```

**And** **un seul niveau** peut être sélectionné (RadioGroup classique)
**And** la sélection **déclenche immédiatement** l'affichage de la **branche correspondante** (AC3, AC4 ou AC5) — pas de bouton "Confirmer" intermédiaire, la branche apparaît en `motion-quick` (200 ms fade-in + slide-up subtil de 8 px) sous la liste niveau, qui reste affichée et **collapsable** (cliquer sur un autre niveau remplace la branche affichée + animation fade out / in)
**And** **désélection impossible** : une fois un niveau choisi, il faut en sélectionner un autre — pas de "neutre". (Anti-piège : empêche l'élève de cliquer "Continuer" avec une branche fantôme.)
**And** **bouton "Continuer" disabled** tant qu'aucun niveau n'est sélectionné, helper sous bouton : *"Choisis ton niveau pour continuer."*

### AC3 — Branche 3ème (3ème → bac pro / général / techno à confirmer)

**Given** je viens de sélectionner le niveau "3ème"
**When** la branche apparaît
**Then** je vois sous la liste niveau :

- Titre `text-h3` : *"Et après la 3ème, tu vises plutôt quoi ?"*
- Sous-titre `text-body-sm` `color-text-muted` : *"Tu peux changer plus tard, t'inquiète."*
- **3 cards RadioGroup** (mêmes specs visuelles que AC2 — **cohérence stricte avec branche lycée pour Mehdi**) :

```
Bac général         — Filière classique, suite naturelle si tu vises des études longues
Bac techno          — Filières STMG / STI2D / ST2S / etc., entre théorie et concret
Bac pro             — Apprendre un métier en formation, souvent en alternance
```

**And** une **4ème card** *"Pas encore décidé"* est disponible en dernière position avec description *"Pas de pression, on garde les options ouvertes — tes recos incluront tout."* — cette option N'EST PAS visuellement distincte des 3 autres
**And** la sélection 3ème + sous-choix **active** le bouton "Continuer" (pas de spécialité à choisir en 3ème)
**And** côté serveur, le profil est enregistré avec :

```json
{
  "level": "college_3eme",
  "intended_track": "general" | "techno" | "pro" | "undecided",
  "filiere": null,
  "specialites": []
}
```

**And** le flag `intended_track` est utilisé downstream pour :
- **Calendrier de notifications** Epic 8 → Affelnet (mai-juin) au lieu de Parcoursup
- **Référentiel formations** Epic 4 → inclut lycées pro + Affelnet
- **Reco vocationnelle** Epic 3 → pondération des métiers compatibles bac pro **élargie** si `intended_track === "pro"` ou `"undecided"`

### AC4 — Branche Lycée (2nde / 1ère / Terminale → filière + spécialités)

**Given** je viens de sélectionner "2nde", "1ère" ou "Terminale"
**When** la branche apparaît
**Then** je vois (logique identique pour les 3 niveaux, **différenciation uniquement par le nombre de spés attendues**) :

- Titre `text-h3` : *"Ta filière"* (ou *"Ta filière au lycée"* si plus de contexte nécessaire)
- **3 cards RadioGroup** identiques aux options 3ème (AC3) :

```
Bac général
Bac techno (STMG / STI2D / ST2S / STL / STD2A / STAV / STHR)
Bac pro
```

**And** la sélection de la filière fait apparaître **un sous-formulaire spécialités** selon les règles suivantes :

| Niveau    | Filière      | Spécialités à déclarer |
|-----------|--------------|------------------------|
| 2nde      | Général      | Aucune (les spés se choisissent en fin de 2nde) — message *"En 2nde, tu n'as pas encore choisi tes spés. On te demandera plus tard."* + bouton "Continuer" activé |
| 2nde      | Techno       | Aucune (orientation en fin de 2nde aussi) — même message |
| 2nde      | Pro          | Spécialité du bac pro (1 select obligatoire dans liste 12-15 options MVP) |
| 1ère      | Général      | **3 spés exactes** (multi-select dans liste 13 spés officielles) |
| 1ère      | Techno       | Sous-filière techno (STMG / STI2D / ST2S / STL / STD2A / STAV / STHR) en RadioGroup |
| 1ère      | Pro          | Spécialité du bac pro (1 select) |
| Terminale | Général      | **2 spés exactes** (l'élève a laissé tomber une spé en fin de 1ère) — multi-select dans la même liste de 13 spés officielles |
| Terminale | Techno       | Sous-filière techno (idem 1ère) — **et déjà choisie**, donc juste confirmation |
| Terminale | Pro          | Spécialité du bac pro (1 select) |

**And** les **13 spécialités lycée général officielles** (référentiel MVP, à porter dans `packages/copy/onboarding/specialites.ts`) :

```
Mathématiques
Physique-Chimie
Sciences de la Vie et de la Terre (SVT)
Sciences Économiques et Sociales (SES)
Histoire-Géo, Géopolitique et Sciences Politiques (HGGSP)
Humanités, Littérature et Philosophie (HLP)
Langues, Littératures et Cultures Étrangères (LLCER)
Littérature, Langues et Cultures de l'Antiquité (LLCA)
Numérique et Sciences Informatiques (NSI)
Arts (plastiques / théâtre / musique / cinéma-audiovisuel / danse)
Sciences de l'Ingénieur (SI)
Biologie-Écologie (lycées agricoles)
Éducation Physique, Pratiques et Culture Sportives (EPPCS)
```

**And** le sous-formulaire spés (quand applicable) est un `<div role="group" aria-labelledby="spes-heading">` contenant 13 checkboxes (chips multi-select même pattern que Story 2.1 AC2) avec :

- Compteur visuel en bas à droite : `2/3 sélectionnées` (cible 3 en 1ère, 2 en Terminale) — passe en `color-success` quand atteint, `color-warning` si > attendu
- Helper inline `text-caption` `color-text-muted` au-dessus de la grille : *"Sélectionne tes 3 spécialités."* (ou *"Sélectionne tes 2 spécialités."*)
- Le bouton "Continuer" reste **disabled** tant que le compteur ≠ cible exacte

**And** côté serveur, le profil enregistre :

```json
{
  "level": "lycee_2nde" | "lycee_1ere" | "lycee_terminale",
  "filiere": "general" | "techno" | "pro",
  "sous_filiere_techno": "STMG" | "STI2D" | ... | null,
  "specialites": ["mathematiques", "svt", "hggsp"],
  "intended_track": null   // pas applicable au lycée
}
```

### AC5 — Branche Post-bac (post-bac → année + type de formation)

**Given** je viens de sélectionner "Post-bac"
**When** la branche apparaît
**Then** je vois :

- Titre `text-h3` : *"Où tu en es dans tes études ?"*
- Sous-titre `text-body-sm` `color-text-muted` : *"On adaptera nos suggestions à ton parcours."*
- **2 champs side-by-side desktop, stacked mobile** :

  **Champ 1 — Année** (RadioGroup horizontal sur desktop, vertical stacked sur mobile) :

  ```
  Bac année en cours (juste obtenu)
  Bac+1
  Bac+2
  Bac+3
  Bac+4 ou +
  En pause / Recherche
  ```

  **Champ 2 — Type de formation actuelle** (Select shadcn classique) :

  ```
  Université (Licence / Master)
  BUT (ex-DUT)
  BTS
  Classe prépa (CPGE)
  École d'ingénieur
  École de commerce
  École spécialisée (design, journalisme, etc.)
  Formation en alternance / apprentissage
  Aucune formation actuellement (option finale)
  ```

**And** l'option *"En pause / Recherche"* sur l'année + *"Aucune formation actuellement"* sur le type est une **combinaison valide** (Léa ré-orientation type) — pas d'erreur, pas de message culpabilisant
**And** côté serveur, le profil enregistre :

```json
{
  "level": "postbac",
  "postbac_year": "bac_year" | "bac+1" | "bac+2" | "bac+3" | "bac+4_plus" | "pause",
  "postbac_formation_type": "universite" | "but" | "bts" | "cpge" | "ecole_ingenieur" | "ecole_commerce" | "ecole_specialisee" | "alternance" | "aucune",
  "intended_track": null,
  "filiere": null,
  "specialites": []
}
```

**And** le bouton "Continuer" est activé dès que les 2 champs sont remplis

### AC6 — Récap visuel avant validation (critique pour confiance)

**Given** j'ai complété la branche correspondante à mon niveau
**When** je touche/clique le bouton "Continuer" la **première fois**
**Then** **au lieu de passer directement** à step-3, l'écran transitionne vers une **vue récap** dans la même page (pas une nouvelle route, juste un swap state) :

- Titre `text-h2` : *"Voilà ce que tu as déclaré"*
- Sous-titre `text-body` `color-text-muted` : *"Tu peux modifier avant de continuer."*
- Une **carte récap** (composant `Card` shadcn, fond `color-bg-2`, border `color-border`, padding `space-6`) avec contenu adapté au niveau :

**Variante Sarah Terminale général :**
```
┌──────────────────────────────────────┐
│ Terminale • Bac général              │ ← text-body weight 600
│                                       │
│ Tes spécialités :                    │ ← text-body-sm color-text-muted
│   • Mathématiques                     │ ← text-body
│   • SVT                               │
│   • HGGSP                             │
│                                       │
│ Tu seras notifié(e) du calendrier     │ ← text-body-sm color-text-subtle
│ Parcoursup à partir de novembre.      │
│                                       │
│              [ Modifier ]             │ ← bouton tertiary, droite
└──────────────────────────────────────┘
```

**Variante Mehdi 3ème → bac pro :**
```
┌──────────────────────────────────────┐
│ 3ème • Visée : Bac pro                │
│                                       │
│ Tu seras notifié(e) du calendrier     │
│ Affelnet à partir de mars.            │
│                                       │
│              [ Modifier ]             │
└──────────────────────────────────────┘
```

**Variante Léa post-bac en pause :**
```
┌──────────────────────────────────────┐
│ Post-bac • En pause                   │
│ Aucune formation actuellement         │
│                                       │
│ On t'aidera à découvrir des pistes,   │
│ à ton rythme.                         │
│                                       │
│              [ Modifier ]             │
└──────────────────────────────────────┘
```

**And** un bouton "Modifier" (tertiary) à droite de la card revient à l'état édition avec les valeurs pré-remplies (focus retourne sur le RadioGroup niveau)
**And** un bouton primary "Continuer vers les bulletins" en footer (full-width mobile, right-aligned desktop) confirme et redirige vers `/onboarding/step-3` (Story 2.3+)
**And** le récap **n'est PAS sautable** — c'est le rempart anti-erreur (Mehdi qui aurait cliqué "Pro" par erreur le voit ici). Le coût UX (1 tap de plus) est assumé.
**And** un PATCH est envoyé vers `/api/v1/students/me/onboarding/level` au passage du récap → step-3 (pas avant — le récap permet correction sans payload "polluant")

### AC7 — Persistence + reprise (cohérent avec Story 2.1)

**Given** je suis sur n'importe quelle branche (édition ou récap)
**When** je quitte l'app sans valider
**Then** mon état partiel est sauvegardé dans **localStorage** sous clé `onboarding_step2_draft` au moindre changement (debounce 500 ms sur toute mutation state)
**And** au retour sur `/onboarding/step-2`, le draft est rechargé prioritairement sur la réponse serveur (last-write-wins client jusqu'au flush PATCH au passage du récap)
**And** si la branche en cours dans le draft est **incomplète** (ex. niveau "1ère" sélectionné + 2 spés au lieu de 3), je reviens en **mode édition** (pas récap) avec la branche en cours pré-remplie + le focus sur le premier élément manquant + helper inline *"Il te manque une spé."*
**And** si le profil serveur indique `onboarding_step2_status === "completed"`, je suis redirigé directement vers `/onboarding/step-3` (parallèle Story 2.1 AC10)

### AC8 — Bouton "Plus tard" (skip global cohérent avec step-1)

**Given** je suis sur n'importe quelle branche ou sur le récap
**When** je tape sur "Plus tard" dans le header droit
**Then** une **`ConsentDialog`** (Story 1.14) s'ouvre avec :

- Title : *"Tu veux remettre ça à plus tard ?"*
- Description : *"Sans ton niveau scolaire, on ne peut pas adapter les recos à ta trajectoire ni te notifier du bon calendrier (Parcoursup ou Affelnet). Tu peux compléter à tout moment depuis ton profil — mais on t'enverra des recos plus génériques pour l'instant."*
- `dataMentioned` : `["Niveau scolaire", "Filière", "Spécialités (si applicable)"]`
- `duration` : *"Tu peux compléter à tout moment depuis ton profil"*
- `beneficiary` : *"Toi — c'est ton parcours, tu décides"*
- `acceptLabel` : *"Oui, plus tard"*
- `refuseLabel` : *"Je continue"*

**And** si l'élève confirme :

- L'état partiel éventuel est persisté côté serveur (le draft n'est pas perdu)
- L'élève est redirigé vers `/onboarding/step-3`
- `onboarding_step2_status = "skipped"` côté serveur
- Le moteur de reco downstream applique un **fallback de niveau "indéterminé"** (label *"estimation indicative — affine en ajoutant ton niveau"*, principe mode dégradé invisible)

### AC9 — Récap mis à jour côté reco / notifications après PATCH

**Given** un autre service consomme `onboarding_step2_status === "completed"` (ex. moteur reco Epic 3 ou worker notifications Epic 8)
**When** le PATCH a réussi côté serveur
**Then** le service publie un **événement domain `student_level_declared`** (via mécanisme à confirmer post-Story 1.8 : Postgres LISTEN/NOTIFY, ou Celery task, ou outbox pattern — décision dev) avec payload :

```json
{
  "student_id": "...",
  "level": "lycee_terminale",
  "filiere": "general",
  "specialites": ["mathematiques", "svt", "hggsp"],
  "intended_track": null,
  "declared_at": "ISO-8601"
}
```

**And** cet événement est **idempotent** (re-éditer le profil ré-émet l'événement avec le delta — le consumer downstream doit gérer la mise à jour)
**And** **côté audit log (Story 1.13)**, chaque `PATCH /api/v1/students/me/onboarding/level` enregistre :
- L'utilisateur (`student_id`)
- L'ancien et le nouveau payload (delta lisible)
- L'IP + user-agent
- Le `motive: "onboarding_step2"` ou `"profile_edit"` selon le contexte d'appel (param querystring sur le PATCH)

### AC10 — Accessibilité RGAA AA (cohérent avec Story 2.1)

**Given** l'écran 2.2 et toutes ses branches
**When** je teste avec clavier seul, lecteur d'écran, et `prefers-reduced-motion: reduce`
**Then** **tout est navigable au clavier** :

- `Tab` traverse dans l'ordre : skip link → back chevron → indicateur progression → bouton "Plus tard" → RadioGroup niveau (flèches haut/bas pour naviguer entre options, Espace ou Entrée pour sélectionner) → branche affichée (Tab continue à l'intérieur) → bouton "Continuer"
- Pas de focus trap fantôme (la branche qui apparaît à la sélection niveau est dans le flow tab linéaire, pas dans une modale)
- Sur le récap, focus initial sur le bouton "Modifier" ; bouton primary "Continuer vers les bulletins" en dernier dans le tab order
- `Esc` sur la `ConsentDialog` "Plus tard" ferme et appelle `onRefuse` (cf Story 1.14)

**And** **HTML sémantique** :

- L'indicateur de progression reproduit la structure de Story 2.1 (`<nav aria-label="Progression onboarding"><ol>` etc.)
- Le RadioGroup niveau est `<fieldset><legend>` + `<input type="radio">` natifs (ou `<RadioGroup>` shadcn qui le fait), un seul `tabindex=0` à la fois (le sélectionné), flèches naviguent
- Les sous-filières techno et spécialités lycée utilisent la même mécanique
- Les transitions de branche sont **annoncées via une zone `aria-live="polite"` SR-only** : *"Niveau 1ère sélectionné, choix de filière disponible."*
- Le récap est un `<section aria-labelledby="recap-heading">` avec heading h2

**And** **reduced motion** :

- Les transitions branche apparaît / disparaît collapsent à fade `~50 ms` (au lieu de slide + fade 200 ms)
- Le swap édition ↔ récap collapse à fade `~50 ms`
- Pas d'autre animation à neutraliser

**And** **touch targets** : tous RadioGroup items et chips respectent 44 × 44 px minimum (via padding vertical sur les cards)

**And** **annonces dynamiques** :

- À chaque sélection niveau : `aria-live` annonce le titre de la branche apparaissant (*"Choix de filière, 3 options disponibles"*)
- Sur compteur spés : *"Mathématiques sélectionné, 1 sur 3 spécialités à choisir."* puis *"3 sur 3 spécialités choisies, tu peux continuer."*
- Sur transition vers récap : *"Récap de tes informations scolaires. Vérifie avant de continuer."*

### AC11 — Édition ultérieure (lien vers Story 2.6)

**Given** je suis déjà passé(e) sur step-2 (`onboarding_step2_status === "completed"`)
**When** je rouvre `/onboarding/step-2` (URL directe, deeplink)
**Then** je suis redirigé vers `/onboarding/step-3` (continuation onboarding) — pas de re-édition possible par cette route
**And** le **point d'entrée canonique d'édition** est `/profile/edit/level` (Story 2.6), qui réutilise les **mêmes composants** que cet écran (factorisation à prévoir dans `apps/web/components/onboarding/LevelForm.tsx` réutilisé par les 2 routes)
**And** si la modification post-onboarding **change le niveau majeur** (ex. 3ème → Terminale = transition impossible IRL, ou Terminale → Post-bac = transition naturelle après bac), un **`ConsentDialog`** spécifique (Story 2.6) prévient des conséquences (recos réinitialisées, etc.)

---

## 3. Tasks / Subtasks

### T1 — Référentiels niveau / filières / spés (AC2-AC5)

- Créer `packages/copy/onboarding/levels.ts` exportant :

```ts
export const LEVELS: ReadonlyArray<{ id: NiveauId; label: string; description: string }> = [...];  // 5 entrées (AC2)
export const TRACKS_3EME = [...];  // 4 entrées (AC3)
export const FILIERES_LYCEE = [...];  // 3 entrées (AC4)
export const SOUS_FILIERES_TECHNO = [...];  // 7 sous-filières (AC4)
export const SPECIALITES_LYCEE = [...];  // 13 entrées (AC4)
export const POSTBAC_YEARS = [...];  // 6 entrées (AC5)
export const POSTBAC_FORMATIONS = [...];  // 9 entrées (AC5)
```

- IDs en kebab-case stable, labels modifiables sans migration
- Référentiel **versionné** (`REF_VERSION = "2026-05-v1"`) → stocké dans le profil pour audit longitudinal (si on change les libellés, on sait qui a déclaré avec quelle version)
- Tests unitaires : référentiels non-vides, IDs uniques, no orphan ID

### T2 — API backend : GET + PATCH `/api/v1/students/me/onboarding/level` (AC2-AC9)

- Modèle `StudentProfile` étendu (ou modèle dédié `OnboardingStep2` selon convention dev) avec colonnes :
  - `level VARCHAR(20)` — enum stricte côté serveur (`college_3eme | lycee_2nde | lycee_1ere | lycee_terminale | postbac`)
  - `filiere VARCHAR(10)` — enum (`general | techno | pro | null`)
  - `sous_filiere_techno VARCHAR(10)` — enum (cf AC4) ou null
  - `specialites JSONB DEFAULT '[]'` (array de string IDs, 0-3 entrées)
  - `intended_track VARCHAR(15)` — enum (`general | techno | pro | undecided | null`)
  - `postbac_year VARCHAR(15)` — enum (cf AC5) ou null
  - `postbac_formation_type VARCHAR(25)` — enum (cf AC5) ou null
  - `onboarding_step2_status VARCHAR(15) DEFAULT 'pending'` (`pending | in_progress | completed | skipped`)
  - `onboarding_step2_completed_at TIMESTAMPTZ`
  - `level_ref_version VARCHAR(20)` — pour audit longitudinal
- Migration Alembic avec backfill `'pending'`
- Validation Zod / pydantic côté serveur : cohérence entre `level` et les autres champs (ex. `level=college_3eme` impose `filiere=null`, `specialites=[]`, `intended_track` requis ; `level=lycee_terminale` + `filiere=general` impose `len(specialites) == 2`, etc.) — matrice complète testée
- Endpoint PATCH accepte payload **partiel pendant l'édition** mais valide la **cohérence complète au passage `completed`** (le récap UX → PATCH commit)
- Endpoint GET retourne l'état complet + `level_ref_version`
- RLS Story 1.8 appliqué
- **Audit log Story 1.13** : chaque PATCH enregistre delta + IP + UA + motive
- **Événement domain `student_level_declared`** publié au commit (AC9) — mécanisme à confirmer (LISTEN/NOTIFY ou Celery, voir avec dev en sprint planning)

### T3 — Frontend : écran `OnboardingStep2` (AC1-AC11)

- Route Next.js : `apps/web/app/(auth)/onboarding/step-2/page.tsx`
- Composant racine `<OnboardingStep2 />` orchestre l'état (`editing | recap`) + branch (`college | lycee | postbac | null`)
- Sous-composants extraits (factorisation pour Story 2.6) :
  - `<LevelForm />` — englobe niveau + branche correspondante (réutilisé par `/profile/edit/level`)
  - `<RecapCard />` — affiche le récap avec variantes par niveau
  - `<NiveauPicker />` — RadioGroup 5 options
  - `<Branche3eme />`, `<BrancheLycee />`, `<BranchePostbac />` — chacun sa logique de validation
  - `<SpecialitesPicker />` — chips multi-select cible 2 ou 3 selon contexte
  - `<SkipDialog />` — réutilise `ConsentDialog` Story 1.14 (factoriser avec Story 2.1 SkipDialog si copy identique → composant unique)
- React Hook Form + Zod resolver pour validation cohérence
- `useLocalStorageDraft('onboarding_step2_draft')` (factoriser avec Story 2.1)
- Pré-fetch GET au mount + skeleton
- Redirection step-3 si déjà `completed` (AC11)

### T4 — Tests (front + back)

- **Backend (pytest)** :
  - GET initial vide / partiel / complete
  - PATCH cohérence : 3ème sans `intended_track` → 400 ; Terminale général avec 3 spés → 400 (Terminale = 2 spés) ; Terminale général avec 2 spés non dans référentiel → 400
  - PATCH partial ne wipe pas les autres champs OK
  - RLS bloque cross-tenant
  - Audit log enregistré + événement domain émis (mock)
- **Frontend (Vitest + RTL)** :
  - Render initial : RadioGroup niveau visible, branche absente
  - Sélection 3ème → branche `Branche3eme` apparaît, bouton continue disabled tant que pas `intended_track`
  - Sélection 1ère → général → 3 spés requises, compteur fonctionne
  - Récap affiche bons champs selon variante (snapshot des 3 personas)
  - Skip dialog → PATCH + redirect step-3
  - Reduced motion : transitions branche < 80 ms
- **E2E (Playwright)** :
  - Sarah Terminale : niveau → général → 3 spés → récap → continue (en < 60 s simulés)
  - Mehdi 3ème → bac pro → récap (vérifie absence de bandeau encouragement)
  - Léa post-bac → pause → aucune formation → récap → continue
  - Test screenshot Mehdi vs Sarah récap : visuellement indiscernable (même structure)
- **A11y (axe-core)** : chaque branche passe sans nouvelle violation
- **Manuel** : VoiceOver iOS + NVDA Windows sur les 3 variantes (cf NFR-A1)

### T5 — Documentation

- `docs/onboarding/step2-level.md` : flow visuel branching + matrice référentielle + copy variants
- Mise à jour `_bmad-output/planning-artifacts/ux-design-specification.md` § Components — `OnboardingStep2` (+ sa factorisation `LevelForm` réutilisée par Story 2.6) ajouté
- `docs/a11y/onboarding-step2.md` : checklist VoiceOver/NVDA

---

## 4. Dev Notes

### 4.1 Wireframes ASCII — état initial (niveau non sélectionné), mobile 375 px

```
┌─────────────────────────────────────────┐
│ <  ● ● ○                       Plus tard │
├─────────────────────────────────────────┤
│                                          │
│  Où tu en es, scolairement ?            │
│  Pour qu'on t'envoie les bonnes infos   │
│  au bon moment.                          │
│                                          │
│  ┌─────────────────────────────────────┐│ ← RadioGroup card lg
│  │ 3ème                                ││   h 56 min, touch target
│  │ Année d'orientation (Affelnet,      ││   border color-border
│  │ choix lycée)                        ││   radio dot droite
│  └─────────────────────────────────────┘│
│  ┌─────────────────────────────────────┐│
│  │ 2nde                                ││
│  │ Découverte des matières, choix de   ││
│  │ spés à venir                        ││
│  └─────────────────────────────────────┘│
│  ┌─────────────────────────────────────┐│
│  │ 1ère                                ││
│  │ Première année de spés, Bac Français││
│  └─────────────────────────────────────┘│
│  ┌─────────────────────────────────────┐│
│  │ Terminale                           ││
│  │ Année de Parcoursup, Bac complet    ││
│  └─────────────────────────────────────┘│
│  ┌─────────────────────────────────────┐│
│  │ Post-bac                            ││
│  │ Tu as déjà ton bac, tu cherches une ││
│  │ (ré)orientation                     ││
│  └─────────────────────────────────────┘│
│                                          │
├─────────────────────────────────────────┤
│  ┌────────────────────────────────────┐ │
│  │     Continuer      →    (disabled) │ │
│  └────────────────────────────────────┘ │
│  Choisis ton niveau pour continuer.     │
└─────────────────────────────────────────┘
```

### 4.2 Wireframes ASCII — branche Terminale → général → spés (Sarah)

```
┌─────────────────────────────────────────┐
│ <  ● ● ○                       Plus tard │
├─────────────────────────────────────────┤
│                                          │
│  Où tu en es, scolairement ?            │
│  ┌─────────────────────────────────────┐│
│  │ Terminale                         ✓ ││ ← sélectionné, brand
│  │ Année de Parcoursup, Bac complet    ││
│  └─────────────────────────────────────┘│
│  (4 autres cards niveau, non sélec)     │
│                                          │
│  Ta filière au lycée                    │ ← branche apparue (motion-quick)
│  ┌─────────────────────────────────────┐│
│  │ Bac général                       ✓ ││
│  └─────────────────────────────────────┘│
│  ┌─────────────────────────────────────┐│
│  │ Bac techno                          ││
│  └─────────────────────────────────────┘│
│  ┌─────────────────────────────────────┐│
│  │ Bac pro                             ││
│  └─────────────────────────────────────┘│
│                                          │
│  Tes spécialités (2 à choisir)          │ ← sous-branche
│  ┌─────┐ ┌─────────┐ ┌─────┐ ┌──────┐  │ ← chips multi-select
│  │ ✓Math│ │Physique-│ │ SVT │ │ SES  │  │   compteur en bas
│  │  s   │ │ Chimie  │ │     │ │      │  │
│  └─────┘ └─────────┘ └─────┘ └──────┘  │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌────┐    │
│  │✓HGGSP│ │ HLP  │ │LLCER │ │LLCA│    │
│  └──────┘ └──────┘ └──────┘ └────┘    │
│  ┌─────┐ ┌────┐ ┌────┐ ┌──────┐       │
│  │ NSI │ │Arts│ │ SI │ │Bio-éco│      │
│  └─────┘ └────┘ └────┘ └──────┘       │
│  ┌──────┐                              │
│  │EPPCS │                              │
│  └──────┘                              │
│                       2 / 2 sélection ✓ │
│                                          │
├─────────────────────────────────────────┤
│  ┌────────────────────────────────────┐ │
│  │         Continuer            →     │ │ ← enabled
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### 4.3 Wireframes ASCII — branche 3ème → bac pro (Mehdi)

```
┌─────────────────────────────────────────┐
│ <  ● ● ○                       Plus tard │
├─────────────────────────────────────────┤
│                                          │
│  Où tu en es, scolairement ?            │
│  ┌─────────────────────────────────────┐│
│  │ 3ème                              ✓ ││ ← sélectionné
│  │ Année d'orientation (Affelnet,      ││
│  │ choix lycée)                        ││
│  └─────────────────────────────────────┘│
│  (4 autres cards niveau, non sélec)     │
│                                          │
│  Et après la 3ème, tu vises plutôt quoi ?│ ← branche
│  Tu peux changer plus tard, t'inquiète. │
│  ┌─────────────────────────────────────┐│
│  │ Bac général                         ││
│  │ Filière classique, suite naturelle  ││
│  │ si tu vises des études longues      ││
│  └─────────────────────────────────────┘│
│  ┌─────────────────────────────────────┐│
│  │ Bac techno                          ││
│  │ Filières STMG / STI2D / ST2S / etc.,││
│  │ entre théorie et concret            ││
│  └─────────────────────────────────────┘│
│  ┌─────────────────────────────────────┐│
│  │ Bac pro                          ✓  ││ ← sélectionné par Mehdi
│  │ Apprendre un métier en formation,   ││   pas de bandeau, pas
│  │ souvent en alternance               ││   d'icône d'encouragement
│  └─────────────────────────────────────┘│
│  ┌─────────────────────────────────────┐│
│  │ Pas encore décidé                   ││
│  │ Pas de pression, on garde les       ││
│  │ options ouvertes — tes recos        ││
│  │ incluront tout.                     ││
│  └─────────────────────────────────────┘│
│                                          │
├─────────────────────────────────────────┤
│  ┌────────────────────────────────────┐ │
│  │         Continuer            →     │ │ ← enabled
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### 4.4 Wireframes ASCII — récap (Sarah Terminale général)

```
┌─────────────────────────────────────────┐
│ <  ● ● ○                       Plus tard │
├─────────────────────────────────────────┤
│                                          │
│  Voilà ce que tu as déclaré              │
│  Tu peux modifier avant de continuer.   │
│                                          │
│  ┌─────────────────────────────────────┐│ ← Card shadcn
│  │ Terminale • Bac général             ││   text-body weight 600
│  │                                     ││
│  │ Tes spécialités :                   ││ ← text-body-sm muted
│  │   • Mathématiques                   ││ ← text-body
│  │   • HGGSP                           ││
│  │                                     ││
│  │ Tu seras notifié(e) du calendrier   ││ ← text-body-sm subtle
│  │ Parcoursup à partir de novembre.    ││
│  │                                     ││
│  │                       [ Modifier ]  ││ ← tertiary droite
│  └─────────────────────────────────────┘│
│                                          │
├─────────────────────────────────────────┤
│  ┌────────────────────────────────────┐ │
│  │  Continuer vers les bulletins  →   │ │ ← primary lg
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### 4.5 Matrice complète niveau × filière × spés (référence dev)

| Level             | Filiere | Sous-filière techno | Spés attendues  | intended_track | postbac_year | postbac_formation_type |
|-------------------|---------|---------------------|-----------------|----------------|--------------|------------------------|
| `college_3eme`    | null    | null                | []              | required       | null         | null                   |
| `lycee_2nde`      | general | null                | []              | null           | null         | null                   |
| `lycee_2nde`      | techno  | null                | []              | null           | null         | null                   |
| `lycee_2nde`      | pro     | null                | [1 spé bac pro] | null           | null         | null                   |
| `lycee_1ere`      | general | null                | [3 spés lycée]  | null           | null         | null                   |
| `lycee_1ere`      | techno  | required            | []              | null           | null         | null                   |
| `lycee_1ere`      | pro     | null                | [1 spé bac pro] | null           | null         | null                   |
| `lycee_terminale` | general | null                | [2 spés lycée]  | null           | null         | null                   |
| `lycee_terminale` | techno  | required            | []              | null           | null         | null                   |
| `lycee_terminale` | pro     | null                | [1 spé bac pro] | null           | null         | null                   |
| `postbac`         | null    | null                | []              | null           | required     | required               |

**Validation à appliquer côté serveur au passage `completed`** : cette matrice exacte. Toute autre combinaison → HTTP 400 avec message d'erreur structuré.

### 4.6 État émotionnel à chaque branche — référentiel copy review

| Branche | État d'entrée probable | Cible émotionnelle | Triggers à bannir |
|---|---|---|---|
| **3ème** (Mehdi) | Méfiance ("Le système va me forcer vers un truc") | Calme, autonomie ("Je décide, on me prend pas de haut") | "Voie pro = aussi bien", icônes encouragement, bandeau différencié |
| **Lycée 2nde / 1ère** (transition Sarah-3 ans) | Doute spés ("Et si je me trompe ?") | Confidence avec porte de sortie ("Je peux changer plus tard") | Validation cérémonieuse, "Tes spés définitives !" |
| **Lycée Terminale** (Sarah) | Pression Parcoursup en arrière-plan | Brièveté, pas de drame ("Tac, c'est dit") | Compte à rebours Parcoursup, anxiété fabriquée |
| **Post-bac en pause** (Léa) | Stigma ressenti ("Je suis pas dans la norme") | Normalisation pleine ("C'est une réponse comme une autre") | "Pourquoi tu es en pause ?", icônes triste / interrogative, ton paternaliste |

### 4.7 Edge cases et failures explicites

| Edge case | Comportement attendu | AC ref |
|---|---|---|
| Élève sélectionne niveau A, branche A s'affiche, clique niveau B sans valider A | Branche A disparaît (fade out 80 ms), branche B apparaît (fade in 200 ms), draft updated | AC2 |
| Élève sélectionne 1ère → général → coche 4 spés au lieu de 3 | 4ème chip rejetée à la sélection, helper `color-warning` *"Maximum 3 spécialités."* + chip non sélectionné, **pas** un toast | AC4 |
| Élève sélectionne 1ère → techno mais ne choisit pas sous-filière | Bouton Continuer disabled, helper *"Précise ta sous-filière techno."* | AC4 |
| Élève sélectionne post-bac → "En pause" + "Aucune formation actuellement" | OK valide, profil enregistré, **pas** de message culpabilisant | AC5 |
| Élève passe au récap puis clique "Modifier" 3 fois de suite | OK, état édition stable, chaque retour récap → édition → récap conserve l'état | AC6 |
| PATCH échoue (réseau ou 5xx) au passage récap → step-3 | Draft conservé localStorage, toast info *"Pas de réseau, on enregistre quand tu reviens."*, l'élève reste sur récap | AC7 |
| Session JWT expire entre édition et récap | Redirect `/login?return_to=/onboarding/step-2`, draft réappliqué | AC7 |
| Élève modifie son niveau après onboarding (via Story 2.6) Terminale → Post-bac | `ConsentDialog` confirme + recos réinitialisées (Story 2.6 handle), événement `student_level_declared` ré-émis | AC11 |
| Référentiel `level_ref_version` évolue côté serveur entre 2 sessions | Front affiche les nouveaux libellés (référentiel TS chargé build-time), profil garde l'ancienne version dans `level_ref_version` pour audit. Pas de migration des données stockées. | T1, T2 |
| Lecteur d'écran VoiceOver, sélection 1ère → techno | Annonce *"1ère sélectionné, choix de filière. Bac techno sélectionné, choix de sous-filière disponible."* puis liste sous-filières | AC10 |
| Reduced motion actif, transitions branche | Fade ~50 ms au lieu de slide + fade 200 ms, état final identique | AC10 |
| Élève ouvre l'app en mode "Plus tard skipped" sur step-2 (`status === "skipped"`) puis revient via URL `/onboarding/step-2` | Charge l'écran normalement en mode édition vide (draft localStorage flush au skip), permet de compléter sans cérémonie | AC8 |
| Élève en plein bug navigateur sélectionne 2 spés à 1 milliseconde d'intervalle | Le second click win race condition côté React state (setState idempotent), pas de double sélection | AC4 |

### 4.8 Décisions design verrouillées

- **Récap obligatoire avant step-3** — anti-erreur Mehdi (clic accidentel "bac pro" / "bac général") et anti-erreur Sarah (mauvaise spé cochée). Le coût UX (1 tap supplémentaire) est assumé.
- **Branche apparaît à la sélection niveau, pas après "Confirmer niveau"** — décision : économise un bouton intermédiaire, optimise pour Sarah (parcours rapide). La validation finale est au récap.
- **Pas de "wizard" multi-pages** — toute la branche se déroule sur la même page, scroll vertical. Cohérent avec Story 2.1.
- **Référentiel 13 spés lycée général** : liste officielle Éducation Nationale **2026** — à vérifier sprint review, peut évoluer si une spé est ajoutée/supprimée
- **Sous-filière techno = sélection requise même en 1ère** — décision : pertinence reco, on ne peut pas suggérer un BUT MMI à un STMG sans le savoir
- **"Pas encore décidé" en 3ème** — option **inclusive**, traitée identique aux autres visuellement. C'est la plus utile pour Mehdi et les ados de 14 ans qui n'ont pas encore décidé.
- **Pas de bouton "Précédent" entre branches** — comme step-1, si l'élève veut revenir au niveau, il clique sur un autre niveau ou re-clique sur le même (no-op idempotent)
- **Référentiel versionné `level_ref_version`** — décision : trace longitudinale pour audit si on change le libellé d'une spé en cours d'année (ex. "HGGSP" devient "Histoire-Géo, Géopolitique"). Permet de re-construire l'écran tel qu'il était vu par l'élève à sa déclaration.
- **PATCH au récap, pas avant** — le draft localStorage pendant édition couvre la perte ; le PATCH commit au récap → step-3 commit limite les payloads "polluants" côté serveur (un seul événement domain `student_level_declared` par session).

### 4.9 Versions et libraries à utiliser

(Cohérent avec Story 2.1 et écosystème global)

- React 19, Next.js 15, TypeScript 5.x
- shadcn/ui composants : `Button`, `Card`, `RadioGroup`, `Toggle`, `Select`, `Dialog` (via `ConsentDialog` Story 1.14), `Skeleton`, `Toast`, `Label`, `Separator`
- React Hook Form 7.x + Zod 3.x (validation cohérence matrice AC4)
- TanStack Query 5.x
- Lucide React (`Check`, `X`, `ChevronLeft`, `Edit`, `Info`)
- Vitest + RTL + Playwright + axe-core (idem Story 2.1)
- Backend : Django/DRF ou FastAPI selon Story 1.1 (à confirmer post-merge 1.8) + Alembic + pytest

### 4.10 Items à différer (`deferred-work.md` post-merge)

- Édition différée du niveau scolaire post-onboarding — Story 2.6 dédiée
- Détection automatique du niveau via OCR bulletin (Story 2.3) — fast-follow, MVP demande à l'élève
- Référentiel sous-filières techno **détaillé** (séries spécifiques STMG : option Gestion-Finance / Marketing / etc.) — MVP s'en tient à la série principale, sous-séries en fast-follow
- Multi-langue référentiel — i18n Epic 7
- Estimation auto de la **promo cible** (`year_of_baccalaureat`) calculée depuis `level` + `today` — utile pour notifications Parcoursup mais pas critique MVP, on l'ajoute si reco le demande

---

## 5. Project Structure Notes

**Files à créer/modifier (estimation indicative) :**

```
apps/web/
  app/(auth)/onboarding/step-2/
    page.tsx
    OnboardingStep2.tsx
    LevelForm.tsx                  ← réutilisé par Story 2.6 (édition profil)
    NiveauPicker.tsx
    Branche3eme.tsx
    BrancheLycee.tsx
    BranchePostbac.tsx
    SpecialitesPicker.tsx
    RecapCard.tsx                  ← variantes par niveau
    SkipDialog.tsx                 ← peut factoriser avec Story 2.1
    useOnboardingStep2.ts
    __tests__/
      OnboardingStep2.test.tsx
      LevelForm.test.tsx
      Branche*.test.tsx
      RecapCard.snapshot.test.tsx
      a11y.spec.ts
  e2e/
    onboarding-step2.spec.ts

packages/
  copy/onboarding/
    levels.ts                      ← référentiels (T1)
    specialites.ts
    postbac.ts
    __tests__/snapshots.test.ts

apps/api/apps/students/             ← ou équivalent post-Story 1.8
  models.py                         ← extensions colonnes (T2)
  views_onboarding_level.py
  serializers_onboarding_level.py
  domain_events.py                  ← student_level_declared (AC9)
  migrations/
    NNNN_onboarding_step2_fields.py
  tests/
    test_onboarding_step2.py
    test_level_validation_matrix.py

docs/onboarding/
  step2-level.md                    ← documentation flow + matrice
docs/a11y/
  onboarding-step2.md
```

**Conventions à respecter :**

- Tokens CSS uniquement (Story 1.2)
- TanStack Query pour data fetching (Story 1.3)
- HTML sémantique d'abord (UX spec a11y)
- **Factorisation `LevelForm`** : ce composant doit être utilisable depuis **2 routes** (onboarding `/onboarding/step-2` et profil `/profile/edit/level`) **sans branching interne** sur la route — le contexte est passé en prop (`mode: "onboarding" | "profile_edit"`). C'est une vraie convention à respecter, pas un détail.

---

## 6. References

- **UX spec globale** : `_bmad-output/planning-artifacts/ux-design-specification.md`
  - § Experience Principles (#4 mode normal = mode dégradé — pivot Mehdi)
  - § Form Patterns (multi-step, RadioGroup, branching)
  - § Button Hierarchy
  - § Motion System
  - § Accessibility Strategy
  - § Anti-patterns proscrits (notamment "mode dégradé visible")
- **Epic 2 detail** : `_bmad-output/planning-artifacts/epics/epic-2-profil-eleve-onboarding.md` § Story 2.2
- **Story 2.1** : `_bmad-output/implementation-artifacts/2-1-onboarding-passions-interets-valeurs.md` — pattern cohérent (header / progress / Plus tard / persistence)
- **Story 1.2 (tokens)** : `_bmad-output/implementation-artifacts/1-2-design-system-tokens.md`
- **Story 1.14 (ConsentDialog)** : `_bmad-output/implementation-artifacts/1-14-composant-consent-dialog.md`
- **Story 1.8 (RLS)** : `_bmad-output/implementation-artifacts/1-8-multi-tenant-rls-postgresql.md`
- **Story 1.13 (audit log)** : `_bmad-output/implementation-artifacts/1-13-journal-audit-acces.md`
- **PRD** : `_bmad-output/planning-artifacts/prd/` — FR16 (niveau), FR25 (spés), FR31 (Affelnet vs Parcoursup), UX-DR30 (vocab par niveau)
- **Story 2.6 (édition profil)** : à venir, consommera `LevelForm.tsx` factorisé
- **Epic 8 (notifications calendrier)** : `_bmad-output/planning-artifacts/epics/epic-8-continuite-temporelle-notifications.md` — consomme `intended_track` et `level` pour Parcoursup vs Affelnet

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

- 2026-05-24 — Story 2.2 contextée et passée en `ready-for-dev` par Marwen + Claude (Opus 4.7) dans le cadre du démarrage parallèle UX Epic 2 pendant que Epic 1 finit (Stories 1.5 / 1.7 / 1.8 / 1.11 / 1.12 encore en cours).

---

## 8. Senior Developer Review (AI)

**Review date:** 2026-06-20
**Outcome:** Changes Requested
**Reviewers:** Blind Hunter + Edge Case Hunter + Acceptance Auditor (Claude Opus, parallel adversarial)
**Raw findings:** 41 → after triage: 5 HIGH, 12 MEDIUM, 12 LOW (29 total), 8 dismissed

### Action Items

#### ✅ Applied patches (15)

- [x] [Review][Patch] Guard completed profile — stale tab no-op replaced by early return [views.py]
- [x] [Review][Patch] Event transition-gated — student_level_declared only on real PENDING→COMPLETED [views.py]
- [x] [Review][Patch] Stale branch fields normalized on commit (matrix consistency) [serializers.py]
- [x] [Review][Patch] Duplicate specialite IDs rejected [serializers.py:validate_specialites]
- [x] [Review][Patch] 2nde général non-empty specialites rejected (expected=None branch) [serializers.py:validate]
- [x] [Review][Patch] declared_at added to Celery event payload (AC9) [tasks.py]
- [x] [Review][Patch] mark_skipped clears completed_at [models.py]
- [x] [Review][Patch] tenant_id stamped at creation, not lazy in save() [views.py:_get_or_create]
- [x] [Review][Patch] draftKeyFor returns null when userId undefined (no shared-key leak) [use-onboarding-step-2.ts]
- [x] [Review][Patch] readDraft validates shape before trusting parsed JSON [use-onboarding-step-2.ts]
- [x] [Review][Patch] toggleSpecialite guards null level + null expected treated as 0-cap [use-onboarding-step-2.ts]
- [x] [Review][Patch] div onClick removed from card rows → Label wrapper (keyboard a11y, no double-fire) [niveau-picker, branche-3eme, branche-lycee]
- [x] [Review][Patch] commitLevel network error surfaced with role=alert [onboarding-step-2.tsx]
- [x] [Review][Patch] continueHelper spés hint only when expectedSpecCount != null [onboarding-step-2.tsx]
- [x] [Review][Patch] RecapCard React key uses spec id not display label [recap-card.tsx]

### Review Follow-ups (AI) — decision needed

- [x] [Review][Decision] #16 HIGH — localStorage fallback key when userId undefined now returns null (applied with patch #11); skip/saveDraft userId-undefined paths verified safe
- [x] [Review][Decision] #17 HIGH — AC9 audit log deferred to Epic 3 / Story 1.13 (explicit sprint decision: out of scope for 2.2)
- [x] [Review][Decision] #18 MEDIUM — outbox/DLQ deferred to Epic 3 (transactional outbox pattern not in 2.2 scope)
- [x] [Review][Decision] #19 MEDIUM — ordering guard added: PATCH returns 400 if StudentProfile doesn't exist; tests updated with with_step1 fixture
- [x] [Review][Decision] #20 MEDIUM — OnboardingStep2ReadSerializer.get_specialites() filters unknown IDs against SPECIALITE_IDS | SPECIALITE_PRO_IDS
- [x] [Review][Decision] #21 MEDIUM — AC8: skip now persists non-null draft fields server-side before mark_skipped()
- [x] [Review][Decision] #22 MEDIUM — AC1: back chevron wrapped with ConsentDialog anti-perte guard (backOpen state)
- [x] [Review][Decision] #23 LOW — skip+commit mutual exclusion: serializer raises 400 when both true
- [x] [Review][Decision] #24 LOW — AC11 server-side: stale-tab guard in views.py returns current snapshot on non-commit PATCH to completed profile
- [x] [Review][Decision] #25 LOW — LevelForm refactor deferred (no /profile/edit/level route yet in current sprint)
- [x] [Review][Decision] #26 LOW — AC7: localStorage-only draft acceptable for now; server-draft already works via PATCH (confirmed)
- [x] [Review][Decision] #27 LOW — level_ref_version now server-stamped from CURRENT_REF on commit
- [x] [Review][Decision] #28 LOW — AC10: aria-live announcer now includes branch option count (BRANCH_OPTION_COUNT map)
- [x] [Review][Decision] #29 LOW — AC4: bac pro single-mandatory spec kept as capped chip (chips UX equivalent, noted in story)
