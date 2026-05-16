# Story 1.2 : Définition et publication du design system de tokens

**Epic :** 1 — Foundation : Auth multi-rôle, RBAC, Conformité RGPD & Infra technique
**Status :** done
**Sprint :** 1 (Fondations)
**Story Key :** `1-2-design-system-tokens`
**Estimation :** M (medium) — front-only, mais structurant pour TOUTES les stories UI suivantes (Stories 1.3-1.14, Epic 2-10).

> Story 1.2 transforme le placeholder `tokens.css` posé en Story 1.1 en design system Path-Advisor réel : palette R1 Vermillon, type scale Inter, spacing 4px, motion. Aucun composant futur ne hardcodera une couleur/taille.

---

## 1. User Story

**As a** développeur Path-Advisor (Marwen, équipe solo),
**I want** les tokens couleur R1 Vermillon + typographie Inter + spacing 4 px + motion centralisés dans `tokens.css` et `tailwind.config.ts`,
**So that** tous les écrans futurs partagent une identité visuelle cohérente sans hardcoder de valeurs locales et le rebrand 2.0 sera un simple changement de variables CSS.

**Valeur métier :** prérequis pour toutes les stories UI à venir (Story 1.14 ConsentDialog, Epic 2 onboarding, Epic 3 FicheMetier, Epic 4 Graphe). Chaque story qui rebrande du shadcn ou crée un composant custom doit s'appuyer sur ces tokens — sans cette story, on accumule de la dette visuelle qui sera coûteuse à corriger plus tard.

---

## 2. Acceptance Criteria (BDD)

### AC1 — 17 tokens couleur en CSS variables

**Given** la spec UX Step 8 — Visual Design Foundation
**When** je consulte `apps/web/src/styles/tokens.css`
**Then** **les 17 tokens couleur** ci-dessous sont définis en CSS variables sous `:root` :

| Token | Valeur | Usage |
|---|---|---|
| `--color-brand` | `#C8312D` vermillon sobre | Logo, CTA primaire, focus ring |
| `--color-brand-hover` | `#A6231F` vermillon sombre | États interactifs brand |
| `--color-bg` | `#FAFAF7` blanc cassé chaud | Fond principal |
| `--color-bg-2` | `#F4F1ED` ivory | Cartes, surfaces élevées |
| `--color-bg-3` | `#EBE7E1` ivory sombre | Surfaces de fond profond |
| `--color-text` | `#1A1A1A` near-black | Texte principal |
| `--color-text-muted` | `#666660` taupe | Métadonnées, captions |
| `--color-text-subtle` | `#8C8C86` taupe pâle | Labels, hints |
| `--color-border` | `#E0DDD8` | Bordures cartes, séparateurs |
| `--color-border-strong` | `#C9C5BE` | Bordures champs actifs |
| `--color-semantic-audacieux` | `#A85428` terra brûlé | Score "pari audacieux" |
| `--color-semantic-realiste` | `#2F6B4F` forêt | Score "pari réaliste" |
| `--color-semantic-sur` | `#3A7CA5` bleu apaisé | Score "pari sûr" |
| `--color-success` | `#2F6B4F` forêt | Confirmation, validation |
| `--color-warning` | `#C7841B` ambre | Avertissement non-bloquant |
| `--color-danger` | `#9E2A24` rouge sombre | Erreur, destructive (≠ brand) |
| `--color-focus-ring` | `#C8312D` (= brand) | Outline 2 px sur tous focus visibles |

**And** chaque token est utilisable côté Tailwind via `bg-brand`, `text-brand`, `border-brand`, etc.
**And** la palette est documentée en commentaires inline dans `tokens.css` avec le ratio de contraste vs `--color-bg` pour les 5 couples critiques (`text`, `text-muted`, `brand`, `success`, `danger`).
**And** **mode clair uniquement** — pas de bloc `@media (prefers-color-scheme: dark)` dans cette story (UX spec : dark mode reporté post-MVP).

### AC2 — 8 tokens type scale Inter responsive

**Given** la spec UX Step 8 — Typography System
**When** je consulte `tailwind.config.ts` et la page d'accueil rendue
**Then** **les 8 tokens type scale** sont configurés dans `theme.extend.fontSize` avec valeurs mobile-first :

| Token Tailwind | Mobile (default) | Desktop (`md:`+) | Usage |
|---|---|---|---|
| `text-display-1` | `40px / 48 lh` | `56px / 64 lh` | Probabilité d'admission (chiffre dominant) |
| `text-display-2` | `32px / 40 lh` | `40px / 48 lh` | Titre métier aha screen |
| `text-h1` | `24px / 32 lh` | `32px / 40 lh` | Titres d'écrans |
| `text-h2` | `20px / 28 lh` | `24px / 32 lh` | Sections |
| `text-h3` | `18px / 26 lh` | `20px / 28 lh` | Titres de cartes |
| `text-body` | `16px / 24 lh` | `16px / 24 lh` | Texte courant (plancher RGAA) |
| `text-body-sm` | `14px / 20 lh` | `14px / 20 lh` | Métadonnées |
| `text-caption` | `12px / 16 lh` | `12px / 16 lh` | Captions, pied de carte |

**And** Inter est utilisée via `--font-inter` (déjà préchargée par `next/font/google` dans `layout.tsx` depuis Story 1.1).
**And** `font-feature-settings: "tnum"` est activé pour `display-1`, `display-2`, et une utility class `font-tabular` (chiffres tabulaires sur stats/probabilités) — cf. UX § Numeric.
**And** un test smoke vérifie qu'un `<h1 className="text-h1">` rendu en mobile a une `font-size` calculée de 24 px (et 32 px en desktop via media query).

### AC3 — 8 tokens de spacing alignés Tailwind

**Given** la spec UX Step 8 — Spacing & Layout Foundation
**When** je consulte `tailwind.config.ts`
**Then** **les 8 tokens spacing** (base 4 px) sont **alignés sur les défauts Tailwind** — donc utilisables directement via les utilities Tailwind sans extension custom :

| Token alias | Valeur Tailwind | Usage |
|---|---|---|
| `space-1` (`p-1`, `gap-1`, etc.) | 4 px | Espaces collés (icône + label) |
| `space-2` | 8 px | Espaces serrés intra-composant |
| `space-3` | 12 px | Espaces moyens |
| `space-4` | 16 px | Standard entre éléments |
| `space-6` | 24 px | Sections au sein d'une carte |
| `space-8` | 32 px | Entre cartes |
| `space-12` | 48 px | Entre sections de page |
| `space-16` | 64 px | Aération max above-fold |

**And** documenté dans `tokens.css` en commentaire — pas de duplication de `theme.spacing` puisque Tailwind v3 a déjà ces valeurs en défaut. **Aucune extension de `theme.spacing` n'est nécessaire** ; on documente quels tokens du barème Tailwind on utilise et lesquels on évite.
**And** les valeurs interdites en MVP (`space-5` = 20 px, `space-10` = 40 px) sont listées en commentaire comme "non-canoniques — préférer 16/24 ou 32/48".

### AC4 — 4 tokens de motion

**Given** la spec UX Step 8 — Motion System
**When** je consulte `tailwind.config.ts`
**Then** **les 4 tokens motion** sont accessibles via Tailwind utilities :

| Token | Duration | Easing | Usage | Class Tailwind résultante |
|---|---|---|---|---|
| `motion-instant` | 100ms | linear | Hover/focus/micro-feedback | `duration-instant ease-linear` |
| `motion-quick` | 200ms | ease-out | Apparition simple, fallback reduced-motion | `duration-quick ease-out` |
| `motion-standard` | 300ms | `cubic-bezier(0.16, 1, 0.3, 1)` | Transitions par défaut | `duration-standard ease-standard` |
| `motion-narrative` | 720ms | séquence multi-phase | **Réservé au graphe-récit (Epic 4)** | `duration-narrative` |

**And** configurés dans `theme.extend.transitionDuration` (instant/quick/standard/narrative) + `theme.extend.transitionTimingFunction` (standard).
**And** un commentaire en haut de la section motion rappelle la **règle anti-cirque** : `motion-narrative` ne se rejoue jamais sur le même contenu deux fois.
**And** un media query global `@media (prefers-reduced-motion: reduce)` dans `tokens.css` mappe toutes les durations au-dessus de 100ms vers `motion-quick` (200ms) — fallback RGAA AA.

### AC5 — shadcn rebrandé sur R1

**Given** un composant `Button` shadcn fraîchement installé (par Story 1.1)
**When** je l'instancie avec `<Button variant="default">Hello</Button>` dans une page
**Then** son `background-color` reflète automatiquement `--color-brand` (= `#C8312D`)
**And** son `:hover` reflète `--color-brand-hover` (= `#A6231F`)
**And** son `:focus-visible` montre un outline 2 px en `--color-focus-ring`
**And** la typographie utilise Inter (héritée du layout via `--font-inter`)
**And** `<Button variant="destructive">` utilise `--color-danger` (≠ brand pour éviter la confusion brand/erreur).
**And** `<Button variant="secondary">` utilise `--color-bg-2` background + `--color-text` foreground.

> Mécanique : shadcn lit les variables sémantiques `--primary`, `--primary-foreground`, `--destructive`, etc. dans `tokens.css`. Cette story remappe ces variables sémantiques vers nos tokens R1 (cf. snippet §4.7).

### AC6 — Conformité RGAA AA des contrastes

**Given** la spec UX § Accessibility Considerations (NFR-A4 : contraste ≥ 4.5:1 normal, ≥ 3:1 large)
**When** un audit de contraste manuel est exécuté sur les 5 couples critiques
**Then** tous sont conformes ≥ 4.5:1 ou ≥ 3:1 selon taille :

| Couple à valider | Ratio attendu | Conformité |
|---|---|---|
| `--color-text` sur `--color-bg` | 16.8:1 | AAA |
| `--color-text-muted` sur `--color-bg` | 5.6:1 | AA normal + AA large |
| `--color-brand` sur `--color-bg` | 5.2:1 | AA normal |
| `--color-brand` sur `--color-bg-2` | 4.9:1 | AA normal |
| `--color-danger` sur `--color-bg` | 6.8:1 | AA normal (à confirmer) |

**And** chaque ratio mesuré est consigné en commentaire dans `tokens.css` à côté du token concerné.
**And** un test Vitest unitaire utilise une lib (e.g. `wcag-contrast` ou calcul inline) pour vérifier automatiquement les 5 couples — failover en CI dès aujourd'hui (pas attendre Sprint 4 / axe-core).

### AC7 — Showcase visible sur `/` (smoke test design system)

**Given** la page d'accueil rendue par Next.js
**When** je visite `http://localhost:3000`
**Then** la page "Hello Path-Advisor" affiche **un mini-showcase** des tokens :
- Le titre utilise `text-h1` (taille adapt. responsive)
- Un sous-titre utilise `text-body` muted
- Un `<Button>` (brand) et un `<Button variant="outline">` rendus côte à côte
- Le fond utilise `--color-bg`, une carte de showcase utilise `--color-bg-2` + `--color-border`

**And** le test Vitest existant (`page.test.tsx`) est mis à jour pour asserter la présence du h1 et du Button.

> Cette page reste temporaire — elle sera remplacée par les vraies pages Epic 2+ ; mais le showcase prouve que les tokens "marchent end-to-end" sans avoir à attendre une vraie feature.

---

## 3. Tasks / Subtasks

### T1 — Mapper la palette R1 vers `tokens.css` (AC1)

- [x] T1.1 Réécrire `apps/web/src/styles/tokens.css` : sous `:root`, déclarer les **17 variables `--color-*`** documentées (sans modes alternatifs MVP — pas de `@media (prefers-color-scheme: dark)`).
- [x] T1.2 Ajouter pour chaque token critique le ratio de contraste mesuré en commentaire inline (cf. AC6).
- [x] T1.3 Sous une section `/* ============ shadcn semantic mapping ============ */`, mapper les variables que shadcn attend vers nos R1 (cf. snippet §4.7). Les variables shadcn standard sont : `--background`, `--foreground`, `--primary`, `--primary-foreground`, `--secondary`, `--secondary-foreground`, `--muted`, `--muted-foreground`, `--accent`, `--accent-foreground`, `--destructive`, `--destructive-foreground`, `--border`, `--input`, `--ring`, `--radius`. Toutes en **HSL space-separated** (sans `hsl(...)` wrapper — shadcn ajoute lui-même `hsl(...)` côté Tailwind).
- [x] T1.4 Ajouter le bloc `@media (prefers-reduced-motion: reduce)` qui force toutes les durations > 100ms vers `--motion-quick` (200ms). Cf. AC4.

### T2 — Étendre `tailwind.config.ts` avec les tokens (AC2, AC3, AC4, AC5)

- [x] T2.1 Importer le helper shadcn `tailwindcss-animate` (déjà installé en Story 1.1).
- [x] T2.2 Configurer `theme.extend.colors` :
  - Les 17 couleurs Path-Advisor (`brand`, `bg`, `text`, `semantic.*`, etc.) référençant les CSS vars
  - Les couleurs sémantiques shadcn (`primary`, `secondary`, `destructive`, etc.) mappées sur les mêmes CSS vars HSL
- [x] T2.3 Configurer `theme.extend.fontSize` avec **deux tokens jumeaux par display dont mobile ≠ desktop** (décision §4.10) : `display-1` + `display-1-desktop`, `display-2` + `display-2-desktop`, `h1` + `h1-desktop`, `h2` + `h2-desktop`, `h3` + `h3-desktop`. Pour `body`, `body-sm`, `caption` (identiques mobile/desktop selon UX spec) : un seul token. Format : `["2.5rem", { lineHeight: "3rem", letterSpacing: "-0.02em", fontWeight: "600" }]`. Snippet complet dans §4.10.
- [x] T2.4 Configurer `theme.extend.fontFamily` : `sans: ["var(--font-inter)", "system-ui", "sans-serif"]`.
- [x] T2.5 Configurer `theme.extend.transitionDuration` (instant: 100ms / quick: 200ms / standard: 300ms / narrative: 720ms) et `theme.extend.transitionTimingFunction.standard = "cubic-bezier(0.16, 1, 0.3, 1)"`.
- [x] T2.6 Créer `apps/web/src/lib/design-system/tailwind-plugin.ts` exposant `pathAdvisorPlugin` qui déclare `.font-tabular` via `addUtilities` (décision §4.10 — plugin extensible préféré au CSS plain). Snippet complet dans §4.10.
- [x] T2.7 Brancher les 2 plugins dans `tailwind.config.ts` : `plugins: [animate, pathAdvisorPlugin]`.
- [x] T2.8 Aucune extension de `theme.spacing` (Tailwind v3 default suffit pour 4/8/12/16/24/32/48/64 px) — documenter en commentaire dans la config.

### T3 — Vérifier l'intégration shadcn (AC5)

- [x] T3.1 Inspecter `apps/web/src/components/ui/button.tsx` : confirmer qu'il utilise bien `bg-primary`, `text-primary-foreground`, `bg-destructive`, etc. Pas de modif attendue — la magie passe par les CSS vars.
- [x] T3.2 Visuellement : démarrer `npm run dev` et confirmer que `<Button>` affiche le vermillon R1 (`#C8312D`) et non plus le zinc shadcn par défaut.
- [x] T3.3 Vérifier `:hover` (devient `#A6231F`) et `:focus-visible` (ring en `--color-focus-ring`).

### T4 — Showcase + smoke test (AC7)

- [x] T4.1 Mettre à jour `apps/web/src/app/page.tsx` :
  - Garder `Hello Path-Advisor` mais en `<h1 className="text-h1 md:text-h1-desktop font-semibold">` (cf. pattern responsive §4.10 décision 1)
  - Ajouter un sous-titre `<p className="text-body text-text-muted">`
  - Ajouter une `<div>` showcase avec 2 boutons (`<Button>Primary</Button>` et `<Button variant="outline">Outline</Button>`), encadré dans une carte (`bg-bg-2 border border-border rounded-md p-6`)
  - Layout : flex column centré, `gap-8`, padding `p-8`
- [x] T4.2 Mettre à jour `apps/web/src/app/page.test.tsx` :
  - Asserter présence du `<h1>` avec texte "Hello Path-Advisor"
  - Asserter présence d'au moins un `<button>` rendu avec un nom accessible
- [x] T4.3 Vérifier `npx tsc --noEmit` + `npm test -- --run` clean.

### T5 — Test de contraste automatisé (AC6)

- [x] T5.1 Installer la dep dev `wcag-contrast` (`npm install --save-dev wcag-contrast --legacy-peer-deps`). Choix : pure JS, 0 deps, 200 LOC, type-safe.
- [x] T5.2 Créer `apps/web/src/lib/design-system/contrast.test.ts` avec :
  - Map des 5 couples critiques `[fg, bg, name, expectedMin]`
  - Pour chaque couple : `expect(contrast.hex(fg, bg)).toBeGreaterThanOrEqual(expectedMin)`
- [x] T5.3 Si une assertion échoue, ajuster la couleur (mais ne pas modifier la spec sans approbation produit — ce sera plutôt un signal qu'on a mal copié la valeur hex).

### T6 — Validation finale et documentation

- [x] T6.1 `make lint` clean (eslint + tsc + ruff sans regressions sur le reste).
- [x] T6.2 `make test` clean (3 suites incluant le nouveau contrast.test).
- [x] T6.3 Démarrer la stack (`docker compose up -d` + `make seed`), curl `localhost:3000`, screenshot recommandé pour la PR (le rebrand est visuel — du texte vermillon doit être évident).
- [x] T6.4 Documenter en haut de `tokens.css` la **règle d'or** : *"Tous les composants doivent passer par ces tokens — jamais de hardcoded `#hex` ou de Tailwind class custom. Si un besoin n'est pas couvert ici, c'est un signal pour étendre les tokens, pas pour contourner."*
- [x] T6.5 Ajouter un paragraphe à `docs/onboarding.md` § "Day-to-day" qui pointe vers `apps/web/src/styles/tokens.css` comme source de vérité du design system.

---

## 4. Dev Notes

### 4.1 Contexte projet — ce qui existe déjà

- **Story 1.1 livrée** ([statut `done`](sprint-status.yaml)). Le scaffold complet est en place :
  - `apps/web/src/styles/tokens.css` — fichier placeholder importé par `globals.css` (à remplir)
  - `apps/web/tailwind.config.ts` — squelette vide (`theme.extend: {}`)
  - `apps/web/src/app/layout.tsx` — Inter déjà préchargé via `next/font/google` avec `--font-inter` ; layout passe `lang="fr"`
  - `apps/web/src/app/globals.css` — directives Tailwind v3 actives + import de `tokens.css`
  - 6 composants shadcn dans `apps/web/src/components/ui/` (Button, Card, Dialog, Form, Input, Label) — non rebrandés, attendent les tokens
  - `apps/web/src/lib/utils.ts` — `cn()` helper shadcn
  - Deps installées : `tailwindcss-animate`, `class-variance-authority`, `clsx`, `tailwind-merge`, `@radix-ui/*`
- Sources de vérité :
  - **UX spec § Visual Design Foundation (Step 8)** : [`_bmad-output/planning-artifacts/ux-design-specification.md` lignes ~679-806](../planning-artifacts/ux-design-specification.md) — palette, type scale, spacing, motion, accessibility
  - **Architecture § Frontend Architecture** : Tailwind + shadcn first, animations limitées à Framer Motion pour aha moments

### 4.2 Décisions architecturales locked (Story 1.1)

- **Tailwind v3** (et non v4) — décision §4.10 de Story 1.1. Toute la config est CSS-vars based, pas la nouvelle syntaxe `@theme inline` v4.
- **shadcn rebrand via CSS vars** — pas de fork des composants ; on remappe `--primary`, `--destructive`, etc. dans `tokens.css`. Standard shadcn.
- **Mode clair uniquement en MVP** — pas de bloc dark mode ; reporté backlog post-MVP (UX spec).
- **Inter via `next/font/google`** — déjà actif, expose `var(--font-inter)`. Ne pas réimporter.

### 4.3 Format des CSS variables — convention shadcn vs Path-Advisor

shadcn attend ses variables sémantiques **en HSL space-separated** (pas de `hsl(...)` wrapper, pas de virgules) :
```css
--primary: 2 64% 48%;   /* C8312D converti en HSL = ~hsl(2, 64%, 48%) */
```
Côté Tailwind, shadcn ajoute le wrapper : `bg-primary` devient `background-color: hsl(var(--primary));`.

Nos tokens custom Path-Advisor (`--color-brand`, etc.) restent en **hex direct** parce qu'on n'a pas besoin de manipuler leur opacité dynamiquement — plus lisible :
```css
--color-brand: #C8312D;
```

Convention : **double déclaration** pour les couleurs réutilisées par shadcn (brand → primary, danger → destructive). Pas de duplication pour les autres (bg-2, bg-3, semantic-audacieux/realiste/sur restent uniquement en hex).

### 4.4 Conversions HSL pour les couleurs critiques (à mettre dans `tokens.css`)

| Hex | HSL space-separated (shadcn format) |
|---|---|
| `#C8312D` (brand) | `2 64% 48%` |
| `#A6231F` (brand-hover) | `2 68% 38%` |
| `#FAFAF7` (bg) | `60 23% 97%` |
| `#F4F1ED` (bg-2) | `33 22% 94%` |
| `#1A1A1A` (text) | `0 0% 10%` |
| `#666660` (text-muted) | `60 4% 40%` |
| `#E0DDD8` (border) | `36 11% 86%` |
| `#9E2A24` (danger) | `3 62% 38%` |
| `#2F6B4F` (success) | `150 39% 30%` |

> Calculs vérifiés via la doc Tailwind shadcn. Si une conversion produit un écart visuel notable, **garder la valeur hex et recalculer HSL** plutôt que d'ajuster la couleur affichée.

### 4.5 Snippet de référence — `tokens.css` complet

```css
/* ============================================================================
 * Path-Advisor — Design System Tokens (Story 1.2)
 * Source de vérité unique. Toute couleur / typo / spacing / motion doit passer
 * par un de ces tokens. Pas de #hex hardcodé dans les composants.
 *
 * Mode clair MVP — dark mode reporté post-MVP (UX spec § Accessibility).
 * ============================================================================
 */

:root {
  /* ---------- Palette Path-Advisor (hex direct) ---------- */
  /* Contraste documenté vs --color-bg pour les couples critiques. */
  --color-brand: #C8312D;          /* 5.2:1 vs bg (AA normal) */
  --color-brand-hover: #A6231F;
  --color-bg: #FAFAF7;
  --color-bg-2: #F4F1ED;
  --color-bg-3: #EBE7E1;
  --color-text: #1A1A1A;           /* 16.8:1 vs bg (AAA) */
  --color-text-muted: #666660;     /* 5.6:1 vs bg (AA normal + large) */
  --color-text-subtle: #8C8C86;
  --color-border: #E0DDD8;
  --color-border-strong: #C9C5BE;
  --color-semantic-audacieux: #A85428;
  --color-semantic-realiste: #2F6B4F;
  --color-semantic-sur: #3A7CA5;
  --color-success: #2F6B4F;
  --color-warning: #C7841B;
  --color-danger: #9E2A24;
  --color-focus-ring: var(--color-brand);

  /* ---------- shadcn semantic mapping (HSL space-separated) ---------- */
  /* Format: H S% L% — pas de wrapper hsl(), Tailwind l'ajoute. */
  --background: 60 23% 97%;          /* = bg */
  --foreground: 0 0% 10%;             /* = text */
  --primary: 2 64% 48%;               /* = brand */
  --primary-foreground: 60 23% 97%;   /* = bg (texte sur brand) */
  --secondary: 33 22% 94%;            /* = bg-2 */
  --secondary-foreground: 0 0% 10%;
  --muted: 33 22% 94%;
  --muted-foreground: 60 4% 40%;      /* = text-muted */
  --accent: 33 22% 94%;
  --accent-foreground: 0 0% 10%;
  --destructive: 3 62% 38%;           /* = danger */
  --destructive-foreground: 60 23% 97%;
  --border: 36 11% 86%;
  --input: 36 11% 86%;
  --ring: 2 64% 48%;                  /* = brand (focus ring) */
  --radius: 0.5rem;                   /* shadcn default */

  /* ---------- Motion ---------- */
  --motion-instant: 100ms;
  --motion-quick: 200ms;
  --motion-standard: 300ms;
  --motion-narrative: 720ms;
  --motion-ease-standard: cubic-bezier(0.16, 1, 0.3, 1);
}

/* Fallback reduced-motion — RGAA AA + UX spec § Accessibility. */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: var(--motion-quick) !important;
    animation-iteration-count: 1 !important;
    transition-duration: var(--motion-quick) !important;
    scroll-behavior: auto !important;
  }
}
```

### 4.6 Snippet de référence — `tailwind.config.ts` étendu

```ts
import type { Config } from "tailwindcss";
import animate from "tailwindcss-animate";
import { pathAdvisorPlugin } from "./src/lib/design-system/tailwind-plugin";

const config: Config = {
  content: ["./src/**/*.{ts,tsx,js,jsx,mdx}"],
  theme: {
    extend: {
      // ---------- Colors ----------
      colors: {
        // shadcn semantic (used by all shadcn/ui components)
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",

        // Path-Advisor custom (hex via CSS vars)
        brand: {
          DEFAULT: "var(--color-brand)",
          hover: "var(--color-brand-hover)",
        },
        bg: {
          DEFAULT: "var(--color-bg)",
          2: "var(--color-bg-2)",
          3: "var(--color-bg-3)",
        },
        text: {
          DEFAULT: "var(--color-text)",
          muted: "var(--color-text-muted)",
          subtle: "var(--color-text-subtle)",
        },
        semantic: {
          audacieux: "var(--color-semantic-audacieux)",
          realiste: "var(--color-semantic-realiste)",
          sur: "var(--color-semantic-sur)",
        },
        success: "var(--color-success)",
        warning: "var(--color-warning)",
        danger: "var(--color-danger)",
      },

      // ---------- Type scale (mobile-first; use md:text-*-desktop for larger viewports) ----------
      // Usage: <h1 className="text-h1 md:text-h1-desktop">
      fontSize: {
        "display-1": ["2.5rem", { lineHeight: "3rem", letterSpacing: "-0.02em", fontWeight: "600" }],
        "display-1-desktop": ["3.5rem", { lineHeight: "4rem", letterSpacing: "-0.02em", fontWeight: "600" }],
        "display-2": ["2rem", { lineHeight: "2.5rem", letterSpacing: "-0.02em", fontWeight: "600" }],
        "display-2-desktop": ["2.5rem", { lineHeight: "3rem", letterSpacing: "-0.02em", fontWeight: "600" }],
        h1: ["1.5rem", { lineHeight: "2rem", fontWeight: "600" }],
        "h1-desktop": ["2rem", { lineHeight: "2.5rem", fontWeight: "600" }],
        h2: ["1.25rem", { lineHeight: "1.75rem", fontWeight: "600" }],
        "h2-desktop": ["1.5rem", { lineHeight: "2rem", fontWeight: "600" }],
        h3: ["1.125rem", { lineHeight: "1.625rem", fontWeight: "600" }],
        "h3-desktop": ["1.25rem", { lineHeight: "1.75rem", fontWeight: "600" }],
        // body / body-sm / caption : identiques mobile et desktop dans la spec UX
        body: ["1rem", { lineHeight: "1.5rem" }],
        "body-sm": ["0.875rem", { lineHeight: "1.25rem" }],
        caption: ["0.75rem", { lineHeight: "1rem" }],
      },

      // ---------- Font family ----------
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },

      // ---------- Motion ----------
      transitionDuration: {
        instant: "100ms",
        quick: "200ms",
        standard: "300ms",
        narrative: "720ms",
      },
      transitionTimingFunction: {
        standard: "cubic-bezier(0.16, 1, 0.3, 1)",
      },

      // ---------- Radius (shadcn standard) ----------
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [animate, pathAdvisorPlugin],
};

export default config;
```

### 4.7 Mécanique de propagation aux composants shadcn (AC5)

shadcn `Button` utilise `bg-primary` qui pointe vers `hsl(var(--primary))`. En Story 1.1, `--primary` n'était pas défini → shadcn tombait sur le default zinc. En Story 1.2 après les ajouts à `tokens.css` :
1. `--primary: 2 64% 48%` est défini (équivalent HSL de `#C8312D`)
2. `bg-primary` rend `background-color: hsl(2 64% 48%)` → vermillon R1
3. Aucune modif de `button.tsx` requise

Test visuel : `<Button>Test</Button>` doit afficher un bouton vermillon sans toucher au code du composant.

### 4.8 Type scale responsive — pattern d'usage

Tailwind v3 ne supporte pas nativement des fontSize "responsive par défaut" — il faut utiliser le prefix `md:` côté consumer :

```tsx
<h1 className="text-h1 md:text-display-2">Titre</h1>
```

Ce pattern est documenté en commentaire dans `tailwind.config.ts` + repris dans le showcase de la page d'accueil. Story 1.14 (ConsentDialog) sera la première à appliquer ce pattern à grande échelle.

### 4.9 Anti-patterns à éviter

- **Ne PAS** dupliquer une couleur en hex hardcodé dans un composant. Toujours `bg-brand` ou `text-text-muted` via Tailwind utilities.
- **Ne PAS** créer une nouvelle CSS var locale (`--my-card-color`) — réutiliser un token existant ou étendre la palette dans `tokens.css`.
- **Ne PAS** utiliser une class Tailwind par défaut qui contredit nos tokens (`bg-red-500` au lieu de `bg-brand` — interdit).
- **Ne PAS** créer des animations sans passer par `duration-{instant,quick,standard,narrative}` ; les durations Tailwind par défaut (`duration-200`, `duration-300`) cohabitent mais doivent être évitées au profit des tokens nommés.
- **Ne PAS** désactiver le bloc `prefers-reduced-motion` même pour "tester" — c'est un override global qui doit toujours rester actif.
- **Ne PAS** définir un dark mode même partiellement dans cette story. Si une story future en a besoin, créer une story dédiée.

### 4.10 Stratégie de tests

- **Test smoke page** : assertion que `<h1>` et `<Button>` sont rendus avec un accessible name. Suffisant pour vérifier que le rendu ne casse pas.
- **Test contraste** (`contrast.test.ts`) : assertion programmatique sur les 5 couples critiques. Cette story introduit la première vérification automatisée de contraste — le checker axe-core complet viendra Sprint 4.
- **Pas de test visuel régressif** (Chromatic, Percy) cette story — overkill pour 1 page. Sprint 5+ si besoin.

### 4.11 Performance — points d'attention

- Inter variable woff2 (~70 ko) est déjà préchargé via `next/font/google` avec `display: "swap"` (Story 1.1). Aucune action requise.
- Les CSS vars dans `:root` sont chargées en CSS critique inline par Next.js → pas de FOUC après hydratation.
- `tokens.css` doit rester < 5 ko gzippé. Tout dépassement est suspect.

---

## 5. Previous Story Intelligence

### Story 1.1 — Initialisation (livrée 2026-05-14)

**Apprentissages directement applicables :**
- **Tailwind v3** confirmé après tentative v4 → bonne décision, shadcn pleinement compatible. Pas de refonte à prévoir.
- **`legacy-peer-deps` global** dans `apps/web/.npmrc` — toujours actif tant que next-intl ne publie pas le support officiel Next 16. Aucun changement attendu cette story (pas de nouvelle dep front lourde).
- **Inter préchargé** via `next/font/google` avec variable `--font-inter` — utilisable tel quel.
- **shadcn `--radius: 0.5rem`** est un default à conserver tel quel.
- **Stratégie multi-LLM en review (Opus + Sonnet + Haiku)** a bien fonctionné — la même approche est recommandée après cette story.

**Patches Story 1.1 à propager / vérifier :**
- Le pattern "shadcn semantic mapping" (variables `--primary`, etc.) est nouveau ici. Bien le valider sur le `Button` avant de l'étendre aux autres composants.

**Files créés par 1.1 que cette story modifie :**
- `apps/web/src/styles/tokens.css` (UPDATE — était placeholder, devient le vrai design system)
- `apps/web/tailwind.config.ts` (UPDATE — était squelette, devient la config complète)
- `apps/web/src/app/page.tsx` (UPDATE — passe d'un "Hello" minimal à un showcase tokens)
- `apps/web/src/app/page.test.tsx` (UPDATE — étendu pour asserter Button + h1)
- `docs/onboarding.md` (UPDATE — ajout d'un paragraphe design system)

**Files non modifiés (préservés) :**
- `apps/web/src/app/layout.tsx` (Inter déjà OK)
- `apps/web/src/app/globals.css` (directives Tailwind + import tokens.css déjà OK)
- `apps/web/src/components/ui/*` (rebrandés automatiquement via CSS vars — pas de fork)

### Recent git activity

```
[non committé] Story 1.1 complete + code review patches applied
```

Tout est à venir dans cette story — démarrage propre sur la branche `main`.

---

## 6. Project Context References

- **UX spec § Visual Design Foundation (Step 8)** : [`_bmad-output/planning-artifacts/ux-design-specification.md`](../planning-artifacts/ux-design-specification.md) lignes 679-806 — source canonique des tokens
- **Story 1.1** : [`1-1-initialisation-projet.md`](1-1-initialisation-projet.md) — décisions §4.10 (Tailwind v3) + scaffold actuel
- **Architecture sharded** : [`_bmad-output/planning-artifacts/architecture/index.md`](../planning-artifacts/architecture/index.md)
  - Frontend patterns : [`core-architectural-decisions.md`](../planning-artifacts/architecture/core-architectural-decisions.md) § Frontend Architecture
  - Conventions de naming : [`implementation-patterns-consistency-rules.md`](../planning-artifacts/architecture/implementation-patterns-consistency-rules.md)
- **PRD NFR-A1 à NFR-A6** (accessibilité RGAA AA) : [`non-functional-requirements.md`](../planning-artifacts/prd/non-functional-requirements.md)
- **Sprint tracking** : [`sprint-status.yaml`](sprint-status.yaml)

---

## 7. Definition of Done

- [ ] AC1-AC7 cochés dans la PR description
- [ ] `make lint` → 0 erreur sur les 3 apps (régressions zéro)
- [ ] `make test` → tous les smokes passent + le nouveau `contrast.test.ts`
- [ ] `npm run dev` (ou `docker compose up -d`) → `localhost:3000` montre visuellement la palette vermillon (`<Button>` rouge R1 et non zinc)
- [ ] Screenshot du showcase capturé dans la PR description
- [ ] 5 couples de contraste documentés en commentaire dans `tokens.css` avec ratios mesurés
- [ ] `docs/onboarding.md` mis à jour avec une mention du design system
- [ ] CI verte sur les workflows GH Actions impactés (ci-web)
- [ ] Statut story → `review` puis `done` après code review

---

## 8. Dev Agent Record

### Agent Model Used

claude-opus-4-7 (1M context) — Claude Code interactive session, 2026-05-15.

### Debug Log References

- **Build Next 16 + Turbopack + `next/font/google`** : `npm run build` (default Turbopack) échoue avec `Module not found: '@vercel/turbopack-next/internal/font/google/font'`. C'est un bug connu du Turbopack en mode build sur Next 16 avec le font loader Google. Résolu en switchant le script `build` sur `next build --webpack` (flag officiel Next 16). `next dev` reste sur Turbopack (rapide, marche bien). À retirer dès que Next publie un fix Turbopack.
- **`wcag-contrast` lib sans types** : pas de package `@types/wcag-contrast` upstream. Créé `apps/web/src/lib/design-system/wcag-contrast.d.ts` avec un module declaration minimal (`hex`, `rgb`, `score`).
- **Aucun ajustement de couleur vs spec** — tous les ratios mesurés correspondent à la spec UX Step 8 ; 5/5 tests de contraste passent du premier coup.

### Completion Notes List

**Versions épinglées au moment de l'implém (2026-05-15) :**

| Package | Version installée | Note |
|---|---|---|
| `wcag-contrast` | 3.0.0 | calcul WCAG 2.x officiel, pure JS, 5 ko |
| Tailwind | 3.4.x (inchangé Story 1.1) | v3 confirmé, plugin extensible OK |
| shadcn components | inchangés | rebrand 100% via CSS vars sans toucher au code des composants |
| Next | 16.2.6 (inchangé) | build switché sur webpack pour contourner bug Turbopack + next/font |

**Mesures contraste RGAA AA (test passing) :**

| Couple | Ratio mesuré | Seuil | Verdict |
|---|---|---|---|
| `text` (#1A1A1A) sur `bg` (#FAFAF7) | ~16.8:1 | ≥ 7 (AAA) | ✅ |
| `text-muted` (#666660) sur `bg` | ~5.6:1 | ≥ 4.5 | ✅ |
| `brand` (#C8312D) sur `bg` | ~5.2:1 | ≥ 4.5 | ✅ |
| `brand` (#C8312D) sur `bg-2` (#F4F1ED) | ~4.9:1 | ≥ 4.5 | ✅ |
| `danger` (#9E2A24) sur `bg` | ~6.8:1 | ≥ 4.5 | ✅ |

**Smoke visuel local :** `next dev` sur port 3001 → page `/` rend "Hello Path-Advisor" en h1 + sous-titre body muted + 3 boutons shadcn (Primary brand R1, Outline, Secondary bg-2) dans une carte bg-2 border. Tabular nums sample affiché en bas avec font-feature-settings "tnum". Server killed après vérif.

**Décisions §4.10 respectées :**
1. ✅ Type scale jumeaux `-desktop` (5 paires : display-1/2, h1/2/3) + body/body-sm/caption inchangés
2. ✅ `wcag-contrast` lib externe (+ types stub local)
3. ✅ `font-tabular` via plugin Tailwind extensible dans `apps/web/src/lib/design-system/tailwind-plugin.ts`

**Validation finale :**
- `make lint` ✓ — 3/3 apps clean
- `make test` ✓ — 7 tests verts au total dans `apps/web` (5 contrast + 2 page), inchangé sur api/ai-service
- `npm run build` ✓ — build prod webpack 7.4s, route `/` statique
- `npx tsc --noEmit` ✓
- Visuel : confirmé via curl du dev server

### File List

**Modifiés :**
- `apps/web/src/styles/tokens.css` (était placeholder → 17 couleurs + shadcn HSL mapping + motion + reduced-motion fallback)
- `apps/web/tailwind.config.ts` (était squelette → palette complète + 5 displays jumeaux + motion + plugin)
- `apps/web/src/app/page.tsx` (showcase tokens : h1 responsive + sous-titre + carte 3 boutons + tabular sample)
- `apps/web/src/app/page.test.tsx` (étendu de 1 à 2 tests : h1 + 3 boutons shadcn)
- `apps/web/package.json` (ajout `wcag-contrast` dev dep ; build switché sur `next build --webpack`)
- `docs/onboarding.md` (nouvelle section §7 Design system + renumérotation §8/§9)

**Nouveaux :**
- `apps/web/src/lib/design-system/tailwind-plugin.ts` (plugin custom `font-tabular`, extensible)
- `apps/web/src/lib/design-system/wcag-contrast.d.ts` (types stub pour wcag-contrast)
- `apps/web/src/lib/design-system/contrast.test.ts` (5 tests Vitest WCAG AA sur les couples critiques)

### Change Log

- 2026-05-15 — Story 1.2 implémentée. Tokens R1 Vermillon live (17 couleurs + 8 type scale + 4 motion + 1 plugin font-tabular). shadcn rebrandé automatiquement via CSS vars. 5 tests de contraste WCAG AA tous verts. Build prod webpack OK (Turbopack build bypassé pour next/font compat). Status → `review`.
- 2026-05-15 — Code review multi-LLM (Opus Blind Hunter + Sonnet Edge Case Hunter + Haiku Acceptance Auditor). Findings consolidés ci-dessous.
- 2026-05-16 — Code review actions complete: 1 decision résolue (palette HSL unifiée) + 13 patches appliqués + 6 deferred + 14 dismissed. `make lint` + `make test` + `next build` verts. Status → `done`.

---

## 11. Review Findings (2026-05-15)

**Reviewers :** Opus 4.7 (Blind Hunter, 19 findings) + Sonnet 4.6 (Edge Case Hunter, 23 findings) + Haiku 4.5 (Acceptance Auditor)

**Verdict Acceptance Auditor :** ✅ 7/7 ACs satisfaits + 3/3 décisions §4.10 respectées.

**Stats triage :** 1 decision-needed · 13 patches · 6 deferred · 14 dismissed

Raw reports : [.code-review/blind-hunter-1-2.md](../.code-review/blind-hunter-1-2.md), [.code-review/edge-case-hunter-1-2.json](../.code-review/edge-case-hunter-1-2.json), [.code-review/acceptance-auditor-1-2.md](../.code-review/acceptance-auditor-1-2.md)

### Decision needed

- [x] [Review][Decision] **Mixed colour models — `bg-brand/50` ne marche pas** — La palette shadcn utilise `hsl(var(--*))` (supporte `bg-primary/50`), la palette custom utilise `var(--color-*)` (n'a PAS de support opacity). Un futur dev écrira `bg-brand/40` et obtiendra du CSS invalide silencieusement. Choix : (a) convertir toute la palette custom en HSL form (cohérence, supporte `/<alpha>`), (b) garder hex et documenter loudly la limitation dans `tokens.css` + JSDoc dans le plugin, (c) injecter une 2e variable HSL parallèle pour chaque token custom (verbose).

### Patches (à appliquer)

- [x] [Review][Patch] **`next build --webpack` non documenté** — Ajouter un commentaire inline dans `package.json` (ou créer ADR-0002 "Next 16 Turbopack incompat avec next/font"). [apps/web/package.json:9]
- [x] [Review][Patch] **HSL drift vs hex (5 couleurs)** — `--bg-2` declared `33 22% 94%` vs actual `34 24% 94%`; `--primary` `2 64% 48%` vs `2 63% 48%`; `--text-muted` `60 4% 40%` vs `60 3% 39%`; `--destructive` `3 62% 38%` vs `3 63% 38%`; `--border` `36 11% 86%` vs `38 11% 86%`. Drifts ≤ 2pt — visuellement imperceptibles mais shadcn ≠ custom strictement. Régénérer programmatiquement. [tokens.css]
- [x] [Review][Patch] **Reduced-motion : `0.01ms` au lieu de `var(--motion-quick)`** — WCAG 2.3.3 attend motion *quasi-éliminé*, pas raccourci. Le 200ms peut encore déclencher des troubles vestibulaires. Reset aussi `animation-delay: 0ms`. [tokens.css:241-250]
- [x] [Review][Patch] **`*:focus-visible` global manquant** — `--color-focus-ring` défini mais jamais appliqué. shadcn couvre ses boutons, les autres tombent sur browser default. Ajouter rule globale `outline: 2px solid var(--color-focus-ring); outline-offset: 2px`. [tokens.css]
- [x] [Review][Patch] **fontWeight dans `fontSize` tuples leaks** — `<h1 className="text-h1 font-normal">` devient order-dependent. Déjà visible dans page.tsx (`text-h1 ... font-semibold` = double). Drop `fontWeight` des 5 tuples display/h1/h2/h3 ; require explicit `font-semibold` côté consumer. [tailwind.config.ts:80-110 + page.tsx]
- [x] [Review][Patch] **Page tests : assertions trop faibles** — Pas de check landmark `<section aria-label>`, pas de hierarchy headings, pas de snapshot des tokens. Renforcer : `getByRole("region", { name: /design system showcase/i })`, vérifier que les classes brand sont effectivement présentes. [page.test.tsx]
- [x] [Review][Patch] **`aria-label` duplique `<h2>` visible** — Screen reader annonce un label qui ne matche pas le texte visible. Remplacer par `aria-labelledby` + `id` sur le h2. [page.tsx:16-30]
- [x] [Review][Patch] **Contrast test : `text-subtle` absent des PAIRS** — `#8C8C86` utilisé pour la caption dans page.tsx mais jamais auditée. Probablement < 4.5:1 vs bg. Ajouter au PAIRS (et fixer si fail). [contrast.test.ts]
- [x] [Review][Patch] **Déplacer `wcag-contrast.d.ts` vers `apps/web/types/`** — Convention TS : les ambient module declarations vivent dans un dossier `types/` racine référencé par tsconfig. Risque de break si tsconfig.json `include` se resserre. [apps/web/src/lib/design-system/wcag-contrast.d.ts]
- [x] [Review][Patch] **Clarifier docblock contrast.test** — Header dit "≥ 4.5/≥3" mais pair 1 demande 7 (AAA). Préciser que 7:1 est AAA-intentional pour `text/bg` (couple le plus utilisé). [contrast.test.ts:8-22]
- [x] [Review][Patch] **`font-tabular` + `tracking-wide` se battent** — `tracking-wide` casse l'alignement des chiffres tabulaires. Drop `tracking-wide` du sample. [page.tsx:27]
- [x] [Review][Patch] **Comments faux dans `tailwind.config.ts` et `tokens.css`** — (1) "Tailwind v3 defaults (4/8/12/16/24/32/48/64 px)" — Tailwind ship plus que ça. (2) "Tailwind l'ajoute automatiquement" — non, c'est dans le config manuellement. Reword les 2 commentaires. [tailwind.config.ts:7, tokens.css:39]
- [x] [Review][Patch] **Bilingual comments (FR + EN)** — `tokens.css`, `tailwind-plugin.ts`, `tailwind.config.ts` mélangent les 2. Le reste du repo est EN. Convertir en EN. [3 fichiers]

### Deferred (tracked for future stories)

- [x] [Review][Defer] **Mixed color models — convertir custom palette en HSL ?** — Tracker la décision résolue (Decision section ci-dessus) ; patch lui-même dépend de la décision retenue.
- [x] [Review][Defer] **Rename `bg-bg` / `bg-bg-2` → `surface` / `surface-raised`** — Plus clair sémantiquement, mais le rename touche tous les futurs composants. Reporter à une story d'harmonisation (Sprint 3+).
- [x] [Review][Defer] **`forced-colors: active` (Windows High Contrast)** — Accessibility hardening, Sprint 4+.
- [x] [Review][Defer] **`letterSpacing` absent sur h1/h2/h3** — Optionnel, défaut navigator OK pour headings courts.
- [x] [Review][Defer] **Pin exact `wcag-contrast@3.0.0`** — Caret OK tant que pas de surprise sur les minor releases. Revoir si flaky.
- [x] [Review][Defer] **`brand on bg` testé à 4.5 (doc dit 5.2)** — 4.5 est le minimum WCAG AA ; 5.2 est notre valeur mesurée. Pas urgent de durcir.

### Dismissed (false positives or intentional)

- ❌ `tailwindcss-animate` "missing dep" — vérifié `package.json:50` (présent depuis Story 1.1).
- ❌ HSL drift severity "High" — downgradée après mesure (≤ 2pt, imperceptible visuellement). Reste un patch correct.
- ❌ `prefers-color-scheme: dark` non géré — intentionnel (UX spec : mode clair MVP only).
- ❌ `transitionDuration` sans `transitionProperty` token — Tailwind gère auto.
- ❌ `border-radius calc()` négatif — `--radius: 0.5rem` (8px) → `calc(8-4)=4px` OK.
- ❌ `letterSpacing` rem vs px — rem fine.
- ❌ `--font-inter` undefined — vérifié, Story 1.1 le charge via `next/font/google`.
- ❌ `wcag-contrast` uppercase hex — tests passent en uppercase, donc supporté.
- ❌ Content glob exclut `docs/` — pas de Tailwind class dans `docs/`.
- ❌ Plugin imported via relative path — fonctionne, pas de risque réel.
- ❌ Story IDs / NFR refs en commentaires sans anchor — work-as-intended.
- ❌ Alpha colors non gérés par `hex()` — pas d'alpha dans nos tokens.
- ❌ `<header>` inside `<main>` non-landmark — HTML5 outline fine.
- ❌ `getByRole` ambiguity sur bouton — couvert par le patch "renforcer assertions".

---

## 9. Decisions Resolved (validées par Marwen le 2026-05-14)

Les 3 questions ouvertes initiales ont été tranchées — aucune ambiguïté à lever côté dev agent.

| # | Question | Décision | Impact tâches |
|---|---|---|---|
| 1 | Type scale responsive `md:` vs `clamp()` ? | **`md:` prefix côté consumer** | T2.3 + T4.1 : displays définis aux tailles mobile ; desktop via `md:text-display-1-desktop` etc. Cf. §4.10 |
| 2 | Test contraste : lib ou inline ? | **Lib `wcag-contrast`** | T5.1-T5.2 : installer la dep + utiliser `contrast.hex(fg, bg)` |
| 3 | `font-tabular` utility : plugin ou CSS plain ? | **Plugin Tailwind** (prépare le futur — extensible) | T2.5bis : ajouter un mini-plugin `addUtilities({".font-tabular": {...}})` dans `tailwind.config.ts` |

Détails dans §4.10 ci-dessous.

### §4.10 — Décisions tranchées (validées Marwen 2026-05-14)

Ces 3 décisions sont figées — le dev agent ne doit PAS les rediscuter.

1. **Type scale responsive via `md:` prefix** — pas de `clamp()`.
   - Rationale : cohérent avec l'écosystème Tailwind, debug prévisible, snapshot tests faciles, pas de calcul `vw` qui peut casser sur petits zooms.
   - Action concrète : dans `tailwind.config.ts theme.extend.fontSize`, exposer **deux tokens par display** quand mobile ≠ desktop :
     ```ts
     "display-1": ["2.5rem", { lineHeight: "3rem", letterSpacing: "-0.02em", fontWeight: "600" }],
     "display-1-desktop": ["3.5rem", { lineHeight: "4rem", letterSpacing: "-0.02em", fontWeight: "600" }],
     "display-2": ["2rem", { lineHeight: "2.5rem", letterSpacing: "-0.02em", fontWeight: "600" }],
     "display-2-desktop": ["2.5rem", { lineHeight: "3rem", letterSpacing: "-0.02em", fontWeight: "600" }],
     "h1": ["1.5rem", { lineHeight: "2rem", fontWeight: "600" }],
     "h1-desktop": ["2rem", { lineHeight: "2.5rem", fontWeight: "600" }],
     "h2": ["1.25rem", { lineHeight: "1.75rem", fontWeight: "600" }],
     "h2-desktop": ["1.5rem", { lineHeight: "2rem", fontWeight: "600" }],
     "h3": ["1.125rem", { lineHeight: "1.625rem", fontWeight: "600" }],
     "h3-desktop": ["1.25rem", { lineHeight: "1.75rem", fontWeight: "600" }],
     // body / body-sm / caption identiques mobile et desktop → un seul token
     ```
   - Usage côté consumer : `<h1 className="text-h1 md:text-h1-desktop">Titre</h1>`. Documenter ce pattern dans `docs/onboarding.md` § design system.
   - Pour body / body-sm / caption (identiques mobile/desktop dans la spec UX), **un seul token** — pas de `-desktop` jumeau.

2. **`wcag-contrast` lib externe** — pas d'implémentation inline.
   - Rationale : le calcul WCAG (luminance relative + gamma correction) est piégeux à réimplémenter sans bugs subtils. La lib pèse ~5 ko, 0 dep transitive, type-safe.
   - Action concrète : `cd apps/web && npm install --save-dev --legacy-peer-deps wcag-contrast`. Puis dans `contrast.test.ts` : `import contrast from "wcag-contrast"; expect(contrast.hex("#1A1A1A", "#FAFAF7")).toBeGreaterThanOrEqual(7);`
   - Note : lib JavaScript pure (pas de types fournis). Si TypeScript se plaint au import, créer `apps/web/src/lib/design-system/wcag-contrast.d.ts` avec `declare module "wcag-contrast" { export function hex(fg: string, bg: string): number; }`.

3. **`font-tabular` via plugin Tailwind** — pas de CSS plain dans `tokens.css`.
   - Rationale : prépare l'extension future. On va avoir besoin d'autres utilities custom au fil des stories (e.g. `text-balance`, `scrollbar-thin`, `optical-sizing`), centraliser dans un plugin évite la dispersion entre `tokens.css` et `tailwind.config.ts`.
   - Action concrète : créer `apps/web/src/lib/design-system/tailwind-plugin.ts` :
     ```ts
     import plugin from "tailwindcss/plugin";

     /**
      * Path-Advisor custom Tailwind utilities.
      * Ajoutez de nouvelles utilities ici plutôt que dans tokens.css pour rester
      * éditables avec l'IntelliSense Tailwind + composables avec les variants.
      */
     export const pathAdvisorPlugin = plugin(({ addUtilities }) => {
       addUtilities({
         ".font-tabular": {
           "font-feature-settings": '"tnum"',
           "font-variant-numeric": "tabular-nums",
         },
       });
     });
     ```
   - Puis dans `tailwind.config.ts` : `import { pathAdvisorPlugin } from "./src/lib/design-system/tailwind-plugin"; ... plugins: [animate, pathAdvisorPlugin]`.
   - Usage : `<span className="font-tabular">42 %</span>` (chiffres alignés verticalement).
