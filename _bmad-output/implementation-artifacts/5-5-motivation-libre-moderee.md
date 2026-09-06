# Story 5.5 : Motivation libre modérée a priori

**Status:** done

## 1. User Story

As a élève premium,
I want accompagner mon envoi anticipé d'une motivation libre (200-500 mots),
So that je peux contextualiser mon profil au-delà des chiffres scolaires (FR34).

## 2. Scope decisions

- **Statuts ajoutés** à `EarlyOutreachRequestStatus` : `pending_moderation` (motivation soumise, envoi bloqué) et `rejected` (motivation refusée, envoi bloqué, `rejection_reason` renseigné). Pas de statut `approved` séparé — l'approbation ramène simplement la demande à `pending` (l'état "envoyée/visible pour l'école", déjà défini en 5.4).
- **Validation 200-500 mots** appliquée uniquement quand `motivation_text` est non vide — une motivation reste optionnelle (5.4), mais dès qu'un élève en écrit une, elle doit respecter la fourchette. Validée côté serializer (`EarlyOutreachCreateSerializer.validate_motivation_text`), pas côté modèle.
- **Modération = Django admin, pas une API dédiée.** Story 9.4 (back-office admin) est la future maison d'une vraie file de modération ; construire un endpoint API + UI frontend spécifique aujourd'hui serait du travail jetable. `apps/outreach/admin.py` expose : une action bulk "Approuver" (aucune saisie requise) et un lien "Rejeter (raison)" par ligne qui ouvre une page de confirmation demandant une raison obligatoire — mêmes patterns que `AccountDeletionRequestAdmin._dpo_cancel_view` (Story 1.12).
- **Resubmit = un vrai endpoint API** (`POST /outreach/requests/{id}/resubmit/`), parce que c'est un flux élève (self-service), pas un flux admin — remis à `pending_moderation`, revalidé 200-500 mots.
- **Emails transactionnels** : 3 templates (`motivation_pending_moderation`, `motivation_approved`, `motivation_rejected`) suivant le pattern déjà établi dans `apps.accounts.services.account_deletion_email` (`_send()` helper, `fr-FR` locale override, txt+html). Best-effort : un échec SMTP est loggé (`logger.warning(..., exc_info=True)`) mais ne fait jamais échouer la transition de statut déjà persistée.
- **Frontend minimal côté "correction"** : `/mes-envois` affiche `rejection_reason` + un `<ResubmitMotivationForm>` (Sheet-less, inline) pour les demandes `rejected` — pas de nouvelle page dédiée.

## 3. Acceptance Criteria

**AC1 — Saisie**
**Given** je suis dans le flow d'envoi anticipé (Story 5.4)
**When** j'arrive à l'étape "Motivation"
**Then** je peux saisir un texte libre 200-500 mots dans un textarea
**And** un compteur de mots m'aide à respecter la longueur
**And** un placeholder me donne 2-3 suggestions d'angles
→ Implémenté : `<SendOutreachButton>` affiche un compteur de mots (`wordCount`) et un placeholder à 3 angles.

**AC2 — Soumission → modération**
**Given** je soumets ma motivation
**When** le texte est enregistré
**Then** il passe en statut `pending_moderation`
**And** l'envoi à l'école est temporairement bloqué
**And** un email m'informe : "Ta motivation est en cours de relecture (sous 24h ouvrées)"
→ Implémenté : `create_early_outreach_request` bascule en `pending_moderation` dès que `motivation_text` est non vide, envoie l'email correspondant.

**AC3 — Approbation**
**Given** la modération admin approuve la motivation
**When** elle passe en statut `approved`
**Then** l'envoi à l'école est débloqué (→ `pending`)
**And** je reçois une notification "Ton profil est en route vers l'école"
→ Implémenté : `approve_early_outreach_motivation` (action admin), email envoyé.

**AC4 — Refus**
**Given** la modération admin refuse la motivation
**When** elle passe en statut `rejected`
**Then** je reçois un email expliquant le motif et la possibilité de réécrire
**And** l'envoi reste bloqué jusqu'à correction
→ Implémenté : `reject_early_outreach_motivation` (action admin, raison obligatoire), email avec raison, `/mes-envois` affiche `<ResubmitMotivationForm>`.

## 4. Out of scope (deferred)

- Story 9.4 : vraie file de modération back-office (l'admin Django est l'outil intérimaire).
- Story 5.6/5.7 : côté école (réception, réponse).
- Story 5.8 : mise à jour stat temps réel.
- Story 5.9 : historique enrichi (groupement, détail).
- Un job Celery async de modération (l'action admin est synchrone — volume MVP trop faible pour le justifier).

## 5. Review Findings

**Backend :**
- Nouveaux statuts `pending_moderation`/`rejected` + champ `rejection_reason` sur `EarlyOutreachRequest` (migration `0002`).
- `apps/outreach/services/early_outreach_email.py` (nouveau) : 3 emails transactionnels, pattern `account_deletion_email.py`.
- `create_early_outreach_request` : gate moderation + email si motivation non vide.
- `approve_early_outreach_motivation` / `reject_early_outreach_motivation` / `resubmit_early_outreach_motivation` : nouvelles fonctions service, toutes `@audit_action`-décorées, toutes valident la transition d'état (`OutreachModerationStateError` 409 sinon).
- `apps/outreach/admin.py` (nouveau) : admin read-mostly + action bulk "approuver" + vue custom "rejeter" (raison obligatoire) mirror `AccountDeletionRequestAdmin`.
- Nouvel endpoint `POST /outreach/requests/{id}/resubmit/` (`IsStudent`, scope `student=request.user` via `get_object_or_404` → 404 si pas le sien).
- Validation mots 200-500 dans `EarlyOutreachCreateSerializer`/`EarlyOutreachResubmitSerializer`.
- **Vérifié :** 20/20 tests (SQLite + Postgres réel), suite complète 1307 passed (0 régression — écart avec les 1330 de 5.4 dû à l'exclusion d'un fichier de collecte cassé indépendant, `apps/students/tests/test_referentials.py`, pré-existant), ruff clean, `makemigrations --check` clean pour `outreach` (dérive pré-existante `bulletins` non liée), `manage.py check` clean.

**Frontend :**
- `lib/api/outreach.ts` : nouveaux statuts, `rejection_reason`, `resubmitOutreachRequest()`.
- `<SendOutreachButton>` : compteur de mots, note "relecture sous 24h" si motivation présente.
- `<ResubmitMotivationForm>` (nouveau) : affiche le motif de refus + formulaire de réécriture.
- `/mes-envois` : nouveaux libellés de statut, rend `<ResubmitMotivationForm>` pour les demandes `rejected`.
- **Vérifié :** 15 tests outreach (30 avec route-guards/mes-envois), suite complète 801 passed (12 échecs pré-existants non liés, même chiffre qu'en 5.4), tsc/eslint clean sur les fichiers touchés (erreurs tsc pré-existantes ailleurs, non liées).

**Smoke test Docker (réel, end-to-end) :** création avec motivation 250 mots → `pending_moderation` → email "relecture" reçu (Mailpit) → `approve_early_outreach_motivation` → `pending` + email "en route" reçu → 2e demande → `reject_early_outreach_motivation` avec raison → `rejected` + email avec raison reçu. Données de test nettoyées après vérification.
