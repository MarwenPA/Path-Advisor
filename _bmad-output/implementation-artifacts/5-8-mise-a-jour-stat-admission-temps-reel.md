# Story 5.8 : Mise à jour stat admission < 5 min après réponse école

**Status:** done

## 1. User Story

As a élève,
I want voir ma statistique d'admission se mettre à jour rapidement après que l'école a répondu à mon envoi anticipé,
So that mes décisions Parcoursup sont basées sur des données fraîches (FR38 + NFR-P5).

## 2. Scope decisions

- **Propagation synchrone, pas de queue.** L'AC parle d'un "job de propagation" en < 5 min — plutôt que construire une infra de queue/worker pour la satisfaire, `respond_to_outreach_request` (Story 5.7) appelle directement `AdmissionPredictionService.apply_outreach_response_delta` dans le même appel. Un recalcul synchrone en quelques millisecondes satisfait trivialement un NFR de 5 minutes ; ajouter une queue Celery pour ça aurait été de la complexité pure sans bénéfice au volume MVP.
- **Réutilisation quasi totale de l'infra Story 4.2.** `AdmissionStat.previous_proba` existait déjà (capturé par `upsert_stat` à chaque recalcul) et le badge "+N pts" (`<CarteAdmission>`'s `UpdateBadge`, avec animation fade-in + cooldown sessionStorage) était déjà entièrement construit et fonctionnel — cette story n'a eu **aucun** changement frontend à faire sur l'affichage du badge lui-même. Seul le champ `expected_proba` avait besoin d'être nudgé par une action école plutôt que recalculé depuis les bulletins.
- **Un seul nouveau champ** : `AdmissionStat.outreach_delta_applied_at`. Nécessaire car `AdmissionStatView.get()` appelle `upsert_stat()` (recalcul bulletins) à *chaque* requête — sans garde-fou, un élève consultant sa fiche école juste après avoir reçu la notification (le moment le plus probable) verrait son badge "+15 pts" écrasé silencieusement par le recalcul du même GET. La vue saute désormais le recalcul si un delta a été appliqué il y a moins de 24h.
- **Valeurs de points fixes** (pas aléatoires dans la fourchette) : intéressant = +15, entretien = +7, non aligné = -15. Déterministe et testable, tout en respectant les fourchettes de l'épic (+10/+20, +5/+10, -10/-20 respectivement — le "flag entretien" de l'AC est simplement `action == interview_requested`, pas un champ séparé).
- **Notification "École a répondu"** : déjà couverte par l'email `school_responded` de la Story 5.7 — pas de second email dupliqué ici.
- **Bug pré-existant corrigé au passage** : `fetchAdmissionStat()` (frontend) appelait `/api/v1/schools/predict-admission/` — un endpoint qui n'existe pas côté backend (code mort, jamais appelé nulle part avant cette story). Corrigé pour appeler le vrai endpoint `GET /schools/{slug}/admission-stat/`, nécessaire pour que le polling 30s (AC3) fonctionne réellement.
- **Polling 30s** : nouveau `<AdmissionStatPoller>`, ne remplace `<CarteAdmission>` que sur `FicheEcole` variant `expanded` (la fiche détail — les variantes `card`/`compare` dans des listes ne pollent pas, ce serait un poll par carte visible).

## 3. Acceptance Criteria

**AC1 — Recalcul < 5 min**
**Given** une école a répondu
**When** l'événement est mis en queue
**Then** le job de propagation s'exécute en < 5 minutes
**And** ma stat est recalculée (+10/+20, +5/+10 +flag entretien, -10/-20)
→ Implémenté : synchrone, donc instantané (bien en-deçà de 5 min).

**AC2 — Badge 24h**
**Given** la stat a été mise à jour
**When** je vois ma fiche école
**Then** la nouvelle valeur s'affiche avec un badge "+14 pts" visible 24h
**And** une notification m'informe
→ Déjà construit (Story 4.2's `<CarteAdmission>`) ; notification déjà couverte (Story 5.7).

**AC3 — Polling 30s**
**Given** je consulte la fiche école au moment de la mise à jour
**When** le polling 30s détecte le changement
**Then** la valeur se met à jour en place avec une animation discrète
→ Implémenté : `<AdmissionStatPoller>` (nouveau) + fix du endpoint mort `fetchAdmissionStat`.

## 4. Out of scope (deferred)

- Notification push (FR-FF2, fast-follow explicite dans l'épic — email MVP déjà là via 5.7).
- Story 5.9 : badge dans l'historique "Mes envois" (le champ `stat_delta` est déjà exposé par le serializer de réponse depuis cette story, prêt à être consommé).
- WebSocket temps réel (ADD-8 exclut explicitement ça du MVP).

## 5. Review Findings

**Backend :**
- `AdmissionStat.outreach_delta_applied_at` (migration `0007`).
- `AdmissionPredictionService.apply_outreach_response_delta` (nouveau) : nudge deterministe, garde-fou anti-humiliation (5-95%) réutilisé.
- `AdmissionStatView.get()` : saute `upsert_stat()` si un delta a été appliqué il y a moins de 24h.
- `respond_to_outreach_request` (Story 5.7) appelle la propagation ; échec silencieux loggé (la réponse école reste la source de vérité, jamais rollback pour un souci de stat).
- `EarlyOutreachResponseSerializer.stat_delta` (nouveau champ calculé, mapping partagé avec le service).
- **Vérifié :** 6 nouveaux tests service/vue (`test_outreach_stat_propagation.py`) + 3 nouveaux tests d'intégration dans `test_school_response.py`, tous passent SQLite + Postgres réel (les 16 erreurs Postgres rencontrées dans `test_favorites.py`/`test_parcours.py` sont confirmées pré-existantes sur `main`, non liées à cette story — vérifié par `git stash`). Suite complète 1340 passed (0 régression), ruff/`assert_rbac_declared`(271)/`manage.py check`/migrations clean.

**Frontend :**
- `fetchAdmissionStat` corrigé (pointait vers un endpoint 404 inexistant).
- `<AdmissionStatPoller>` (nouveau), intégré dans `FicheEcole` (variant `expanded` uniquement).
- **Vérifié :** 3 nouveaux tests (`AdmissionStatPoller.test.tsx`), 101 tests existants dans `components/schools` inchangés (le remplacement de `<CarteAdmission>` par `<AdmissionStatPoller>` ne change rien au DOM rendu au premier tick), suite complète 816 passed (12 échecs pré-existants non liés), tsc/eslint clean sur les fichiers touchés.

**Smoke test Docker (réel, end-to-end) :** stat baseline créée (32%) → réponse école "intéressant" → stat recalculée à 47% (+15, dans la fourchette +10/+20 de l'épic) → `GET /admission-stat/` renvoie la valeur nudgée sans l'écraser (`updated_recently: true`, `previous_proba: 32`). Données de test nettoyées après vérification.
