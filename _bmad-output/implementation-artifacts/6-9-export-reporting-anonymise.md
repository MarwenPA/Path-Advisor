# Story 6.9 : Export reporting anonymisé cohorte (CSV / PDF)

**Status:** done

## 1. User Story

As a conseillère,
I want exporter un reporting anonymisé de ma cohorte en CSV ou PDF,
So that je puisse partager des stats internes à mon établissement sans exposer des données nominatives (FR45).

## 2. Scope decisions

- **CSV seul** — même résolution que la Story 5.10 ("CSV ou PDF" satisfait par un seul format déterministe, sans dupliquer un moteur PDF pour les mêmes nombres agrégés).
- **Synchrone, pas de job async** — une cohorte plafonne à quelques centaines d'élèves ; l'agrégation réutilisée (`get_cohort_dashboard`, Story 6.6) tourne déjà bien sous la seconde. Aucune queue/worker n'existe ailleurs dans le codebase pour ce type de génération courte (la Story 5.10 est également synchrone) — introduire une queue ici serait de l'infra neuve pour un calcul sub-seconde, pas une réponse proportionnée à "< 30 s".
- **Seuil d'anonymisation k=5** — toute catégorie (`top_metiers`/`distribution_filiere`) avec `count < 5` est repliée dans un bucket "Autres (<5)" plutôt qu'affichée individuellement.
- **Aucune donnée nominative** — l'export ne lit que le dict agrégé déjà retourné par `get_cohort_dashboard` ; `eleves`/`activite_recente` (lignes par élève) sont explicitement exclues du CSV.
- **Traçabilité** — `record_audit` avec `content_hash` (SHA-256 du contenu CSV généré) dans les metadata, action `establishments.cohort_reporting_exported`.

## 3. Acceptance Criteria

**AC1 — Export**
**Given** je suis sur mon `CohortDashboard`
**When** je clique sur "Exporter le reporting"
**Then** un fichier CSV est généré (synchrone, < 30s — voir §2 pour la justification de l'absence de job async)
✅ bouton "Exporter le reporting (CSV)" sur `/cohorte`, `GET /establishments/cohort-dashboard/export.csv/`.

**AC2 — Anonymisation**
**Given** le fichier est généré
**Then** il contient les stats agrégées SANS donnée nominative, seuil k=5 appliqué
✅ `export_cohort_reporting_csv`, `_fold_small_categories`, testé (3 tests dédiés).

**AC3 — Traçabilité**
**Given** l'export est généré
**Then** une trace est ajoutée à `audit_log` avec horodatage et hash du contenu
✅ `record_audit(..., metadata={"content_hash": ...})`, vérifié par test + smoke test Docker.

## 4. Fichiers modifiés/créés

**Backend**
- `apps/establishments/services/cohort_reporting_export.py` (new) — `export_cohort_reporting_csv`, `_fold_small_categories`, `K_ANONYMITY_THRESHOLD`.
- `apps/establishments/counselor_views.py` — `counselor_cohort_reporting_export`.
- `apps/establishments/cohort_urls.py` — route `cohort-dashboard/export.csv/`.
- `apps/establishments/tests/test_cohort_reporting_export.py` (new, 6 tests).

**Frontend**
- `lib/api/cohort-dashboard.ts` — `COHORT_REPORTING_EXPORT_URL`.
- `app/(authenticated)/cohorte/page.tsx` — bouton d'export ajouté.

## 5. Vérifications

- Ruff : 0 erreur.
- Tests SQLite : `6 passed`. Tests Postgres (parité RLS) : `6 passed`.
- `manage.py check` : 0 issue. `assert_rbac_declared.py` : 285 endpoints (+1).
- Suite backend complète : `1387 passed, 144 skipped` (+6 vs Story 6.6), 0 régression.
- Frontend : suite complète `856 passed, 12 failed` (échecs pré-existants non liés), `eslint` 0 erreur.
- Smoke test Docker live : cohorte de 6 élèves (tous filière Générale, tous complétés) → CSV généré avec KPIs corrects, métier au-dessus du seuil affiché directement (count=6≥5), audit log avec `content_hash` de 64 caractères (SHA-256 hex) confirmé — données de test nettoyées après vérification.
