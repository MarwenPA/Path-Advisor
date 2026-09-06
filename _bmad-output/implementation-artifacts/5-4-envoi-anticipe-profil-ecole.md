# Story 5.4: Envoi anticipé d'un profil à une école partenaire

**Epic:** 5 — Premium B2C & Envoi Anticipé Biface
**Status:** done
**Story Key:** `5-4-envoi-anticipe-profil-ecole`
**Estimation:** M — nouveau modèle + service + 2 endpoints + UI (bouton + Sheet de confirmation + liste minimale). Pas de nouvelle app école (Story 5.6+) : cette story ne couvre QUE le côté élève.
**Depends on:** 5.2 (`Subscription`/`IsPremium`), 5.3 (`/premium`), 4.4 (`School`), 4.3 (`Parcours`), 3.x (recommandations élève).

> Story 5.4 crée `EarlyOutreachRequest` — le modèle central de tout le reste de l'Epic 5 (5.5 modération, 5.6 réception école, 5.7 réponse école, 5.8 stat temps réel, 5.9 historique enrichi). Cette story ne livre QUE la création côté élève : bouton sur la fiche école, Sheet de confirmation, quota mensuel, audit, et une page "Mes envois" **minimale** (liste avec statut — 5.9 l'enrichira). **Aucun côté école n'existe encore** (Story 5.6 pas commencée) : une demande créée ici reste en `pending` indéfiniment jusqu'à ce que 5.6/5.7 existent — c'est un choix de scope assumé, pas un oubli.

---

## 1. User Story

**As an** élève premium,
**I want** déclencher un envoi anticipé de mon profil à une école partenaire depuis sa fiche,
**So that** je puisse obtenir un signal d'admission précoce plus tard (FR33).

---

## 2. Scope decisions

- **Nouvelle app `apps/outreach`** — `EarlyOutreachRequest` : `id` (pattern `generate_id("reach")`), `student` (FK `User`), `school` (FK `School`), `profession` (FK `professions.Profession`, "métier visé" — choisi par l'élève parmi SES recommandations, pas un choix libre), `parcours` (FK `schools.Parcours`, nullable, résolu **automatiquement côté serveur** — le `Parcours` `is_default=True` pour `(profession, target_school=school)` s'il existe, sinon `null` ; **pas** de sélecteur de parcours côté UI, pour ne pas complexifier le Sheet), `motivation_text` (TextField, blank — champ présent dès maintenant pour éviter une migration Story 5.5, mais **aucune logique de modération** ici : Story 5.5 ajoutera `motivation_status`), `status` (`pending` — seule valeur atteignable tant que 5.6/5.7 n'existent pas ; `responded`/`expired_7d` déjà dans l'enum pour compat), `created_at`.
- **Quota mensuel (AC3)** : 5 envois / mois civil / élève. Vérifié par un `COUNT` sur `EarlyOutreachRequest.objects.filter(student=user, created_at__gte=<premier jour du mois courant>)`. Pas de table de quota séparée — recompté à chaque requête, cohérent avec le faible volume attendu en MVP.
- **Permission** : `[IsAuthenticatedAndActive, IsStudent, IsPremium]` sur l'endpoint de création — la fiche `IsPremium` existe déjà (Story 5.2).
- **Audit** : `@audit_action("early_outreach.created", ...)`.
- **Pas de job Celery de notification à l'école** — il n'y a personne côté école à notifier (Story 5.6 pas commencée). Hors scope explicite ; Story 5.6 branchera la notification quand l'espace école existera.
- **Frontend** :
  - Bouton "Envoyer mon profil à cette école" sur `/schools/[slug]` (fiche école), visible uniquement si `is_premium` (sinon un lien vers `/premium`, pattern `PaywallContextuel` simplifié — le vrai composant est Story 5.11, pas construit ici).
  - Un `Sheet` (mobile) — réutilise `@/components/ui/sheet` déjà utilisé ailleurs — avec : sélecteur du métier visé (liste déroulante des recommandations de l'élève, `fetchRecommendations()`), textarea motivation optionnelle (200-500 mots, compteur — validation de longueur MINIMALE, mais champ optionnel donc 0 mot accepté aussi), puis un second écran de confirmation listant ce qui sera partagé (nom, métier visé, motivation si renseignée — PAS les autres recommandations).
  - Nouvelle page `/mes-envois` — liste simple (école, métier visé, date, statut), pas de groupement par statut ni de fiche détail (Story 5.9). Empty state avec lien vers `/schools`.
  - Message de quota atteint : non-anxiogène, cf. AC3.

## 3. Acceptance Criteria (BDD)

**AC1** — Un élève premium sur `/schools/{slug}` voit le bouton "Envoyer mon profil à cette école" ; un élève freemium voit un lien vers `/premium` à la place.

**AC2** — Cliquer le bouton ouvre un Sheet : choix du métier visé (parmi les recommandations de l'élève), motivation optionnelle, puis un écran de confirmation listant précisément les données partagées. Confirmer crée un `EarlyOutreachRequest(status=pending)`, audite l'action, et redirige vers `/mes-envois`.

**AC3** — Un élève ayant déjà 5 envois ce mois-ci voit, à la place du bouton, un message "Tu as utilisé tes 5 envois ce mois — ta limite repart le 1er du mois prochain" (pas de blocage anxiogène, juste informatif) ; il peut toujours ajouter l'école à ses favoris (`FavoriteSchool`, inchangé).

**AC4** — `/mes-envois` liste tous les envois de l'élève (école, métier visé, date, statut `pending`), triés du plus récent au plus ancien. Vide → empty state avec lien vers `/schools`.

**AC5** — Un élève non-premium qui appelle directement l'endpoint de création (contournement UI) reçoit 403 (`IsPremium`).

## 4. Out of scope (explicite)

- Modération de la motivation (Story 5.5).
- Réception/réponse côté école (Story 5.6/5.7) — le statut reste `pending` pour toujours dans cette story.
- Mise à jour temps réel de la stat d'admission (Story 5.8).
- Historique enrichi / fiche détail (Story 5.9) — `/mes-envois` reste une liste plate.
- Sélecteur de parcours manuel côté UI — résolu automatiquement côté serveur.
- Composant `PaywallContextuel` générique (Story 5.11) — un simple lien conditionnel suffit ici.

## 5. Review Findings

**Implémentation** :
- Backend : nouvelle app `apps/outreach` — `EarlyOutreachRequest` (migration `0001`), service `create_early_outreach_request`/`count_outreach_this_month`, 3 endpoints (`POST /api/v1/schools/{slug}/outreach/`, `GET /api/v1/outreach/requests/`, `GET /api/v1/outreach/quota/`). Gating via `SubscriptionService.require_premium` (402 typé, pas `IsPremium` en `permission_classes` — cf. docstring de cette dernière : les endpoints d'écriture préfèrent le gate service-layer). `parcours` résolu côté serveur (le `Parcours.is_default=True` pour `(profession, target_school=school)` s'il existe), aucun sélecteur manuel côté UI.
- Frontend : `SendOutreachButton` (Sheet 2 écrans : formulaire → confirmation), `OutreachSection` (décide bouton / lien premium / message de quota selon `is_premium`+quota), page `/mes-envois` (liste plate, Story 5.9 l'enrichira), branché sur `/schools/[slug]`.

**Vérification** :
- Backend : 11/11 tests, verts sur SQLite ET Postgres réel. `ruff check .` (repo entier) clean, `assert_rbac_declared.py` : 246 endpoints OK, `makemigrations --check` : aucun drift pour `outreach` (le drift `apps/bulletins` pré-existant, documenté Story 6.5, est sans rapport). Suite complète : 1330 passed / 0 régression.
- Frontend : 15 tests nouveaux (`send-outreach-button`, `outreach-section`, `mes-envois/page`, `route-guards`). `tsc --noEmit`/`eslint` clean. Suite complète : 797 passed / 12 échecs pré-existants sans rapport.
- Smoke test Docker bout en bout avec un vrai compte premium créé à la volée : `POST /api/v1/schools/{slug}/outreach/` → 201, `GET /api/v1/outreach/quota/` → reflète l'usage, `GET /api/v1/outreach/requests/` → liste la demande créée, `/schools/{slug}` → 200, `/mes-envois` → 200 et affiche la demande.

**Non couvert par cette story, hors scope explicite (§4)** : modération motivation (5.5), réception/réponse école (5.6/5.7) — le statut reste `pending` indéfiniment tant que ces stories n'existent pas, mise à jour stat temps réel (5.8), historique enrichi (5.9), composant `PaywallContextuel` générique (5.11 — remplacé ici par un simple lien conditionnel).
