# Story 10.1 — Détection profils à risque (dashboard conseillère)

**Epic 10 — Fast-follow post-MVP · FR-FF1 · Statut : review**

As a conseillère B2B (Mme Dupont), I want voir la liste des élèves « profils à
risque » avec motifs expliqués, So that je puisse intervenir proactivement.

## Ce qui est livré

### API
- **`services/risk_detection.py`** — 3 règles, calculées à la demande au
  chargement du dashboard (lazy, patron Epic 10 ; requêtes batchées, pas
  d'appel IA par élève) :
  - `faible_engagement` : > 30 j sans connexion (`last_login`, le signal que
    le dashboard 6.6 expose déjà par élève) ; un élève jamais connecté compte
    depuis l'acceptation de son invitation.
  - `profil_incoherent` : zéro recoupement entre les spécialités choisies et
    celles couvrant ses passions — **table d'affinité éditoriale v1**
    (19 passions → spécialités GT, consignée, révisable produit), déclenchée
    seulement avec ≥ 2 passions mappées ; vocabulaire bac pro hors périmètre
    (consigné).
  - `baisse_moyenne` : moyenne des deux derniers bulletins manuels (ordre
    `created_at`, `trimestre_label` étant du texte libre — consigné),
    baisse > 2 pts.
- **Frontière de consentement (décision structurante)** : le signal suit la
  donnée. `faible_engagement` court sur toute la cohorte (donnée déjà
  exposée) ; les deux règles individuelles (profil, bulletins) ne courent
  **que si le consentement 6.7 est accordé**. La réponse porte
  `students_without_consent` pour que la conseillère connaisse les limites de
  sa liste.
- **`CounselorIntervention`** (migration 0007, miroir de `CounselorNote` :
  FK simples, pas de RLS, toujours filtré par `counselor=request.user`) :
  une ligne par (conseillère, élève), POST = marque ou **rouvre**, DELETE =
  résout — l'élève marqué reste listé sous « intervention en cours » au lieu
  de ré-alerter (AC2).
- **Endpoints** : `GET cohort-dashboard/at-risk/` (audité
  `at_risk_list_viewed` — dérive des signaux individuels, comme la vue 6.8) ;
  `POST/DELETE students/<id>/intervention/` (appartenance à l'établissement
  = autorisation, audités). RBAC : 323 endpoints verts.
- **L'élève n'a aucune surface** : endpoints IsCounselor, aucun chemin de
  lecture côté élève. Tension avec le droit d'accès art. 15 (le flag n'est
  pas dans l'export) : **item DPO consigné**, comme les notes conseillère.

### Fix transverse attrapé par la preuve live (auth MFA)
- **Aucun staff réel non-superuser ne pouvait passer une permission
  `requires_mfa_verified`** : ni `mfa/challenge/` ni `enroll/confirm/`
  n'appelaient `django_otp.login()` — la session ne portait jamais le device
  vérifié, `user.is_verified()` restait False → 403 `not_mfa_verified`.
  Invisible jusqu'ici : les preuves des epics 5-9 utilisaient un path_admin
  **superuser** (bypass d'IsPathAdmin). Attrapé en montant la session MFA
  réelle de la conseillère. Fix : `_bind_verified_device` dans les deux vues +
  test épinglant `otp_device_id` en session.

### Web
- **`AtRiskPanel`** en tête de `/cohorte` (ce qui demande une action passe
  avant les stats) : wording **constructif par construction** — section
  « Nécessite ton attention », motifs en phrases d'accompagnement, jamais
  « en échec » (testé négativement) ; note de limite consentement ; CTA
  « Suggérer un entretien — voir le profil » (enchaîne sur le flux consentement
  6.8 existant) ; marquage optimiste avec retour arrière.
- Français en dur comme le reste de l'UI cohorte (dette i18n du namespace
  préexistante, consignée — non aggravée).

## Résultats

- **Tests** : API fast lane **1633** (11 nouveaux `test_risk_detection` +
  1 pin MFA session) ; establishments **75** ; web **1041** (5 nouveaux
  `AtRiskPanel` + page cohorte) ; lane RLS locale **156** ; ruff/tsc propres ;
  mypy zéro nouvelle erreur (16=16 accounts, 10=10 counselor_views) ;
  RBAC 323.
- **Preuve live** (stack dev, session **MFA réelle** de la conseillère
  `dupont-risk@test.local` — enrollment TOTP puis challenge) :
  - `GET at-risk` → 3 élèves, 3 motifs exacts :
    `faible_engagement(48 j)`, `profil_incoherent(3 passions)`,
    `baisse_moyenne(3.25 : 14.0 → 10.75)` ; `sans_consentement: 1`
    (l'inactif, évalué sur l'activité seule).
  - `POST intervention` **201** → l'élève passe `intervention_in_progress` ;
    `DELETE` **204** ; re-POST **200** (réouverture, une seule ligne).
  - **SSR** : `GET /cohorte` avec la session conseillère → le HTML serveur
    contient « Nécessite ton attention », « Pas de connexion depuis
    48 jours », « Sa moyenne est passée de 14 à 10.75 », la note de
    consentement et le bouton de marquage.
  - Comptes de preuve conservés : `dupont-risk@test.local` (+ 3 élèves,
    établissement « Lycée Preuve 10-1 »).
