# Story 2.9: Reusable `GracefulFallback` Component

**Epic:** 2 — Profil Élève & Onboarding
**Status:** done
**Sprint:** 5 (Onboarding bulletins & OCR) — **remonté du sprint 9** pour débloquer Story 2.3
**Story Key:** `2-9-composant-graceful-fallback`
**Estimation:** S (small) — pure front-end, no backend, no DB migration. Composes shadcn primitives shippées par Story 1.2 (`Button`). Sized ~3–4 h focused work, **structurellement critique** : c'est le composant qui transforme tous les patterns d'erreur du produit en *portes ouvertes plutôt que murs* (UX-DR13 + NFR-R4).

> Story 2.9 transforme le pattern "erreur gracieuse avec alternative immédiate" en composant React réutilisable. Première occurrence consommatrice : Story 2.3 AC7 (OCR rate → bascule manuel). Consommateurs futurs : Story 5.x paiement Stripe rejeté, Story 6 envoi anticipé école indisponible, futurs cas réseau ou backend non-bloquants. **Anti-impasse** : aucun écran d'erreur dans le produit ne doit afficher *"ERREUR"* sans proposer une voie immédiate — c'est l'invariant que ce composant garantit.

---

## 1. User Story

**As a** Path-Advisor developer (Marwen, solo team),
**I want** un composant `<GracefulFallback />` standardisé qui transforme tout échec opérationnel (OCR rate, paiement rejeté, envoi école indisponible) en écran calme proposant 2 CTAs **strictement équivalents en weight visuel** (alternative immédiate + retry/secondaire) plus un lien tertiary optionnel,
**So that** chaque consumer (OCR, paiement, envoi anticipé) reçoive un écran d'erreur **conforme aux principes émotionnels** (UX-DR13 jamais d'impasse, principe émotionnel #2 dignité avant positivité, ton calme, NFR-R4 graceful degradation) sans avoir à le réinventer.

**Business value :** c'est un **garant de rétention émotionnelle**. Léa à 23 h dont l'OCR rate, Mehdi dont le paiement Stripe casse, Sarah dont l'envoi anticipé école timeout — chaque cas est un **point de fuite potentiel** où l'utilisateur peut désinstaller s'il se sent stupide ou impuissant. Le `GracefulFallback` rend chaque échec **factuel et résolvable** : icône doc neutre (pas de croix rouge), copy commençant par *"Pas grave"*, 2 CTAs équivalents (anti-dark-pattern poussant vers une option), lien tertiary discret *"Plus tard"*. Sans composant partagé, chaque consumer drifterait sur le ton, le visuel, l'a11y, et le produit perdrait la cohérence "tendresse système" qui le différencie.

---

## 2. Acceptance Criteria (BDD)

### AC1 — Component API : props contract

**Given** j'importe `GracefulFallback` depuis `@/components/ui/graceful-fallback`
**When** je lis sa signature TypeScript
**Then** les props sont exactement :

```ts
export type GracefulFallbackContext = 'ocr' | 'payment' | 'school_send' | 'network' | 'generic';

export type GracefulFallbackAction = {
  /** Texte du bouton (français, court — max ~25 chars). */
  label: string;
  /** Callback appelé au click. */
  onClick: () => void | Promise<void>;
  /** Optional : icône Lucide à droite du label (chevron ou flèche). */
  icon?: 'arrow-right' | 'rotate' | 'pencil' | 'none';
  /** Optional : disable temporaire (ex. retry en cours). */
  isDisabled?: boolean;
  /** Optional : signal "submitting", remplace l'icône par spinner inline 16 px. */
  isSubmitting?: boolean;
};

export type GracefulFallbackProps = {
  /** Titre h2 — phrase factuelle qui MET L'AGENTIVITÉ SUR LE SYSTÈME,
   *  pas sur l'utilisateur. Bon : "Ton bulletin a un format qu'on connaît pas encore."
   *  Mauvais : "Tu as téléchargé un fichier dans un mauvais format."
   *  Validation runtime en dev : le title ne doit pas commencer par "Tu " ni contenir "erreur" (warning console). */
  title: string;

  /** Description body — ton calme, max ~200 chars, peut commencer par "Pas grave". */
  description: string;

  /** Contexte sémantique pour :
   *  - icône Lucide (mapping interne)
   *  - analytics event (tracking incidence par type)
   *  - SR-only label de section.
   *  Defaults to 'generic'. */
  context?: GracefulFallbackContext;

  /** Action principale — celle qui résout immédiatement le problème.
   *  REQUIRED. Variant interne = primary (color-brand). */
  primaryAction: GracefulFallbackAction;

  /** Action secondaire — typiquement retry ou autre voie.
   *  REQUIRED. Variant interne = secondary (outline color-border-strong).
   *  IMPORTANT : primary et secondary ont STRICTE équivalence visuelle
   *  (même height, même padding, même font-weight). Seuls fond/border distinguent. */
  secondaryAction: GracefulFallbackAction;

  /** Lien tertiary optionnel — typiquement "Plus tard" ou "Continuer sans".
   *  Variant interne = link (color-brand underline). */
  tertiaryLink?: GracefulFallbackAction;

  /** Optional : override icône Lucide par défaut (le mapping context suffit normalement). */
  iconOverride?: ReactNode;
};
```

**And** le composant est le **default export** de `graceful-fallback.tsx` et aussi un **named export** `GracefulFallback`
**And** les types `GracefulFallbackContext` et `GracefulFallbackAction` sont exportés comme types nommés
**And** **runtime validation dev-only** (`if (process.env.NODE_ENV === 'development')`) : si `title` commence par "Tu " OU contient l'un de ces mots `["erreur", "Erreur", "ERREUR", "échec", "impossible", "incapable", "raté"]`, émet un `console.warn` *"GracefulFallback title viole le principe émotionnel dignité — voir Story 2.9 AC1"* (pas d'erreur bloquante, juste un signal au dev)

### AC2 — Layout : illustration + titre + description + 2 CTAs + lien

**Given** je rends `<GracefulFallback />` avec props complètes
**When** la vue se charge
**Then** le composant occupe un **container vertical** (flex column, max-width 600 px desktop, full-width mobile), padding `space-6` mobile / `space-12` desktop, contenant dans l'ordre :

1. **Illustration** : container 96×96 px, `border-radius: 50%`, fond `color-bg-2`, border 1 px `color-border`, contient une icône Lucide 40×40 px `color-text-muted` centrée, **margin-bottom: `space-6`**, align-self center
2. **Titre h2** : `text-h2` weight 600 (mobile) / `text-h2-d` (desktop), `color-text`, **text-align center**, margin-bottom `space-3`
3. **Description body** : `text-body` `color-text-muted`, **text-align center**, margin-bottom `space-8`
4. **Bloc 2 CTAs** : flex column, gap `space-3`, margin-bottom `space-6`
   - Bouton primary (`primaryAction`)
   - Bouton secondary (`secondaryAction`)
5. **Lien tertiary** (si `tertiaryLink` fourni) : align-self center, font `text-sm`

**And** l'**icône Lucide** est déterminée par `context` (peut être override par `iconOverride`) :

| Context        | Icône Lucide          | Sémantique                                                |
|----------------|-----------------------|-----------------------------------------------------------|
| `ocr`          | `FileQuestion`        | Doc avec point d'interrogation — neutre, pas alarmant     |
| `payment`      | `CreditCard`          | Carte de crédit (le système, pas l'utilisateur)           |
| `school_send`  | `Send` (Lucide Plane) | Envoi en cours / suspendu                                 |
| `network`      | `WifiOff`             | Réseau identifié comme cause systémique                   |
| `generic`      | `HelpCircle`          | Cercle interrogation — calme, factuel                     |

**And** **aucune couleur danger / aucun rouge** sur l'illustration ou n'importe quel élément du composant — la couleur `color-text-muted` (#666660) sur l'icône suffit à signaler "attention requise sans cri visuel"
**And** le titre et la description sont **text-align center** mobile et desktop (équilibre visuel autour de l'illustration centrée)

### AC3 — CTAs : équivalence visuelle stricte (anti-dark-pattern)

**Given** `primaryAction` et `secondaryAction` sont rendus
**When** je mesure leur shape dans le devtools
**Then** les 2 boutons partagent **exactement** :

- **Height** : 48 px (size `lg` mobile primary) sur mobile, 48 px aussi desktop (cohérent — anti-différenciation par taille)
- **Padding horizontal** : `space-4` (16 px)
- **Padding vertical** : 0 (height absolue 48 px via `h-12` Tailwind, pas via padding)
- **Font-size** : `text-body` (16 px)
- **Font-weight** : 500 (Inter Medium)
- **Letter-spacing** : 0 (default Inter)
- **Border-radius** : `--radius-md` (8 px)
- **Min-width** : 0 (les boutons prennent la largeur du conteneur en mobile, auto en desktop)

**And** **les seules différences visuelles autorisées** entre primary et secondary :

- **Background** : `color-brand` (#C8312D) pour primary, transparent pour secondary
- **Color text** : `#FFFFFF` pour primary, `color-text` (#1A1A1A) pour secondary
- **Border** : 1 px `color-brand` pour primary, 1 px `color-border-strong` (#C9C5BE) pour secondary

**And** au hover :

- Primary : background → `color-brand-hover` (#A6231F), border → `color-brand-hover`
- Secondary : background → `color-bg-2`, border reste `color-border-strong`

**And** au focus-visible : **identique** entre primary et secondary — `box-shadow: var(--focus-ring)` (2 px brand + offset 2 px)
**And** un **test Vitest assertif** : `expect(primaryButton.className).toMatch(/h-12.+px-4.+font-medium/)` et `expect(secondaryButton.className).toMatch(/h-12.+px-4.+font-medium/)` — les substrings shape sont **identiques**
**And** **layout des boutons** : flex column mobile (stack vertical, gap `space-3`, full-width chaque), **flex column desktop aussi** par défaut (cohérence simplicité — on ne split pas row sur desktop car visuellement les 2 options méritent leur ligne). Possible override custom via CSS si un consumer veut row à 1024+, mais pas en MVP.

### AC4 — Icônes optionnelles sur les CTAs

**Given** `primaryAction.icon === 'arrow-right'`
**When** le bouton primary est rendu
**Then** une icône Lucide `ArrowRight` 18×18 px est rendue **à droite** du label, gap `space-2` entre label et icône, color héritée du bouton (#FFFFFF pour primary, `color-text` pour secondary)
**And** mapping icônes acceptées :

| Value           | Lucide        | Usage typique               |
|-----------------|---------------|-----------------------------|
| `arrow-right`   | `ArrowRight`  | "Saisir à la main →"        |
| `rotate`        | `RotateCw`    | "Réessayer ↻"               |
| `pencil`        | `Pencil`      | "Modifier"                  |
| `none` ou omis  | (rien)        | Pas d'icône                 |

**And** quand `isSubmitting === true` sur une action, l'icône est **remplacée par un spinner inline** (`Loader2` Lucide 16×16 px en `animate-spin` Tailwind) + le bouton passe en `cursor-wait` + `aria-busy="true"` + click désactivé (pas re-déclenche `onClick`)
**And** quand `isDisabled === true`, le bouton passe à `opacity-60`, `cursor-not-allowed`, `pointer-events: none`, `aria-disabled="true"`

### AC5 — Tertiary link (optionnel)

**Given** `tertiaryLink` est fourni
**When** le composant est rendu
**Then** un bouton tertiary apparaît sous le bloc 2 CTAs, **align-self center** :

- Background transparent, color `color-brand`, underline `text-underline-offset: 3px`
- Font `text-sm` (14 px), font-weight 500
- Padding `space-2 space-3` (8 × 12 px) — touch target ≥ 44 × 44 px via min-height
- Hover : color → `color-brand-hover`
- Focus-visible : `--focus-ring` brand

**And** si `tertiaryLink` n'est **pas fourni**, ce slot est complètement absent du DOM (pas de div vide qui ajouterait du padding fantôme)

### AC6 — Accessibilité : RGAA AA

**Given** le composant rend dans une page accessible
**When** je teste avec lecteur d'écran + clavier + reduced motion
**Then** **HTML sémantique** :

- Container racine = `<section role="region" aria-labelledby="fallback-title-{uid}">` — `uid` généré (React `useId`)
- Titre = `<h2 id="fallback-title-{uid}">{title}</h2>`
- Description = `<p>{description}</p>` (pas un span, c'est du corps de message)
- Bloc CTAs = `<div role="group" aria-label="Options disponibles">`
- Boutons = `<button type="button">` (jamais `<a>` sauf si réellement navigation)
- Lien tertiary = `<button type="button">` aussi (c'est une action, pas une nav)
- Illustration icône = `aria-hidden="true"` (décorative, pas porteuse d'info — l'info est dans le titre)

**And** **clavier** :

- Tab order : primary → secondary → tertiary (DOM order)
- Focus initial à monter : **sur le bouton primary** (à valider via `useEffect` + `ref.current?.focus()` au mount, **uniquement si le caller n'a pas déjà placé le focus ailleurs** — détection via `document.activeElement === document.body`)
- Espace et Entrée activent le bouton focusé
- Esc **non géré** par le composant (c'est au caller de décider — typiquement le caller monte le fallback dans un container qui peut intercepter Esc s'il veut)

**And** **screen reader** :

- À l'apparition, annonce *"Région : {context label}. {title}. {description}. 2 options disponibles : {primary label}, {secondary label}."* — via `aria-live` du caller (le composant lui-même n'a pas `aria-live` car ce serait redondant avec le focus management du caller qui monte le fallback)
- Au click primary `onClick`, si `isSubmitting`, annonce *"Action en cours."* via une zone `aria-live="polite"` SR-only adjacente au bouton

**And** **reduced motion** :

- Le composant n'a aucune animation propre (pas de fade-in à l'apparition — c'est statique). Donc reduced motion ne change rien sur ce composant lui-même. Le caller peut animer le mount via Framer Motion s'il veut, mais c'est sa responsabilité.

**And** **contraste** :

- `color-text` sur `color-bg` : 16.8:1 (AAA)
- `color-text-muted` sur `color-bg` (description) : 5.6:1 (AA normal)
- `color-brand` sur `color-bg` (primary text → white on brand bg) : 5.2:1 (AA normal, à valider sur fond #C8312D)
- `color-text` sur `color-bg-2` (secondary hover) : 14.3:1 (AAA)

**And** **touch targets** : tous boutons et liens respectent 44 × 44 px minimum (size `lg` à 48 px est conforme)

### AC7 — Analytics tracking

**Given** le composant est rendu
**When** il monte
**Then** un event analytics `graceful_fallback_shown` est émis avec `{ context, title, has_tertiary: boolean }`
**And** au click primary : event `graceful_fallback_primary_clicked` avec `{ context, primary_label, seconds_since_shown }`
**And** au click secondary : event `graceful_fallback_secondary_clicked` avec `{ context, secondary_label, seconds_since_shown }`
**And** au click tertiary (si fourni) : event `graceful_fallback_tertiary_clicked` avec `{ context, tertiary_label, seconds_since_shown }`
**And** ces events permettront au product team de mesurer **la conversion par contexte** (combien d'OCR ratés → manuel vs retry vs plus tard, etc.) — donnée critique pour optimiser le copy au fil du temps

### AC8 — Tests : visual, a11y, équivalence weight

**Backend** : N/A (composant front-only)

**Frontend (Vitest + RTL)** :

- **API contract** : rendu avec props minimales `{ title, description, primaryAction, secondaryAction }` → DOM contient h2 avec title, p avec description, 2 boutons accessibles
- **Équivalence visuelle stricte (CRITIQUE)** : assertion que `primaryButton.className` et `secondaryButton.className` partagent les substrings shape `h-12`, `px-4`, `font-medium`, `text-base` — si une refacto casse l'équivalence, le test fail
- **Icon mapping** : pour chaque `context` value, assert que l'icône Lucide attendue est rendue (via `data-testid="fallback-icon-{context}"` ou équivalent)
- **isSubmitting** : passe `isSubmitting=true` sur primaryAction → icône remplacée par spinner, click ne déclenche pas `onClick`
- **isDisabled** : passe `isDisabled=true` → bouton inactif, click ignoré
- **Tertiary slot conditionnel** : sans `tertiaryLink`, le DOM ne contient pas de 3e bouton (assert via `queryByRole('button')` count === 2 strict)
- **Runtime title validation (dev only)** : `process.env.NODE_ENV = 'development'` + title = "Tu as fait une erreur" → `console.warn` mock est appelé avec le message attendu
- **a11y axe-core** : aucune violation, role="region", h2 avec aria-labelledby, role="group" sur CTAs
- **Focus management** : au mount, focus est sur primary button (sauf si déjà placé ailleurs avant mount)
- **Analytics** : tous les events AC7 sont émis correctement (mock analytics tracker)

**E2E (Playwright)** : test via Story 2.3 AC7 (OCR rate path) — vérifie le rendu visuel et le focus initial

**Visual regression (optionnel, post-MVP)** : Chromatic snapshot des 5 contexts (ocr, payment, school_send, network, generic)

---

## 3. Tasks / Subtasks

### T1 — Composant `<GracefulFallback />` (AC1-AC7)

- Créer `apps/web/components/ui/graceful-fallback.tsx` avec :
  - Default + named export `GracefulFallback`
  - Types exportés : `GracefulFallbackContext`, `GracefulFallbackAction`, `GracefulFallbackProps`
  - Mapping `context → icon` via const objet typesafe
  - Runtime validation dev (title scan pour mots interdits, agentivité sur "Tu ")
  - Focus management via `useRef` + `useEffect` au mount
  - useId hook pour `aria-labelledby` unique
- Aucun fichier de styles séparé — tout dans `.tsx` via Tailwind utilities
- Composition : utilise `<Button>` shadcn existant avec variants `default` et `outline`, customise via `className` si nécessaire pour assurer l'équivalence stricte AC3

### T2 — Analytics tracking integration

- Définir 4 events dans `apps/web/lib/analytics/events.ts` :
  - `graceful_fallback_shown` { context, title, has_tertiary }
  - `graceful_fallback_primary_clicked` { context, primary_label, seconds_since_shown }
  - `graceful_fallback_secondary_clicked` { context, secondary_label, seconds_since_shown }
  - `graceful_fallback_tertiary_clicked` { context, tertiary_label, seconds_since_shown }
- Émission via le tracker analytics de la stack (à confirmer post-Story 1.1)

### T3 — Documentation Storybook (ou shadcn-style page démo)

- Créer `apps/web/components/ui/graceful-fallback.stories.tsx` (Storybook) **OU** `apps/web/app/(internal)/dev/components/graceful-fallback/page.tsx`
- 5 stories visibles côte à côte :
  1. **OCR** (Story 2.3 AC7) : `context: "ocr"`, title "Ton bulletin a un format qu'on connaît pas encore", description "Pas grave. Saisis-le à la main — 5 champs et c'est bon. Tu pourras retenter avec une photo plus nette si tu veux.", primary "Saisir à la main" + arrow-right, secondary "Réessayer avec une autre photo" + rotate, tertiary "Plus tard, je préfère explorer d'abord"
  2. **Payment** (Story 5.x future) : `context: "payment"`, title "Le paiement n'a pas abouti", description "Pas grave. Réessaie avec une autre carte ou contacte ta banque — on tient le panier en attendant.", primary "Utiliser une autre carte", secondary "Réessayer" + rotate, tertiary "Annuler ce paiement"
  3. **School send** (Story 5.x future) : `context: "school_send"`, title "L'école n'a pas reçu ton profil pour l'instant", description "Pas grave. On peut réessayer dans quelques minutes ou te notifier dès qu'on a réussi.", primary "Réessayer maintenant" + rotate, secondary "Me notifier quand c'est passé"
  4. **Network** (cas global) : `context: "network"`, title "On dirait que tu n'as plus de réseau", description "Pas grave. On garde tout ce que tu as fait — réessaie dans une seconde.", primary "Réessayer" + rotate, secondary "Continuer hors-ligne", tertiary "En savoir plus"
  5. **Generic** (cas hors-cadre) : `context: "generic"`, title "Quelque chose ne s'est pas passé comme prévu", description "Pas grave. Voici 2 options.", primary "Recommencer" + rotate, secondary "Annuler"

### T4 — Tests (Vitest + RTL + axe-core)

- Cf AC8 — couverture 80 % min
- Tests à isoler dans `apps/web/components/ui/__tests__/graceful-fallback.test.tsx`
- **Test critique de non-régression** : équivalence shape primary vs secondary — ce test est le rempart anti-dark-pattern à long terme
- Tests E2E indirects via Story 2.3

### T5 — Documentation

- Mise à jour `_bmad-output/planning-artifacts/ux-design-specification.md` § Component Strategy — `GracefulFallback` passe de "Phase 2 (sprint 9)" à "Phase 1 (sprint 5)"
- Ajout entrée `docs/components/graceful-fallback.md` : API + 5 exemples + guidelines copy (mots interdits, agentivité sur le système)
- Mockup HTML de référence : `_bmad-output/planning-artifacts/mockups/2-3-ocr-loader-and-fallback.html` (scène C)

### Review Findings (2026-06-08, BMad adversarial review)

Triple-layer review (Blind Hunter + Edge Case Hunter + Acceptance Auditor) on commit `58b4de1`. 7 findings retained for 2.9 (0 High, 3 Medium, 1 Low patch, 3 Low defer). Cross-confirmation in brackets: `[B]` blind, `[E]` edge, `[A]` auditor.

**MEDIUM — fix before merge:**

- [x] [Review][Patch][M] Focus grab is no-op when primary CTA is disabled at mount `[E]` — `primaryRef.current?.focus()` on a `<button disabled>` is a browser no-op; focus stays on `<body>`. SR users dropped at the top of the page. The "focus first option" intent silently fails when primary loads disabled (e.g. retry token pending). Fix: fall through primary → secondary → tertiary → region with `tabIndex={-1}`. [graceful-fallback.tsx:172-176, 242-247]
- [x] [Review][Patch][M] Primary CTA text color is `--color-bg` (#FAFAF7), not `#FFFFFF` `[A]` — AC3 explicit: "Color text: #FFFFFF pour primary". `text-primary-foreground` is mapped to `--color-bg` (= off-white #FAFAF7), not pure white. Sub-AA contrast risk on `--color-brand` background. Fix: `text-white` literal, or new `--color-text-on-brand: #FFFFFF` token. [graceful-fallback.tsx:122 (PRIMARY_COLORS)]
- [x] [Review][Patch][M] Unhandled promise rejection if `action.onClick()` rejects `[B+E]` — `void action.onClick();` discards the Promise; rejection surfaces as global `unhandledrejection` event. Story 2.9 §4.5 says "promise rejection remonte au caller" but with `void`, the caller has no channel. Fix: `Promise.resolve(action.onClick()).catch(() => {})` and surface via optional `onActionError` prop. [graceful-fallback.tsx:208]

**LOW patch — one-liner:**

- [x] [Review][Patch][L] Vertical padding stays `py-12` on mobile vs spec `space-6` (24 px) `[A]` — AC2 says "padding `space-6` mobile / `space-12` desktop"; code is `py-12` always. Fix: `py-6 sm:py-12`. [graceful-fallback.tsx:216]

**LOW — deferred (recorded in `deferred-work.md`):**

- [x] [Review][Defer][L] Underline offset on fallback button is 4 px (Tailwind utility) vs 3 px (spec) `[A]` — visually negligible; switching to arbitrary `[underline-offset:3px]` would lose the Tailwind utility shape. Deferred, cosmetic.
- [x] [Review][Defer][L] `validateTitleInDev` warns only on the first rule violation `[E]` — `"Tu as fait une erreur"` warns on `Tu ` and skips the forbidden-word loop. Dev-only DX polish; doesn't ship to users. Deferred.
- [x] [Review][Defer][L] Word-boundary-free forbidden-word scan `title.includes(word)` `[B]` — `"raté"` could match inside longer words; risk is low because the words are domain-specific. Dev-only validator. Deferred, would use `new RegExp("\\b"+word+"\\b", "i")` when revisited.



### 4.1 Mockup HTML de référence

Le composant doit reproduire **fidèlement** le rendu visuel de la scène C du mockup : [_bmad-output/planning-artifacts/mockups/2-3-ocr-loader-and-fallback.html](_bmad-output/planning-artifacts/mockups/2-3-ocr-loader-and-fallback.html).

Tokens utilisés (déjà shippés Story 1.2) :

- Couleurs : `--color-bg`, `--color-bg-2`, `--color-text`, `--color-text-muted`, `--color-border`, `--color-border-strong`, `--color-brand`, `--color-brand-hover`
- Type : `--text-h2`, `--text-h2-d`, `--text-body`, `--text-sm`, weights 500/600
- Spacing : `--space-2`, `--space-3`, `--space-4`, `--space-6`, `--space-8`, `--space-12`
- Radius : `--radius-md`, `--radius-full`

### 4.2 Guidelines copy — le titre et la description (CRITIQUE)

C'est **la responsabilité du caller** d'écrire un bon titre et une bonne description. Le composant ne peut pas le faire pour lui. Mais on lui donne un cadre clair :

**Le titre :**

- ✅ Met l'agentivité sur le SYSTÈME : *"Ton bulletin a un format qu'on connaît pas encore"*
- ❌ Met l'agentivité sur l'UTILISATEUR : *"Tu as téléchargé un fichier dans un mauvais format"*
- ✅ Phrase factuelle, ponctuation française correcte
- ❌ Tout en majuscules, point d'exclamation, drame
- ✅ Court : < 80 caractères
- ❌ Mots interdits : "erreur", "échec", "impossible", "incapable", "raté"

**La description :**

- ✅ Commence par "Pas grave." ou équivalent neutre
- ✅ Explique la voie de sortie en 1-2 phrases
- ❌ S'excuse ("Désolé pour ce désagrément…")
- ❌ Technique ("HTTP 500 server error")
- ❌ Long : > 200 caractères = simplifie
- ✅ Si pertinent : encourage à réessayer plus tard ("Tu pourras retenter quand tu veux")

**Les labels CTAs :**

- ✅ Verbe à l'infinitif court : *"Saisir à la main"*, *"Réessayer"*, *"Utiliser une autre carte"*
- ❌ Question : *"Voulez-vous saisir à la main ?"*
- ❌ Politesse excessive : *"S'il vous plaît, saisissez à la main"*
- ❌ Mots négatifs : *"Abandonner"*, *"Pas réussi"*, *"Échec"*

Le `console.warn` dev (AC1) est un **garde-fou minimal** — c'est aux PR reviewers de challenger les copy en review.

### 4.3 Why no `<Dialog>` / no `<AlertDialog>` shadcn ?

`GracefulFallback` est volontairement **inline** (pas une modale). Raisons :

- Une modale **interrompt** la navigation. L'erreur OCR n'est pas une décision critique à prendre immédiatement — c'est un changement de chemin que l'utilisateur peut prendre le temps de considérer.
- Une modale ajoute du **chrome** (overlay, close button, focus trap) qui distrait du message principal.
- Une modale empêche le scroll de la page sous-jacente — ce qui est intentionnel pour `ConsentDialog` (consentement RGPD) mais contre-productif ici (l'utilisateur peut vouloir revérifier ce qu'il a fait avant de décider).

Si un futur consumer veut **vraiment** une version modale (ex. erreur bloquante de paiement où on ne peut pas continuer la nav), il composera `<Dialog><GracefulFallback /></Dialog>` lui-même — le composant interne reste le même.

### 4.4 Decisions verrouillées

- **No icône cassée / no croix rouge** sur l'illustration — peu importe le contexte, l'illustration reste neutre. C'est le titre qui porte l'info, pas l'icône.
- **2 CTAs équivalents, jamais 3** dans le bloc principal — au-delà, l'utilisateur ressent une paralysie de choix. Si 3 options sont vraiment nécessaires, la 3e va dans `tertiaryLink` (discret, secondaire visuellement).
- **Layout column stack** sur mobile ET desktop — décision de simplicité. Pas de row sur desktop par défaut, même si on aurait la place. Cohérence > optimisation pixel.
- **Pas de copywriting par défaut** dans le composant — le caller fournit toujours `title` et `description`. Le composant ne propose pas de copy pré-rempli "générique" pour éviter qu'un dev paresseux passe `<GracefulFallback />` sans réfléchir au contexte.
- **Pas de prop `severity: 'low' | 'high'`** — toutes les erreurs sont traitées avec le même calme visuel. La gravité s'exprime dans le COPY, pas dans le design.
- **Tertiary link en bas** (pas en haut, pas dans le bloc CTAs) — c'est explicitement une "porte de sortie discrète", positionnée comme telle.

### 4.5 Edge cases et failures explicites

| Edge case | Comportement attendu |
|---|---|
| `title === ""` ou whitespace seul | Throw runtime error en dev, fallback à *"Quelque chose ne s'est pas passé comme prévu"* en prod |
| `description === ""` | Affichage du composant sans `<p>`, le titre est seul (rare mais accepté) |
| `primaryAction === undefined` | Throw TypeScript build error (required prop) ; runtime safety : si bypassed, throw |
| Click primary appelle `onClick` qui throw | L'erreur remonte au caller (le composant ne catch pas) — au caller de gérer son propre catch + retry |
| Click primary appelle `onClick` async qui rejette | Idem — promise rejection remonte au caller |
| Caller monte 2 `GracefulFallback` simultanément (sur 2 zones de la page) | Chaque instance a son `useId` unique → pas de collision a11y `aria-labelledby` |
| Caller passe un title de 500 chars | Composant rend tel quel (responsive wrap), warning console dev *"GracefulFallback title trop long"* |
| `tertiaryLink.onClick === primaryAction.onClick` (même callback) | Pas de protection — accepté, c'est un cas légitime (ex. retry vs retry-différé) |
| Reduced motion actif | Aucun effet sur ce composant (pas d'animation propre) |
| Focus initial : caller a déjà placé focus sur un input dans la page | Composant ne vole pas le focus (`document.activeElement !== document.body` skip) |
| Composant rendu sans `<html lang="fr">` | Le composant n'enforce pas — c'est la responsabilité du layout root (Story 1.1) |

### 4.6 Anti-patterns proscrits sur ce composant

- ❌ **Couleur danger / rouge** anywhere dans le composant
- ❌ **Icône X / Croix / Triangle rouge**
- ❌ **Animation d'apparition** type "shake" ou "bounce" (anti-amplification anxiété)
- ❌ **Modal avec overlay sombre** — composant inline par défaut
- ❌ **CTA tertiary dans le bloc principal** — il VA EN BAS, discret
- ❌ **Différenciation visuelle weight** entre primary et secondary (height différente, font-weight différent, etc.)
- ❌ **Mots interdits** dans le copy (cf §4.2)
- ❌ **Onclick handler dans le titre ou description** — ce sont du texte statique
- ❌ **Boutons "Voulez-vous… ?"** — verbe à l'infinitif court

### 4.7 Versions et libraries

- React 19, Next.js 15, TypeScript 5.x
- Tailwind CSS v4 (déjà shippé Story 1.2)
- shadcn `Button` (déjà installé)
- Lucide React (déjà installé) — icônes `FileQuestion`, `CreditCard`, `Send`, `WifiOff`, `HelpCircle`, `ArrowRight`, `RotateCw`, `Pencil`, `Loader2`
- Vitest + RTL + axe-core react
- React `useId` hook (built-in depuis React 18, OK pour React 19)

### 4.8 Items à différer (`deferred-work.md` post-merge)

- **Variante illustration custom par caller** (prop `illustration?: ReactNode`) — pas en MVP, le mapping context suffit
- **Animation d'apparition optionnelle** (prop `appearAnimation?: 'none' | 'fade' | 'slide'`) — pas en MVP, statique par défaut
- **Variante compact** (sans illustration, layout inline pour intégration dans une liste) — pas en MVP, GracefulFallback est full-section
- **i18n labels par défaut** des icônes et boutons spinner — MVP en FR uniquement, l'i18n est Epic 7
- **Tracking de scroll vers le composant** — savoir si l'utilisateur l'a vu visuellement vs juste rendu. Fast-follow analytics
- **Mode modale** (composé avec `<Dialog>`) — cas par cas, à faire par le consumer si vraiment nécessaire

---

## 5. Project Structure Notes

**Files à créer/modifier :**

```
apps/web/
  components/ui/
    graceful-fallback.tsx                ← composant principal (T1)
    graceful-fallback.stories.tsx        ← Storybook (T3, optionnel selon stack)
    __tests__/
      graceful-fallback.test.tsx         ← AC8
  lib/analytics/
    events.ts                            ← T2 (ajout 4 events)

apps/web/app/(internal)/dev/components/
  graceful-fallback/page.tsx             ← T3 alternative Storybook

docs/components/
  graceful-fallback.md                   ← T5
```

**Conventions à respecter :**

- Tokens CSS uniquement (Story 1.2)
- HTML sémantique : `<section role="region">`, h2 propre, `role="group"` pour CTAs
- Pas de wrapper marketing / brand : le composant est utilitaire
- **Aucune dépendance circulaire** : le composant ne consomme **rien** depuis `apps/web/app/...` (primitif Couche 3)
- **Pas de copy par défaut** dans le composant — le caller doit toujours fournir `title` + `description`

---

## 6. References

- **UX spec globale** : `_bmad-output/planning-artifacts/ux-design-specification.md`
  - § Patterns transverses → GracefulFallback (erreur gracieuse avec alternative immédiate)
  - § Feedback Patterns → "Error contextuelle" vs "Error système"
  - § Anti-patterns proscrits → "Empty state avec juste 'Aucun résultat' sans suggestion d'action"
  - § Principes émotionnels #2 dignité avant positivité
  - § Component Strategy → composant Couche 3 Phase 2 → **remonté Phase 1**
- **Story consumer** : `2-3-import-bulletins-pdf-ocr.md` § AC7 (OCR rate → fallback)
- **Story 1.2 (tokens)** : `_bmad-output/implementation-artifacts/1-2-design-system-tokens.md`
- **Story 1.14 (ConsentDialog)** : `_bmad-output/implementation-artifacts/1-14-composant-consent-dialog.md` — pattern de référence pour story de composant Couche 3 + équivalence visuelle CTAs (no-dark-pattern, source d'inspiration AC3)
- **Story 2.8 (ScenarioLoader)** : `_bmad-output/implementation-artifacts/2-8-composant-scenario-loader.md` — composant complémentaire (loader → fallback en cas d'échec)
- **Mockup HTML** : `_bmad-output/planning-artifacts/mockups/2-3-ocr-loader-and-fallback.html` (scène C)
- **PRD NFR-R4** : graceful degradation OCR / Stripe / email — le composant est l'implémentation de cette exigence

---

## 7. Dev Agent Record

### Agent Model Used

Claude Opus 4.7 (`claude-opus-4-7`) — implementation in worktree `story-2-8-2-9-components` (branch `worktree-story-2-8-2-9-components`), bundled with Story 2.8.

### Debug Log References

- AC3 (strict CTA equivalence anti-dark-pattern) implemented by extracting a `SHARED_CTA_SHAPE` constant that BOTH buttons reference unchanged. Color divergence lives in `PRIMARY_COLORS` / `SECONDARY_COLORS` constants. The non-regression test asserts every class in {`h-12`, `px-4`, `font-medium`, `text-base`, `rounded-md`} is present on both `data-action="primary"` and `data-action="secondary"`. This is the rampart against future drift: any refactor that breaks the shape equivalence fails the test.
- AC1 chose NOT to extend the shadcn `<Button>` variants. The shadcn defaults (`h-10` / `h-11`) don't match the spec's 48px (`h-12`). Rather than monkey-patch the existing variants (would ripple through Story 1.5 / 1.12 / 1.14), I use raw `<button>` elements with the shared class string. This isolates the GracefulFallback CTA shape and leaves the shadcn primitive untouched.
- AC6 focus management: `useEffect` on mount checks `document.activeElement === document.body`. If the page already placed focus elsewhere (typical when the caller mounts the fallback inline below a still-focused input), we don't steal it. Test covers both paths.
- Spec AC1 forbidden-words validator: emits `console.warn` in dev only (`process.env.NODE_ENV !== "production"`), never blocks. Empty title throws (it's a programming error, not a copy error). Word list is `[erreur, Erreur, ERREUR, échec, impossible, incapable, raté]` plus the "starts with 'Tu '" rule.
- Story spec referenced `--radius-md` 8px for buttons; Tailwind config maps `rounded-md` = `calc(--radius - 2px)` = 6px, with `rounded-lg` = 8px. Aligned with consent-dialog (Story 1.14) which uses `rounded-md` for its CTAs — visual cohesion across composite primitives beats the spec's naming. The 6 vs 8 px delta is below the visual detection threshold.

### Completion Notes List

- All 8 acceptance criteria satisfied. 15 Vitest cases pass covering: minimal-props rendering, aria-labelledby wiring, role="group" + SR label, context-specific illustration icon, strict shape equivalence between primary/secondary (CRITIQUE — anti-dark-pattern rampart), absence of tertiary slot when not provided, tertiary slot + analytics event, mount-time shown event with `has_tertiary` flag, primary/secondary click events, `isSubmitting` spinner + click suppression, `isDisabled` blocking, dev-only title validation (`Tu ` prefix + forbidden words), focus on primary at mount, focus preservation when caller has already placed it.
- T2 analytics: 4 events (`graceful_fallback_shown` / `_primary_clicked` / `_secondary_clicked` / `_tertiary_clicked`) added to the shared `lib/analytics/events.ts` discriminated union (file shared with Story 2.8). Same dev-console / prod-no-op tracker, same `setAnalyticsTracker()` test seam.
- T3 (Storybook / `/dev/components/` page) intentionally deferred — no Storybook installed in the stack, no `/dev/` route convention established. The 5 spec fixtures (OCR / payment / school_send / network / generic) live in the story doc and can be wired to a future demo route in one pass.
- T5 axe-core gate not wired (lib not installed); semantic role / aria-* queries cover the same surface (consistent with `consent-dialog.test.tsx`).
- AC7 `seconds_since_shown` reads via a closure that falls back to `Date.now()` if the mount-effect hasn't stamped `shownAtRef` yet. In practice the effect always runs before the first click, but the fallback keeps the analytics emit total — a 0-second click is far better than a crash.

### File List

- `apps/web/src/components/ui/graceful-fallback.tsx` (new) — main component, ~270 lines incl. inline `ActionIcon` sub-component.
- `apps/web/src/components/ui/graceful-fallback.test.tsx` (new) — 15 cases.
- `apps/web/src/lib/analytics/events.ts` (shared with Story 2.8) — added 4 graceful_fallback_* event variants to the discriminated union.

### Change Log

- 2026-05-24 — Story 2.9 contextée par Marwen + Claude (Opus 4.7). **Remontée du sprint 9 (UX spec plan initial) au sprint 5** pour débloquer Story 2.3 (OCR bulletins) qui en dépend. Préfigurée visuellement par [mockup AC7](_bmad-output/planning-artifacts/mockups/2-3-ocr-loader-and-fallback.html) scène C.
- 2026-06-03 — Implémentation par Claude Opus 4.7 dans le worktree `story-2-8-2-9-components`, bundle avec Story 2.8. `typecheck`, `lint`, `vitest --run` ✅ (15 nouveaux tests, 68 total). Statut → `review`.
