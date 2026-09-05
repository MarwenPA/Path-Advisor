# Story 1.15: Navigation globale multi-rôle — sidebar desktop, tab bar mobile, déconnexion

**Epic:** 1 — Foundation : Auth multi-rôle, RBAC, Conformité RGPD, Infra technique
**Status:** done
**Sprint:** Epic 1 (hardening post-MVP — réouverture ciblée)
**Story Key:** `1-15-navigation-globale-multi-role`
**Estimation:** M (medium) — composants neufs mais simples (pas de nouvel état serveur), le risque est le câblage transverse dans `(authenticated)/layout.tsx`, partagé par TOUS les rôles.

> **Pourquoi cette story existe** : `UX-DR31` (navigation responsive) est référencé dans Epic 1 depuis le PRD initial mais n'a jamais été implémenté. Constaté en session live (2026-09-04) : un utilisateur qui se connecte atterrit sur `/accueil` (Story 8.8) et ne peut plus RIEN faire d'autre que cliquer les 1-2 liens contenus dans les cartes de la page — aucune nav persistante, aucun moyen de se déconnecter, aucun accès à `/parametres` sans taper l'URL à la main. `logoutUser()` existe dans `apps/web/src/lib/api/auth.ts` depuis la Story 1.5 mais n'est appelé par **aucun** composant du repo (vérifié par grep). Design détaillé dans l'addendum "Navigation Multi-Rôle (2026-09)" de `_bmad-output/planning-artifacts/ux-design-specification.md` (section Navigation Patterns) — **lire cet addendum avant de coder**, il contient le mapping rôle → items et le raisonnement Revolut/N26 (chrome minimal, compte toujours au même endroit, items = ce que CE compte peut faire).

---

## 1. User Story

**As an** utilisateur authentifié (élève, parent, conseillère, école, admin, support),
**I want** une navigation persistante qui me montre les sections que mon rôle peut utiliser et me permette de me déconnecter,
**So that** je peux circuler dans l'application sans connaître les URL par cœur, et quitter mon compte proprement sur un poste partagé.

**Business value:** Débloquant transverse — sans ça, `/accueil` (Story 8.8) et toutes les pages authentifiées sont des culs-de-sac. Risque produit direct : un utilisateur qui ne trouve pas comment se déconnecter sur un ordinateur partagé (CDI, cyber-base) est un vrai problème RGPD/confiance, pas juste une gêne UX.

---

## 2. Scope decisions (lire avant les ACs)

- **Deux nouveaux composants, pas un seul "Navbar" générique** :
  - `apps/web/src/components/features/navigation/desktop-sidebar.tsx` — sidebar fixe gauche, ≥ `lg` (1024px, cohérent avec les breakpoints Tailwind déjà déclarés dans le design system).
  - `apps/web/src/components/features/navigation/mobile-nav.tsx` — soit une bottom tab bar (rôles à ≥ 2 items métier), soit un header sticky minimal avec juste le menu compte (rôles à 1 item ou 0 item métier). Voir §Mapping ci-dessous pour qui a droit à quoi.
  - Un composant partagé `apps/web/src/components/features/navigation/account-menu.tsx` (email + Paramètres + Déconnexion) utilisé par les deux — **pas de duplication de la logique de déconnexion**.
- **Registre `NAV_ITEMS` — séparé de `ROUTE_ALLOWED_ROLES`, jamais dérivé de lui** : nouveau fichier `apps/web/src/lib/auth/nav-items.ts`. C'est la leçon centrale de l'addendum UX : `ROUTE_ALLOWED_ROLES` (guard serveur, `route-guards.ts`) dit "qui a le DROIT de voir cette route" ; `NAV_ITEMS` dit "quelle route est assez avancée pour être montrée dans le menu". Aujourd'hui `/cohorte`, `/ecole`, `/support` sont déjà dans `ROUTE_ALLOWED_ROLES` (déclarées par avance, pages pas livrées) — si `NAV_ITEMS` était calculé depuis `ROUTE_ALLOWED_ROLES`, la nav afficherait des liens vers des pages inexistantes → 404. **Au lancement de cette story, seuls `student` et `parent` ont des items métier réels ; les autres rôles n'ont que "Paramètres" + le menu compte** (voir tableau exact plus bas). Ne PAS créer de placeholder pages pour `/cohorte`/`/ecole`/`/support` dans cette story — hors scope, une story dédiée les ajoutera à `NAV_ITEMS` en même temps que la page.
- **`path_admin`** : le lien "Admin" pointe vers `/admin/` (Django, cookie de session séparé — cf. `post-login-redirect.ts` déjà en place) avec `target="_blank" rel="noopener noreferrer"`. Ce n'est PAS une route Next, ne pas essayer de la faire matcher par `assertAllowedRole`.
- **`(authenticated)/layout.tsx`** : aujourd'hui rend `<MfaBanner /><LimitedModeBanner />{children}` dans un simple `<div>`. Cette story restructure en layout à 2 zones (sidebar + zone de contenu sur desktop ; header + contenu + tab bar sur mobile), **sans** changer la logique des 2 guards existants (auth guard, role guard) ni des deux banners — ils restent rendus, juste repositionnés dans la nouvelle structure (les banners vont dans la zone de contenu, au-dessus de `{children}`, pas dans la nav).
- **Logo → destination** : le logo dans la sidebar/header pointe vers `getPostLoginPath(role, status)` (déjà exporté par `post-login-redirect.ts`), jamais vers `/` — un utilisateur connecté ne doit jamais revoir la landing publique (cohérent avec le comportement déjà en place sur `/` elle-même, Story 7.8).
- **Pas de nouvelle dépendance npm** : pas de `@radix-ui/react-dropdown-menu` ni `@radix-ui/react-popover` (absents du repo à ce jour) — construire `account-menu.tsx` à la main avec `useState` + un `useEffect` de click-outside + gestion clavier (Échap ferme, focus trap simple). Le pattern est trivial (un seul menu, 2 items) et évite d'alourdir le bundle pour ça.
- **Icônes** : `lucide-react` (déjà une dépendance). Suggestions : `Home`, `Briefcase` (Mes métiers), `GraduationCap` (Mes paris), `Sparkles` (Premium), `Settings`, `LogOut`, `ChevronDown`, `Users` (Cohorte/École placeholders futurs — pas utilisées dans cette story).
- **Tests** : chaque nouveau composant a son fichier `.test.tsx` (Vitest + Testing Library, pattern déjà utilisé partout dans `src/components/features/`). `route-guards.test.ts` n'est pas modifié par cette story (aucun changement à `ROUTE_ALLOWED_ROLES`).

### Mapping rôle → `NAV_ITEMS` (source unique, copier tel quel dans `nav-items.ts`)

| Rôle | Items | Bottom tab bar mobile ? |
|---|---|---|
| `student` | Accueil (`/accueil`, `Home`) · Mes métiers (`/mes-metiers`, `Briefcase`) · Mes paris (`/mes-paris`, `GraduationCap`) · Premium (`/premium`, `Sparkles`) | Oui (4 items + compte = 5, à la limite fixée par le design system) |
| `parent` | Tableau de bord (`/parent`, `Home`) | Non — header sticky + menu compte |
| `counselor` | *(aucun item métier — `/cohorte` pas livrée)* | Non |
| `school_admin` | *(aucun item métier — `/ecole` pas livrée)* | Non |
| `support` | *(aucun item métier — `/support` pas livrée)* | Non |
| `path_admin` | Admin (`/admin/`, externe, `target="_blank"`) | Non |

`Paramètres` n'est PAS dans `NAV_ITEMS` — c'est un item du menu compte (`account-menu.tsx`), pas de la nav principale, pour tous les rôles (cohérent avec l'addendum : "Paramètres" vit à côté de "Déconnexion", pas dans la sidebar).

---

## 3. Acceptance Criteria (BDD)

### AC1 — Sidebar desktop visible et fonctionnelle (`≥ lg`)

**Given** je suis un élève authentifié sur un viewport ≥ 1024px
**When** je charge n'importe quelle page sous `(authenticated)`
**Then** une sidebar fixe à gauche (224px) affiche : le logo (lien vers `/accueil`), les items de `NAV_ITEMS["student"]` avec icône + label, l'item correspondant à la page courante marqué visuellement actif (fond `bg-muted` + trait `bg-primary` 2px à gauche) et `aria-current="page"`, et en bas un bloc compte (initiale de l'email dans un cercle `bg-primary`, email tronqué).

### AC2 — Menu compte : Paramètres + Déconnexion

**Given** je suis authentifié et je clique sur le bloc compte (sidebar desktop ou icône compte mobile)
**When** le menu s'ouvre
**Then** il affiche mon email (lecture seule), un lien "Paramètres" vers `/parametres/confidentialite`, et un bouton "Déconnexion". Le menu se ferme au clic extérieur, à la touche Échap, ou après sélection d'une action. Le focus revient sur le bouton déclencheur à la fermeture (RGAA).

### AC3 — Déconnexion effective

**Given** le menu compte est ouvert
**When** je clique "Déconnexion"
**Then** `logoutUser()` est appelé, puis je suis redirigé vers `/auth/login` ; toute tentative de revisiter une page `(authenticated)` après ce point déclenche le guard d'auth existant (`redirect-login`, comportement déjà en place, non modifié par cette story). Un échec réseau sur `logoutUser()` ne bloque pas la redirection (mieux vaut un utilisateur qui se croit déconnecté côté client, avec un cookie de session qui expirera de toute façon, qu'un bouton qui semble ne rien faire).

### AC4 — Tab bar mobile pour les rôles à ≥ 2 items (`< lg`)

**Given** je suis un élève authentifié sur un viewport < 1024px
**When** je charge une page authentifiée
**Then** une bottom tab bar fixe affiche les 4 items de `NAV_ITEMS["student"]` + une icône compte (5 au total), touch targets ≥ 44×44px, item actif marqué par icône remplie + `color-brand` + `aria-current="page"`. Aucune sidebar n'est visible à cette largeur.

### AC5 — Header minimal mobile pour les rôles à 0-1 item

**Given** je suis un parent authentifié sur un viewport < 1024px
**When** je charge `/parent`
**Then** pas de bottom tab bar (un seul item métier ne justifie pas 2 icônes) ; à la place, un header sticky en haut affiche le nom de la section courante à gauche et l'icône compte à droite (ouvre le même `account-menu.tsx` qu'ailleurs).

### AC6 — Rôles sans item métier livré (`counselor`, `school_admin`, `support`)

**Given** un utilisateur `counselor` (ou `school_admin`/`support`) authentifié
**When** il charge une page qu'il a le droit de voir (ex. `/parametres`)
**Then** la nav (desktop ET mobile) n'affiche aucun item métier vide/cassé — uniquement le logo (lien vers `getPostLoginPath`, ici `MVP_FALLBACK_PATH` = `/parametres/confidentialite`) et le bloc/icône compte. Pas de section "Cohorte"/"École"/"Support" visible tant que `NAV_ITEMS` n'a pas été étendu par la story qui livrera cette page.

### AC7 — `path_admin` : lien externe, pas de route Next

**Given** un utilisateur `path_admin` authentifié
**When** il regarde la sidebar/nav
**Then** il voit un item "Admin" qui ouvre `/admin/` dans un nouvel onglet (`target="_blank" rel="noopener noreferrer"`), et un item "Paramètres" + compte comme les autres rôles. Cliquer "Admin" ne déclenche AUCUNE navigation côté Next (pas de `<Link>`, un `<a>` simple).

### AC8 — Bannières existantes préservées

**Given** un élève avec `status = pending_parental_consent` (mode limité) ou un staff MFA non enrôlé
**When** il charge une page authentifiée après cette story
**Then** `LimitedModeBanner` / `MfaBanner` s'affichent exactement comme avant (même position relative : au-dessus du contenu de page, sous le header/dans la zone de contenu — pas dans la sidebar/tab bar). Aucune régression sur leur logique d'affichage (non touchée par cette story).

### AC9 — Accessibilité clavier

**Given** j'utilise seulement le clavier
**When** je navigue dans la sidebar/tab bar et le menu compte
**Then** chaque item de nav est atteignable au Tab dans l'ordre visuel, le menu compte s'ouvre à Entrée/Espace sur le bouton déclencheur, se ferme à Échap en rendant le focus au déclencheur, et `<nav aria-label="Navigation principale">` englobe les items de nav (sidebar ET tab bar).

---

## 4. Dev Notes

### 4.1 Fichiers à créer

- `apps/web/src/lib/auth/nav-items.ts` — `NAV_ITEMS: Record<UserRole, NavItem[]>` + type `NavItem = { href: string; label: string; icon: LucideIcon } | { href: string; label: string; icon: LucideIcon; external: true }`. Exporte aussi `hasBottomTabBar(role): boolean` (vrai ssi `NAV_ITEMS[role].length >= 2`, cf. tableau §2).
- `apps/web/src/components/features/navigation/account-menu.tsx` — bouton déclencheur (avatar/initiale + chevron) + menu (email, Paramètres, Déconnexion). Prend `email: string` en prop ; appelle `logoutUser()` + `router.push("/auth/login")` (via `useRouter` de `next/navigation`, Client Component — `"use client"`).
- `apps/web/src/components/features/navigation/desktop-sidebar.tsx` — Server OU Client Component selon si `usePathname()` est nécessaire pour l'état actif (probablement Client, comme `account-menu.tsx` qu'il contient). Prend `role: UserRole`, `email: string` en props (pas de fetch interne — le layout parent a déjà `fetchCurrentUser()`).
- `apps/web/src/components/features/navigation/mobile-nav.tsx` — bottom tab bar OU header selon `hasBottomTabBar(role)`. Mêmes props.
- Fichiers `.test.tsx` associés à chacun des 3 composants ci-dessus.

### 4.2 Fichier à modifier

- `apps/web/src/app/(authenticated)/layout.tsx` — actuellement :
  ```tsx
  return (
    <div className="flex min-h-screen flex-col bg-bg">
      <MfaBanner />
      <LimitedModeBanner />
      {children}
    </div>
  );
  ```
  Devient (schéma, adapter aux classes Tailwind réelles du repo — vérifier `tokens.css`/`tailwind.config.ts` pour les noms exacts de couleurs, ne pas inventer des classes `bg-bg`/`bg-card` qui n'existent pas) :
  ```tsx
  return (
    <div className="flex min-h-screen bg-bg">
      <DesktopSidebar role={role} email={user.email} />
      <div className="flex min-h-screen flex-1 flex-col">
        <MobileNav role={role} email={user.email} />
        <MfaBanner />
        <LimitedModeBanner />
        <main className="flex-1 pb-16 lg:pb-0">{children}</main>
      </div>
    </div>
  );
  ```
  Le `role` et `user` sont déjà résolus dans ce fichier via `fetchCurrentUser()` (variable `user`/`role` existante, voir le code actuel) — pas de fetch supplémentaire. `pb-16 lg:pb-0` réserve l'espace pour la bottom tab bar fixe sur mobile (adapter la valeur à la hauteur réelle du composant une fois codé).

### 4.3 Ce qui NE change PAS

- `route-guards.ts` / `ROUTE_ALLOWED_ROLES` — intact.
- `post-login-redirect.ts` — intact (`getPostLoginPath` est réutilisé, pas modifié).
- Les 2 guards (auth, role) dans `layout.tsx` — logique intacte, seul le JSX de retour change.
- Aucune page/route existante ne change de comportement.

### 4.4 Référence design

Lire `_bmad-output/planning-artifacts/ux-design-specification.md`, section "Navigation Patterns" → addendum "Navigation Multi-Rôle (2026-09)" avant de commencer — il contient le raisonnement complet (pourquoi Revolut/N26, pourquoi `NAV_ITEMS` ≠ `ROUTE_ALLOWED_ROLES`, tokens couleur à réutiliser).

---

## 5. Tasks

- [x] T1 — Créer `nav-items.ts` avec le mapping exact du tableau §2 + `hasBottomTabBar()`.
- [x] T2 — Créer `account-menu.tsx` (trigger + menu + click-outside + Échap + focus-return) avec tests.
- [x] T3 — Créer `desktop-sidebar.tsx` avec tests (item actif via `usePathname()`, lien logo, rendu conditionnel `path_admin` externe).
- [x] T4 — Créer `mobile-nav.tsx` avec tests (bottom tab bar vs header selon rôle).
- [x] T5 — Modifier `(authenticated)/layout.tsx` pour composer les deux + garder les banners existants. Pas de test de layout dédié ajouté — aucun autre layout serveur du repo n'en a (convention existante : mocker `headers()`/`fetchCurrentUser()`/`redirect()` d'un Server Component async est peu rentable ici), la couverture vient des 3 composants de nav + de la vérification manuelle T6.
- [x] T6 — Vérifié manuellement en Docker (`pa-web`/`pa-api` locaux) : `student` (`/accueil`) affiche la sidebar + les 4 items + `Path Advisor` ; `parent` (`/parent`) affiche le header sticky "Tableau de bord" sans tab bar ; `path_admin` non vérifiable en live (exige l'enrôlement MFA, Story 1.6, hors scope de cette story) — couvert à la place par le test unitaire `desktop-sidebar.test.tsx` (lien externe `/admin/`, `target="_blank"`, `rel="noopener noreferrer"`).
- [x] T7 — `npx vitest run` → 741 passed / 5 failed (les 5 échecs sont pré-existants, dans `onboarding/step-3` et `ParcoursList`, sans rapport avec cette story — confirmés avant/après). `npx eslint` clean sur les fichiers touchés. `npx tsc --noEmit` : zéro erreur sur les fichiers touchés/créés (le repo a des erreurs TS pré-existantes ailleurs, dans `onboarding`/e2e, non liées à cette story).
- [x] T8 — Story + `sprint-status.yaml` mis à jour (`1-15-navigation-globale-multi-role: review`).

---

## 6. Out of scope (explicitement)

- Pages `/cohorte`, `/ecole`, `/support` — pas créées ici ; `NAV_ITEMS` reste vide pour ces rôles jusqu'à ce qu'elles existent.
- Search `⌘K` (mentionné dans la section Navigation Patterns originale) — story séparée, pas un prérequis de la nav de base.
- Breadcrumb — uniquement pertinent sur les fiches profondes (métier/école), aucune page actuelle n'en a besoin ; à ajouter quand une telle page existera.
- Dark mode — hors scope produit MVP (cf. Visual Design Foundation : "mode clair uniquement en MVP").
- Notifications (cloche) — Epic 8 backlog, pas de route/données à afficher aujourd'hui.

---

## 7. Review Findings

**Bug bloquant découvert en session live, sans rapport avec le contenu de la nav elle-même** : cette version de Next.js (16.2.x) a renommé la convention `middleware.ts`/`middleware()` en `proxy.ts`/`proxy()`, ET exige que ce fichier vive **au même niveau que `app/`** (donc `apps/web/src/proxy.ts`, pas `apps/web/proxy.ts` à la racine du package, même si `app/` est dans `src/`). Sans ça, le header `x-pathname` que `(authenticated)/layout.tsx` lit pour son guard de rôle n'était jamais injecté → fallback silencieux sur `/`, qui ne correspond à aucune règle de `ROUTE_ALLOWED_ROLES` → **403 systématique sur toute page authentifiée**, y compris juste après un login réussi. Un agent concurrent avait déjà créé `apps/web/proxy.ts` (bon nom, mauvais emplacement) lors d'un merge antérieur — corrigé ici en le déplaçant vers `apps/web/src/proxy.ts` et en supprimant l'ancien `middleware.ts` mort. Confirmé par instrumentation (log ajouté puis retiré) : zéro invocation tant que le fichier était au mauvais endroit, invoqué à chaque requête une fois déplacé.

Revue adversariale menée par un second agent (2026-09-04) sur les 9 fichiers de la story. 7 findings réels remontés, tous corrigés et re-vérifiés (tests + lint + tsc + smoke test Docker) :

| # | Sévérité | Constat | Fix |
|---|---|---|---|
| 1 | HIGH | Le logo de `path_admin` était un `<Link>` Next vers `/admin/` (pas une route Next → 404 client-side), alors que l'item de nav lui-même gérait déjà le cas externe. Contredisait directement AC7. | `desktop-sidebar.tsx` : `homeIsExternal = homeHref.startsWith("/admin")` → rend un `<a target="_blank">` dans ce cas, comme pour l'item de nav. Test ajouté. |
| 2 | HIGH | Le menu compte en variante `compact` s'ouvrait toujours vers le bas (`top-full`) — dans la bottom tab bar (`fixed bottom-0`), le popover s'ouvrait donc sous le viewport, inatteignable. Déconnexion cassée pour `student` sur mobile (AC2/AC4). | Nouvelle prop `placement: "up" \| "down"` sur `AccountMenu`. `desktop-sidebar` (déjà en bas) et la tab-bar mobile passent `"up"` ; le header sticky mobile passe `"down"`. Tests de placement ajoutés (assertion de classe `bottom-full`/`top-full`). |
| 3 | MEDIUM | `handleLogout` utilisait `router.push` — le Router Cache App Router pouvait re-render le shell authentifié depuis le cache au bouton Retour après déconnexion, exactement le risque "session qui traîne sur poste partagé" qu'AC3 veut éviter. | `router.replace("/auth/login")` + `router.refresh()`. Test mis à jour pour vérifier les deux appels. |
| 4 | MEDIUM | La branche "header sticky" (rôles à < 2 items) ne rendait QUE l'icône compte — l'unique item métier du rôle (`/parent`, `/admin/` pour `path_admin`) n'était accessible que via une re-saisie d'URL une fois qu'on avait navigué ailleurs (ex. `/parametres`). Contredisait la prémisse même de la story pour ces rôles. | `mobile-nav.tsx` : la branche header rend maintenant les items du rôle (icône + `aria-label`, external-aware) à côté du titre, avant l'icône compte. Tests ajoutés (`parent`, `path_admin`). |
| 5 | LOW-MEDIUM | `pb-16` (espace pour la tab bar) appliqué inconditionnellement dans `layout.tsx`, même pour les rôles sans tab bar — 64px d'espace mort en bas sur mobile pour `parent`/`counselor`/`school_admin`/`support`/`path_admin`. | `cn("flex-1", hasBottomTabBar(safeRole) && "pb-16 lg:pb-0")` — `hasBottomTabBar` est une fonction pure, importable sans risque dans le Server Component. |
| 6 | LOW-MEDIUM | Le popover portait `role="menu"`/`role="menuitem"` sans en implémenter le contrat clavier (flèches, Home/End, roving tabindex, focus-on-open) — contrat ARIA annoncé et non tenu, pire pour un lecteur d'écran qu'un simple disclosure. | Rôles ARIA `menu`/`menuitem` retirés ; popover devenu un simple conteneur (`data-testid` pour les tests) avec des `<Link>`/`<button>` normaux + `aria-expanded` sur le déclencheur — Tab atteint déjà tout dans l'ordre. Tests adaptés (`getByRole("link"/"button")` au lieu de `menuitem`). |
| 7 | LOW | Le lien "Paramètres" réutilisait `MVP_FALLBACK_PATH` (sémantiquement "route de repli post-login pour les rôles sans dashboard") en `<a>` plein-reload plutôt qu'un `<Link>` avec sa propre constante. | Nouvelle constante locale `SETTINGS_PATH = "/parametres/confidentialite"` + `<Link>` (soft-navigation). |

**Confirmé propre par la revue (pas de fix nécessaire)** : pas de fuite d'autorisation (`NAV_ITEMS` ⊆ `ROUTE_ALLOWED_ROLES` par rôle, testé), matching d'état actif correct (pas de faux positif `/mes-metiers-foo`), `hidden lg:flex` retire bien la sidebar de l'arbre d'accessibilité sur mobile, pas de fuite de listener, pas de mismatch d'hydratation (`usePathname()` disponible en SSR côté Client Component), typage sain (seul cast : `role as UserRole`, documenté et sûr).

**Vérification post-fix** : `npx vitest run` → 744 passed (mêmes 5 échecs pré-existants, sans rapport, dans `onboarding/step-3` et `ParcoursList`) ; `eslint`/`tsc --noEmit` clean sur les fichiers touchés ; smoke test Docker (`/accueil` → 200 après connexion).

**Limitations connues, volontairement non traitées (hors scope)** :
- Icônes de la bottom tab bar utilisent `fill="currentColor"` sur des icônes `lucide-react` conçues stroke-only — effet "rempli" pour l'état actif approximatif ; un set filled/outline pairé serait plus propre, non bloquant.
- Pas de composant `Popover`/`DropdownMenu` du design system installé — `account-menu.tsx` reste une implémentation maison minimale. Factoriser si un futur composant a besoin d'un popover similaire.
- `getPostLoginPath(role, "active")` dans `desktop-sidebar.tsx` passe un statut littéral au lieu du vrai statut courant — sans impact, `_status` n'est pas encore consommé par `getPostLoginPath` (paramètre réservé, cf. sa docstring).
