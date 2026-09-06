# Story 7.3 : Landing pages long-tail SEO

**Status:** done

## 1. User Story

As a moteur de recherche et acquisition organique,
I want des pages SEO long-tail générées dynamiquement à partir du référentiel (`/devenir-{metier}`, `/{niveau}/quel-bac-pour-{metier}`, `/{niveau}/integrer-{ecole}`),
So that Path-Advisor capte les requêtes spécifiques d'orientation (FR46).

## 2. Scope decisions

- **`/{niveau}/integrer-{ecole}` non implémenté cette story** — l'AC liste trois formes d'URL en exemple ("`/devenir-{metier}`, `/{niveau}/quel-bac-pour-{metier}`, `/{niveau}/integrer-{ecole}`") mais les critères d'acceptation détaillés ne couvrent que les deux premières formes (aucun AC ne décrit le contenu de la page "intégrer-{école}"). Les deux formes avec AC explicite sont livrées ; la troisième est différée, pas oubliée silencieusement.
- **Bug de routing Next.js découvert et corrigé pendant cette story** : un segment de dossier App Router ne peut PAS mélanger texte littéral + `[param]` dynamique (ex. `devenir-[metier]` ou `quel-bac-pour-[metier]`) — seul `[param]` seul, couvrant tout le segment, est un vrai segment dynamique. Le préfixe littéral collé au crochet est traité comme du texte statique qui ne matche jamais l'URL réelle (confirmé par un 404 live en test Docker, alors que le build avait compilé la route sans erreur). Correction : chaque préfixe ("devenir-", "quel-bac-pour-") est extrait manuellement dans le code à partir d'un segment `[slug]`/`[metierSlug]` entièrement dynamique — tout slug qui ne porte pas le préfixe attendu retourne 404.
- **Un seul segment dynamique par niveau de route** — Next.js exige que tous les dossiers dynamiques frères au même niveau partagent le même nom de paramètre. `/devenir-{metier}` (racine) et `/{niveau}/quel-bac-pour-{metier}` (racine + un niveau) partagent donc `[slug]` à la racine ; le second niveau utilise `[metierSlug]` (différent nom, niveau différent — pas de conflit).
- **Niveaux supportés pour `/{niveau}/quel-bac-pour-{metier}`** : `3eme`, `terminale-generale`, `terminale-technologique`, `terminale-pro` — correspondance directe avec `Parcours.NiveauScolaire` (Story 4.7), aucun niveau fictif inventé. "3ème" (exemple de l'AC) mappe sur `troisieme_bac_pro`, seul parcours 3ème modélisé dans le référentiel (pas de 3ème→bac général/techno — cette donnée n'existe pas).
- **Panel "Quels bacs / formations choisir ?" et écoles cibles** réutilisent le modèle `Parcours` existant (Story 4.3/4.7, FK réelle profession→école) via un nouvel endpoint public `GET /api/v1/public/metiers/{slug}/parcours/` (`AllowAny`, `ParcoursPublicSeoSerializer` — sans `nodes`/`edges`/`admission_stat`, juste niveau + école cible).
- **FAQ générée à partir des données réelles de la fiche** (`median_salary_eur`, `requirements_json` type=studies, `prospects_text`, `level_compatibility`) — jamais de faits fabriqués. Le markup `FAQPage` reflète exactement ce contenu visible (exigence Google Rich Results : le JSON-LD ne doit jamais contenir plus/autre chose que ce qui est affiché).
- **Schema.org `Occupation` + `FAQPage`** implémentés (via `<script type="application/ld+json">`) ; `EducationalOrganization`/`Course` (mentionnés dans l'AC) laissés à la Story 7.4 (balisage Schema.org dédié + sitemap) qui les couvrira sur les fiches école/formation elles-mêmes.

## 3. Acceptance Criteria

**AC1 — `/devenir-{metier}`**
✅ Combine fiche métier (réutilise l'endpoint public Story 7.1) + panel "Quels bacs / formations choisir ?" (regroupé par niveau) + liens écoles cibles + FAQ structuré.

**AC2 — `/{niveau}/quel-bac-pour-{metier}`**
✅ Contenu adapté par niveau (3ème → lycées pro associés ; terminales → formations accessibles), niveaux limités à ceux réellement modélisés (voir §2).

**AC3 — Schema.org + title/meta**
✅ `Occupation` + `FAQPage` JSON-LD sur les deux pages ; `title`/`meta description` optimisés par URL (`generateMetadata`).

## 4. Fichiers modifiés/créés

**Backend**
- `apps/schools/serializers.py` — `ParcoursPublicSeoSerializer`.
- `apps/schools/views.py` — `ParcoursPublicSeoListView` (`AllowAny`).
- `apps/schools/urls.py` — route `public/metiers/<slug>/parcours/`.
- `scripts/assert_rbac_declared.py` — whitelist `public-seo-metier-parcours-list`.
- `apps/schools/tests/test_parcours_public.py` (new, 5 tests).

**Frontend**
- `lib/api/schools.ts` — `ParcoursSummary`, `fetchPublicParcoursSummary`.
- `lib/seo/occupation-landing.ts` (new) — `buildOccupationFaq`, `buildOccupationJsonLd`, `buildFaqPageJsonLd`, `SITE_ORIGIN` + test (6 tests).
- `app/[slug]/page.tsx` (new, ex-`devenir-[metier]`) — `/devenir-{metier}` + test (4 tests).
- `app/[slug]/[metierSlug]/page.tsx` (new, ex-`[niveau]/quel-bac-pour-[metier]`) — `/{niveau}/quel-bac-pour-{metier}` + test (4 tests).

## 5. Vérifications

- Ruff : 0 erreur.
- Tests backend : `5 passed` sur SQLite, `5 passed` sur Postgres (parité RLS, aucun bug trouvé).
- `manage.py check` : 0 issue. `makemigrations --check` : uniquement la dérive pré-existante `bulletins`.
- `assert_rbac_declared.py` : 290 endpoints (+1).
- Suite backend complète : `1406 passed, 150 skipped` (+5 vs Story 7.2), 0 régression.
- Frontend : 14 nouveaux tests passent (6 helper + 4 + 4 pages) ; suite complète `886 passed, 12 failed` (échecs pré-existants non liés) ; `eslint` 0 erreur ; `tsc --noEmit` 0 nouvelle erreur.
- **Bug de routing détecté ET corrigé pendant le smoke test Docker live** (voir §2) — sans ce test end-to-end réel, les deux pages auraient été mergées en 404 permanent malgré des tests unitaires passants (les tests unitaires appellent directement la fonction de page avec des `params` déjà résolus, ils ne passent jamais par le routeur Next.js réel).
- Smoke test Docker live (après correction) : `/devenir-agent-securite-privee` → `200`, JSON-LD Occupation+FAQPage présents, FAQ générée à partir des vraies données ; `/terminale-generale/quel-bac-pour-agent-securite-privee` → `200`, école cible liée ; `/3eme/quel-bac-pour-agent-securite-privee` → `200`, "Lycées professionnels associés" affiché ; `/premiere/quel-bac-pour-agent-securite-privee` (niveau non supporté) → `404` ; `/agent-securite-privee` (sans préfixe `devenir-`) → `404` — données de test nettoyées après vérification.
