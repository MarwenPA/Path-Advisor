# Story 8.1 : Email transactionnel — abstraction Mailpit local + Postmark prod

**Status:** review

## 1. User Story

As a système Path-Advisor,
I want une couche d'abstraction email permettant Mailpit local en PoC et Postmark / SendGrid en production,
So that les notifications email sont opérationnelles partout sans modification de code (NFR-I2).

## 2. État réel de l'existant (inventaire fait AVANT d'écrire cette story)

- **L'abstraction provider existe déjà : c'est `EMAIL_BACKEND` de Django.** `local.py` pointe le SMTP vers Mailpit (conteneur `pa-mailpit`, UI sur 8025 — l'AC2 est déjà vraie aujourd'hui) ; `prod.py`/`staging.py` prennent l'hôte SMTP par variables d'env. Réécrire une hiérarchie `EmailProvider`/`MailpitProvider`/`PostmarkProvider` par-dessus serait réinventer la roue — exactement l'anti-pattern que la brief du projet interdit. **L'AC1 est satisfaite dans son intention** (bascule par env sans changement de code) par : backend Django + ajout d'**anymail[postmark]** comme backend prod nommé, sélectionné par `EMAIL_PROVIDER`.
- **Huit modules envoient des emails**, tous sur le même patron (`render_to_string` ×3 → `EmailMultiAlternatives` → try/except) : `accounts/{tasks,adapters,views}`, `accounts/services/{parental_consent,account_deletion}_email`, `family/services/emails`, `establishments/services/emails`, `outreach/services/early_outreach_email`.
- **Le vrai manque est l'AC3, et il est réel** : le contrat actuel est « best-effort — un échec SMTP ne casse jamais la transaction » avec `except Exception → log.warning → return False`. **Un email peut se perdre silencieusement aujourd'hui** ; rien n'est mis en file, rien n'est rejoué, aucune trace durable au-delà d'un log.
- Celery est en place (beat + tâches dans `accounts/tasks.py`, qui contient déjà une liste soignée d'« exceptions email retryables » vs bugs de programmation — à réutiliser, pas à redécouvrir). `CELERY_TASK_ALWAYS_EAGER=True` en tests.

## 3. Périmètre retenu (décisions explicites)

1. **Nouvelle app `apps.mailer`** (précédent : `apps.telemetry` hier) : modèle `EmailOutbox` (row durable : destinataire, template, contexte JSON, statut queued/sent/failed, tentatives, dernière erreur) + service `send_transactional(...)` + tâche Celery avec **retry exponentiel** (`retry_backoff`, `max_retries`, `acks_late`) ; l'enfilage passe par `transaction.on_commit` pour ne pas courser la ligne.
2. **« Aucun email perdu silencieusement »** = à l'épuisement des retries, la ligne passe `failed` avec l'erreur — visible, requêtable, rejouable (commande `retry_failed_emails`) — et un log `error` (pas `warning`).
3. **Provider prod** : `anymail[postmark]`, activé par `EMAIL_PROVIDER=postmark` (+ `POSTMARK_SERVER_TOKEN`) dans `prod.py` ; défaut inchangé = SMTP (Mailpit en local). `sendBatch` de l'AC : non implémenté — aucun cas d'usage batch n'existe encore (8.5 en aura peut-être) ; consigné comme non-fait plutôt que codé à vide.
4. **Migration des 8 émetteurs** : patron uniforme → migration complète dans cette story (contrairement au cas i18n de 7.7, le volume est borné : 8 modules minces). Le contexte de l'outbox doit être JSON-sérialisable — les appels passent des scalaires/URLs, à vérifier site par site.
5. **RGPD** : l'outbox contient des emails et des contextes potentiellement sensibles (tokens d'invitation) → pas d'API exposée du tout (aucun serializer/view), lecture réservée à l'ORM/admin, et commande `prune_email_outbox` (rétention type 90 j) comme pour la RUM.

## 4. Acceptance Criteria (relues contre l'existant)

**AC1 (intention)** — bascule d'env sans changement de code : backend Django + Postmark via anymail sous `EMAIL_PROVIDER`. ✍️ L'interface littérale `EmailProvider.sendTransactional/sendBatch` n'est PAS créée — Django est l'interface ; le service s'appelle `send_transactional` pour garder le vocabulaire de l'AC.
**AC2** — déjà vraie (Mailpit compose, UI 8025) ; vérifiée live dans cette story (email visible dans Mailpit).
**AC3** — outbox + retry exponentiel + échec final visible et rejouable ; test qui prouve qu'une panne SMTP ne perd pas l'email (la ligne reste `queued/failed`, le retry le délivre après rétablissement).

## 5. Résultats (2026-09-23)

### Deux découvertes d'infrastructure fondamentales, réparées

1. **`path_advisor/__init__.py` était vide** — le câblage Celery-Django canonique n'a jamais existé. L'app Celery configurée (broker Redis, `CELERY_TASK_ALWAYS_EAGER` en tests) n'était chargée que par l'entrypoint worker : partout ailleurs, `shared_task` se liait à l'app par défaut de Celery. Conséquences : l'eager des tests n'a **jamais** réellement fonctionné (les tests existants passent parce qu'ils patchent `.delay` — le commentaire de `test_csv_import` qui affirme le contraire est du folklore) ; et au runtime web, tout `.delay()` publiait vers `amqp://127.0.0.1:5672`, où rien n'écoute. Corrigé (2 lignes canoniques) ; suite complète : **1477 passants, 0 régression** — l'eager désormais actif ne casse rien.
2. **Aucun service `worker` ni `beat` dans le compose** — cohérent avec le point 1 : Celery ne tournait nulle part. Les tâches beat (rappels consentement parental à 04:00, story 1.x) n'ont jamais pu s'exécuter en dev. `pa-worker` et `pa-beat` ajoutés à `infra/docker-compose.yml`.

### Preuve vivante sur infrastructure réelle (pas d'eager)

- **Chemin nominal** : `send_transactional` en shell → ligne 1 `queued` → le **worker** (conteneur séparé, broker Redis réel) la prend → SMTP Mailpit → ligne `sent` (1 tentative), message visible dans l'UI 8025 avec son sujet rendu (« Sarah t'invite à rejoindre Path-Advisor »). AC2 ✓.
- **Panne (AC3)** : Mailpit coupé → envoi → la ligne 2 reste `queued`, tentative 1, **`gaierror` inscrite sur la ligne** — rien de silencieux. Mailpit rétabli → le retry exponentiel planifié livre **seul** : ligne `sent`, tentatives = 2, erreur effacée, message dans Mailpit. Zéro intervention humaine.

### Tests du cœur (9)

Succès→sent ; rollback transactionnel → **aucun email et aucune ligne orpheline** (on_commit) ; contexte non-JSON refusé au call-site ; panne SMTP → Retry levé, tentative et erreur sur la ligne ; épuisement → `failed` bruyant ; bug de programmation (template manquant) → `failed` immédiat **sans** retry ; redélivrance d'une ligne `sent` → no-op (acks_late) ; `retry_failed_emails` rejoue ; `prune_email_outbox` épargne les `queued` (une ligne queued est un email non délivré — la rétention n'a pas le droit d'y toucher).

## 6. Migration des émetteurs (agent) + bug du cœur attrapé par elle

**Neuf émetteurs, pas huit** — l'inventaire initial de cette story avait raté `billing/services/emails.py`. Sept migrés vers `send_transactional` (family, establishments, parental_consent, account_deletion, outreach, billing, + les deux call-sites parental-consent de views/tasks), avec adaptations de contexte JSON-sérialisable (datetimes pré-formatés en fr-FR pour préserver la garantie de locale 1.12 §P21 maintenant que le rendu part dans le worker ; instances de modèles aplaties en dicts calqués sur les lookups des templates — corps byte-identiques).

**Laissés en place, avec raisons** : `accounts/adapters.py` + 3 envois de `views.py` (plomberie allauth — convention de templates `_message.txt` incompatible sans renommage interdit) ; la famille export RGPD de `accounts/tasks.py` — **le mot de passe d'export en clair ne doit jamais être persisté** : une ligne d'outbox le garderait au repos pendant la rétention, strictement pire que le design D1 post-review 1.11. C'est désormais le SEUL émetteur direct hors mailer (grep-vérifié).

**Sémantique assumée et documentée** : la suppression de compte RGPD n'est plus otage du SMTP — l'email de confirmation rejoint la transaction d'effacement et se rejoue, au lieu de bloquer l'effacement.

### Le bug du cœur que la migration a révélé

Ma tâche `deliver_email` avait une branche morte : `self.retry(exc=exc)` fait re-lever l'exception **originale** à l'épuisement — jamais `MaxRetriesExceededError` — donc la transition `FAILED` ne s'exécutait jamais et une ligne épuisée restait `QUEUED` pour toujours, invisible de `retry_failed_emails`. **Mon propre test masquait le bug** en patchant `retry` avec `side_effect=MaxRetriesExceededError` : je testais mon hypothèse, pas Celery (même patron de faux vert que le mock de police en 7.11). Corrigé par un contrôle d'épuisement **avant** l'appel à retry ; le test épingle désormais les vraies sémantiques (`max_retries=0` pinné), et les 6 tests AC3 de la migration sont passés du terminal bogué (`QUEUED`) au terminal correct (`FAILED`).

### Note DPO (à transmettre)

`send_account_deletion_completed_email` persiste l'adresse de l'utilisateur effacé dans `email_outbox` jusqu'à la rétention `prune_email_outbox` — même classe de trace que les logs SMTP, mais à consigner côté conformité.

## 7. Gates finaux

Lane rapide : **1483 passants** (+6 tests AC3, zéro régression sur la baseline 1477) ; lane RLS : **151 passants** (Postgres jetable provisionné comme la CI, la migration `email_outbox` incluse) ; ruff + format propres ; RBAC gate **294 endpoints** ; `mypy apps/mailer` **0 erreur** ; aucune nouvelle erreur mypy sur les apps touchées (diff ligne-à-ligne fait par l'agent sur accounts : jeu d'erreurs identique).


## Amendement post-revue (2026-09-26)

La revue adversariale de l'Epic 8 a corrigé et/ou consigné plusieurs points de cette story — voir `epic-8-review-fixes.md` (lots A→E) pour le détail des décisions qui amendent ce document.
