# Résumé — Epic 9 : Back-office Administration & Modération

> Statut : **clos le 27/09/2026** — 6/6 stories mergées (PRs #113 → #118, clôture #119).
> Objectif : donner à l'admin Path-Advisor (Karim) un vrai back-office (`/admin`, Next, réservé `path_admin` + MFA) pour maintenir le référentiel, traiter les signalements, modérer les contenus libres, et gouverner/auditer le modèle IA.

## Story 9.1 — CRUD référentiel professions (PR #113)

Maintenir les 50 métiers MVP (et 500+ en growth, FR48 + NFR-SC5).

- Liste admin avec recherche, tri, filtre par statut **publié / brouillon / archivé** ; création avec tous les champs éditoriaux.
- Chaque modification est **versionnée** : historique consultable, **rollback** possible (réappliqué comme nouvelle révision, jamais de réécriture du passé).
- Chaque écriture est tracée dans `audit_log` (qui, quoi, quand).
- « Supprimer » = **archiver** (les fiches sont référencées par paris, stats, envois) ; recalcul des recos **lazy** (au retour de l'élève).

## Story 9.2 — CRUD référentiel formations / écoles + calendrier (PR #114)

Maintenir le référentiel 100+ formations (FR48).

- Miroir du patron 9.1 sur les écoles : filtres type / région / statut, révisions, rollback, audit.
- **Import CSV** (open data Parcoursup) : validation ligne à ligne, les conflits (école déjà existante) ne sont **jamais écrasés** — drill-down manuel ; créations en brouillon, tout-ou-rien.
- **Calendrier Parcoursup** (délégué par la Story 8.3) : CRUD visuel des jalons ; un jalon déjà **notifié** a sa date **verrouillée** (l'email est parti → 409).

## Story 9.3 — File de signalements, SLA 7 jours (PR #115)

Traiter les retours élèves rapidement (FR49).

- File ordonnée du plus ancien au plus récent, filtre par type, **alerte au-delà de 7 jours** (badge + compteur).
- Trois actions : **corriger** (lien direct vers la fiche 9.1/9.2), **rejeter** (motif obligatoire, silencieux pour l'élève), **demander des précisions** (notification, le signalement reste en file).
- À la résolution : l'élève signaleur reçoit « La fiche que tu as signalée a été mise à jour » (nouvelle catégorie de notification `report_updates`, opt-out respecté).

## Story 9.4 — Modération a priori des motivations libres (PR #116)

Filtrer contenus inappropriés / discriminatoires / données tierces avant transmission aux écoles (FR50).

- File des motivations `pending_moderation` ; décision **Approuver** (débloque l'envoi 5.5) ou **Refuser** avec **catégorie typée** (contenu inapproprié, données tierces, discrimination, autre) + commentaire.
- SLA **24 h réellement ouvrées** (lun-ven), compteur d'âge et alerte.
- **Pré-screening automatique** (PII : email/téléphone/URL + lexique à risque) comme **aide à la priorisation uniquement — la décision est toujours humaine**, pas d'auto-refus.
- **Commentaires libres des écoles** (délégué par la revue Epic 8, P2-5) : gatés a priori dans la même file ; l'email « réponse école » part immédiatement **sans** le commentaire, qui n'apparaît in-app qu'après approbation.

## Story 9.5 — Versioning modèles IA + audit trail (PR #117)

Rendre les décisions IA auditables et rejouables (RGPD art. 22 + NFR-M3 + ADD-10).

- Table `model_versions` : version, `dataset_hash` (SHA256), hyperparamètres, métriques d'évaluation, `deployed_at/by` ; **activation exclusive**, anciens modèles servables (rollback).
- Journal `scoring_decisions` (RLS) : chaque reco élève trace la version + un **snapshot fidèle** des entrées (profil + tranche du référentiel au moment T) → **rejeu reproductible** via `replay_scoring_decision`. Rétention 365 j (note DPO).
- **Porte éthique** : écart inter-groupes > 10 % dans les métriques d'évaluation ⇒ activation refusée (409) sans note de revue éthique.
- **Cadrage sous-populations** : ni genre ni attribut sensible (privacy by construction) ; dimensions = celles qui existent (niveau, filière). Introduire le genre exigerait une décision produit + DPO.

## Story 9.6 — Métriques audit ML : drift, biais (PR #118)

Détecter les dégradations du modèle en production (FR52).

- Dashboard `/admin/audit-ml` : distribution mensuelle des scores, **drift KS** vs baseline gelée à l'activation (plancher 50 échantillons), écarts par sous-population (niveau, filière ; groupes ≥ 30).
- **Beat hebdomadaire** : audit automatique → si drift au-dessus du seuil ou écart > 10 %, **email d'alerte aux ops** avec workflow proposé (réentraîner ? rollback 9.5 ?) + modèle **flaggé pour revue éthique** ; trace `audit_log`. Slack : non câblé (aucun webhook dans l'infra, consigné).

## Décisions transverses

- Back-office = section **Next `/admin`** (guards `path_admin` + MFA préexistants) ; le Django admin reste le break-glass.
- `status` éditorial est la source de vérité, `is_active` **dérivé** dans `save()` → les requêtes publiques des epics 3/7/8 restent intactes.
- Historique **append-only** partout (fiches et journal art. 22).
- La modération est toujours **humaine** ; les rejets sont motivés ; rien de rejeté ne surface côté élève.
- Recalculs « background » des AC = **lazy par construction** (recos à la requête, stats à la consultation), consigné plutôt que sur-machiné.

## Reste ouvert (consigné hors epic)

Signalement d'écoles côté élève · indicateur élève « commentaire en relecture » (API prête via `comment_pending`) · Slack pour les alertes ML · dimensions région/type d'établissement quand la donnée existera · items DPO (DPA Postmark).
