---
title: "Product Brief: Path-Advisor"
status: "draft"
created: "2026-05-12"
updated: "2026-05-12"
inputs: ["user interviews", "web research - marché orientation francophone 2025"]
---

# Product Brief: Path-Advisor

## Executive Summary

Chaque année, près d'un million de lycéens français arrivent à un carrefour décisif — le choix de leur orientation post-bac — sans outil adapté pour les y préparer vraiment. Les plateformes publiques (Onisep, Diagoriente) délivrent de l'information générale mais aucune recommandation personnalisée. Parcoursup gère les candidatures mais pas le conseil. Les comparateurs privés (Diplomeo, L'Étudiant) sont structurellement biaisés : leur modèle économique repose sur la revente de leads aux écoles, pas sur l'intérêt de l'élève.

Path-Advisor est la première plateforme d'orientation continue pour les jeunes francophones. Elle accompagne l'élève dès la 3ème jusqu'aux premières années post-bac, en combinant deux moteurs de recommandation complémentaires : un moteur vocationnel (qui suis-je, quelles professions me correspondent ?) et un moteur de parcours (comment y parvenir, quelles formations et écoles ?). Alimenté par des données objectives — notes, bulletins scolaires, avis enseignants — et des signaux déclaratifs — passions, centres d'intérêt — Path-Advisor produit des recommandations fiables et neutres commercialement.

Le marché est clair, le timing est favorable (IA grand public, génération alpha, désillusion vis-à-vis des outils institutionnels), et aucun acteur ne couvre aujourd'hui ce parcours de bout en bout en français.

---

## Le Problème

Un lycéen en Terminale doit, en quelques semaines, formuler des vœux Parcoursup qui engagent ses 3 à 5 prochaines années. Il le fait sans avoir clarifié sa vocation, sans comprendre les passerelles entre filières, et souvent sans accès à un conseiller d'orientation compétent (ratio France : 1 conseiller pour 1 400 élèves).

Les alternatives actuelles souffrent toutes d'un défaut majeur :
- **Parcoursup** : outil de candidature, pas de conseil — il faut déjà savoir quoi choisir
- **Onisep / Diagoriente** : bases documentaires statiques, questionnaires RIASEC génériques, aucune personnalisation par le profil scolaire réel
- **Diplomeo / L'Étudiant** : conflits d'intérêt structurels (rémunérés par les écoles pour y orienter les élèves)
- **Professeurs et parents** : de bonne volonté, mais peu équipés pour naviguer un marché de la formation en constante évolution

Le coût du mauvais choix est élevé : réorientation, perte d'une année, désengagement scolaire, dette étudiante pour une formation inadaptée. En France, 20 % des étudiants se réorientent en cours de licence.

---

## La Solution

Path-Advisor propose une expérience d'orientation continue en trois temps :

**1. Découverte vocationnelle**
L'élève renseigne ses passions, centres d'intérêt et valeurs. La plateforme intègre — via ENT/Pronote ou import de bulletins — ses notes et appréciations enseignants. Un moteur de recommandation croise ces signaux pour proposer un ensemble de professions correspondantes, avec une explication transparente du score.

**2. Recommandation de parcours**
Pour chaque vocation identifiée, Path-Advisor génère un ou plusieurs parcours scolaires concrets : lycée → classe prépa / BTS / L1 → école cible. Les parcours sont enrichis de données réelles sur les taux d'admission, les débouchés et les coûts.

**3. Accompagnement continu**
La plateforme suit l'élève dans le temps — de la 3ème à bac+2/3 — et adapte ses recommandations à l'évolution du profil. À terme : mise en relation avec des professionnels du secteur visé, aide à la recherche de stages, et orientation dans les transitions (réorientation, poursuite d'études).

Le "moment aha" arrive quand l'élève voit pour la première fois un parcours complet et réaliste — "tu peux devenir ingénieur en aérospatiale, voici les 3 chemins pour y arriver depuis ton profil".

---

## Ce qui nous différencie

| Dimension | Path-Advisor | Concurrents |
|---|---|---|
| **Double moteur** | Vocation → Parcours en un seul produit | Séparés ou absents |
| **Données objectives** | Notes + bulletins + appréciations enseignants | Questionnaires déclaratifs uniquement |
| **Neutralité commerciale** | Aucune revente de leads aux écoles | Modèle économique des comparateurs |
| **Continuité temporelle** | 3ème → Bac+2/3 | Snapshot ponctuel |
| **Francophonie** | France, Belgique, Maroc, Tunisie, Sénégal… | Essentiellement France métropolitaine |

La donnée scolaire objective est le vrai avantage défensif : elle crée un profil riche que l'élève ne peut pas construire lui-même sur une plateforme concurrente.

---

## À qui ça s'adresse

**Utilisateur primaire — Le lycéen (B2C)**
15-20 ans, souvent perdu face à l'orientation, influencé par ses parents et ses pairs mais manquant d'information fiable. Il cherche de la clarté, pas plus de contenu. La version freemium lui donne accès aux recommandations de base ; le premium (10,99€/mois) déverrouille les parcours détaillés, le suivi personnalisé et la mise en relation professionnelle.

**Utilisateur secondaire — L'établissement scolaire (B2B)**
Lycées publics et privés, établissements francophones hors France. Ils cherchent à améliorer les résultats d'orientation de leurs élèves et à outiller leurs conseillers. Modèle licence : 5 000€/an pour 100 utilisateurs — un outil à disposition de tous les élèves, avec dashboard conseiller.

**Utilisateur tertiaire — Les parents**
Impliqués dans la décision, souvent prescripteurs de l'outil, rassurés par la neutralité commerciale affichée.

---

## Critères de succès

**Phase MVP (6-12 mois)**
- 500 utilisateurs actifs (B2C) avec un taux de complétion du profil > 60 %
- 3 à 5 établissements scolaires pilotes en B2B
- NPS utilisateur > 40
- Couverture : sous-ensemble de 50+ professions et 100+ établissements de formation référencés

**Phase croissance (12-24 mois)**
- 10 000 utilisateurs actifs, 5 % en premium
- 30+ établissements licenciés
- Intégration ENT fonctionnelle (Pronote / Espace Numérique de Travail)
- Lancement Belgique ou Maroc

---

## Périmètre MVP

**Dans le scope :**
- Profil utilisateur (passions, intérêts, import bulletins)
- Moteur de recommandation professions (sous-ensemble ~50 métiers)
- Moteur de recommandation parcours (sous-ensemble ~100 formations/écoles)
- Interface web responsive (pas d'app mobile v1)
- Espace conseiller d'orientation (B2B basique)

**Hors scope v1 :**
- Mise en relation avec professionnels et stages
- Intégration ENT temps réel (import manuel de bulletins d'abord)
- Application mobile native
- Marché hors France
- Accompagnement bac+2/3 (phase 2)

---

## Vision 3 ans

Path-Advisor devient le compagnon d'orientation de référence en francophonie — présent de la 3ème aux premières années d'études supérieures. La plateforme évolue en réseau : mise en relation avec des professionnels pour des témoignages et du mentorat, aide active à la recherche de stages, et potentiellement un rôle dans le matching entre jeunes diplômés et premiers employeurs. À terme, Path-Advisor sait non seulement vers quoi orienter un élève, mais peut l'aider à franchir chaque étape du chemin.
