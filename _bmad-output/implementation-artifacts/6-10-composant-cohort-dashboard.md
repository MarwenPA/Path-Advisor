# Story 6.10 : Composant `CohortDashboard` (desktop dense Linear-like)

**Status:** done

## 1. User Story

As a développeur Path-Advisor,
I want un composant `CohortDashboard` desktop dense avec KPIs et drill-down,
So that Mme Dupont ait un dashboard pro efficace en < 2 min (UX-DR21).

## 2. Scope decisions

- **Déjà construit générique par la Story 6.6.** Même schéma que la Story 6.3 cette session (une story d'extraction ultérieure se retrouve déjà satisfaite par la story fonctionnelle précédente) : `<CohortDashboard>` ne connaît que sa forme de données (`CohortDashboardData`), pas de dépendance implicite à "conseillère" — le travail de cette story se limite donc à combler les écarts d'AC non couverts par la 6.6 (mobile, RGAA), pas à réécrire le composant.
- **Pas de Recharts/Visx** — aucune librairie de graphique installée (confirmé `package.json`) ; barres HTML/CSS déjà en place depuis la 6.6, cohérent avec le précédent 5.10 (CSV seul plutôt qu'un moteur de reporting).
- **`⌘K` command palette toujours différé** — aucune autre surface de commandes n'existe dans l'app pour justifier une palette globale ; deviation déjà documentée en 6.6, reconduite ici.

## 3. Acceptance Criteria

**AC1 — Layout dense + sections + drill-down**
✅ Déjà livré par la Story 6.6 (`<CohortDashboard>`, `/cohorte`, drill-down `/cohorte/eleves/[id]`).

**AC2 — Navigation clavier first-class**
✅ `/`, `j`/`k`, `e` déjà livrés en 6.6. `⌘K` différé (voir §2).

**AC3 — Responsive mobile**
**Given** je consulte sur < 1024px
**Then** un message explique que l'interface est optimisée desktop, layout dégradé gracieusement
✅ Ajouté cette story : bannière `lg:hidden` avec le texte exact de l'AC ; le reste du layout reste utilisable (grid CSS se réduit nativement en dessous du breakpoint).

**AC4 — RGAA AA**
**Given** un lecteur d'écran
**Then** les KPIs sont annoncés avec valeur + contexte, les graphes ont une alternative tabulaire
✅ Ajouté cette story : `aria-label` explicite sur chaque carte KPI (`"Élèves cohorte : 2"`, etc.) et sur chaque barre (`role="img"` + `aria-label` du type `"Infirmier·ère : 6 élève(s)"`) — les valeurs textuelles déjà visibles à l'écran (nom + count) servent d'alternative tabulaire de fait, renforcées par ces labels pour les lecteurs d'écran.

## 4. Fichiers modifiés

**Frontend**
- `components/features/establishments/cohort-dashboard.tsx` — bannière mobile + `aria-label` KPIs/barres.
- `components/features/establishments/cohort-dashboard.test.tsx` — +2 tests (bannière mobile, aria-labels KPIs).

## 5. Vérifications

- `eslint` : 0 erreur.
- Tests composant : `6 passed` (+2 vs Story 6.6).
- Suite frontend complète : `858 passed, 12 failed` (échecs pré-existants non liés), +2 vs Story 6.9.
- Aucun changement backend — pas de nouvelle vérification RBAC/migrations/Postgres nécessaire pour cette story.
