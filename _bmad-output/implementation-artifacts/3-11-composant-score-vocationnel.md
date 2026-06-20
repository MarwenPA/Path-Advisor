# Story 3.11: Composant `ScoreVocationnel` réutilisable

**Epic:** 3 — Recommandation Vocationnelle (Premier Aha)
**Status:** review
**Sprint:** 6 (Recommandation vocationnelle)
**Story Key:** `3-11-composant-score-vocationnel`
**Estimation:** M (medium) — composant UI pur React + 3 variants + accessibilité + tap-to-copy. Pas de backend. Sized ~1.5 j focused work.

> Composant UI fondamental de l'Epic 3 : `ScoreVocationnel` est la carte qui affiche un score métier 0-100 avec phrase recopiable et chips signaux. Il est indépendant du moteur de scoring (Story 3.3) — il consomme des props, il ne fait pas d'appel réseau. Peut être développé et testé en isolation avec des données mock avant que le backend soit prêt.

---

## 1. User Story

**As a** développeur Path-Advisor,
**I want** un composant `ScoreVocationnel` standardisé affichant un score métier avec phrase recopiable et chips signaux,
**So that** la présentation des scores soit cohérente sur tous les écrans (UX-DR5 + UX-DR23 pattern phrase recopiable) et que Story 3.4 (liste métiers) et Story 3.6 (explicabilité) puissent l'intégrer directement.

---

## 2. Acceptance Criteria (BDD)

### AC1 — Interface props et rendu de base

**Given** le composant est instancié avec ses props obligatoires
**When** je le rends avec `{ metierId, score, metiersName, phraseRecopiable, signals, variant }`
**Then** il affiche :
- **Header** : nom métier (`h3` weight 600, `text-h3`) + chip score à droite (couleur sémantique selon score : ≥70 `color-success`, 40–69 `color-warning`, <40 `color-muted`)
- **Body** : phrase recopiable en `text-body` italic + bouton "Copier" subtil (icône Lucide `Copy`, taille `sm`, `color-text-subtle`)
- **Footer** : 3 à 5 chips signaux contributifs cliquables (variant `outline`, taille `sm`)

**And** le score dans le chip est affiché comme "78 / 100" avec `font-feature-settings: "tnum"` (tabular numbers)

**And** toutes les props sont typées TypeScript strict (pas de `any`)

### AC2 — Variant `compact` (liste des recos — Story 3.4)

**Given** `variant="compact"`
**When** le composant est rendu
**Then** la card fait max 360 × 160 px (mobile) avec overflow masqué
**And** la phrase recopiable est tronquée à 1 ligne (`text-overflow: ellipsis`) avec tooltip au hover/focus affichant la phrase complète
**And** les chips signaux sont limités à 3 (les 2 premiers + chip "+N autres" si N > 0)
**And** le bouton "Copier" est visible (pas masqué en compact)

### AC3 — Variant `expanded` (drill-down fiche — Story 3.5)

**Given** `variant="expanded"`
**When** le composant est rendu
**Then** la phrase recopiable est affichée en entier (pas de troncature)
**And** les chips signaux sont tous affichés (jusqu'à 8)
**And** chaque chip signal au clic ouvre le drawer d'explicabilité (via prop `onSignalClick(signalId)`)
**And** un lien "Pourquoi ce score ?" est affiché sous les chips (déclenche `onExplainClick()`)

### AC4 — Variant `comparison` (2 cartes côte à côte)

**Given** `variant="comparison"`
**When** 2 composants sont rendus en grid côte à côte
**Then** sur mobile : swipe horizontal entre les 2 cartes (snap scroll)
**And** sur desktop (≥1024 px) : affichage en grid 2 colonnes avec même hauteur (CSS `align-items: stretch`)
**And** le score chip est mis en évidence par rapport au variant `compact` (taille légèrement supérieure)

### AC5 — Tap-to-copy (UX-DR23)

**Given** je tape sur le bouton "Copier"
**When** l'action se déclenche
**Then** la phrase recopiable est copiée dans le presse-papier via `navigator.clipboard.writeText()`
**And** un toast 3 s confirme "Phrase copiée — colle-la où tu veux"
**And** le bouton passe temporairement à l'état `copied` (icône `Check` pendant 2 s, puis retour à `Copy`)
**And** si `navigator.clipboard` n'est pas disponible (contexte non-HTTPS ou navigateur old), un fallback `document.execCommand('copy')` est tenté silencieusement — si les deux échouent, le toast indique "Copie manuelle : sélectionne la phrase et appuie sur Ctrl+C"

### AC6 — Accessibilité RGAA AA

**Given** un lecteur d'écran lit le composant
**When** il traverse la card
**Then** le score est annoncé "Compatible à 78 % avec ce métier" (via `aria-label` sur le chip score)
**And** la phrase recopiable a un `aria-label` : "Phrase défendable pour {nom métier} : {phrase}"
**And** le bouton copier a `aria-label="Copier la phrase défendable pour {nom métier}"` + `aria-live="polite"` qui annonce "Phrase copiée" après l'action
**And** les chips signaux sont `role="button"` avec `aria-label="Signal contributif : {label}"` et navigables au clavier (`Tab` + `Enter`/`Space`)
**And** la card entière est accessible au clavier (pas de trap de focus)

**Given** `prefers-reduced-motion: reduce`
**When** le composant est rendu
**Then** aucune animation (fade-in, transition score chip) n'est jouée — affichage statique immédiat

### AC7 — Prop `confidenceLevel` (Story 3.10 — profil incomplet)

**Given** la prop `confidenceLevel="indicative"` est passée
**When** le composant est rendu
**Then** un label discret "indicatif" est affiché sous le chip score, en `text-caption color-text-muted`
**And** aucune alerte visuelle, aucune couleur rouge, aucun message culpabilisant
**And** sans cette prop (ou `confidenceLevel="normal"`), le label n'est pas affiché

### AC8 — Tests

**Given** le composant est testé avec Vitest + RTL
**When** les tests tournent
**Then** les cas suivants passent :
- Render `compact` : phrase tronquée, 3 chips max, bouton Copier visible
- Render `expanded` : phrase complète, chips cliquables, lien "Pourquoi ce score ?"
- Score ≥70 → chip `color-success` ; 40–69 → `color-warning` ; <40 → `color-muted`
- Clic "Copier" → `navigator.clipboard.writeText` appelé + toast affiché
- `confidenceLevel="indicative"` → label "indicatif" présent
- Navigation clavier : Tab traverse header → bouton copier → chips → lien explain
- `aria-label` score = "Compatible à 78 % avec ce métier"
- Reduced motion : pas d'animation class

---

## 3. Tasks / Subtasks

### T1 — Composant `ScoreVocationnel`

- [x] Créer `apps/web/src/components/professions/ScoreVocationnel.tsx`
- [x] Types TypeScript dans `apps/web/src/components/professions/types.ts`
- [x] Utiliser les tokens design (Story 1.2) — zéro couleur hardcodée
- [x] Sous-composants internes : `ScoreChip`, `CopyButton`, `SignalChips`

### T2 — Hook `useCopyToClipboard`

- [x] Créer `apps/web/src/hooks/useCopyToClipboard.ts`
- [x] Gère `navigator.clipboard` + fallback `execCommand` + état `copied` (2 s)
- [x] Réutilisable hors de ce composant

### T3 — Storybook stories

- [x] Skipped — Storybook non configuré dans le projet

### T4 — Tests Vitest + RTL

- [x] Couvrir tous les cas AC8 — 26 tests passent
- [x] Mock `navigator.clipboard.writeText` dans les tests
- [x] Test reduced motion via `matchMedia` mock

### Review Findings (code review 2026-06-20)

- [x] [Review][Decision → 1b] AC4 variant `comparison` complété dans le composant — Ajout d'un wrapper `ScoreVocationnelComparison` (snap-scroll horizontal mobile + `lg:grid lg:grid-cols-2 lg:items-stretch`, cartes `h-full` pour hauteur égale). Le variant `comparison` agrandit le chip score (`text-body`). Tests AC4 ajoutés (chip agrandi, `h-full`, wrapper 2 cartes + classes snap/grid). [apps/web/src/components/professions/ScoreVocationnel.tsx]
- [x] [Review][Decision → 2b] AC5 durée alignée sur 2 s — Spec ajustée : un seul timer `RESET_DELAY_MS = 2000` pour le toast ET le reset d'icône (pas de découplage). Commentaire « 3 s » corrigé. [apps/web/src/hooks/useCopyToClipboard.ts]
- [x] [Review][Decision → 3a] AC1/§4.3 fond teinté conservé — Couples `bg-success/10 text-success` / `bg-warning-bg text-warning` / `bg-muted text-muted-foreground` gardés, exposés comme variants du composant `Badge`. §4.3 mise à jour en conséquence. [apps/web/src/components/professions/ScoreVocationnel.tsx]
- [x] [Review][Decision → 4b] Primitives shadcn créées/adoptées — `Badge` (`apps/web/src/components/ui/badge.tsx`, variants success/warning/muted/outline) pour le chip score et les chips signaux ; `Tooltip`/`TooltipTrigger`/`TooltipContent` (`apps/web/src/components/ui/tooltip.tsx`, primitive CSS/aria légère **sans** `@radix-ui/react-tooltip`) pour la phrase tronquée compact ; `Button` déjà existant. La nouvelle tooltip corrige aussi un import cassé pré-existant dans `bulletin-recap-editor.tsx`.
- [x] [Review][Patch] Mismatch commentaire « 3 s » vs reset 2 s — Commentaire de la live region réécrit : auto-dismiss après 2 s (`RESET_DELAY_MS`). [apps/web/src/components/professions/ScoreVocationnel.tsx]
- [x] [Review][Patch] `role="button"` redondant supprimé — Les chips signaux sont des `<button>` natifs (via `Badge asChild`) sans `role` explicite. [apps/web/src/components/professions/ScoreVocationnel.tsx]
- [x] [Review][Patch] `metierId` désormais consommé — Émis comme `data-metier-id` sur l'`<article>` (clé/analytics) et utilisé comme `key` dans `ScoreVocationnelComparison`. [apps/web/src/components/professions/ScoreVocationnel.tsx]
- [x] [Review][Patch] `metiersName` retiré de `ScoreChipProps` — Prop morte supprimée ; le chip n'en a pas besoin. [apps/web/src/components/professions/ScoreVocationnel.tsx]
- [x] [Review][Patch] `large` du chip score fiabilisé — La taille de base n'est plus posée dans la classe de base du chip : le ternaire `large ? "text-body" : "text-body-sm"` est l'unique source. `cn` étendu (`extendTailwindMerge`) pour enregistrer les font-sizes custom → plus de collision `text-{color}` vs `text-{size}`. Test AC4 vérifie que `comparison` rend bien `text-body` sans `text-body-sm`. [apps/web/src/components/professions/ScoreVocationnel.tsx + apps/web/src/lib/utils.ts]
- [x] [Review][Patch] Fallback `execCommand` atteint sur rejet de `writeText` — Le `legacyCopy()` est tenté dans le `catch` du `writeText` (refus de permission) ET quand l'API clipboard est absente. Test hook dédié « falls back to execCommand when writeText rejects ». [apps/web/src/hooks/useCopyToClipboard.ts]
- [x] [Review][Patch] Fuite textarea + focus restauré — `legacyCopy()` utilise try/finally : `removeChild` toujours exécuté, focus de l'élément actif (bouton Copier) sauvegardé/restauré. [apps/web/src/hooks/useCopyToClipboard.ts]
- [x] [Review][Patch] Garde `isMounted` dans le chemin async — `isMountedRef` empêche tout `setStatus` après démontage (promesse en vol + timeout). Test hook « does not set state after unmount ». [apps/web/src/hooks/useCopyToClipboard.ts]
- [x] [Review][Patch] Test navigation clavier ajouté — AC8 « copier → chip → lien explain » : focusabilité + ordre DOM (= ordre Tab) vérifiés. [apps/web/src/components/professions/__tests__/ScoreVocationnel.test.tsx]
- [x] [Review][Patch] Décompte tests corrigé — La suite contient désormais 37 `it()` (tous verts). Dev Agent Record mis à jour. [apps/web/src/components/professions/__tests__/ScoreVocationnel.test.tsx]
- [x] [Review][Patch] Garde sur `score` — `normaliseScore()` : clamp [0,100] + `Math.round`, NaN → 0. Tests AC1 (150→100, -5→0, 78.6→79, NaN→0). [apps/web/src/components/professions/ScoreVocationnel.tsx]
- [x] [Review][Patch] `phraseRecopiable` vide/blanc géré — `trim()` + garde `hasPhrase` : placeholder « Phrase à venir », bouton Copier désactivé, aria-label adapté. Test « phrase recopiable vide ». [apps/web/src/components/professions/ScoreVocationnel.tsx]
- [x] [Review][Patch] AC3 lien « Pourquoi ce score ? » inconditionnel en expanded — Rendu dès `isExpanded` ; `onExplainClick?.()` no-op si absent. Test « affiche le lien même sans onExplainClick ». [apps/web/src/components/professions/ScoreVocationnel.tsx]
- [x] [Review][Patch] `afterEach` de restauration ajouté — `navigator.clipboard`, `document.execCommand` et `window.matchMedia` sauvegardés/restaurés → plus de fuite globale entre tests. [apps/web/src/components/professions/__tests__/ScoreVocationnel.test.tsx]
- [x] [Review][Patch] Live region unique — Une seule région `role="status" aria-live="polite"` sert d'annonce ET de toast visible ; le doublon `role="alert"` est supprimé (plus de double annonce). [apps/web/src/components/professions/ScoreVocationnel.tsx]
- [x] [Review][Defer] `aria-label` sur `<span>` role `generic` non exposé aux lecteurs d'écran réels — Le score est annoncé via `aria-label` sur un `<span>` ; les tests jsdom passent (faux positif sur l'échec de test annoncé), mais le nom accessible n'est pas fiablement exposé en AT réelle. Refonte a11y (wrapper sémantique ou texte sr-only) à traiter avec le passage RGAA AA global. [apps/web/src/components/professions/ScoreVocationnel.tsx:28-42] — deferred, dette a11y transverse
- [x] [Review][Defer] Pas de dédup des `signals` par `id` — Doublons d'id → collision de clé React + chips indistinguables. À traiter côté contrat de données (moteur de scoring Story 3.3), pas dans ce composant UI. [apps/web/src/components/professions/ScoreVocationnel.tsx:114-120] — deferred, dépend du producteur de données

---

## 4. Dev Notes

### 4.1 Wireframe ASCII — variant `compact` (mobile 375 px)

```
┌──────────────────────────────────────────┐
│  Infirmier·ère de bloc opératoire  [78/100] │ ← h3 + chip color-success
│                                            │
│  "Mon projet est de travailler en          │ ← italic, 1 ligne tronquée...
│   salle d'op car…"                   [📋] │ ← bouton Copier
│                                            │
│  [SVT ×]  [aider ×]  [+2 autres]          │ ← 3 chips max
└──────────────────────────────────────────┘
```

### 4.2 Wireframe ASCII — variant `expanded`

```
┌──────────────────────────────────────────┐
│  Infirmier·ère de bloc opératoire  [78/100] │
│                               indicatif    │ ← si confidenceLevel="indicative"
│                                            │
│  "Mon projet est de travailler en salle    │ ← phrase complète, multi-ligne
│   d'op car j'aime la précision et         │
│   l'adrénaline des urgences."      [📋]   │
│                                            │
│  [SVT ×]  [aider ×]  [hôpital ×]          │
│  [précision ×]  [travail d'équipe ×]       │
│                                            │
│  → Pourquoi ce score ?                     │ ← lien text, déclenche onExplainClick
└──────────────────────────────────────────┘
```

### 4.3 Couleurs sémantiques score

> **Décision review 2026-06-20 (Decision 3a)** : on **conserve le fond teinté** actuel
> (badge `Badge` variants `success` / `warning` / `muted`) plutôt que le couple
> background plein + texte « on-* » initialement esquissé. Plus discret, meilleur
> contraste sur fond carte, et tous les tokens existent déjà dans la config Tailwind.

Utiliser uniquement des tokens (pas de hex hardcodé) — couples background teinté + texte sémantique :
- Score ≥70 : `bg-success/10` + `text-success` (badge variant `success`)
- Score 40–69 : `bg-warning-bg` + `text-warning` (badge variant `warning`)
- Score <40 : `bg-muted` + `text-muted-foreground` (badge variant `muted`)

Ces trois couples sont exposés comme variants du composant `Badge` (`apps/web/src/components/ui/badge.tsx`).

### 4.4 Décisions design verrouillées

- **Phrase recopiable en italic** — signal visuel que c'est un artefact à réutiliser (UX-DR23)
- **Chip score à droite du titre** — pas centré, pas en grand, pas d'anneau de progression — discret mais lisible
- **Chips signaux cliquables même en `compact`** — mais `onSignalClick` peut no-op en compact si le contexte ne supporte pas le drawer
- **Pas de `onClick` sur la card entière** — l'interaction est décomposée (chips → explain, copier → clipboard, titre → navigation externe via le parent)
- **`confidenceLevel` n'est pas un boolean** — anticipé pour un futur `"low"` / `"medium"` / `"high"` si le moteur évolue

### 4.5 Items à différer

- Animation fade-in séquentiel (Story 3.4 — côté liste, pas côté composant)
- Favoris / "Mes paris" (Story 3.4 AC1 — prop `onFavoriteToggle` à ajouter plus tard)
- Variant `print-friendly` (Story 3.12 FicheMetier — le ScoreVocationnel en version print est géré par FicheMetier)

---

## 5. Project Structure Notes

```
apps/web/src/components/professions/
  ScoreVocationnel.tsx               ← composant principal (T1)
  ScoreVocationnel.stories.tsx       ← Storybook (T3, si configuré)
  types.ts                           ← interfaces TypeScript (T1)
  __tests__/
    ScoreVocationnel.test.tsx        ← tests RTL (T4)

apps/web/src/hooks/
  useCopyToClipboard.ts              ← hook réutilisable (T2)
  __tests__/
    useCopyToClipboard.test.ts
```

**Conventions à respecter :**
- Tokens CSS uniquement (Story 1.2)
- Aucun appel réseau dans ce composant (props only)
- shadcn/ui : `Badge` (chip score + chips signaux — `apps/web/src/components/ui/badge.tsx`), `Button` (existant), `Tooltip`/`TooltipTrigger`/`TooltipContent` (phrase tronquée compact — primitive CSS/aria légère sans Radix, `apps/web/src/components/ui/tooltip.tsx`)

---

## 6. References

- **Epic 3 detail** : `_bmad-output/planning-artifacts/epics/epic-3-recommandation-vocationnelle-premier-aha.md` § Story 3.11
- **Story 3.4** : liste métiers — intègre ce composant en variant `compact`
- **Story 3.5** : fiche métier — intègre ce composant en variant `expanded`
- **Story 3.6** : explicabilité — reçoit `onSignalClick` + `onExplainClick`
- **Story 3.10** : niveau de confiance — utilise `confidenceLevel="indicative"`
- **Story 1.2** : tokens design — source de vérité des couleurs
- **UX-DR5** : cohérence visuelle composants
- **UX-DR23** : pattern phrase recopiable

---

## 7. Dev Agent Record

### Agent Model Used
claude-sonnet-4-6 (implémentation initiale) ; claude-opus-4-8 (corrections code review 2026-06-20)

### Completion Notes List
- Composant `ScoreVocationnel` avec 3 variants (compact / expanded / comparison) et tous les AC satisfaits
- Hook `useCopyToClipboard` réutilisable : fallback `execCommand` sur rejet de `writeText` (try/finally + restauration du focus), garde `isMounted`, reset auto 2 s
- Feedback copie via une live region unique `role="status" aria-live="polite"` (annonce + toast visible)
- Primitives shadcn adoptées : `Badge` (chip score + signaux), tooltip CSS/aria légère `Tooltip`/`TooltipTrigger`/`TooltipContent` sans `@radix-ui/react-tooltip`
- `cn` étendu via `extendTailwindMerge` pour enregistrer les font-sizes custom (corrige une collision `text-{color}` vs `text-{size}`)
- AC4 `comparison` complété dans le composant : wrapper `ScoreVocationnelComparison` (snap-scroll mobile + `lg:grid-cols-2 items-stretch`)
- Storybook non configuré → T3 skippé
- 37 tests Vitest + RTL sur `ScoreVocationnel` + 7 sur `useCopyToClipboard`, tous verts ; 26 tests `FicheMetier` (consommateur) restent verts → aucune régression

### File List
- `apps/web/src/components/professions/types.ts` (new)
- `apps/web/src/components/professions/ScoreVocationnel.tsx` (new)
- `apps/web/src/components/professions/__tests__/ScoreVocationnel.test.tsx` (new)
- `apps/web/src/hooks/useCopyToClipboard.ts` (new)
- `apps/web/src/hooks/__tests__/useCopyToClipboard.test.ts` (new)
- `apps/web/src/components/ui/badge.tsx` (new — review 4b)
- `apps/web/src/components/ui/tooltip.tsx` (new — review 4b, primitive CSS/aria sans Radix)
- `apps/web/src/lib/utils.ts` (updated — `extendTailwindMerge` pour font-sizes custom)
- `_bmad-output/implementation-artifacts/3-11-composant-score-vocationnel.md` (updated)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (updated)

### Change Log

- 2026-06-20 — Story 3.11 créée (Epic 3 launch). Composant UI indépendant, développable avant le moteur de scoring.
- 2026-06-20 — Implémentation complète : ScoreVocationnel + useCopyToClipboard + 26 tests. Status → review.
- 2026-06-20 — Code review : 4 décisions résolues (1b AC4 dans le composant, 2b toast 2 s, 3a fond teinté, 4b primitives shadcn `Badge`/`Tooltip`) + 15 patches appliqués. Tests : 37 (ScoreVocationnel) + 7 (useCopyToClipboard) verts. Status reste → review.
