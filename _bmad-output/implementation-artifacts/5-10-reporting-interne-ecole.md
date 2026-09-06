# Story 5.10 : Reporting interne école

**Status:** done

## 1. User Story

As a école partenaire (Mme Garcia),
I want consulter un reporting interne sur les profils reçus, mes actions et les conversions,
So that je peux mesurer l'impact de Path-Advisor sur mon recrutement (FR40).

## 2. Scope decisions

- **"Répartition par région d'origine" — différé.** Aucun champ région/adresse n'existe sur `User` (email + `birth_date` seulement, vérifié). Construire cette collecte de données serait un chantier de profil élève à part entière, hors scope de ce reporting.
- **"Taux de conversion en candidature Parcoursup déclarée" — différé.** Aucun suivi de dépôt de candidature Parcoursup n'existe nulle part dans le code — rien à agréger.
- **Export CSV uniquement, pas PDF.** L'AC dit "CSV ou PDF" — le CSV seul satisfait l'AC telle qu'écrite ; ajouter une lib de génération PDF pour ce MVP n'aurait eu aucun bénéfice supplémentaire.
- **Anonymisation structurelle, pas un filtre.** Le modèle `User` n'a ni prénom ni nom — impossible de faire fuiter une identité nominative dans le reporting agrégé même par erreur. La fiche individuelle (Story 5.6) reste le seul endroit où l'école voit quoi que ce soit sur un élève précis (et là encore : un âge, pas un nom).
- **KPIs livrés** : profils reçus (mois + année), répartition par métier visé, répartition par action prise (intéressant/non aligné/entretien/**pas encore répondu** — ce dernier bucket n'était pas dans l'AC mais c'est un KPI évident pour une école), détail par mois (année en cours).

## 3. Acceptance Criteria

**AC1 — KPIs**
**Given** je vais sur "Reporting"
**When** la page s'affiche
**Then** je vois : nombre profils reçus (mensuel + cumul année), répartition par métier visé, par région d'origine, par action prise, taux de conversion
→ Implémenté (sauf région d'origine et taux de conversion, différés — §2).

**AC2 — Drill down + export**
**Given** je veux explorer en détail
**When** je drill down
**Then** je peux voir le détail par mois, par métier, par profil scolaire
**And** je peux exporter en CSV ou PDF
→ Implémenté : détail par mois + par métier (le "profil scolaire" n'existe pas comme axe de segmentation — aucune donnée académique agrégeable, cf. Story 5.6 §2). Export CSV.

**AC3 — RGPD**
**Given** la conformité RGPD
**When** je consulte le reporting agrégé
**Then** aucune donnée nominative n'est visible
**And** je dois aller sur la fiche individuelle pour voir le nom (avec audit log)
→ Trivialement satisfait : `User` n'a pas de champ nom, et le reporting n'agrège jamais que des compteurs (profession/action/mois), jamais un identifiant élève.

## 4. Out of scope (deferred)

- Répartition par région d'origine (aucune donnée collectée).
- Taux de conversion Parcoursup (aucun tracking de dépôt de candidature).
- Export PDF (CSV suffit à l'AC).
- Drill-down par "profil scolaire" (aucune donnée académique agrégeable côté outreach aujourd'hui).

## 5. Review Findings

**Backend :**
- `apps/outreach/services/school_reporting.py` (nouveau) : `build_school_reporting` (agrégation par métier/action/mois via `annotate`/`Count`/`TruncMonth`), `export_school_reporting_csv`.
- 2 nouveaux endpoints : `GET /ecole/reporting/`, `GET /ecole/reporting/export.csv/` (`IsSchoolAdmin`).
- Aucune requête ne touche la table `users` (filtrage par `school=`/`profession__name`/`response__action` uniquement) — pas de souci RLS à gérer ici, contrairement aux Stories 5.6/5.7.
- **Vérifié :** 6 nouveaux tests, 55/55 tests `outreach` (SQLite + Postgres réel), suite complète 1348 passed (0 régression), ruff/`assert_rbac_declared`(274)/`manage.py check`/migrations clean.

**Frontend :**
- `lib/api/ecole-reporting.ts` (nouveau), page `/ecole/reporting` (nouveau) avec les 3 sections + bouton export CSV (lien direct, pas de fetch — le navigateur gère le téléchargement via `Content-Disposition`).
- Lien "Voir le reporting" ajouté sur `/ecole/outreach`.
- **Vérifié :** 8 nouveaux tests (`ecole/reporting` + non-régression `ecole/outreach`), suite complète 823 passed (12 échecs pré-existants non liés, même chiffre que les stories précédentes), tsc/eslint clean.

**Smoke test Docker (réel) :** 3 profils reçus (1 avec réponse "intéressant", 2 sans réponse) → `build_school_reporting` renvoie les compteurs exacts (3 total, 1 interested / 2 no_response, répartition par métier et par mois correcte) → export CSV généré sans aucune trace d'email/identité élève. Données de test nettoyées après vérification.
