# Epic 8 : Continuité Temporelle & Notifications

Servir le moat différenciant vs LLMs grand public : l'utilisateur revient à J+30 et voit "ce qui a bougé" via un écran `DeltaRecap` style Spotify Wrapped léger et des notifications email calées sans urgence fabriquée.

## Story 8.1 : Email transactionnel — abstraction Mailpit local + Postmark prod

As a système Path-Advisor,
I want une couche d'abstraction email permettant Mailpit local en PoC et Postmark / SendGrid en production,
So that les notifications email sont opérationnelles partout sans modification de code (NFR-I2).

**Acceptance Criteria :**

**Given** la couche d'abstraction email
**When** je consulte le code
**Then** une interface `EmailProvider` est définie avec méthodes (`sendTransactional`, `sendBatch`)
**And** une implémentation `MailpitProvider` (local) + `PostmarkProvider` (prod) basculent via env var

**Given** un environnement local
**When** je lance `docker-compose up`
**Then** Mailpit est exposé sur un port (typiquement 8025) avec interface web
**And** tous les emails envoyés en dev arrivent dans Mailpit (vérifiable visuellement)

**Given** la dégradation gracieuse (NFR-R4)
**When** le service email est indisponible
**Then** les envois sont mis en queue avec retry exponentiel
**And** aucun email n'est perdu silencieusement

## Story 8.2 : Engine de notifications email avec templates et opt-in

As a élève / parent / conseillère / école,
I want recevoir des notifications email pertinentes que je peux contrôler (opt-in / opt-out par catégorie),
So that je suis informé sans être spammé (FR47).

**Acceptance Criteria :**

**Given** une table `notification_preferences` par user
**When** je vais dans Paramètres → "Notifications"
**Then** je peux activer / désactiver par catégorie (Calendrier Parcoursup, Réponses école, Nouvelles écoles pertinentes, Rappels de complétion profil)
**And** mes préférences sont sauvegardées immédiatement

**Given** les templates email
**When** un email est envoyé
**Then** il utilise un template MJML ou similaire (responsive mobile-friendly) avec branding Path-Advisor sobre
**And** il inclut un lien "Gérer mes notifications" + lien "Se désinscrire" (obligation légale)

**Given** la conformité RGPD
**When** un user se désinscrit
**Then** ses préférences sont mises à jour
**And** aucun email de cette catégorie n'est envoyé sans qu'un acte explicite ne réinscrive

## Story 8.3 : Notifications calendrier Parcoursup (sans urgence fabriquée)

As a élève (Sarah, Terminale),
I want recevoir des notifications email calées sur le calendrier Parcoursup (ouverture, J-30, résultats),
So that je sois préparée sans angoisse fabriquée (FR47 + UX-DR28 calendrier sans urgence).

**Acceptance Criteria :**

**Given** le calendrier Parcoursup (dates connues par avance, configuration admin)
**When** un jalon approche (ex : "Parcoursup ouvre dans 18 jours")
**Then** un email est envoyé aux élèves concernés (Terminale, post-bac) avec ton factuel
**And** le copy bannit toute urgence ("DERNIÈRE CHANCE", "Plus que 18 jours !!") — UX-DR28
**And** la posture est : "Voici où on en est. Voici ce que tu peux préparer d'ici là."

**Given** les jalons standards
**When** la config est en place
**Then** au moins 5 jalons sont notifiés : Ouverture Parcoursup, J-30 fermeture voeux, Fermeture voeux, Résultats phase principale, Résultats phase complémentaire
**And** chaque notification propose une checklist non-bloquante d'actions ("Voici ce que tu peux préparer")

**Given** la cohérence anti-urgence
**When** un utilisateur de lecteur d'écran consulte la notification
**Then** elle est annoncée sans alarmisme
**And** les CTAs sont calmes ("Revoir mes paris", "Compléter mon profil")

## Story 8.4 : Notification "réponse école" envoi anticipé

As a élève premium,
I want recevoir une notification email quand une école a répondu à mon envoi anticipé,
So that je puisse réagir rapidement (FR47 + lien avec Story 5.8).

**Acceptance Criteria :**

**Given** une école a répondu à mon envoi anticipé
**When** la stat est mise à jour (Story 5.8)
**Then** un email m'informe immédiatement : "INSA Lyon a répondu — voir le détail" + résumé en 1 phrase + CTA "Voir la réponse"

**Given** la conformité émotionnelle
**When** la réponse est "Profil non aligné"
**Then** le ton de l'email est diplomatique (pas "Mauvaise nouvelle !")
**And** il propose des alternatives ("Tu peux explorer d'autres écoles avec un profil similaire")

**Given** la conformité opt-in
**When** un utilisateur a désactivé cette catégorie de notification
**Then** aucun email n'est envoyé
**And** la notification reste visible in-app

## Story 8.5 : Notification "nouvelle école pertinente"

As a élève,
I want être notifié quand une nouvelle école / formation pertinente pour mon profil est ajoutée au référentiel,
So that mon graphe de parcours s'enrichit et je découvre de nouvelles opportunités (FR47).

**Acceptance Criteria :**

**Given** un admin ajoute une nouvelle école au référentiel (Story 9.2)
**When** le job de matching s'exécute (cron quotidien)
**Then** les élèves dont le profil correspond reçoivent une notification email "X écoles de plus correspondent à ton profil ingénieure biomédicale"
**And** le matching utilise les critères des recos vocationnelles (Story 3.3)

**Given** la fréquence d'envoi
**When** plusieurs écoles sont ajoutées en peu de temps
**Then** les notifications sont regroupées (digest hebdomadaire max) pour éviter le spam
**And** un compteur indique "5 nouvelles écoles correspondent à toi"

## Story 8.6 : Composant `DeltaRecap` — écran "voici ce qui a bougé"

As a élève qui revient à J+30,
I want voir un écran d'accueil qui me montre ce qui a bougé depuis ma dernière visite,
So that ma session démarre sur du delta, pas sur l'écran neutre (UX-DR14 + UX-DR29).

**Acceptance Criteria :**

**Given** le composant est implémenté (style Spotify Wrapped léger)
**When** je l'instancie pour un user au retour
**Then** il affiche les types de delta supportés :
- Carte "Réponse école envoi anticipé" : "INSA Lyon a répondu — profil intéressant" + stat avant/après
- Carte "Nouvelles écoles référencées" : "X écoles de plus correspondent à ton profil"
- Carte "Calendrier Parcoursup" : "Parcoursup ouvre dans 18 jours — voici ce que tu peux préparer"
- État stable (rien de neuf) : redirection silencieuse vers la home, pas d'écran vide

**Given** la conformité UX-DR29 (retour avec delta)
**When** je me connecte après J+1 ou plus
**Then** le DeltaRecap s'affiche en plein écran (1 carte par delta)
**And** chaque carte a un CTA primary unique ("Voir le parcours mis à jour", "Voir les nouvelles écoles", "Préparer mes vœux")
**And** un bouton "Tout vu, continuer" passe au dashboard normal

**Given** la conformité émotionnelle
**When** un delta est positif (réponse école positive, nouvelles écoles)
**Then** ton calme, pas confetti, pas "🎉" (anti-cirque)
**When** un delta est négatif (réponse école négative)
**Then** la carte est cadrée constructive ("INSA Lyon a refusé — voici 3 alternatives compatibles")

## Story 8.7 : Composant `CalendarNotification`

As a développeur Path-Advisor,
I want un composant `CalendarNotification` réutilisable pour toute notification calée sur calendrier Parcoursup,
So that le pattern "calendrier sans urgence" soit cohérent (UX-DR17 + UX-DR28).

**Acceptance Criteria :**

**Given** le composant est implémenté
**When** je l'instancie avec props (`jalon`, `daysUntil`, `recommendedActions[]`)
**Then** il affiche un titre factuel ("Parcoursup ouvre dans 18 jours"), une description calme, une checklist d'actions recommandées non-bloquantes
**And** AUCUN compte à rebours visuel agressif (pas de timer rouge clignotant)

**Given** la conformité émotionnelle UX-DR28
**When** je consulte le copy
**Then** il bannit "URGENT", "DERNIÈRE CHANCE", "Plus que X jours !!", "Ne rate pas"
**And** il utilise "Voici où on en est", "Voici ce que tu peux préparer"

**Given** la réutilisation
**When** je l'utilise dans email (Story 8.3) et dans `DeltaRecap` (Story 8.6)
**Then** le même composant alimente les deux contextes
**And** seul le rendering layer change (HTML email vs React app)

## Story 8.8 : Dashboard d'accueil élève — page modulaire post-connexion

As a élève,
I want atterrir après connexion sur une page d'accueil qui rassemble en un coup d'œil mes métiers recommandés, mes parcours sauvegardés et ce qu'il me reste à compléter,
So that je sache immédiatement où j'en suis et quoi faire ensuite, plutôt que de tomber sur une simple liste de recommandations sans contexte (FR47 — complète le "dashboard normal" référencé mais jamais spécifié par la Story 8.6).

**Contexte** : aujourd'hui, la home post-connexion élève est directement `/mes-metiers` (Epic 3 — liste de recommandations brute). La Story 8.6 (`DeltaRecap`) suppose l'existence d'un "dashboard normal" vers lequel son bouton "Tout vu, continuer" redirige — cette story crée ce dashboard, qui devient la nouvelle home élève (`getPostLoginPath` — `apps/web/src/lib/auth/post-login-redirect.ts` — pointe désormais ici pour `role=student`, plus vers `/mes-metiers` directement).

**Acceptance Criteria :**

**Given** je suis un élève authentifié et je me connecte
**When** j'arrive sur ma home (nouvelle route, ex. `/accueil` ou racine authentifiée)
**Then** je vois une page composée de plusieurs modules distincts, pas une liste unique :
- **Module "Tes métiers"** : les 3 recommandations vocationnelles au score le plus élevé (variant compact de `ScoreVocationnel`, Story 3.11), avec lien "Voir tous mes métiers" vers `/mes-metiers`
- **Module "Ta progression"** : score de complétude du profil (Story 2.7) + liste des étapes non terminées avec CTA direct pour les reprendre : onboarding passions/valeurs (Story 2.1) si non fait, niveau/filière (Story 2.2) si non fait, import ou saisie bulletins (Story 2.3/2.4) si `mode_degrade` (Story 2.5)
- **Module "Tes paris"** : les parcours sauvegardés (Story 4.8 `mes-paris`) les plus récents (3 max), avec lien "Voir tous mes paris"
- **État vide par module** : un module sans contenu (ex. aucun pari sauvegardé) affiche un texte d'invitation court + CTA, jamais une section vide silencieuse ni une erreur

**Given** un élève dont le profil est fraîchement créé (aucune recommandation, aucun pari, onboarding non terminé)
**When** il consulte sa home
**Then** le module "Ta progression" domine visuellement la page (c'est la seule chose actionnable) — pas de mise en avant artificielle de modules vides

**Given** la Story 8.6 (`DeltaRecap`)
**When** un élève revient avec un delta à afficher
**Then** le `DeltaRecap` s'affiche en interstitiel PLEIN ÉCRAN au-dessus de cette home (comme déjà spécifié en 8.6) ; "Tout vu, continuer" démonte l'interstitiel et révèle cette page dessous — cette story ne modifie pas 8.6, elle lui donne enfin une cible réelle

**Given** la densité mobile-first (persona élève = mobile primaire, cf. UX spec)
**When** je consulte la home sur mobile
**Then** les modules s'empilent verticalement dans l'ordre : Progression (si incomplet) → Métiers → Paris ; sur desktop, layout 2 colonnes (Métiers + Paris côte à côte, Progression en bandeau supérieur)

**Given** l'accessibilité RGAA AA
**When** un lecteur d'écran navigue la page
**Then** chaque module est une `<section>` avec un titre de niveau cohérent (`h2`) et un `aria-label` explicite, l'ordre de tabulation suit l'ordre visuel
