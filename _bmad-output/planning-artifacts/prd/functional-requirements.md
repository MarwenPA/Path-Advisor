# Functional Requirements

## A. Comptes, Rôles & Conformité

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

## B. Profil Élève & Onboarding

- **FR13 :** Un élève peut déclarer ses passions, centres d'intérêt et valeurs via un questionnaire structuré
- **FR14 :** Un élève peut importer ses bulletins scolaires en format PDF, et le système peut extraire automatiquement notes et appréciations enseignants par OCR
- **FR15 :** Un élève peut saisir manuellement ses notes et appréciations dans un formulaire structuré lorsque l'OCR échoue ou est indisponible
- **FR16 :** Un élève peut déclarer son niveau scolaire (3ème, 2nde, 1ère, Terminale, post-bac), sa filière (général, technologique, professionnel) et ses spécialités
- **FR17 :** Un élève peut compléter son profil partiellement et accéder à une expérience dégradée (sans stats d'admission personnalisées) tant que ses bulletins ne sont pas importés
- **FR18 :** Un élève peut mettre à jour son profil à tout moment (bulletins de l'année en cours, évolution des passions, changement de filière)
- **FR19 :** Un élève peut visualiser un score de complétude de son profil et identifier les éléments manquants

## C. Recommandation Vocationnelle

- **FR20 :** Un élève peut recevoir une liste personnalisée de métiers recommandés, scorés sur une échelle de 0 à 100, dès la complétion du déclaratif
- **FR21 :** Un élève peut consulter, pour chaque métier recommandé, une fiche détaillée (description, journée type, prérequis, débouchés, revenu médian)
- **FR22 :** Un élève peut consulter, pour chaque métier recommandé, les signaux qui ont contribué à son score (explicabilité IA, art. 22 RGPD)
- **FR23 :** Un élève peut demander une revue humaine d'une recommandation qu'il juge incorrecte ou choquante
- **FR24 :** Un élève peut signaler une erreur ou une information obsolète sur la fiche métier
- **FR25 :** Le système peut adapter la nature des recommandations vocationnelles au niveau scolaire de l'élève (un élève de 3ème reçoit des métiers compatibles avec un parcours bac pro ou général)
- **FR26 :** Le système peut afficher un niveau de confiance sur chaque recommandation lorsque le profil est incomplet

## D. Recommandation de Parcours & Stats d'Admission

- **FR27 :** Un élève peut consulter, pour chaque métier sélectionné, un ou plusieurs **graphes de parcours scolaires** menant à ce métier
- **FR28 :** Un élève peut consulter, pour chaque école / formation d'un graphe de parcours, une fiche détaillée (frais, durée, sélectivité, débouchés, dates de candidature)
- **FR29 :** Un élève peut consulter une **statistique d'admission personnalisée** (probabilité ou fourchette d'incertitude) pour chaque école cible, basée sur son profil scolaire
- **FR30 :** Un élève peut filtrer les graphes de parcours selon des critères (proximité géographique, coût maximum, niveau de sélectivité, alternance possible)
- **FR31 :** Le système peut adapter le graphe de parcours au niveau scolaire de l'élève (graphe partant d'un lycée pro associé pour un élève de 3ème orienté bac pro)
- **FR32 :** Un élève peut sauvegarder des écoles cibles dans une liste de favoris pour comparaison

## E. Envoi Anticipé Écoles & Espace École

- **FR33 :** Un élève **premium** peut déclencher un "envoi anticipé" de son profil à une école partenaire
- **FR34 :** Un élève **premium** peut accompagner son envoi anticipé d'une motivation libre (texte modéré côté admin)
- **FR35 :** Une école partenaire peut recevoir une notification (email + push) à chaque profil envoyé en anticipé
- **FR36 :** Une école partenaire peut consulter une fiche profil élève synthétique (données scolaires, motivation, métier visé, parcours sélectionné), sans accès aux autres recos ou écoles ciblées
- **FR37 :** Une école partenaire peut répondre à un envoi anticipé via 3 actions explicites : *Profil intéressant — candidature encouragée* / *Profil non aligné* / *Demande d'entretien*
- **FR38 :** Le système peut mettre à jour la statistique d'admission affichée à l'élève sous 5 minutes après une réponse école
- **FR39 :** Un élève peut consulter le statut et l'historique de tous ses envois anticipés
- **FR40 :** Une école partenaire peut consulter un reporting interne sur les profils reçus, les actions effectuées et les conversions de candidature

## F. Espaces Tiers (Parent & Conseiller B2B)

- **FR41 :** Un parent lié peut consulter les métiers explorés et les parcours sauvegardés de l'élève (sans accès aux bulletins détaillés ni aux appréciations enseignants)
- **FR42 :** Un parent peut souscrire et payer un abonnement premium au bénéfice du compte élève lié
- **FR43 :** Un conseiller d'orientation peut consulter un dashboard cohorte (élèves de son établissement) avec taux de complétion, métiers les plus explorés, distribution par filière
- **FR44 :** Un conseiller d'orientation peut consulter le profil individuel d'un élève de sa cohorte **uniquement après consentement explicite de l'élève**
- **FR45 :** Un conseiller d'orientation peut exporter un reporting anonymisé de cohorte (CSV ou PDF) pour usage interne établissement

## G. Découverte & Engagement

- **FR46 :** Le système peut exposer des pages publiques indexables par les moteurs de recherche pour chaque métier, formation et école référencés (SEO)
- **FR47 :** Le système peut envoyer des notifications par email à un élève lors d'événements clés (réponse école, nouvelle école référencée pertinente, échéance Parcoursup, rappel de complétion profil)

## H. Administration & Modération

- **FR48 :** Un admin Path-Advisor peut créer, modifier et supprimer des fiches du référentiel professions / formations / écoles
- **FR49 :** Un admin Path-Advisor peut consulter et traiter les signalements d'élèves (erreur métier, école obsolète, contenu inapproprié)
- **FR50 :** Un admin Path-Advisor peut modérer les motivations libres rédigées par les élèves dans le cadre des envois anticipés (a priori avant transmission à l'école)
- **FR51 :** Un admin Path-Advisor peut versionner un modèle de recommandation IA et tracer le dataset d'entraînement associé
- **FR52 :** Le système peut produire des métriques d'audit ML (distribution des scores par sous-population, drift des prédictions dans le temps) consultables par un admin

## FRs Fast-Follow (Post-MVP immédiat, mois 9-12)

- **FR-FF1 :** Le système peut détecter des "profils à risque" (faible engagement, profil incohérent, signes de décrochage) et les remonter dans le dashboard conseiller
- **FR-FF2 :** Le système peut envoyer des notifications **push web** (en plus de l'email) aux élèves et parents
- **FR-FF3 :** Un admin peut consulter un tableau de bord de qualité du référentiel (couverture, fraîcheur, signalements en attente)
- **FR-FF4 :** Le système peut proposer un module **RDV visio intégré** entre élève et école partenaire (au lieu d'un lien externe)
- **FR-FF5 :** Le système peut proposer un mécanisme de **parrainage / partage** permettant à un utilisateur d'inviter un pair via un lien traçable
