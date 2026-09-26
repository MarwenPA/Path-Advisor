# Story 9.6 — Métriques d'audit ML (drift, biais)

Statut : review · Epic 9 · 2026-09-26

## 1. User Story

As a admin Path-Advisor, I want consulter drift, biais par sous-population et distributions de scores, So that je détecte les dégradations du modèle en production (FR52).

ACs : métriques (distribution mensuelle des scores, drift vs baseline par KS-test, distribution par sous-population — cadrage amendé : dimensions existantes, pas de genre) ; drift critique → alerte admin (email + Slack si configuré) + workflow de revue proposé ; écart inter-groupes > 10 % sur métrique critique → alerte + modèle marqué pour revue éthique.

## 2. Décisions de périmètre

1. **Source unique = le journal `ScoringDecision` (9.5)** : la métrique observée est le **score du top 1** de chaque décision (la reco principale montrée à l'élève — c'est elle qui porte l'enjeu). Consigné : ni scipy ni pandas — le KS deux-échantillons est implémenté à la main (max |ΔECDF|, seuil critique 1,36·√((n+m)/nm), α = 0,05) avec un plancher n,m ≥ 50 pour ne pas alerter sur du bruit.
2. **Baseline de drift = capturée sur la version active** : les 500 premiers top-1 postérieurs à son activation, stockés dans `ModelVersion.baseline_scores` (rempli paresseusement par la tâche d'audit dès que ≥ 50 décisions existent). Un rollback (9.5) ramène la baseline de la version réactivée avec lui.
3. **Sous-populations** : moyenne du top-1 par `niveau` et par `filière` sur 30 j, groupes ≥ 30 décisions seulement ; écart relatif max > 10 % ⇒ biais. Mêmes dimensions que 9.5 (cadrage amendé — pas de genre ; région/type-étab inexistants côté élève).
4. **Alertes** : tâche beat hebdomadaire `recommendations.run_ml_audit` (dimanche 05:00 UTC, avant le digest du lundi) sous `with_system_actor` (whitelist `rls.py` mise à jour — leçon de la revue Epic 8). Drift ou biais ⇒ ligne d'audit `ml.audit_alert` + **email aux path_admins actifs** (template ops neutre listant le workflow de revue : réentraîner ? rollback 9.5 ?) ; biais ⇒ en plus `requires_ethics_review=True` sur la version active. **Slack : non câblé, consigné** (aucun webhook Slack n'existe dans l'infra — l'AC dit « si configuré »).
5. Le tableau `/admin/audit-ml` lit un agrégat calculé à la demande (pas de table de métriques matérialisée — le journal 9.5 est la vérité, l'agrégation sur 6 mois reste bon marché à l'échelle MVP ; consigné, à matérialiser si le volume l'exige).

## 3. Périmètre technique

- `apps/recommendations/ml_audit.py` (KS, distributions mensuelles, gaps, baseline) ; tâche beat + alerte email + flag ; `GET /api/v1/admin/ml-audit/` ; UI `/admin/audit-ml` (tuiles, barres CSS, table sous-pops) ; template email ops.
- Tests : KS unitaire (identiques ⇒ calme, décalées ⇒ alerte), gaps, baseline lazy, tâche ⇒ email+flag, API RBAC/forme.

## 4. Résultats (implémentation)

**Livré.**

- **`ml_audit.py`** : KS deux-échantillons maison (max |ΔECDF|, seuil 1,36·√((n+m)/nm), plancher n,m ≥ 50 — jamais d'alerte sur du bruit) ; distributions mensuelles du top-1 (6 mois) ; baseline gelée paresseusement sur la version active (500 premiers top-1 post-activation, jamais réécrite) ; gaps par niveau/filière (groupes ≥ 30, écart relatif > 10 % ⇒ biais).
- **Bug réel attrapé par la preuve live** : le two-pointer KS naïf gonflait D à ~0,5 sur des échantillons IDENTIQUES à ex-aequo massifs (mon test unitaire utilisait un range sans doublons). Fix : consommation des ties des deux côtés avant mesure ; épinglé par `test_ks_handles_massive_ties`.
- **Tâche beat hebdo** `recommendations.run_ml_audit` (dimanche 05:00 UTC, `with_system_actor` whitelisté dans `core/rls.py` #11) : alerte ⇒ ligne d'audit `ml.audit_alert` + email ops aux path_admins actifs (template neutre listant le workflow : consulter /admin/audit-ml, comparer /admin/modeles, réentraîner ou rollback 9.5) ; biais ⇒ `requires_ethics_review=True` sur la version active. Slack non câblé (consigné §2.4). Cas sain : silencieux (testé).
- **API** `GET /admin/ml-audit/` (calcul à la demande — le journal 9.5 est la vérité) ; **UI** `/admin/audit-ml` : chip Sain/Revue requise, tuiles (KS vs seuil, écart max, baseline), barres mensuelles mono-série (labels directs, pas de légende — dataviz), tables par dimension avec effectifs, note de cadrage sous-populations.
- **Tests** : 9 backend (KS identiques/décalées/plancher/**ties**, baseline lazy+gelée, gaps niveau/filière, petits groupes silencieux, tâche ⇒ email+flag+audit, cas sain silencieux, forme API+403) + 2 front (chips alerte/sain, tuiles, table). Fast lane **1601**, lane RLS **155**, web **133 fichiers**, RBAC 319.
- **Preuve live** (beat réel) : seed 40×0,85 (terminale) vs 40×0,55 (postbac) → `run_ml_audit` → baseline capturée (80) → **`bias=True, drift=False`** (le drift=True du 1er run = le bug KS, corrigé puis re-prouvé) → **Mailpit** : « [Path-Advisor ops] Alerte audit ML — modèle 0.3.0-statistical » au path_admin, biais mentionné, drift absent, workflow rollback inclus → `requires_ethics_review=True` posé. Seed purgé après preuve.
