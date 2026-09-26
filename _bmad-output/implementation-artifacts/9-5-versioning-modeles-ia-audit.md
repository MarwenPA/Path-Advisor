# Story 9.5 — Versioning modèles IA + audit trail des décisions

Statut : review · Epic 9 · 2026-09-26

## 1. User Story

As a admin Path-Advisor, I want versionner chaque modèle de recommandation avec son dataset et ses hyperparamètres, et tracer chaque décision de scoring, So that les décisions IA soient auditables et rejouables (RGPD art. 22 + NFR-M3 + ADD-10).

ACs : table `model_versions` (name, version, dataset_hash SHA256, hyperparameters, métriques d'évaluation, deployed_at/by) ; ancien modèle accessible (rollback) ; chaque scoring porte `model_version_id` ; décision rejouable depuis le modèle archivé ; métriques désagrégées par sous-population (cadrage amendé : région/type étab/niveau — PAS de genre) avec alerte si écart > 10 % AVANT déploiement.

## 2. Décisions de périmètre

1. **Le « modèle » d'aujourd'hui est le scorer statistique 3.3** (`0.3.0-statistical`, déjà exposé par l'ai-service dans chaque réponse) : une « version » = le tuple (code du scorer, POIDS des 5 dimensions, dataset de calibration). `hyperparameters_json` = les `_WEIGHTS` ; `dataset_hash` = SHA256 du référentiel de signaux au moment de l'enregistrement. La ligne historique `0.3.0-statistical` est seedée avec `dataset_hash="unversioned-legacy"` (honnête : personne n'a hashé le dataset à l'époque) — les versions suivantes le calculent.
2. **Rejouabilité = registre de poids dans l'ai-service** (`MODEL_REGISTRY`), + paramètre optionnel `model_version` sur `/v1/score-metiers` : un email HTTP par élève reste l'architecture, la version archivée reste servable (l'AC « l'ancien modèle reste accessible en lecture »). Rejouer = renvoyer l'`inputs_snapshot` archivé avec la version archivée et diff-er les sorties (management command `replay_scoring_decision`).
3. **`ScoringDecision`** : journal art. 22 — user, model_version (PROTECT : on ne supprime pas un modèle qui a des décisions), `inputs_snapshot` (le payload EXACT envoyé à l'ai-service), `top_scores` (borné au top 15), created_at. **RLS** (données d'orientation d'un mineur), politiques calquées sur `notification_preferences`. Écrit dans `compute_recommendations` à chaque calcul ; un échec d'écriture ne casse JAMAIS la reco de l'élève (log ERROR — consigné : l'UX prime, l'alerte ops couvre le trou). **Rétention 365 j** (purge beat quotidienne, note DPO : durée d'auditabilité art. 22 choisie à 12 mois).
4. **Sous-populations (cadrage amendé)** : les dimensions RÉELLEMENT présentes côté élève sont `niveau` et `filière` (StudentLevelProfile). Ni région ni type d'établissement n'existent sur le profil élève (le lien élève↔établissement n'est pas encore porté par une story) — consigné : l'audit démarre sur niveau+filière, les autres dimensions s'ajouteront quand la donnée existera. Pas de genre (privacy by construction).
5. **Porte éthique au déploiement** : activer une version dont `evaluation_metrics_json.subpopulations` montre un écart > 10 % entre groupes → refus (409) tant que `ethics_review_note` n'est pas posée par l'admin (l'alerte AVANT déploiement de l'AC) ; l'activation est exclusive (une seule version active) et auditée. Version inconnue remontée par l'ai-service → ligne auto-enregistrée `requires_ethics_review=True` (dérive de config détectée, jamais silencieuse).

## 3. Périmètre technique

- API : `ModelVersion` + `ScoringDecision` (+RLS) ; écriture du journal dans `compute_recommendations` (+ `model_version`/`decision_id` dans la réponse élève) ; admin API list/activate ; command `replay_scoring_decision` ; purge beat ; UI `/admin/modeles`.
- ai-service : `MODEL_REGISTRY`, param `model_version` optionnel, tests.
- Tests : gate éthique 409/activation exclusive, journal écrit avec la bonne version, snapshot suffisant pour rejouer, replay diff OK/KO, RLS isolation, purge, RBAC ; ai-service : version inconnue 422, version archivée servie.

## 4. Résultats (implémentation)

**Livré.**

- **Modèles** : `ModelVersion` (version unique, dataset_hash, hyperparamètres, métriques, activation exclusive, `requires_ethics_review`/note, `baseline_scores` pour 9.6) + `ScoringDecision` (journal art. 22 : user, version PROTECT, `inputs_snapshot` FIDÈLE — profil ET tranche du référentiel au moment de la décision, une fiche éditée en 9.1 ne change pas ce qu'un rejeu recalcule —, top 15 scores avec id+slug). Migrations 0002/0003 : **RLS** sur `scoring_decisions` (3 branches maison) + seed honnête `0.3.0-statistical` (`dataset_hash="unversioned-legacy"`).
- **Journal branché dans `compute_recommendations`** : chaque scoring écrit sa décision et la réponse élève porte `model_version` + `decision_id` ; version inconnue répondue par l'ai-service → ligne auto-enregistrée `requires_ethics_review=True` (dérive de config jamais silencieuse) ; un échec de journalisation ne casse JAMAIS la reco (UX prime, log ERROR — consigné §2.3).
- **ai-service** : `MODEL_REGISTRY` immuable + param `model_version` sur `/v1/score-metiers` (version inconnue → 422) — l'ancien modèle reste servable (rejouabilité + rollback).
- **Gouvernance** : `register_model_version` (SHA256 du référentiel actif) ; `activate_model_version` avec **porte éthique** (écart inter-groupes > 10 % dans `evaluation_metrics.subpopulations` → refus tant qu'aucune note de revue, activation exclusive, tout audité `ml.*`) ; command `replay_scoring_decision` (diff par id, tolérance 0.01) ; purge beat 365 j (note DPO : durée d'auditabilité art. 22 = 12 mois).
- **Sous-populations (cadrage amendé)** : dimensions réelles = niveau + filière ; ni région ni type d'établissement n'existent côté élève — consigné §2.4, pas de genre.
- **Front** : `/admin/modeles` — liste (hash, hyperparamètres dépliables, badge écart %, compteur de décisions), activation directe ou avec note obligatoire selon la porte ; nav +Modèles IA/+Audit ML.
- **Tests** : 8 backend (journal fidèle id+slug+référentiel, version fantôme auto-flaggée, échec journal ⇒ reco servie, hash réel + flag biais au register, gate EthicsGateError puis activation exclusive, API 409→200, 403, purge 365 j) + 3 ai-service (version archivée servie/echo, 422 registre, défaut = courante) + 2 front (badge écart, note obligatoire). Fast lane **1593**, lane RLS **155**, ai-service **71**, RBAC 318.
- **Preuve live** : reco élève réelle → `model_version=0.3.0-statistical` + `decision_id` → `replay_scoring_decision` : **« Rejeu conforme — décision reproductible »** (diffs vides, version archivée) ; register (SHA256 64c) → activate sans note **409** (« Écart inter-groupes de 17 % ») → avec note **200** → 0.3.0 désactivée (exclusivité) → **rollback** vers 0.3.0 **200**.
