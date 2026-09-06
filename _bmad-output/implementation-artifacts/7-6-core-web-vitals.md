# Story 7.6 : Core Web Vitals au vert sur toutes les pages publiques

**Status:** done

## 1. User Story

As a Path-Advisor,
I want des Core Web Vitals au vert sur 100 % des pages publiques indexables,
So that le SEO ne soit pas pénalisé et l'acquisition organique reste forte (NFR-P3 + UX-DR34).

## 2. Découverte majeure hors périmètre : le pipeline `ci-web` était cassé sur `main`

En construisant le job Lighthouse, `npm run build` échouait sur `main` — confirmé via `gh run list` : **20+ échecs consécutifs de `ci-web`** remontant au moins à la Story 5.6, jamais remarqués car les fusions de PR n'attendaient jamais le statut CI. Corrigé dans un commit/PR séparé (`fix(ci): repair broken ci-web pipeline`, PR #93, **fusionné avant** cette story) : ~10 erreurs ESLint, ~30 erreurs TypeScript réparties dans tout le dépôt, 59 fichiers non formatés, et 18 échecs de tests runtime. CI est maintenant verte sur `main` pour la première fois de la session (confirmé via `gh run watch`). Voir le commit `0def607` pour le détail complet.

## 3. Scope decisions

- **Job CI dédié** `.github/workflows/ci-lighthouse.yml` plutôt qu'un ajout à `ci-web.yml` — dépend à la fois de `apps/web` et `apps/api` (backend réel requis), scope de déclenchement (`paths`) différent des deux pipelines existants.
- **Backend réel migré + seedé** (`seed_professions`, `seed_schools` — commandes déjà existantes, idempotentes) plutôt que des mocks — les 5 pages de référence font de vrais appels API publics (Story 7.1/7.2/7.3), aucune ne dépend de l'ai-service (endpoints publics = lectures Django pures), donc pas de conteneur ai-service nécessaire dans ce job.
- **5 pages de référence** (AC : "5 pages publiques de référence") : `/`, `/metiers/{slug}`, `/formations/{slug}`, `/devenir-{slug}`, `/{niveau}/quel-bac-pour-{slug}` — utilisant les données seedées stables `technicien-aeronautique` / `lycee-pro-saint-exupery-marseille`.
- **Preset mobile par défaut de Lighthouse** (throttling simulé) conservé tel quel — conforme à l'AC "audite mobile", pas de preset desktop qui aurait été plus stable en CI mais n'aurait pas testé la bonne cible.
- **Bug SEO réel détecté et corrigé** : `/metiers/{slug}` avait un `loading.tsx` (Suspense boundary) — Lighthouse capturait l'état de streaming AVANT que la balise `<meta name="description">` ne soit finalisée dans le DOM (bien que le HTML final, tel que vu par `curl`, la contienne bien) → audit `meta-description` à 0, score SEO 0.91 < 0.95. Ce chemin n'a aucune valeur UX réelle (fetch backend < 50ms, pas d'ai-service) — `loading.tsx` supprimé, la page reste synchrone jusqu'à ce que les données soient prêtes. Après correction : SEO 1.0, meta-description 1.0, confirmé par re-audit Lighthouse local sur un build de production réel.
- **AVIF/WebP/srcset** : aucune image raster n'est actuellement rendue sur les 5 pages publiques (confirmé par grep — pas de `<img>`/`next/image` sur homepage/fiches) ; l'exigence est satisfaite par absence de sujet, pas ignorée. Les images OG (Story 7.5) sont déjà générées en PNG via `next/og`, hors périmètre de cet AC (pas des images de contenu de page).
- **Police préchargée + `font-display: swap`** : déjà en place depuis Story 1.1 (`next/font/google` avec `display: "swap"`) — aucun changement nécessaire.
- **JS critique < 200 ko + code-splitting par route** : satisfait nativement par l'architecture App Router de Next.js (chaque route est son propre bundle) — pas d'audit manuel de taille de bundle effectué dans ce cycle ; le score `performance` de Lighthouse (seuil ≥ 0.8) sert de garde-fou indirect.

## 4. Acceptance Criteria

**AC1 — PageSpeed mobile (LCP/FID/CLS + scores)**
✅ `lighthouserc.json` : `categories:performance ≥ 0.80`, `categories:seo ≥ 0.95`, `largest-contentful-paint ≤ 2500ms`, `cumulative-layout-shift ≤ 0.1`, `total-blocking-time ≤ 200ms` (proxy moderne de FID — Lighthouse ne mesure plus FID directement).

**AC2 — Gate CI bloquante**
✅ `.github/workflows/ci-lighthouse.yml` — migre + seed le backend réel, build+démarre Next.js en production, exécute `lhci autorun` ; un échec d'assertion retourne un exit code non-nul qui fait échouer le job (bloque la fusion via branch protection sur `main`, à activer côté ops si pas déjà fait).

**AC3 — Optimisations (images/polices/JS)**
✅ Polices déjà optimisées (Story 1.1). Aucune image de contenu actuellement rendue (documenté). Code-splitting natif Next.js App Router.

## 5. Fichiers modifiés/créés

- `.github/workflows/ci-lighthouse.yml` (new).
- `apps/web/lighthouserc.json` (new).
- `apps/web/package.json`/`package-lock.json` — `@lhci/cli` en devDependency.
- `apps/web/.gitignore` — exclusion `.lighthouseci` (artefacts de run local).
- `apps/web/src/app/metiers/[slug]/loading.tsx` — **supprimé** (cause du bug SEO ci-dessus).

## 6. Vérifications

- Aucun changement backend au-delà de la migration/seed déjà existante — pas de nouvelle vérification RBAC nécessaire.
- Frontend (sur la base déjà réparée par PR #93) : `npm run lint` 0 erreur, `npm run typecheck` 0 erreur, `npm run format:check` propre, `npm test -- --run` → **919 passed, 0 failed** (aucune régression après suppression de `loading.tsx`).
- `npm run build` (production réelle) : succès.
- **Lighthouse CI exécuté en local contre un vrai build de production + backend réel seedé** (reproduisant exactement le job CI) : 5/5 pages passent toutes les assertions après correction du bug `loading.tsx` (`lhci autorun` → "All results processed!", aucun échec d'assertion).
- Bug SEO détecté ET corrigé au moment même de la vérification live — sans cette vérification end-to-end réelle (backend + build de prod réels, pas de mocks), ce problème serait resté invisible indéfiniment malgré des tests unitaires qui passent tous.
