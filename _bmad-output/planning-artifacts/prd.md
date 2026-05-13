---
stepsCompleted: ["step-01-init", "step-02-discovery", "step-02b-vision", "step-02c-executive-summary", "step-03-success", "step-04-journeys", "step-05-domain", "step-06-innovation", "step-07-project-type", "step-08-scoping", "step-09-functional", "step-10-nonfunctional", "step-11-polish", "step-12-complete"]
status: "complete"
completedDate: "2026-05-13"
classification:
  projectType: "saas_web_app"
  domain: "edtech"
  complexity: "medium"
  projectContext: "greenfield"
releaseMode: "phased"
inputDocuments:
  - "product-brief-Path-Advisor.md"
workflowType: 'prd'
---

# Product Requirements Document - Path-Advisor

**Author:** Marwen
**Date:** 2026-05-12

## Executive Summary

Chaque année, près d'un million de lycéens français se confrontent à un choix d'orientation post-bac engageant — sans outil capable de les y préparer vraiment. Les plateformes publiques (Onisep, Diagoriente) délivrent une information générique. Parcoursup gère la candidature, pas le conseil. Les comparateurs privés (Diplomeo, L'Étudiant) sont structurellement biaisés : leur modèle repose sur la revente de leads aux écoles. Et le ratio conseillers d'orientation/élèves en France (1 pour 1 400) rend l'accompagnement humain inaccessible à l'échelle.

**Path-Advisor est la première plateforme d'orientation continue pour les jeunes francophones**, de la 3ème aux premières années post-bac. Elle combine deux moteurs de recommandation complémentaires — vocationnel et parcours — alimentés par des données objectives (notes, bulletins, appréciations enseignants) et déclaratives (passions, centres d'intérêt). L'élève passe de *"qui suis-je et qu'est-ce qui me correspond ?"* à *"comment y arriver concrètement, avec mes chances réelles ?"* dans un seul produit, neutre commercialement.

**Cibles :** lycéens 15-20 ans (B2C freemium, premium 10,99€/mois) et établissements scolaires (B2B licence, ~5 000€/an pour 100 utilisateurs). Marché francophone : France d'abord, puis Belgique, Maroc, Tunisie, Sénégal.

### What Makes This Special

Le différenciateur central de Path-Advisor est son **double moteur de recommandation** : un même produit articule la question vocationnelle (*qui je peux devenir*) et la question opérationnelle (*comment y arriver*). Aujourd'hui, ces deux questions sont traitées par des outils séparés, génériques, ou commercialement biaisés — jamais par un acteur unique avec une logique de bout en bout.

Trois renforts rendent ce double moteur crédible :

1. **Données scolaires objectives** — l'intégration des bulletins (via ENT/Pronote ou import) crée un profil que l'élève ne peut pas reconstruire sur une plateforme concurrente. C'est l'avantage défensif structurel.
2. **Neutralité commerciale** — aucune revente de leads. Le revenu vient de l'utilisateur (premium B2C) et des établissements (licence B2B), jamais des écoles cibles. La recommandation reste orientée intérêt élève.
3. **Continuité temporelle** — de la 3ème à bac+2/3, la plateforme suit l'évolution du profil et adapte ses recommandations, là où tous les concurrents proposent un snapshot ponctuel.

**Double moment "aha"** qui structure l'expérience :
- *"Voilà les métiers qui te correspondent vraiment"* — révélation vocationnelle dès la complétion du profil
- *"Voilà le chemin concret, avec tes chances réelles d'admission"* — graphe de parcours enrichi de statistiques d'admission par école

**Insight fondamental :** L'orientation n'est pas un événement ponctuel (Parcoursup en Terminale) — c'est un processus continu qui mérite un compagnon dans la durée. Et la donnée scolaire objective est le levier qui transforme un questionnaire générique en recommandation vraiment personnalisée.

**Pourquoi maintenant :** Convergence rare entre un problème permanent (chaque cohorte de lycéens vit la même angoisse, année après année) et une fenêtre technologique nouvellement ouverte (l'IA grand public rend enfin possible la personnalisation à grande échelle pour un produit d'intérêt général). Aucun acteur ne couvre aujourd'hui ce parcours de bout en bout en français.

## Project Classification

| Dimension | Valeur |
|---|---|
| **Type de projet** | Web App SaaS (B2C + B2B), responsive — pas d'app mobile native en v1 |
| **Domaine** | EdTech — orientation scolaire, francophonie |
| **Complexité** | Medium — données scolaires de mineurs (RGPD, conformité éducative), pas de certification réglementaire lourde |
| **Contexte** | Greenfield — construction depuis zéro, aucun système existant à intégrer |

**Considérations EdTech spécifiques :**
- Conformité **RGPD** renforcée (mineurs, données scolaires sensibles)
- Accessibilité **WCAG** (établissements publics → exigence légale)
- Modération de contenu et alignement curriculum
- Gestion du consentement parental (utilisateurs < 15 ans)

## Success Criteria

### User Success

L'élève doit non seulement *utiliser* Path-Advisor — il doit *agir* sur ses recommandations. Trois métriques principales captent cet impact :

| Métrique | Cible MVP (6-12 mois) | Cible Growth (12-24 mois) |
|---|---|---|
| **Étudiants actifs / mois (MAU)** | 500 | 10 000 |
| **Étudiants qui postulent à au moins 1 école recommandée** | 30% des MAU | 50% des MAU |
| **Étudiants qui s'inscrivent dans un parcours conseillé** | À mesurer (tracking annuel) | 25% des cohortes suivies |

**Métriques d'expérience associées :**
- **Complétion onboarding obligatoire** (bulletins + résultats + passions) > 70 % des inscrits — étape critique car les bulletins sont obligatoires
- **NPS utilisateur** > 40 en MVP, > 50 en growth
- **Retour à 30 jours** > 40 % (validation du "compagnon continu", pas de l'outil ponctuel)

**Moment de vérité :** un utilisateur qui complète son onboarding, consulte ses recommandations vocationnelles, puis explore au moins un graphe de parcours détaillé = signal fort que le double moteur a fonctionné pour lui.

### Business Success

**Modèle B2C — Freemium :**
- **MVP :** 5 % des MAU en premium (10,99 €/mois) → ~25 utilisateurs premium à 500 MAU
- **Long terme :** 10-15 % des MAU en premium
- **Feature premium clé (MVP) :** envoi anticipé du profil aux écoles partenaires

**Modèle B2B — Licence :**
- **MVP :** 5 établissements scolaires **pilotes gratuits pendant 1 an** — leur rôle dépasse l'usage : ils deviennent les premières écoles partenaires de la feature "envoi anticipé", ce qui crée l'effet réseau initial
- **Growth :** 30+ établissements licenciés (5 000 €/an pour 100 utilisateurs) après bascule des pilotes en payant à T+12 mois

**Indicateur santé business :** au moins 3 des 5 pilotes B2B convertissent en payant à la fin de l'année de gratuité.

### Technical Success

| Critère | Cible MVP | Cible Growth |
|---|---|---|
| **Temps de réponse moteur de recommandation** | < 3 secondes | < 1,5 seconde |
| **Disponibilité plateforme** | 99 % (≈ 7h downtime/mois) | 99,5 % |
| **Conformité RGPD** | Audit interne documenté + DPIA réalisée | Audit externe par tiers certifié |
| **Accessibilité WCAG** | Niveau AA sur parcours critiques | Niveau AA complet |
| **Sécurité données mineurs** | Chiffrement at-rest + in-transit, gestion consentement parental < 15 ans | Pen-test annuel |

### Measurable Outcomes

**Année 1 (MVP — 6 à 12 mois) :**
- 500 MAU B2C, dont 25 premium (5 %)
- 5 établissements scolaires pilotes gratuits actifs
- 50+ professions et 100+ formations référencées
- 150 étudiants qui postulent à au moins 1 école recommandée (30 % des MAU)
- NPS > 40 ; complétion onboarding > 70 %

**Année 2 (Growth — 12 à 24 mois) :**
- 10 000 MAU, dont 500-1 500 premium (5-15 %)
- 30+ établissements licenciés payants (incluant au moins 3 ex-pilotes convertis)
- Intégration ENT/Pronote fonctionnelle (import automatique des bulletins)
- Lancement Belgique **ou** Maroc validé
- 5 000 étudiants qui postulent à au moins 1 école recommandée (50 % des MAU)

## User Journeys

### Parcours 1 — Sarah, lycéenne en Terminale (utilisateur primaire, happy path)

**Personnage :** Sarah, 17 ans, Terminale générale (spécialités Maths + SVT). Bonnes notes mais pas top. Curieuse de la santé sans savoir si "médecine" lui correspond vraiment.

**Scène d'ouverture — La douleur.** On est en novembre. Parcoursup ouvre dans deux mois. Sarah a regardé des vidéos YouTube, parlé à sa conseillère d'orientation (15 min, frustrant), feuilleté Onisep (générique). Elle est anxieuse — ses parents la poussent vers médecine, elle hésite, elle ne sait pas comment décider.

**Découverte.** Une amie partage Path-Advisor sur Instagram. Sarah s'inscrit.

**Action montante — L'onboarding.**
- Crée un compte (consentement parental géré car elle a 17 ans donc OK)
- Saisit passions (sciences, bénévolat hôpital, dessin), centres d'intérêt, valeurs
- Importe ses bulletins (PDF) — l'OCR extrait notes + appréciations
- Temps total : 12 minutes

**Premier moment "aha" — Révélation vocationnelle.** Path-Advisor lui propose 8 métiers scorés : infirmière praticienne avancée (92 %), sage-femme (87 %), ingénieure biomédicale (84 %), pharmacienne (78 %)… Médecin n'est qu'à 71 %. Pour chaque métier : un score, les signaux qui l'ont fait monter, ce que c'est concrètement, une journée type.

> *Surprise.* Sarah n'avait jamais entendu parler d'ingénieure biomédicale. Elle creuse.

**Deuxième moment "aha" — Révélation du parcours.** Elle clique sur "ingénieure biomédicale". Un graphe de parcours s'affiche : 3 chemins possibles (prépa BCPST → école d'ingénieur biotech / PASS → réorientation ingénierie / IUT mesures physiques → école d'ingé). Pour chaque chemin : durée, coût total, écoles cibles avec **statistiques d'admission personnalisées** ("avec ton profil, tu as 38 % de chances d'intégrer INSA Lyon, 71 % à Polytech Marseille").

**Climax — Décision.** Sarah passe en premium (10,99 €). Elle déclenche la feature **envoi anticipé** vers Polytech Marseille et INSA Lyon. Elle reçoit dans la semaine un email d'INSA : *"Profil intéressant, candidature encouragée"*. Sa stat d'admission INSA passe de 38 % à 52 %.

**Résolution.** Sarah formule ses vœux Parcoursup avec **clarté** : 3 prépas BCPST en sécurité, 2 IUT mesures physiques en plan B, INSA Lyon en pari. Elle revient sur Path-Advisor en mars pour ajuster, en mai pour comparer les réponses Parcoursup.

**Capacités révélées :** Inscription + consentement (mineur) • OCR bulletins PDF • Saisie profil (passions, intérêts, valeurs) • Moteur de reco vocationnelle avec explicabilité des scores • Graphe de parcours interactif avec stats d'admission • Paiement premium • Feature "envoi anticipé" • Notifications + sessions répétées (compagnon continu)

### Parcours 2 — Mehdi, élève de 3ème, orientation bac pro (variation du happy path)

**Personnage :** Mehdi, 14 ans, 3ème dans un collège REP+. Bon en techno et arts plastiques, moins à l'aise en français/maths. Il aime ses mains et créer des objets.

**Scène d'ouverture.** Le conseil de classe approche. La principale a évoqué le bac pro, ses parents préfèrent le général "au cas où". Mehdi est partagé — il ne veut pas être "celui qui n'a pas eu le général" mais il déteste la pression scolaire actuelle.

**Découverte.** Le collège est l'un des 5 pilotes B2B. Sa conseillère d'orientation lui envoie un lien Path-Advisor.

**Onboarding adapté 3ème.** Pas de bulletins lycée (il n'y est pas encore). Il saisit ses bulletins collège, ses appréciations, ses passions (mécanique, jeux vidéo, vidéo TikTok DIY). Consentement parental requis (mineur < 15 ans).

**Premier "aha" — Révélation vocationnelle (cohérente 3ème).** Path-Advisor lui propose : technicien aéronautique (89 %), ébéniste designer (84 %), monteur vidéo (81 %), électromécanicien systèmes automatisés (78 %).

**Deuxième "aha" — Le graphe est différent.** Comme on parle d'un élève de 3ème conseillé bac pro, le graphe **commence par un lycée pro associé** (et non un lycée général). Exemple pour technicien aéronautique : *Bac pro Aéronautique option Avionique (Lycée pro Saint-Exupéry, Toulouse) → BTS Aéronautique → option : poursuite école d'ingé en alternance*.

Le graphe affiche 2-3 lycées pro accessibles depuis sa carte scolaire, avec ouvertures Affelnet et stats d'admission.

**Résolution.** Mehdi en parle à ses parents avec le graphe imprimé — il leur montre que "bac pro" n'est pas un cul-de-sac, qu'il existe une passerelle école d'ingé alternance. Ils acceptent le pari.

**Capacités révélées :** Onboarding différencié par niveau scolaire (collège / lycée général / lycée pro) • Logique de parcours bac pro avec lycée associé + débouchés post-bac • Intégration carte scolaire (lycées géographiquement accessibles) • Affelnet (équivalent Parcoursup pour le 3ème) • Référentiel de formations couvrant les filières pro

### Parcours 3 — Léa, lycéenne sans bulletins (edge case dégradé)

**Personnage :** Léa, 16 ans, 1ère générale. Elle s'inscrit par curiosité après avoir vu une vidéo TikTok. Pas envie de partager ses bulletins ("pourquoi tu veux mes notes ?").

**Onboarding partiel.** Elle saisit passions et intérêts. À l'étape bulletins, elle clique "Plus tard".

**Expérience dégradée — choix produit explicite.** Path-Advisor lui montre quand même des recommandations vocationnelles basées sur le déclaratif seul, mais avec un **score d'incertitude élevé**. Les métiers sont là, mais la fiabilité est affichée comme "indicative".

Quand elle ouvre un graphe de parcours : les chemins sont visibles, mais **les statistiques d'admission affichent une probabilité quasi nulle** (faute de données scolaires pour prédire). Un bandeau persistant et bien visible : *"Ajoute tes bulletins pour débloquer tes vraies chances d'admission — c'est gratuit et confidentiel."*

**Résolution.** Deux semaines plus tard, Léa cède (sa mère l'y pousse). Elle importe ses bulletins. Les stats d'admission deviennent significatives. Elle découvre que l'école qu'elle visait par défaut est en réalité accessible — elle reprend confiance.

**Capacités révélées :** Mode "profil dégradé" assumé (pas de dead-end) • Affichage explicite de l'incertitude des scores • Bandeau d'incitation persistant + non-bloquant • Conversion progressive vers le profil complet

### Parcours 4 — Mme Dupont, conseillère d'orientation (B2B pilote)

**Personnage :** Sandrine Dupont, conseillère psychologue de l'Éducation Nationale, partagée sur 3 lycées et 1 collège (1 600 élèves). Surchargée. Engagée mais frustrée.

**Scène d'ouverture.** Son chef d'établissement lui annonce que le lycée fait partie des 5 pilotes Path-Advisor — gratuit pendant 1 an. Elle est sceptique : "encore un outil".

**Onboarding B2B.** Elle reçoit un accès admin. Une session de formation 1h en visio. Elle crée la cohorte de Terminale (250 élèves) + envoie des invitations.

**Action montante — Dashboard conseiller.** Trois semaines plus tard, 180 élèves se sont inscrits, 120 ont complété leur profil. Mme Dupont voit dans son dashboard :
- Vue cohorte : taux de complétion, métiers les plus consultés, profils "à risque" (décrochage, profil incohérent, peu d'engagement)
- Vue élève individuel (avec consentement) : profil, recos vocationnelles, parcours explorés, vœux en construction

**Climax — Un usage qui change sa pratique.** Elle prépare ses entretiens individuels en consultant le dashboard. Au lieu de découvrir l'élève en 15 min, elle arrive **avec un contexte** : "Tu as exploré les métiers du social et de la santé, tu hésites entre kiné et infirmier — qu'est-ce qui te retient sur kiné ?"

Les entretiens passent de 15 min de présentation à 15 min de conseil ciblé.

**Résolution.** Fin d'année : Mme Dupont fait remonter à sa direction que l'outil l'a aidée. Le lycée signe pour une licence payante l'année suivante (3 pilotes sur 5 convertissent — l'objectif business).

**Capacités révélées :** Espace conseiller B2B (auth, gestion cohorte, invitations) • Dashboard cohorte agrégé + dashboard élève individuel • Détection "profils à risque" (signaux de décrochage) • Gestion consentement élève pour partage profil au conseiller • Reporting fin d'année pour conversion pilote → payant

### Parcours 5 — M. Martin, parent prescripteur

**Personnage :** Pascal Martin, père de Sarah (parcours 1), 48 ans, cadre dans le bâtiment. Inquiet pour l'avenir de sa fille, peu équipé pour l'aider.

**Scène d'ouverture.** Sarah lui montre Path-Advisor un soir. Il regarde par-dessus l'épaule, sceptique.

**Action montante — Espace parent.** Sarah l'invite (avec son consentement à elle, contrôle côté élève). Il crée un compte parent **lié** au sien. Il voit :
- Les métiers que Sarah explore (pas son journal intime, mais les recos)
- Les graphes de parcours qu'elle a ouverts
- Le coût et la durée totale de chaque parcours
- Pas de notes, pas d'appréciations enseignants (frontière de confidentialité posée)

**Climax — Rassurance.** Pascal voit qu'ingénieure biomédicale offre des débouchés solides et un revenu médian correct. Il arrête de pousser médecine. Il dit oui pour le passage en premium (il paie l'abonnement).

**Résolution.** M. Martin recommande Path-Advisor à 3 collègues qui ont des enfants en lycée — viralité organique B2C.

**Capacités révélées :** Espace parent lié au compte élève (contrôle côté élève) • Vue parent : recos et coûts visibles, données scolaires masquées • Gestion des liens famille + droits d'accès différenciés • Paiement premium par le parent au profit de l'élève • Mécanique de recommandation virale (parrainage)

### Parcours 6 — Mme Garcia, responsable admissions école partenaire (envoi anticipé)

**Personnage :** Carla Garcia, responsable communication & admissions à Polytech Marseille. Cherche à attirer des profils qualifiés au-delà du périmètre régional habituel.

**Scène d'ouverture.** Path-Advisor lui propose un partenariat : recevoir gratuitement les profils d'élèves qualifiés qui visent Polytech Marseille, avec leurs données scolaires + motivations. Elle accepte.

**Action montante — Réception du profil.** Elle reçoit un **email + push notification** : *"Sarah, Terminale spé Maths/SVT, moyenne 14,8, profil scoré 78 % de compatibilité avec votre cursus ingénierie biomédicale, a déclenché un envoi anticipé."*

Elle clique : fiche profil complète sur Path-Advisor (vue école), avec bulletins synthétiques, appréciations, motivation déclarée par l'élève.

**Climax — Trois actions possibles.** Elle a 7 jours pour répondre via 3 boutons :
- ✅ **"Profil intéressant — candidature encouragée"** → Sarah reçoit la réponse + sa stat d'admission Polytech monte +14 points
- ❌ **"Profil non aligné"** → Sarah reçoit un message diplomatique + stat ajustée à la baisse (avec explicabilité)
- 📅 **"Demande d'entretien"** → Sarah reçoit une proposition de RDV visio

Mme Garcia choisit "entretien" — Polytech veut sécuriser ce profil.

**Résolution.** Sarah candidate à Polytech en première position sur Parcoursup. Polytech enregistre 3 admissions hors région via Path-Advisor cette année — la convertit en argument pour signer un partenariat plus structuré l'année 2.

**Capacités révélées :** Compte école/admissions séparé (auth dédiée, rôles) • File de réception profils + email/push de notification • Vue profil élève côté école (avec consentement élève déclenché par envoi anticipé) • 3 actions de réponse + impact sur stat d'admission élève • Module RDV visio (intégré ou délégué) • Reporting école : nb profils reçus, conversions, ROI

### Parcours 7 — Karim, admin Path-Advisor (back-office)

**Personnage :** Karim, content & data ops chez Path-Advisor. Responsable du référentiel professions/formations et de la qualité des données.

**Tâches quotidiennes :**
- Curer le référentiel des 50+ professions MVP (descriptifs, prérequis, débouchés, journées types)
- Mettre à jour les 100+ formations (frais, sélectivité, places disponibles, dates Parcoursup)
- Traiter les signalements d'élèves ("ce métier n'est plus exact", "cette école a déménagé")
- Modérer les motivations déclarées par les élèves dans les envois anticipés (anti-discrimination, contenu inapproprié)
- Auditer les stats d'admission : versionner les modèles, détecter les biais, documenter les recalibrages

**Capacités révélées :** Back-office référentiel professions/formations (CRUD éditorial) • File de signalements + workflow modération • Versioning des modèles de recommandation + audit trail • Modération de contenu utilisateur (motivations envois anticipés) • Tableau de bord qualité données (couverture, fraîcheur, signalements)

### Journey Requirements Summary

| Domaine | Capacités |
|---|---|
| **Auth & comptes** | Inscription élève (mineur, consentement parental < 15 ans) • Compte parent lié • Compte conseiller B2B • Compte école/admissions • Compte admin Path-Advisor |
| **Profil & onboarding** | Saisie passions/intérêts/valeurs • Import bulletins (PDF + OCR) • Onboarding différencié (collège / lycée général / lycée pro) • Mode "profil dégradé" sans bulletins |
| **Moteur de recommandation vocationnelle** | Scoring métiers avec explicabilité • 50+ professions MVP • Affichage incertitude • Variantes selon niveau scolaire |
| **Moteur de parcours** | Graphes interactifs • 100+ formations MVP • Stats d'admission personnalisées • Logique bac pro avec lycée associé • Intégration carte scolaire + Affelnet |
| **Engagement & continuité** | Notifications, retours réguliers, suivi évolution profil |
| **Premium B2C** | Paiement (élève ou parent) • Envoi anticipé écoles • RDV visio écoles |
| **B2B conseiller** | Dashboard cohorte • Vue élève individuelle (avec consentement) • Détection profils à risque • Reporting conversion |
| **Écoles partenaires** | Réception profils par email + push • Vue profil école • 3 actions réponse • Impact stat d'admission • Reporting |
| **Back-office** | Référentiel professions/formations • Modération signalements & contenu • Versioning modèles • Audit qualité données |
| **Conformité** | Consentement parental • Gestion droits d'accès parent / conseiller / école • Confidentialité bulletins (frontières par rôle) • RGPD |

## Domain-Specific Requirements

### Conformité réglementaire (Compliance & Regulatory)

**Cadre RGPD + données de mineurs :**
- **RGPD** (UE) — base légale du traitement : exécution d'un contrat (B2C premium) et intérêt légitime + consentement (recommandations IA, partage profil aux écoles)
- **Loi Informatique et Libertés** (CNIL, France) — âge du consentement numérique abaissé à **15 ans** ; en dessous, **consentement parental requis par simple opt-in email parent** (lien de validation envoyé à l'adresse parent fournie par l'élève)
- **DPIA (Analyse d'Impact Relative à la Protection des Données)** obligatoire — déclencheurs cumulés : traitement automatisé à grande échelle + données de mineurs + impact significatif sur le sujet (orientation = décision majeure)
- **Désignation d'un DPO** (Data Protection Officer) — exigible compte tenu du volume et de la sensibilité

**Décisions automatisées (RGPD art. 22) :**
- Les recommandations vocationnelles et stats d'admission sont des **profilages** au sens RGPD
- Obligations associées : explicabilité du score, droit à l'intervention humaine, droit de contester le résultat
- Implémenté en MVP via : explications visibles "voici les signaux qui ont fait monter ce métier", lien "demander une revue humaine"

**Accessibilité légale :**
- **RGAA 4.1** (équivalent français du WCAG 2.1) — niveau **AA obligatoire** pour services publics et établissements publics (lycées, collèges). Sans RGAA AA, pas de marché B2B Éducation Nationale en growth.
- En MVP : RGAA AA sur les parcours critiques (onboarding, recos, graphes) — full RGAA en growth

**Hébergement et souveraineté :**
- **Données stockées en UE obligatoire** (RGPD)
- Hébergement **France ou UE** recommandé — pour B2B Éducation Nationale, la souveraineté française devient un argument commercial fort (alignement doctrine "Cloud au centre" et SecNumCloud)
- Cibler à terme : hébergeur certifié **SecNumCloud** (ANSSI) ou équivalent

**Cadre éducatif et institutionnel :**
- **Code de l'éducation** — articulation avec Parcoursup, Affelnet ; pas de revente de données aux écoles → important commercialement et déontologiquement
- **Doctrine numérique éducatif** (MENJS) — alignement souhaitable pour pénétrer le B2B EN
- **Référentiel général de sécurité (RGS 2.0)** — exigible pour les contractants publics en growth

### Contraintes techniques (Technical Constraints)

**Sécurité :**
- Chiffrement au repos (AES-256) et en transit (TLS 1.3 minimum)
- Authentification : MFA optionnel B2C, **MFA obligatoire** pour comptes conseiller, école, admin
- Gestion des secrets via coffre dédié (HashiCorp Vault, AWS Secrets Manager, ou équivalent)
- Logs d'audit complets pour : accès aux profils élèves par tiers (parent, conseiller, école, admin) — exigence RGPD + traçabilité
- Pen-test annuel à partir de growth

**Confidentialité par rôle (frontières strictes) :**

| Rôle | Voit | Ne voit pas |
|---|---|---|
| **Élève** | Tout son profil | — |
| **Parent** (lié) | Métiers explorés, parcours, coûts | Bulletins détaillés, appréciations enseignants |
| **Conseiller B2B** (avec consentement élève) | Profil complet + activité | Identifiants de connexion, données paiement |
| **École partenaire** (envoi anticipé, consentement élève + parent) | Profil scolaire synthétique + motivation déclarée | Autres écoles ciblées, autres recos vocationnelles |
| **Admin Path-Advisor** | Référentiel + signalements modérés | Données personnelles élèves (sauf en cas d'incident, avec workflow d'audit) |

**Performance et disponibilité :**
- Latence moteur de recommandation < 3 s en MVP, < 1,5 s en growth
- Disponibilité 99 % MVP, 99,5 % growth
- Saisonnalité forte : pic d'usage **janvier-mars** (préparation Parcoursup) et **mai-juillet** (vœux + réponses) — capacité prévisionnelle indispensable

**Modération de contenu :**
- Motivations déclarées par l'élève dans les envois anticipés → modération anti-discrimination, propos haineux, données personnelles tierces
- Files de signalements (référentiel professions/formations) → workflow back-office traité sous 7 jours

**Versioning et auditabilité des modèles IA :**
- Chaque version du moteur de recommandation est versionnée avec son dataset d'entraînement, ses signaux et son scoring
- Audit trail des décisions : pour chaque reco, on peut rejouer le scoring
- Détection et documentation des biais : audit régulier (genre, origine sociale via codes postaux, type d'établissement d'origine)

### Exigences d'intégration (Integration Requirements)

**MVP :**
- **Import bulletins par PDF + OCR** avec **saisie manuelle assistée en plan B** — un formulaire structuré permet à l'élève de recopier ses notes lorsque l'OCR échoue (PDF non standardisés selon établissements)
- **Paiement** : Stripe ou équivalent (B2C premium) + facturation classique (B2B)
- **Email transactionnel** : SendGrid / Postmark / équivalent
- **Push notifications** : web push standard

**Growth :**
- **ENT/Pronote** — API ou connecteur officiel pour import automatique des bulletins (priorité partenariale)
- **Parcoursup / Affelnet** — pas d'API publique disponible aujourd'hui ; veille produit nécessaire (le ministère publie périodiquement des datasets ouverts)
- **SI éducation nationale** (annuaire BCN/RNE pour les établissements) — référentiel public exploitable

### Risques domaine et mitigations

| Risque | Impact | Mitigation MVP |
|---|---|---|
| **Biais algorithmique** (recos qui reproduisent les inégalités sociales/territoriales) | Crédibilité produit + risque CNIL + reputational | Audit régulier des biais, explicabilité, dataset d'entraînement diversifié (comité éthique trimestriel reporté en growth) |
| **Pression école sur le scoring** (école payant pour mieux apparaître) | Perte de neutralité = perte du différenciateur central | Engagement contractuel + transparence publique du modèle de scoring + audit externe en growth |
| **Mauvaise réception parents** (perception "outil qui décide à la place") | Adoption B2C bloquée | Espace parent qui clarifie le rôle d'aide vs décision, ton produit explicite sur ce point |
| **Incident données mineurs** (fuite, accès non autorisé) | RGPD lourdes amendes + impact médiatique majeur | Chiffrement, MFA staff, audit accès, plan réponse incident, notification CNIL < 72h |
| **Refus B2B Éducation Nationale** (positionnement commercial vs public service) | Marché B2B bloqué | Neutralité commerciale documentée, hébergement souverain, RGAA, alignement doctrine MENJS |
| **Inexactitude statistiques d'admission** (élève déçu post-Parcoursup) | NPS, image, juridique | Affichage explicite de l'incertitude, fourchettes plutôt que valeurs ponctuelles, mise à jour annuelle des modèles |
| **Désengagement (saisonnalité forte)** | LTV B2C limité | Mécaniques de retour (nouvelles écoles, nouvelles formations, échéances Parcoursup) + collège (cycle plus long) |
| **Échec OCR bulletins** (formats hétérogènes selon établissements) | Friction onboarding | Saisie manuelle assistée en plan B + détection de patterns OCR par établissement émetteur pour amélioration continue |

## Innovation & Novel Patterns

### Detected Innovation Areas

**1. Architecture en double moteur articulé**

Le cœur d'innovation de Path-Advisor n'est pas l'existence séparée de recommandation vocationnelle (RIASEC depuis les années 1970) ni de recommandation de parcours (sites de comparaison d'écoles depuis 2000). C'est l'**articulation produit** des deux dans une expérience continue :

> Profil → recommandation vocationnelle → sélection d'un métier → recommandation de parcours scolaires → stats d'admission par école → action (candidature, envoi anticipé)

Aucun acteur ne livre aujourd'hui ce flux complet dans un seul produit. Onisep s'arrête au métier (et donne des fiches statiques). Diplomeo commence à l'école (sans contexte vocationnel). Parcoursup gère la candidature (sans conseil amont). Path-Advisor est le premier à traiter le flux *bout en bout*.

**2. Donnée scolaire objective comme moteur principal de personnalisation**

Tous les outils d'orientation existants (Onisep, Diagoriente, les tests métier MOOC) reposent sur du **déclaratif pur** : l'élève répond à des questionnaires (RIASEC, intérêts, valeurs). Path-Advisor croise ce déclaratif avec des **données scolaires objectives** : bulletins, notes, appréciations enseignants. Cela permet :

- de pondérer le déclaratif par la réalité scolaire (l'élève qui *dit* aimer les maths mais qui a 8/20 doit voir ses recommandations ajustées)
- de calculer des **statistiques d'admission personnalisées** pour chaque école cible (impossible sans le profil scolaire réel)
- de créer un avantage défensif structurel : l'élève ne peut pas reconstruire ce profil sur une plateforme concurrente sans réimporter ses bulletins

C'est cette objectivité qui rend les recommandations crédibles et le scoring auditable.

**3. Envoi anticipé du profil aux écoles — biface assumé**

L'idée du *"profil envoyé en avance de phase à une école pour augmenter les chances d'admission"* est une nouveauté de marché. Aucun équivalent en orientation post-bac francophone. Le pattern le plus proche conceptuellement vient du recrutement professionnel (LinkedIn Recruiter, Welcome to the Jungle) où le candidat envoie un profil à des employeurs avant un job ouvert. Path-Advisor importe cette mécanique dans le domaine scolaire.

Innovation produit : la **réponse de l'école** (intéressant / non aligné / RDV) devient un signal qui **modifie en temps réel la statistique d'admission** affichée à l'élève. Le profil n'est plus statique — il vit, il interagit, il se déplace.

Innovation business : Path-Advisor crée un **marketplace biface** sans tomber dans le piège du "lead seller" (cf. Diplomeo). L'école *ne paie pas* pour mieux apparaître ; elle paie (en growth) pour répondre à un volume plus large de profils qualifiés. C'est l'élève qui choisit où envoyer, pas un algorithme orienté revenus.

**4. Continuité temporelle "compagnon" 3ème → bac+2/3**

La pratique de marché actuelle traite l'orientation comme un **événement ponctuel** centré sur Parcoursup en Terminale. Path-Advisor adopte le pattern *"compagnon continu"* qu'on retrouve dans la santé (apps de fitness/sommeil), la finance personnelle (Linxo, YNAB), ou l'apprentissage des langues (Duolingo). Le profil évolue, les recommandations s'adaptent, la plateforme apprend de l'élève au fil des années.

C'est un **engagement model** rare en EdTech orientation, et il transforme l'économie : LTV étalée sur plusieurs années plutôt qu'un pic d'usage de 3 mois.

**5. Explicabilité IA en première intention (pas en option)**

Là où la plupart des produits IA grand public traitent l'explicabilité comme une feature avancée ou une exigence légale subie, Path-Advisor en fait un **élément central de l'UX** : chaque score est accompagné d'une visualisation "voici les signaux qui ont fait monter ce métier". Cette transparence est :

- une obligation RGPD (art. 22 sur les décisions automatisées)
- un avantage produit (la confiance vient de la compréhension, pas du marketing)
- un différenciateur vs. les outils déclaratifs opaques

**6. Architecture IA hybride — recommandation statistique + deep learning**

Path-Advisor est nativement un produit *AI-first*, pas un produit "avec une couche IA en option". Le moteur de recommandation est conçu comme une **architecture hybride** combinant deux approches complémentaires :

**a) Moteur de recommandation statistique** (filtrage collaboratif + content-based + facteurs explicites)
- Scoring vocationnel basé sur des features structurées : notes, appréciations enseignants (NLP), passions déclarées, valeurs, type d'établissement, parcours académique
- Filtrage collaboratif sur les cohortes : *"des élèves au profil similaire ont aussi exploré ces métiers / ont effectivement intégré ces écoles"*
- Explicabilité native par construction (poids des features visibles → respect RGPD art. 22)
- Adapté au MVP : pas besoin de gros volumes de données pour démarrer (cold-start gérable via le content-based)

**b) Moteur de deep learning** (modèles de représentation et prédiction d'admission)
- **Embeddings** des profils élèves et des couples métier/formation pour capturer des similarités non triviales (un élève passionné de jeux vidéo + bon en maths peut matcher avec "ingénieur en game design" sans qu'aucune feature explicite ne le code)
- **Modèles prédictifs d'admission** : probabilité d'admission par école cible, conditionnée sur le profil scolaire + historique des admissions
- **NLP sur appréciations enseignants** : transformer les phrases libres ("élève sérieux, manque de confiance", "très créatif mais inégal") en signaux exploitables
- Modèles versionnés avec dataset d'entraînement traçable + audit de biais régulier

**Architecture combinée :** le moteur statistique produit des recommandations explicables servies en premier (transparence, confiance, conformité). Le deep learning enrichit les recommandations avec des cas que les règles manquent + alimente le scoring d'admission. L'utilisateur voit toujours une explication structurée ; le DL fonctionne en *renforcement*, pas en remplacement.

**Pourquoi cette architecture maintenant :**
- **Maturité de l'IA grand public** rend acceptable et attendu d'avoir un produit IA en EdTech (le scepticisme post-LLM est plus faible qu'il y a 5 ans)
- **Volume de données scolaires** suffisant en open data (Parcoursup, ONISEP) pour entraîner les premiers modèles d'admission
- **Coût d'inférence** abordable : les modèles peuvent tourner sur de l'infrastructure cloud standard, pas besoin de GPU dédié pour le scoring d'un élève

### Market Context & Competitive Landscape

| Acteur | Couverture | Modèle | Faiblesse |
|---|---|---|---|
| **Onisep** | Information générique métiers + formations | Public, gratuit | Aucune personnalisation, contenu statique, format vieillissant |
| **Diagoriente** | Questionnaire compétences + recommandation métier | Public, gratuit | Pas de parcours scolaire, pas de stats d'admission, profil purement déclaratif |
| **Parcoursup** | Candidature post-bac | Public, obligatoire | Outil de candidature, pas de conseil amont |
| **Diplomeo** | Annuaire formations + mise en relation école | Privé, **lead seller** | Conflit d'intérêt structurel, pas de moteur vocationnel, pas de scoring objectif |
| **L'Étudiant / Studyrama** | Annuaire formations + classements | Privé, publicitaire | Snapshot statique, pas de personnalisation par profil scolaire |
| **MyJobGlasses, Mentor Goal** | Mise en relation lycéen ↔ professionnel | Privé, freemium | Mentorat ponctuel, pas de recommandation, pas de parcours |
| **Inspire (ex-Frateli)** | Mentorat orientation pour boursiers | Associatif | Niche, sans technologie de reco |

**Position unique de Path-Advisor :** seul acteur combinant (a) moteur vocationnel + (b) moteur parcours + (c) données scolaires objectives + (d) neutralité commerciale + (e) continuité temporelle + (f) feature levier d'admission + (g) architecture IA hybride. Chacun pris isolément existe ailleurs ; la combinaison est inédite en francophonie.

**Veille à exercer :**
- **Aux États-Unis** : Niche.com (data-driven choix d'université), Naviance/Cialfo (B2B high schools), CommonApp — pas d'équivalent francophone des moteurs vocationnels intégrés
- **France** : surveiller émergence d'acteurs IA grand public sur l'orientation (les LLMs grand public commencent à être utilisés comme conseillers d'orientation par les élèves → risque de désintermédiation si Path-Advisor n'apporte pas plus que ChatGPT + un PDF Onisep)

### Validation Approach

**Phase 1 — Validation différenciateur sur le MVP (mois 0-6) :**

- **Test du double moment "aha"** : enquête utilisateurs sur 50 lycéens avant lancement public, mesurer le taux d'élèves qui rapportent une découverte significative (métier ou parcours inconnu) après usage
- **Test de fiabilité du scoring vocationnel** : panel test avec 20 lycéens ayant un projet d'orientation déjà clair → la reco top-3 du moteur inclut-elle leur projet déclaré ? Cible : ≥ 80 %
- **Test des modèles de recommandation** : benchmark sur dataset annoté (profils + métiers cibles validés humainement) → cible précision top-5 ≥ 75 % en MVP
- **Audit de biais ML initial** : test du modèle sur sous-populations (genre, type d'établissement, code postal) → écart inter-groupes < 10 % avant mise en production
- **Test de la valeur perçue des stats d'admission** : A/B test sur l'affichage avec/sans stats personnalisées → mesure d'engagement (consultation graphe complet, retour à 7j)

**Phase 2 — Validation business sur 6-12 mois :**

- **Conversion premium** : 5 % cible (modèle bouche-à-oreille + parents). Si < 2 %, repenser la proposition de valeur premium
- **Conversion B2B pilote → payant** : 3 sur 5 cible. Si < 2, ajuster soit le dashboard conseiller, soit le pricing, soit le pitch
- **Adoption "envoi anticipé"** : % d'utilisateurs premium qui activent au moins 1 envoi. Cible : 60 %. Si faible, la feature premium ne justifie pas le prix

**Phase 3 — Validation impact (mois 12-24) :**

- **Taux d'admission effectif** dans les écoles recommandées (suivi cohorte post-Parcoursup, données déclaratives)
- **Réduction de la réorientation à 1 an** : comparer les cohortes utilisateurs vs population générale (20 % de réorientation en licence en France) — cible : -5 points

### Risk Mitigation (innovation-specific)

| Risque innovation | Mitigation |
|---|---|
| **Le double moteur n'est pas perçu comme une innovation par l'élève** (il voit "encore un test métier") | Onboarding qui scénarise les deux aha moments, copywriting explicite sur l'enchaînement, démos visuelles avant inscription |
| **Les stats d'admission sont fausses ou peu fiables** (modèle prédictif insuffisant) | MVP basé sur données publiques agrégées (Parcoursup open data) ; modèle prédictif personnalisé en growth seulement, avec fourchettes d'incertitude |
| **L'envoi anticipé échoue à attirer les écoles** (pas assez de profils, pas assez de volume) | Bundle B2B pilote + envoi anticipé : les 5 écoles pilotes B2B sont aussi les premières écoles partenaires côté envoi anticipé → garantie de volume initial |
| **Désintermédiation par LLMs grand public** (l'élève va sur ChatGPT) | Différenciation par la donnée scolaire intégrée (un LLM grand public n'a pas accès aux bulletins) + référentiel curé + neutralité auditée |
| **Pression réglementaire sur les décisions automatisées en éducation** (CNIL, MENJS, AI Act UE) | Mise en conformité RGPD art. 22 + AI Act dès le MVP (explicabilité, opt-out, revue humaine), positionnement éthique défendable |
| **Effet réseau biface lent à démarrer côté écoles** (peu d'écoles → faible valeur envoi anticipé → peu de premium) | Démarrage régional ciblé (ex. Île-de-France ou Auvergne-Rhône-Alpes) pour atteindre une densité d'écoles partenaires localement avant d'étendre |
| **Drift des modèles ML** (la pertinence se dégrade avec le temps : nouveaux métiers, évolution des formations, changements Parcoursup) | Pipeline de réentraînement régulier (tous les 6 mois ou trigger statistique sur métriques de qualité), monitoring de la distribution des prédictions en production |
| **Hallucination ou recommandation aberrante** (métier inadapté, école inexistante, stat d'admission grotesque) | Garde-fous post-modèle : règles métier en sortie (vérification cohérence prérequis métier ↔ profil), liste blanche du référentiel curé, seuil de confiance minimum sous lequel on n'affiche pas la reco |

## Web App SaaS — Spécifications techniques

### Project-Type Overview

Path-Advisor est une **Web App SaaS hybride** combinant un produit grand public B2C (lycéens, parents) et une offre B2B (établissements scolaires, écoles partenaires). Architecture monolithique modulaire en MVP — pas de microservices prématurés — avec une séparation claire du moteur de recommandation (service IA dédié, scaling indépendant).

**Décisions architecturales structurantes :**
- Front : **SPA + SSR hybride** (Next.js ou équivalent) — pour combiner expérience interactive (graphe de parcours, dashboard) et SEO B2C (pages métiers/formations indexables)
- Back : monolithe modulaire **Django 5 + DRF + drf-spectacular (Python 3.12+)** avec service IA séparé **FastAPI** (bibliothèques ML/DL natives Python) — choix figé en Architecture Decision Document
- Stockage : PostgreSQL (transactionnel + vector store pour embeddings via pgvector) + S3 (bulletins chiffrés)
- Architecture **PoC-local-first** : tout doit pouvoir tourner sur machine de dev avec Docker Compose avant tout déploiement cloud

### Technical Architecture Considerations

**Front-end :**
- **SPA + SSR** via Next.js (ou Nuxt si écosystème Vue) — SSR pour pages métiers/formations indexables, CSR pour zones interactives (graphe parcours, dashboard conseiller)
- Responsive design mobile-first (cible primaire = lycéens sur mobile)
- Pas d'app mobile native MVP — PWA installable comme fallback

**Back-end :**
- API REST + couche GraphQL optionnelle si besoin de jointures complexes côté dashboard B2B
- Service IA séparé exposé en API interne (FastAPI ou équivalent) — versionnement modèles indépendant du back applicatif
- Job queue **Celery + Redis** (Python-native, mature, scaling clair) pour : OCR async, génération de notifications, envoi anticipé, recalculs de stats

**Données :**
- **PostgreSQL** : tables transactionnelles + référentiels (professions, formations, établissements)
- **pgvector** (extension PostgreSQL) : embeddings élèves + métiers + formations pour similarités vectorielles
- **S3-compatible (chiffré, région EU)** : bulletins PDF + exports
- Cache **Redis** : sessions, rate limiting, recos pré-calculées

**Hébergement :**
- Cible : France ou UE obligatoire (RGPD + B2B EN)
- Recommandé : Scaleway (FR), OVH (FR), AWS Paris/Frankfurt (EU)
- Cibler **SecNumCloud** en growth (argument B2B EN)

### Modèle Multi-Tenant (Hybride dès le MVP)

Choix : **tenancy hybride (option c)** dès le MVP, pas de migration risquée plus tard.

**Données partagées (cross-tenant) :**
- Référentiel professions (50+ MVP, 500+ growth)
- Référentiel formations / établissements (100+ MVP)
- Modèles de recommandation IA versionnés
- Logs d'audit et téléimétrie produit anonymisée

**Données tenant (isolées par établissement B2B) :**
- Cohorte d'élèves rattachés (relations établissement ↔ élève)
- Dashboard conseiller + reporting
- Configuration pédagogique (curriculum spécifique, périmètre métiers conseillés)

**Données utilisateur (isolées par élève) :**
- Profil personnel, bulletins, recos, parcours explorés
- Envoi anticipé : isolation forte par élève, l'école partenaire ne voit que les profils qui lui ont été envoyés

**Mécanique d'isolation :**
- Colonnes `tenant_id` (établissement) + `user_id` (élève) sur toutes les tables sensibles
- Row-Level Security PostgreSQL (RLS) pour empêcher les fuites cross-tenant au niveau DB
- Tests d'intégration de l'isolation en CI (régression critique)

### Matrice RBAC (Permissions par Rôle)

| Rôle | Scope | Permissions clés | Restrictions |
|---|---|---|---|
| **Élève** | Self | CRUD profil • vues recos/parcours • déclencher envoi anticipé (premium) • inviter parent • inviter conseiller (consentement) | — |
| **Parent** (lié) | Élève lié | Vue métiers explorés + parcours + coûts • paiement premium au profit élève | Pas d'accès bulletins détaillés, pas d'accès aux appréciations enseignants |
| **Conseiller B2B** | Cohorte établissement | Vue cohorte agrégée • vue élève individuelle (si consentement) • exports anonymisés | Pas d'écriture sur profil élève • pas d'accès identifiants/paiement |
| **École partenaire** | Profils reçus | Vue profil scolaire synthétique + motivation • 3 actions de réponse (intéressant / non aligné / RDV) • reporting interne | Pas d'accès aux autres écoles ciblées par l'élève • pas d'accès aux recos vocationnelles non liées à elle |
| **Admin Path-Advisor** | Plateforme | CRUD référentiel professions/formations • modération signalements & contenu • versioning modèles IA | Pas d'accès données personnelles élèves sauf workflow incident (escalade DPO, journal d'audit) |
| **Support utilisateur** | Tickets ouverts | Vue masquée profil + journal activité élève • répondre aux tickets | Pas d'accès bulletins sans escalade DPO + consentement élève |

### Tiers d'Abonnement

| Tier | Audience | Prix | Inclus | Limites |
|---|---|---|---|---|
| **Freemium B2C** | Lycéens, parents | Gratuit | Profil • Recos vocationnelles • 1 graphe de parcours par mois • Stats top 3 écoles | Pas d'envoi anticipé • Pas de vue parent • Pas de notifications proactives |
| **Premium B2C** | Lycéens, parents | 10,99 €/mois | Tout Freemium + graphes illimités • Stats toutes écoles • Envoi anticipé • Vue parent • Notifs proactives • RDV visio écoles | — |
| **Pilote B2B** | 5 établissements MVP | Gratuit 12 mois | Dashboard conseiller complet • Cohorte jusqu'à 250 élèves • Support email | Durée 12 mois, conversion payante ou abandon |
| **Licence B2B Standard** | Établissements (growth) | 5 000 €/an | Dashboard conseiller • Cohorte 100 utilisateurs • Support prioritaire • Exports reporting | Au-delà : palier supplémentaire |
| **Licence B2B Enterprise** | Multi-établissements / collectivités (vision) | Sur devis | Tenancy dédiée option • SLA renforcé • API exports • Audit annuel | — |

### Performance & Browser Support

**Performance MVP :**
- Latence moteur de recommandation : **< 3 s** (synchrone)
- TTFB pages publiques (SEO) : **< 1 s**
- LCP (Largest Contentful Paint) mobile : **< 2,5 s**
- Disponibilité : **99 % MVP, 99,5 % growth**

**Saisonnalité :**
- Pics **janvier-mars** (préparation Parcoursup) et **mai-juillet** (vœux + réponses)
- Auto-scaling configuré sur ces périodes (multiplier x3 la capacité de base)

**Browsers supportés :**

| Navigateur | Versions cibles |
|---|---|
| Chrome | ≥ 100 (desktop + Android) |
| Safari | ≥ 15 (macOS + iOS) |
| Firefox | ≥ 100 |
| Edge | ≥ 100 |
| Internet Explorer | Non supporté |

**Accessibilité :** RGAA 4.1 niveau AA sur parcours critiques en MVP (full RGAA en growth — cf. domain requirements).

### Stratégie SEO (B2C critique)

**Pages indexables (SSR) :**
- Pages métier : `/metiers/{slug}` — fiche profession + parcours types + écoles
- Pages formation : `/formations/{slug}` — fiche école/formation + débouchés + stats publiques
- Landing pages long-tail : `/devenir-{metier}`, `/{niveau}/quel-bac-pour-{metier}`, `/{niveau}/integrer-{ecole}`
- Pages éditoriales : guides Parcoursup, articles orientation

**Optimisations techniques :**
- Sitemap XML auto-généré et soumis à Search Console
- Balisage Schema.org : `Occupation`, `EducationalOrganization`, `Course`, `FAQPage`
- Open Graph + Twitter Cards pour partage social (canal de viralité)
- Core Web Vitals au vert (LCP, FID, CLS)
- Pas de contenu derrière JavaScript only (SSR garantit l'indexabilité)

### Stratégie Temps Réel & Asynchronisme

| Cas d'usage | Mode | Justification |
|---|---|---|
| **Recommandation vocationnelle (génération)** | Synchrone, < 3 s | Cœur de l'expérience aha — pas d'attente |
| **Graphe de parcours + stats admission** | Synchrone | Affichage immédiat après clic métier |
| **Envoi anticipé du profil à l'école** | Asynchrone (queue) | Email + push, pas critique en temps réel |
| **Réponse école → MAJ stat élève** | Asynchrone, propagation < 5 min | Notification push + email, pas de WebSocket nécessaire |
| **Import OCR bulletins** | Asynchrone, < 30 s | Traitement lourd, UX avec indicateur de progression |
| **Recalcul cohorte (dashboard conseiller)** | Asynchrone planifié (toutes les heures) | Pas de besoin temps réel |

**Décision :** **pas de WebSocket en MVP**. Le polling léger (toutes les 30s sur les pages critiques) + notifications push suffisent. Simplifie infra et coûts.

### Intégrations & Outils

**Principe directeur : PoC local first.** Tous les choix d'intégration doivent permettre un environnement de développement local complet via Docker Compose, sans dépendance dure à un service cloud. On bascule en cloud à la mise en production, mais le code reste portable.

| Type | Outil production | Équivalent PoC local | Critique en MVP ? |
|---|---|---|---|
| **Paiement B2C** | Stripe | Stripe test mode (clés sandbox locales) | Oui |
| **Email transactionnel** | Postmark ou SendGrid | **Mailpit** (capture mail local) | Oui |
| **Push notifications** | Web Push standard + OneSignal | Web Push standard local (clés VAPID dev) | Oui |
| **OCR bulletins** | AWS Textract ou Mindee | **Tesseract OCR** open source en Docker | Oui |
| **Analytics produit** | PostHog Cloud EU (Frankfurt) ou Amplitude | **PostHog self-hosted** en Docker | Oui |
| **Visio RDV école** | Lien Whereby / Daily.co | Liens jitsi.org self-hosted | Souhaitable |
| **CRM B2B** | HubSpot ou Pipedrive | Pas requis pour PoC | Préférable, peut attendre |
| **Stockage objets** | S3 EU (Scaleway, AWS Paris) | **MinIO** S3-compatible en Docker | Oui |
| **Base de données** | PostgreSQL managé (RDS, Scaleway) | PostgreSQL 16 + extension pgvector en Docker | Oui |
| **Cache / Queue** | Redis managé | Redis en Docker | Oui |
| **Modèles ML** | API service interne (FastAPI) | Même service en Docker, modèles locaux (HuggingFace) | Oui |
| **LLM (NLP appréciations enseignants)** | OpenAI / Mistral API EU | Modèle local (Mistral 7B via Ollama) pour PoC | Oui |
| **Monitoring** | Grafana Cloud + Sentry | Prometheus + Grafana + Sentry self-hosted en Docker | Oui |

**Environnement PoC local cible :**
- `docker-compose up` lance toute la stack (front, back, IA, DB, cache, queue, OCR, mail, monitoring, analytics, stockage objets)
- Seeds de référentiel professions/formations injectés au boot pour avoir un produit utilisable end-to-end sans appel cloud
- Variables d'environnement clairement séparées local / staging / production

### Implementation Considerations

**Ordre de mise en place recommandé MVP (12 sprints estimés) :**

1. **Sprints 1-2 — Fondations** : auth multi-rôle, RBAC, multi-tenant hybride, stockage chiffré bulletins, RGPD/DPIA, consentement parental email
2. **Sprints 3-4 — Onboarding élève** : profil + import bulletins (PDF + OCR + saisie manuelle assistée fallback) + déclaratif (passions, intérêts, valeurs)
3. **Sprints 5-6 — Moteur vocationnel** : architecture statistique + content-based + 50 professions référencées + UI recos avec explicabilité
4. **Sprints 7-8 — Moteur parcours** : graphe interactif + 100 formations référencées + stats admission (basées open data Parcoursup) + carte scolaire (Affelnet 3ème, Parcoursup lycéen)
5. **Sprint 9 — Premium + Stripe** : tiers freemium/premium, paiement, gating de fonctionnalités
6. **Sprint 10 — Envoi anticipé écoles** : flux complet école (auth, réception profil, 3 actions, MAJ stat), email/push, intégration aux pilotes B2B
7. **Sprint 11 — Dashboard conseiller B2B** : cohorte, vue élève (consentement), détection profils à risque, exports
8. **Sprint 12 — Polish, RGAA AA, perfs, monitoring, lancement bêta** : SEO setup, accessibilité critique, observabilité, plan incident

**Risques techniques majeurs :**
- **OCR bulletins** : formats hétérogènes selon établissements → fallback manuel essentiel + collecte de patterns pour amélioration
- **Pré-calcul stats admission** : sans modèle prédictif fin en MVP → fourchettes basées open data Parcoursup, indication explicite de l'incertitude
- **Performance moteur reco sous charge** : tests de charge sur cohorte 500 utilisateurs simultanés (= 5 % d'usage simultané sur 10K MAU growth)
- **Compatibilité PoC local ↔ cloud production** : maintenir une CI qui teste les deux modes pour détecter les divergences précoces

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**Approche MVP retenue : Problem-Solving × Experience (double accent)**

Path-Advisor est un produit où la valeur naît de l'expérience — les deux moments "aha" sont le cœur de la promesse. Mais le produit doit aussi *fonctionner de bout en bout* dès le MVP : un élève doit pouvoir, en moins de 20 minutes, passer de l'inscription à un graphe de parcours actionnable. Pas de demi-mesure :

- **Problem-solving non négociable** : l'élève résout son problème d'orientation, même avec un référentiel limité (50 métiers / 100 formations) et un modèle prédictif simplifié (open data Parcoursup, pas de DL custom)
- **Experience non négociable** : les 2 aha moments sont *polis* — UI travaillée, copywriting soigné, explicabilité visuelle, animations qui rendent la révélation tangible

Ce qu'on **sacrifie volontairement en MVP** pour tenir cette ambition en équipe restreinte :
- Pas de modèle de DL custom sur les stats d'admission (open data Parcoursup + fourchettes d'incertitude assumées)
- Pas d'app mobile native (PWA installable)
- Pas d'intégration ENT (import PDF/saisie manuelle uniquement)
- Pas de marché hors France
- Pas d'accompagnement post-bac (Phase 2)
- Pas de mentorat professionnels (Phase 2)

### Resource Requirements & Realistic Timeline

**Configuration équipe : Solo / 1-2 personnes**

| Rôle nécessaire | Solution réaliste avec 1-2 personnes |
|---|---|
| **Dev full-stack** (front + back) | Le ou les fondateurs, fortement assistés par **dev IA (Claude Code, Cursor, agents)** |
| **Data/ML** (moteur vocationnel + scoring) | Stack Python + bibliothèques standard (scikit-learn, sentence-transformers) ; modèles simples mais bien évalués ; pas de R&D ML |
| **Content/Référentiel** (50 métiers + 100 formations) | **Bootstrap LLM** : génération assistée à partir d'Onisep open data + Parcoursup + scraping responsable, **revue éditoriale humaine** systématique |
| **UX/Design** | Système de design lean (Tailwind + composants headless, ex. shadcn/ui) ; pas de designer dédié |
| **Commercial B2B** (5 pilotes) | Fait par le fondateur en sourcing direct (réseau + LinkedIn + appels) — 5 pilotes gratuits = pitch facile |
| **RGPD/DPO** | DPO mutualisé externalisé (prestataire à temps partagé, ~200-400€/mois) |

**Timeline réaliste : 9 mois** (au lieu de 6) pour MVP avec 1-2 personnes + dev assisté IA intensif. Compressible à 6-7 mois si :
- Vraiment 2 personnes à temps plein (pas 1 + extras)
- Aucun pivot de scope mid-route
- Stack technique connue par l'équipe (pas d'apprentissage à l'aveugle)

### MVP Feature Set (Phase 1 — 0 à 9 mois)

**Parcours utilisateur essentiel servi :**
- Parcours 1 (Sarah, happy path lycéen) ✅
- Parcours 3 (Léa, profil dégradé sans bulletins) ✅
- Parcours 5 (parent prescripteur, version basique) ✅
- Parcours 6 (école partenaire envoi anticipé) ✅ — version simplifiée

**Parcours partiellement servis :**
- Parcours 2 (Mehdi, 3ème bac pro) — *cas servi mais avec référentiel bac pro limité (10-15 formations bac pro sur 100)*
- Parcours 4 (conseiller B2B) — *dashboard fonctionnel mais minimaliste : cohorte + vue élève, pas de détection profils à risque en MVP*
- Parcours 7 (admin Path-Advisor) — *back-office basique : CRUD référentiel + signalements, pas de tableau qualité données*

**Must-Have Capabilities :**

| Capability | Justification MVP |
|---|---|
| Auth multi-rôle + RBAC + multi-tenant hybride | Fondation conformité + B2B + différenciation par rôle |
| Onboarding élève (profil + OCR bulletins + saisie manuelle fallback + consentement parental email) | Sans bulletins, pas de stats personnalisées = pas de différenciation |
| Moteur vocationnel (statistique + 50 métiers curés) | Premier moment aha |
| Moteur parcours (100 formations + graphe interactif + stats admission open data) | Deuxième moment aha |
| Mode "profil dégradé" (sans bulletins) | Anti-friction onboarding, pas un dead-end |
| Premium B2C + Stripe + gating fonctionnalités | Validation revenue B2C dès MVP |
| Envoi anticipé écoles (premium) + flow complet école (auth, réception, 3 actions, MAJ stat) | Différenciateur premium clé + accrochage B2B |
| Dashboard conseiller B2B basique (cohorte + vue élève consentie) | 5 pilotes nécessitent un produit utilisable, même minimaliste |
| Vue parent (lecture restreinte + paiement) | Levier conversion premium + adoption |
| RGPD complet (DPIA, consentement parental, art. 22 explicabilité) | Non négociable légalement |
| RGAA AA sur parcours critiques | Exigence B2B EN |
| SEO B2C (SSR + Schema.org + sitemap) | Acquisition organique = vital sans budget pub |
| Monitoring + observabilité (Sentry, PostHog, Grafana) | Détection précoce des dérives |

**Nice-to-Have (descopable si retard) :**
- Détection profils à risque dans dashboard conseiller → reporter à fast-follow (mois 9-12)
- Tableau qualité données admin → reporter à fast-follow
- Notifications push proactives (mensuelles, nouvelles écoles, etc.) → premier release email only, push en fast-follow

### Phase 2 — Growth (mois 9 à 24)

**Capacités ajoutées :**
- Intégration ENT/Pronote (import automatique bulletins)
- Modèle prédictif d'admission custom (deep learning sur historiques)
- App mobile native (iOS + Android)
- Mise en relation professionnels (mentorat + témoignages)
- Aide recherche de stages
- Lancement Belgique **ou** Maroc (1 marché)
- Dashboard conseiller enrichi (détection profils à risque, recommandations cohorte)
- Comité éthique trimestriel (audit biais formalisé)
- Audit RGPD externe certifié
- Migration RGAA AA full (toutes pages, pas seulement parcours critiques)
- Licence B2B Enterprise (multi-établissements + tenancy dédiée option)

**Cibles business croissance :**
- 10 000 MAU, 5-15 % premium
- 30+ établissements payants (incluant 3+ ex-pilotes convertis)
- 50 % des MAU postulent à au moins 1 école recommandée

### Phase 3 — Vision (mois 24+)

- Couverture francophone complète (Tunisie, Sénégal, Canada francophone, Suisse romande)
- Plateforme matching jeunes diplômés / premiers employeurs (extension continuité jusqu'à la vie active)
- API publique pour intégrations tierces (établissements, ministères, plateformes publiques)
- Outil conseiller enrichi IA (assistance entretien d'orientation)

### Risk Mitigation Strategy

**Risques techniques :**
- **Stack inconnue** → choisir une stack maîtrisée par l'équipe (pas d'apprentissage à l'aveugle), même si moins "tendance"
- **OCR bulletins échoue** → fallback manuel assistée intégrée dès le MVP (déjà décidé)
- **Stats admission inexactes** → assumer l'incertitude visuellement (fourchettes, pas valeurs ponctuelles) + recalibrage post-Parcoursup année 1
- **Performance moteur reco sous charge saisonnière** → load testing simulé sur 500 utilisateurs concurrents avant le pic janvier-mars

**Risques marché :**
- **B2B EN refuse Path-Advisor (RGAA, souveraineté)** → conformité RGAA AA + hébergement français acté dès MVP
- **Premium B2C ne convertit pas à 5 %** → revue trimestrielle de la proposition de valeur premium ; si < 2 %, repenser les features premium ou le pricing
- **Envoi anticipé n'attire pas les écoles** → bundle B2B pilote = écoles partenaires côté envoi anticipé (volume garanti dès le lancement)
- **Désintermédiation LLM grand public** → veille active + accent sur ce que ChatGPT ne fait pas (bulletins, stats par école, neutralité auditée)

**Risques ressources (criticité élevée — équipe 1-2 personnes) :**
- **Une seule personne tombe malade / s'épuise** → documentation système rigoureuse, code commentaire dense, mémoires partagées (CLAUDE.md, README, ADR) ; sous-traitance ponctuelle envisageable (référentiel content)
- **Budget content (50 métiers + 100 formations) sous-estimé** → bootstrap LLM + revue humaine, pas de rédaction from scratch ; partenariat éventuel avec un journaliste/rédacteur orientation freelance
- **Manque de feedback utilisateur précoce** → cohorte beta de 30-50 lycéens recrutés AVANT le lancement public (LinkedIn, réseau perso, écoles pilotes)
- **Curation du référentiel devient un travail à temps plein** → automatisation maximum (Onisep open data + scraping responsable) + community sourcing (les utilisateurs signalent les corrections, traité dans le back-office admin)
- **Manque de commercial B2B** → pitcher pendant la phase de construction (mois 3-6) pour avoir les 5 pilotes prêts à activer dès le launch (mois 9)

**Risques produit non négociables (à surveiller chaque sprint) :**
- Les 2 aha moments **fonctionnent vraiment** (tester sur 5 utilisateurs minimum à chaque release)
- La complétion d'onboarding reste **> 70 %** (si elle chute, l'OCR ou le wizard sont en cause)
- La latence du moteur reco reste **< 3 s** (si elle dérive, dette technique à régler avant feature)

## Functional Requirements

### A. Comptes, Rôles & Conformité

- **FR1 :** Un élève (≥ 15 ans) peut créer un compte sans intervention parentale et accepter explicitement les conditions d'usage RGPD
- **FR2 :** Un élève (< 15 ans) peut créer un compte via un consentement parental obtenu par opt-in email envoyé à un parent désigné
- **FR3 :** Un parent peut créer un compte parent **lié** à un compte élève existant, après invitation explicite de l'élève
- **FR4 :** Un conseiller d'orientation peut s'authentifier sur un espace B2B dédié avec MFA obligatoire
- **FR5 :** Une école partenaire peut s'authentifier sur un espace admissions dédié avec MFA obligatoire
- **FR6 :** Un admin Path-Advisor peut s'authentifier sur un back-office dédié avec MFA obligatoire
- **FR7 :** Le système peut isoler les données par tenant (établissement B2B) et par utilisateur (élève) selon une matrice RBAC documentée
- **FR8 :** Un élève peut consulter à tout moment la liste de tous les tiers ayant accès à son profil (parent, conseiller, école partenaire)
- **FR9 :** Un élève peut révoquer à tout moment l'accès accordé à un tiers (parent, conseiller, école)
- **FR10 :** Un élève peut exporter l'intégralité de ses données personnelles (droit à la portabilité RGPD)
- **FR11 :** Un élève peut demander la suppression complète de son compte et de toutes ses données (droit à l'oubli RGPD)
- **FR12 :** Le système peut produire un journal d'audit de tous les accès aux données personnelles d'un élève, consultable par le DPO

### B. Profil Élève & Onboarding

- **FR13 :** Un élève peut déclarer ses passions, centres d'intérêt et valeurs via un questionnaire structuré
- **FR14 :** Un élève peut importer ses bulletins scolaires en format PDF, et le système peut extraire automatiquement notes et appréciations enseignants par OCR
- **FR15 :** Un élève peut saisir manuellement ses notes et appréciations dans un formulaire structuré lorsque l'OCR échoue ou est indisponible
- **FR16 :** Un élève peut déclarer son niveau scolaire (3ème, 2nde, 1ère, Terminale, post-bac), sa filière (général, technologique, professionnel) et ses spécialités
- **FR17 :** Un élève peut compléter son profil partiellement et accéder à une expérience dégradée (sans stats d'admission personnalisées) tant que ses bulletins ne sont pas importés
- **FR18 :** Un élève peut mettre à jour son profil à tout moment (bulletins de l'année en cours, évolution des passions, changement de filière)
- **FR19 :** Un élève peut visualiser un score de complétude de son profil et identifier les éléments manquants

### C. Recommandation Vocationnelle

- **FR20 :** Un élève peut recevoir une liste personnalisée de métiers recommandés, scorés sur une échelle de 0 à 100, dès la complétion du déclaratif
- **FR21 :** Un élève peut consulter, pour chaque métier recommandé, une fiche détaillée (description, journée type, prérequis, débouchés, revenu médian)
- **FR22 :** Un élève peut consulter, pour chaque métier recommandé, les signaux qui ont contribué à son score (explicabilité IA, art. 22 RGPD)
- **FR23 :** Un élève peut demander une revue humaine d'une recommandation qu'il juge incorrecte ou choquante
- **FR24 :** Un élève peut signaler une erreur ou une information obsolète sur la fiche métier
- **FR25 :** Le système peut adapter la nature des recommandations vocationnelles au niveau scolaire de l'élève (un élève de 3ème reçoit des métiers compatibles avec un parcours bac pro ou général)
- **FR26 :** Le système peut afficher un niveau de confiance sur chaque recommandation lorsque le profil est incomplet

### D. Recommandation de Parcours & Stats d'Admission

- **FR27 :** Un élève peut consulter, pour chaque métier sélectionné, un ou plusieurs **graphes de parcours scolaires** menant à ce métier
- **FR28 :** Un élève peut consulter, pour chaque école / formation d'un graphe de parcours, une fiche détaillée (frais, durée, sélectivité, débouchés, dates de candidature)
- **FR29 :** Un élève peut consulter une **statistique d'admission personnalisée** (probabilité ou fourchette d'incertitude) pour chaque école cible, basée sur son profil scolaire
- **FR30 :** Un élève peut filtrer les graphes de parcours selon des critères (proximité géographique, coût maximum, niveau de sélectivité, alternance possible)
- **FR31 :** Le système peut adapter le graphe de parcours au niveau scolaire de l'élève (graphe partant d'un lycée pro associé pour un élève de 3ème orienté bac pro)
- **FR32 :** Un élève peut sauvegarder des écoles cibles dans une liste de favoris pour comparaison

### E. Envoi Anticipé Écoles & Espace École

- **FR33 :** Un élève **premium** peut déclencher un "envoi anticipé" de son profil à une école partenaire
- **FR34 :** Un élève **premium** peut accompagner son envoi anticipé d'une motivation libre (texte modéré côté admin)
- **FR35 :** Une école partenaire peut recevoir une notification (email + push) à chaque profil envoyé en anticipé
- **FR36 :** Une école partenaire peut consulter une fiche profil élève synthétique (données scolaires, motivation, métier visé, parcours sélectionné), sans accès aux autres recos ou écoles ciblées
- **FR37 :** Une école partenaire peut répondre à un envoi anticipé via 3 actions explicites : *Profil intéressant — candidature encouragée* / *Profil non aligné* / *Demande d'entretien*
- **FR38 :** Le système peut mettre à jour la statistique d'admission affichée à l'élève sous 5 minutes après une réponse école
- **FR39 :** Un élève peut consulter le statut et l'historique de tous ses envois anticipés
- **FR40 :** Une école partenaire peut consulter un reporting interne sur les profils reçus, les actions effectuées et les conversions de candidature

### F. Espaces Tiers (Parent & Conseiller B2B)

- **FR41 :** Un parent lié peut consulter les métiers explorés et les parcours sauvegardés de l'élève (sans accès aux bulletins détaillés ni aux appréciations enseignants)
- **FR42 :** Un parent peut souscrire et payer un abonnement premium au bénéfice du compte élève lié
- **FR43 :** Un conseiller d'orientation peut consulter un dashboard cohorte (élèves de son établissement) avec taux de complétion, métiers les plus explorés, distribution par filière
- **FR44 :** Un conseiller d'orientation peut consulter le profil individuel d'un élève de sa cohorte **uniquement après consentement explicite de l'élève**
- **FR45 :** Un conseiller d'orientation peut exporter un reporting anonymisé de cohorte (CSV ou PDF) pour usage interne établissement

### G. Découverte & Engagement

- **FR46 :** Le système peut exposer des pages publiques indexables par les moteurs de recherche pour chaque métier, formation et école référencés (SEO)
- **FR47 :** Le système peut envoyer des notifications par email à un élève lors d'événements clés (réponse école, nouvelle école référencée pertinente, échéance Parcoursup, rappel de complétion profil)

### H. Administration & Modération

- **FR48 :** Un admin Path-Advisor peut créer, modifier et supprimer des fiches du référentiel professions / formations / écoles
- **FR49 :** Un admin Path-Advisor peut consulter et traiter les signalements d'élèves (erreur métier, école obsolète, contenu inapproprié)
- **FR50 :** Un admin Path-Advisor peut modérer les motivations libres rédigées par les élèves dans le cadre des envois anticipés (a priori avant transmission à l'école)
- **FR51 :** Un admin Path-Advisor peut versionner un modèle de recommandation IA et tracer le dataset d'entraînement associé
- **FR52 :** Le système peut produire des métriques d'audit ML (distribution des scores par sous-population, drift des prédictions dans le temps) consultables par un admin

### FRs Fast-Follow (Post-MVP immédiat, mois 9-12)

- **FR-FF1 :** Le système peut détecter des "profils à risque" (faible engagement, profil incohérent, signes de décrochage) et les remonter dans le dashboard conseiller
- **FR-FF2 :** Le système peut envoyer des notifications **push web** (en plus de l'email) aux élèves et parents
- **FR-FF3 :** Un admin peut consulter un tableau de bord de qualité du référentiel (couverture, fraîcheur, signalements en attente)
- **FR-FF4 :** Le système peut proposer un module **RDV visio intégré** entre élève et école partenaire (au lieu d'un lien externe)
- **FR-FF5 :** Le système peut proposer un mécanisme de **parrainage / partage** permettant à un utilisateur d'inviter un pair via un lien traçable

## Non-Functional Requirements

### Performance

- **NFR-P1 :** Une recommandation vocationnelle complète (top 8 métiers + explicabilité) doit être servie en **< 3 secondes** au P95 en MVP, **< 1,5 seconde** au P95 en growth
- **NFR-P2 :** Un graphe de parcours avec stats d'admission personnalisées doit s'afficher en **< 2 secondes** au P95
- **NFR-P3 :** Une page publique métier/formation (SEO) doit avoir un **TTFB < 1 seconde** et un **LCP mobile < 2,5 secondes** (cible Core Web Vitals)
- **NFR-P4 :** L'OCR d'un bulletin standard doit aboutir en **< 30 secondes** au P95
- **NFR-P5 :** Une mise à jour de statistique d'admission suite à une réponse école doit être propagée à l'élève (push + email) en **< 5 minutes**
- **NFR-P6 :** L'authentification d'un utilisateur (élève, parent, conseiller, école) doit aboutir en **< 1 seconde** au P95

### Security

- **NFR-S1 :** Toutes les données personnelles (profil, bulletins, communications) doivent être **chiffrées au repos en AES-256** et **en transit via TLS 1.3 minimum**
- **NFR-S2 :** L'accès aux comptes conseiller, école et admin doit imposer une **MFA obligatoire** (TOTP ou WebAuthn), l'accès B2C peut activer la MFA en option
- **NFR-S3 :** Les bulletins scolaires PDF doivent être stockés dans un bucket S3-compatible chiffré (clé de chiffrement gérée par hébergeur ou KMS dédié), région UE obligatoire
- **NFR-S4 :** Le système doit produire un **journal d'audit immuable** de tout accès aux données personnelles d'un élève par un tiers (parent, conseiller, école, admin), conservé 3 ans
- **NFR-S5 :** Les secrets applicatifs (clés API, tokens, mots de passe DB) doivent être stockés dans un coffre dédié (HashiCorp Vault, AWS Secrets Manager, ou équivalent self-hosted en PoC)
- **NFR-S6 :** Le système doit respecter les **délais légaux RGPD** : notification d'incident à la CNIL **< 72 heures**, réponse à une demande d'accès / suppression **< 30 jours**
- **NFR-S7 :** Une DPIA documentée doit exister et être à jour avant tout déploiement en production
- **NFR-S8 :** Le système doit prévenir les attaques OWASP Top 10 (injection, XSS, CSRF, broken auth, SSRF, etc.), validé par un audit interne en MVP et **pen-test annuel externe** en growth
- **NFR-S9 :** Un consentement parental email vérifié doit être obtenu avant toute création de compte pour un utilisateur **< 15 ans**, et tracé avec horodatage immuable

### Scalability

- **NFR-SC1 :** Le système doit supporter **500 MAU en MVP** (production-ready) et permettre une montée en charge jusqu'à **10 000 MAU en growth** sans refonte architecturale majeure
- **NFR-SC2 :** Le système doit supporter **500 utilisateurs concurrents** lors des pics saisonniers (janvier-mars, mai-juillet) sans dégradation perçue
- **NFR-SC3 :** L'auto-scaling de l'infrastructure doit pouvoir **multiplier x3 la capacité** en moins de 10 minutes sur déclencheur de charge
- **NFR-SC4 :** Le moteur de recommandation doit pouvoir être déployé indépendamment du back applicatif (scaling horizontal séparé)
- **NFR-SC5 :** Le référentiel de professions et formations doit pouvoir croître de **50 → 500 entrées** sans dégradation de la latence de recommandation
- **NFR-SC6 :** La base de données doit supporter au minimum **100 000 profils élèves** en production (objectif vision long terme)

### Reliability

- **NFR-R1 :** La disponibilité de la plateforme doit être **≥ 99 %** en MVP (downtime ≤ 7h/mois) et **≥ 99,5 %** en growth
- **NFR-R2 :** Le système doit disposer d'une **sauvegarde quotidienne** des données de production avec rétention de 30 jours minimum, **testée mensuellement** par restauration partielle
- **NFR-R3 :** Le **Recovery Time Objective (RTO)** doit être **< 4 heures**, le **Recovery Point Objective (RPO) < 1 heure**
- **NFR-R4 :** Le système doit dégrader gracieusement en cas de panne d'un service tiers (OCR indisponible → fallback saisie manuelle ; Stripe indisponible → file d'attente paiement ; email indisponible → retry asynchrone)
- **NFR-R5 :** Le système doit disposer d'une observabilité production complète (logs centralisés, métriques, alerting) avec un **MTTR cible < 1 heure** sur incident critique

### Accessibility

- **NFR-A1 :** Les **parcours utilisateurs critiques** (inscription, onboarding, consultation recommandation, consultation graphe de parcours, déclenchement envoi anticipé) doivent être conformes **RGAA 4.1 niveau AA** dès le MVP
- **NFR-A2 :** L'ensemble du produit doit atteindre la conformité **RGAA 4.1 niveau AA** en growth (prérequis B2B Éducation Nationale)
- **NFR-A3 :** L'interface doit être pleinement utilisable au clavier seul (navigation, sélections, validation de formulaire)
- **NFR-A4 :** Les contrastes texte/fond doivent respecter un ratio **≥ 4,5:1** pour le texte normal et **≥ 3:1** pour le texte large
- **NFR-A5 :** Les graphes de parcours doivent fournir une **alternative textuelle structurée** (tableau, liste séquentielle) accessible aux lecteurs d'écran
- **NFR-A6 :** Le produit doit être utilisable sur écrans mobiles dès **320 px de largeur** (cible smartphones bas de gamme)

### Integration

- **NFR-I1 :** L'intégration avec **Stripe** (paiement B2C) doit supporter le mode test local (clés sandbox) en PoC et le mode production en cloud
- **NFR-I2 :** L'intégration avec un service email transactionnel (Postmark, SendGrid) doit pouvoir être substituée par **Mailpit local** en PoC sans modification du code applicatif (couche d'abstraction)
- **NFR-I3 :** L'intégration OCR (AWS Textract / Mindee en production) doit pouvoir être substituée par **Tesseract OCR local** en PoC avec une dégradation acceptable de précision
- **NFR-I4 :** L'analytique produit (PostHog / Amplitude) doit respecter le **hébergement EU** ou être **self-hosted**
- **NFR-I5 :** Le système doit exposer des **données ouvertes anonymisées** (référentiel formations enrichi, tendances orientation) sous licence Etalab en growth (positionnement institutionnel)
- **NFR-I6 :** L'intégration ENT/Pronote en growth doit être **opt-in côté établissement** et **opt-in côté élève** (double consentement RGPD)
- **NFR-I7 :** Le système doit pouvoir consommer les **datasets open data Parcoursup** (CSV mis à jour annuellement par le MENJS) pour alimenter les stats d'admission

### Maintenability & Evolvability (équipe restreinte)

- **NFR-M1 :** L'ensemble de la stack (front, back, IA, DB, cache, queue, OCR, mail, monitoring, analytics, stockage) doit pouvoir être lancée localement par **`docker-compose up` en moins de 5 minutes**, avec données de seed pour un produit utilisable end-to-end
- **NFR-M2 :** Le code doit respecter une **couverture de tests automatisés ≥ 70 %** sur les zones critiques (auth, RBAC, moteur reco, paiement, RGPD)
- **NFR-M3 :** Toute modification du **modèle de recommandation IA** doit être versionnée avec dataset d'entraînement, hyperparamètres et métriques d'évaluation tracés
- **NFR-M4 :** L'architecture doit être documentée via **Architecture Decision Records (ADR)** versionnés en git, mis à jour à chaque choix structurant
- **NFR-M5 :** Le système doit pouvoir être maintenu et opéré par **1 à 2 personnes** sans dépendance critique à un savoir tacite — toute opération critique (déploiement, restauration, modération) doit être documentée sous forme de runbook
