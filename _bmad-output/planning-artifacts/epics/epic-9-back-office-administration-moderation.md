# Epic 9 : Back-office Administration & Modération

Permettre à Karim (admin Path-Advisor) de maintenir le référentiel professions/formations/écoles, traiter les signalements sous 7 jours, modérer les motivations libres a priori, versionner les modèles IA + dataset, et auditer le drift ML.

## Story 9.1 : CRUD référentiel professions

As a admin Path-Advisor (Karim),
I want créer, modifier et supprimer des fiches du référentiel professions,
So that je puisse maintenir la qualité éditoriale des 50 métiers MVP et étendre vers 500+ en growth (FR48 + NFR-SC5).

**Acceptance Criteria :**

**Given** je suis admin connecté (MFA validé)
**When** je vais dans Back-office → "Référentiel" → "Métiers"
**Then** je vois la liste des 50+ professions avec recherche, tri, filtre par statut (publié / brouillon / archivé)
**And** je peux créer un nouveau métier avec tous les champs (description, journée type, prérequis, débouchés, signaux, niveau compatibilité…)

**Given** je modifie une fiche existante
**When** je sauvegarde
**Then** un versionning de l'édition est tracé (historique consultable, rollback possible)
**And** un job background recalcule les recos vocationnelles impactées (lazy : seulement quand l'élève revient)

**Given** la conformité audit
**When** je modifie une fiche
**Then** une trace dans `audit_log` enregistre la modification (qui, quoi, quand)

## Story 9.2 : CRUD référentiel formations / écoles

As a admin Path-Advisor,
I want créer, modifier et supprimer des fiches du référentiel formations / écoles,
So that je puisse maintenir la qualité du référentiel 100+ formations MVP (FR48).

**Acceptance Criteria :**

**Given** je suis admin et je vais dans "Référentiel" → "Écoles"
**When** je consulte la liste
**Then** je peux filtrer par type (lycée pro / prépa / BTS / IUT / écoles d'ingé / commerce), par région, par statut
**And** je peux créer une école avec tous ses champs + lien vers formations associées

**Given** je peux importer en masse via CSV
**When** je télécharge un CSV d'écoles depuis open data Parcoursup
**Then** l'import valide chaque ligne + signale les conflits (école déjà existante)
**And** je peux drill-down pour résoudre les conflits manuellement

**Given** la traçabilité (NFR-S4)
**When** je modifie une école
**Then** l'historique est tracé + le job de recalcul des stats d'admission impactées s'exécute en background

## Story 9.3 : File de signalements + workflow modération sous 7 jours

As a admin Path-Advisor,
I want une file de signalements priorisée + workflow de traitement sous 7 jours,
So that les retours utilisateurs sont traités rapidement et la qualité du référentiel reste haute (FR49).

**Acceptance Criteria :**

**Given** des signalements ont été émis par les élèves (Story 3.8)
**When** je vais dans Back-office → "Signalements"
**Then** je vois la file ordonnée par âge + priorité (jalon : alerter si signalement > 7 jours non traité)
**And** je peux filtrer par type (erreur métier / école obsolète / contenu inapproprié)

**Given** je traite un signalement
**When** je l'ouvre
**Then** je vois la fiche concernée + le contexte + le message utilisateur
**And** je peux : corriger la fiche (lien direct vers Story 9.1 ou 9.2), rejeter le signalement (avec motif), demander des précisions à l'élève (via notification)

**Given** la résolution
**When** je marque le signalement résolu
**Then** l'élève signaleur reçoit une notification "La fiche que tu as signalée a été mise à jour" (si opt-in)
**And** la file se met à jour

## Story 9.4 : Modération a priori des motivations libres (envoi anticipé)

As a admin Path-Advisor,
I want modérer les motivations libres rédigées par les élèves a priori (avant transmission à l'école),
So that les contenus inappropriés / discriminatoires / les données personnelles tierces soient filtrés (FR50).

**Acceptance Criteria :**

**Given** un élève a soumis une motivation (Story 5.5)
**When** je vais dans Back-office → "Modération motivations"
**Then** je vois la file de motivations en attente (statut `pending_moderation`)
**And** je peux ouvrir une motivation et la consulter en plein écran

**Given** je modère une motivation
**When** je décide
**Then** je peux Approuver (statut `approved` → l'envoi se débloque, Story 5.5) ou Refuser (statut `rejected` avec catégorie : contenu inapproprié, données tierces, discrimination, autre + commentaire)

**Given** la SLA
**When** une motivation est dans la file
**Then** elle doit être traitée en < 24 h ouvrées
**And** un compteur d'âge alerte si > 24 h

**Given** l'aide à la modération
**When** je consulte une motivation
**Then** un pré-screening automatique (mots-clés à risque, données personnelles détectées) m'aide à prioriser
**But** la décision finale est toujours humaine (pas d'auto-refus)

## Story 9.5 : Versioning modèles IA + audit trail dataset

As a admin Path-Advisor,
I want versionner chaque modèle de recommandation IA avec son dataset d'entraînement et ses hyperparamètres,
So that les décisions IA soient auditables (RGPD art. 22 + NFR-M3 + ADD-10).

**Acceptance Criteria :**

**Given** un nouveau modèle est déployé
**When** le déploiement est traçé
**Then** la table `model_versions` enregistre : `id`, `name`, `version`, `dataset_hash` (SHA256 du dataset d'entraînement), `hyperparameters_json`, `evaluation_metrics_json`, `deployed_at`, `deployed_by`
**And** l'ancien modèle reste accessible en lecture (rollback possible)

**Given** un score IA produit pour un élève
**When** la décision est tracée
**Then** chaque scoring inclut le `model_version_id` utilisé
**And** je peux rejouer la décision à partir du modèle archivé (audit reproductibilité)

**Given** la conformité éthique (audit biais)
**When** je consulte les métriques d'évaluation d'un modèle
**Then** je vois les performance disaggregées par sous-population (genre, région, type d'établissement)
**And** un écart > 10 % inter-groupes déclenche une alerte avant déploiement

## Story 9.6 : Métriques audit ML (drift, biais)

As a admin Path-Advisor,
I want consulter les métriques d'audit ML (drift des prédictions, biais par sous-population, distribution des scores),
So that je détecte les dégradations du modèle en production (FR52).

**Acceptance Criteria :**

**Given** la production envoie des décisions de scoring
**When** je vais dans Back-office → "Audit ML"
**Then** je vois des métriques temps réel : distribution des scores vocationnels par mois, drift par rapport au baseline, distribution par sous-population (genre, région, niveau scolaire)

**Given** un drift est détecté (KS-test ou similaire au-dessus du seuil)
**When** la métrique devient critique
**Then** une alerte est envoyée à l'admin (email + Slack si configuré)
**And** un workflow de revue est proposé (réentraîner ? rollback ?)

**Given** les biais inter-groupes
**When** un écart > 10 % est détecté sur une métrique critique (score moyen par genre par exemple)
**Then** une alerte est envoyée + le modèle est marqué pour revue éthique
