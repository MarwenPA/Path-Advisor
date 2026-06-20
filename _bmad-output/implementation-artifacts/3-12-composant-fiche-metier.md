# Story 3.12: Composant `FicheMetier` réutilisable

**Epic:** 3 — Recommandation Vocationnelle (Premier Aha)
**Status:** done
**Sprint:** 6 (Recommandation vocationnelle)
**Story Key:** `3-12-composant-fiche-metier`
**Estimation:** M (medium) — composant page produit multi-sections + responsive mobile/desktop + variant print. Pas de backend. Sized ~2 j focused work.

> Composant UI page complète pour la fiche détaillée d'un métier. Indépendant du moteur de scoring — consomme une `Profession` en props. Peut être développé en isolation avec des données mock du référentiel (Story 3.2). Sera intégré par Story 3.5 (fiche métier). Le variant `print-friendly` anticipe l'export conseillère (Epic 5).

---

## 1. User Story

**As a** développeur Path-Advisor,
**I want** un composant `FicheMetier` page produit complète avec sections structurées,
**So that** chaque métier ait une présentation cohérente et exhaustive (UX-DR9), réutilisable depuis la liste des recos (Story 3.4), les liens deep-link et l'export PDF conseillère (Epic 5).

---

## 2. Acceptance Criteria (BDD)

### AC1 — Structure des 6 sections

**Given** le composant est rendu avec une `Profession` complète
**When** je consulte la fiche
**Then** je vois 6 sections dans cet ordre :
1. **Hero** — nom métier (h1), score 0-100 + chip (si props `score` fourni), phrase recopiable + bouton copier, secteur badge
2. **C'est quoi** — `description` de la profession (texte narratif)
3. **Pour qui** — `requirements_json` (liste prérequis : études, compétences, qualités) + `daily_routine` (journée type)
4. **Comment y aller** — `prospects_text` (débouchés et évolutions)
5. **Infos pratiques** — `median_salary_eur` / `salary_range_json` (fourchette salariale) + niveaux compatibles (`level_compatibility`)
6. **Signaux contributifs** — `signals_json` (chips passions / valeurs / spés, cliquables → onSignalClick)

**And** chaque section est wrappée dans `<section aria-labelledby="section-{slug}">` avec un `<h2 id="section-{slug}">` en heading

### AC2 — Responsive mobile (320 px+)

**Given** `variant="mobile"` ou viewport < 1024 px
**When** le composant est rendu
**Then** les sections sont empilées verticalement
**And** les sections 3, 4, 5 ("Pour qui", "Comment y aller", "Infos pratiques") sont collapsées par défaut dans un accordéon (composant shadcn `Accordion`)
**And** la section Hero et "C'est quoi" sont toujours visibles (jamais dans l'accordéon)
**And** les sections accordéon s'ouvrent au tap avec animation `motion-quick` (neutralisée si `prefers-reduced-motion`)
**And** un bouton "Tout afficher" en bas déploie tous les accordéons d'un coup

### AC3 — Responsive desktop (1024 px+)

**Given** viewport ≥ 1024 px
**When** le composant est rendu
**Then** une TOC (Table of Contents) sticky est affichée à gauche (width ~200 px) avec liens ancres vers chaque section
**And** les sections sont affichées en tabs horizontaux (composant shadcn `Tabs`) dans la zone principale
**And** la TOC met en surbrillance la section active au scroll (Intersection Observer)
**And** le layout utilise CSS Grid : `grid-template-columns: 200px 1fr`

### AC4 — Hero section avec score optionnel

**Given** la prop `score` est fournie (cas depuis liste des recos Story 3.4)
**When** le Hero est rendu
**Then** le chip score `ScoreVocationnel` (Story 3.11, variant `expanded`) est intégré dans le Hero
**And** la phrase recopiable est celle issue du scoring, pas une phrase générique

**Given** la prop `score` n'est pas fournie (cas accès direct à la fiche sans scoring)
**When** le Hero est rendu
**Then** le chip score n'est pas affiché
**And** une phrase générique de présentation du métier est affichée à la place

### AC5 — Variant `print-friendly`

**Given** `variant="print"`
**When** le composant est rendu (ou imprimé via `@media print`)
**Then** les sections sont linéarisées en 1 colonne sans TOC, sans accordéon, sans tabs
**And** les CTAs interactifs (boutons copier, chips cliquables, accordéons) ne sont pas rendus
**And** la mise en page est A4 (max-width 210 mm, marges 15 mm)
**And** les couleurs sont adaptées à l'impression (pas de backgrounds colorés, texte noir sur blanc)
**And** le composant est utilisable avec `react-to-print` ou similaire

### AC6 — Accessibilité RGAA AA

**Given** un lecteur d'écran parcourt la fiche
**When** il traverse le composant
**Then** la hiérarchie est stricte : 1 `h1` (nom métier dans Hero) → `h2` par section → `h3` dans les sous-listes si nécessaire
**And** chaque section a un landmark sémantique `<section aria-labelledby="...">`
**And** les accordéons (mobile) ont `aria-expanded` + `aria-controls` corrects
**And** les tabs (desktop) ont `role="tablist"` + `role="tab"` + `aria-selected` (héritage shadcn)
**And** la TOC (desktop) est une `<nav aria-label="Sections de la fiche">` avec liens `<a href="#section-{slug}">`

**Given** `prefers-reduced-motion: reduce`
**When** le composant est rendu
**Then** les animations accordéon et transitions tabs sont désactivées

### AC7 — Section "Signaux contributifs" interactive

**Given** la section "Signaux contributifs" est visible
**When** je consulte les chips
**Then** les chips sont regroupés par catégorie : "Passions" / "Valeurs" / "Spécialités"
**And** chaque chip au clic déclenche `onSignalClick(signalId)` (délégation vers Story 3.6 — drawer explicabilité)
**And** si `onSignalClick` n'est pas fourni, les chips sont en lecture seule (pas de `role="button"`)

### AC8 — Tests

**Given** le composant est testé avec Vitest + RTL
**When** les tests tournent
**Then** les cas suivants passent :
- Render de base : 6 sections présentes, `h1` = nom métier
- Mobile : sections 3-5 en accordéon, collapsées par défaut
- Accordéon : tap sur section 3 → expand, `aria-expanded=true`
- Desktop (mock viewport ≥1024) : TOC présente, tabs visibles
- Score fourni → chip score présent ; score absent → chip score absent
- Variant `print` : accordéons absents, CTAs interactifs absents
- `onSignalClick` appelé au clic d'un chip signal
- Hiérarchie heading : 1 h1, h2 pour chaque section (snapshot)
- Reduced motion : pas d'animation class sur accordéon

---

## 3. Tasks / Subtasks

### T1 — Composant `FicheMetier`

- [x] Créer `apps/web/src/components/professions/FicheMetier.tsx`
- [x] Types TypeScript dans `apps/web/src/components/professions/types.ts` (étendre les types Story 3.11) :
  ```ts
  interface FicheMetierProps {
    profession: Profession // from Story 3.2 schema
    score?: number
    phraseRecopiable?: string
    confidenceLevel?: 'normal' | 'indicative'
    variant?: 'default' | 'print'
    onSignalClick?: (signalId: string) => void
  }
  ```
- [x] Sous-composants internes : `HeroSection`, `RequirementsList`, `DailyRoutine`, `ProspectsList`, `SalaryInfo`, `SignalChipsGrouped`
- [x] Réutilise `ScoreVocationnel` (Story 3.11) pour le Hero si `score` fourni

### T2 — TOC sticky (desktop)

- [x] Créer `apps/web/src/components/professions/FicheMetierTOC.tsx`
- [x] Navigation par ancres (liens `<a href="#section-{key}">`) avec callback `onSectionClick` pour switcher le tab actif
- [x] Mise en surbrillance de la section active (via prop `activeSection`)

### T3 — Storybook stories (si Storybook configuré)

- N/A — Storybook non configuré dans ce projet

### T4 — Tests Vitest + RTL

- [x] Couvrir tous les cas AC8 (26 tests)
- [x] Mock `matchMedia` pour les tests mobile/desktop
- [x] Tests reduced motion via mock `matchMedia`

### Review Findings (code-review 2026-06-20)

- [x] [Review][Decision] `slugify` : labels identiques entre catégories (ex. "SVT" dans passions ET spécialités) produisent le même `signalId` → `onSignalClick` ne peut pas distinguer la catégorie d'origine. Faut-il inclure la catégorie dans l'id passé au handler ? [FicheMetier.tsx:174] → D1-b appliqué : signalId = `${categoryKey}-${slug}`
- [x] [Review][Decision] AC3 — Pas d'IntersectionObserver : la TOC commute un tab (pas de scroll suivi). Avec un layout en tabs il n'y a pas de scroll entre sections. Valider l'intent : (a) garder les tabs sans IO, (b) passer à des sections scrollables avec IO pour la TOC. → D2-b appliqué : scrollable sections + IntersectionObserver
- [x] [Review][Decision] AC2 — `variant="mobile"` mentionné dans la spec mais absent de l'interface `FicheMetierProps` (seuls `default` | `print` sont supportés). Nécessaire en prop explicite ou le viewport-detection suffit ? → D3-b appliqué : `variant="mobile"` ajouté à FicheMetierProps
- [x] [Review][Patch] `aria-controls` référence un panel absent du DOM quand l'accordéon est fermé (conditional render → dangling IDREF). Fix : rendre le panel toujours présent avec `hidden={!isOpen}` au lieu du conditional render. [FicheMetier.tsx:409]
- [x] [Review][Patch] Print + `score` fourni : `ScoreVocationnel` rend encore `CopyButton` et "→ Pourquoi ce score ?" dans `FicheMetierPrint` — CTAs interactifs présents (AC5). Fix : remplacer `ScoreVocationnel` par un affichage statique (score + phrase sans boutons) en mode print. [FicheMetier.tsx:573]
- [x] [Review][Patch] `slugify("")` ou label tout-non-alphanumérique → `signalId=""`. Fix : ajouter un fallback `|| label.toLowerCase().replace(/\s+/g, "-") || "signal"` ou lancer une erreur si le slug est vide. [FicheMetier.tsx:19]
- [x] [Review][Defer] Hydratation SSR flash : `getServerSnapshot` retourne `false` → arbre mobile rendu côté serveur, swap desktop côté client (layout flash). Inhérent à `useSyncExternalStore` + viewport-detection sans SSR guard. — deferred, pre-existing pattern
- [x] [Review][Defer] `mockReducedMotion` et `mockMatchMedia` s'écrasent mutuellement via `Object.defineProperty` — impossible de tester simultanément reduced-motion + desktop. — deferred, test infrastructure limitation
- [x] [Review][Defer] `SalaryInfo` : section "Infos pratiques" blanche si `median_salary_eur`, `salary_range_json` et `level_compatibility` sont tous absents/vides. Pas d'empty-state. — deferred, hors scope story 3.12
- [x] [Review][Defer] `level_compatibility` tokens bruts affichés (ex. "lycee 1ere tle general") sans libellés lisibles. — deferred, référentiel de labels hors scope
- [x] [Review][Defer] "Tout afficher" est one-way (pas de "Tout masquer"). — deferred, non requis par la spec

---

## 4. Dev Notes

### 4.1 Wireframe ASCII — mobile (375 px), sections accordéon

```
┌───────────────────────────────────────────┐
│  ← Infirmier·ère de bloc op.    [Santé]  │ ← Hero h1 + badge secteur
│  ┌──────────────────────────────────────┐ │
│  │ Score : 78/100              indicatif│ │ ← ScoreVocationnel expanded
│  │ "Mon projet est de travailler en…"   │ │
│  │                               [📋]   │ │
│  │ [SVT]  [aider]  [précision]  [hôpital]│ │
│  └──────────────────────────────────────┘ │
│                                           │
│  C'est quoi                               │ ← Section toujours visible
│  Infirmier·ère de bloc opératoire (IBODE) │
│  est un professionnel de santé…           │
│                                           │
│  ▶ Pour qui            [accordéon fermé]  │ ← tap pour ouvrir
│  ▶ Comment y aller     [accordéon fermé]  │
│  ▶ Infos pratiques     [accordéon fermé]  │
│                                           │
│  Signaux contributifs                     │ ← section toujours visible
│  Passions : [SVT] [biologie] [soins]      │
│  Valeurs : [utilité sociale] [contact]    │
│  Spécialités : [SVT] [chimie]             │
│                                           │
│  [ Tout afficher ]                        │ ← déploie tous les accordéons
└───────────────────────────────────────────┘
```

### 4.2 Wireframe ASCII — desktop (1280 px)

```
┌─────────┬──────────────────────────────────────┐
│   TOC   │  Hero : Infirmier·ère de bloc op.     │
│ ──────  │  ────────────────────────────────     │
│ C'est   │  [Tabs: C'est quoi | Pour qui |       │
│ quoi    │   Comment y aller | Infos | Signaux]  │
│ Pour    │                                       │
│ qui     │  [Contenu de l'onglet actif]           │
│ Comment │                                       │
│ y aller │                                       │
│ Infos   │                                       │
│ Signaux │                                       │
│ (sticky)│                                       │
└─────────┴──────────────────────────────────────┘
```

### 4.3 Format `requirements_json` → rendu

```tsx
// Input
requirements_json = [
  { type: "studies", label: "BTS IBODE" },
  { type: "skill", label: "Gestion du stress en urgence" },
  { type: "quality", label: "Précision et rigueur" }
]

// Rendu — groupé par type avec icône Lucide
<h3>Études</h3>
<ul><li>BTS IBODE</li></ul>
<h3>Compétences</h3>
<ul><li>Gestion du stress en urgence</li></ul>
<h3>Qualités</h3>
<ul><li>Précision et rigueur</li></ul>
```

### 4.4 Décisions design verrouillées

- **1 seul `h1` par page** — la hiérarchie heading est stricte, les sections utilisent `h2`
- **Accordéon mobile par défaut fermé** pour les sections 3-5 — réduire la longueur de page perçue, pas une contrainte technique
- **TOC desktop sticky** — `position: sticky; top: 80px` (sous le header nav global)
- **Variant `print` = rendu statique** — pas de `window.print()` dans le composant, c'est le parent qui trigger
- **Section Hero sans Score = fiche générique** — utilisée pour les deep-links directs `/metiers/{slug}` hors contexte de scoring

### 4.5 Items à différer

- Animation fade-in séquentiel des sections (hors scope composant — géré par la page Story 3.5)
- Favoris / "Mes paris" dans le Hero (Story 3.4 — prop `onFavoriteToggle`)
- Section "Écoles cibles" dans le Hero (citée dans l'epic — données disponibles en Epic 4 seulement)
- Revue humaine CTA (Story 3.7 — prop `onRequestHumanReview`)
- Signalement erreur CTA (Story 3.8 — prop `onReportError`)

---

## 5. Project Structure Notes

```
apps/web/src/components/professions/
  FicheMetier.tsx                    ← composant principal (T1)
  FicheMetierTOC.tsx                 ← TOC sticky desktop (T2)
  FicheMetier.stories.tsx            ← Storybook (T3, si configuré)
  types.ts                           ← interfaces (étendu depuis Story 3.11)
  __tests__/
    FicheMetier.test.tsx             ← tests RTL (T4)
    FicheMetierTOC.test.tsx
```

**Conventions à respecter :**
- Tokens CSS uniquement (Story 1.2)
- Aucun appel réseau dans ce composant (props only)
- shadcn/ui : `Accordion`, `Tabs`, `Badge`, `Button`
- Réutilise `ScoreVocationnel` (Story 3.11)

---

## 6. References

- **Epic 3 detail** : `_bmad-output/planning-artifacts/epics/epic-3-recommandation-vocationnelle-premier-aha.md` § Story 3.12
- **Story 3.2** : référentiel professions — fournit le type `Profession`
- **Story 3.4** : liste métiers — navigue vers `FicheMetier` au tap
- **Story 3.5** : fiche métier page — intègre ce composant
- **Story 3.6** : explicabilité — reçoit `onSignalClick`
- **Story 3.7** : revue humaine — prop `onRequestHumanReview` (à ajouter plus tard)
- **Story 3.8** : signalement erreur — prop `onReportError` (à ajouter plus tard)
- **Story 3.11** : `ScoreVocationnel` — intégré dans Hero section
- **Epic 5** : export PDF conseillère — variant `print`
- **UX-DR9** : structure fiche métier

---

## 7. Dev Agent Record

### Agent Model Used
claude-sonnet-4-6

### Completion Notes List

- **T1** : `FicheMetier.tsx` implémenté avec layout responsive via `useSyncExternalStore` + `matchMedia("(min-width: 1024px)")`. Accordéon custom (état React + ARIA complet) pour mobile, tabs custom (role tablist/tab/tabpanel) + TOC pour desktop, layout linéarisé pour print. Sous-composants : `HeroSection`, `RequirementsList`, `SalaryInfo`, `SignalChipsGrouped`, `SectionContent`. Réutilise `ScoreVocationnel` variant `expanded` dans le Hero quand `score` fourni. Déduplication des flatSignals via `Map` pour éviter les clés React dupliquées.
- **T2** : `FicheMetierTOC.tsx` avec `<nav aria-label="Sections de la fiche">`, liens `<a>` vers ancres, mise en surbrillance via prop `activeSection`, callback `onSectionClick` pour synchroniser avec les tabs desktop.
- **T3** : Storybook non configuré → skipped.
- **T4** : 26 tests Vitest + RTL couvrant tous les cas AC8. 26/26 passent, 0 régression. Les 3 échecs pré-existants (`ocr-loader.test.tsx`) sont antérieurs à cette story.

### File List

- `apps/web/src/components/professions/types.ts` (modifié — ajout `Profession`, `FicheMetierProps`, `RequirementItem`, `SignalsByCategory`, `SalaryRange`)
- `apps/web/src/components/professions/FicheMetier.tsx` (créé)
- `apps/web/src/components/professions/FicheMetierTOC.tsx` (créé)
- `apps/web/src/components/professions/__tests__/FicheMetier.test.tsx` (créé)

### Change Log

- 2026-06-20 — Story 3.12 créée (Epic 3 launch). Composant UI indépendant, développable avec mock data Story 3.2.
- 2026-06-20 — Implémentation complète : FicheMetier.tsx + FicheMetierTOC.tsx + types + 26 tests. Story → review.
