# Story 6.3 : Frontières confidentialité parent (bulletins + appréciations masqués)

**Status:** done

## 1. User Story

As a système Path-Advisor,
I want garantir que le compte parent n'a aucun accès aux bulletins détaillés ni aux appréciations enseignants de son enfant,
So that la confidentialité de l'élève soit protégée conformément à FR41 et la matrice RBAC.

## 2. Scope decisions

- **AC1 (filtre RBAC bulletins) et l'essentiel d'AC2 (audit) étaient déjà construits** par les Stories 6.1/6.2 — `apps.family.services.parent_view` n'a jamais exposé de champ bulletin/appréciation (chaque endpoint parent utilise un serializer DTO à liste blanche, pas une liste noire), et `get_child_dashboard` logge déjà `record_audit("parent.child_dashboard_viewed", ...)` à chaque accès. Vérifié par les tests existants (`test_parent_view_dashboard.py`, `test_parent_child_detail_views.py`, `test_parent_bulletins_forbidden.py`) — tous passaient déjà avant cette story.
- **Le vrai delta de cette story : AC3 (`CarteAdmission` visible, `action_lever` masqué).** Un choix de revue de code antérieur (2026-08, documenté dans `get_child_ecole_detail`) avait opté pour l'exclusion totale de `AdmissionStat` côté parent — plus conservateur que l'AC de cette story, qui demande explicitement que le parent voie la probabilité ("un résultat dérivé"), seulement pas le levier d'action ("+ 2 points en maths → 58 %", qui nomme une matière et révèle indirectement une note). Cette story inverse ce choix conservateur pour se conformer à l'AC écrit de l'épic — décision documentée dans le code (docstring de `_parent_admission_stat_view`), pas silencieuse.
- **Pas de recalcul.** `get_child_ecole_detail` lit un `AdmissionStat` déjà existant (`.filter(...).first()`) — ne déclenche jamais `upsert_stat()` lui-même, qui nécessiterait des moyennes de bulletins que ce chemin parent-scopé n'a aucune raison de manipuler. Si l'élève n'a jamais consulté sa propre fiche école, `admission_stat` est `null` côté parent aussi.

## 3. Acceptance Criteria

**AC1 — Filtre RBAC**
**Given** la matrice RBAC
**When** un endpoint API retourne des données élève à un parent
**Then** `bulletins_pdf_url`, `bulletins_extracted`, `teacher_appreciations` sont absents
→ Déjà garanti structurellement (Story 6.1/6.2) — vérifié par les tests existants, aucun changement nécessaire.

**AC2 — Audit RGPD**
**Given** un parent accède au profil de son enfant
**When** l'accès a lieu
**Then** un événement est loggué dans `audit_log`
→ Déjà implémenté (`parent.child_dashboard_viewed`, Story 6.2).

**AC3 — `CarteAdmission` visible, levier masqué**
**Given** un parent voit une `CarteAdmission`
**When** la stat est un résultat dérivé
**Then** elle est affichée
**But** `action_lever` est masqué
→ Implémenté cette story : `get_child_ecole_detail` retourne désormais `admission_stat` (tous les champs sauf `action_lever`), le frontend l'affiche via `<CarteAdmission>` avec `action_lever: null`.

## 4. Out of scope (deferred)

- Rien — cette story clôt les 3 ACs de l'épic.

## 5. Review Findings

**Backend :**
- `get_child_ecole_detail` (apps/family/services/parent_view.py) : lit l'`AdmissionStat` existant du (school, student), retourne `admission_stat` via `_parent_admission_stat_view` (nouveau helper, tous les champs sauf `action_lever`).
- `ParentAdmissionStatSerializer` (nouveau) + `ParentEcoleDetailSerializer.admission_stat` (nullable).
- Test existant `test_ecole_detail_returns_school_and_formations` mis à jour (le champ existe désormais, `null` par défaut) + nouveau test `test_ecole_detail_exposes_admission_stat_without_action_lever` (vérifie `expected_proba` présent, `action_lever` absent du payload ET de la string JSON brute).
- **Vérifié :** 52/52 tests `family` (SQLite + Postgres réel), suite complète 1349 passed (0 régression), ruff/`assert_rbac_declared`(274)/`manage.py check`/migrations clean.

**Frontend :**
- `lib/api/parent.ts` : `ParentAdmissionStat` (nouveau type) + `ParentEcoleDetail.admission_stat`.
- `/parent/enfants/[studentId]/ecoles/[slug]` : affiche `<CarteAdmission>` (réutilisé tel quel, `action_lever` forcé à `null` au niveau du mapping) quand `admission_stat` existe. Bug de contrôle de flux pré-existant corrigé au passage (`redirect()`/`notFound()` sans `return` après — même classe de bug déjà rencontrée et corrigée sur d'autres pages cette session).
- **Vérifié :** 4 nouveaux tests (aucun test n'existait pour cette page avant cette story), suite complète 836 passed (12 échecs pré-existants non liés, même chiffre que les stories précédentes), tsc/eslint clean.

**Smoke test Docker (réel) :** `AdmissionStat` créé avec `action_lever` renseigné → `get_child_ecole_detail` + `ParentEcoleDetailSerializer` renvoient `expected_proba=45` mais aucune trace de `action_lever` dans le payload. Données de test nettoyées après vérification.
