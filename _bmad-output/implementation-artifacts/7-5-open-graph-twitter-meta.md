# Story 7.5 : Open Graph + Twitter Cards + meta tags

**Status:** done

## 1. User Story

As a réseau social (Instagram, WhatsApp, X, LinkedIn),
I want un preview riche quand un utilisateur partage une page Path-Advisor,
So that le partage social viralise correctement avec image + titre + description (FR46 et viralité organique).

## 2. Scope decisions

- **Convention fichier Next.js** (`opengraph-image.tsx` par segment de route) + API `ImageResponse` (`next/og`) — pas de service de génération d'image externe, pas de librairie de canvas custom.
- **Pas de fichier `twitter-image.tsx` séparé** — Twitter utilise `og:image` en fallback quand aucun `twitter:image` dédié n'est fourni (spec Twitter Card officielle) ; confirmé lors du smoke test live (`twitter:image` apparaît bien dans le head, généré à partir du même `opengraph-image.tsx`). Un seul rendu par page, pas de duplication.
- **Aucune police custom chargée** — le rendu par défaut de `next/og` suffit pour cette mise en page simple (titre + eyebrow + branding) ; charger un `.ttf` aurait ajouté du poids sans gain visuel perceptible pour ce contenu.
- **Branding sobre** : vermillon `#C8312D` (token `--color-brand`, Story 1.2), un dégradé léger, le nom "Path-Advisor" en majuscules — cohérent avec l'AC "branding Path-Advisor sobre + texte contextuel".
- **Cinq pages publiques couvertes** (toutes celles créées Stories 7.1-7.4) : `/` (statique), `/metiers/{slug}`, `/formations/{slug}`, `/devenir-{metier}`, `/{niveau}/quel-bac-pour-{metier}` — chacune avec un `opengraph-image.tsx` contextuel (nom du métier/école récupéré via les endpoints publics existants) + `og:url`/`og:type`/Twitter Card dans `generateMetadata`.
- **Duplication de la logique d'extraction de préfixe** (`devenir-`, `quel-bac-pour-`) dans les fichiers `opengraph-image.tsx` plutôt qu'un import depuis `page.tsx` — les conventions de fichiers image Next.js sont compilées comme des route handlers séparés ; documenté dans chaque fichier, fonctions minuscules (une ligne), risque de désynchronisation faible.

## 3. Acceptance Criteria

**AC1 — Preview riche (og:image 1200×630)**
✅ `renderOgImage` (helper partagé) génère une image 1200×630 PNG par page, avec titre contextuel (nom métier/école) — vérifié via smoke test Docker live sur les 5 pages (`file` confirme `1200 x 630 PNG` sur chacune).

**AC2 — Balises Open Graph + Twitter Card**
✅ `og:title`, `og:description`, `og:image` (+ `og:image:type/width/height/alt`), `og:url`, `og:type` + `twitter:card` (`summary_large_image`) présents dans le `<head>` — confirmé via `curl` brut sur `/metiers/agent-securite-privee`.

**AC3 — Génération à la volée (Next.js `ImageResponse`)**
✅ `next/og`'s `ImageResponse`, pas de pré-génération statique côté build pour les pages dynamiques (métier/école récupérés à la requête).

## 4. Fichiers modifiés/créés

**Frontend**
- `lib/seo/og-image.tsx` (new) — `renderOgImage`, `OG_IMAGE_SIZE`, `OG_IMAGE_CONTENT_TYPE` + test (2 tests).
- `app/opengraph-image.tsx` (new, racine, statique).
- `app/metiers/[slug]/opengraph-image.tsx` (new) + test (2 tests).
- `app/formations/[slug]/opengraph-image.tsx` (new) + test (2 tests).
- `app/[slug]/opengraph-image.tsx` (new, devenir-{metier}) + test (2 tests).
- `app/[slug]/[metierSlug]/opengraph-image.tsx` (new, quel-bac-pour-{metier}) + test (2 tests).
- `app/page.tsx`, `app/metiers/[slug]/page.tsx`, `app/formations/[slug]/page.tsx`, `app/[slug]/page.tsx`, `app/[slug]/[metierSlug]/page.tsx` — `generateMetadata`/`metadata` étendus (`openGraph.url/type`, `twitter.card`) ; tests étendus (+2).

## 5. Vérifications

- Aucun changement backend — pas de nouvelle vérification RBAC/migrations/Postgres nécessaire.
- Tests frontend : 12 nouveaux/étendus passent ; suite complète `907 passed, 12 failed` (échecs pré-existants non liés) ; `eslint` 0 erreur ; `tsc --noEmit` 0 nouvelle erreur.
- Smoke test Docker live : `curl` sur `/opengraph-image` (racine) et sur les 4 routes dynamiques → `200 image/png`, `file` confirme `1200 x 630 PNG` sur chacune ; `curl` brut sur `/metiers/agent-securite-privee` → toutes les balises `og:*`/`twitter:*` attendues présentes, `og:image`/`twitter:image` pointant vers l'URL générée dynamiquement.
