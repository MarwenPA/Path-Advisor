# Story 6.6 : Dashboard cohorte conseillère B2B

**Status:** done

## 1. User Story

As a conseillère d'orientation (Mme Dupont),
I want consulter un dashboard cohorte de mes élèves avec taux de complétion, métiers les plus explorés, distribution filière,
So that je puisse identifier les tendances et préparer mes entretiens (FR43).

## 2. Scope decisions

- **`<CohortDashboard>` construit générique dès cette story** — anticipant la Story 6.10 ("composant `CohortDashboard` générique"), même schéma que plusieurs stories Epic 5/6 cette session où une story d'extraction ultérieure s'est retrouvée déjà satisfaite par la story fonctionnelle précédente. Le composant ne connaît que sa forme de données (`CohortDashboardData`), pas une dépendance implicite à "conseillère" — réutilisable ailleurs si besoin.
- **Pas de librairie de graphiques** (aucune installée, confirmé via `package.json`) — histogramme/pie rendus en barres HTML/CSS plates, cohérent avec le précédent de la Story 5.10 (export CSV seul plutôt qu'un moteur de reporting).
- **"Métiers les plus explorés" — aucun modèle de tracking de vues/clics n'existe** dans le codebase. Proxy utilisé : le métier recommandé en rang #1 par élève (même moteur IA que `get_child_professions`, réutilisé par la Story 6.8), agrégé par comptage sur la cohorte. Documenté explicitement, pas simulé silencieusement.
- **"Mode dégradé" — aucun flag de ce nom n'existe.** Défini comme `onboarding_step1_status != COMPLETED`, cohérent avec le commentaire déjà présent dans `recommendation_service.compute_recommendations` ("missing profile → empty profile dict sent to ai-service").
- **Un seul dashboard combiné par conseillère**, pas de picker par cohorte — la conseillère voit tous les élèves acceptés de son établissement (`counselor.tenant_id`), toutes cohortes confondues ; l'AC ne demande pas de sélecteur.
- **Raccourcis clavier** : `/` (focus recherche), `j`/`k` (navigation), `e` (ouvrir profil/entretien, Story 6.8) — implémentés. **`⌘K` command palette différé** : aucune autre surface de commandes n'existe encore dans l'app pour justifier une palette générique à ce stade ; déviation documentée, pas un oubli silencieux.

## 3. Acceptance Criteria

**AC1 — Dashboard KPIs + sections**
**Given** je suis connectée en tant que conseillère (MFA validé)
**When** j'arrive sur mon dashboard
**Then** je vois `CohortDashboard` avec KPIs (nb élèves, taux de complétion, nb élèves mode dégradé), "Métiers les plus explorés" (top 10), "Distribution filière", "Activité récente"
✅ `get_cohort_dashboard`, `counselor_cohort_dashboard` view, `/cohorte` page.

**AC2 — Densité desktop + raccourcis**
**Given** densité desktop (écran 27")
**Then** layout dense en grille 2 colonnes, `/`, `j`/`k`, `e` fonctionnels
✅ `<CohortDashboard>` (`⌘K` différé, voir §2).

**AC3 — Drill-down**
**Given** je tape sur une entrée élève
**Then** je vais sur le profil individuel (Story 6.8), gated par le consentement (Story 6.7)
✅ liens `/cohorte/eleves/{id}` + raccourci `e`.

## 4. Fichiers modifiés/créés

**Backend**
- `apps/establishments/services/cohort_dashboard.py` (new) — `get_cohort_dashboard`.
- `apps/establishments/serializers.py` — `CohortDashboardSerializer` + sous-serializers.
- `apps/establishments/counselor_views.py` — `counselor_cohort_dashboard`.
- `apps/establishments/cohort_urls.py` — route `cohort-dashboard/`.
- `apps/establishments/tests/test_cohort_dashboard.py` (new, 3 tests).

**Frontend**
- `lib/api/cohort-dashboard.ts` (new).
- `components/features/establishments/cohort-dashboard.tsx` (new, générique — voir §2) + test (4 tests).
- `app/(authenticated)/cohorte/page.tsx` (new) + test (1 test).

## 5. Vérifications

- Ruff : 0 erreur.
- Tests SQLite : `3 passed`.
- Tests Postgres (parité RLS) : `3 passed` — aucun bug RLS.
- `manage.py check` : 0 issue. `makemigrations --check` : uniquement la dérive pré-existante `bulletins`.
- `assert_rbac_declared.py` : 284 endpoints (+1) passent la gate.
- Suite backend complète : `1381 passed, 144 skipped` (+3 vs Story 6.8), 0 régression.
- Frontend : 5 nouveaux tests passent ; suite complète `856 passed, 12 failed` (échecs pré-existants non liés) ; `eslint` 0 erreur.
- Smoke test Docker live : 2 élèves (1 complété/Générale, 1 en mode dégradé/non renseigné) → KPIs corrects (`nb_eleves=2`, `taux_completion_profil=50.0`, `nb_eleves_mode_degrade=1`), top métiers agrégé via appel réel ai-service, distribution filière correcte — données de test nettoyées après vérification.
