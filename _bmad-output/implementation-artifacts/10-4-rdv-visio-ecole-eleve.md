# Story 10.4 — RDV visio intégré école-élève

**Epic 10 — Fast-follow post-MVP · FR-FF4 · Statut : review**

As a élève premium recevant une demande d'entretien d'une école, I want
prendre un RDV visio directement dans Path-Advisor, So that je n'aie pas à
jongler entre apps externes.

## Ce qui est livré

### API
- **`InterviewMeeting`** (migration 0005) : OneToOne sur la demande, créé
  automatiquement quand l'élève **accepte un créneau** (5.7) — `scheduled_at`
  typé (les slots 5.7 restent des chaînes ISO, consigné ; un slot legacy
  illisible n'empêche pas l'acceptation, warning consigné), `room_slug`
  non devinable (128 bits) → **lien visio Jitsi** via `VISIO_BASE_URL`
  (dev = meet.jit.si, prod = self-hosted, PRD). **Transit only** (AC3) :
  aucun média stocké, et la copie des emails le dit à l'élève (« Aucune
  vidéo n'est enregistrée ni conservée »). Pas de RLS : frontière
  applicative comme tout outreach (deux parties), consigné.
- **Notifications** : confirmation élève via le moteur 8.2 (catégorie
  `school_responses` — l'entretien est la suite d'une réponse école, même
  opt-out ; nouvelle catégorie évitée, consigné) + **push** sobre (jamais le
  nom de l'école sur écran verrouillé) ; l'email école
  `interview_slot_accepted` porte désormais **date (Europe/Paris,
  pré-formatée au queue) + lien visio** — c'est par cet email que l'école
  rejoint (UI école non touchée, consigné).
- **Rappels J-1 / H-1** (AC2) : beat `outreach.send_interview_reminders`
  toutes les 15 min — fenêtres balayées + **claim par UPDATE conditionnel**
  (patron milestone 8.3) plutôt qu'ETA : le broker Redis a un
  `visibility_timeout` de 4 h, un ETA à J-1 serait redélivré. Un RDV pris en
  dernière minute reçoit les deux rappels ; un RDV commencé n'en reçoit
  plus. `bypass_rls` consigné (#7 de la liste nominale).
- Serializer élève : `response.meeting {scheduled_at, visio_url}`.
- **Pas de nouveau gate premium** sur l'acceptation : l'entrée du flux
  (création d'envoi anticipé) est déjà premium — bloquer l'accept d'un
  élève dont l'abonnement vient d'expirer alors que l'école l'a invité
  serait hostile. Consigné.

### Web
- **Mini-calendrier** (AC1) : les créneaux proposés sont groupés par jour
  (titre) avec l'heure en bouton — fuseau **Europe/Paris explicite**
  (l'incohérence 5.7 serveur/navigateur est corrigée au passage sur la
  ligne « créneau accepté »). « Proposer un autre » reste la note libre 5.7
  (une ronde, pas de négociation — périmètre maintenu, consigné).
- **Carte RDV** sur /mes-envois : date, bouton « Rejoindre la visio »
  (nouvel onglet), mention transit-only.
- Type `OutreachResponse` += `meeting` (+ drive-by : `comment_pending`
  manquant depuis 9.4).

## Résultats

- **Tests** : API fast lane **1645** (7 nouveaux `test_interview_meeting`,
  1 test 5.7 mis à jour — l'acceptation envoie désormais 2 emails) ;
  lane RLS locale **156** ; web **31** outreach/mes-envois (nouveau cas
  carte RDV, heure Paris vérifiée 10:00 UTC → 12:00) ; ruff/tsc/eslint
  propres ; mypy 4=4 (zéro nouvelle).
- **Preuve live biface** (stack dev) :
  1. **École en MFA réelle** (school_admin, enrollment TOTP — possible
     grâce au fix 10.1) → propose 2 créneaux dont un à now+90 min.
  2. Élève (login réel, **abonné push** au sink 10.2) → liste → accepte →
     `meeting` exposé avec `https://meet.jit.si/path-advisor-…`.
  3. Mailpit : « Ton entretien avec Aix-Marseille Université est confirmé »
     (lien + mention aucune vidéo) + « Créneau d'entretien accepté » côté
     école (date + lien) ; **push chiffré** reçu au sink.
  4. Beat rappels : run 1 → `24h:1, 1h:0` (RDV à 89 min) ; RDV avancé à
     +50 min → « commence dans une heure » + push ; run 3 → silence
     (claims). **3 pushes** au total (confirmation, J-1, H-1).
  Comptes de preuve conservés : `eleve-visio-104@`/`staff-visio-104@test.local`.
- Champ visio réel (ouvrir meet.jit.si à deux) : vérification manuelle
  recommandée, consigné.
