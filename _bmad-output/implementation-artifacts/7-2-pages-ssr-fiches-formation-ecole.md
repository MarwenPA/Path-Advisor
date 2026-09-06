# Story 7.2 : Pages publiques SSR — fiches formation / école indexables

**Status:** done

## 1. User Story

As a moteur de recherche et acquisition organique,
I want une URL canonique stable et indexable par école / formation (`/formations/{slug}` ou `/ecoles/{slug}`),
So that les pages formations apparaissent sur les recherches "INSA Lyon", "BUT MMI", "Prépa BCPST" (FR46).

## 2. Scope decisions

- **`/formations/{slug}`** choisi (l'AC autorise `/formations/{slug}` OU `/ecoles/{slug}` — exemple littéral de l'AC = `/formations/insa-lyon-genie-biomedical`) comme NOUVELLE route publique, distincte de `/schools/{slug}` (authentifiée, Story 4.4, inchangée). Pas de fusion comme la Story 7.1 (métiers) : `/schools/{slug}` embarque `<OutreachSection>` (feature premium, personnalisée) qui ne doit jamais apparaître pour un visiteur anonyme — deux pages séparées est plus sûr qu'une page conditionnelle complexe.
- **`SchoolPublicSeoSerializer` sans `admission_stat`** — l'AC exige "sélectivité brute (anonyme, pas personnalisée)", pas la probabilité personnalisée-ou-baseline que `SchoolDetailSerializer.get_admission_stat` résout. `selectivity_index` (note 1-5 statique) reste — c'est la donnée "brute" demandée. `<FicheEcole>` masque déjà conditionnellement `<AdmissionStatPoller>` quand `admission_stat` est absent — aucun composant dédié "anonyme" à écrire.
- **Cross-linking (AC2) sans nouveau modèle de données** :
  - "Métiers cibles" : `top_debouches` (`JSONField` de strings libres, aucune FK vers `Profession`) — matching best-effort par nom (insensible à la casse) contre le référentiel métiers actif, calculé côté serializer (`get_metiers_cibles`). Les entrées non matchées sont simplement absentes des liens (le frontend a quand même `top_debouches` brut si besoin futur) — documenté, pas une perte silencieuse de données.
  - "Écoles similaires" : aucun moteur de recommandation/similarité n'existe — heuristique documentée : même `type` (`School.Type`), exclusion de soi-même, limite 4, tri alphabétique.
  - Choix : calculer ces deux champs côté backend (`SerializerMethodField`) plutôt que d'ajouter deux nouveaux endpoints catalogue publics côté frontend — une seule requête HTTP, cohérent avec le pattern déjà utilisé par `get_admission_stat`.
- **`School.id` rendu optionnel** côté TS (même raisonnement que `Profession.id` en Story 7.1 — absent du payload anonyme, seul le variant "compare" de `<FicheEcole>` le lit, jamais atteint depuis cette page).
- **Pas de page catalogue publique `/formations`** — aucune AC ne le demande pour cette story ; le lien "retour" vers une liste a donc été omis plutôt que de pointer vers une page inexistante.

## 3. Acceptance Criteria

**AC1 — SSR + contenu complet + CTA**
✅ `/formations/{slug}` accessible sans compte (confirmé `curl` sans cookies → 200), nom/ville/description/débouchés/frais/sélectivité/dates Parcoursup visibles, CTA "Crée ton compte pour voir ta proba d'admission personnalisée".

**AC2 — Pages liées (cross-linking)**
✅ Liens vers `/metiers/{slug}` (métiers cibles matchés) et écoles similaires (`/formations/{slug}`), tous deux issus du même appel API.

**AC3 — Core Web Vitals**
✅ `revalidate = 3600` (même approche que Story 7.1) ; mesure formelle laissée à la Story 7.6 (gate CI dédiée).

## 4. Fichiers modifiés/créés

**Backend**
- `apps/schools/serializers.py` — `SchoolPublicSeoSerializer` (+ `get_metiers_cibles`, `get_similar_schools`).
- `apps/schools/views.py` — `SchoolPublicSeoDetailView` (`AllowAny`).
- `apps/schools/urls.py` — route `public/schools/<slug>/`.
- `scripts/assert_rbac_declared.py` — whitelist `public-seo-school-detail`.
- `apps/schools/tests/test_endpoints.py` — +8 tests (`TestSchoolPublicSeoDetail`).

**Frontend**
- `lib/api/schools.ts` — `fetchPublicSchool`, `School.id` optionnel, `metiers_cibles`/`similar_schools`.
- `app/formations/[slug]/page.tsx` (new) + test (3 tests).

## 5. Vérifications

- Ruff : 0 erreur.
- Tests backend : `31 passed` sur SQLite, `31 passed` sur Postgres (parité RLS, aucun bug trouvé).
- `manage.py check` : 0 issue. `makemigrations --check` : uniquement la dérive pré-existante `bulletins`.
- `assert_rbac_declared.py` : 289 endpoints (+1).
- Suite backend complète : `1401 passed, 150 skipped` (+8 vs Story 7.1), 0 régression.
- Frontend : 3 nouveaux tests passent ; suite complète `872 passed, 12 failed` (échecs pré-existants non liés) ; `eslint` 0 erreur ; `tsc --noEmit` 0 nouvelle erreur.
- Smoke test Docker live : `curl` anonyme sur `/formations/universite-aix-marseille` → `200`, `<title>` correct, CTA présent ; `curl` direct sur `/api/v1/public/schools/universite-aix-marseille/` → `200`, champs corrects (`id`/`admission_stat` absents, `metiers_cibles`/`similar_schools` présents).
