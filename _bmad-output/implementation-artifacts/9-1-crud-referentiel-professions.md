# Story 9.1 — CRUD référentiel professions

Statut : review · Epic 9 (back-office administration & modération) · 2026-09-26

## 1. User Story

As a admin Path-Advisor (Karim), I want créer, modifier et supprimer des fiches du référentiel professions, So that je maintienne la qualité éditoriale des 50 métiers MVP et l'extension vers 500+ (FR48 + NFR-SC5).

ACs : liste avec recherche/tri/filtre par statut (publié/brouillon/archivé) ; création avec tous les champs ; versionning tracé + rollback ; recalcul lazy des recos impactées ; trace `audit_log` (qui/quoi/quand).

## 2. Décisions de périmètre

1. **Back-office = section `/admin` de l'app Next** (pas le Django admin). Les breadcrumbs du codebase le disent : `route-guards.ts` réserve déjà `/admin` à `path_admin`, la story 3.2 a amorcé l'API admin (`/api/v1/admin/professions/` list+detail read-only), et le 5.5 a explicitement qualifié son écran Django admin d'« interim » en promettant l'UI dédiée à l'Epic 9. Le Django admin reste l'outil break-glass.
2. **Statut éditorial = nouveau champ `status`** (`draft`/`published`/`archived`), avec `is_active` CONSERVÉ et synchronisé (`is_active = status == published` dans `save()`) : les dizaines de requêtes publiques `is_active=True` des epics 3/7/8 restent intactes. Migration de données : `is_active=True → published`, `False → archived`.
3. **« Supprimer » = archiver, jamais de hard delete.** Une profession est référencée par `Parcours`, `ProfessionReport`, les envois anticipés 5.x — un DELETE SQL casserait l'intégrité et effacerait du contexte élève. L'AC parle de suppression ; on livre l'archivage (disparition immédiate de tout le public) + consigne la déviation.
4. **Versionning = `ProfessionRevision`** : un snapshot JSON complet des champs éditoriaux à CHAQUE écriture (création, édition, rollback, changement de statut), avec éditeur et horodatage. Rollback vers la révision N = réapplication du snapshot **qui crée une nouvelle révision** (l'historique ne se réécrit jamais). Patron : `StudentProfileHistory` (2.6).
5. **Audit** : `record_audit(action="referential.profession_*", subject_id, metadata={changed_fields})` — rejoint la transaction de l'écriture (sémantique 1.13 : pas d'audit d'une écriture rollbackée).
6. **Recalcul lazy des recos : conforme PAR CONSTRUCTION.** `RecommendationsView` appelle `compute_recommendations(user)` à chaque requête — rien n'est persisté côté recos vocationnelles. Une fiche modifiée est donc prise en compte à la visite suivante de l'élève sans job ni invalidation. Consigné, pas de machinerie ajoutée.
7. **MFA** : l'AC suppose « MFA validé » — c'est le socle 1.x (OTP middleware) qui le porte ; cette story n'ajoute pas de logique MFA, elle exige `IsPathAdmin` sur toute l'API.
8. **Champs JSON** (`signals_json`, `requirements_json`, `salary_range_json`, `sources_json`, `level_compatibility`) : édités dans l'UI via des éditeurs JSON avec validation de forme côté serializer (types + clés attendues pour `signals_json` — les 3 dimensions du matching 8.5/8.6 en dépendent).

## 3. Périmètre technique

- **API** : `GET /api/v1/admin/professions/` (recherche `q`, `status`, tri, pagination — TOUS statuts) ; `POST` création ; `GET/PATCH /{slug}/` ; `POST /{slug}/archive/` ; `GET /{slug}/revisions/` ; `POST /{slug}/rollback/{revision_id}/`. `IsPathAdmin` partout.
- **Modèles** : `Profession.status` (+ sync `is_active`, data migration) ; `ProfessionRevision` (FK profession CASCADE, snapshot JSON, editor FK SET_NULL, action, created_at). Pas de RLS (référentiel public, pas de donnée perso — même statut que `parcoursup_milestones`).
- **Front** : `(authenticated)/admin/layout.tsx` (nav back-office) ; `/admin/metiers` (table recherche/tri/filtre statut) ; `/admin/metiers/nouveau` ; `/admin/metiers/[slug]` (formulaire complet + panneau historique + rollback). `lib/api/admin-professions.ts`.
- **Tests** : permissions (élève → 403), CRUD, sync `is_active`, révisions à chaque écriture, rollback restaure + nouvelle révision, audit rows, recherche/filtres, archivé invisible du public ; front : liste + formulaire + rollback.

## 4. Résultats (implémentation)

**Livré.**

- **Modèle** : `Profession.status` (draft/published/archived) avec sync `is_active` verrouillée dans `save()` ; migrations 0006 (+`ProfessionRevision`) et 0007 (backfill) ; un writer legacy (`test_early_outreach`) migré vers la nouvelle source de vérité.
- **Service `referential_admin.py`** : create/update/archive/rollback — révision snapshot + `record_audit` dans LA transaction de chaque écriture ; rollback = réapplication en NOUVELLE révision (historique append-only). « Supprimer » = archiver (§2.3, consigné).
- **API** (`IsPathAdmin`, MFA porté par la permission — superuser bypass = break-glass DPO documenté 1.7) : liste tous statuts avec `q`/`status`/`sort` + pagination, POST création, PATCH, `archive/`, `revisions/`, `rollback/{id}/`. Validation de forme sur `signals_json` (les 3 dimensions du matching 8.5/8.6), `level_compatibility`, `requirements_json`, `sources_json`.
- **Front** : layout `/admin` (nav 5 sections, guard `path_admin` existant), `/admin/metiers` (table recherche debouncée/tri/filtre statut/pagination, badges), fiche création + édition avec panneau historique et rollback, champs JSON en éditeurs avec parse-check calme. Namespace `admin` ajouté à `AUTH_ONLY_NAMESPACES` (les pages publiques ne le paient pas — garde perf de la revue Epic 8). `post-login-redirect` commenté : `/admin` est désormais le vrai back-office.
- **Tests** : 10 backend (`test_admin_crud.py`) — 403 élève sur les 7 endpoints, création+sync, brouillon invisible partout (public 404, admin 200), forme `signals_json` rejetée, révision par écriture + audit `changed_fields`, PATCH no-op = zéro révision fantôme, archive, rollback restaure + append + refuse une révision étrangère, liste/recherche/filtres ; 6 front (table statuts/filtre piloté, JSON malformé refusé calmement, PATCH, rollback ciblé sur la révision choisie, archive→liste). API **1560 verts**, web **1011 verts**, ruff/tsc/eslint 0 (sur mes fichiers), RBAC 301.
- **Preuve live** (stack dev) : **flux MFA staff réel** — login → `mfa_enrollment_required` → enroll/start (secret TOTP) → enroll/confirm avec un vrai code calculé (`django_otp.oath`) → session (l'AC « MFA validé » exercé de bout en bout, pas contourné) ; puis cycle complet par l'API : create draft **201** → public **404** → publish → public **200** → edit → revisions `[updated, status_changed, created]` → rollback **200** (salaire 32000 ET statut draft restaurés — snapshot complet) → archive → public **404**. Audit trail : 5 lignes `referential.*` avec acteur et `changed_fields`. SSR `/admin/metiers` **200** en session MFA (chrome complet).
- Consigné : challenge MFA exige `method: "totp"` dans le payload (appris du test 1.6 — la preuve documente le contrat).
