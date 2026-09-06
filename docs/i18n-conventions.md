# Conventions i18n (Story 7.7)

## Stack

`next-intl`, single locale (`fr`) for le MVP, **sans routing par locale** (pas de segment `[locale]`, pas de préfixe `/fr/` sur les URLs). Voir `_bmad-output/implementation-artifacts/7-7-i18n-foundation.md` §4 pour la justification (URLs SEO Epic 7 déjà indexées sans préfixe).

- Config : `apps/web/src/i18n/config.ts` (locales supportées), `apps/web/src/i18n/request.ts` (résolution du catalogue de messages).
- Catalogue : `apps/web/messages/fr.json`.
- Provider : branché une fois dans `apps/web/src/app/layout.tsx` (`NextIntlClientProvider`), messages chargés côté serveur via `getMessages()`.

## Utilisation

- **Server Components** (pages, `generateMetadata`) : `getTranslations(namespace)` de `next-intl/server`.
- **Client Components** : `useTranslations(namespace)` de `next-intl`.
- Interpolation : `t("key", { variable })` avec `{variable}` dans la valeur JSON (syntaxe ICU basique — pas de pluriels/genre complexes utilisés pour l'instant, `next-intl` les supporte si besoin futur).

## Namespaces (organisation des clés)

Un namespace par feature/page, jamais un fichier plat. Structure actuelle (`messages/fr.json`) :

- `common.*` — strings partagées entre plusieurs pages (ex : lien mentions légales).
- `homepage.*` — page d'accueil publique (Story 7.8) : `hero`, `howItWorks`, `ahaMoments`, `trust`, `meta` (title/description SEO).
- `metierPage.*` — `/metiers/{slug}` (Story 7.1).
- `formationPage.*` — `/formations/{slug}` (Story 7.2).
- `devenirMetierPage.*` — `/devenir-{metier}` (Story 7.3 AC1).
- `quelBacPourPage.*` — `/{niveau}/quel-bac-pour-{metier}` (Story 7.3 AC2), y compris `niveauLabels.*` (labels des niveaux scolaires, avant hardcodés dans une constante de code).

**Règle** : le nom du namespace correspond à la page/feature, pas au composant — plusieurs composants d'une même page peuvent partager un namespace (ex : les 4 composants de `homepage/`) via des sous-clés (`homepage.hero.*`, `homepage.trust.*`).

**Convention de clé** : `camelCase`, descriptive du rôle UI (`signupCta`, `signupCtaTitle`, `descriptionFallback`) plutôt que du texte français lui-même — permet de retraduire sans renommer la clé.

**Rich text / liens intégrés** : ne PAS utiliser `t.rich()` pour un lien simple entouré de texte — préférer découper en `xBeforeLink` / `xLink` et garder le `<Link>` comme un vrai composant Next.js (navigation client-side), voir `TrustSection` pour l'exemple.

## Ajout d'un nouveau pays growth (AC3)

Créer `apps/web/messages/{locale}.json` (ex : `fr-BE.json`, `fr-MA.json`) avec les clés à surcharger (ex : `"Parcoursup"` → équivalent local) — **aucun changement de code applicatif** tant que le routing reste mono-locale (voir §4 de la story). Le jour où un 2e pays doit être réellement routé (`/fr-BE/...`), c'est une story dédiée avec sa propre migration SEO (redirections 301 depuis les URLs actuelles) — pas un simple ajout de fichier JSON.

## Tests

Un composant migré vers `useTranslations` a besoin d'un ancêtre `NextIntlClientProvider` pour être rendu en test, sinon RTL lève "No intl context found". Utiliser `renderWithIntl` (`apps/web/src/test/render-with-intl.tsx`) à la place de `render` de `@testing-library/react`.

Un Server Component utilisant `getTranslations`/`getMessages` de `next-intl/server` échoue sous Vitest (`next-intl/server` résout sa build `react-client`, qui lève "not supported in Client Components" — Vitest n'a pas la condition d'export `react-server` que Next.js configure réellement). Mocker le module dans le fichier de test :

```ts
vi.mock("next-intl/server", () => import("@/test/next-intl-server-mock"));
```

`@/test/next-intl-server-mock` lit le vrai `messages/fr.json` (pas une fixture par test) — une clé renommée/supprimée fait échouer le test comme en production, au lieu de passer silencieusement contre un mock obsolète.

## Dette assumée (pages/flows non migrés dans cette story)

Voir `_bmad-output/implementation-artifacts/7-7-i18n-foundation.md` §6 et sa liste de "Fichiers modifiés" pour le périmètre exact couvert par la Story 7.7 et ce qui reste hardcodé (espace authentifié hors le flow onboarding représentatif, back-office, emails/notifications).
