# Story 6.2: Vue parent — métiers explorés, parcours sauvegardés et coûts

**Epic:** 6 — Espaces Tiers : Parent & Conseillère B2B
**Status:** review
**Sprint:** Epic 6
**Story Key:** `6-2-vue-parent-metiers-parcours-couts`
**Estimation:** M (medium) — la brique d'autorisation parent↔élève (`ParentStudentLink`, `IsLinkedParent`) est déjà posée par Story 6.1 ; 6.2 se limite à exposer des endpoints parent-scoped en lecture seule qui réutilisent les services existants (`compute_recommendations` d'Epic 3, `FavoriteSchool`/`School` d'Epic 4) sans nouveau modèle ni migration. Le coût réel est la frontière RBAC (AC3 : bulletins 403 + audit) et la garantie qu'aucun champ bulletin ne fuit dans les réponses parent.

> Story 6.2 implémente **FR41** ("un parent lié peut consulter les métiers explorés + parcours sauvegardés + coûts estimés de son enfant, mais jamais ses bulletins"). Elle dépend entièrement de Story 6.1 (rôle `parent`, `ParentStudentLink`, `IsLinkedParent`) et de la `VISIBILITY_MATRIX["parent"]` (Story 1.9). Elle prépare Story 6.3 (frontière confidentialité renforcée) et Story 6.4 (paiement premium par le parent).

---

## 1. User Story

**As a** parent (M. Martin) lié à un compte élève,
**I want** consulter les métiers que mon enfant a explorés et les parcours qu'il a sauvegardés avec leurs coûts,
**So that** je peux comprendre son cheminement et lui apporter un avis éclairé (FR41).

**Business value:** Transforme le parent en acteur outillé de l'orientation sans compromettre la confidentialité de l'élève. C'est le cœur de la proposition B2C d'Epic 6 côté parent et le préalable à la monétisation par le parent (Story 6.4).

---

## 2. Acceptance Criteria (BDD)

### AC1 — Dashboard parent : 3 sections

**Given** je suis connecté en tant que `parent` lié à un élève et je consulte le dashboard de mon enfant
**When** la page s'affiche
**Then** je vois la section "Métiers explorés" (liste de cartes `ScoreVocationnel` variant `compact`)
**And** je vois la section "Mes paris" de mon enfant (parcours/écoles sauvegardés)
**And** je vois la section "Coûts estimés des parcours sauvegardés" (somme totale + breakdown par école)
**And** l'API `GET /api/v1/family/children/{student_id}/dashboard/` retourne uniquement `metiers_explores`, `mes_paris`, `couts_estimes` (matrice de visibilité `parent`) — jamais de bulletins.

### AC2 — Détail accessible au rôle parent, jamais les bulletins

**Given** je tape sur un métier ou un parcours
**When** la vue détail s'ouvre
**Then** je vois la fiche métier / l'école avec les infos accessibles à mon rôle (données publiques du référentiel + résultats dérivés)
**But** aucune donnée bulletin (`bulletins_pdf_url`, `bulletins_extracted`, `teacher_appreciations`, notes brutes) n'est présente dans la réponse.

### AC3 — RBAC : tentative d'accès aux bulletins → 403 + audit (NFR-S4)

**Given** la matrice RBAC (Story 1.7) et la frontière confidentialité (FR41)
**When** un parent tente d'accéder à une URL exposant les bulletins de son enfant (`GET /api/v1/family/children/{student_id}/bulletins/` ou tout endpoint bulletins élève)
**Then** l'API retourne `403 Forbidden`
**And** l'accès refusé est écrit dans `audit_log` (`action="parent.bulletins_access_denied"`, `subject_id=student.id`).

### AC4 — Autorisation par lien : un parent ne voit QUE ses enfants liés

**Given** je suis `parent` et je tente d'accéder au dashboard d'un élève auquel je ne suis PAS lié (ou lien révoqué)
**When** j'appelle `GET /api/v1/family/children/{other_student_id}/dashboard/`
**Then** l'API retourne `403 Forbidden` (le `ParentStudentLink` non-révoqué est la SEULE source d'autorisation — AC7 de Story 6.1)
**And** le refus est audité (`action="parent.child_access_denied"`).

**Given** je liste mes enfants
**When** j'appelle `GET /api/v1/family/children/`
**Then** je reçois uniquement les élèves auxquels j'ai un lien actif.

### AC5 — Authentification / rôle

**Given** un utilisateur non authentifié
**When** il appelle un endpoint `/api/v1/family/children/...`
**Then** il reçoit `401`/`403`.

**Given** un utilisateur authentifié dont le rôle n'est pas `parent` (ex : `student`)
**When** il appelle ces endpoints
**Then** il reçoit `403 Forbidden` (audité `rbac.access_denied`).

---

## 3. Tasks / Subtasks

- [x] **T1 — Exceptions `apps/api/apps/family/exceptions.py`**
  - [x] T1.1 `ParentNotLinkedToStudent` (403) — parent sans lien actif vers l'élève demandé (AC4)
  - [x] T1.2 `ParentBulletinsForbidden` (403) — frontière bulletins (AC3)

- [x] **T2 — Service `apps/api/apps/family/services/parent_view.py`**
  - [x] T2.1 `get_linked_children(parent) -> list[User]` — élèves liés actifs (bypass_rls pour lire les rows `users` invisibles sous la session RLS du parent)
  - [x] T2.2 `resolve_linked_child(parent, student_id) -> User` — lève `ParentNotLinkedToStudent` + audit `parent.child_access_denied` si pas de lien actif
  - [x] T2.3 `get_child_professions(student) -> list[dict]` — réutilise `compute_recommendations` (Epic 3), mappe vers cartes `ScoreVocationnel` compactes ; dégrade en `[]` si service IA indisponible ; AUCUN champ bulletin exposé
  - [x] T2.4 `get_child_mes_paris(student) -> list[School]` — `FavoriteSchool` de l'élève (Story 4.8)
  - [x] T2.5 `get_child_parcours_costs(student) -> dict` — somme `tuition_min/max_eur` + breakdown par école
  - [x] T2.6 `get_child_dashboard(parent, student_id) -> dict` — orchestre + audit `parent.child_dashboard_viewed`

- [x] **T3 — Endpoints `apps/api/apps/family/views.py` + `urls.py`**
  - [x] T3.1 `GET /api/v1/family/children/` — `[IsAuthenticated, IsParent]`
  - [x] T3.2 `GET /api/v1/family/children/{student_id}/dashboard/` — `[IsAuthenticated, IsParent]`
  - [x] T3.3 `GET /api/v1/family/children/{student_id}/bulletins/` — `[IsAuthenticated, IsParent]` → 403 + audit (AC3)

- [x] **T4 — Serializers `apps/api/apps/family/serializers.py`** (DTO snake_case pour dashboard)

- [x] **T5 — Frontend**
  - [x] T5.1 `apps/web/src/lib/api/parent.ts` — fetchers typés (`fetchLinkedChildren`, `fetchChildDashboard`)
  - [x] T5.2 `apps/web/src/lib/i18n/fr/parent.ts` — dict FR co-localisé
  - [x] T5.3 `apps/web/src/app/(authenticated)/parent/page.tsx` — liste enfants liés
  - [x] T5.4 `apps/web/src/app/(authenticated)/parent/enfants/[studentId]/page.tsx` — dashboard 3 sections
  - [x] T5.5 `apps/web/src/components/features/parent/parent-dashboard.tsx` — réutilise `ScoreVocationnel`
  - [x] T5.6 `apps/web/src/lib/auth/route-guards.ts` — ajout `/parent` → `["parent"]`

- [x] **T6 — Tests backend** (`postgresql_only` + `bypass_rls` pour setup, pattern Story 6.1)
  - [x] T6.1 `test_parent_view_dashboard.py` — parent voit professions + mes-paris + coûts de l'enfant lié
  - [x] T6.2 `test_parent_view_rbac.py` — cross-child 403 + audit ; role non-parent 403 ; non-auth 401/403
  - [x] T6.3 `test_parent_bulletins_forbidden.py` — bulletins 403 + audit ; aucun champ bulletin dans le dashboard

- [x] **T7 — RBAC / ruff / eslint gates**

---

## 4. Dev Notes

### 4.1 — Réutilisation obligatoire (NE PAS réinventer)
- `IsLinkedParent` / `ParentStudentLink` (Story 6.1) = source unique d'autorisation.
- `compute_recommendations` (Epic 3) = données "métiers explorés". Il lit le profil élève et un résumé agrégé des bulletins EN INTERNE mais n'expose AUCUN champ bulletin dans son output (id/slug/name/sector/score/confidence/signals). Frontière AC2/AC3 respectée par construction.
- `FavoriteSchool` + `School.tuition_min/max_eur` (Story 4.8 / 4.1) = "mes paris" + coûts.
- `VISIBILITY_MATRIX["parent"]` (Story 1.9) = source de vérité de ce qui est visible.
- `bypass_rls` (Story 1.8) pour les lectures cross-user légitimes (parent autorisé par lien) — même rationale que `ParentLinkSource` de Story 6.1.

### 4.2 — Frontière bulletins (AC3)
Les endpoints bulletins élève (`apps/bulletins`) sont déjà `[IsAuthenticatedAndActive, IsStudent]` : un parent y reçoit un 403 `wrong_role` audité par `_record_rbac_denial`. Story 6.2 ajoute un endpoint explicite `children/{id}/bulletins/` qui, même pour un parent LIÉ, retourne 403 + audit dédié `parent.bulletins_access_denied` — rend l'invariant testable et lisible. Aucun endpoint parent ne sérialise de champ bulletin.

### 4.3 — "Mes paris" = FavoriteSchool (déviation documentée vs libellé AC1 "ParcoursCard")
Le seul stockage persistant des "paris" de l'élève est `FavoriteSchool` (Story 4.8) — des écoles, pas des graphes de parcours complets (`Parcours` n'est pas sauvegardé par élève). Le backend expose donc les écoles favorites + leurs coûts ; le frontend les rend en cartes école simples (pas `ParcoursCard`, qui exige un objet `Parcours` avec nodes/edges inexistant côté favoris). `ScoreVocationnel` est bien réutilisé pour les métiers. Déviation mineure, fidèle à la donnée réelle.

### 4.4 — RLS
La requête parent traverse le middleware qui pose `app.current_user_id = parent.id`. Les rows enfant (`StudentProfile`, `FavoriteSchool`, `users`) sont invisibles sous cette session. Toutes les lectures de données enfant passent par `bypass_rls(reason="parent_view...")` APRÈS vérification du lien — l'autorisation métier est le lien, pas la RLS.

---

## 5. Out of Scope
- Filtre RBAC field-level renforcé + `CarteAdmission` sans levier d'action → Story 6.3.
- Paiement premium par le parent → Story 6.4.
- Notification "dernière consultation" visible côté élève → Story 6.11.

---

## 6. Dev Agent Record

### Agent Model Used
claude-opus-4 (general-purpose subagent)

### Debug Log References

- `DJANGO_SETTINGS_MODULE=path_advisor.settings.test uv run python manage.py check` → `System check identified no issues (0 silenced).`
- Backend, Postgres CI-parity lane:
  `DJANGO_SETTINGS_MODULE=path_advisor.settings.test_postgres POSTGRES_USER=path_advisor_test POSTGRES_PASSWORD=ci_test_role POSTGRES_DB=path_advisor_test uv run pytest apps/family/tests/test_parent_view_dashboard.py apps/family/tests/test_parent_view_rbac.py apps/family/tests/test_parent_bulletins_forbidden.py -q` → **11 passed**.
- Full family suite (regression): `uv run pytest apps/family/ -q` (postgres lane) → **36 passed** (25 Story 6.1 + 11 Story 6.2), no new failures.
- `uv run ruff check --fix apps/family/` → All checks passed. `uv run ruff format apps/family/` → clean (1 test file reformatted). The `apps/family/** = ["RUF012","DJ001"]` per-file-ignore added in Story 6.1 already covers 6.2.
- `scripts/assert_rbac_declared.py` → the 3 new endpoints (`parent-children-collection`, `parent-child-dashboard`, `parent-child-bulletins`) declare `[IsAuthenticated, IsParent]` and do NOT appear in the failure list. The 13 remaining failures are all pre-existing students/bulletins/schools endpoints (unchanged, out of scope).
- Frontend: `npx eslint` on the 6 new/changed files → clean. `npx tsc --noEmit` → no errors in any parent/route-guards file (the 5 remaining errors are pre-existing in FicheMetier/StatPersonnelle/professions/levels). `npx vitest run src/lib/auth/route-guards.test.ts` → 14 passed (route-guard change is backward-compatible).

### Completion Notes List

- **"Métiers explorés" data source:** there is no persisted `RecommendationScore` / explored-professions model in the repo — recommendations are computed on demand by `compute_recommendations` (Epic 3, calls the AI service). The parent professions endpoint reuses it directly and maps the top-8 to compact `ScoreVocationnel` card DTOs. It degrades to `[]` on `AIServiceUnavailableError` so the dashboard still renders mes-paris + costs. `compute_recommendations` reads a bulletin *summary* internally but returns only id/slug/name/sector/score/confidence/signals — **no bulletin field is ever exposed** (AC2/AC3 satisfied by construction; asserted by `test_dashboard_never_exposes_bulletin_fields`).
- **"Mes paris" = FavoriteSchool (deviation vs AC1 literal "ParcoursCard"):** the only persisted "paris" store is `FavoriteSchool` (schools, Story 4.8), not per-student `Parcours` graphs. The backend returns favorited schools + tuition; the frontend renders them as simple school cost cards (not `ParcoursCard`, which requires a `Parcours` object with nodes/edges that saved favorites do not have). `ScoreVocationnel` IS reused for professions as specified. Documented in §4.3.
- **Costs:** `couts_estimes` sums `School.tuition_min_eur`/`tuition_max_eur` over the child's favorites; a school with unknown tuition contributes 0 to totals but still appears in the breakdown (null tuition).
- **RBAC boundary for bulletins (AC3):** two layers. (1) Existing bulletin endpoints (`apps/bulletins`, `[IsAuthenticatedAndActive, IsStudent]`) already 403 a parent via `wrong_role`, audited by `_record_rbac_denial`. (2) A dedicated `GET /api/v1/family/children/{id}/bulletins/` always 403s — **even a linked parent** — via `deny_bulletins_access`, writing `audit_log` action `parent.bulletins_access_denied`. Proven by `test_parent_bulletins_forbidden.py`.
- **Authorization:** the non-revoked `ParentStudentLink` is the SOLE source (`resolve_linked_child`). No link → 403 + `parent.child_access_denied` audit. Cross-child and revoked-link cases covered by `test_parent_view_rbac.py`.
- **RLS:** all child-data reads (`users`, `student_profiles`, `favorite_schools`) run under `bypass_rls` AFTER the link check, because the parent request session (`app.current_user_id = parent.id`) cannot see the child's rows — same sanctioned rationale as `ParentLinkSource` (Story 6.1). Tests are `postgresql_only` with setup writes wrapped in `bypass_rls`.
- No new model, no migration. No change to the generic RBAC/audit infrastructure.

### File List

**Backend (new):**
- `apps/api/apps/family/services/parent_view.py`
- `apps/api/apps/family/tests/test_parent_view_dashboard.py`
- `apps/api/apps/family/tests/test_parent_view_rbac.py`
- `apps/api/apps/family/tests/test_parent_bulletins_forbidden.py`

**Backend (modified):**
- `apps/api/apps/family/exceptions.py` — `ParentNotLinkedToStudent` (403), `ParentBulletinsForbidden` (403)
- `apps/api/apps/family/serializers.py` — parent dashboard DTO serializers
- `apps/api/apps/family/views.py` — `parent_children_collection`, `parent_child_dashboard`, `parent_child_bulletins_denied`
- `apps/api/apps/family/urls.py` — `children/`, `children/<id>/dashboard/`, `children/<id>/bulletins/`

**Frontend (new):**
- `apps/web/src/lib/api/parent.ts`
- `apps/web/src/lib/i18n/fr/parent.ts`
- `apps/web/src/components/features/parent/parent-dashboard.tsx`
- `apps/web/src/app/(authenticated)/parent/page.tsx`
- `apps/web/src/app/(authenticated)/parent/enfants/[studentId]/page.tsx`

**Frontend (modified):**
- `apps/web/src/lib/auth/route-guards.ts` — `"/parent": ["parent"]` in `ROUTE_ALLOWED_ROLES`

**BMAD artifacts:**
- `_bmad-output/implementation-artifacts/6-2-vue-parent-metiers-parcours-couts.md` — this file

---

## 7. Change Log

| Date | Author | Change |
|---|---|---|
| 2026-08-26 | dev (claude-opus-4) | Story créée + implémentée : endpoints parent-scoped `children/`, `children/{id}/dashboard/`, `children/{id}/bulletins/` (403+audit), service `parent_view` réutilisant `compute_recommendations` + `FavoriteSchool`, frontend dashboard parent réutilisant `ScoreVocationnel`, route-guard `/parent`. Status → review. |
