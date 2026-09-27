# Story 10.3 — Tableau qualité référentiel admin

**Epic 10 — Fast-follow post-MVP · FR-FF3 · Statut : review**

As a admin Path-Advisor, I want un tableau de bord de qualité du référentiel,
So that je gouverne la qualité éditoriale en continu.

## Ce qui est livré

- **`professions/referential_quality.py`** — `build_quality_report()`,
  calculé à la demande (patron 9.6, rien de stocké) : comptes par statut
  éditorial (source de vérité 9.1/9.2) vs **cibles FR48** (50/500 métiers,
  100/1000 écoles) ; **fraîcheur 12 mois** = part des fiches publiées dont la
  dernière révision (`Max(revisions.created_at)`, repli `created_at` pour les
  fiches seedées jamais éditées — plus strict qu'`updated_at` qui bouge sur
  tout save) est dans la fenêtre ; signalements ouverts
  (pending + info_requested, le filtre canonique 9.3) + overdue 7 j ;
  modérations en attente (motivations 9.4 + commentaires d'écoles) ;
  **tendances 6 mois** (éditions métiers/écoles via les révisions,
  signalements ouverts) bucketées en Python.
- **Seuils d'alerte de l'AC** : > 20 signalements ouverts, fraîcheur < 60 %
  (None sur référentiel vide — 0 % serait une fausse alerte). Hébergement
  dans `professions` (l'app qui possède déjà l'outillage qualité), consigné.
- **`GET /api/v1/admin/referential-quality/`** (`IsAuthenticatedAndActive,
  IsPathAdmin`) — RBAC 324 endpoints verts.
- **Web `/admin/qualite`** : nav admin (8e section), tuiles patron 9.6
  (valeur en `text-warning` si alerte, chip « À traiter »/« Sain » —
  « Attention requise » refusé par le lint de ton, marqueur d'urgence),
  **CTA par file** vers /admin/signalements et /admin/moderation (AC),
  3 séries de barres CSS mensuelles à teinte unique.

## Résultats

- **Tests** : professions **656** (5 nouveaux `test_referential_quality`) ;
  web qualite 2 ; tone lint OK ; tsc/eslint/ruff propres ; mypy 0 sur le
  module ; RBAC **324**. Pas de migration ni de RLS (lecture d'agrégats).
- **Preuve live** (session **MFA réelle** d'un path_admin **non-superuser**
  `karim-quality@test.local` — enrollment TOTP → l'endpoint répond : preuve
  croisée que le fix `_bind_verified_device` de la 10.1 fonctionne aussi sur
  le chemin enrollment et sans bypass superuser) :
  - KPIs réels du dev : 55/50 métiers publiés, 76/100 écoles, fraîcheur
    100 %, 0 signalement ouvert, alertes éteintes.
  - Tendances = l'activité réelle du mois (5 éditions métiers, 2 écoles,
    1 signalement — les preuves des stories 9.x/10.x).
  - SSR `/admin/qualite` : nav + état de chargement rendus serveur.
