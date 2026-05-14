# User Journeys

## Parcours 1 — Sarah, lycéenne en Terminale (utilisateur primaire, happy path)

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

## Parcours 2 — Mehdi, élève de 3ème, orientation bac pro (variation du happy path)

**Personnage :** Mehdi, 14 ans, 3ème dans un collège REP+. Bon en techno et arts plastiques, moins à l'aise en français/maths. Il aime ses mains et créer des objets.

**Scène d'ouverture.** Le conseil de classe approche. La principale a évoqué le bac pro, ses parents préfèrent le général "au cas où". Mehdi est partagé — il ne veut pas être "celui qui n'a pas eu le général" mais il déteste la pression scolaire actuelle.

**Découverte.** Le collège est l'un des 5 pilotes B2B. Sa conseillère d'orientation lui envoie un lien Path-Advisor.

**Onboarding adapté 3ème.** Pas de bulletins lycée (il n'y est pas encore). Il saisit ses bulletins collège, ses appréciations, ses passions (mécanique, jeux vidéo, vidéo TikTok DIY). Consentement parental requis (mineur < 15 ans).

**Premier "aha" — Révélation vocationnelle (cohérente 3ème).** Path-Advisor lui propose : technicien aéronautique (89 %), ébéniste designer (84 %), monteur vidéo (81 %), électromécanicien systèmes automatisés (78 %).

**Deuxième "aha" — Le graphe est différent.** Comme on parle d'un élève de 3ème conseillé bac pro, le graphe **commence par un lycée pro associé** (et non un lycée général). Exemple pour technicien aéronautique : *Bac pro Aéronautique option Avionique (Lycée pro Saint-Exupéry, Toulouse) → BTS Aéronautique → option : poursuite école d'ingé en alternance*.

Le graphe affiche 2-3 lycées pro accessibles depuis sa carte scolaire, avec ouvertures Affelnet et stats d'admission.

**Résolution.** Mehdi en parle à ses parents avec le graphe imprimé — il leur montre que "bac pro" n'est pas un cul-de-sac, qu'il existe une passerelle école d'ingé alternance. Ils acceptent le pari.

**Capacités révélées :** Onboarding différencié par niveau scolaire (collège / lycée général / lycée pro) • Logique de parcours bac pro avec lycée associé + débouchés post-bac • Intégration carte scolaire (lycées géographiquement accessibles) • Affelnet (équivalent Parcoursup pour le 3ème) • Référentiel de formations couvrant les filières pro

## Parcours 3 — Léa, lycéenne sans bulletins (edge case dégradé)

**Personnage :** Léa, 16 ans, 1ère générale. Elle s'inscrit par curiosité après avoir vu une vidéo TikTok. Pas envie de partager ses bulletins ("pourquoi tu veux mes notes ?").

**Onboarding partiel.** Elle saisit passions et intérêts. À l'étape bulletins, elle clique "Plus tard".

**Expérience dégradée — choix produit explicite.** Path-Advisor lui montre quand même des recommandations vocationnelles basées sur le déclaratif seul, mais avec un **score d'incertitude élevé**. Les métiers sont là, mais la fiabilité est affichée comme "indicative".

Quand elle ouvre un graphe de parcours : les chemins sont visibles, mais **les statistiques d'admission affichent une probabilité quasi nulle** (faute de données scolaires pour prédire). Un bandeau persistant et bien visible : *"Ajoute tes bulletins pour débloquer tes vraies chances d'admission — c'est gratuit et confidentiel."*

**Résolution.** Deux semaines plus tard, Léa cède (sa mère l'y pousse). Elle importe ses bulletins. Les stats d'admission deviennent significatives. Elle découvre que l'école qu'elle visait par défaut est en réalité accessible — elle reprend confiance.

**Capacités révélées :** Mode "profil dégradé" assumé (pas de dead-end) • Affichage explicite de l'incertitude des scores • Bandeau d'incitation persistant + non-bloquant • Conversion progressive vers le profil complet

## Parcours 4 — Mme Dupont, conseillère d'orientation (B2B pilote)

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

## Parcours 5 — M. Martin, parent prescripteur

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

## Parcours 6 — Mme Garcia, responsable admissions école partenaire (envoi anticipé)

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

## Parcours 7 — Karim, admin Path-Advisor (back-office)

**Personnage :** Karim, content & data ops chez Path-Advisor. Responsable du référentiel professions/formations et de la qualité des données.

**Tâches quotidiennes :**
- Curer le référentiel des 50+ professions MVP (descriptifs, prérequis, débouchés, journées types)
- Mettre à jour les 100+ formations (frais, sélectivité, places disponibles, dates Parcoursup)
- Traiter les signalements d'élèves ("ce métier n'est plus exact", "cette école a déménagé")
- Modérer les motivations déclarées par les élèves dans les envois anticipés (anti-discrimination, contenu inapproprié)
- Auditer les stats d'admission : versionner les modèles, détecter les biais, documenter les recalibrages

**Capacités révélées :** Back-office référentiel professions/formations (CRUD éditorial) • File de signalements + workflow modération • Versioning des modèles de recommandation + audit trail • Modération de contenu utilisateur (motivations envois anticipés) • Tableau de bord qualité données (couverture, fraîcheur, signalements)

## Journey Requirements Summary

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
