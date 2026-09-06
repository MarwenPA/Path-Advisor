# Story 7.4 : Sitemap XML + robots.txt + Schema.org markup

**Status:** done

## 1. User Story

As a moteur de recherche,
I want une sitemap XML auto-générée et un balisage Schema.org strict pour découvrir et indexer toutes les pages publiques,
So that Path-Advisor maximise son indexabilité (FR46).

## 2. Scope decisions

- **Convention fichier Next.js** (`app/robots.ts`, `app/sitemap.ts`) plutôt que des routes API custom — génération native `/robots.txt`/`/sitemap.xml`, déjà anticipée par `src/proxy.ts`'s matcher (excluait déjà ces deux chemins de l'injection `x-pathname`, écrit avant même que ces fichiers existent).
- **Deux nouveaux endpoints backend minimalistes** (`GET /api/v1/public/professions/slugs/`, `GET /api/v1/public/schools/slugs/`, `AllowAny`) — `{slug, updated_at}` seulement, pas de pagination (catalogue de quelques centaines de lignes), pas de réutilisation des endpoints catalogue existants (qui exigent une authentification et renvoient des champs inutiles pour une sitemap).
- **Pas de sitemap index segmentée** — l'AC ne l'exige que "si > 50 000 URLs" ; le référentiel actuel (professions + écoles) est plusieurs ordres de grandeur en dessous. Revisiter si le catalogue grossit fortement.
- **`/{niveau}/quel-bac-pour-{metier}` volontairement absent de la sitemap** — avec 4 niveaux × chaque métier, l'énumérer multiplierait la taille de la sitemap pour des pages dont le contenu recoupe largement `/devenir-{metier}` (même fiche + même FAQ) ; ces pages restent indexables/crawlables directement, juste non déclarées dans la sitemap (Google découvre aussi via les liens internes).
- **Balisage Schema.org ajouté aux fiches canoniques** : `Occupation` sur `/metiers/{slug}` (Story 7.1 — c'est la "fiche métier" que l'AC teste littéralement) réutilisant le helper `buildOccupationJsonLd` déjà créé en Story 7.3 ; `EducationalOrganization` (nouveau helper `buildEducationalOrganizationJsonLd`) sur `/formations/{slug}` (Story 7.2) — mentionné dans l'intro de l'épique bien que l'AC détaillée de 7.4 ne teste explicitement que `Occupation`. `Course`/`FAQPage` restent sur les landing pages long-tail (déjà livrés en Story 7.3).
- **`robots.txt` — liste littérale des préfixes disallow** plutôt qu'un import de `ROUTE_ALLOWED_ROLES` (ce fichier de config RBAC n'a rien à faire dans un bundle exposé à un crawler) : tous les préfixes authentifiés connus (`/parametres/`, `/onboarding/`, `/accueil/`, `/mes-metiers/`, `/mes-paris/`, `/mes-envois/`, `/profile/`, `/premium/`, `/parent/`, `/support/`, `/cohorte/`, `/ecole/`, `/auth/`) + `/api/` + `/admin/` + `/schools/` (la version AUTHENTIFIÉE, distincte de `/formations/` publique qui reste autorisée).
- **Soumission Google Search Console + Bing Webmaster Tools** (dernier AC) — action manuelle d'ops, non automatisable dans le code ; documentée comme étape manuelle post-déploiement, pas oubliée.

## 3. Acceptance Criteria

**AC1 — Sitemap XML**
✅ `/sitemap.xml` liste métiers (`/metiers/{slug}`), landings long-tail (`/devenir-{metier}`), formations (`/formations/{slug}`) avec `lastmod`/`priority`. Pas de segmentation (voir §2, sous le seuil de 50 000 URLs).

**AC2 — robots.txt**
✅ Autorise les pages publiques, interdit `/api/*`, `/admin/*` et toutes les pages applicatives authentifiées.

**AC3 — Schema.org**
✅ `Occupation` complet sur `/metiers/{slug}`, validé par construction (mêmes champs que Story 7.3, déjà testés).

**AC4 — Soumission Google/Bing**
◻️ Manuel, hors code (voir §2).

## 4. Fichiers modifiés/créés

**Backend**
- `apps/professions/serializers.py` — `ProfessionSlugSerializer`.
- `apps/professions/views.py` — `PublicProfessionSlugsView`.
- `apps/professions/urls.py` — route `public/professions/slugs/`.
- `apps/schools/serializers.py` — `SchoolSlugSerializer`.
- `apps/schools/views.py` — `SchoolPublicSlugsView`.
- `apps/schools/urls.py` — route `public/schools/slugs/`.
- `scripts/assert_rbac_declared.py` — whitelist des deux nouveaux endpoints.
- `apps/professions/tests/test_endpoints.py`, `apps/schools/tests/test_endpoints.py` — +5 tests.

**Frontend**
- `lib/api/professions.ts`, `lib/api/schools.ts` — `fetchPublicProfessionSlugs`, `fetchPublicSchoolSlugs`.
- `lib/seo/occupation-landing.ts` — `buildEducationalOrganizationJsonLd` + test (+2 tests).
- `app/robots.ts` (new) + test (3 tests).
- `app/sitemap.ts` (new) + test (2 tests).
- `app/metiers/[slug]/page.tsx` — Occupation JSON-LD ajouté + test (+1).
- `app/formations/[slug]/page.tsx` — EducationalOrganization JSON-LD ajouté + test (+1).

## 5. Vérifications

- Ruff : 0 erreur.
- Tests backend : `64 passed` sur Postgres (parité RLS, aucun bug trouvé), skip attendu sur SQLite pour les tests `postgresql_only`.
- `manage.py check` : 0 issue. `makemigrations --check` : uniquement la dérive pré-existante `bulletins`.
- `assert_rbac_declared.py` : 292 endpoints (+2).
- Suite backend complète : `1408 passed, 153 skipped` (+2 vs Story 7.3), 0 régression.
- Frontend : 21 nouveaux/étendus tests passent ; suite complète `895 passed, 12 failed` (échecs pré-existants non liés) ; `eslint` 0 erreur ; `tsc --noEmit` 0 nouvelle erreur.
- Smoke test Docker live : `curl /robots.txt` → liste correcte, `Sitemap:` pointant vers `/sitemap.xml` ; `curl /sitemap.xml` → XML valide avec vraies URLs métiers/formations/devenir et `lastmod` réels ; `curl /metiers/agent-securite-privee` → JSON-LD `Occupation` valide avec vraies données ; `curl /formations/universite-aix-marseille` → JSON-LD `EducationalOrganization` valide.
