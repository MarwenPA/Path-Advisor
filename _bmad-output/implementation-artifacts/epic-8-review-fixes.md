# Epic 8 — Correctifs post-revue (lots A→E)

2026-09-26 · branche `fix-epic-8-review` · revue source : artifact « Revue Epic 8 » (5 lentilles adversariales, 37 findings, 1 réfuté).

## Ce qui a été corrigé (par lot)

**A · Fiabilité d'envoi** — claim atomique du jalon 8.3 (`UPDATE … WHERE notified_at IS NULL` en tête de transaction — P0-1, prouvé live : deux runs parallèles → 1 email/destinataire) ; CAS `QUEUED→SENDING` dans `deliver_email` avec `F(attempts)+1` (P1-2a) ; `CELERY_BROKER_TRANSPORT_OPTIONS.visibility_timeout=4h` (P1-2b) ; `sweep_stale_outbox` beat 15 min — orphelins/retries perdus/SENDING crashés (P1-1, prouvé live) ; `on_commit(robust=True)` ; `retry_failed_emails` concurrent-safe ; `autoretry_for` transitoire sur le digest ; docstring backoff honnête (≈2 h) ; log par jalon.

**B · Rétention & effacement** — `mailer.prune_email_outbox` + `telemetry.prune_rum_vitals` en beat quotidien 04:40/04:45 (P0-2 — la promesse « 90 j » de la page RGPD tourne) ; purge `email_outbox` par adresse dans `hard_delete()` (P0-3, Art. 17 — l'email de complétion reste la seule exception, DPO 8.1, bornée par la purge) ; footer légal construit AU RENDU depuis `notification_user_id/category` — token de désinscription plus jamais persisté (P2-6, prouvé live : context 5 clés propres, footer présent dans Mailpit) ; opt-out re-vérifié à la livraison → statut `SKIPPED` (P2-11) ; désinscription post-suppression → 200 idempotent (P2-7) ; exporter RGPD `notifications` (préférences + curseur) ; `last_error` loggé par type seulement.

**C · Produit calendrier** — carte jalon limitée à l'audience 8.3 terminale/post-bac (P1-3, prouvé live seconde/terminale) ; sélection du prochain jalon DANS SA FENÊTRE (P1-4 — le seed réel a deux jalons le même jour) ; jalons à date passée marqués `missed`, jamais envoyés (P1-5) ; stat avant/après filtrée `outreach_delta_applied_at≥since` + body en deux morceaux (`stat_suffix` seulement si la stat est là — P2-1) ; fenêtre du digest ancrée sur le `sent_at` du dernier run (P2-2 — **supersède** la limitation 8.5 §2.2 « semaine sautée perdue » : un run en retard rattrape) ; sujet du digest avec métier seulement s'il est unique ; body carte nouvelles-écoles mentionne les spécialités ; bornes du recap (5 cartes réponse, lookback 90 j) ; recap student-only sans création de curseur pour les autres rôles.

**D · A11y & front** — contrat modal APG complet (piège Tab, scroll-lock, focus restitué à `#accueil-title`, h2, Escape FERME SANS ACKER — décision : Échap = fermer l'onglet, « non-vu = actualité » ; seuls « Tout vu » et les CTA consomment) ; StatChip en sr-only ; garde `Array.isArray` + `error.tsx` global calme ; switch actif pendant le PUT (`aria-busy`) + piste off `control-off` ≈3,9:1 ; `headingLevel` sur FicheEcole (outline réparé) ; timeout 2,5 s + logs sur les fetchs de `/accueil` ; ack `keepalive` + warn ; clamp `daysUntil≤0`.

**E · Gouvernance** — `NUM_PROXIES=1` en prod (bypass XFF du throttle RUM) ; whitelist `with_system_actor` à jour ; listes de ton partagées `apps/notifications/tone.py` (les 4 lints backend importent) + lint front sur fr.json/error.tsx ; chrome `/accueil` + badge CalendarNotification dans fr.json ; catégorie fantôme `profile_completion` masquée du GET + salutation neutralisée ; commentaire « critères 3.3 » honnête ; page RGPD : opt-out dit honnêtement + §5 « journal des emails : 90 j » ; commentaires beat UTC explicites.

## Consignations (décisions actées par ces fixes — amendent les docs de story)

1. **8.2 AC1 amendé** : le réglage n'affiche que les catégories AYANT un émetteur — `profile_completion` masquée jusqu'à son premier sender (PUT l'accepte toujours). Un toggle qui ne pilote rien est une UX malhonnête.
2. **8.5 §2.2 supersédé** : fenêtres du digest contiguës par construction (ancrage sur le dernier run) — une panne beat se rattrape au run suivant au lieu de perdre la semaine.
3. **8.5 audience** : le digest nouvelles-écoles reste TOUS niveaux (exploration sans urgence) là où le calendrier Parcoursup (email 8.3 ET carte 8.6) est terminale/post-bac — décision produit actée ici.
4. **8.6 Escape** : Échap ferme sans consommer (≠ « Tout vu »). Un réflexe Échap ne jette pas un mois de deltas.
5. **8.6 §2.5** : le filtre temporel de la stat promis par le doc existe désormais dans le code (la revue avait trouvé la déviation doc↔code).
6. **Heures beat** : le beat du projet est en UTC (convention existante, cf. 1.12) — jalon 07:00 UTC = 08/09 h Paris, digest lundi 08:00 UTC = 09/10 h Paris. Consigné plutôt que changé : `CELERY_TIMEZONE=Europe/Paris` aurait décalé silencieusement les crons des autres epics.
7. **Fenêtre SMTP irréductible** : un crash entre l'acceptation SMTP et l'UPDATE `sent` peut produire UN doublon au re-queue du sweeper (30 min) — choix at-least-once assumé et loggé `mailer.sending_stale_requeued` (l'inverse = perte silencieuse).
8. **P2-5 consigné sans code** : le commentaire libre d'une école part toujours verbatim dans l'email (modération = Epic 9) ; à terme, le montrer uniquement in-app derrière le CTA après modération.
9. **Points DPO restants** (hors code) : DPA/rétention Postmark ; métier rêvé dans l'objet du digest (conservé — c'est la proposition de valeur ; visible en préversion de boîte) ; capability-URLs des AUTRES flux (consentement, invitations) toujours en context — leurs TTL applicatifs bornent le risque, à revisiter si leur volume croît.
10. **Non traité, volontairement** : landmarks `<main>` imbriqués (transverse pré-existant, candidat story Epic 9+) ; batch complet des `is_enabled` à 10 k élèves (prefetch des opt-outs fait ; le bulk_create outbox reste une optimisation future) ; seed dev `demo` laissé (à l'utilisateur) — `proof-8-6`/`race-proof` purgés.

## Vérifications

Fast lane API **1550 verts** (dont 26 nouveaux `test_review_fixes.py` ×2) ; lane RLS Postgres **155 verts** (migration mailer 0002 incluse) ; web **1005 verts** (127 fichiers, +12 nouveaux) ; mypy 0 ; ruff clean ; tsc 0 ; eslint 0 ; RBAC 298. **Preuves live** : course jalon (2 runs parallèles → 1 email/destinataire, worker logs 2/0 au même horodatage) ; sweeper (orphelin QUEUED-20 min → `requeued_fresh=1` → `email_sent`) ; footer rendu (Mailpit : désinscription+gérer+label présents ; `context` en base : 5 clés, zéro token) ; audience (seconde sans carte jalon, terminale avec) ; 3 tâches beat enregistrées au worker.
