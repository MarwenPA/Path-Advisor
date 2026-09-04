# Story 8.8: Dashboard d'accueil élève — page modulaire post-connexion

**Epic:** 8 — Continuité Temporelle & Notifications
**Status:** review
**Sprint:** Epic 8
**Story Key:** `8-8-dashboard-accueil-eleve`
**Estimation:** M (medium) — cette story **compose** presque exclusivement des briques déjà livrées (`ScoreVocationnel` compact, `ProfileMaturityIndicator` variant `dashboard-card`, favoris `/mes-paris`) sur une page neuve. Aucun nouveau modèle backend, aucun nouvel endpoint d'écriture. Le seul vrai risque est le câblage transverse (route guard, redirect post-login) qui touche des fichiers partagés par tous les rôles.

> Story 8.8 crée la nouvelle home élève (`/accueil`) et donne enfin un contenu réel au « dashboard normal » que la Story 8.6 (`DeltaRecap`, non implémentée à ce jour) suppose déjà exister. Aujourd'hui la home élève est directement `/mes-metiers` (liste de recommandations brute, Epic 3) — cette story la remplace par une page à 3 modules : recommandations, progression, parcours sauvegardés.

---

## 1. User Story

**As an** élève,
**I want** atterrir après connexion sur une page qui rassemble mes métiers recommandés, ma progression et mes parcours sauvegardés,
**So that** je sache immédiatement où j'en suis et quoi faire ensuite, plutôt que de tomber sur une simple liste sans contexte (FR47).

**Business value:** Première vraie « home » du produit — jusqu'ici l'app enchaîne des listes isolées (métiers, paris) sans jamais donner une vue d'ensemble. C'est aussi le prérequis technique explicite de la Story 8.6 (`DeltaRecap`), qui n'a aujourd'hui aucune page derrière laquelle s'afficher.

---

## 2. Scope decisions (lire avant les ACs)

- **Route** : `/accueil` (cohérent avec la famille de routes FR déjà en place : `/mes-metiers`, `/mes-paris`, `/parametres`). Nouveau fichier `apps/web/src/app/(authenticated)/accueil/page.tsx`.
- **`getPostLoginPath`** (`apps/web/src/lib/auth/post-login-redirect.ts`) : `student` pointe désormais vers `/accueil` au lieu de `/mes-metiers`. **Ne pas supprimer** la route `/mes-metiers` elle-même (le module « Tes métiers » y renvoie via « Voir tous mes métiers », et Story 3.x/Story 6.2 la référencent encore).
- **`route-guards.ts`** : ajouter `"/accueil": ["student"]` à `ROUTE_ALLOWED_ROLES`. **Point d'attention découvert en recherche** : `/mes-metiers`, `/mes-paris`, `/metiers`, `/schools`, `/premium` ne sont eux-mêmes PAS dans cette matrice alors qu'ils fonctionnent en prod — `assertAllowedRole` a un comportement fail-closed documenté (« Code-review P12 ») pour toute route non listée. Avant de conclure à un bug pré-existant à corriger ici, **vérifie d'abord** (`route-guards.test.ts` + `layout.tsx`) si ces routes passent par un autre mécanisme (ex. préfixe non testé, ou le guard n'est pas appelé pour elles) — si c'est bien un trou de couverture, ajoute UNIQUEMENT `/accueil` à la matrice (ne corrige pas les routes existantes, hors scope de cette story) et note l'observation dans Completion Notes pour une story de durcissement dédiée.
- **Module « Ta progression »** : réutilise **tel quel** `ProfileMaturityIndicator` avec `variant="dashboard-card"` (`apps/web/src/components/features/profile/profile-maturity-indicator.tsx`) — ce variant existe déjà spécifiquement pour ce cas d'usage (retourne `null` si `level === "complete"`, affiche déjà un lien). Alimenté par `useMaturityLevel()` (`apps/web/src/hooks/use-maturity-level.ts`). **Ne pas créer de nouveau composant de progression.**
- **Module « Tes métiers »** : les 3 premiers éléments de `fetchRecommendations().results` (déjà triés par score décroissant côté backend, à vérifier — sinon trier côté client par `score` desc avant de slicer), rendus avec `<ScoreVocationnel variant="compact" .../>` dans le même pattern `<Link href="/metiers/{slug}?...">` que `MetiersList.tsx`/`parent-dashboard.tsx` (dupliquer le petit helper de construction de l'URL plutôt que de le factoriser dans cette story — pas dans le scope).
- **Module « Tes paris »** : les 3 premiers éléments de `GET /api/v1/mes-paris/` (déjà triés par `-favorited_by__created_at`, donc `.slice(0, 3)` client-side suffit — le backend n'a pas de paramètre `?limit=`, ne PAS en ajouter dans cette story, c'est un slice trivial côté page). Réutilise `FicheEcole` (variant déjà utilisé par `/mes-paris/page.tsx` aujourd'hui) — **ne PAS** essayer de brancher `ParcoursCard` ici (le `TODO(story-4-12)` dans `mes-paris/page.tsx` est un chantier distinct, hors scope).
- **Layout composant** : pas de nouveau composant de grille générique — composer à la main avec `<section aria-labelledby>` + `<h2>` (pattern déjà utilisé par `parent-dashboard.tsx`), et le composant `Card`/`CardHeader`/`CardContent` du design system (`apps/web/src/components/ui/card.tsx`) pour l'habillage visuel de chaque module.
- **`DeltaRecap` (Story 8.6)** : n'existe pas dans le code à ce jour (vérifié — zéro fichier). Cette story **n'en dépend pas** et ne crée aucun point d'intégration avec lui ; 8.6 s'en chargera plus tard en s'affichant par-dessus `/accueil`.

---

## 3. Acceptance Criteria (BDD)

### AC1 — Nouvelle home élève avec 3 modules

**Given** je suis un élève authentifié et je me connecte
**When** j'arrive sur `/accueil`
**Then** je vois 3 sections distinctes dans cet ordre visuel : **Ta progression** (si non `complete`) → **Tes métiers** → **Tes paris**
**And** chaque section est une `<section aria-labelledby="...">` avec un `<h2>` de titre

### AC2 — Module « Ta progression »

**Given** mon `ProfileMaturityLevel` n'est pas `complete`
**When** la page charge
**Then** le module affiche `<ProfileMaturityIndicator variant="dashboard-card" level={...} nextActions={...} />` tel quel (aucune prop nouvelle, aucun style custom)

**Given** mon profil est `complete`
**When** la page charge
**Then** le module ne s'affiche pas du tout (comportement déjà géré par le composant — `variant="dashboard-card"` retourne `null`)

### AC3 — Module « Tes métiers »

**Given** j'ai au moins 1 recommandation
**When** la page charge
**Then** je vois les 3 recommandations au score le plus élevé en `<ScoreVocationnel variant="compact">`, chacune liée vers sa fiche métier (même construction d'URL que `MetiersList.tsx` : `slug`, `score`, `confidence`, `signals`)
**And** un lien « Voir tous mes métiers » vers `/mes-metiers`

**Given** je n'ai aucune recommandation (profil trop récent, service IA down, etc.)
**When** la page charge
**Then** le module affiche un texte d'invitation court (pas de section vide silencieuse, pas d'erreur visible) — ex. « Tes recommandations arrivent dès que ton profil est prêt »

### AC4 — Module « Tes paris »

**Given** j'ai au moins 1 école en favori (`/mes-paris`)
**When** la page charge
**Then** je vois les 3 favoris les plus récents (le tri backend existant suffit, `.slice(0,3)` côté page)
**And** un lien « Voir tous mes paris » vers `/mes-paris`

**Given** je n'ai aucun favori
**When** la page charge
**Then** le module affiche un texte d'invitation + lien vers l'exploration des écoles (cohérent avec l'empty state déjà écrit dans `/mes-paris/page.tsx` — réutiliser le même texte si possible, ne pas en inventer un nouveau)

### AC5 — Élève au profil neuf (tous modules vides sauf progression)

**Given** un élève dont le profil vient d'être créé (aucune reco, aucun pari, onboarding non terminé)
**When** il consulte `/accueil`
**Then** le module « Ta progression » est affiché en premier et domine visuellement (c'est la seule chose actionnable) — pas de mise en avant artificielle des modules « Tes métiers »/« Tes paris » vides

### AC6 — Responsive

**Given** je consulte `/accueil` sur mobile
**When** la page s'affiche
**Then** les modules s'empilent verticalement dans l'ordre de AC1

**Given** je consulte `/accueil` sur desktop (≥1024px)
**When** la page s'affiche
**Then** « Ta progression » occupe un bandeau supérieur pleine largeur (si présent), « Tes métiers » et « Tes paris » sont côte à côte en 2 colonnes en dessous

### AC7 — Routing et redirection

**Given** un élève se connecte
**When** `getPostLoginPath` est appelé avec `role="student"`
**Then** il retourne `/accueil` (plus `/mes-metiers`)

**Given** un élève authentifié navigue directement vers `/accueil`
**When** `assertAllowedRole` évalue la route
**Then** l'accès est autorisé pour `role="student"` uniquement (403/forbidden pour les autres rôles, cohérent avec le reste de la matrice)

### AC8 — Accessibilité RGAA AA

**Given** un utilisateur de lecteur d'écran
**When** il navigue `/accueil`
**Then** chaque `<section>` a un `aria-labelledby` pointant vers son `<h2>`, l'ordre de tabulation suit l'ordre visuel, et les liens « Voir tous mes X » ont un texte de lien explicite (pas de « cliquez ici »)

---

## 4. Dev Notes

### 4.1 — Réutilisation stricte (NE PAS réinventer)

- **`ProfileMaturityIndicator`** (`apps/web/src/components/features/profile/profile-maturity-indicator.tsx`) + **`useMaturityLevel`** (`apps/web/src/hooks/use-maturity-level.ts`) — le variant `dashboard-card` a été construit *pour* cet usage exact (Story 2.7). Zéro nouvelle logique de progression à écrire.
- **`ScoreVocationnel`** (`apps/web/src/components/professions/ScoreVocationnel.tsx`), `variant="compact"` — copier le pattern d'usage de `MetiersList.tsx:101` (construction du lien avec score/confidence/signals en query params) ou de `parent-dashboard.tsx:63` (mapping `confidence_level === "low" → "indicative"`).
- **`fetchRecommendations()`** (`apps/web/src/lib/api/recommendations.ts`) — appel direct, pas de nouveau client à écrire. Vérifier si `results` est déjà trié par score desc (probable vu l'usage existant) ; sinon trier avant `.slice(0, 3)`.
- **`FicheEcole`** — le composant déjà utilisé par `/mes-paris/page.tsx` pour rendre chaque `School`. Réutiliser le même variant.
- **`Card`/`CardHeader`/`CardContent`** (`apps/web/src/components/ui/card.tsx`) pour l'habillage visuel des modules « Tes métiers »/« Tes paris » (pas nécessaire pour « Ta progression », qui a déjà son propre habillage dans `ProfileMaturityIndicator`).

### 4.2 — Page Server Component, pattern d'agrégation

Suivre le pattern Server Component déjà utilisé par `/mes-paris/page.tsx` (`apiFetch` direct, `try/catch` → tableau vide sur erreur, pas de throw qui casserait toute la page pour un module en panne). **Chaque module doit dégrader indépendamment** : si `/api/v1/mes-paris/` échoue, le module « Tes paris » affiche son empty state — ça ne doit JAMAIS faire planter les modules « Tes métiers »/« Ta progression ». Utiliser `Promise.allSettled` (pas `Promise.all`) pour les 2 fetchs côté page (recommandations + mes-paris) ; `ProfileMaturityIndicator` reste côté client via son hook existant (TanStack Query gère déjà son propre état d'erreur/chargement).

### 4.3 — Tests (pattern à suivre)

- Page : mocker les modules `@/lib/api/recommendations` et l'équivalent pour `/mes-paris` (créer un petit client `apps/web/src/lib/api/mes-paris.ts` si utile pour la testabilité — actuellement la page `/mes-paris` appelle `apiFetch` en dur sans client dédié, ce qui explique qu'elle n'a aucun test ; ne pas reproduire ce trou de couverture ici). Suivre le pattern de mock par module de `apps/web/src/app/page.test.tsx`, PAS un mock de `fetch` global.
- `useMaturityLevel`/`ProfileMaturityIndicator` : mocker le hook (`vi.mock("@/hooks/use-maturity-level", ...)`) plutôt que le fetch sous-jacent, comme fait pour `ScoreVocationnel`/`SignauxDrawer` dans `MetiersList.test.tsx`.
- Couvrir explicitement : les 3 modules avec contenu, les 3 empty states indépendamment, le cas AC5 (profil neuf), et un cas où un module échoue (mock rejeté) sans casser les autres.

### 4.4 — Anti-patterns à éviter

- **NE PAS** utiliser `Promise.all` pour les fetchs de la page — un module en panne ferait planter toute la home (violerait AC3/AC4 empty-state-jamais-erreur).
- **NE PAS** créer de nouveau composant de progression — `ProfileMaturityIndicator variant="dashboard-card"` existe déjà pour ça.
- **NE PAS** toucher à `ParcoursCard`/le TODO de `/mes-paris/page.tsx` — chantier distinct.
- **NE PAS** implémenter quoi que ce soit lié à `DeltaRecap` (Story 8.6) — il n'existe pas encore, cette story est autosuffisante.
- **NE PAS** ajouter de paramètre `?limit=` côté backend `/api/v1/mes-paris/` — un `.slice(0,3)` client-side suffit très largement pour 3 éléments et évite de toucher à un endpoint partagé par une autre page.

### 4.5 — Risques

| Risque | Likelihood | Mitigation |
|---|---|---|
| `route-guards.ts` a un vrai trou de couverture pré-existant (`/mes-metiers` etc. non listés) et l'ajout de `/accueil` révèle/interagit mal avec ce comportement | M | Lancer `route-guards.test.ts` avant et après l'ajout ; si le comportement fail-closed bloque réellement des routes existantes en prod, c'est un bug pré-existant hors scope — documenter, ne pas corriger ici |
| Le tri de `fetchRecommendations().results` n'est pas garanti par score desc | L | Trier explicitement côté page avant `.slice(0,3)`, ne pas supposer l'ordre backend |
| Layout desktop 2 colonnes casse sur un écran entre mobile et 1024px | L | Utiliser les breakpoints Tailwind déjà en place ailleurs dans le repo (`md:`/`lg:`), tester visuellement aux tailles intermédiaires |

---

## 5. Tasks / Subtasks

- [x] **T1 — Page `apps/web/src/app/(authenticated)/accueil/page.tsx`**
  - [x] T1.1 Server Component, `Promise.allSettled([fetchRecommendations(), fetch mes-paris])`
  - [x] T1.2 Section « Ta progression » (Client Component wrapper autour de `ProfileMaturityIndicator`/`useMaturityLevel`)
  - [x] T1.3 Section « Tes métiers » (3 `ScoreVocationnel` compact + lien « Voir tous »)
  - [x] T1.4 Section « Tes paris » (3 `FicheEcole` + lien « Voir tous »)
  - [x] T1.5 Empty states des 3 modules (texte + CTA, jamais vide silencieux)
  - [x] T1.6 Responsive mobile (stack) / desktop (bandeau + 2 colonnes)

- [x] **T2 — Client API `mes-paris` (petit, pour testabilité)**
  - [x] T2.1 `apps/web/src/lib/api/mes-paris.ts` — `fetchMesParis(): Promise<School[]>` (wrap `apiFetch("/api/v1/mes-paris/")`), typé sur le type `School` déjà exporté quelque part côté frontend (vérifier `apps/web/src/components/schools/types.ts` ou équivalent avant d'en recréer un)

- [x] **T3 — Routing transverse**
  - [x] T3.1 `apps/web/src/lib/auth/post-login-redirect.ts` : `student: "/accueil"`
  - [x] T3.2 `apps/web/src/lib/auth/route-guards.ts` : ajouter `"/accueil": ["student"]` à `ROUTE_ALLOWED_ROLES`
  - [x] T3.3 Vérifier `route-guards.test.ts` + le comportement réel des routes existantes non listées (§4.5) — documenter l'observation sans corriger si hors scope

- [x] **T4 — Tests**
  - [x] T4.1 `apps/web/src/app/(authenticated)/accueil/page.test.tsx` — 3 modules avec contenu, 3 empty states, cas profil neuf (AC5), cas 1 module en échec sans casser les autres
  - [x] T4.2 `apps/web/src/lib/api/mes-paris.test.ts` (si le client est assez substantiel pour le justifier — sinon couvert indirectement par T4.1) — **non créé**, couvert indirectement par `page.test.tsx` (mock du module `@/lib/api/mes-paris`) comme prévu par la clause alternative de la tâche : le client est un wrapper d'une ligne, sans logique propre à tester isolément.
  - [x] T4.3 `route-guards.test.ts` — cas `/accueil` autorisé pour `student`, refusé pour les autres rôles
  - [x] T4.4 `post-login-redirect.test.ts` si le fichier existe déjà (sinon, couverture indirecte suffisante via `page.test.tsx` du login, ne pas créer un fichier de test dédié pour une fonction d'une ligne) — le fichier n'existe pas, couverture indirecte via `app/page.test.tsx` (mis à jour pour `/accueil`) conservée.

- [x] **T5 — Accessibilité**
  - [x] T5.1 Vérification manuelle `aria-labelledby`/ordre de tabulation (pas d'outil automatisé dans le repo pour ça à ce jour, cf. `deferred-work.md` sur `axe-core` non encore intégré)

---

## 6. Out of Scope (do NOT do in this story)

- **`DeltaRecap`** (Story 8.6) — composant et logique de delta non implémentés ici.
- **Branchement `ParcoursCard` sur `/mes-paris`** — TODO pré-existant, chantier distinct.
- **Paramètre de pagination/limite sur `/api/v1/mes-paris/`** — slice client-side suffit.
- **Personnalisation avancée du dashboard** (réordonnancement de modules par l'utilisateur, widgets configurables) — pas demandé, pas dans l'epic.

> **Mise à jour post-review (2026-09-04)** : le point "trou de couverture `route-guards.ts`" ci-dessus a été **requalifié et corrigé**, pas seulement documenté — voir §10 Review Findings. Ce n'était pas de la dette technique différable : c'était un bug bloquant déjà actif en prod, rendu critique par le fait que `/accueil` (cette story) devient la home dont 100 % des liens sortants pointaient vers des routes cassées.

---

## 7. Definition of Done

- [x] Toutes les ACs (1–8) implémentées ; AC2/AC6/AC8 initialement livrées SANS test réel (composant entièrement mocké) — corrigé en review, voir §10
- [x] `/accueil` devient la home élève (`getPostLoginPath` + `route-guards.ts` mis à jour, tests correspondants verts)
- [x] Les 3 modules dégradent indépendamment — initialement vrai seulement pour les rejets de promesse, PAS pour un payload 200 malformé (bug réel, corrigé en review §10)
- [x] Aucune régression sur `/mes-metiers`, `/mes-paris`, `route-guards.test.ts`, `page.test.tsx` (racine) existants
- [x] `npx vitest run` vert (715 passés / 5 échecs pré-existants sans rapport, après review), `npm run lint` (0 erreur, warnings pré-existants uniquement) + `npx tsc --noEmit` clean sur les fichiers de cette story
- [x] Sprint-status sync : `8-8-dashboard-accueil-eleve: ready-for-dev → in-progress → review` (le passage à `done` reste au reviewer/PO)

---

## 8. Dev Agent Record

### Agent Model Used

claude-sonnet-5 (Claude Code)

### Debug Log References

None — no long-running debug session needed. `npx vitest run`, `npm run lint`, `npx tsc --noEmit` executed directly from the shell during dev (see Completion Notes for outcomes).

### Completion Notes List

- **Route-guards pre-existing coverage gap confirmed (§4.5/§2 point d'attention)** — verified by reading `route-guards.test.ts` and `(authenticated)/layout.tsx`: `assertAllowedRole` is called unconditionally for every path under `(authenticated)/*` with no bypass, and `/mes-metiers`, `/mes-paris`, `/metiers`, `/schools`, `/premium` genuinely have **no entry** in `ROUTE_ALLOWED_ROLES`. Given the documented fail-closed default ("Code-review P12"), a direct call `assertAllowedRole("/mes-metiers", "student")` returns `"forbidden"` today — this is a real pre-existing bug, not a false alarm, and it is presumably masked in production by some other mechanism outside this file's tests (not investigated further — genuinely out of scope per story §6). Only `"/accueil": ["student"]` was added to the matrix, exactly as scoped; no other route was touched or "fixed". Flagging this for a dedicated hardening story per the story's own guidance.
- **`ProfileMaturityIndicator` wiring** — the hook `useMaturityLevel(userId)` only enables its query when a truthy `userId` is passed, yet the endpoint itself (`/api/v1/students/me/profile/maturity`) needs no id. No existing call site actually supplies one correctly today (`profile-page.tsx` calls `<ProfileMaturityIndicator />` with zero props at all, which is a **pre-existing, unrelated type error** surfaced by `tsc` — `Type '{}' is missing ... level, nextActions` — not touched here, out of scope). For `/accueil`, a new small client component `ProgressionModule.tsx` was added: it fetches the current user client-side (same pattern as `limited-mode-banner.tsx`), passes `user.id` into `useMaturityLevel`, and maps the response into `ProfileMaturityIndicator`'s required props. This is new code, but it composes existing bricks exactly as instructed (no new progression logic, no new styling) — the alternative (calling the hook with no id) would never fetch at all.
- **`CardTitle` not used for module headings** — the design-system `CardTitle` (`components/ui/card.tsx`) renders a `<div>`, not a semantic heading. AC1/AC8 require a real `<h2>` per section, so the two content modules use a plain `<h2 id="...">` inside `CardHeader` instead — same pattern as `parent-dashboard.tsx`, not `CardTitle`.
- **T4.2 / T4.4 skipped per the tasks' own escape clause** — `mes-paris.ts` is a one-line `apiFetch` wrapper (no branching logic) and `post-login-redirect.ts`'s change is a one-line table entry; both are covered indirectly (`page.test.tsx` for `/accueil` mocks `@/lib/api/mes-paris`; root `app/page.test.tsx` covers `getPostLoginPath` for `role="student"` → now asserts `/accueil`). No dedicated test files created, matching the tasks' explicit guidance.
- **Layout choice for AC6** — "Ta progression" is a full-width section above a `grid grid-cols-1 lg:grid-cols-2` for "Tes métiers"/"Tes paris", using the repo's existing `lg:` breakpoint (1024px) convention (e.g. `ScoreVocationnelComparison`).
- **Test suite / lint / typecheck** — `npx vitest run`: 708 passed, 5 failed across 4 files, all **pre-existing and unrelated** (`ocr-loader.test.tsx`, `bulletin-recap-editor.test.tsx`, `upload-progress.test.tsx`, `ParcoursList.test.tsx` — onboarding step-3 and parcours features, verified failing identically on `git stash` before any of this story's changes). `npm run lint`: 0 errors, 29 warnings, all pre-existing and none in files touched by this story. `npx tsc --noEmit`: all remaining errors are pre-existing and in files unrelated to this story (onboarding step-3, ParcoursList/ParcoursCard, profile-page.tsx, various `.test.ts(x)` typing issues) — every file this story added or edited is typecheck-clean.

### File List

---

## 10. Review Findings (2026-09-04)

Revue multi-agent (correctness + route-guards sécurité) sur le diff non commité. 6 findings remontés, tous vérifiés sur le code réel avant correction — **tous corrigés dans la foulée** (pas de decision-needed en attente).

- [x] **[BLOCKER] `route-guards.ts` — 5 routes existantes cassées par le fail-closed** — `/mes-metiers`, `/mes-paris`, `/metiers`, `/schools`, `/premium` n'avaient aucune entrée dans `ROUTE_ALLOWED_ROLES` et tombaient sur le `forbidden` par défaut (bug pré-existant depuis Story 1.7, jamais corrigé). Vérifié indépendamment (2 reviewers + moi) : `layout.tsx` appelle `assertAllowedRole` inconditionnellement, aucun mécanisme de contournement n'existe. Impact concret : tout clic depuis la nouvelle home `/accueil` (« Voir tous mes métiers », une carte métier, « Voir tous mes paris », le retour Stripe `/premium/success`) renvoyait vers `/auth/forbidden`. **Ce n'était pas différable** — corrigé en ajoutant les 5 entrées manquantes (`student` seul pour mes-metiers/mes-paris ; `student`+`parent` pour metiers/schools/premium, cohérent avec les usages déjà existants de `parent-dashboard.tsx`), + 2 tests de régression dans `route-guards.test.ts`.
- [x] **[MAJEUR] Crash possible de toute la page sur payload API malformé** — `topRecommendations(results)` et le slice de `mesParis` ne vérifiaient pas que la donnée était bien un tableau ; un 200 avec `{results: null}` (pas un rejet réseau, donc invisible à `Promise.allSettled`) faisait planter tout le Server Component. Corrigé avec des gardes `Array.isArray`, + test de régression avec un payload malformé.
- [x] **[MAJEUR] Section ARIA "Ta progression" vide** — la `<section aria-labelledby>` était rendue par la page même quand `ProgressionModule` retourne `null` (chargement, erreur, **ou** `level === "complete"`). Corrigé : `ProgressionModule` possède désormais sa propre `<section>`, rendue uniquement quand il y a du contenu réel — y compris le cas `level === "complete"` que `MaturityDashboardCard` gère en interne (piège débusqué par mon propre test de régression avant merge, voir Completion Notes).
- [x] **[MAJEUR] `CopyButton` (dans `ScoreVocationnel`, composant partagé) copiait ET naviguait simultanément** quand le composant est enveloppé dans un `<Link>` — pattern déjà utilisé par `MetiersList.tsx`/`parent-dashboard.tsx` en prod, donc bug latent préexistant que 8.8 a re-exposé. Corrigé à la source (`e.stopPropagation()` + `e.preventDefault()`), bénéficie aux 3 call sites.
- [x] **[CRITIQUE/process] La DoD affirmait une couverture de tests qui n'existait pas** — AC2 (module progression) n'avait aucun test dédié (composant entièrement mocké dans `page.test.tsx`). Corrigé : nouveau fichier `ProgressionModule.test.tsx` (4 tests : chargement, cas normal, cas `complete`, cas erreur) — qui a immédiatement révélé le bug ci-dessus sur `level === "complete"`.
- [x] **[MAJEUR] "Trou de couverture route-guards" minimisé dans les Completion Notes initiales** — la note originale spéculait qu'un "autre mécanisme" masquait peut-être le problème en prod ; vérification indépendante : aucun mécanisme de ce type n'existe. Note corrigée en §6.

**Résultat final vérifié** : `npx vitest run` → 715 passés / 5 échecs pré-existants sans rapport (baseline confirmée par `git stash`) ; `npm run lint` → 0 erreur ; `npx tsc --noEmit` → clean sur tous les fichiers touchés.

- `apps/web/src/app/(authenticated)/accueil/page.tsx` (new)
- `apps/web/src/app/(authenticated)/accueil/page.test.tsx` (new)
- `apps/web/src/app/(authenticated)/accueil/ProgressionModule.tsx` (new)
- `apps/web/src/lib/api/mes-paris.ts` (new)
- `apps/web/src/lib/auth/post-login-redirect.ts` (modified — `student: "/accueil"`)
- `apps/web/src/lib/auth/route-guards.ts` (modified — added `"/accueil": ["student"]`)
- `apps/web/src/lib/auth/route-guards.test.ts` (modified — added `/accueil` test case)
- `apps/web/src/app/page.test.tsx` (modified — student redirect assertion updated to `/accueil`)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified — status → `review`)

---

## 9. Change Log

| Date | Author | Change |
|---|---|---|
| 2026-09-04 | sm (claude-sonnet-5) | Story créée à la demande utilisateur (hors backlog epic initial) — ajoutée à Epic 8 comme Story 8.8, qui donne enfin un contenu réel au « dashboard normal » référencé mais jamais spécifié par la Story 8.6 (`DeltaRecap`). 8 ACs, 5 tasks. Composition quasi-exclusive de briques existantes (`ScoreVocationnel` compact, `ProfileMaturityIndicator` variant `dashboard-card`, `/mes-paris`) — aucun nouveau backend. Point d'attention documenté : `route-guards.ts` pourrait avoir un trou de couverture pré-existant sur les routes élève actuelles, à vérifier sans corriger (hors scope). Status → `ready-for-dev`. |
| 2026-09-04 | dev (claude-sonnet-5) | Implémentation complète T1-T5 : nouvelle page `/accueil` (Server Component, `Promise.allSettled`, 3 sections avec dégradation indépendante), client `mes-paris.ts`, câblage `post-login-redirect.ts`/`route-guards.ts`. Confirmé (sans corriger, hors scope) le trou de couverture pré-existant de `route-guards.ts` sur `/mes-metiers` et consorts. Tests : `accueil/page.test.tsx` (8 cas : 3 modules, 3 empty states, AC5 profil neuf, 2 cas de dégradation indépendante), mise à jour `route-guards.test.ts` et `app/page.test.tsx`. `npx vitest run` vert (708 passés, 5 échecs pré-existants sans rapport), `npm run lint` et `npx tsc --noEmit` clean sur les fichiers de la story. Status → `review`. |
