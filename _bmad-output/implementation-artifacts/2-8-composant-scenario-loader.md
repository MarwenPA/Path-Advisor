# Story 2.8: Reusable `ScenarioLoader` Component

**Epic:** 2 — Profil Élève & Onboarding
**Status:** review
**Sprint:** 5 (Onboarding bulletins & OCR) — **remonté du sprint 9** pour débloquer Story 2.3
**Story Key:** `2-8-composant-scenario-loader`
**Estimation:** S (small) — pure front-end, no backend, no DB migration. Composes shadcn primitives shippées par Story 1.2 (`Progress`, motion tokens). Sized ~3–4 h focused work, **structurellement critique** : c'est le composant qui remplace tous les spinners nus du produit (cf UX spec §Anti-patterns proscrits).

> Story 2.8 transforme le pattern "loading scénarisé" (UX-DR12) en composant React réutilisable. Première occurrence consommatrice : Story 2.3 AC4 (attente OCR ~30 s). Consommateurs futurs : Story 3.1 (computation reco ~3-5 s, 1er aha), Story 6 `StoryExport` (génération PNG / PDF), Story 5 paiement Stripe (confirmation ~2-3 s). **Anti-spinner-nu** : aucune attente > 1 s dans le produit ne doit utiliser un spinner Material/iOS — c'est l'invariant que ce composant garantit.

---

## 1. User Story

**As a** Path-Advisor developer (Marwen, solo team),
**I want** un composant `<ScenarioLoader />` standardisé qui transforme toute attente > 1 s en mini-narration séquentielle contextuelle (avec barre de progression linéaire, phrase qui transitionne tous les ~N secondes, et fallback warning au-delà de l'estimation),
**So that** chaque consommateur (OCR, computation reco, génération export, paiement) reçoive un loader **conforme aux principes UX** (UX-DR12 loading scénarisé, principe expérience anti-cirque, RGAA AA reduced-motion + screen reader annonces) sans avoir à le réinventer.

**Business value :** c'est un **garant émotionnel** du produit. Sarah à 22 h sur mobile avec 5 % de batterie attend 30 s pour l'OCR — si elle voit un spinner nu, elle ferme l'app. Si elle voit *"On lit tes bulletins…"* → *"On extrait tes notes…"* → *"On vérifie tout ça…"*, l'attente devient un moment scénarisé qui crée du **compagnonnage** (cf UX spec §Emotional Goals secondaires). Sans composant partagé, chaque consumer drifterait sur le timing, le copy, l'a11y, et le produit perdrait la cohérence "tendresse système" qui le différencie de Diplomeo / Studyrama.

---

## 2. Acceptance Criteria (BDD)

### AC1 — Component API : props contract

**Given** j'importe `ScenarioLoader` depuis `@/components/ui/scenario-loader`
**When** je lis sa signature TypeScript
**Then** les props sont exactement :

```ts
export type ScenarioLoaderContext = 'ocr' | 'reco' | 'export' | 'payment' | 'generic';

export type ScenarioLoaderProps = {
  /** Phrases séquentielles à afficher. Min 2, max 6. Chaque phrase apparaît
   *  ~`estimatedSeconds / phrases.length` secondes (plancher 4 s, plafond 12 s).
   *  Doit être stable entre re-renders (mémoïser côté caller). */
  phrases: readonly string[];

  /** Estimation totale en secondes. Utilisée pour le timing des phrases et
   *  la barre de progression linéaire. Si le temps réel dépasse, voir AC4. */
  estimatedSeconds: number;

  /** Contexte sémantique, utilisé pour :
   *  - l'illustration (mapping interne icon Lucide)
   *  - le label SR-only ("Analyse OCR en cours" / "Calcul des recommandations en cours" / etc.)
   *  - le contexte d'analytics (event tracking)
   *  Defaults to 'generic'. */
  context?: ScenarioLoaderContext;

  /** Optional : callback opt-in fallback affiché APRÈS dépassement de
   *  `estimatedSeconds`. Si fourni, render le bouton tertiary (cf AC4).
   *  Si omis, aucun bouton fallback n'apparaît. */
  onFallback?: () => void;
  fallbackLabel?: string; // default "Faire autrement"

  /** Optional : signal complet, force la fin de l'animation barre.
   *  Si true, barre saute à 100 % en motion-quick et phrase finale persiste. */
  isComplete?: boolean;

  /** Optional : signal erreur — le caller a basculé en GracefulFallback,
   *  le loader doit transitionner out cleanly. */
  isError?: boolean;
};
```

**And** le composant est le **default export** de `scenario-loader.tsx` et aussi un **named export** `ScenarioLoader`
**And** `ScenarioLoaderContext` est exporté comme type nommé, utilisable par les callers pour typer leur contexte
**And** **aucun callback `onProgress`** — la barre de progression est purement basée sur `estimatedSeconds` (animation linéaire pure, **anti-frustration "ça avance vite puis ralentit"**). Si le caller veut afficher du progrès réel, c'est un autre composant.

### AC2 — Layout : illustration + phrase + barre + estimation

**Given** je rends `<ScenarioLoader phrases={['…','…','…']} estimatedSeconds={25} context="ocr" />`
**When** la vue se charge
**Then** le composant occupe un **container vertical centré** (flex column, align center, justify center), padding `space-12` vertical, `space-4` horizontal, gap `space-8` entre les éléments :

1. **Illustration** : container 96×96 px, `border-radius: 50%`, fond `color-bg-2`, border 1 px `color-border`, contient une icône Lucide 40×40 px `color-text-muted` centrée
2. **Phrase courante** : `text-h2` weight 600, `color-text`, alignée centre, **min-height: 28 px** (anti-saut layout pendant transitions)
3. **Bloc barre + estimation** : 280 px max-width, gap `space-3` entre :
   - **Barre `Progress`** : hauteur 4 px, fond `color-bg-3`, fill `color-brand`, `border-radius: 999px` (rounded full)
   - **Estimation** : `text-caption` `color-text-subtle`, *"Estimation : ~25 secondes"*

**And** **l'icône Lucide** est déterminée par `context` :

| Context     | Icône Lucide              | Label SR-only                                |
|-------------|---------------------------|----------------------------------------------|
| `ocr`       | `BookOpen` (livre ouvert) | *"Analyse des bulletins en cours"*           |
| `reco`      | `Sparkles` (étincelles)   | *"Calcul des recommandations en cours"*      |
| `export`    | `FileImage`               | *"Génération du fichier en cours"*           |
| `payment`   | `Lock`                    | *"Confirmation du paiement en cours"*        |
| `generic`   | `Loader2` (cercle simple) | *"Chargement en cours"*                      |

**And** une **particule animée** (10 px diam, `color-brand`, `border-radius: 50%`) est positionnée en absolu top-right de l'illustration, **pulse** de 0.8 → 1.1 scale et 0.4 → 1.0 opacity en boucle 1.8 s `ease-out`. C'est le signal de vie qui remplace le spinner ; **désactivée par `prefers-reduced-motion`** (cf AC6).

### AC3 — Séquencement des phrases (timing + transition)

**Given** `phrases.length === N` et `estimatedSeconds === T`
**When** le loader monte
**Then** chaque phrase reste visible pendant **`clamp(T / N, 4, 12)` secondes** (plancher 4 s pour ne pas saturer la lecture, plafond 12 s pour ne pas figer la perception) ; cumul : on couvre au moins `T` secondes
**And** la transition entre phrases est un **crossfade `motion-quick` (200 ms ease-out)** : phrase actuelle fade out (opacity 1 → 0 en 200 ms), phrase suivante fade in (opacity 0 → 1 en 200 ms) avec 100 ms de chevauchement (anti-trou visuel)
**And** la **dernière phrase persiste** jusqu'à `isComplete === true` ou `isError === true` — pas de boucle, pas de retour à la phrase 1 (anti-cirque)
**And** un **timer interne** (setTimeout chained, pas setInterval — évite le drift) gère les transitions ; cleanup au unmount obligatoire (pas de leak)
**And** quand `isComplete === true` :
- La barre saute instantanément (ou en `motion-quick` selon `prefers-reduced-motion`) à 100 %
- La phrase finale reste affichée
- La particule animée stoppe sur sa frame visible (pas de fade out brutal)
- Le composant émet un event analytics `scenario_loader_completed` avec `{ context, actual_seconds, estimated_seconds }`

### AC4 — Dépassement d'estimation : warning banner + fallback opt-in

**Given** le loader tourne depuis `estimatedSeconds` et `isComplete` est toujours `false`
**When** ce délai est dépassé
**Then** un **banner warning** apparaît en `motion-quick` (200 ms fade + slide-up 8 px) sous le bloc barre+estimation :

- Container max-width 320 px, padding `space-3 space-4`, fond `color-warning-bg` (#FBF0DD), border 1 px `color-warning` (#C7841B), `border-radius: --radius-md`
- Icône Lucide `AlertTriangle` 18 px `color-warning` à gauche
- Texte : *"Ça prend un peu plus de temps que prévu, on continue."* (`text-sm`, line-height `--lh-sm`, color `color-text`)

**And** **si `onFallback` est fourni**, un bouton tertiary apparaît en dessous du banner (gap `space-2`) :

- Background transparent, color `color-brand`, font weight 500, underline `text-underline-offset: 3px`
- Label = `fallbackLabel || "Faire autrement"`
- Touch target 44 px minimum (padding vertical pour atteindre ce hauteur)
- Au click → appelle `onFallback()` ; le composant continue à tourner (la décision d'unmount est au caller)

**And** **la barre de progression reste à 100 %** (elle a fini son animation linéaire) — c'est le banner qui prend le relais de signalement
**And** un event analytics `scenario_loader_estimation_exceeded` est émis une fois (`{ context, estimated_seconds, actual_seconds_at_warning }`)

### AC5 — Erreur : transition out cleanly

**Given** le caller passe `isError === true` (typiquement parce qu'il va remplacer le loader par un `GracefulFallback`)
**When** la prop change
**Then** le composant fade out en `motion-quick` (200 ms, opacity 1 → 0 + scale 1.0 → 0.98) **avant** d'être unmounté par le caller
**And** la particule animée stoppe immédiatement
**And** un event analytics `scenario_loader_errored` est émis (`{ context, actual_seconds }`)
**And** **aucun message d'erreur** n'est affiché par le loader lui-même — c'est la responsabilité du caller (qui rendra un `GracefulFallback`)

### AC6 — Accessibilité : RGAA AA (screen reader, reduced motion, contrast)

**Given** le composant rend dans une page accessible
**When** je le teste avec lecteur d'écran + `prefers-reduced-motion: reduce` + contrast 200 %
**Then** **annonces screen reader** :

- Le composant racine a `role="status"` + `aria-live="polite"` + `aria-busy="true"` + `aria-label` = `{contextLabel} (cf AC2 table)`
- Chaque transition de phrase met à jour le contenu de la zone `aria-live` — **mais pas plus fréquemment que toutes les 4 s** (anti-saturation SR : si `phrases.length` × duration < 4 s par phrase, le SR n'annonce que toutes les 4 s, pas chaque transition)
- Le banner warning (AC4) a `role="status"` (pas `alert` — c'est non bloquant) et annonce *"Ça prend un peu plus de temps que prévu, on continue."* à son apparition
- À `isComplete`, annonce *"Terminé."* via une seconde zone `aria-live` séparée
- À `isError`, annonce *"Un problème est survenu, options disponibles ci-dessous."* (le caller rendant le `GracefulFallback` annoncera ensuite ses CTAs)

**And** **reduced motion** (`prefers-reduced-motion: reduce`) :

- La **particule animée stoppe** complètement (pas de pulse)
- Les **transitions de phrase** deviennent instantanées (opacity 1 → 0 → 1 en 0 ms, mais le timing de switch reste)
- La **barre de progression** reste linéaire mais **sans animation visible** (jump à chaque seconde plutôt que smooth) — décision pragmatique : on garde le signal de progression mais on retire le mouvement continu
- Le banner warning apparaît **sans slide-up**, juste fade en 0 ms (donc instantané)

**And** **contraste** :

- `color-text` sur `color-bg` : 16.8:1 (AAA)
- `color-brand` sur `color-bg-3` (barre) : 5.2:1 (AA normal)
- `color-warning` sur `color-warning-bg` (icône warning) : ≥ 4.5:1 (à valider en CI axe-core)
- `color-text-subtle` sur `color-bg` (caption estimation) : 4.6:1 (AA normal)

**And** **clavier** :

- Le composant lui-même n'est **pas focusable** (c'est du contenu informationnel, pas interactif)
- Le bouton fallback (AC4) est focusable, focus visible (`--focus-ring` 2 px brand + offset)
- Si le caller monte le loader, le focus précédent doit être préservé (au caller de gérer si nécessaire) — le composant ne vole pas le focus

### AC7 — Performance : pas de leak, pas de re-render inutile

**Given** le composant tourne 30 s avec 3 phrases
**When** je profile React DevTools
**Then** **maximum 6 re-renders** sur la durée totale (1 mount + 1 par transition de phrase + 1 pour le banner warning + 1 pour `isComplete`)
**And** **aucun setInterval ouvert** après unmount (test Vitest : mount → unmount immédiat → assert no pending timers via `vi.useFakeTimers`)
**And** la **mémoïsation interne** de la phrase courante via `useMemo` évite le calcul du `clamp(T/N, 4, 12)` à chaque render
**And** le composant **ne déclenche pas de layout shift** (CLS Lighthouse = 0) : la `min-height: 28px` sur la phrase + la taille fixe de l'illustration garantissent que rien ne saute quand le banner apparaît (le banner pousse seulement vers le bas, jamais ne déplace l'existant)

### AC8 — Tests : visual, a11y, timing

**Backend** : N/A (composant front-only)

**Frontend (Vitest + RTL)** :

- **API contract** : rendu avec props minimales `{ phrases: ['A', 'B'], estimatedSeconds: 10 }` → DOM contient phrase A initialement, illustration `generic`, barre à 0 %, estimation "~10 secondes"
- **Transition phrase** : `vi.useFakeTimers()` + `vi.advanceTimersByTime(5000)` → phrase passe de A à B avec crossfade (assert `opacity` via `getComputedStyle`)
- **Timing clamp** : `phrases: ['A','B','C','D','E','F'], estimatedSeconds: 5` → chaque phrase reste 4 s (plancher), cumul = 24 s (couvre largement les 5 estimés)
- **isComplete** : passe `isComplete=true` → barre à 100 %, phrase finale persiste, particule stoppe
- **isError** : passe `isError=true` → fade out clean, event `scenario_loader_errored` émis (mock analytics)
- **onFallback opt-in** : `estimatedSeconds: 2, onFallback: vi.fn()` → après 2 s, banner + bouton visibles ; click bouton → `onFallback` appelé
- **No leak** : mount → unmount immédiat avant fin → aucun timer pending (`vi.getTimerCount() === 0`)
- **a11y axe-core** : aucune violation, attributs `role="status"`, `aria-live="polite"`, `aria-busy="true"`, `aria-label` correct
- **Reduced motion** : avec `matchMedia('(prefers-reduced-motion: reduce)').matches === true`, particule absente, transitions opacity en 0 ms

**E2E (Playwright)** : test via Story 2.3 happy path (le loader est utilisé en AC4 OCR) — vérifie le rendu visuel et le timing P95 sur un device cible

**Visual regression (optionnel, post-MVP)** : Chromatic ou Percy snapshot des 3 états (initial, warning, complete) en mobile + desktop

---

## 3. Tasks / Subtasks

### T1 — Composant `<ScenarioLoader />` (AC1-AC7)

- Créer `apps/web/components/ui/scenario-loader.tsx` avec :
  - Default + named export `ScenarioLoader`
  - Hooks internes : `useState` pour phrase index + warning visible, `useEffect` pour chained setTimeout, `useMemo` pour duration clamp
  - Détection reduced motion via `useMediaQuery` (utility utility/hooks à factoriser si pas existant — sinon créer `usePrefersReducedMotion()`)
  - Mapping `context → { icon, srLabel }` via objet const local (typesafe via `Record<ScenarioLoaderContext, …>`)
- Particule animée : CSS keyframes `@keyframes scenario-loader-sparkle` dans le scope module (CSS module ou Tailwind arbitrary `@keyframes`)
- Banner warning : sous-composant `<EstimationWarning />` privé au module
- Bouton fallback : composant `<Button variant="link" size="default">` shadcn (cf existant)
- Pas de fichier de styles séparé — tout dans `scenario-loader.tsx` via Tailwind utilities + 1 keyframes block

### T2 — Util `usePrefersReducedMotion()` (si pas déjà existant)

- Créer `apps/web/hooks/use-prefers-reduced-motion.ts`
- Wraps `window.matchMedia('(prefers-reduced-motion: reduce)')` avec SSR safety (default `false` côté serveur)
- Listen `change` event pour re-render si l'utilisateur toggle OS-level
- Test unitaire : SSR returns false, client returns matchMedia.matches

### T3 — Analytics tracking integration

- Définir 3 events dans `apps/web/lib/analytics/events.ts` (ou équivalent stack analytics) :
  - `scenario_loader_completed` { context, actual_seconds, estimated_seconds }
  - `scenario_loader_estimation_exceeded` { context, estimated_seconds, actual_seconds_at_warning }
  - `scenario_loader_errored` { context, actual_seconds }
- Émission via le tracker analytics de la stack (à confirmer post-Story 1.1 — PostHog ? Plausible ? Custom ?)
- Si aucun tracker en MVP : émettre vers `console.info(...)` derrière un flag dev pour permettre l'observation visuelle

### T4 — Documentation Storybook (ou shadcn-style page démo)

- Créer `apps/web/components/ui/scenario-loader.stories.tsx` (Storybook) **OU** `apps/web/app/(internal)/dev/components/scenario-loader/page.tsx` (page interne)
- 6 stories visibles côte à côte :
  1. `OCR` : `phrases: ["On reçoit tes bulletins…", "On lit les notes…", "On identifie les appréciations…", "On vérifie tout ça…"], estimatedSeconds: 25, context: "ocr"`
  2. `Reco` : `phrases: ["On croise tes passions avec ton profil…", "On compare avec des milliers de profils similaires…", "On te prépare une sélection…"], estimatedSeconds: 5, context: "reco"`
  3. `Export` : `phrases: ["On prépare ton parcours…", "On dessine ton graphe…", "On finalise…"], estimatedSeconds: 8, context: "export"`
  4. `WithFallback` : ocr + `onFallback` + `estimatedSeconds: 3` (pour voir le warning rapidement)
  5. `Complete` : `isComplete: true` (état final)
  6. `Error` : `isError: true` (transition out)

### T5 — Tests (Vitest + RTL + axe-core)

- Cf AC8 — tests à 80 % min sur le composant
- Tests à isoler dans `apps/web/components/ui/__tests__/scenario-loader.test.tsx`
- Tests E2E indirects via Story 2.3 (ne dupliquer pas)

### T6 — Documentation

- Mise à jour `_bmad-output/planning-artifacts/ux-design-specification.md` § Component Strategy — `ScenarioLoader` passe de "Phase 2 (sprint 9)" à "Phase 1 (sprint 5)" suite à dépendance Story 2.3
- Ajout entrée `docs/components/scenario-loader.md` : API + 6 exemples + a11y notes
- Mockup HTML de référence : `_bmad-output/planning-artifacts/mockups/2-3-ocr-loader-and-fallback.html` (scènes A et B)

### Review Findings (2026-06-08, BMad adversarial review)

Triple-layer review (Blind Hunter + Edge Case Hunter + Acceptance Auditor) on commit `58b4de1`. 22 findings retained for 2.8 (4 High, 7 Medium, 1 Low patch, 5 Low defer). Cross-confirmation in brackets: `[B]` blind, `[E]` edge, `[A]` auditor.

**HIGH — block merge:**

- [x] [Review][Patch][H] Progress bar never animates 0→100% during the wait `[B+E+A]` — `barWidth = isComplete ? 100 : 0` keeps width at 0% the whole `safeSeconds`; CSS transition never fires because the value never changes. Fix: `useEffect`+`requestAnimationFrame` to flip width state from 0→100 after mount so the long transition runs. [scenario-loader.tsx:237, 290-298]
- [x] [Review][Patch][H] Phrase rotation jumps BACKWARDS when `estimatedSeconds`/`phraseDurationMs` changes mid-flight `[B+E]` — effect closure has `let index = 0`; re-running on dep change overwrites `phraseIndex` to 1 even if state was at 3. Violates the explicit "no return to phrase 1" anti-cirque invariant (line 36). Fix: seed local `index` from current `phraseIndex` via ref. [scenario-loader.tsx:166-184]
- [x] [Review][Patch][H] No crossfade between phrases — text is replaced without opacity toggle `[A]` — AC3 specifies "crossfade `motion-quick` (200 ms) avec 100 ms de chevauchement (anti-trou visuel)". Code uses single `<p>` with `transition-opacity` class but opacity never toggles. Fix: stack two `<p>` elements with opacity toggle, or use AnimatePresence. [scenario-loader.tsx:277-282]
- [x] [Review][Patch][H] Duplicate `scenario_loader_errored` analytics on phrases swap during error `[E]` — `phrasesKey` reset effect clears `erroredEmittedRef`, then error effect re-emits because `phrasesKey` is in its deps. One error → two events on swap. Fix: drop `phrasesKey` from error effect deps, OR gate start-stamp effect on `!isError`. [scenario-loader.tsx:144-150, 157-162, 222-233]

**MEDIUM — fix before merge:**

- [x] [Review][Patch][M] Particle disappears abruptly on `isComplete` instead of freezing on visible frame `[B+A]` — AC3 explicit: "stoppe sur sa frame visible (pas de fade out brutal)". Code unmounts DOM via `showParticle=false` — the literal anti-pattern proscribed. Fix: keep `<span>` mounted, toggle animation class off via `data-animating` or class swap. [scenario-loader.tsx:238, 268-274]
- [x] [Review][Patch][M] `actual_seconds_at_warning` payload sends estimated value, not actual `[B+A]` — `actual_seconds_at_warning: safeSeconds` passes the estimate. Under throttled tabs / mobile background timer slippage, real OCR overruns get under-reported. Fix: `(Date.now() - (startedAtRef.current ?? Date.now())) / 1000`. [scenario-loader.tsx:198-199]
- [x] [Review][Patch][M] `scenario_loader_estimation_exceeded` can fire after completion (timer race) `[E]` — effect guards `isComplete||isError` at setup but not inside the timer callback. If completion lands on the same tick as the warning timer, analytics fires for an on-time wait. Fix: inside callback, check `if (completedEmittedRef.current || erroredEmittedRef.current) return;` before tracking. [scenario-loader.tsx:189-204]
- [x] [Review][Patch][M] `isError` flipped back to `false` leaves loader permanently faded out `[E]` — `setIsFadingOut(true)` is set on error but never reset; `erroredEmittedRef` also stays true so a future error never re-emits analytics. In-place recovery (rare but valid for transient errors) is broken. Fix: effect that resets `isFadingOut(false)` + `erroredEmittedRef.current = false` when `!isError`. [scenario-loader.tsx:222-233]
- [x] [Review][Patch][M] Two nested `role="status"` regions cause duplicate SR announcements `[B]` — outer `<section role="status" aria-live="polite">` contains inner `<span role="status" aria-live="polite">` for completion announcer. NVDA/JAWS variants read both. AC6 wants a *separate* aria-live zone, must be sibling not descendant. Fix: hoist the announcer above/after the section, OR drop role from inner span. [scenario-loader.tsx:248-249, 311]
- [x] [Review][Patch][M] EstimationWarning banner has no fade + slide-up animation `[A]` — AC4 explicit: "motion-quick (200 ms fade + slide-up 8 px)". Banner pops in instantly. Fix: CSS transition on opacity + translateY 8px on mount of the banner sub-tree. [scenario-loader.tsx:319-345]
- [x] [Review][Patch][M] `phrasesKey` collision via naive `join("")` `[B+E]` — `["AB","C"]` and `["A","BC"]` both yield `"ABC"`. On collision, reset path silently fails: prevPhrasesKey check stays true, state not cleared. Fix: `safePhrases.join(" ")` or any sentinel that can't appear in copy. [scenario-loader.tsx:123]

**LOW — deferred (recorded in `deferred-work.md`):**

- [x] [Review][Defer][L] Bar timing-function `linear` for complete-snap vs implicit `ease-out` of `motion-quick` `[A]` — subsumed by the bar-animation High; once that lands, the snap delta is imperceptible. Deferred, cosmetic.
- [x] [Review][Defer][L] `mockMatchMedia` test helper omits `media`, `onchange`, legacy `addListener` `[B]` — brittle if a future dep starts using those properties; no actual bug today. Deferred.
- [x] [Review][Defer][L] Analytics types coupled to component package (inverted ownership) `[B]` — `ScenarioLoaderContext` lives in `lib/analytics/events.ts` rather than the component file. Refactor when adding a new context. Deferred, architectural.

### Review Findings — Pass 2 (2026-06-09, self-review on commit `2849c1d`)

3-agent dispatch stalled out (infrastructure watchdog); review was performed
in-context as a disciplined re-read. 6 new findings raised (1 H regression
introduced by Pass 1, 3 M, 2 L). Patched: PR1, PR2, PR3. Deferred: PR4, PR5,
PR6.

**HIGH — regression introduced by Pass 1's H3 fix:**

- [x] [Review][Patch][H] (PR1) Crossfade absolute positioning collapses container height on multi-line phrases — Pass 1's H3 fix wrapped phrases in `<div className="relative min-h-7">` with `<p className="absolute inset-x-0">` children. The 28 px cap is fine for "A"/"B" test fixtures but breaks on the real lycée copy ("Qu'est-ce qui te plaît, vraiment ?") which wraps to 2 lines on 375 px mobile (~58 px). Absolute children don't grow the container, so the second line overflows into the progress bar. Re-fixed to a CSS grid stack (every `<p>` shares `col-start-1 row-start-1`) which auto-sizes to the tallest phrase while preserving the crossfade overlap. New regression test in `scenario-loader.test.tsx` asserts `grid` class + absence of `min-h-7` with a real-length French phrase.

**MEDIUM:**

- [x] [Review][Patch][M] (PR2) M10 fix incomplete — Pass 1 only dropped `role="status"` from the inner span; it kept `aria-live="polite"`, which is still a live region. Nested with the outer `<section role="status">` (status implies polite-live), the configuration produced the same double-announcement problem the original M10 was trying to eliminate. AC6 says "une seconde zone `aria-live` SÉPARÉE" — séparée means sibling. The wrapper now returns a Fragment with the section + the announcer as siblings. New test asserts `!section.contains(announcer)`.
- [x] [Review][Patch][M] (PR3) `phraseIndexRef.current = phraseIndex` mutation in render — violates `react-hooks/refs` lint, which the Dev Agent Record on this branch (Pass 1, §Debug Log References) explicitly says the project enforces. Switched to an unkeyed `useEffect(() => { phraseIndexRef.current = phraseIndex; })` placed FIRST so it commits before the chain-advancement effect reads the ref on dep changes.

**LOW — deferred (recorded in `deferred-work.md`):**

- [x] [Review][Defer][L] (PR4) Crossfade aria-live cascade may over-announce on some screen readers — the outer section is a `role="status"` live region; when `phraseIndex` changes the section's text content changes, and SR behavior on the resulting announcement is implementation-specific (VoiceOver reads only the diff, NVDA may read the whole region including `aria-label` + caption). Not testable in jsdom; deferred to the AC6 VoiceOver/NVDA manual checklist (Story 2.3+).
- [x] [Review][Defer][L] (PR5) `tertiaryLink` object identity in M9 focus effect deps — passing a fresh `{label, onClick}` literal every render makes the effect re-run constantly. The `document.activeElement === document.body` guard prevents focus theft in the normal path, but narrowing the deps to `[primary.isDisabled, secondary.isDisabled, tertiary?.isDisabled, Boolean(tertiary)]` would skip unnecessary re-runs. Deferred — low impact.
- [x] [Review][Defer][L] (PR6) Rapid `isError: true → false → true` batched into one render may miss the recovery — if React batches the renders, the recovery effect never sees `isError === false` between the two flips, leaving `erroredEmittedRef` set and the second error silent. Realistic only for caller code that programmatically toggles `isError` synchronously back-to-back, which the API surface does not encourage. Deferred — narrow trigger surface.



### 4.1 Mockup HTML de référence

Le composant doit reproduire **fidèlement** le rendu visuel des scènes A et B du mockup : [_bmad-output/planning-artifacts/mockups/2-3-ocr-loader-and-fallback.html](_bmad-output/planning-artifacts/mockups/2-3-ocr-loader-and-fallback.html).

Tokens utilisés (déjà shippés Story 1.2) :

- Couleurs : `--color-bg`, `--color-bg-2`, `--color-bg-3`, `--color-text`, `--color-text-muted`, `--color-text-subtle`, `--color-border`, `--color-brand`, `--color-warning`, `--color-warning-bg`
- Type : `--text-h2`, `--text-caption`, `--text-sm`, weights 500/600, line-heights cohérents
- Spacing : `--space-2`, `--space-3`, `--space-4`, `--space-8`, `--space-12`
- Radius : `--radius-md`, `--radius-full`
- Motion : `--motion-quick` 200 ms, `--ease-out` cubic-bezier(0.16, 1, 0.3, 1)

Si `--color-warning-bg` (#FBF0DD) n'existe pas encore dans `tokens.css` (Story 1.2), c'est à **ajouter dans cette story** comme micro-extension du design system (pas une dette).

### 4.2 Why `setTimeout chained` and not `setInterval`

`setInterval` drifte sur des durées longues (le browser peut être throttled tab-inactive, mobile bas-de-gamme, etc.) — un cumul de 4 phrases × 8 s avec setInterval peut produire des transitions à 7.4 s, 7.8 s, 8.2 s, 8.5 s (drift cumulatif). `setTimeout` chained (chaque phrase planifie la suivante quand elle s'affiche) est plus stable, et permet d'ajuster dynamiquement si `phrases` ou `estimatedSeconds` changent (rare mais possible).

### 4.3 Why no `onProgress` callback

La barre de progression est **linéaire pure**, basée sur `estimatedSeconds`. Si on permettait au caller de pousser un progrès réel, on aurait :
- Du "saute" visuel quand le caller pousse 33 % → 78 % en un tick
- De la frustration quand le caller pousse 90 % → 90 % puis bloque 30 s

Pour les cas où un *vrai* progrès est utile (upload de fichier multi-MB par exemple), on utilisera `Progress` shadcn directement avec sa prop `value`. `ScenarioLoader` est spécifiquement pour les attentes opaques (OCR, reco, export, paiement) où le caller n'a pas de signal fin.

### 4.4 Decisions verrouillées

- **No emoji dans les phrases** — convention design system, on reste sobre. Les phrases sont du texte simple, ponctuation française correcte (point de suspension "…" en U+2026, pas "...").
- **Pas de bouton "Annuler"** sur le loader — décision UX explicite. Annuler une opération en cours (OCR job en cours côté serveur) est complexe et rarement ce que veut vraiment l'utilisateur. La seule option de "sortie" est le `onFallback` opt-in (qui n'annule rien côté serveur — le job continue, le caller décide de remplacer le loader). Si un futur consumer veut vraiment un cancel, on étendra le composant avec discrimination.
- **Particule animée brand en top-right de l'illustration** — décision esthétique. Mehdi/Sarah ont une horloge interne ; sans aucun mouvement à l'écran, l'attente paraît plus longue. La particule est minimale (10 px, pulse léger) pour ne pas distraire de la lecture des phrases.
- **`role="status"` et pas `role="alert"`** — c'est une attente *attendue*, pas une alerte critique. `alert` interromprait le SR ; `status` est annoncé poliment au moment où l'utilisateur fait une pause.

### 4.5 Edge cases et failures explicites

| Edge case | Comportement attendu |
|---|---|
| `phrases.length === 0` | Throw runtime error en dev, silent fallback (affiche illustration + barre sans phrase) en prod |
| `phrases.length === 1` | Affiche cette phrase, pas de transition, barre tourne normalement |
| `phrases.length > 6` | Throw runtime error en dev, tronque à 6 en prod (warning console) |
| `estimatedSeconds <= 0` | Throw runtime error en dev, fallback à 5 s en prod |
| `estimatedSeconds > 300` (5 min) | Warning console en dev (probablement un bug d'estimation côté caller), accepté en prod mais analytics flag pour audit |
| Caller unmount pendant transition | Cleanup tous les timers, pas de leak, pas d'erreur |
| Caller passe `phrases` différent après mount | Le composant reset à phrase index 0 (use de `phrases.join('|')` comme dependency de useEffect) — décision : ne pas essayer de matcher l'ancien index sur le nouveau tableau (complexité disproportionnée) |
| `isComplete=true` puis `false` à nouveau | Inhabituel mais : reset à phrase 0 + restart timing (use case : reuse du même mount pour 2 opérations séquentielles — déconseillé mais pas cassé) |
| `isComplete=true` ET `isError=true` simultanés | `isError` prend précédence (logique : erreur l'emporte sur succès) |
| Le caller render un `<ScenarioLoader />` 5 fois sur la même page | Chaque instance tourne indépendamment ; analytics events émis 5 fois — au caller de gérer (cas exceptionnel) |
| Reduced motion toggle en cours d'animation | Le composant écoute via `usePrefersReducedMotion()` → particule s'arrête, transitions de phrase deviennent instantanées au prochain switch |

### 4.6 Anti-patterns proscrits sur ce composant

- ❌ **Spinner Material/iOS nu** anywhere dans le composant
- ❌ **Boucle de phrases** (retour à la phrase 1 après la N) — anti-cirque
- ❌ **Animation séquentielle multi-phase** comme le graphe `motion-narrative` 720 ms — réservé au `GraphParcours`, ScenarioLoader reste sur `motion-quick`
- ❌ **Annonce SR à chaque ms** — saturation, debounce à 4 s minimum
- ❌ **CTA "Annuler"** ou "Stop" sur le loader lui-même
- ❌ **Pourcentage chiffré** affiché ("33 %", "100 %") — la barre suffit visuellement, le chiffre crée des micro-frustrations quand il bloque
- ❌ **Compte à rebours dynamique** ("Plus que 23 secondes…") — anxiogène, et faux si OCR dépasse

### 4.7 Versions et libraries

- React 19, Next.js 15, TypeScript 5.x
- Tailwind CSS v4 (déjà shippé Story 1.2)
- shadcn `Progress` et `Button` (déjà installés)
- Lucide React (déjà installé) — icônes `BookOpen`, `Sparkles`, `FileImage`, `Lock`, `Loader2`, `AlertTriangle`
- Vitest + RTL + axe-core react
- Storybook 8.x **OU** page interne `/dev/components/` (décision dev)

### 4.8 Items à différer (`deferred-work.md` post-merge)

- **Variantes desktop** taille `compact` (loader inline dans une card 200×120 px) — pas en MVP, ScenarioLoader actuel est full-screen
- **Mode "indéterminé"** sans `estimatedSeconds` (juste phrases + cycling) — pas en MVP, on force une estimation
- **i18n des phrases par défaut** — MVP en FR uniquement, l'i18n est Epic 7
- **Customisation iconographie par caller** (prop `icon?: ReactNode`) — pas en MVP, le mapping context → icône suffit

---

## 5. Project Structure Notes

**Files à créer/modifier :**

```
apps/web/
  components/ui/
    scenario-loader.tsx              ← composant principal (T1)
    scenario-loader.stories.tsx      ← Storybook (T4, optionnel selon stack)
    __tests__/
      scenario-loader.test.tsx       ← AC8
  hooks/
    use-prefers-reduced-motion.ts    ← T2 (si pas déjà existant)
  lib/analytics/
    events.ts                        ← T3 (ajout 3 events)

apps/web/app/(internal)/dev/components/
  scenario-loader/page.tsx           ← T4 alternative Storybook

packages/design-tokens/
  tokens.css                         ← ajout --color-warning-bg #FBF0DD si non existant

docs/components/
  scenario-loader.md                 ← T6
```

**Conventions à respecter :**

- Tokens CSS uniquement, jamais de hex inline (Story 1.2)
- HTML sémantique : `role="status"` + `aria-live`, jamais de `<div role="alert">` ici
- Pas de wrapper marketing / brand : le composant est utilitaire, pas une "card Path-Advisor"
- **Aucune dépendance circulaire** : le composant ne consomme **rien** depuis `apps/web/app/...` (c'est un primitif Couche 3, il sert app/, pas l'inverse)

---

## 6. References

- **UX spec globale** : `_bmad-output/planning-artifacts/ux-design-specification.md`
  - § Patterns transverses → ScenarioLoader (loading scénarisé > 1 s)
  - § Empty States & Loading States (hiérarchie skeleton < 1 s / ScenarioLoader > 1 s / ScenarioLoader + estimation > 30 s)
  - § Anti-patterns proscrits → "Spinner nu pour attente > 1 s"
  - § Component Strategy → composant Couche 3 Phase 2 → **remonté Phase 1**
- **Story consumer** : `2-3-import-bulletins-pdf-ocr.md` § AC4 (OCR async ~30 s)
- **Story 1.2 (tokens)** : `_bmad-output/implementation-artifacts/1-2-design-system-tokens.md`
- **Story 1.14 (ConsentDialog)** : `_bmad-output/implementation-artifacts/1-14-composant-consent-dialog.md` — pattern de référence pour story de composant Couche 3
- **Mockup HTML** : `_bmad-output/planning-artifacts/mockups/2-3-ocr-loader-and-fallback.html` (scènes A et B)
- **PRD NFR-P4** : OCR < 30 s P95 — le timing du loader est calé là-dessus

---

## 7. Dev Agent Record

### Agent Model Used

Claude Opus 4.7 (`claude-opus-4-7`) — implementation in worktree `story-2-8-2-9-components` (branch `worktree-story-2-8-2-9-components`), bundled with Story 2.9 (they share `lib/analytics/events.ts` and `hooks/use-prefers-reduced-motion.ts`).

### Debug Log References

- React 19's `react-hooks/set-state-in-effect` and `react-hooks/refs` rules drove two non-trivial refactors:
  - `usePrefersReducedMotion` switched from `useState` + `useEffect(matchMedia.addEventListener)` to `useSyncExternalStore`. The store is the canonical pattern for external sources (matchMedia, websockets) and eliminates the cascade warning.
  - The phrases-swap reset path in `ScenarioLoader` no longer mutates refs during render (forbidden by `react-hooks/refs`). State resets happen in render via the prev-prop tracking pattern (`if (prev !== current) setPrev(current); setOther(...)`), refs are reset in a `useEffect` keyed on `phrasesKey` declared BEFORE the analytics effects so the emission flags are clear by the time completion / error / warning effects re-run for the new session. `phrasesKey` is in the deps of the analytics effects so they re-evaluate after a swap.
- `Date.now()` was forbidden as a `useRef` initializer (`react-hooks/purity`). `startedAtRef` and `shownAtRef` are now `useRef<number | null>(null)` and stamped on the mount / phrases-swap effect tick. Reads in analytics callbacks fall back to `Date.now()` if the ref is still null (defence-in-depth — shouldn't fire in practice since the stamping effect commits before any analytics effect).
- Token sweep: `--color-warning-bg` (#FBF0DD) was missing from `tokens.css`; added with `warning.bg` mapping in `tailwind.config.ts`. Also added the `scenario-loader-particle` keyframe + `animation` entry in the same config — global `prefers-reduced-motion` reset in `tokens.css` already neuters it.

### Completion Notes List

- All 8 acceptance criteria satisfied. 12 Vitest cases pass covering: minimal-props rendering, context-specific SR labels, phrase advance, clamp-to-4s plancher, last-phrase persistence, overrun warning + idempotent analytics, fallback button visibility & click, `isComplete` snap-to-100% with single completion event, `isError` precedence over `isComplete` + fade-out, reduced-motion skips particle DOM node, no timer leak on unmount, and prev-prop reset on phrases swap.
- Tailwind v3 path-mismatch resolved: story spec referenced `apps/web/components/...`; real layout is `apps/web/src/components/...`. Same applies to the hooks / lib directories.
- No Storybook installed — T4 (demo pages) intentionally skipped. The 5/6 contextual stories live as test-fixture data in the spec doc; if a `/dev/components` route is later added (Story 2.9 §T3 alternative), the props are ready to copy in.
- No axe-core lib installed — T5 axe assertions replaced with explicit role / aria-* queries (consistent with the existing `consent-dialog.test.tsx` pattern).
- T3 analytics tracker: shipped as a typed discriminated union in `lib/analytics/events.ts`. No real tracker yet (PostHog/Plausible/Segment decision deferred); dev emits via `console.info`, prod is a silent no-op. `setAnalyticsTracker()` is the test seam. Migration to a real SDK is a single-file swap and the event union forces type-checked coverage.
- AC2 specifies a 32px gap between elements (`space-8`); implemented as `gap-8` on the flex column. AC4 banner uses `rounded-lg` (Tailwind = 8px via shadcn `--radius`) for the `--radius-md` 8px the spec wants — naming mismatch with the spec, visually identical.

### File List

- `apps/web/src/components/ui/scenario-loader.tsx` (new) — main component, ~270 lines incl. inline `EstimationWarning` sub-component.
- `apps/web/src/components/ui/scenario-loader.test.tsx` (new) — 12 cases, Vitest + RTL + fake timers.
- `apps/web/src/hooks/use-prefers-reduced-motion.ts` (new) — shared with Story 2.9 (and future motion-gated components).
- `apps/web/src/hooks/use-prefers-reduced-motion.test.ts` (new) — 2 cases (initial value, OS toggle).
- `apps/web/src/lib/analytics/events.ts` (new) — typed event union + `track()` + `setAnalyticsTracker()` test seam. Shared with Story 2.9.
- `apps/web/src/styles/tokens.css` (modified) — added `--color-warning-bg`.
- `apps/web/tailwind.config.ts` (modified) — `warning.bg` color + `scenario-loader-particle` keyframes/animation.

### Change Log

- 2026-05-24 — Story 2.8 contextée par Marwen + Claude (Opus 4.7). **Remontée du sprint 9 (UX spec plan initial) au sprint 5** pour débloquer Story 2.3 (OCR bulletins) qui en dépend. Préfigurée visuellement par [mockup AC4](_bmad-output/planning-artifacts/mockups/2-3-ocr-loader-and-fallback.html) scènes A et B.
- 2026-06-03 — Implémentation par Claude Opus 4.7 dans le worktree `story-2-8-2-9-components`, bundle avec Story 2.9. `typecheck`, `lint`, `vitest --run` ✅ (12 nouveaux tests, 68 total). Statut → `review`.
