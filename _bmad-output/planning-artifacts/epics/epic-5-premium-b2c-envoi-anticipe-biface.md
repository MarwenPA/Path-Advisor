# Epic 5 : Premium B2C & Envoi Anticipé Biface

Permettre à l'élève premium (10,99 €/mois via Stripe ou parent) d'envoyer son profil aux écoles partenaires. L'école répond en 3 actions, la stat d'admission se met à jour en < 5 min.

## Story 5.1 : Intégration Stripe (sandbox local + production)

As a système Path-Advisor,
I want une intégration Stripe abstraite supportant le mode test local (sandbox) en PoC et le mode production en cloud,
So that les paiements sont opérationnels en dev et prod sans modification du code applicatif (NFR-I1).

**Acceptance Criteria :**

**Given** la couche d'abstraction paiement
**When** je consulte le code
**Then** une interface `PaymentProvider` est définie avec méthodes (`createCheckoutSession`, `handleWebhook`, `cancelSubscription`, `getSubscriptionStatus`)
**And** une implémentation `StripeProvider` utilise les clés sandbox en dev, prod en production via env vars

**Given** un environnement local
**When** je lance `docker-compose up`
**Then** Stripe sandbox est configuré avec un webhook listener local (Stripe CLI ou ngrok-like)
**And** je peux tester un paiement end-to-end avec la carte test `4242 4242 4242 4242`

**Given** la conformité PCI-DSS
**When** un paiement est traité
**Then** AUCUNE donnée carte n'est stockée côté Path-Advisor (tokens Stripe uniquement)
**And** Stripe Checkout (hosted) ou Stripe Elements est utilisé (pas de form custom)

## Story 5.2 : Tiers d'abonnement freemium / premium + gating

As a système Path-Advisor,
I want gérer les 2 tiers B2C (Freemium gratuit / Premium 10,99 €/mois) avec gating de fonctionnalités,
So that les features premium sont accessibles uniquement aux abonnés.

**Acceptance Criteria :**

**Given** la table `subscriptions` en PostgreSQL
**When** je consulte le schéma
**Then** elle lie un user_id à un tier (`free` / `premium`), un statut (`active` / `cancelled` / `past_due`), une période (`current_period_end`)
**And** elle référence le `stripe_subscription_id` pour traçabilité

**Given** un user en tier `free`
**When** il tente d'accéder à une feature premium (envoi anticipé, vue parent étendue, notifs proactives)
**Then** le middleware d'autorisation bloque l'accès
**And** un `PaywallContextuel` (Story 5.11) s'affiche au lieu de la feature

**Given** un user en tier `premium` actif
**When** il accède aux features premium
**Then** l'accès est autorisé sans friction
**And** son statut est rafraîchi périodiquement via webhook Stripe

**Given** la dégradation gracieuse
**When** un user premium passe en `past_due` (paiement échoué)
**Then** un grace period de 7 jours est appliqué (features premium toujours accessibles)
**And** des emails de relance sont envoyés à J+0, J+3, J+7
**Then** après 7 jours sans paiement, le tier passe à `free` et les features premium se ferment proprement

## Story 5.3 : Souscription premium par l'élève

As a élève,
I want souscrire à l'abonnement premium 10,99 €/mois pour débloquer l'envoi anticipé et les autres features premium,
So that je puisse activer les leviers stratégiques pour mes vœux Parcoursup.

**Acceptance Criteria :**

**Given** je suis sur un écran déclenchant un `PaywallContextuel` (ex : "Envoyer mon profil à cette école")
**When** je clique sur "Passer en premium — 10,99 €/mois"
**Then** je suis redirigé vers Stripe Checkout (mode hosted)
**And** le checkout affiche : nom du plan, prix, ce que ça débloque, méthode de paiement (CB, Apple Pay, Google Pay)

**Given** je complète le paiement avec succès
**When** Stripe envoie le webhook `checkout.session.completed`
**Then** mon tier passe immédiatement à `premium` (avec rollback si webhook échoue)
**And** je suis redirigé vers la page d'origine avec la feature débloquée
**And** je reçois un email de confirmation

**Given** je veux annuler mon abonnement
**When** je vais dans Paramètres → "Abonnement" → "Annuler"
**Then** une `ConsentDialog` confirme l'annulation
**And** je conserve l'accès premium jusqu'à la fin de la période payée
**And** au-delà, mon tier passe à `free`

## Story 5.4 : Envoi anticipé d'un profil à une école partenaire

As a élève premium,
I want déclencher un envoi anticipé de mon profil à une école partenaire,
So that je puisse obtenir un signal d'admission précoce et augmenter mes chances Parcoursup (FR33).

**Acceptance Criteria :**

**Given** je suis premium et je consulte une fiche école partenaire (Story 4.4)
**When** je clique sur "Envoyer mon profil à cette école"
**Then** un Sheet bottom (mobile) ou modal (desktop) s'ouvre me demandant motivation libre optionnelle (Story 5.5) + confirmation des données partagées
**And** une `ConsentDialog` finale me liste ce que l'école verra (profil scolaire synthétique, motivation, métier visé, parcours sélectionné — pas autres recos)

**Given** je confirme l'envoi
**When** la demande est créée
**Then** un job async est mis en queue (notification email + push à l'école)
**And** je suis redirigé vers "Mes envois" avec mon envoi en statut `pending` (en attente de réponse école sous 7 jours)
**And** une trace est ajoutée au journal d'audit

**Given** je n'ai droit qu'à un nombre limité d'envois par mois (5 envois/mois en premium MVP)
**When** j'atteins la limite
**Then** un message m'informe sans urgence "Tu as utilisé tes 5 envois ce mois — ta limite repart le 1er du mois prochain"
**And** je peux toujours sauvegarder l'école en favori sans envoyer

## Story 5.5 : Motivation libre modérée a priori

As a élève premium,
I want accompagner mon envoi anticipé d'une motivation libre (200-500 mots),
So that je peux contextualiser mon profil au-delà des chiffres scolaires (FR34).

**Acceptance Criteria :**

**Given** je suis dans le flow d'envoi anticipé (Story 5.4)
**When** j'arrive à l'étape "Motivation"
**Then** je peux saisir un texte libre 200-500 mots dans un textarea
**And** un compteur de caractères m'aide à respecter la longueur
**And** un placeholder me donne 2-3 suggestions d'angles

**Given** je soumets ma motivation
**When** le texte est enregistré
**Then** il passe en statut `pending_moderation`
**And** l'envoi à l'école est temporairement bloqué (queue d'attente modération admin Story 9.4)
**And** un email m'informe : "Ta motivation est en cours de relecture (sous 24 h ouvrées)"

**Given** la modération admin approuve la motivation
**When** elle passe en statut `approved`
**Then** l'envoi à l'école est débloqué et le job de notification se déclenche
**And** je reçois une notification "Ton profil est en route vers l'école"

**Given** la modération admin refuse la motivation
**When** elle passe en statut `rejected`
**Then** je reçois un email expliquant le motif et la possibilité de réécrire
**And** l'envoi reste bloqué jusqu'à correction

## Story 5.6 : Espace école partenaire — auth + réception profils

As a école partenaire (Mme Garcia, Polytech Marseille),
I want m'authentifier sur un espace dédié et recevoir les profils élèves envoyés en anticipé,
So that je puisse traiter les candidatures précoces et identifier les profils intéressants (FR35 + FR36).

**Acceptance Criteria :**

**Given** je suis admin école partenaire et j'ai été onboardée par l'équipe Path-Advisor
**When** je me connecte à l'espace école
**Then** j'arrive sur un MFA enrollment au premier login (Story 1.6 — obligatoire NFR-S2)
**And** une fois MFA actif, j'arrive sur ma file de réception des profils

**Given** ma file de réception
**When** je consulte la liste
**Then** je vois les profils reçus en file (les plus récents en haut), avec nom élève, métier visé, parcours sélectionné, score compatibilité école, date réception, statut (`pending` / `responded` / `expired_7d`)
**And** je peux filtrer par statut, trier par date ou par score

**Given** je tape sur un profil
**When** la fiche détail s'ouvre
**Then** je vois `EcoleResponseFlow` (Story 5.12) avec profil scolaire synthétique + motivation déclarée + métier visé + parcours envisagé
**But** PAS les autres recos vocationnelles de l'élève, ni les autres écoles ciblées (frontière RBAC NFR-S4)

**Given** un envoi reçu il y a > 7 jours sans réponse
**When** le statut bascule à `expired_7d`
**Then** l'élève reçoit une notification "L'école n'a pas répondu — stat inchangée"
**And** l'école ne peut plus répondre (entrée archivée)

## Story 5.7 : 3 actions de réponse école

As a école partenaire,
I want répondre à un envoi anticipé via 3 actions explicites (Profil intéressant / Profil non aligné / Demande d'entretien),
So that je donne un signal clair à l'élève qui ajuste ses chances d'admission (FR37).

**Acceptance Criteria :**

**Given** je suis sur une fiche profil élève dans mon `EcoleResponseFlow`
**When** je veux répondre
**Then** je vois 3 boutons d'action distincts : "Profil intéressant — candidature encouragée" (primary), "Profil non aligné" (secondary), "Demande d'entretien" (tertiary avec icône calendrier)
**And** un champ optionnel "Commentaire pour l'élève" (max 200 mots, modéré)

**Given** je choisis "Profil intéressant"
**When** je confirme
**Then** la réponse est enregistrée + l'événement est mis en queue pour propagation (Story 5.8)
**And** un toast confirme "Réponse envoyée — l'élève reçoit la notification dans les 5 min"

**Given** je choisis "Profil non aligné"
**When** je confirme
**Then** une `ConsentDialog` me rappelle que le message à l'élève doit être respectueux et constructif
**And** un template diplomatique est suggéré ("Ton profil est intéressant mais ne correspond pas à nos critères cette année. Continue à explorer !")

**Given** je choisis "Demande d'entretien"
**When** je confirme
**Then** je propose 2-3 créneaux (visio externe en MVP — RDV intégré en fast-follow FR-FF4)
**And** l'élève reçoit la proposition et peut accepter / proposer un autre créneau

## Story 5.8 : Mise à jour stat admission < 5 min après réponse école

As a élève,
I want voir ma statistique d'admission se mettre à jour rapidement après que l'école a répondu à mon envoi anticipé,
So that mes décisions Parcoursup sont basées sur des données fraîches (FR38 + NFR-P5).

**Acceptance Criteria :**

**Given** une école a répondu à mon envoi anticipé
**When** l'événement est mis en queue
**Then** le job de propagation s'exécute en < 5 minutes (NFR-P5)
**And** ma stat d'admission pour cette école est recalculée : "Profil intéressant" → + 10 à + 20 points, "Demande d'entretien" → + 5 à + 10 points + flag entretien, "Profil non aligné" → - 10 à - 20 points

**Given** la stat a été mise à jour
**When** je vois ma fiche école ou mon graphe parcours
**Then** la nouvelle valeur s'affiche avec un badge "+ 14 pts" visible pendant 24 h
**And** une notification push (FR-FF2 fast-follow) ou email (MVP) m'informe : "INSA Lyon a répondu — voir le détail"

**Given** je suis en train de consulter la fiche école au moment de la mise à jour
**When** le polling 30 s (ADD-8 pas WebSocket MVP) détecte le changement
**Then** la valeur se met à jour en place avec une animation discrète 300 ms
**And** aucune action utilisateur n'est requise

## Story 5.9 : Historique des envois anticipés côté élève

As a élève,
I want consulter le statut et l'historique de tous mes envois anticipés,
So that je peux suivre mes démarches et planifier mes vœux Parcoursup (FR39).

**Acceptance Criteria :**

**Given** je vais sur "Mes envois" (depuis le menu profil ou bottom tab)
**When** la page s'affiche
**Then** je vois la liste de tous mes envois, regroupés par statut (En attente / Réponses positives / Réponses négatives / Entretiens demandés / Expirés)
**And** chaque envoi affiche école, métier visé, date d'envoi, statut, impact stat (badge "+ 14 pts" si applicable)

**Given** je tape sur un envoi
**When** la fiche détail s'ouvre
**Then** je vois ma motivation envoyée + la réponse de l'école (texte + action) + l'impact sur ma stat + un lien vers la fiche école

**Given** je n'ai aucun envoi
**When** je consulte la page
**Then** un empty state explique "Tu n'as pas encore envoyé ton profil à une école. C'est une feature premium qui peut booster tes chances d'admission."
**And** un CTA explore "Voir les écoles partenaires" liste les écoles éligibles

## Story 5.10 : Reporting interne école

As a école partenaire (Mme Garcia),
I want consulter un reporting interne sur les profils reçus, mes actions et les conversions,
So that je peux mesurer l'impact de Path-Advisor sur mon recrutement (FR40).

**Acceptance Criteria :**

**Given** je suis dans l'espace école et je vais sur "Reporting"
**When** la page s'affiche
**Then** je vois des KPIs : nombre profils reçus (mensuel + cumul année), répartition par métier visé, par région d'origine, par action prise (intéressant / non aligné / entretien), taux de conversion en candidature Parcoursup déclarée

**Given** je veux explorer en détail
**When** je drill down
**Then** je peux voir le détail par mois, par métier, par profil scolaire
**And** je peux exporter le reporting en CSV ou PDF

**Given** la conformité RGPD
**When** je consulte le reporting agrégé
**Then** aucune donnée nominative n'est visible (les profils sont anonymisés au niveau du reporting)
**And** je dois aller sur la fiche individuelle pour voir le nom (avec audit log)

## Story 5.11 : Composant `PaywallContextuel`

As a développeur Path-Advisor,
I want un composant `PaywallContextuel` qui s'affiche quand un user free tente d'accéder à une feature premium,
So that le passage premium soit déclenché de manière contextuelle, non agressive (UX-DR15).

**Acceptance Criteria :**

**Given** le composant est implémenté
**When** je l'instancie avec props (`feature`, `context`, `benefits[]`)
**Then** il rend une carte ou un Sheet avec titre contextuel "Cette feature est en premium", description (1-2 phrases), 2-3 bénéfices listés, CTA primary "Passer en premium — 10,99 €/mois", CTA secondary "Plus tard"

**Given** la conformité émotionnelle (anti-urgence-fabriquée, anti-FOMO)
**When** le composant s'affiche
**Then** il ne crie JAMAIS ("DERNIÈRE CHANCE !!", "Plus que 3 jours !!")
**And** il ne culpabilise pas (pas de "Tu rates des opportunités")
**And** le ton est factuel : "Voici ce que cette feature t'apporte. Choix libre."

**Given** un user free clique "Plus tard"
**When** le composant se ferme
**Then** il retourne sur sa navigation précédente sans pénalité
**And** un cooldown léger évite que le paywall réapparaisse à chaque tap (max 1×/session par feature)

## Story 5.12 : Composant `EcoleResponseFlow`

As a développeur Path-Advisor,
I want un composant `EcoleResponseFlow` qui affiche un profil élève + permet à l'école de répondre en 3 actions,
So that l'espace école soit cohérent et efficace pour Mme Garcia (UX-DR22).

**Acceptance Criteria :**

**Given** le composant est implémenté
**When** je l'instancie avec props (`studentProfile`, `motivation`, `targetMetier`, `targetSchool`, `parcours`)
**Then** il rend header (nom élève + score compatibilité école + date d'envoi) + section "Profil scolaire" (moyennes, spés, niveau, appréciations enseignants synthétique) + section "Motivation" + section "Métier & parcours visés" + footer (3 boutons d'action)

**Given** les frontières RBAC sont strictes
**When** je consulte un profil reçu
**Then** je ne vois PAS les autres écoles ciblées par l'élève
**And** je ne vois PAS les autres recos vocationnelles de l'élève
**And** un message rappelle "Tu vois uniquement ce que l'élève a choisi de partager avec toi"

**Given** la densité desktop (école = desktop primaire)
**When** je consulte le composant sur écran 1024+ px
**Then** layout en 2 colonnes (profil à gauche, actions à droite)
**And** raccourcis clavier supportés (`i` pour "intéressant", `n` pour "non aligné", `e` pour "entretien")
