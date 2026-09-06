# Story 5.6 : Espace école partenaire — auth + réception profils

**Status:** done

## 1. User Story

As a école partenaire (Mme Garcia, Polytech Marseille),
I want m'authentifier sur un espace dédié et recevoir les profils élèves envoyés en anticipé,
So that je puisse traiter les candidatures précoces et identifier les profils intéressants (FR35 + FR36).

## 2. Scope decisions

- **Rôle et MFA déjà existants.** `UserRole.SCHOOL_ADMIN` et `IsSchoolAdmin` (avec `requires_mfa_verified=True`) existaient déjà avant cette story (préparés en amont), tout comme `SCHOOL_ADMIN` dans `STAFF_ROLES_REQUIRING_MFA` (Story 1.6). Aucune nouvelle infra auth/MFA n'a été construite — cette story branche `EarlyOutreachRequest` dessus.
- **`SchoolStaff` (nouveau modèle, `apps/schools`)** lie un compte `SCHOOL_ADMIN` à **une seule** école. Créé uniquement via le Django admin par l'équipe Path-Advisor (pas de flow d'invitation self-service) — colle au libellé de l'AC "j'ai été onboardée par l'équipe Path-Advisor" et évite de construire un flow d'onboarding jetable avant que le besoin (plusieurs écoles multi-sites ?) soit confirmé.
- **Frontière RBAC (NFR-S4) structurelle, pas défensive.** `EarlyOutreachRequest` ne stocke déjà pas les autres recos de l'élève ni les autres écoles ciblées (décision de scope de la Story 5.4) — rien à filtrer en plus côté 5.6. Ce que 5.6 apporte : le scoping tenant (une école ne voit que ses propres lignes) + une identité élève minimale (âge, pas nom/email — le modèle `User` n'a d'ailleurs ni prénom ni nom).
- **Pas de score de compatibilité.** Aucun score élève↔école n'existe nulle part dans le code (vérifié). L'AC "score compatibilité école" est explicitement différé — construire un vrai matching serait un chantier à part entière, pas un sous-produit de cette story. Tri disponible : date seulement (`?ordering=`).
- **"Profil scolaire synthétique" réduit à l'âge.** Aucune synthèse académique (bulletins/niveau) n'est encore exposée ailleurs dans le code pour être réutilisée ; construire cette synthèse est le territoire des Epics 2/4, pas de cette story. Seul l'âge (dérivé de `birth_date`) est montré.
- **Lecture seule.** Story 5.7 (les 3 actions de réponse) n'est pas construite ici — 5.6 couvre l'auth + la réception, pas la réponse.
- **RLS + `bypass_rls`.** Une requête école tourne sous `app.current_user_id = <admin>` ; la RLS sur `users` rend la ligne `student` invisible à cette session. Les deux fonctions de lecture (`list_school_outreach_requests`, `get_school_outreach_request`) enveloppent la requête dans `bypass_rls` **après** le scoping `school=` déjà appliqué — l'autorisation métier est "cette ligne appartient à ton école", pas la policy RLS (même rationale que `apps.family.services.parent_view` et `SubscriptionService.process_dunning`).
- **Expiration à J+7 = tâche Celery beat**, suivant le pattern déjà établi (`family.expire_parent_invitations`, `billing.process_dunning`). Seules les requêtes `pending` peuvent expirer — une requête encore `pending_moderation`/`rejected` n'a jamais été visible de l'école, son horloge n'a pas démarré.

## 3. Acceptance Criteria

**AC1 — Auth + MFA**
**Given** je suis admin école partenaire et j'ai été onboardée par l'équipe Path-Advisor
**When** je me connecte à l'espace école
**Then** j'arrive sur un MFA enrollment au premier login
**And** une fois MFA actif, j'arrive sur ma file de réception des profils
→ Déjà couvert par Story 1.6 (SCHOOL_ADMIN est dans `STAFF_ROLES_REQUIRING_MFA`, testé dans `test_mfa_login_flow.py`). `/ecole` redirige vers `/ecole/outreach`.

**AC2 — File de réception**
**Given** ma file de réception
**When** je consulte la liste
**Then** je vois les profils reçus en file (les plus récents en haut), avec métier visé, parcours sélectionné, date réception, statut
**And** je peux filtrer par statut, trier par date
→ Implémenté : `GET /api/v1/ecole/outreach/` (`?status=`, `?ordering=`), page `/ecole/outreach` avec filtres. Pas de tri par score (§2).

**AC3 — Fiche détail**
**Given** je tape sur un profil
**When** la fiche détail s'ouvre
**Then** je vois le profil scolaire synthétique + motivation déclarée + métier visé + parcours envisagé
**But** PAS les autres recos vocationnelles de l'élève, ni les autres écoles ciblées
→ Implémenté : `GET /api/v1/ecole/outreach/{id}/`, page `/ecole/outreach/[id]`. 404 (pas 403) pour une requête d'une autre école ou pas encore modérée — ne confirme pas que l'id existe.

**AC4 — Expiration 7 jours**
**Given** un envoi reçu il y a > 7 jours sans réponse
**When** le statut bascule à `expired_7d`
**Then** l'élève reçoit une notification "L'école n'a pas répondu — stat inchangée"
**And** l'école ne peut plus répondre (entrée archivée)
→ Implémenté : `outreach.expire_stale_requests` (Celery beat, 04:45 quotidien), email dédié. "Ne peut plus répondre" est de facto vrai — 5.7 (réponse) n'est pas construite, donc aucune action n'existe de toute façon.

## 4. Out of scope (deferred)

- Story 5.7 : les 3 actions de réponse école.
- Story 5.8 : mise à jour stat temps réel.
- Story 5.9 : historique enrichi côté élève.
- Story 5.10 : reporting interne école.
- Un vrai score de compatibilité élève↔école (aucune base existante).
- Une synthèse académique complète du profil élève (au-delà de l'âge).
- Un flow d'invitation self-service pour onboarder une école (le Django admin suffit pour le volume MVP).
- Multi-écoles par compte `SCHOOL_ADMIN` (`SchoolStaff` est `OneToOne`).

## 5. Review Findings

**Backend :**
- Nouveau modèle `SchoolStaff` (`apps/schools/models.py`, migration `0006`) — lien 1:1 user↔school, admin Django only (`SchoolStaffAdmin`, `autocomplete_fields`).
- `apps/outreach/services/school_reception.py` (nouveau) : `get_school_for_admin`, `list_school_outreach_requests`, `get_school_outreach_request` — tous scopés + `bypass_rls` documenté.
- `SchoolStaffNotLinked` (403) — défensif si le lien manque.
- 2 nouvelles vues (`EcoleOutreachQueueView`, `EcoleOutreachDetailView`), `IsSchoolAdmin` (déjà existant), nouveaux serializers `EcoleOutreachListSerializer`/`EcoleOutreachDetailSerializer` (âge dérivé, pas d'email/nom).
- `apps/outreach/tasks.py` (nouveau) : `expire_stale_early_outreach_requests`, enregistré dans `path_advisor/celery.py` (04:45 quotidien) + email `outreach_expired`.
- **Vérifié :** 32/32 tests (SQLite + Postgres réel — la 1ère passe Postgres a révélé le piège RLS/JOIN sur `users`, corrigé avec `bypass_rls` avant de re-vérifier), suite complète 1319 passed (0 régression), ruff/`assert_rbac_declared`(262)/`manage.py check` clean, `makemigrations --check` clean.

**Frontend :**
- `lib/api/ecole-outreach.ts` : `fetchEcoleOutreachQueue`, `fetchEcoleOutreachDetail`.
- `/ecole` (redirect) + `/ecole/outreach` (file, filtres statut) + `/ecole/outreach/[id]` (détail) — `ROUTE_ALLOWED_ROLES["/ecole"]` couvrait déjà `school_admin` (déclaré en amont).
- **Vérifié :** 5 nouveaux tests, suite complète 806 passed (12 échecs pré-existants non liés, même chiffre que 5.4/5.5), tsc/eslint clean sur les fichiers touchés.

**Smoke test Docker (réel, end-to-end) :** compte `school_admin` lié à une école via `SchoolStaff`, 3 `EarlyOutreachRequest` créées (1 pour son école, 1 pour une autre école, 1 vieille de 8 jours) → `list_school_outreach_requests` ne retourne QUE les 2 requêtes de sa propre école (confirmé : la requête de l'autre école est invisible) → `expire_stale_early_outreach_requests()` bascule la requête vieille de 8 jours en `expired_7d` (count=1) → email "Pas de réponse de l'école" reçu (vérifié via Mailpit). Test du login complet avec MFA enrollment via curl non refait ici (déjà couvert et testé génériquement par Story 1.6 pour `SCHOOL_ADMIN`). Données de test nettoyées après vérification.
