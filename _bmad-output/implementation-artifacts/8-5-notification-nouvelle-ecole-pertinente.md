# Story 8.5 : Notification "nouvelle école pertinente"

**Status:** in-progress

## 1. User Story

As a élève,
I want être notifié quand une nouvelle école / formation pertinente pour mon profil est ajoutée au référentiel,
So that mon graphe de parcours s'enrichit (FR47).

## 2. Décisions de périmètre

1. **Matching local sur les critères 3.3, pas sur le scorer complet** : `compute_recommendations` appelle l'ai-service en HTTP par élève — un batch hebdomadaire dessus coupler ait le digest à la disponibilité de l'ai-service et ferait N appels réseau. L'AC exige « les critères des recos vocationnelles » : ces critères sont les **signaux** (passions/valeurs/spécialités du profil vs `signals_json` du métier). Le digest calcule donc un recouvrement de signaux **en local**, borné aux seuls métiers ciblés par les nouvelles écoles (travail ∝ nouveautés, pas ∝ catalogue). Seuil explicite et testé : `OVERLAP_MIN = 2` recouvrements cumulés sur les trois dimensions.
2. **Digest hebdomadaire strict (AC2)** : beat le lundi 08:00 ; fenêtre = écoles `is_active` créées sur les 7 derniers jours. **Anti-double-envoi par état global** `NewSchoolsDigestRun` (semaine ISO unique) — un re-run manuel ou un retry de la même semaine ne renvoie rien. Limitation assumée : une semaine de panne beat = fenêtre sautée (pas de rattrapage rétroactif) — MVP, consigné.
3. Compteur et exemple dans l'objet (« 5 nouvelles écoles correspondent à ton profil {métier} »), liste bornée à 5 écoles dans le corps, CTA calme « Découvrir ces écoles » → `/schools`. **Ton linté** comme en 8.3/8.4.
4. Opt-out, footer légal, durabilité : portés par l'engine 8.2 / l'outbox 8.1 — zéro logique locale.
5. Le déclencheur « un admin ajoute une école (9.2) » n'existe pas encore — le digest lit `School.created_at`, ce qui couvrira le CRUD 9.2 sans changement.

## 3. Résultats (implémentation)

**Livré.**

- `NewSchoolsDigestRun` (`new_schools_digest_runs`, semaine ISO unique) + migration `notifications.0004` ; tâche `notifications.send_new_schools_digest` (beat lundi 08:00) ; triplet de templates `new_schools_digest{_subject.txt,.txt,.html}` ; accord français par `pluralize`/`pluralize:"ent"` (« 1 nouvelle école correspond… » / « 5 nouvelles écoles correspondent… » — l'exemple de l'AC verbatim).
- Matching : `_signal_overlap` local (passions + valeurs sur `StudentProfile`, spécialités sur `StudentLevelProfile`), `OVERLAP_MIN = 2`, professions résolues via `Parcours` des seules écoles nouvelles. Envoi via `notify()` (opt-out + footer + désinscription signée) → outbox 8.1.
- **Tests** : 7 nouveaux dans `test_new_schools_digest.py` — recouvrement unitaire, groupement AC2 (« 3 nouvelles écoles correspondent » dans UN seul email), re-run même semaine = 0, école de 30 j exclue (semaine quand même marquée), opt-out silencieux, lint de ton paramétré [1, 5] avec assertion d'accord. Fast lane **1516 passed** ; mypy 0 (clés d'index uniformisées `str()` — pk hétérogènes) ; ruff OK ; gate RBAC 296 (aucun endpoint nouveau).
- **Lane RLS** (pgvector jetable, rôle NOSUPERUSER/NOBYPASSRLS) : **154 passed**, migration 0004 appliquée sur Postgres.
- **Preuve live** (stack dev, vrai worker) : seed élève {sciences, autonomie} + école neuve dont le métier porte ces signaux → `celery call notifications.send_new_schools_digest` → worker `queued=1 week=2026-W39` → `mailer.email_sent attempts=1` → **Mailpit** : objet « 1 nouvelle école correspond à ton profil Ingénierie biomédicale », école listée avec ville, CTA `/schools`, footer gérer/désinscription tokenisée. Re-run immédiat : `new_schools_digest_already_ran week=2026-W39`, retour 0 ; en base `2026-W39 | 1`. Piège rejoué : le worker démarré avant l'ajout de la tâche la rejette `unregistered` — restart worker+beat requis après tout ajout de tâche.
- Limitation consignée (§2) : pas de rattrapage rétroactif d'une semaine sautée ; déclencheur admin 9.2 couvert d'avance par `created_at`.


## Amendement post-revue (2026-09-26)

La revue adversariale de l'Epic 8 a corrigé et/ou consigné plusieurs points de cette story — voir `epic-8-review-fixes.md` (lots A→E) pour le détail des décisions qui amendent ce document.
