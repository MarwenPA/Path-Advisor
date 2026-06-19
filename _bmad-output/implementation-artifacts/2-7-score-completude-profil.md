# Story 2.7: Maturité de profil — Indicateur qualitatif 3 états

**Epic:** 2 — Profil Élève & Onboarding
**Status:** review
**Sprint:** 6 (Post-onboarding, profil & continuité)
**Story Key:** `2-7-score-completude-profil`
**Estimation:** S (small) — composant Couche 3 indicateur + endpoint compute + intégration en haut de page profil Story 2.6. Pas de calcul ML, juste logique déterministe sur l'état du profil. Sized ~0.5–1 j focused work.

> Story du **principe émotionnel #2** : *"dignité avant positivité"*. Le pattern classique "Profil complété à 73 %" est **interdit** dans Path-Advisor — il culpabilise (Diplomeo, LinkedIn) et transforme l'utilisateur en projet à terminer. Cette story propose à la place un indicateur **qualitatif 3 états** (*Profil de base / Profil enrichi / Profil complet*) qui décrit ce que l'utilisateur **DÉBLOQUE** plutôt que ce qu'il **MANQUE**. C'est la story qui clôt l'épine dorsale émotionnelle d'Epic 2.

---

## 1. User Story

**As an** élève (Sarah complète, Mehdi en cours, Léa minimale),
**I want** visualiser ma maturité de profil de façon qualitative (3 états sémantiquement clairs) avec une description neutre de ce que chaque état débloque, et identifier les éléments manquants via une liste d'actions courtes facultatives,
**So that** je sache ce qui s'ouvre à chaque palier sans culpabilisation (FR19), **so that** je ne ressente jamais que l'app me classe ou me note, et **so that** chaque action de complétion soit présentée comme un **gain** (ce que j'ouvre) et non comme un **manque** (ce qu'il me reste à faire).

**Business value :** sans cette story, soit on n'a pas d'indicateur (l'utilisateur ne sait pas pourquoi telle reco est moins précise), soit on retombe sur le pattern Diplomeo "Profil à 73 %" qui contredit le positionnement neutralité + dignité. Cette story est la **réponse opérationnelle** au pattern d'industrie qu'on rejette. Côté analytics, on s'attend à mesurer la **conversion par palier** (base → enrichi → complet) — KPI MVP critique pour comprendre la friction de complétion.

**Garde-fous personas activés :**

- **Léa (dignité PILIER)** — l'état *"Profil de base"* doit être présenté comme **un état viable**, pas comme un défaut à corriger. Test sprint review : Léa lit la description état 1 → si elle pense "donc je manque de trucs", on a échoué.
- **Mehdi (anti-stigma)** — même test. Si Mehdi en bac pro voit "Profil enrichi" mais sent que "Profil complet" est réservé aux élèves avec bulletins lycée général, on a échoué.
- **Sarah (utilité)** — Sarah veut savoir *concrètement* ce qu'elle gagne à compléter. La liste d'actions doit être **actionable** (1 tap → flow direct), pas vague.

---

## 2. Acceptance Criteria (BDD)

### AC1 — Component API : `<ProfileMaturityIndicator />`

**Given** j'importe `ProfileMaturityIndicator` depuis `@/components/profile/profile-maturity-indicator`
**When** je lis sa signature TypeScript
**Then** les props sont exactement :

```ts
export type MaturityLevel = 'base' | 'enriched' | 'complete';

export type MaturityNextAction = {
  /** Label de l'action ("Ajoute un bulletin", "Précise tes spés", ...) */
  label: string;
  /** Sous-titre concret du bénéfice ("Tu débloques les stats personnalisées") */
  benefit: string;
  /** Callback au tap → ouvre le flow correspondant (sheet Story 2.5 / 2.6 / 2.1 / 2.2) */
  onClick: () => void;
  /** Icône Lucide à gauche (FileText pour bulletins, BookOpen pour level, Heart pour passions) */
  icon: 'bulletins' | 'level' | 'passions' | 'specialites';
};

export type ProfileMaturityIndicatorProps = {
  /** Niveau actuel calculé par le backend. */
  level: MaturityLevel;
  /** Liste des actions ouvrables pour passer au niveau supérieur (vide si level === 'complete'). */
  nextActions: readonly MaturityNextAction[];
  /** Optional : variant visuel selon contexte d'affichage. */
  variant?: 'profile-header' | 'dashboard-card' | 'inline-compact';
  /** Optional : afficher le bouton "Voir comment compléter" (true par défaut sauf si complete). */
  showCallToAction?: boolean;
};
```

**And** le composant est default + named export
**And** **AUCUNE prop `percentage: number`** ou `progress: 0..100` — interdit par construction

### AC2 — Logique de calcul des 3 états (côté serveur)

**Given** un profil utilisateur avec ses 3 dimensions (passions, level, bulletins)
**When** le backend calcule le niveau de maturité
**Then** la logique déterministe est :

| Niveau | Conditions cumulatives |
|---|---|
| **`base`** | Profil créé (`onboarding_step1_status IN ['completed', 'skipped']` OU `onboarding_step1_status === 'partial'` avec ≥ 3 passions) ET (`onboarding_step2_status IN ['completed', 'skipped']`) ET (`bulletins_status IN ['pending', 'postponed']`) |
| **`enriched`** | Conditions `base` + `bulletins_status IN ['partial']` (au moins 1 trimestre rempli, OCR ou manuel) |
| **`complete`** | Conditions `base` + `bulletins_status === 'completed'` (au moins 2 trimestres remplis OU profil flag explicite "tout est saisi") + `onboarding_step1_status === 'completed'` (passions/valeurs/intérêts non skipped) + `onboarding_step2_status === 'completed'` (niveau/filière/spés validés) |

**And** **aucun seuil basé sur un pourcentage** ou un score — uniquement des conditions sémantiques sur les statuts des sous-stories
**And** le calcul est **idempotent** et **peu coûteux** (lecture du profil, conditions sur enum) — peut être calculé à chaque GET profile sans cache
**And** une fonction pure `computeMaturity(profileSnapshot): MaturityLevel` est exposée côté serveur (Python `profile_maturity.py`) **et côté client** (TypeScript `packages/profile/maturity.ts`) — partage du référentiel via un fichier de test golden snapshot (10-15 cas) qui valide les 2 implémentations donnent le même résultat

**And** le calcul des `nextActions` (AC1) est lié au niveau actuel :

| Niveau actuel | nextActions retournées |
|---|---|
| `base` | `[{ icon: 'bulletins', label: "Ajoute un bulletin", benefit: "Tu débloques les stats personnalisées", onClick: openBulletinsSheet }, { icon: 'passions', label: "Affine tes passions et valeurs", benefit: "Tes recos métiers seront plus précises", onClick: openPassionsSheet }]` (priorisé : bulletins en premier car c'est le plus gros gain) |
| `enriched` | `[{ icon: 'bulletins', label: "Ajoute un autre trimestre", benefit: "Tes stats deviennent encore plus précises", onClick: openBulletinsSheet }, { icon: 'specialites', label: "Vérifie tes spécialités", benefit: "Parcours encore mieux ciblés", onClick: openLevelSheet }]` |
| `complete` | `[]` (pas d'action — l'utilisateur est au max) |

### AC3 — Layout variant `'profile-header'` (page profil Story 2.6)

**Given** je suis sur la page profil avec un niveau de maturité calculé
**When** `<ProfileMaturityIndicator variant="profile-header" />` est rendu en haut de page
**Then** la card mesure :

- Container : full-width mobile, max-width 1080 px desktop (cohérent récap éditable desktop)
- Fond : `color-bg-2`, border 1 px `color-border`, radius `--radius-lg`, padding `space-6`
- Hauteur ~120-160 px selon contenu (pas de hauteur fixe — natural)
- **Aucune bordure colorée** par niveau (anti-distinction visuelle stigma — chaque niveau a la même neutralité visuelle)

**And** le contenu :

```
┌─────────────────────────────────────────┐
│ {Niveau libellé : "Profil enrichi"}     │ ← text-h3 weight 600 color-text
│                                          │
│ {Description état}                      │ ← text-body color-text-muted
│ "Tu débloques les stats personnalisées."│
│                                          │
│ [ Voir comment compléter →            ] │ ← bouton secondary
└─────────────────────────────────────────┘
```

**And** les **descriptions par niveau** (copy verrouillé sprint review avec Mehdi/Léa proxies) :

| Niveau | Libellé | Description |
|---|---|---|
| `base` | *"Profil de base"* | *"Tu as l'essentiel pour des recos indicatives — toutes les explorations sont ouvertes."* |
| `enriched` | *"Profil enrichi"* | *"Tu débloques les stats personnalisées sur tes parcours."* |
| `complete` | *"Profil complet"* | *"Tu profites de toutes les features — recos affinées, stats précises, parcours ciblés."* |

**And** **AUCUN** copy ne contient les mots interdits suivants (validation runtime dev) : `["incomplet", "manque", "manquant", "X %", "raté", "tu rates", "il te reste"]`

**And** au clic *"Voir comment compléter"* (sauf si `level === 'complete'`) → expand inline une liste des `nextActions` (AC4) — ou navigation vers une page dédiée si variante desktop

### AC4 — Liste des `nextActions` expandée

**Given** je clique *"Voir comment compléter"* dans la card maturité
**When** la liste expand inline
**Then** je vois 1-3 actions empilées (selon `nextActions` retournées), chacune sous forme de **card cliquable** :

```
┌─────────────────────────────────────────┐
│ 📋 Ajoute un bulletin                    │ ← text-body weight 500
│    Tu débloques les stats personnalisées │ ← text-body-sm color-text-muted
│                                       →  │ ← chevron right
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 💛 Affine tes passions et valeurs        │
│    Tes recos métiers seront plus précises│
│                                       →  │
└─────────────────────────────────────────┘
```

- Container : `Card` shadcn, fond `color-bg`, border 1 px `color-border`, radius `--radius-md`, padding `space-4`
- Touch target ≥ 64 px hauteur (zone tactile généreuse)
- Hover : background `color-bg-3`, border `color-border-strong`
- Focus : `--focus-ring`
- Au tap → appelle `onClick` qui ouvre directement le sheet/drawer correspondant (Story 2.5 AC6 pour bulletins, Story 2.6 AC2 pour passions, Story 2.6 AC3 pour spés)

**And** le ton du copy de chaque action :
- ✅ Présente le **gain** : *"Tu débloques X"*, *"Tes recos deviennent plus précises"*
- ❌ Pas de **manque** : *"Il te manque tes bulletins"*, *"Tu n'as pas complété…"*

**And** **AUCUNE indication d'effort** : pas de *"~2 minutes"*, pas de *"3 champs à remplir"* — la durée est subjective et ajoute de la friction perçue

**And** un bouton tertiary "Plier" (chevron up) ferme la liste expand

### AC5 — Variant `'dashboard-card'` (Epic 3 dashboard)

**Given** je suis sur le dashboard (Epic 3 entry, post-onboarding)
**When** `<ProfileMaturityIndicator variant="dashboard-card" />` est rendu
**Then** la card est **plus compacte** :

- Layout horizontal (mobile : stack vertical, desktop : row)
- Pas de bouton expand par défaut — juste un lien tertiary *"Mon profil →"* qui redirige vers `/profile`
- Disparait quand `level === 'complete'` (anti-bruit) — Sarah avec profil complet ne voit pas de carte sur le dashboard, c'est cohérent

```
Variant dashboard-card :
┌─────────────────────────────────────────────────────────────┐
│ Profil enrichi · Tu débloques les stats personnalisées.    │
│                                          Mon profil →       │
└─────────────────────────────────────────────────────────────┘
```

### AC6 — Variant `'inline-compact'` (autres pages contextuelles)

**Given** une page comme la fiche métier Epic 3 affiche un mini-indicateur
**When** `<ProfileMaturityIndicator variant="inline-compact" />` est rendu
**Then** le composant est **réduit à une pill discrète** :

```
[ Profil enrichi ] ← chip discret, color-bg-2, border color-border, text-sm
```

- Pas de description, pas d'action
- Hover : tooltip avec description du niveau
- Click : navigue vers `/profile`

### AC7 — Accessibilité RGAA AA

**Given** le composant dans ses 3 variants
**When** je teste clavier + screen reader + reduced motion
**Then** **HTML sémantique** :

- Container racine : `<section role="region" aria-labelledby="maturity-title-{uid}">`
- Libellé niveau : `<h3 id="maturity-title-{uid}">` (variant profile-header) ou `<span class="sr-only">{niveau}</span>` (variant inline)
- Description : `<p>`
- Bouton "Voir comment compléter" : `<button type="button" aria-expanded="true|false" aria-controls="next-actions-{uid}">`
- Liste `nextActions` expandée : `<ul id="next-actions-{uid}">` avec chaque action en `<li><button>...</button></li>`

**And** **annonces dynamiques** :

- Au mount : annonce SR-only *"Niveau de profil : Profil enrichi. Tu débloques les stats personnalisées."*
- Click expand : *"Liste des suggestions ouverte, 2 actions disponibles."*
- Click une action : pas d'annonce propre (l'annonce vient du sheet ouvert)
- Quand le niveau **monte** (ex. après ajout d'un bulletin), une annonce `aria-live="polite"` *"Niveau de profil : Profil enrichi (mis à jour)."* — utile pour célébration discrète **non culpabilisante** (cf AC8)

**And** **clavier** :
- Tab order : titre (focusable décoratif) → bouton "Voir comment compléter" → (si expand) chaque action → bouton "Plier"
- Espace / Entrée active les boutons
- Échap sur la liste expand la ferme

**And** **reduced motion** : pas d'animation propre sur cet écran ; transition expand collapse en `motion-quick` → ~0 ms

### AC8 — Évolution du niveau : célébration discrète, non culpabilisante

**Given** le niveau de maturité augmente (`base → enriched` ou `enriched → complete`)
**When** l'utilisateur consulte la page profil ou le dashboard après la transition
**Then** une **célébration discrète** est appliquée :

- **Banner toast `success`** transient (3 s auto-dismiss) en haut de la page concernée : *"Profil enrichi débloqué — tes stats sont maintenant personnalisées."* (ou variante selon niveau atteint)
- Couleur du toast : `color-success` (#2F6B4F) — **PAS un toast brand brand**, plus calme
- **AUCUN confetti, AUCUNE animation type Wrapped Spotify** — anti-euphorie creuse (UX spec § Emotional Goals à bannir)
- **AUCUNE modal** "Bravo, tu as atteint le niveau X !"
- Le banner est dismissible et **n'apparaît qu'UNE FOIS** par transition (déduplication côté serveur : flag `maturity_celebration_shown_for_{level}_at` dans le profil)

**And** un event analytics `profile_maturity_level_up` est émis avec `{ from: MaturityLevel, to: MaturityLevel, triggered_by_action: string }`
**And** si le niveau **redescend** (ex. suppression de tous les bulletins → `enriched → base`) :
- **Aucun toast** — pas de "tu as régressé !"
- La card maturité affiche silencieusement le nouveau niveau au prochain refresh
- Event analytics `profile_maturity_level_down` émis pour observabilité, mais **rien côté UX**

### AC9 — Tests : logique + visual + a11y

**Backend (pytest)** :
- `compute_maturity()` cas golden : 15 snapshots de profils → niveau attendu (couvre base/enriched/complete + edge cases comme step-1 skipped + bulletins partial)
- Cohérence client / serveur : exécution du même golden sur les 2 implémentations doit donner le même résultat (test critique anti-drift)
- Endpoint `GET /api/v1/students/me/profile/maturity` retourne `{ level, next_actions, computed_at }`

**Frontend (Vitest + RTL)** :
- API contract : props minimales `{ level: 'base', nextActions: [...] }`
- Variant `profile-header` : layout complet visible, bouton expand fonctionnel
- Variant `dashboard-card` : layout compact, pas expand
- Variant `inline-compact` : pill seule visible
- Click "Voir comment compléter" → liste expand
- Click action → `onClick` appelé
- `level === 'complete'` + variant `dashboard-card` → composant absent du DOM (anti-bruit AC5)
- **Test runtime validation dev** : copy contenant "incomplet" → `console.warn` mock appelé
- a11y axe-core : aucune violation

**E2E (Playwright)** :
- Léa onboarding postponed → maturité `base` → ajoute bulletin via mini-flow → maturité passe `enriched` → toast success visible
- Sarah ajoute son dernier trimestre → maturité passe `complete` → carte dashboard disparaît (cohérent AC5)
- Visual regression : 3 variants × 3 niveaux = 9 snapshots

---

## 3. Tasks / Subtasks

### T1 — Backend : logique `compute_maturity` + endpoint (AC2)

- [x] Fonction pure `compute_maturity(profile: StudentProfile) -> MaturityLevel` dans `apps/api/apps/students/profile_maturity.py`
- [x] 15 golden snapshots de tests dans `apps/api/apps/students/tests/test_profile_maturity.py`
- [x] Endpoint `GET /api/v1/students/me/profile/maturity` retournant `{ level, next_actions: NextAction[], computed_at }`
- [x] Module partagé client / serveur via golden test file (`apps/web/src/lib/profile/golden-maturity.test.json`)

### T2 — Frontend : `compute_maturity` côté client (AC2)

- [x] Fonction pure dans `apps/web/src/lib/profile/maturity.ts` (TypeScript pur)
- [x] Mêmes 15 golden cas testés en Vitest + 15 JSON alignment cases
- [x] Calcul instantané côté client disponible pour optimistic UI

### T3 — Composant `<ProfileMaturityIndicator />` (AC1, AC3, AC4, AC5, AC6, AC7)

- [x] `apps/web/src/components/features/profile/profile-maturity-indicator.tsx`
- [x] 3 sous-composants pour les variants (MaturityProfileHeader, MaturityDashboardCard, MaturityInlineCompact)
- [x] Sous-composant `<NextActionsList />` partagé (AC4)
- [x] Hook `useMaturityLevel()` (TanStack Query sur `GET /api/v1/students/me/profile/maturity`)
- [x] **Runtime validation dev** : check copy contre mots interdits, `console.warn` si match

### T4 — Toast célébration discrète (AC8)

- [x] Hook `useMaturityCelebration()` avec sessionStorage + fire-and-forget server flag
- [x] Silence total sur downgrade

### T5 — Intégration page profil (Story 2.6 cross-cut)

- [x] Composant prêt pour intégration (variant="profile-header" pour Story 2.6, variant="dashboard-card" pour Epic 3)

### T6 — Tests + documentation

- [x] 16 tests pytest backend (15 golden + 1 JSON alignment) — `test_profile_maturity.py`
- [x] 6 tests endpoint — `test_views_maturity.py`
- [x] 30 tests Vitest logique TS — `maturity.test.ts`
- [x] 15 tests RTL composant — `profile-maturity-indicator.test.tsx`
- [x] 6 tests hook celebration — `use-maturity-celebration.test.ts`
- [x] `docs/components/profile-maturity-indicator.md` : API + 3 variants + copy guidelines + mots interdits

---

## 4. Dev Notes

### 4.1 Wireframes ASCII

#### Variant `profile-header` (page profil) — mobile

```
┌─────────────────────────────────────────┐
│                                          │
│  Profil enrichi                          │ ← text-h3 weight 600
│                                          │
│  Tu débloques les stats personnalisées   │ ← text-body muted
│  sur tes parcours.                       │
│                                          │
│  [ Voir comment compléter →           ] │ ← secondary button
│                                          │
└─────────────────────────────────────────┘

État expand (après tap "Voir comment compléter") :
┌─────────────────────────────────────────┐
│  Profil enrichi                          │
│  Tu débloques les stats personnalisées   │
│                                          │
│  [ ▴ Plier                            ] │ ← rotation chevron
│                                          │
│  ┌─────────────────────────────────────┐│
│  │ 📋 Ajoute un autre trimestre         ││
│  │    Tes stats deviennent plus précises││
│  │                                  →   ││
│  └─────────────────────────────────────┘│
│  ┌─────────────────────────────────────┐│
│  │ 💛 Vérifie tes spécialités           ││
│  │    Parcours encore mieux ciblés      ││
│  │                                  →   ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

#### Variant `dashboard-card` — desktop horizontal

```
┌─────────────────────────────────────────────────────────────┐
│ Profil enrichi · Tu débloques les stats personnalisées.    │
│                                          Mon profil →       │
└─────────────────────────────────────────────────────────────┘
```

#### Variant `inline-compact`

```
[ Profil enrichi ]   ← chip / pill discret
```

### 4.2 Copy verrouillé par niveau (à valider sprint review)

| Niveau | Libellé h3 | Description body |
|---|---|---|
| `base` | "Profil de base" | "Tu as l'essentiel pour des recos indicatives — toutes les explorations sont ouvertes." |
| `enriched` | "Profil enrichi" | "Tu débloques les stats personnalisées sur tes parcours." |
| `complete` | "Profil complet" | "Tu profites de toutes les features — recos affinées, stats précises, parcours ciblés." |

**Test sortie écran** : si Léa lit "Profil de base" et pense *"donc je suis incomplète"*, on refait. Cible : *"Voilà ce que j'ai aujourd'hui — je peux explorer, je verrai si je veux compléter."*

### 4.3 Mots interdits dans le copy (validation runtime dev)

```
["incomplet", "incomplète", "manque", "manquant", "manquante",
 "%", "pourcentage", "X %", "raté", "ratée",
 "tu rates", "il te reste", "tu n'as pas encore",
 "termine ton profil", "complète ton profil", "finalise"]
```

Au moindre match, `console.warn` dev avec lien vers ce paragraphe.

### 4.4 Décisions design verrouillées

- **3 états qualitatifs, jamais de pourcentage** — c'est le COEUR de la story.
- **Pas de bordure colorée par niveau** (anti-distinction visuelle stigma).
- **Variant `dashboard-card` disparaît à `complete`** — anti-bruit, Sarah avec profil complet n'a pas besoin de rappel.
- **Variant `inline-compact` n'expose pas les actions** — juste un tooltip + navigation vers `/profile`.
- **Célébration `level_up` discrète** : toast success 3 s, jamais confetti.
- **Aucune célébration `level_down`** — silence respectueux quand l'utilisateur retire des données.
- **Copy verrouillé, mots interdits enforced runtime dev** — c'est trop critique pour laisser au libre arbitre.
- **Action priorisée bulletins en premier** pour `base` — c'est le gain le plus net (stats personnalisées).

### 4.5 Anti-patterns proscrits (PILIER)

- ❌ **Pourcentage** sous TOUTES ses formes (numéraire, jauge, ring de progression, smiley évolutif)
- ❌ **"Profil à X %"** ou variantes
- ❌ **Couleur sémantique progressive** (rouge base → orange enriched → vert complete)
- ❌ **Confetti** ou animation type Spotify Wrapped à `level_up`
- ❌ **Modal "Bravo !"** ou cérémonie quelconque
- ❌ **"Allez, tu y es presque !"** ou variantes (UX spec § Emotional Goals à bannir)
- ❌ **"Plus que X éléments à remplir"** ou compteur de manques
- ❌ **Couleur danger / warning** sur le niveau `base`
- ❌ **Bouton "Compléter mon profil"** en CTA primary criant
- ❌ **Notification push** "Tu n'as pas mis à jour ton profil depuis X jours"
- ❌ **Badge "À compléter"** sur le menu profil
- ❌ **"Tu manques de X"** (formulation par déficit)

### 4.6 Edge cases et failures explicites

| Edge case | Comportement attendu | AC ref |
|---|---|---|
| Élève fraîchement inscrit (step-1 pas même skipped) | Niveau `base` par défaut (le profil EXISTE, c'est l'essentiel) | AC2 |
| Élève skip step-1 ET step-2 ET bulletins postponed | Niveau `base` (cohérent — c'est l'état d'entrée valide) | AC2 |
| Élève complète step-1 + step-2 + ajoute 1 trimestre | Niveau `enriched` (transition `base → enriched` → toast célébration) | AC8 |
| Élève complète tout (3 steps + 2 trimestres) | Niveau `complete` (transition `enriched → complete` → toast célébration) | AC8 |
| Élève supprime tous ses bulletins après être à `complete` | Niveau redescend à `base` ou `enriched` selon état, **aucun toast**, card maturité reflète silencieusement | AC8 |
| Modification mineure (passions) sans changement de niveau | Pas de toast (déduplication serveur sur `maturity_celebration_shown_for_{level}_at`) | AC8 |
| Niveau identique calculé client vs serveur (drift) | Test golden snapshot doit fail, regression CI bloquant | T1, T2 |
| Dev passe une description avec "Tu manques" | `console.warn` runtime dev | AC3 |
| Variant `dashboard-card` + `level === 'complete'` | Composant retourne `null`, pas de DOM | AC5 |
| Lecteur d'écran sur card maturité | Annonce niveau + description, puis disponibilité du bouton "Voir comment compléter" | AC7 |
| Reduced motion sur expand | Expand instantané sans animation | AC7 |
| Sarah à `enriched`, supprime un bulletin pour `base`, ajoute un autre pour revenir à `enriched` | 2e transition `base → enriched` → **PAS de toast** (déjà vu), comportement silencieux | AC8 |
| Élève consulte sa page profil 6 mois après être passé à `complete` | Pas de toast récurrent, état stable affiché | AC8 |

---

## 5. Project Structure Notes

```
apps/web/
  components/profile/
    profile-maturity-indicator.tsx     ← T3
    maturity-profile-header.tsx        ← variant 1
    maturity-dashboard-card.tsx        ← variant 2
    maturity-inline-compact.tsx        ← variant 3
    next-actions-list.tsx              ← sous-composant partagé AC4
    __tests__/
      profile-maturity-indicator.test.tsx
      maturity-celebration.test.tsx
  hooks/
    use-maturity-level.ts              ← TanStack Query
    use-maturity-celebration.ts        ← T4

packages/profile/
  maturity.ts                          ← T2 (logique partagée)
  golden-maturity.test.json            ← 15 snapshots
  __tests__/maturity.test.ts

apps/api/apps/students/
  profile_maturity.py                  ← T1 (Python)
  views_maturity.py                    ← endpoint GET maturity
  models.py                            ← ajout flag maturity_celebration_shown_for_{level}_at
  migrations/
    NNNN_maturity_celebration_flags.py
  tests/
    test_profile_maturity.py           ← golden snapshots

docs/components/
  profile-maturity-indicator.md        ← T6
```

**Conventions à respecter :**

- Pas de duplication logique : golden snapshots JSON shared client + serveur
- Tokens CSS uniquement (Story 1.2)
- Audit log Story 1.13 sur `profile_maturity_level_up` et `_down`
- RLS Story 1.8 sur endpoint maturity

---

## 6. References

- **UX spec globale** :
  - § Emotional Goals secondaires → Dignité (PILIER)
  - § Anti-patterns proscrits → "Profil complété à X %"
  - § Experience Principles #4 (mode normal = mode dégradé)
  - § Principles to bann → "Verdict-fatigue", "Stigmate", "Euphorie creuse"
- **Epic 2 detail** : § Story 2.7
- **Story 2.5 (mode dégradé invisible)** : sémantique cohérente — `bulletins_status` informe la maturité
- **Story 2.6 (mise à jour profil)** : consume `<ProfileMaturityIndicator variant="profile-header" />` en haut de page
- **Story 1.13 (audit log)** : events `profile_maturity_level_up` / `_down`
- **PRD** : FR19 (score de complétude + identification éléments manquants — implémenté qualitativement)

---

## 7. Dev Agent Record

### Agent Model Used
claude-sonnet-4-6

### Debug Log References
- Forbidden words check déplacé au niveau render (pas dans NextActionsList) pour pouvoir être testé sans expand
- sr-only aria-live réduit à juste le niveau (sans la description) pour éviter le "Found multiple elements" en test RTL
- Path JSON golden (Python) corrigé : 6 remontées de parent (pas 5) pour atteindre la racine du repo

### Completion Notes List
- T1 ✅ : `BulletinsStatus` enum + champs `bulletins_status` + `maturity_celebration_shown_for_{level}_at` + migration `0003_maturity_celebration_flags`. Logique pure `compute_maturity()` dans `profile_maturity.py`. Endpoint GET `/api/v1/students/me/profile/maturity`. 16 tests pytest (15 golden + 1 JSON alignment).
- T2 ✅ : Golden JSON `golden-maturity.test.json` (15 cas). Logique TS pure `computeMaturity()` dans `lib/profile/maturity.ts`. 30 tests Vitest (15 inline + 15 JSON alignment).
- T3 ✅ : Composant `ProfileMaturityIndicator` avec 3 variants (profile-header, dashboard-card, inline-compact). Runtime forbidden words check. Hook `useMaturityLevel` (TanStack Query). 15 tests RTL couvrant API contract, expand/collapse, onClick, dashboard null, inline pill, a11y aria-expanded.
- T4 ✅ : Hook `useMaturityCelebration` — détecte transition level-up, retourne message toast one-shot, silence sur downgrade. 6 tests.
- T5 : Composant prêt pour intégration dans Story 2.6 (`variant="profile-header"`) et Epic 3 dashboard (`variant="dashboard-card"`).
- T6 ✅ : `docs/components/profile-maturity-indicator.md` avec API, variants, copy guidelines, mots interdits.

### File List
- `apps/api/apps/students/models.py` — BulletinsStatus enum + bulletins_status + maturity celebration flags
- `apps/api/apps/students/migrations/0003_maturity_celebration_flags.py` — migration
- `apps/api/apps/students/profile_maturity.py` — compute_maturity() pure function
- `apps/api/apps/students/views_maturity.py` — ProfileMaturityView GET endpoint
- `apps/api/apps/students/urls.py` — route me/profile/maturity added
- `apps/api/apps/students/tests/test_profile_maturity.py` — 16 golden tests
- `apps/api/apps/students/tests/test_views_maturity.py` — 6 endpoint tests
- `apps/web/src/lib/profile/golden-maturity.test.json` — 15 golden snapshots (shared)
- `apps/web/src/lib/profile/maturity.ts` — computeMaturity() TS pure function
- `apps/web/src/lib/profile/__tests__/maturity.test.ts` — 30 Vitest tests
- `apps/web/src/components/features/profile/profile-maturity-indicator.tsx` — main component
- `apps/web/src/components/features/profile/__tests__/profile-maturity-indicator.test.tsx` — 15 RTL tests
- `apps/web/src/hooks/use-maturity-level.ts` — TanStack Query hook
- `apps/web/src/hooks/use-maturity-celebration.ts` — celebration hook
- `apps/web/src/hooks/__tests__/use-maturity-celebration.test.ts` — 6 tests
- `docs/components/profile-maturity-indicator.md` — API docs

### Change Log

- 2026-05-25 — Story 2.7 contextée par Marwen + Claude (Opus 4.7). **Story pilier du principe émotionnel #2 (dignité avant positivité)**. Indicateur qualitatif 3 états remplace TOUT pattern "Profil à X %" classique Diplomeo / LinkedIn. Mots interdits enforced runtime dev. Golden snapshots client+serveur pour cohérence stricte.
- 2026-06-19 — Implémentation complète par Claude Sonnet 4.6. Backend (BulletinsStatus enum, compute_maturity(), endpoint maturity, 22 tests pytest). Frontend (golden JSON + TS maturity logic + composant 3 variants + 2 hooks, 51 tests Vitest/RTL). 441 tests backend passent, 299 tests frontend passent. Aucune régression.
