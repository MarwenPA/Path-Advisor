# Story 3.6 — Explicabilité des signaux contributifs (RGPD art. 22)

## Status: review

## Story

**As** an élève,  
**I want** to understand which signals contributed to a recommended profession's score,  
**so that** I trust the recommendation and can defend it, in compliance with RGPD art. 22 (FR22).

## Acceptance Criteria

**AC1 — Ouverture du drawer depuis ScoreVocationnel :**  
Given I am on `/mes-metiers` and I see a `ScoreVocationnel` card  
When I tap a signal chip OR tap the "→ Pourquoi ce score ?" button (expanded variant)  
Then a drawer / sheet opens showing the signals that contributed to this score  
And the drawer title is the profession name  
And each signal is explained in plain language: e.g. "Passion soins : +12 pts", "Valeur entraide : +8 pts"

**AC2 — Ouverture depuis FicheMetier :**  
Given I am on `/metiers/[slug]`  
When I tap a signal chip in the "Signaux contributifs" section  
Then the same explicability drawer opens with the relevant signals  
And there is a link "Demander une revue humaine" pointing to Story 3.7 flow  
And there is a link "Comment ça marche" linking to `/methodologie` (static page, deferred — render as `<a>` only)

**AC3 — Contenu du drawer :**  
Given the drawer is open  
When I read the signals  
Then I see a positive copy: "Voilà les ingrédients qui ont fait monter ce métier"  
And each signal row shows: category icon (passion / valeur / spécialité), label in natural language, contribution in pts (e.g. "+12 pts")  
And signals are sorted by contribution descending  
And if signals_contributifs is empty, a fallback message is shown: "Les signaux détaillés ne sont pas disponibles pour ce métier"

**AC4 — Comportement responsive :**  
Given the drawer is controlled by `useIsMobile` (breakpoint 1023px)  
When on mobile (< 1024px)  
Then it renders as `Sheet side="bottom"` (same pattern as ReportErrorButton)  
When on desktop (≥ 1024px)  
Then it renders as `Dialog` centered

**AC5 — Accessibilité :**  
When a screen reader user opens the drawer  
Then the title is announced as the profession name + "— Signaux contributifs"  
And each signal row has a readable `aria-label`  
And focus is trapped inside the drawer  
And Escape closes it

**AC6 — Intégration dans MetiersList / mes-metiers :**  
Given I am on `/mes-metiers`  
When I tap a signal chip on a `ScoreVocationnel` compact card  
Then the explicability drawer opens with the signals_contributifs from that profession  
And the link to the fiche métier still works (tapping the card body, not chips, navigates to the fiche)

**AC7 — Intégration dans la page fiche métier :**  
Given I am on `/metiers/[slug]`  
When the `onSignalClick` prop of `FicheMetier` is wired  
Then tapping any signal chip opens the drawer with the relevant signal details  
And the `signals_contributifs` data must be passed down from the page via URL state or component state (see Dev Notes)

## Tasks / Subtasks

- [x] **Task 1 — Composant `SignauxDrawer`**
  - [x] 1.1 Create `apps/web/src/components/professions/SignauxDrawer.tsx` — `"use client"`, accepts `open`, `onOpenChange`, `metiersName`, `signals: SignalContributif[]`
  - [x] 1.2 Responsive: Sheet (mobile) / Dialog (desktop) using `useIsMobile` pattern from `ReportErrorButton.tsx`
  - [x] 1.3 Render signal list sorted by `contribution` descending, with category icon + label + "+X pts"
  - [x] 1.4 Include "Demander une revue humaine" link and "Comment ça marche" `<a>` link
  - [x] 1.5 Fallback when signals array is empty
  - [x] 1.6 Write Vitest unit tests: renders signals sorted, fallback shown, links present

- [x] **Task 2 — Wiring dans MetiersList (page `/mes-metiers`)**
  - [x] 2.1 Add local state `activeDrawer: { profession: ScoredProfession } | null` in `MetiersList.tsx`
  - [x] 2.2 Pass `onSignalClick` to `ScoreVocationnel` — opens the drawer with that profession's `signals_contributifs`
  - [x] 2.3 Render `<SignauxDrawer>` conditionally below the list, controlled by `activeDrawer`
  - [x] 2.4 Prevent the wrapping `<Link>` from navigating when a chip is clicked (stop propagation)
  - [x] 2.5 Update Vitest test: clicking a signal chip opens the drawer, clicking card body still navigates

- [x] **Task 3 — Wiring dans la page fiche métier `/metiers/[slug]`**
  - [x] 3.1 Make `page.tsx` pass `signals_contributifs` via a client wrapper component (Server Components cannot hold interactive state)
  - [x] 3.2 Create `apps/web/src/app/(authenticated)/metiers/[slug]/FicheMetierClient.tsx` — `"use client"` wrapper that holds `drawerOpen` state + `signals`, renders `<FicheMetier onSignalClick={...} />` + `<SignauxDrawer />`
  - [x] 3.3 `page.tsx` passes `profession` + `score` + `confidenceLevel` + `signalsContributifs` props to `FicheMetierClient`
  - [x] 3.4 `signalsContributifs` are read from `searchParams` (passed as JSON-encoded string from `MetiersList` link OR empty array when navigating directly) — see Dev Notes for the encoding strategy
  - [x] 3.5 Write Vitest test for `FicheMetierClient`: renders FicheMetier, drawer opens on signal click

## Dev Notes

### Composants existants à RÉUTILISER (ne pas recréer)

**Pattern drawer responsive (`ReportErrorButton.tsx`) — COPIER EXACTEMENT CE PATTERN :**
- `useIsMobile()` hook inline (useSyncExternalStore, breakpoint 1023px, server snapshot = false)
- Mobile → `<Sheet side="bottom">` from `@/components/ui/sheet`
- Desktop → `<Dialog>` from `@/components/ui/dialog`
- Imports: `Sheet, SheetContent, SheetHeader, SheetTitle` / `Dialog, DialogContent, DialogHeader, DialogTitle`

**`SignalContributif` interface (ne pas redéfinir) :**
```ts
// from apps/web/src/lib/api/recommendations.ts
export interface SignalContributif {
  signal: string;    // e.g. "passion_soins", "valeur_entraide", "specialite_svt"
  weight: number;    // 0-1 weight in the scoring formula
  contribution: number; // points contributed to the final score (e.g. 12)
}
```

**`ScoreVocationnelProps.onSignalClick` (existant — NE PAS MODIFIER LA SIGNATURE) :**
```ts
onSignalClick?: (signalId: string) => void;
// signalId = SignalContributif.signal (e.g. "passion_soins")
```

**`FicheMetierProps.onSignalClick` (existant — NE PAS MODIFIER LA SIGNATURE) :**
```ts
onSignalClick?: (signalId: string) => void;
```

**Composant `SignauxDrawer` — interface recommandée :**
```tsx
interface SignauxDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  metiersName: string;
  signals: SignalContributif[];
}
```

### Naturalization des labels signaux

`SignalContributif.signal` est au format `category_keyword` (e.g. `"passion_soins"`, `"valeur_entraide"`, `"specialite_svt"`). À convertir en langage naturel :

```ts
function formatSignalLabel(signal: string): { category: "passion" | "valeur" | "spécialité" | "autre"; label: string } {
  const [cat, ...rest] = signal.split("_");
  const label = rest.join(" ").replace(/-/g, " ");
  const categoryMap: Record<string, "passion" | "valeur" | "spécialité" | "autre"> = {
    passion: "passion",
    valeur: "valeur",
    specialite: "spécialité",
  };
  return {
    category: categoryMap[cat] ?? "autre",
    label: label.charAt(0).toUpperCase() + label.slice(1),
  };
}
```

### Stratégie pour passer `signals_contributifs` à la fiche métier

Le Server Component `page.tsx` reçoit les `searchParams`. La stratégie recommandée est :

**Option A (recommandée) : JSON encodé en query param**
- `MetiersList.tsx` encode les signaux dans le lien :
  ```ts
  const encodedSignals = encodeURIComponent(JSON.stringify(p.signals_contributifs));
  href={`/metiers/${p.slug}?score=${p.score}&confidence=${p.confidence_level}&signals=${encodedSignals}`}
  ```
- `page.tsx` decode depuis `searchParams.signals`, parse JSON, valide la shape (array de `{signal, weight, contribution}`), fallback sur `[]` si absent/malformé
- `page.tsx` passe `signalsContributifs` à `FicheMetierClient` comme prop

**Avantages** : pas de state management côté client, fonctionne sur accès direct URL (signals = []) et depuis MetiersList (signals présents).

**Garde obligatoire** dans `page.tsx` :
```ts
function parseSignals(raw: string | undefined): SignalContributif[] {
  if (!raw) return [];
  try {
    const parsed = JSON.parse(decodeURIComponent(raw));
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(
      (s) => typeof s.signal === "string" && typeof s.contribution === "number"
    );
  } catch {
    return [];
  }
}
```

### Wrapper client `FicheMetierClient`

`FicheMetier` est `"use client"` mais `page.tsx` est un Server Component. Il faut un wrapper pour gérer l'état du drawer :

```tsx
// apps/web/src/app/(authenticated)/metiers/[slug]/FicheMetierClient.tsx
"use client";

import { useState } from "react";
import { FicheMetier } from "@/components/professions/FicheMetier";
import { SignauxDrawer } from "@/components/professions/SignauxDrawer";
import type { SignalContributif } from "@/lib/api/recommendations";
import type { FicheMetierProps } from "@/components/professions/types";

interface FicheMetierClientProps extends Omit<FicheMetierProps, "onSignalClick"> {
  signalsContributifs: SignalContributif[];
}

export function FicheMetierClient({ signalsContributifs, ...ficheProps }: FicheMetierClientProps) {
  const [drawerSignals, setDrawerSignals] = useState<SignalContributif[]>([]);
  const [drawerOpen, setDrawerOpen] = useState(false);

  function handleSignalClick(signalId: string) {
    const found = signalsContributifs.filter((s) => s.signal === signalId);
    setDrawerSignals(found.length ? found : signalsContributifs);
    setDrawerOpen(true);
  }

  return (
    <>
      <FicheMetier {...ficheProps} onSignalClick={handleSignalClick} />
      <SignauxDrawer
        open={drawerOpen}
        onOpenChange={setDrawerOpen}
        metiersName={ficheProps.profession.name}
        signals={drawerSignals}
      />
    </>
  );
}
```

**Note** : si `signalId` n'est pas trouvé dans `signalsContributifs` (accès direct sans query params), ouvrir le drawer avec tous les signaux disponibles (ou drawer vide si `signalsContributifs = []`).

### Stop propagation dans MetiersList

Le `ScoreVocationnel` est wrappé dans un `<Link>`. Taper sur un chip ne doit PAS déclencher la navigation :

```tsx
// Dans le handler onSignalClick de MetiersList
onSignalClick={(signalId) => {
  // Ne pas stopper l'event ici — ScoreVocationnel / SignalChips gèrent les boutons
  // La stop propagation est déjà implicite car les chips sont des <button> dans un <Link>
  // Next.js Link ne navigue pas sur click d'éléments interactifs enfants
  setActiveDrawer({ profession: p });
}}
```

**Test à écrire** : vérifier que cliquer sur un chip n'appelle pas `router.push`.

### UX Copy — ton positif obligatoire

| ❌ À éviter | ✅ À utiliser |
|---|---|
| "Justification du score" | "Voilà les ingrédients qui ont fait monter ce métier" |
| "Votre profil manque de données" | (ne jamais afficher) |
| "Score basé sur..." | "Ce métier monte parce que..." |
| "Contribution légale requise" | (jamais) |

Header du drawer : **"Pourquoi ce métier ?"**  
Sous-titre : **"Voilà les ingrédients qui ont fait monter {metiersName}"**

### Icônes par catégorie (lucide-react — déjà installé)

```ts
import { Heart, Star, BookOpen, Zap } from "lucide-react";

const CATEGORY_ICONS = {
  passion: Heart,
  valeur: Star,
  "spécialité": BookOpen,
  autre: Zap,
};
```

### Règles qualité

- **`"use client"` uniquement sur `SignauxDrawer` et `FicheMetierClient`** — `page.tsx` reste Server Component pur
- **`page.tsx` ne doit pas importer de composants client directement** — les passer via `FicheMetierClient`
- **La navigation depuis MetiersList ne doit pas casser** — vérifier que le `<Link>` fonctionne encore après l'ajout du drawer
- **Pas de `react-query` / `SWR`** — les signaux viennent du query param, pas d'un appel API séparé
- **Tests Vitest** (pas Cypress) — tous les tests unitaires utilisent `@testing-library/react` + `vi.mock`
- **Pas de nouveau endpoint Django** — tout est côté frontend

### Fichiers à créer / modifier

**CRÉER :**
- `apps/web/src/components/professions/SignauxDrawer.tsx`
- `apps/web/src/components/professions/__tests__/SignauxDrawer.test.tsx`
- `apps/web/src/app/(authenticated)/metiers/[slug]/FicheMetierClient.tsx`
- `apps/web/src/app/(authenticated)/metiers/[slug]/__tests__/FicheMetierClient.test.tsx`

**MODIFIER :**
- `apps/web/src/app/(authenticated)/mes-metiers/MetiersList.tsx` — ajouter drawer + onSignalClick + signals dans le href
- `apps/web/src/app/(authenticated)/mes-metiers/__tests__/MetiersList.test.tsx` — mettre à jour pour couvrir le drawer
- `apps/web/src/app/(authenticated)/metiers/[slug]/page.tsx` — parse `searchParams.signals`, passer à `FicheMetierClient`

**NE PAS MODIFIER :**
- `ScoreVocationnel.tsx` — la prop `onSignalClick` existe déjà
- `FicheMetier.tsx` — la prop `onSignalClick` existe déjà
- `types.ts` — `ScoreVocationnelProps` et `FicheMetierProps` déjà définis
- Aucun fichier Django

### Commits précédents (patterns)

```
feat(story-3-5): fiche métier détaillée — page SSR /metiers/[slug] (#37)
feat(story-3-4): liste métiers scorés — Django RecommendationService + ...
```

Pattern à suivre : `feat(story-3-6): explicabilité signaux RGPD art22 — SignauxDrawer + wiring MetiersList + FicheMetierClient`

## Dev Agent Record

### File List

**Created:**
- `apps/web/src/components/professions/SignauxDrawer.tsx`
- `apps/web/src/components/professions/__tests__/SignauxDrawer.test.tsx`
- `apps/web/src/app/(authenticated)/metiers/[slug]/FicheMetierClient.tsx`
- `apps/web/src/app/(authenticated)/metiers/[slug]/__tests__/FicheMetierClient.test.tsx`

**Modified:**
- `apps/web/src/app/(authenticated)/mes-metiers/MetiersList.tsx`
- `apps/web/src/app/(authenticated)/mes-metiers/__tests__/MetiersList.test.tsx`
- `apps/web/src/app/(authenticated)/metiers/[slug]/page.tsx`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`

### Change Log

- 2026-06-21: Story 3.6 implemented — SignauxDrawer component, MetiersList wiring, FicheMetierClient wrapper, page.tsx signals parsing

### Debug Log

- jsdom doesn't implement `window.matchMedia` — stubbed in tests as `{ matches: false }` (Desktop/Dialog path in tests)
- Radix Dialog close button uses "Close" (English) not "Fermer" — test regex covers both

### Completion Notes

- **SignauxDrawer**: responsive Sheet/Dialog pattern from ReportErrorButton, signals sorted by contribution desc, category icons (Heart/Star/BookOpen/Zap), positive UX copy, fallback for empty signals, "Demander une revue humaine" + "Comment ça marche" links
- **MetiersList**: drawer state added, signals encoded as JSON in href (`?signals=...`), onSignalClick opens drawer with profession's signals_contributifs
- **FicheMetierClient**: thin "use client" wrapper holding drawerOpen state, passes onSignalClick → opens drawer with signalsContributifs passed from page
- **page.tsx**: parseSignals() guard (JSON.parse + array + type validation + fallback []), passes signalsContributifs to FicheMetierClient, replaces direct FicheMetier render
- **Tests**: 10 tests SignauxDrawer + 8 tests MetiersList (updated) + 6 tests FicheMetierClient — all green. 3 pre-existing step-3 failures unchanged.
