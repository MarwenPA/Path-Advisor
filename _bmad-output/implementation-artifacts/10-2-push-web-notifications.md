# Story 10.2 — Push web notifications

**Epic 10 — Fast-follow post-MVP · FR-FF2 · Statut : review**

As a élève / parent / conseillère / école, I want recevoir des push web
notifications en plus des emails, So that je sois informé instantanément des
événements critiques (FR-FF2).

## Ce qui est livré

### API
- **`PushSubscription`** (`push_subscriptions`, migrations 0008 + 0009 RLS
  3-branches miroir de `delta_recap_cursors`) : endpoint unique par profil
  navigateur (re-POST = mise à jour, changement de compte = réassignation),
  suppression dure à l'opt-out, **purge auto sur 404/410** du push service.
- **Endpoints** : `POST/DELETE /api/v1/me/push-subscriptions/` (payload
  `PushSubscription.toJSON()`, DELETE idempotent 204) ;
  `GET /api/v1/notifications/push/vapid-public-key/` (204 si non configuré →
  le toggle se cache). Gate RBAC : 321 endpoints verts.
- **Moteur (8.2) étendu** : `notify(..., push={title, body, url})` enfile
  `send_web_push` **sur commit** (`transaction.on_commit`, robust) derrière
  la MÊME porte opt-out que l'email. Sans `push=`, rien ne change.
- **`push.py`** : `deliver_web_push` — re-vérifie l'opt-out à la délivrance
  (miroir de `deliver_email` P2-11), chiffre aes128gcm via pywebpush
  (VAPID RFC 8292), TTL 24 h ; échec = loggé, **jamais rejoué** (l'email est
  le canal durable, pas de double buzz). Tâche `notifications.send_web_push`
  sous `with_system_actor` (whitelist #12 de `core/rls.py`).
- **Événements critiques branchés** (AC1) : réponse école (8.4) et jalons
  Parcoursup (8.3) passent `push=` ; copie **sûre pour écran verrouillé**
  (jamais le nom de l'école dans le push — le téléphone d'un mineur se lit
  par-dessus l'épaule).
- Secrets : `WEBPUSH_VAPID_{PUBLIC,PRIVATE}_KEY` env-only
  (`manage.py generate_vapid_keys`, .env gitignoré / secrets manager —
  jamais commitées) ; clés vides = canal désactivé, emails intacts (NFR-R4).
- Export RGPD : `push_subscriptions` (endpoint + date) ajouté à l'exporteur
  notifications ; suppression compte couverte par CASCADE.

### Web
- **`public/sw.js`** : service worker minimal (push → `showNotification`,
  clic → focus/navigate ou `openWindow`) — pas de cache offline, pas de PWA.
- **`lib/push.ts`** : `enablePush` (clé VAPID via l'API → permission →
  subscribe → POST), `disablePush` (**API d'abord**, puis
  `subscription.unsubscribe()` — aucun push ne peut partir après le resolve,
  AC2), statuts distincts unsupported/unconfigured/denied.
- **`PushToggle`** dans `/parametres/notifications` : état lu du NAVIGATEUR
  (l'abonnement de CET appareil), se cache si non supporté/non configuré,
  permission refusée = retour off + phrase calme, optimiste sans `disabled`
  (P2-8a). RGAA : patron des toggles de catégories.
- Drive-by consigné : `report_updates` manquait à l'union TS
  `NotificationCategory` (catégorie 9.3 déjà servie par le GET).

## Décisions

- **Push = canal secondaire du moteur 8.2**, pas un moteur parallèle : mêmes
  portes (émission + délivrance), l'email reste la garantie de l'AC
  « informé ». Un push raté n'est pas retenté.
- **Opt-in = la ligne `push_subscriptions`** (par appareil), au-dessus des
  préférences par catégorie (globales). Les deux se composent.
- **Clé publique servie par l'API** (pas de `NEXT_PUBLIC_*`) : rotation de
  paire = changement d'env, pas de redeploy front.
- Parent/conseillère/école (AC « tous rôles ») : le canal est neutre au rôle
  (toggle dans Paramètres, table par user) ; seuls les émetteurs critiques
  actuels (réponse école, calendrier) ciblent des élèves — les futurs
  émetteurs passent `push=` et héritent de tout.
- Slack/HTTP proxy du sw : `src/proxy.ts` matche `/sw.js` (il ne fait que
  poser `x-pathname`) — inoffensif, consigné plutôt que touché.

## Résultats

- **Tests** : notifications API **67** (dont 15 nouveaux `test_push.py` +
  1 RLS isolation `push_subscriptions`) ; web **1041** (dont 6 `PushToggle`) ;
  lane RLS locale re-due avant PR ; ruff/mypy zéro nouvelle erreur ;
  `assert_rbac_declared` 321 endpoints.
- **Preuve live** (stack dev, sink HTTP jouant le push service dans le
  conteneur worker, clés navigateur P-256 réelles générées pour la preuve) :
  1. Login réel → `vapid-public-key` 200 → subscribe **201** via l'API.
  2. `notify(push=…)` via le moteur → on_commit → Celery → worker →
     **le sink reçoit** `Authorization: vapid t=eyJ…` (JWT),
     `Content-Encoding: aes128gcm`, `TTL: 86400`, corps 238 o **chiffré**
     (illisible par le relais — conformité mineurs).
  3. Sink passé en **410** → nouvelle livraison → `souscriptions restantes: 0`
     (purge auto, AC2).
  4. Ré-abonnement → **opt-out catégorie via l'API** → `notify` →
     `skipped_opted_out`, **ni email ni push** (sink inchangé).
  5. DELETE abonnement **204** ; préférence restaurée, lignes de preuve
     purgées. Compte de preuve : `sideflow-live-106@test.local`.
- Vérification navigateur réel (permission, affichage de la notification
  système) : non automatisable ici, **à faire en manuel** — consigné.
