# Story 8.2 : Engine de notifications email avec templates et opt-in

**Status:** review

## 1. User Story

As a élève / parent / conseillère / école,
I want recevoir des notifications email pertinentes que je peux contrôler (opt-in / opt-out par catégorie),
So that je suis informé sans être spammé (FR47).

## 2. Décisions de périmètre (sur inventaire réel)

1. **Nouvelle app `apps.notifications`** : `NotificationPreference` (user × catégorie, `enabled`) — **première table Epic 8 à données personnelles → RLS obligatoire**, politiques calquées sur `students/0001_initial` (SELECT/ALL par `app.current_user_id`, branches `path_admin` + `bypass_rls`). Le lane RLS, désormais requis en CI, vérifie réellement ces politiques — c'est le filet construit en 1.16.
2. **Quatre catégories** (enum fermé, AC) : `parcoursup_calendar`, `school_responses`, `new_schools`, `profile_completion`. **Défaut = activé (modèle opt-out)** : l'AC liste des catégories à « activer/désactiver » et les stories 8.3-8.5 supposent des envois par défaut ; la désinscription doit être un acte, la réinscription aussi (AC3). L'absence de ligne = activé ; une ligne `enabled=False` = désinscrit.
3. **Engine** : `notify(user, category, template_app, template_base, context)` → vérifie la préférence (silencieusement no-op si désinscrit, en le journalisant) → **injecte les liens légaux** (`manage_notifications_url`, `unsubscribe_url` tokenisé) dans le contexte → délègue à `send_transactional` (socle 8.1 : outbox durable, retry). Aucune réinvention d'envoi.
4. **Templates « MJML ou similaire »** : pas de chaîne de build MJML — un **gabarit HTML responsive artisanal** (`notifications/email/base.html`, tables + styles inline, branding sobre R1 Vermillon) que les emails de catégorie étendent, avec footer légal obligatoire (gérer + se désinscrire). « ou similaire » le permet explicitement ; une dépendance de build Node dans le pipeline d'emails Django serait disproportionnée.
5. **Désinscription sans login (obligation légale)** : token **signé** (`django.core.signing`, salt dédié, user+catégorie, sans expiration — un lien de désinscription dans un vieil email doit marcher) → endpoint public `POST /api/v1/notifications/unsubscribe/` (AllowAny → **whitelist RBAC + throttle**, patron consentement parental) qui écrit la préférence via `bypass_rls(reason=...)` — call-site nominatif, conforme au contrat de `core/rls.py`. Page front publique `/desinscription/[token]` (confirmation en un clic, pas de désinscription au simple GET — les préchargeurs d'emails suivent les liens).
6. **API authentifiée** : `GET/PUT /api/v1/me/notification-preferences/` — GET liste les 4 catégories avec état effectif ; PUT upsert par catégorie, sauvegarde immédiate (AC1). Front : nouvelle page `parametres/notifications` (toggles, i18n, RGAA — état non porté par la seule couleur).
7. **Pas d'envoi réel de catégorie dans cette story** : les émetteurs arrivent en 8.3-8.5. L'engine est prouvé par tests + un envoi de démonstration live (Mailpit) via un template de catégorie témoin.

## 3. Acceptance Criteria

**AC1** — table `notification_preferences` ; Paramètres → Notifications : 4 catégories activables/désactivables, sauvegarde immédiate.
**AC2** — emails responsive avec branding sobre + liens « Gérer mes notifications » et « Se désinscrire » dans chaque email de catégorie.
**AC3** — désinscription (page publique tokenisée ou toggle) → plus aucun email de la catégorie sans ré-opt-in explicite ; l'engine le garantit au point d'envoi, pas seulement à l'UI.

## 4. Résultats (2026-09-26)

**Backend** — `apps.notifications` : préférences RLS dès la migration initiale (politiques calquées sur `students/0001`, lane RLS **154 passants** dont mes 3 tests d'isolation avec contrôles positifs) ; engine `notify()` = point d'application unique de l'AC3 avec log observable `skipped_opted_out` ; tokens signés sans expiration ; endpoint public POST-only whitelist é au gate RBAC (**296**), `bypass_rls` à call-site nominatif documenté dans `core/rls.py`. Gabarit email responsive artisanal (base + footer légal impossible à perdre) + template témoin. Lane rapide **1493**, mypy notifications **0**.

**Preuve vivante complète** (infra réelle, worker + broker) : `notify()` → email dans Mailpit avec les deux liens légaux → **token extrait du HTML de l'email lui-même** → POST public sans session → 200 → second `notify()` **refusé par l'engine** (`skipped_opted_out` loggé) → Mailpit toujours à 1 message.

**Frontend** — `/parametres/notifications` (Server Component + liste cliente : bascule optimiste, PUT immédiat, échec → revert + `role="alert"` lié par `aria-describedby` ; switch = checkbox natif `role="switch"`, état porté par la position, jamais la seule couleur) ; page publique `/desinscription/[token]` avec machine d'états confirmer→pending→done|invalide, **POST uniquement au clic** (épinglé par test « zéro appel au mount » + preuve structurelle : la page se rend avec l'API éteinte) ; non-collision avec le `[slug]` racine vérifiée **empiriquement**. i18n `notifications.*` (+28 clés), labels de catégories affichés depuis l'API, pas dupliqués. Web : **983 tests / 124 fichiers** (+7), lint/typecheck/format exit 0, build vert, pages SEO toujours `●`.

## 5. Vérifications prévues (à l'écriture)

Deux lanes (dont politiques RLS de la nouvelle table exercées réellement), gates habituels + RBAC gate (nouvel endpoint AllowAny), preuve vivante Mailpit : email de démo avec footer légal → clic simulé du token → préférence coupée → second envoi bloqué par l'engine (ligne d'audit du no-op).
