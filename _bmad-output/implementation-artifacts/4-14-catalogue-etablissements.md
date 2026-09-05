# Story 4.14: Catalogue de tous les établissements — miroir du catalogue métiers

**Epic:** 4 — Graphe de Parcours & Stats d'Admission (réouverture ciblée)
**Status:** done
**Story Key:** `4-14-catalogue-etablissements`
**Estimation:** S (small) — mirrors Story 3.13 (catalogue métiers) exactement. Le référentiel `School` (Story 4.1) existe déjà avec 72 établissements riches et seedés (`seed_schools`), la fiche détail `/schools/[slug]` existe déjà (Story 4.4/4.10). Cette story n'ajoute qu'un endpoint de LISTE (jamais créé — seul le detail existait) + une page catalogue + un lien de repli sur `/accueil`.

> Demandé explicitement en session live (2026-09-05), en suite directe de la Story 3.13 : "rajoute un bloc avec mes écoles et la liste des écoles" — même trou que le référentiel métiers avant 3.13.

---

## 1. User Story

**As an** élève ou parent,
**I want** pouvoir parcourir le catalogue complet des établissements du référentiel (pas seulement mes favoris),
**So that** je puisse explorer les écoles disponibles même sans avoir encore de "paris" enregistrés.

---

## 2. Scope decisions

- **Backend** : `School` (72 lignes seedées, `apps/schools/management/commands/seed_schools.py`) a déjà un serializer detail (`SchoolDetailSerializer`) mais aucun endpoint de liste public — seul `AdminSchoolViewSet` (staff) existe. Ajouté :
  - `SchoolCatalogSerializer` — version allégée (id, slug, name, type, city, region, selectivity_index). Ne renvoie PAS `formations`/`admission_stat` (detail-only, N+1/user-spécifique).
  - `SchoolListView` (`GET /api/v1/schools/`), même permission que le detail existant (`IsAuthenticated`), paginé (`_SchoolPagination`, déjà utilisée pour l'admin).
  - Ajouté `"school-list"` à `_ISAUTHENTICATED_ONLY_WHITELIST` dans `assert_rbac_declared.py` (même rationale que l'entrée pré-existante `"school-detail"` : donnée de référence publique, pas de restriction de rôle par design).
- **Frontend** :
  - `fetchSchools()` dans `lib/api/schools.ts`.
  - Nouvelle page `apps/web/src/app/(authenticated)/schools/page.tsx` — grille de cartes (nom, type, ville, sélectivité), chaque carte `<Link href="/schools/{slug}">` vers la fiche détail existante. `/schools` déjà dans `ROUTE_ALLOWED_ROLES` (`["student", "parent"]`), pas de nouvelle entrée.
  - `apps/web/src/app/(authenticated)/accueil/page.tsx` — nouveau module "Tes écoles" (miroir de "Tes métiers"), lien persistant "Voir la liste des établissements" → `/schools`. Voir Story 8.8 §Change Log pour l'historique complet des itérations de layout de `/accueil` qui ont suivi cette story.
  - Pas de nouvel item de nav — même raisonnement que 3-13 (repli contextuel, pas une section de premier plan).

## 3. Acceptance Criteria

**AC1** — `GET /api/v1/schools/` (authentifié) retourne les établissements, paginés, triés par nom.
**AC2** — `/schools` affiche une grille de toutes les fiches (nom + type + ville + sélectivité), chaque carte cliquable vers `/schools/{slug}` (fiche détail inchangée).
**AC3** — Sur `/accueil`, un lien "Voir la liste des établissements" est toujours visible (module "Tes écoles").

## 4. Out of scope (explicite)

- Filtres/recherche dans le catalogue.
- Nouvel item de nav pour `/schools`.

## 5. Review Findings

**Bug pré-existant trouvé et corrigé en cours de route** : `apps/schools/tests/test_endpoints.py`'s `student_user`/`admin_user` fixtures n'étaient pas wrappées en `bypass_rls()` — chaque test échouait dès le setup contre un vrai rôle Postgres NOSUPERUSER. Corrigé (même pattern que le fix RLS déjà appliqué à `apps/professions/tests/test_endpoints.py`, Story 3.13) — 23/23 tests passent maintenant sur Postgres réel.

**Vérification** :
- Backend : `SchoolListView` — 3 nouveaux tests (200 pour student, exclut les champs detail-only, 401 anonyme) + les tests pré-existants, tous verts sur Postgres réel. `assert_rbac_declared.py` : 243 endpoints OK. `ruff check` clean.
- Frontend : 3 tests dédiés (`schools/page.test.tsx`) + 1 test accueil (`Tes écoles` link). `tsc --noEmit`/`eslint` clean. 760 passed / 12 échecs pré-existants sans rapport.
- Smoke test Docker : `seed_schools` déjà exécuté en local (72 écoles) ; `/schools` → 200, 72 cartes ; `/accueil` → 200, lien "Voir la liste des établissements" présent.

**Reporté explicitement par l'utilisateur** : rien — c'était le point différé de la Story 3.13, maintenant traité.
