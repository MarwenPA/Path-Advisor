# Epic 10 : Fast-Follow (post-MVP immédiat mois 9-12)

Polish post-MVP : détection profils à risque dashboard conseillère, push web, tableau qualité référentiel admin, RDV visio intégré, parrainage / partage lien traçable.

## Story 10.1 : Détection profils à risque dashboard conseillère

As a conseillère B2B (Mme Dupont),
I want voir dans mon dashboard la liste des élèves "profils à risque" (faible engagement, profil incohérent, signes de décrochage),
So that je puisse intervenir proactivement (FR-FF1).

**Acceptance Criteria :**

**Given** des règles de détection sont définies (faible engagement = pas d'activité depuis 30 jours, profil incohérent = passions très divergentes des spés, décrochage = baisse moyenne > 2 points)
**When** un élève remplit un ou plusieurs critères
**Then** il apparaît dans la liste "Profils à risque" de son conseiller
**And** le motif est expliqué (pas opaque)

**Given** je consulte la liste
**When** je tape sur un profil
**Then** je vois le détail des signaux à risque + propositions d'action ("Suggérer un entretien")
**And** je peux marquer le profil comme "intervention en cours" pour éviter les doublons d'alertes

**Given** la conformité RGPD + dignité
**When** la liste est affichée
**Then** la formulation est constructive ("nécessite ton attention"), pas stigmatisante ("élève en échec")
**And** l'élève ne voit pas qu'il est marqué "à risque" (information conseillère uniquement)

## Story 10.2 : Push web notifications

As a élève / parent / conseillère / école,
I want recevoir des push web notifications en plus des emails,
So that je sois informé instantanément des événements critiques (FR-FF2).

**Acceptance Criteria :**

**Given** la stack Web Push (Service Worker + VAPID keys)
**When** un utilisateur active les push notifications
**Then** son navigateur enregistre l'abonnement et stocke le token
**And** les événements critiques (réponse école, calendrier Parcoursup) déclenchent un push

**Given** la conformité opt-in
**When** un user souhaite désactiver les push
**Then** il peut le faire dans Paramètres + révoque l'abonnement navigateur
**And** aucun push n'est envoyé après désactivation

**Given** la dégradation gracieuse
**When** un user n'a pas activé les push
**Then** seuls les emails sont envoyés (NFR-R4)

## Story 10.3 : Tableau qualité référentiel admin

As a admin Path-Advisor,
I want un tableau de bord de qualité du référentiel (couverture, fraîcheur, signalements en attente),
So that je gouverne la qualité éditoriale en continu (FR-FF3).

**Acceptance Criteria :**

**Given** je vais dans Back-office → "Qualité référentiel"
**When** la page s'affiche
**Then** je vois des KPIs : nombre de métiers (50/500), nombre de formations (100/1000), fraîcheur (% mis à jour ces 12 derniers mois), signalements ouverts, motivations en attente de modération
**And** des graphes de tendance sur 6 mois

**Given** des seuils d'alerte
**When** un KPI dépasse un seuil (ex : > 20 signalements ouverts, fraîcheur < 60 %)
**Then** une alerte visible me prévient
**And** un CTA me redirige vers la file à traiter

## Story 10.4 : RDV visio intégré école-élève

As a élève premium recevant une demande d'entretien d'une école,
I want pouvoir prendre un RDV visio directement dans Path-Advisor (calendrier + lien visio),
So that je n'ai pas à jongler entre apps externes (FR-FF4).

**Acceptance Criteria :**

**Given** une école a déclenché "Demande d'entretien" (Story 5.7)
**When** je reçois la proposition de RDV
**Then** je vois un mini-calendrier avec les 3 créneaux proposés par l'école
**And** je peux confirmer un créneau ou en proposer un autre

**Given** un créneau confirmé
**When** le RDV approche
**Then** un lien visio est généré (intégration Whereby / Daily.co / Jitsi self-hosted)
**And** un rappel email + push est envoyé J-1 et 1 h avant

**Given** la conformité RGPD
**When** le RDV se termine
**Then** aucune capture vidéo n'est conservée par Path-Advisor (transit only)

## Story 10.5 : Parrainage / partage avec lien traçable

As a élève satisfait de Path-Advisor,
I want partager le produit à un pair via un lien traçable,
So that la viralité organique se développe (FR-FF5).

**Acceptance Criteria :**

**Given** je vais dans Paramètres → "Parrainer un pote"
**When** je clique sur "Inviter"
**Then** un lien personnalisé est généré (ex : `pathadvisor.fr/r/{my_id}`)
**And** je peux le partager via WhatsApp / Instagram / SMS (share natif)

**Given** un pair clique sur mon lien
**When** il s'inscrit
**Then** son inscription est attribuée à mon parrainage
**And** je reçois une notification "Ton pote vient de rejoindre Path-Advisor"

**Given** des incentives éventuels (V2)
**When** N parrainages réussis (à définir post-MVP)
**Then** une récompense optionnelle pourrait être proposée (mois gratuit premium par exemple)
**But** sans dark pattern et sans urgence fabriquée

## Story 10.6 : Composant `SideFlow` (consentement parental en attente, etc.)

As a développeur Path-Advisor,
I want un composant `SideFlow` réutilisable pour les confirmations critiques qui ne bloquent pas l'exploration en cours,
So that les flow non-bloquants soient gérés proprement (UX-DR18).

**Acceptance Criteria :**

**Given** le composant est implémenté
**When** je l'instancie pour un cas (ex : consentement parental en attente Story 1.4)
**Then** un bandeau persistant non-bloquant apparaît en bas / haut de l'app
**And** l'exploration utilisateur reste possible sans validation immédiate

**Given** la conformité émotionnelle
**When** le bandeau s'affiche
**Then** il informe sans culpabiliser ("Ton parent reçoit l'email — tu peux continuer pendant qu'on vérifie")
**And** il a un CTA secondaire optionnel ("Relancer mon parent")

**Given** la résolution
**When** la condition se débloque (parent valide)
**Then** le bandeau disparaît + un toast confirme ("Ton compte est entièrement actif maintenant")
