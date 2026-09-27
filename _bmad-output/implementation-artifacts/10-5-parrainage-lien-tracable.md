# Story 10.5 — Parrainage / partage avec lien traçable

**Epic 10 — Fast-follow post-MVP · FR-FF5 · Statut : review**

As a élève satisfait de Path-Advisor, I want partager le produit à un pair
via un lien traçable, So that la viralité organique se développe.

## Ce qui est livré

### API
- **`ReferralCode`** (OneToOne, créé au premier accès) + **`Referral`**
  (attribution, filleul OneToOne — une inscription = au plus une
  attribution), migration accounts 0015. **Déviation consignée de l'AC** :
  le lien est `/r/{code opaque}` et non `/r/{my_id}` — un `usr_…` dans une
  URL WhatsApp est une fuite d'énumération (précédent : tokens opaques
  partout). CASCADE des deux côtés (suppression 1.12 = donnée minimale).
  Pas de RLS (ligne à deux parties, patron CounselorConsent), consigné.
- **`GET /api/v1/auth/referral/`** (IsStudent) : code, url, compteur sobre.
  RBAC **325**.
- **Signup** : `referral_code` optionnel de bout en bout (serializer →
  adapter → signal). **Validation silencieuse** : code inconnu ou
  auto-parrainage = ignoré sans erreur (pas d'oracle d'énumération), et
  l'attribution est best-effort — elle ne casse jamais une inscription.
- **Notification parrain** : nouvelle catégorie `referrals` (migration
  notifications 0010 ; émet dès sa naissance — règle P2-4 ; apparaît dans
  les préférences) : email + push « Ton pote vient de rejoindre » — **sans
  jamais l'identité du filleul** (pas de first_name par construction ; le
  parrain sait à qui il a envoyé son lien).
- **Export RGPD** : le profil porte `referral {code, referred_count,
  was_referred}` — jamais les filleuls, et le filleul ne voit pas par qui
  il a été parrainé (testé).
- Incentives : V2 hors périmètre (AC) — aucun compteur pressant, aucune
  récompense.

### Web
- **`/r/[code]`** (public) → redirection serveur vers
  `/auth/signup?ref={code}` (la page ne confirme jamais l'existence d'un
  code). Le formulaire d'inscription transmet le code en silence.
- **`/parametres/parrainage`** : lien + **partage natif**
  (`navigator.share` → feuille système WhatsApp/Instagram/SMS, AC) avec
  repli copie (toast), compteur sobre. Entrée « Parrainer un pote » dans le
  menu compte (élèves uniquement — l'endpoint est IsStudent).

## Résultats

- **Tests** : API fast lane **1651** (6 nouveaux `test_referral`) ; lane RLS
  locale **156** ; web referral-panel 4 + signup-form 5 (payload `ref`) +
  nav 32 ; mypy **30 < 31 baseline** (une préexistante corrigée par le
  typage du dict d'export) ; RBAC 325.
- **Preuve live** : parrain réel (`sideflow-live-106@test.local`) →
  `GET referral` : lien opaque stable (`/r/jWcDuqx7`, aucun `usr_`) →
  **`GET /r/{code}` → 307** vers `/auth/signup?ref=…` → inscription réelle
  de `pote-105@test.local` avec le code → `referred_count: 1`, catégorie
  `referrals` visible dans les préférences, **email « Ton lien de
  parrainage a fait mouche »** dans Mailpit (sans identité du filleul).
- Prise annexe : le volume anonyme `/app/.next` du conteneur web garde un
  **manifest de routes périmé** — une nouvelle route top-level exige
  `rm -rf /app/.next/*` + restart, pas seulement `cache/` (mémoire
  colima-stale-runtimes à durcir).
