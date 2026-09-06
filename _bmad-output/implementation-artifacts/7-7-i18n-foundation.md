# Story 7.7 : i18n foundation (français MVP, préparation francophonie)

**Status:** ready-for-dev

## 1. User Story

As a système Path-Advisor,
I want une foundation i18n structurée (clés de traduction extractibles, pas de strings hardcodés),
So that l'expansion francophonie (Belgique, Maroc, Tunisie, Sénégal) en growth soit faisable sans refactor majeur (ADD-11 / NFR cross-cutting n°8).

## 2. Acceptance Criteria (epic 7)

**AC1** — Toutes les strings UI sont dans `messages/fr.json` (français MVP unique) ; aucun string user-facing n'est hardcodé dans le JSX.

**AC2** — Les clés de `messages/fr.json` sont organisées par feature (`onboarding.*`, `recos.*`, `parcours.*`, `paywall.*`, etc.) ; une convention de naming est documentée.

**AC3** — Ajouter un nouveau pays growth ne nécessite que la création de `messages/{locale}.json` (ex : `fr-BE`, `fr-MA`) avec les overrides spécifiques (ex : "Parcoursup" → équivalent local) — aucun changement de code applicatif requis.

## 3. Contexte architecture (déjà décidé, non renégociable)

- **Stack imposée : `next-intl`** — `core-architectural-decisions.md` : *"i18n | next-intl avec routing locale (/fr/... par défaut) | NFR cross-cutting n°8"*. `starter-template-evaluation.md` liste `next-intl` comme dépendance déjà prévue dès le starter (`npm install next-intl ...`), mais **jamais installée depuis** (absent de `apps/web/package.json` actuel — vérifié).
- **Emplacement attendu** : `apps/web/messages/` (traductions), `apps/web/src/i18n/` (config next-intl) — `project-structure-boundaries.md#L34,88`.
- **Règle transverse déjà en vigueur** (`implementation-patterns-consistency-rules.md#L260`) : *"Tout texte utilisateur passe par i18n (useTranslations front, gettext Django) — pas de string en dur"* — donc en théorie déjà une règle PR checklist (`#L268`), mais **jamais appliquée en pratique** : la totalité du code Epic 1-6 + Epic 7 (7.1-7.6, 7.8) a été écrite avec des strings françaises hardcodées directement dans le JSX (confirmé par grep — voir §5).
- **Backend (Django)** : `apps/api/**/i18n/`, `apps/api/**/locale/`, middleware `i18n.py` sont mentionnés dans l'arborescence cible mais n'existent pas encore dans le repo réel (vérifié : aucun dossier `locale/` sous `apps/api`). Le backend expose déjà des textes utilisateur en dur (messages d'erreur DRF, contenus de notification) — **hors périmètre de cette story** : l'AC epic 7.7 ne parle que du front (`messages/fr.json`, JSX) ; le `gettext` Django n'est pas dans les AC listées et n'a pas de story dédiée dans le sprint actuel. Le documenter comme dette explicite plutôt que l'ignorer silencieusement.

## 4. Décision architecturale bloquante à trancher AVANT implémentation

`next-intl` tel que décrit dans `core-architectural-decisions.md` implique un **routing par locale** (`/fr/...`). Or **toutes les routes publiques SEO d'Epic 7 (7.1 à 7.6, 7.8) ont été construites et indexées sans préfixe de locale** : `/metiers/{slug}`, `/formations/{slug}`, `/devenir-{metier}`, `/{niveau}/quel-bac-pour-{metier}`, `/`, plus tout l'espace authentifié (`/mes-metiers`, `/parametres`, `/parent`, etc.). `sitemap.ts`/`robots.ts` (Story 7.4) et tous les `generateMetadata` (canonical URLs, OG `url`) référencent ces chemins **sans** `/fr/`.

Deux options, avec un delta de périmètre très différent :

- **Option A (recommandée pour cette story) — `next-intl` sans routing par locale** : une seule locale (`fr`) servie à la racine, `messages/fr.json` chargé globalement (provider unique côté `app/layout.tsx`ou format "non-i18n-routing" documenté par next-intl pour les apps mono-locale). Aucune URL ne change, zéro impact sur le SEO déjà shippé (sitemap, canonical, OG). Quand un vrai 2e pays est ajouté (growth, hors scope MVP), le passage au routing par locale (`/fr/`, `/fr-BE/`) sera une story dédiée avec ses propres migrations de redirections SEO (301 depuis les URLs actuelles).
- **Option B — routing par locale dès maintenant** (`/fr/...` conforme à la lettre de `core-architectural-decisions.md`) : casse toutes les URLs déjà indexées par Epic 7, nécessite de refaire sitemap/robots/canonical/OG et d'ajouter des redirections 301 — gros risque de régression SEO sur du travail fraîchement mergé pour une AC (7.7) qui ne demande explicitest qu'un seul JSON `fr` unique et ne mentionne aucun changement d'URL.

**Cette story implémente l'Option A** — cohérent avec l'AC epic ("français MVP unique", "aucun changement de code applicatif requis" pour ajouter un pays) qui ne demande pas de routing par locale actif pour du mono-locale. Le routing par locale est noté comme decision différée, pas ignorée : voir §7.

## 5. État réel du code (grep effectué avant écriture de cette story)

- Aucune dépendance `next-intl` dans `apps/web/package.json` — à ajouter.
- Aucun dossier `apps/web/messages/` ni `apps/web/src/i18n/` — à créer.
- Strings hardcodées : présentes dans la quasi-totalité des ~150+ composants/pages `apps/web/src/**/*.tsx` (JSX, labels, placeholders, messages d'erreur, `aria-label`, `alt`, toasts). Épics 1 à 6 + 7.1-7.6/7.8 sont concernés en totalité.

## 6. Scope decision — migration complète vs. fondation + migration progressive

Migrer **100 % des strings de l'application entière** (8+ epics, des dizaines de milliers de lignes JSX) en une seule story serait un chantier disproportionné par rapport à une story de fondation ("i18n foundation"). L'AC dit littéralement "toutes les strings UI sont dans messages/fr.json" — pris au pied de la lettre c'est une migration totale, mais le titre et l'intent ("foundation", "préparation" francophonie) suggèrent que la story pose la structure et convention, avec une migration qui peut être terminée dans des passes suivantes (hors sprint courant si nécessaire).

**Décision retenue pour cette story (à confirmer explicitement avec l'utilisateur avant dev — voir clarifications) :**
- Mettre en place `next-intl` (config, provider, `useTranslations`) — infra complète et fonctionnelle.
- Créer `messages/fr.json` avec la structure de namespaces par feature, convention documentée (`docs/i18n-conventions.md` ou équivalent).
- Migrer **intégralement les pages publiques SEO d'Epic 7** (7.1-7.6, 7.8 — `/`, `/metiers/[slug]`, `/formations/[slug]`, `/[slug]`, `/[slug]/[metierSlug]`) — ce sont les pages qui ont le plus de valeur SEO/faible profondeur, et elles servent de démonstration concrète de la convention pour le reste de l'app.
- Migrer un échantillon représentatif de l'espace authentifié (au moins un flow complet, ex: onboarding) pour prouver que la convention tient aussi côté authentifié (formulaires, validations, toasts).
- Documenter explicitement (dans cette story, section Vérifications) la liste des zones **non encore migrées** — dette assumée et traçable, pas cachée — plutôt que de prétendre à une migration à 100 % qui ne serait pas honnête compte tenu du volume réel du code.

## 7. Tasks / Subtasks

- [ ] **T1 (AC1, AC2)** — Installer `next-intl`, créer `apps/web/src/i18n/` (config/request/routing minimal sans préfixe de locale), brancher le provider dans `app/layout.tsx`.
- [ ] **T2 (AC2)** — Créer `apps/web/messages/fr.json` avec une structure de namespaces par feature (`common.*`, `nav.*`, `onboarding.*`, `recos.*`, `parcours.*`, `paywall.*`, `seo.*`, `auth.*`, `parent.*`, `cohorte.*`, `ecole.*`...). Documenter la convention de naming dans un fichier dédié.
- [ ] **T3 (AC1)** — Migrer les pages publiques Epic 7 (7.1, 7.2, 7.3, 7.8) vers `useTranslations`/`getTranslations` — zéro string hardcodée restante sur ces pages précises.
- [ ] **T4 (AC1)** — Migrer un flow authentifié représentatif (onboarding, au minimum step 1-3 + les composants partagés `passions-picker`, `specialites-picker`, etc.) comme preuve de convention côté authentifié.
- [ ] **T5 (AC3)** — Documenter (README ou doc dédiée) la procédure d'ajout d'un nouveau pays growth : créer `messages/{locale}.json`, aucune modif de code applicatif attendue au-delà (vérifier avec un faux `messages/fr-BE.json` de test si le temps le permet, supprimé avant merge).
- [ ] **T6** — Lister explicitement, dans la section Vérifications de cette story, toutes les zones du code NON migrées (dette assumée) pour que ce ne soit pas silencieusement oublié.
- [ ] **T7** — Vérifier que `ci-web` reste vert (lint/typecheck/build/tests) et qu'aucune régression SEO n'est introduite sur les pages migrées (rebuild + spot-check `curl` du HTML final, cohérent avec la discipline établie sur 7.1-7.6).

## 8. Dev Notes

### Fichiers/dossiers à créer

- `apps/web/src/i18n/request.ts` (ou équivalent selon la doc `next-intl` v3+ — **doc à relire dans `node_modules/next-intl` une fois installé, ce package n'a jamais été utilisé dans ce repo** ; suivre la même discipline que le reste de la session : ne pas halluciner l'API sur la base de connaissances d'entraînement, lire la doc réelle du package installé).
- `apps/web/messages/fr.json`.
- `apps/web/src/i18n/config.ts` (locales supportées = `["fr"]` pour le MVP).

### Fichiers à modifier

- `apps/web/src/app/layout.tsx` — brancher `NextIntlClientProvider`.
- `apps/web/package.json`/`package-lock.json` — ajout dépendance `next-intl`.
- Pages/composants listés en §6 (migration ciblée).

### Contraintes à respecter

- **Aucun changement d'URL** — pas de préfixe `/fr/` (voir §4, Option A). Les tests de routing existants (Story 7.3 notamment, avec ses contraintes Next.js sur les segments dynamiques `[slug]`) ne doivent pas être touchés par cette story.
- Les `generateMetadata` des pages migrées peuvent continuer à utiliser des données backend (nom de métier/école, dynamique) concaténées à des clés i18n statiques — ne pas essayer de i18n-iser du contenu qui vient de la base de données (professions/schools), seulement les strings UI statiques.
- Respecter la discipline établie cette session : `npm run lint`/`typecheck`/`format:check`/`test -- --run`/`build` doivent tous passer avant de pousser ; ne merger qu'après confirmation `gh run watch` que `ci-web` (et `ci-lighthouse`, qui audite les mêmes pages publiques migrées) sont verts.

### Project Structure Notes

- Conforme à `project-structure-boundaries.md` (`apps/web/messages/`, `apps/web/src/i18n/`).
- Écart assumé et documenté : le backend Django (`gettext`, `locale/`) n'est PAS traité ici (hors AC epic 7.7) — à créer comme story explicite si/quand le backend expose des textes utilisateur destinés à être traduits (actuellement webhooks/erreurs techniques, pas des contenus front-facing multi-locale).
- Écart assumé et documenté : routing par locale non activé (Option A, §4) — diverge de la lettre de `core-architectural-decisions.md` mais cohérent avec l'AC réelle de cette story (mono-locale) ; à réévaluer explicitement dès qu'un 2e pays réel est planifié.

### References

- [Source: _bmad-output/planning-artifacts/epics/epic-7-decouverte-publique-seo.md#Story 7.7]
- [Source: _bmad-output/planning-artifacts/architecture/core-architectural-decisions.md#L74]
- [Source: _bmad-output/planning-artifacts/architecture/project-structure-boundaries.md#L34,88,218,372,472]
- [Source: _bmad-output/planning-artifacts/architecture/implementation-patterns-consistency-rules.md#L118,260,268]
- [Source: _bmad-output/planning-artifacts/architecture/starter-template-evaluation.md#L38,104,107,187]

## 9. Previous story intelligence (7.6, 7.8)

- 7.6 a établi la discipline : ne jamais merger sans `gh run watch` confirmant CI vert ; toujours reproduire en local avec un build de production réel avant de considérer une AC vérifiée. À répliquer ici : le "0 string hardcodée sur les pages migrées" doit être vérifié par une lecture réelle du JSX final, pas juste "j'ai remplacé ce que j'ai trouvé".
- 7.8 (page d'accueil publique moderne, déjà `done`) a créé `hero-section.tsx`, `how-it-works-section.tsx`, `trust-section.tsx`, `aha-moments-section.tsx` sous `apps/web/src/components/features/homepage/` — ce sont des composants de la page `/` (dans le périmètre T3 de cette story), à vérifier/migrer en priorité car récents et donc représentatifs du style de code actuel.

## 10. Dev Agent Record

### Agent Model Used

claude-sonnet-5

### Debug Log References

### Completion Notes List

### File List
