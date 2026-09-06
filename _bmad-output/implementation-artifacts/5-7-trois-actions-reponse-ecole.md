# Story 5.7 : 3 actions de réponse école

**Status:** done

## 1. User Story

As a école partenaire,
I want répondre à un envoi anticipé via 3 actions explicites (Profil intéressant / Profil non aligné / Demande d'entretien),
So that je donne un signal clair à l'élève qui ajuste ses chances d'admission (FR37).

## 2. Scope decisions

- **Nouveau modèle `EarlyOutreachResponse`** (1:1 avec `EarlyOutreachRequest`) : `action` (3 choix), `comment` (≤200 mots), et pour `interview_requested` uniquement : `proposed_slots` (2-3 ISO datetimes), `accepted_slot`, `alternative_note`.
- **Le commentaire n'est PAS gaté par la modération a priori** que la Story 5.5 a construite pour la motivation élève. Le message d'une école doit atteindre l'élève rapidement (la promesse "5 min" de l'épic elle-même), et la surface d'abus est bien plus faible (quelques dizaines de comptes école onboardés manuellement, vs. des milliers d'élèves). Visibilité a posteriori pour un `path_admin` via le Django admin (lecture seule) si jamais un signalement arrive.
- **Pas de propagation de stat.** L'épic donne des valeurs précises (+10/+20, +5/+10, -10/-20 points) — c'est explicitement le travail de la Story 5.8, pas de celui-ci. Cette story enregistre la réponse et notifie l'élève qu'une réponse est arrivée ; le badge "+14 pts" n'existe pas encore.
- **Pas de `ConsentDialog` générique** pour "Profil non aligné" — une étape de confirmation inline avec le rappel de ton respectueux + template suggéré, même pattern de réduction de scope que le Sheet de la Story 5.4 (pas de composant générique construit avant que le besoin soit confirmé ailleurs).
- **Entretien : un seul aller-retour.** L'élève accepte un créneau OU propose une alternative en texte libre — pas de boucle de négociation multi-tours. L'école recontacte ensuite en externe (cohérent avec le "visio externe en MVP" de l'épic elle-même).
- **RLS.** `respond_to_outreach_request` s'exécute déjà dans le contexte `bypass_rls` établi par `get_school_outreach_request` (Story 5.6) — mais le respond-view devait re-fetch via ce même service après la mutation plutôt qu'un simple `refresh_from_db()`, qui vide le cache FK `student` et refait une requête hors bypass (bloquée par la RLS côté Postgres — détecté par le passage Postgres, pas SQLite). Le fan-out d'emails vers le staff d'une école (`_notify_school_staff`, appelé depuis une requête élève) a la même exigence de `bypass_rls`.

## 3. Acceptance Criteria

**AC1 — Les 3 actions**
**Given** je suis sur une fiche profil élève
**When** je veux répondre
**Then** je vois 3 boutons : "Profil intéressant" (primary), "Profil non aligné" (secondary), "Demande d'entretien" (tertiary, icône calendrier)
**And** un champ optionnel "Commentaire pour l'élève" (max 200 mots)
→ Implémenté : `<EcoleRespondForm>` sur `/ecole/outreach/[id]`.

**AC2 — "Profil intéressant"**
**Given** je choisis "Profil intéressant"
**When** je confirme
**Then** la réponse est enregistrée + événement "mis en queue" pour 5.8
**And** un toast confirme l'envoi
→ Implémenté (le "toast" est géré côté client après le 201 ; l'"event queue" pour 5.8 est le futur consommateur de `EarlyOutreachResponse`, pas construit ici).

**AC3 — "Profil non aligné"**
**Given** je choisis "Profil non aligné"
**When** je confirme
**Then** un rappel du ton respectueux + template suggéré
→ Implémenté : étape de confirmation inline avec le texte exact de l'épic pré-rempli.

**AC4 — "Demande d'entretien"**
**Given** je choisis "Demande d'entretien"
**When** je confirme
**Then** je propose 2-3 créneaux ; l'élève reçoit la proposition et peut accepter/proposer un autre créneau
→ Implémenté : validation 2-3 créneaux, `<InterviewResponseForm>` côté élève sur `/mes-envois` (accepter ou texte libre alternatif).

## 4. Out of scope (deferred)

- Story 5.8 : propagation de la réponse vers la stat d'admission (points, badge).
- Story 5.9 : historique enrichi (détail dédié, groupement par statut).
- Story 5.10 : reporting interne école.
- Story 5.12 : `EcoleResponseFlow` générique réutilisable (implémenté ici inline, pas comme composant partagé).
- Négociation multi-tours sur les créneaux d'entretien.
- Modération a priori du commentaire école (reactive via Django admin seulement).

## 5. Review Findings

**Backend :**
- Nouveau modèle `EarlyOutreachResponse` (migration `0003`), nouvelles exceptions (`OutreachAlreadyResponded` 409, `InterviewSlotNotProposed` 400, `NoInterviewToRespondTo` 409).
- `apps/outreach/services/school_response.py` (nouveau) : `respond_to_outreach_request`, `accept_interview_slot`, `propose_interview_alternative` — tous audit-décorés, tous valident leur transition d'état.
- 3 nouveaux endpoints : `POST /ecole/outreach/{id}/respond/`, `POST /outreach/requests/{id}/interview/accept/`, `POST /outreach/requests/{id}/interview/alternative/`.
- 3 nouveaux templates email + admin read-only pour `EarlyOutreachResponse`.
- **Bug RLS réel détecté et corrigé** lors du passage Postgres : `refresh_from_db()` après une réponse école videait le cache `student` (chargé sous `bypass_rls`), forçant une requête hors bypass que la RLS vide silencieusement pour une session école. Corrigé en re-fetchant via `get_school_outreach_request` (déjà `bypass_rls`-wrapped) au lieu de `refresh_from_db()`.
- **Vérifié :** 44/44 tests (SQLite + Postgres réel, bug RLS ci-dessus détecté puis corrigé), suite complète 1331 passed (0 régression), ruff/`assert_rbac_declared`(271)/`manage.py check`/migrations clean.

**Frontend :**
- `lib/api/ecole-outreach.ts` (+`respondToOutreachRequest`), `lib/api/outreach.ts` (+`acceptInterviewSlot`/`proposeInterviewAlternative`).
- `<EcoleRespondForm>` (nouveau, sur `/ecole/outreach/[id]`) : 3 boutons + commentaire + étape de confirmation "non aligné" + saisie de créneaux.
- `<InterviewResponseForm>` (nouveau, sur `/mes-envois`) : accepter un créneau ou proposer une alternative.
- **Vérifié :** 27 tests dans `outreach`+`mes-envois`+`ecole` (9 nouveaux), suite complète 813 passed (12 échecs pré-existants non liés, même chiffre que les stories précédentes), tsc/eslint clean sur les fichiers touchés.

**Smoke test Docker (réel, end-to-end) :** réponse "demande d'entretien" avec 2 créneaux + commentaire → email reçu par l'élève (Mailpit) → acceptation d'un créneau côté élève → email reçu par l'école admin (Mailpit) → `accepted_slot` correctement enregistré. Données de test nettoyées après vérification.
