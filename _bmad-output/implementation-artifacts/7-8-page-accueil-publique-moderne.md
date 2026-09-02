# Story 7.8: Page d'accueil publique moderne

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a visiteur non connecté (Sarah, Mehdi, ou un parent) arrivant sur `path-advisor.fr`,
I want une vraie page d'accueil moderne qui explique la proposition de valeur de Path-Advisor et me guide vers l'inscription ou la connexion,
so that je comprenne en quelques secondes ce que fait le produit et sois incité·e à créer un compte (remplace le seed de démo Story 1.2, FR46).

## Acceptance Criteria

1. **Given** un visiteur non connecté **When** il visite `/` **Then** il voit un hero section avec proposition de valeur claire (headline + sous-titre) et deux CTA primaires : "Créer un compte" → `/auth/signup`, "Se connecter" → `/auth/login`. **And** le placeholder de démo Story 1.2 ("Hello Path-Advisor" + showcase design tokens) est retiré du bundle public. *(Révisé en code review du 2026-09-02 : le hero est texte seul pour cette itération — aucun asset d'illustration disponible ; l'ajout d'un visuel est laissé à une itération design future plutôt que de produire un placeholder improvisé.)*
2. **Given** la page d'accueil **When** le visiteur scrolle **Then** il voit au minimum : une section "comment ça marche" (3-4 étapes : profil → recommandations → parcours → suivi), une section mettant en avant les 2 "aha moments" produit (recommandation vocationnelle Epic 3, graphe de parcours + stats admission Epic 4), une section de réassurance (confidentialité RGPD / gratuit pour commencer), et un footer avec lien légal `/legal/rgpd`.
3. **Given** un visiteur avec une session active **When** il visite `/` **Then** il est redirigé server-side vers son espace applicatif (`/mes-metiers` par défaut, ou l'équivalent pertinent pour son rôle) plutôt que de revoir la landing page.
4. **Given** la conformité Core Web Vitals et SEO **When** Google PageSpeed Insights audite `/` sur mobile **Then** LCP < 2,5 s, CLS < 0,1, Performance ≥ 80, SEO ≥ 95. **And** la page expose un `title` + `meta description` dédiés (pas ceux du layout racine générique) via `export const metadata`.
5. **Given** le design system Path-Advisor (tokens R1 Vermillon, Story 1.2) **When** la page est construite **Then** elle réutilise exclusivement les tokens Tailwind (`bg`, `text`, `border`, etc.) et les composants `src/components/ui` (shadcn) existants — aucune couleur/espacement en dur. **And** elle est responsive mobile-first et accessible RGAA AA (un seul `h1`, hiérarchie de titres correcte, contrastes AA, tout CTA atteignable au clavier).

## Tasks / Subtasks

- [x] Task 1 — Redirection des utilisateurs authentifiés (AC: #3)
  - [x] Dans `src/app/page.tsx`, appeler `fetchCurrentUser()` côté Server Component ; si elle résout, `redirect(getPostLoginPath(user.role, user.status))` — **pivot vs plan initial** : `src/lib/auth/route-guards.ts` n'a pas de mapping "route d'accueil par rôle" (c'est un garde d'autorisation, pas un routeur) ; le vrai mapping existant est `src/lib/auth/post-login-redirect.ts` (Story 1.5 §AC8), déjà utilisé par `login-form.tsx`. Réutilisé tel quel plutôt que d'inventer un second mapping qui aurait divergé du comportement post-login réel.
  - [x] Sur `ApiError` 401/403, rendu normal de la landing ; toute autre erreur (5xx, réseau) est logguée et tombe aussi sur la landing plutôt que de propager — seule l'erreur `redirect()` de Next (non-`ApiError`) est re-levée pour laisser son mécanisme de contrôle de flux fonctionner
- [x] Task 2 — Construire les sections de la landing (AC: #1, #2, #5)
  - [x] `src/components/features/homepage/{hero,how-it-works,aha-moments,trust}-section.tsx` créés
  - [x] `hero-section.tsx` : `h1` (unique de la page) + sous-titre + deux `Button asChild` + `next/link` vers `/auth/signup` (default) et `/auth/login` (outline)
  - [x] `how-it-works-section.tsx` : `<ol>` de 4 étapes (profil → recos → parcours → suivi), grille `md:grid-cols-4`
  - [x] `aha-moments-section.tsx` : 2 blocs (recommandation vocationnelle Epic 3 / graphe de parcours + stats admission Epic 4), contenu marketing statique
  - [x] `trust-section.tsx` : réassurance RGPD + gratuit pour commencer + lien `/legal/rgpd`
  - [x] Sections assemblées dans `src/app/page.tsx`
  - [x] Footer inline ajouté dans `page.tsx` (pas de composant footer partagé pré-existant trouvé dans `src/components/` — vérifié, seuls des `CardFooter`/`SheetFooter` UI existent, sans rapport)
- [x] Task 3 — Métadonnées SEO de la page (AC: #4)
  - [x] `export const metadata: Metadata` ajouté dans `page.tsx`, distinct du fallback générique de `layout.tsx`
  - [x] Aucune image ajoutée (pas de visuel lourd introduit dans cette itération — contenu texte uniquement) ; pas de nouvelle dépendance
- [x] Task 4 — Nettoyage du seed de démo (AC: #1)
  - [x] Placeholder "Hello Path-Advisor" + showcase tokens retiré de `page.tsx`
  - [x] `page.test.tsx` réécrit entièrement (les anciennes assertions sur "Hello Path-Advisor" n'existent plus)
- [x] Task 5 — Tests (AC: #1, #2, #3, #5)
  - [x] `page.test.tsx` : redirection student/parent/path_admin (mock `getPostLoginPath` via le vrai module, assert sur `MVP_FALLBACK_PATH` / `/admin/`), rendu landing sur 401/403, non-crash sur 5xx, présence du footer légal
  - [x] Un test de rendu par sous-composant (CTA + `href`, titres, nombre d'étapes)
  - [x] Pas de `jest-axe` dans le repo (vérifié — aucune occurrence) ; accessibilité couverte par la structure sémantique (`<ol>`, un seul `h1`, `aria-labelledby` par section) plutôt qu'un test automatisé dédié — pas de nouvelle dépendance ajoutée pour une story qui n'en demandait pas explicitement

### Review Findings

- [x] [Review][Decision] **Résolu — option "construire maintenant".** `src/lib/auth/post-login-redirect.ts` mis à jour : `student → /mes-metiers` (Epic 3, existe et livré) et `parent → /parent` (Epic 6/Story 6.2, existe et livré) remplacent le fallback générique — la table était juste restée non mise à jour depuis que ces epics ont livré. `counselor`/`school_admin`/`support` restent sur `/parametres/confidentialite` (dashboards réellement pas construits, Epic 6/9 backlog). AC3 est maintenant littéralement vraie sans modification de son texte. Bénéfice bonus : corrige aussi le vrai flux de login (`login-form.tsx` consomme la même table). [apps/web/src/lib/auth/post-login-redirect.ts]
- [x] [Review][Decision] **Résolu — option "livrer tel quel".** AC1 réécrite pour retirer l'exigence d'illustration (pas d'asset disponible ; un placeholder improvisé aurait ajouté de la dette visuelle sans direction artistique). Hero reste texte seul pour cette itération. [apps/web/src/components/features/homepage/hero-section.tsx]
- [x] [Review][Patch] Toute erreur non-`ApiError` levée par `fetchCurrentUser`/`getPostLoginPath` (timeout réseau, `AbortError`, `user` malformé) est re-levée et crashe la page publique — contredit l'intention documentée ("must NOT break this page") [apps/web/src/app/page.tsx:244-259] — **Corrigé** : remplacement du test `instanceof ApiError` par `unstable_rethrow(cause)` (API Next 16 dédiée à ce pattern exact : rethrow des erreurs de contrôle de flux `redirect`/`notFound`, no-op sur tout le reste), puis fallback générique "log + rendu landing" pour tout le reste. 3 tests de régression ajoutés (timeout `DOMException`, `fetchCurrentUser` résolvant `null`, plus les cas 401/403/500 déjà couverts).
- [x] [Review][Patch] Open Graph de base manquant dans `metadata` alors que l'epic (Story 7.8, texte source) le demande explicitement dès cette story (génération complète différée à 7.5, mais `og:title`/`og:description` de base attendus maintenant) [apps/web/src/app/page.tsx:219-223] — **Corrigé** : `openGraph: { title, description, type: "website" }` ajouté (pas d'image dynamique — différé à Story 7.5).
- [x] [Review][Patch] `key={moment.title}` / `key={step.title}` utilisent un texte marketing traduisible comme clé React — fragile si la copie change [apps/web/src/components/features/homepage/aha-moments-section.tsx, how-it-works-section.tsx] — **Corrigé** : ajout d'un champ `id` stable (slug) sur chaque entrée, utilisé comme clé à la place du `title`.
- [x] [Review][Patch] `console.error` journalise l'objet `ApiError` complet (incluant `.problem`) plutôt qu'un résumé minimal (`status`/`message`) [apps/web/src/app/page.tsx:252] — **Corrigé** : log réduit à `{ status, message }`.
- [x] [Review][Patch] Completion Notes affirment "Toutes les ACs satisfaites" de façon trop catégorique au vu des écarts ci-dessus — à corriger une fois les decisions tranchées — **Corrigé** : voir Completion Notes mises à jour ci-dessous, wording aligné avec les décisions effectivement tranchées en review.
- [x] [Review][Defer] Audit chiffré Core Web Vitals (AC4 : LCP/CLS/Performance/SEO) non exécuté — nécessite build de prod + Lighthouse CI, dépendance déjà documentée vers Story 7.6 — deferred, pre-existing (dépendance d'infra pas encore livrée)
- [x] [Review][Defer] Copie marketing en dur (pas d'extraction i18n) — Story 7.7 (i18n foundation) est backlog ; prématuré de l'exiger ici — deferred, pre-existing (scope explicitement post-MVP)
- [x] [Review][Defer] `vi.mock("next/navigation")` remplace tout le module au lieu de ne mocker que `redirect` — piège de maintenance pour un futur contributeur qui utiliserait `useRouter`/`usePathname` dans ce fichier — deferred, pre-existing (pattern déjà utilisé ailleurs dans le repo)
- [x] [Review][Defer] Pas de `robots`/`alternates.canonical` dans `metadata` — relève du scope Story 7.4 (sitemap/robots) — deferred, pre-existing (story dédiée déjà planifiée)
- [x] [Review][Defer] Lien footer "Mentions légales & RGPD" potentiellement dupliqué à l'identique sur d'autres pages (ambiguïté pour un lecteur d'écran naviguant par nom de lien) — pattern pré-existant dans l'app, pas introduit spécifiquement de façon aggravante par cette story — deferred, pre-existing

## Dev Notes

- **Contexte** : `src/app/page.tsx` est aujourd'hui un placeholder de démonstration des design tokens (Story 1.2), pas une vraie landing page. Cette story le remplace par une page marketing/produit réelle. Elle est rattachée à l'Epic 7 (Découverte publique & SEO) car c'est la porte d'entrée publique du produit, mais elle ne dépend PAS des autres stories de l'Epic 7 (SSR fiches métier, sitemap, i18n) — elle peut être livrée indépendamment.
- **Redirection des connectés** : suivre le même pattern que `src/app/(authenticated)/layout.tsx` (`fetchCurrentUser()` + catch `ApiError` 401/403), mais en beaucoup plus permissif : ici toute erreur non-auth doit laisser passer le rendu public plutôt que throw, car `/` doit rester joignable même si l'API a un problème transitoire.
- **Route group** : `page.tsx` est actuellement à la racine de `src/app/`, hors de `(public)` ou `(authenticated)`. Garder cet emplacement (c'est la route `/` elle-même) — ne pas la déplacer dans `(public)/` sauf si l'architecture Next.js l'exige (vérifier que `(public)` n'a pas déjà un `layout.tsx` qui s'appliquerait involontairement).
- **Design tokens** : classes Tailwind déjà en usage dans le seed actuel (`bg-bg`, `bg-bg-2`, `text-text`, `text-text-muted`, `text-h1`, `text-h1-desktop`, `border-border`, etc.) — s'y référer plutôt que d'inventer de nouvelles classes. Composants `Button` (`src/components/ui/button`) supportent au moins les variants `default`, `outline`, `secondary` (vus dans le seed).
- **Pas de nouvelle dépendance** sans vérification : le repo a `next/image`, `next/link`, `next/font/google` (Inter) déjà en place via `layout.tsx`. Pas besoin d'une librairie d'icônes si elle n'est pas déjà installée — vérifier `package.json` avant d'ajouter `lucide-react` ou équivalent (il est probable que shadcn l'ait déjà installé, mais à confirmer).
- **Contenu marketing** : les textes (headline, description des étapes, etc.) sont à rédiger par le développeur en français, ton direct et rassurant, cohérent avec le persona Sarah/Mehdi/parent du PRD. Pas de contenu factice ("Lorem ipsum") en prod.

### Project Structure Notes

- Nouveau dossier `src/components/features/homepage/` — cohérent avec la convention existante `src/components/features/*` (ex: `src/components/features/auth/` vu dans `(authenticated)/layout.tsx`).
- `src/app/page.tsx` modifié (pas déplacé) — c'est un fichier existant (UPDATE, pas NEW). Le lire intégralement avant modification (déjà fait durant le cadrage de cette story — voir extrait ci-dessus) : il exporte uniquement un composant par défaut, pas de `metadata` local aujourd'hui, donc l'ajout de `export const metadata` est une extension propre sans conflit.
- `src/app/page.test.tsx` existe déjà et couvre probablement le contenu placeholder — à mettre à jour, pas à ignorer (sinon CI rouge).
- Aucun `middleware.ts` de garde d'auth pour les routes publiques (le `middleware.ts` racine ne fait qu'injecter `x-pathname`) — la garde "rediriger si connecté" doit donc être implémentée directement dans `page.tsx`, pas dans le middleware.

### References

- [Source: apps/web/src/app/page.tsx] — contenu placeholder actuel à remplacer
- [Source: apps/web/src/app/(authenticated)/layout.tsx] — pattern de référence pour `fetchCurrentUser()` + gestion `ApiError`
- [Source: apps/web/middleware.ts] — confirme l'absence de garde d'auth au niveau middleware
- [Source: _bmad-output/planning-artifacts/epics/epic-7-decouverte-publique-seo.md#Story 7.8] — story source (ajoutée dans le cadre de cette création)
- [Source: _bmad-output/planning-artifacts/epics/epic-1-foundation-auth-multi-role-rbac-conformite-rgpd-infra-technique.md] — Story 1.2 (design tokens, origine du seed à remplacer)

## Dev Agent Record

### Agent Model Used

claude-sonnet-5

### Debug Log References

### Completion Notes List

- Story créée via `bmad-create-story` à la demande directe de l'utilisateur (pas de backlog sprint pré-existant pour cette story — Epic 7 et son fichier `epics/epic-7-*.md` mis à jour avec la nouvelle Story 7.8 avant création du fichier story).
- Implémentation via `bmad-dev-story`, puis `bmad-code-review` (3 couches : Blind Hunter, Edge Case Hunter, Acceptance Auditor) avec 2 décisions tranchées par l'utilisateur et 5 patches appliqués. État final :
  - AC1 : hero + CTA livrés ; l'exigence d'illustration a été retirée du texte de l'AC en review (pas d'asset disponible, cf. décision ci-dessus) — satisfaite telle que révisée.
  - AC2/AC5 : landing composée de 4 sections (hero, comment-ça-marche, aha-moments, réassurance) + footer légal, 100 % tokens/composants existants, seed Story 1.2 retiré. Accessibilité assurée par la sémantique native (`<ol>`, un seul `h1`, `aria-labelledby`, éléments focusables natifs) plutôt que par un test automatisé dédié — pas de `jest-axe` dans le repo.
  - AC3 : `src/lib/auth/post-login-redirect.ts` mis à jour en review pour pointer `student → /mes-metiers` et `parent → /parent` (routes réellement livrées, Epics 3/6) au lieu du fallback générique périmé — AC3 est maintenant littéralement exacte, sans avoir eu besoin de la réécrire. Effet de bord positif : corrige aussi le vrai flux de post-login (`login-form.tsx`).
  - AC4 : `metadata` avec title + description + Open Graph de base. L'audit chiffré Core Web Vitals (LCP/CLS/Performance/SEO) reste explicitement différé — dépend d'un build de prod + Lighthouse CI (Story 7.6, pas encore livrée).
  - Tests : 14 tests sur `page.tsx`/sections, dont 3 tests de régression ajoutés en review (timeout réseau, payload `fetchCurrentUser` malformé) prouvant la correction du bug critique trouvé en review (voir Review Findings). Suite complète : 704 tests, 5 échecs pré-existants et sans rapport confirmés par `git stash` avant toute modification — 0 régression.
  - Lint (`npm run lint`) : 0 erreur. `tsc --noEmit` : 0 erreur dans les fichiers touchés.
- **Écart vs plan initial** : le fichier `src/lib/auth/home-route.ts` envisagé dans les Dev Notes n'a pas été créé — `src/lib/auth/post-login-redirect.ts` (`getPostLoginPath`) fournissait déjà ce mapping et est la source de vérité du login (Story 1.5) ; il a été mis à jour en review au lieu d'être dupliqué.
- **Bug corrigé en review** : la garde de redirection re-levait toute erreur non-`ApiError` (timeout, payload malformé), ce qui aurait crashé la page publique. Remplacé par `unstable_rethrow()` (Next 16) — voir Review Findings.

### File List

- `_bmad-output/planning-artifacts/epics/epic-7-decouverte-publique-seo.md` (ajout Story 7.8)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (ajout `7-8-page-accueil-publique-moderne`, epic-7 → in-progress)
- `_bmad-output/implementation-artifacts/7-8-page-accueil-publique-moderne.md` (ce fichier)
- `apps/web/src/app/page.tsx` (réécrit — landing publique + garde de redirection)
- `apps/web/src/app/page.test.tsx` (réécrit)
- `apps/web/src/components/features/homepage/hero-section.tsx` (nouveau)
- `apps/web/src/components/features/homepage/hero-section.test.tsx` (nouveau)
- `apps/web/src/components/features/homepage/how-it-works-section.tsx` (nouveau)
- `apps/web/src/components/features/homepage/how-it-works-section.test.tsx` (nouveau)
- `apps/web/src/components/features/homepage/aha-moments-section.tsx` (nouveau)
- `apps/web/src/components/features/homepage/aha-moments-section.test.tsx` (nouveau)
- `apps/web/src/components/features/homepage/trust-section.tsx` (nouveau)
- `apps/web/src/components/features/homepage/trust-section.test.tsx` (nouveau)
- `apps/web/src/lib/auth/post-login-redirect.ts` (modifié en review — `student`/`parent` pointent vers leurs vraies routes existantes)
- `_bmad-output/implementation-artifacts/deferred-work.md` (ajout section "Deferred from: code review of story-7-8")

## Change Log

- 2026-09-02 — Story créée (Epic 7 + sprint-status mis à jour) puis implémentée intégralement (dev-story) : nouvelle landing publique remplaçant le seed Story 1.2, redirection role-based des connectés, 11 tests ajoutés, 0 régression. Status → review.
- 2026-09-02 — Code review (3 couches adversariales) : 2 décisions tranchées (redirection par rôle construite pour de vrai via `post-login-redirect.ts` ; AC1 ajustée pour un hero texte seul), 5 patches appliqués (bug de crash sur erreur réseau/payload malformé corrigé via `unstable_rethrow`, Open Graph ajouté, clés React stabilisées, log simplifié, wording Completion Notes aligné), 5 items différés (documentés dans `deferred-work.md`), 0 items dismiss restants après application. 14 tests, 0 régression. Status → done.
