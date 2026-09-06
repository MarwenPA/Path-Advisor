# Story 7.1 : Pages publiques SSR — fiches métier indexables

**Status:** done

## 1. User Story

As a moteur de recherche (Google, Bing) et acquisition organique,
I want une URL canonique stable et indexable par métier (`/metiers/{slug}`),
So that les pages métiers Path-Advisor apparaissent sur les recherches "devenir X" (FR46 + ADD-6).

## 2. Scope decisions

- **La page existait déjà, gated par erreur.** `apps/web/src/app/(authenticated)/metiers/[slug]/` rendait déjà une fiche SSR complète (le composant `FicheMetierClient` avait même un commentaire anticipant "direct URL access (shared link, refresh, SEO)") — mais vivait sous le layout `(authenticated)`, qui redirige tout visiteur anonyme vers `/auth/login`. Le vrai travail de cette story : déplacer la page hors du groupe protégé et rendre l'endpoint backend réellement anonyme, pas réécrire la vue.
- **Nouvel endpoint backend dédié** `GET /api/v1/public/professions/{slug}/` (`AllowAny`) plutôt que retirer l'authentification de l'endpoint existant `PublicProfessionDetailView` (mal nommé — en réalité `IsAuthenticatedAndActive, IsStudent`) : celui-ci reste inchangé pour ne pas perturber le flux authentifié `/mes-metiers` existant (Story 3.12/3.13), qui continue de l'utiliser en interne via le même composant.
- **`ProfessionPublicSeoSerializer` inclut `signals_json`** (malgré son nom trompeur, ce ne sont que des tags descriptifs "quelles passions/valeurs correspondent à ce métier", pas un secret de l'algorithme de scoring) — `<FicheMetier>` lit ce champ sans condition pour l'onglet "Signaux" et les chips du hero ; l'omettre aurait cassé le rendu, pas seulement caché des internals. Seuls `id`/`is_active` sont exclus (PK/flag interne, jamais affichés — confirmé par grep sur tout l'arbre de composants professions, zéro usage).
- **Une seule URL, deux modes de rendu** — pas de route publique séparée en plus de l'authentifiée : `/metiers/{slug}` sert l'anonyme ET l'authentifié (le flux personnalisé Story 3.12 passe déjà `score`/`confidence`/`signals` en query params depuis `/mes-metiers`, jamais via une session). La présence de `score` dans l'URL distingue "arrivée depuis le flux authentifié" (CTA masqué, lien retour "← Mes métiers") de "visite publique générique" (CTA affiché, lien retour "← Tous les métiers").
- **Bug latent corrigé au passage** : le `notFound()` de la page n'avait pas de `return` après lui (même classe de bug déjà corrigée plusieurs fois cette session, ex. Story 6.3) — un 404 retombait quand même sur le `throw err` suivant. Découvert en écrivant le premier test de cette page (aucun test n'existait avant).
- **Cache CDN (AC2)** : `export const revalidate = 3600` (ISR 1h) — la révalidation à la demande sur signalement (AC "TTL 1h, revalidation On-Demand sur signalement") réutilise le flux `ProfessionReport` existant (Story 3.8) ; câbler un `revalidatePath` sur approbation admin est laissé pour une story de modération future si besoin, différé plutôt que fabriqué sans consommateur.

## 3. Acceptance Criteria

**AC1 — SSR + contenu complet + CTA**
✅ `/metiers/{slug}` accessible sans compte, rendu SSR (confirmé via `curl` sans cookies → 200, HTML complet avec description/journée type/prérequis/parcours visibles), CTA "Crée ton compte pour voir tes chances réelles" affiché pour un visiteur anonyme.

**AC2 — Performance / cache CDN**
✅ `revalidate = 3600`. TTFB/LCP/CLS non mesurés dans ce cycle (Story 7.6 possède l'AC dédié + gate CI Lighthouse) — la page réutilise le même composant `FicheMetier` déjà en prod pour les utilisateurs authentifiés, pas de nouveau poids JS ajouté.

**AC3 — RGAA AA + lisible sans JS**
✅ Rendu SSR Next.js : le HTML complet est envoyé avant hydratation (confirmé par le `curl` brut ci-dessus, sans exécuter de JS). Composants réutilisés tels quels (aucun audit RGAA dédié dans ce cycle — hérité de la conformité déjà établie pour `<FicheMetier>`).

## 4. Fichiers modifiés/créés

**Backend**
- `apps/professions/serializers.py` — `ProfessionPublicSeoSerializer` (new).
- `apps/professions/views.py` — `PublicSeoProfessionDetailView` (new, `AllowAny`).
- `apps/professions/urls.py` — route `public/professions/<slug>/`.
- `scripts/assert_rbac_declared.py` — whitelist `public-seo-detail`.
- `apps/professions/tests/test_endpoints.py` — +6 tests (`TestPublicSeoProfessionDetail`).

**Frontend**
- Déplacé `(authenticated)/metiers/[slug]/{page.tsx,loading.tsx,FicheMetierClient.tsx,__tests__/}` → `metiers/[slug]/` (hors groupe protégé).
- `page.tsx` — `fetchPublicProfession`, CTA conditionnelle, `revalidate=3600`, bug `notFound()` corrigé, nouveau test `page.test.tsx` (3 tests).
- `lib/api/professions.ts` — `fetchPublicProfession`.
- `components/professions/types.ts` — `Profession.id` rendu optionnel.

## 5. Vérifications

- Ruff : 0 erreur.
- Tests backend (Postgres, `postgresql_only`) : `28 passed` (6 nouveaux + 22 existants, aucune régression).
- `manage.py check` : 0 issue. `makemigrations --check` : uniquement la dérive pré-existante `bulletins`.
- `assert_rbac_declared.py` : 288 endpoints (+1).
- Suite backend complète : `1393 passed, 150 skipped` (+6 skip vs Story 6.11, les nouveaux tests `postgresql_only` sont skippés sur la lane SQLite), 0 régression.
- Frontend : 12 tests sur la route déplacée/nouvelle passent ; suite complète `869 passed, 12 failed` (échecs pré-existants non liés) ; `eslint` 0 erreur ; `tsc --noEmit` 0 nouvelle erreur (après purge du cache `.next` stale référençant l'ancien chemin).
- Smoke test Docker live : `curl` anonyme (sans cookie) sur `/metiers/agent-securite-privee` → `200`, HTML complet avec `<title>` correct, CTA présent, "Journée type" visible ; `curl` direct sur `/api/v1/public/professions/agent-securite-privee/` → `200`, champs corrects (`id`/`is_active` absents, `signals_json` présent).
