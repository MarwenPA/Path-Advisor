# Story 8.3 : Notifications calendrier Parcoursup (sans urgence fabriquée)

**Status:** review

## 1. User Story

As a élève (Sarah, Terminale),
I want recevoir des notifications email calées sur le calendrier Parcoursup (ouverture, J-30, résultats),
So that je sois préparée sans angoisse fabriquée (FR47 + UX-DR28).

## 2. Décisions de périmètre

1. **`ParcoursupMilestone`** (app `notifications`) : jalon global — `kind` (enum fermé des 5 jalons AC), `date`, `notify_days_before`, `campaign` (« 2026-2027 »), `notified_at`. **Pas de RLS** : dates publiques de campagne, aucune donnée personnelle. « Configuration admin » = commande `seed_parcoursup_calendar` idempotente (dates de la campagne courante) ; le CRUD admin visuel appartient à l'Epic 9 (consigné, pas escamoté).
2. **Tâche beat quotidienne** `send_parcoursup_milestone_notifications` : jalons dus (`date - notify_days_before == aujourd'hui`, non notifiés) → audience = élèves actifs vérifiés en `lycee_terminale` ou `postbac` (lecture cross-users via **`with_system_actor`**, son usage documenté) → `notify()` par élève — **l'engine 8.2 porte l'opt-out et le footer légal**, cette story n'y touche pas → `notified_at` marqué dans la même transaction que les lignes d'outbox (crash avant commit = rien d'envoyé ni marqué ; après = tout en file durable). Envoi unique par jalon.
3. **Copy anti-urgence exécutable (UX-DR28)** : le ton n'est pas une intention mais un **test** — les 5 jalons rendus (sujet + texte + HTML) passent un lint interdisant les marqueurs d'urgence (« dernière chance », « plus que », « vite », « urgent », « !! », compte à rebours pressant). Posture imposée : « Voici où on en est. Voici ce que tu peux préparer d'ici là », checklist non-bloquante, CTAs calmes (« Revoir mes paris », « Compléter mon profil »).
4. **Un seul triplet de templates** paramétré par jalon (titre/intro/checklist en constantes Python revues d'un seul regard), étendant la base 8.2 — footer légal garanti par construction.

## 3. AC (relues)

**AC1** — email factuel aux Terminale/post-bac quand un jalon approche ; copy sans urgence (testé, pas promis).
**AC2** — les 5 jalons standards notifiés, chacun avec checklist « ce que tu peux préparer ».
**AC3** — lecteur d'écran : pas d'alarmisme, CTAs calmes — même copy texte/HTML, le lint couvre les deux.

## 4. Résultats (2026-09-26)

- **UX-DR28 est un test, pas une promesse** : les 5 jalons rendus (sujet + texte + HTML) passent un lint regex interdisant « dernière chance », « plus que N », « vite », « urgent », « !! », « dépêche », « ne rate pas », « attention ! » — un futur ajout de copy pressant casse la CI. Posture vérifiée (« préparer » présent partout), CTAs bornés à « Revoir mes paris » / « Compléter mon profil ».
- **Deux bugs évités par vérification préalable, pas par chance** : (a) le champ `level` vit sur `StudentLevelProfile` via la chaîne `student_profile__level_profile__level` — un `student_profile__level` naïf aurait silencieusement matché personne ; (b) `User.first_name` **n'existe pas** (minimisation des données, app pour mineurs) — salutation neutre « Bonjour, », la values_list ne demande plus un champ fantôme.
- Dédup par lot : `notified_at` commité **dans la même transaction** que les lignes d'outbox (crash avant commit = rien d'envoyé ni marqué). Second run = 0 envoi, testé.
- Opt-out porté par l'engine 8.2, testé de bout en bout (préférence coupée → 0 email, le lot se termine quand même).
- Audience lue sous `with_system_actor` — l'échappatoire documentée de `core/rls.py` pour les tâches beat.
- **Preuve vivante** : jalon dû créé en base → tâche invoquée par `celery call` (le chemin exact de beat) → exécutée par `pa-worker` → email dans Mailpit (« Parcoursup : la plateforme ouvre le 14 octobre 2026 »), footer légal 8.2 inclus, `notified_at` marqué. Beat planifié à 07:00 dans `celery.py`.
- Gates : lane rapide **1503**, lane RLS **154**, ruff/format propres, `mypy apps/notifications` **0**, RBAC **296**.
- Consigné : le CRUD admin visuel des jalons appartient à l'Epic 9 ; la commande `seed_parcoursup_calendar` (idempotente) tient lieu de « configuration admin » MVP.
