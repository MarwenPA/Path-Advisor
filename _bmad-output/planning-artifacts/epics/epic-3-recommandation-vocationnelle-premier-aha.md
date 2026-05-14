# Epic 3 : Recommandation Vocationnelle (Premier Aha)

Servir le PREMIER moment "aha" : l'élève reçoit 8 métiers scorés avec phrase recopiable défendable et explicabilité des signaux contributifs (RGPD art. 22).

## Story 3.1 : Service IA `apps/ai-service` activé pour le scoring vocationnel

As a système Path-Advisor,
I want activer le service IA FastAPI (créé en Story 1.1) avec ses premiers endpoints de scoring vocationnel, distinct du back Django principal,
So that le moteur de recommandation scale horizontalement de manière séparée (NFR-SC4) et bénéficie de l'écosystème ML/DL natif Python (ADD-4).

**Acceptance Criteria :**

**Given** le service `apps/ai-service` (FastAPI) déjà initialisé en Story 1.1
**When** je l'active pour le MVP
**Then** il expose les premiers endpoints REST de scoring : `/health`, `/v1/score-metiers`, `/v1/model-version`
**And** il communique avec le back Django via API interne (auth par token de service partagé)
**And** la séparation est physique : 2 conteneurs Docker distincts, scaling indépendant configuré (réplicas FastAPI séparés de Django)

**Given** la frontière Django ↔ FastAPI claire
**When** je consulte un appel de scoring depuis le front
**Then** le flow est : `Next.js → Django API (/recos) → Service FastAPI (/v1/score-metiers) → DB lecture profil + référentiel`
**And** Django est responsable de l'authentification utilisateur, du multi-tenant et de la persistance
**And** FastAPI est responsable uniquement du scoring (stateless côté IA, sauf modèle versionné chargé en mémoire)

**Given** la conformité avec le PoC local-first (ADD-2 + NFR-M1)
**When** un dev installe le projet
**Then** le service IA tourne en local avec ses dépendances Python (scikit-learn, sentence-transformers, pandas, Pydantic v2)
**And** aucune dépendance cloud n'est requise pour le développement (modèles HuggingFace téléchargés au build, Mistral 7B via Ollama local)

**Given** le scaling indépendant en growth
**When** la charge augmente sur le service IA (pics saisonniers janvier-mars)
**Then** le service peut scaler horizontalement (Docker Swarm / Kubernetes / Scaleway Functions) sans toucher au back Django applicatif
**And** un ADR documente la séparation Django (app) vs FastAPI (IA) et leur protocole de communication interne

## Story 3.2 : Référentiel professions MVP (50 métiers curés)

As a content / data ops Path-Advisor,
I want un référentiel de 50+ professions curées avec description, prérequis, débouchés, revenu médian, journée type,
So that le moteur de recommandation a une base de métiers crédible et utilisable dès le MVP (FR21).

**Acceptance Criteria :**

**Given** une table `professions` en PostgreSQL
**When** je consulte le schéma
**Then** elle contient `id`, `slug`, `name`, `description`, `daily_routine`, `requirements_json`, `prospects_text`, `median_salary_eur`, `signals_json` (mots-clés liés aux passions/valeurs/spés), `level_compatibility` (3ème / lycée général / lycée pro)

**Given** le seed initial du MVP
**When** la migration de seed s'exécute
**Then** au moins 50 métiers sont créés couvrant un panel diversifié (sciences, social, tech, arts, BTP, soin, business…)
**And** au moins 15 métiers sont compatibles bac pro / 3ème (pour servir Mehdi)
**And** la curation est documentée (sources : Onisep open data, fiches ROME, validations humaines)

**Given** la qualité des données
**When** je consulte une fiche métier seed
**Then** elle a au minimum : 100-300 mots de description, 5 prérequis, 3 débouchés, 1 fourchette salariale, 1 journée type narrative
**And** aucun métier n'a de champ vide critique

**Given** les contraintes éthiques (risque inégalité Step 2)
**When** la curation est revue
**Then** au moins 30 % des métiers servent les profils "Mehdi" (bac pro, voies techniques, moins valorisées par défaut)

## Story 3.3 : Moteur de scoring vocationnel statistique + content-based

As a service IA Path-Advisor,
I want un moteur de scoring qui produit un score 0-100 par couple (profil élève, métier) basé sur features explicites et filtrage content-based,
So that le scoring soit explicable nativement (RGPD art. 22) et fonctionne sans gros volume de données (cold-start MVP).

**Acceptance Criteria :**

**Given** un profil élève avec passions, valeurs, niveau scolaire, bulletins (ou pas)
**When** un appel `/v1/score-metiers` est effectué
**Then** le service IA retourne une liste de 50 métiers scorés (id + score + signals_contributifs)
**And** la latence est < 3 s P95 (NFR-P1) sur instance de référence

**Given** le calcul du score
**When** un métier est scoré pour un élève
**Then** le score est une somme pondérée de features explicites : recouvrement passions × signaux métier, alignement valeurs, compatibilité niveau scolaire, qualité du dossier scolaire (si bulletins disponibles)
**And** chaque feature contributive est tracée avec son poids dans la réponse (explicabilité)

**Given** un profil incomplet (sans bulletins)
**When** le score est calculé
**Then** le moteur dégrade gracieusement (pondération bulletins → 0, autres features compensent)
**And** un flag `confidence_level` est ajouté à la réponse (Story 3.10)

**Given** la conformité versioning (ADD-10 + NFR-M3)
**When** un déploiement est effectué
**Then** chaque version du modèle est tracée avec : dataset d'entraînement (hash), hyperparamètres, métriques d'évaluation, date de déploiement
**And** un endpoint admin `/v1/model-version` retourne ces infos

## Story 3.4 : Liste métiers scorés affichée à l'élève

As a élève (Sarah, Mehdi, Léa),
I want voir une liste personnalisée de 8 métiers recommandés avec leur score 0-100,
So that je découvre les métiers qui me correspondent dès la fin de l'onboarding (FR20 + premier moment aha).

**Acceptance Criteria :**

**Given** mon onboarding est terminé (passions + niveau + bulletins ou skip)
**When** j'arrive sur l'écran "Mes métiers"
**Then** je vois une liste de 8 cartes `ScoreVocationnel` (Top 8 métiers scorés)
**And** chaque carte affiche : nom métier, score 0-100, phrase recopiable défendable, 3-5 chips signaux contributifs
**And** la liste est affichée en < 3 s P95 (NFR-P1)

**Given** le moment du premier aha
**When** la liste apparaît pour la première fois
**Then** une animation discrète (fade-in séquentiel 100 ms par carte) accueille la révélation
**And** au moins 1 métier inattendu (mais plausible) est inclus dans le Top 8 pour produire la surprise (validation par le moteur)

**Given** un retour ultérieur sur la liste
**When** je reviens consulter mes métiers
**Then** je vois la liste sans animation (anti-cirque UX-DR27)
**And** un indicateur "mis à jour le X" est visible si les recos ont changé depuis ma dernière visite

**Given** je peux interagir avec la liste
**When** je tape sur une carte métier
**Then** j'accède à la fiche métier détaillée (Story 3.5)
**Or** je peux marquer un métier en favori (sauvegarde dans "Mes paris")

## Story 3.5 : Fiche métier détaillée

As a élève,
I want consulter une fiche détaillée par métier (description, journée type, prérequis, débouchés, revenu),
So that je comprenne concrètement ce qu'est un métier avant d'explorer son parcours (FR21).

**Acceptance Criteria :**

**Given** je tape sur une carte `ScoreVocationnel` dans la liste des recos
**When** la fiche s'ouvre
**Then** je vois le composant `FicheMetier` (UX-DR9) avec sections : Hero (nom + score + phrase recopiable) / "C'est quoi" / "Pour qui" / "Comment y aller" / "Écoles cibles" / "Signaux contributifs"

**Given** la fiche est responsive
**When** je la consulte sur mobile (320 px+)
**Then** les sections sont empilées et l'accordéon collapse les sections non-prioritaires
**When** je la consulte sur desktop (1024 px+)
**Then** une sidebar TOC sticky permet de naviguer entre sections, sections en tabs horizontaux

**Given** la conformité accessibilité
**When** un utilisateur de lecteur d'écran consulte la fiche
**Then** la hiérarchie h1 → h2 → h3 est stricte (1 h1 par page, pas de skip)
**And** les sections sont annoncées sémantiquement

## Story 3.6 : Explicabilité des signaux contributifs (RGPD art. 22)

As a élève,
I want comprendre quels signaux ont contribué au score d'un métier recommandé,
So that j'ai confiance dans la recommandation et je peux la défendre, conformément à RGPD art. 22 (FR22).

**Acceptance Criteria :**

**Given** je suis sur une carte `ScoreVocationnel` ou une `FicheMetier`
**When** je tape sur "Pourquoi ce score ?" ou sur un chip signal contributif
**Then** un drawer / popover s'ouvre montrant les signaux qui ont fait monter (ou descendre) ce score
**And** chaque signal est expliqué en langage naturel : "Ton 16 en SVT a fortement contribué (+12 pts)", "Ta passion pour le bénévolat hôpital (+8 pts)", "L'appréciation 'élève engagée' (+4 pts)"

**Given** la conformité art. 22 RGPD
**When** je consulte l'explicabilité
**Then** je vois aussi un lien "Demander une revue humaine" (Story 3.7)
**And** la méthodologie du scoring est accessible en 2 clics depuis n'importe quelle reco (lien "Comment ça marche")

**Given** l'explicabilité est intégrée au design UX
**When** je consulte le composant
**Then** il ne sent pas "explication légale obligatoire" mais "moment produit propre" (Step 4 — "explicabilité comme munition narrative")
**And** le copy est positif : "Voilà les ingrédients qui ont fait monter ce métier", pas "Justification du score"

## Story 3.7 : Demander une revue humaine d'une recommandation

As a élève,
I want demander une revue humaine d'une recommandation qui me semble incorrecte ou choquante,
So that je peux exercer mon droit RGPD art. 22 à l'intervention humaine et le système apprenne (FR23).

**Acceptance Criteria :**

**Given** je suis sur une fiche métier qui me paraît absurde
**When** je tape sur "Cette reco me dérange — demander une revue"
**Then** un formulaire court s'ouvre : raison (3 catégories : "Ne me correspond pas du tout" / "Métier choquant ou inapproprié" / "Autre") + commentaire libre optionnel

**Given** je soumets la demande
**When** la demande est enregistrée
**Then** elle apparaît dans la file d'attente admin (Epic 9)
**And** je reçois un email de confirmation "Ta demande est prise en compte, on te répondra sous 7 jours ouvrés"
**And** la reco contestée est marquée visuellement "en revue" jusqu'à réponse admin

**Given** la revue admin est traitée (Epic 9)
**When** l'admin répond
**Then** je reçois la réponse par email + notification in-app
**And** si la reco était correcte, le copy explique pourquoi sans paternalisme ; si la reco était mauvaise, le modèle est marqué pour ajustement

## Story 3.8 : Signaler une erreur ou information obsolète sur une fiche métier

As a élève ou utilisateur attentif,
I want signaler une erreur ou information obsolète sur une fiche métier,
So that le référentiel reste à jour grâce au community sourcing (FR24).

**Acceptance Criteria :**

**Given** je suis sur une fiche métier et je remarque une erreur
**When** je tape sur "Signaler une erreur" en pied de fiche
**Then** un formulaire compact s'ouvre demandant : type d'erreur (4 catégories : "Description inexacte" / "Débouchés périmés" / "Lien cassé" / "Autre"), localisation précise (champ optionnel pour pointer la section), commentaire libre

**Given** je soumets le signalement
**When** il est enregistré
**Then** il apparaît dans la file admin (Epic 9 — workflow modération sous 7 jours)
**And** je reçois un toast "Merci, ton signalement a été pris en compte"
**And** une trace est ajoutée au journal d'audit

**Given** l'admin traite mon signalement
**When** la fiche est mise à jour
**Then** je reçois (optionnellement, opt-in dans paramètres) une notification "La fiche que tu as signalée a été mise à jour"

## Story 3.9 : Adaptation des recommandations par niveau scolaire

As a élève (Mehdi 3ème ou Sarah Terminale),
I want que mes recos métiers soient adaptées à mon niveau scolaire et à la filière vers laquelle je suis orienté,
So that mes recos soient cohérentes et actionnables (FR25).

**Acceptance Criteria :**

**Given** je suis Mehdi (3ème, orientation bac pro à confirmer)
**When** le moteur me score
**Then** au moins 60 % de mon Top 8 est compatible avec un parcours bac pro
**And** les 40 % restants incluent des métiers généraux accessibles via bac général + études supérieures

**Given** je suis Sarah (Terminale spé Maths + SVT)
**When** le moteur me score
**Then** mon Top 8 privilégie les métiers compatibles avec mes spés (santé, ingénierie, sciences, environnement)
**And** les fiches métier mentionnent explicitement les spés requises

**Given** je change de niveau scolaire (Mehdi qui passe en 2nde Pro)
**When** je mets à jour mon profil (Story 2.6)
**Then** mes recos sont recalculées et la composition du Top 8 évolue en conséquence
**And** un message contextuel m'explique le changement : "Tes recos s'adaptent à ta nouvelle situation"

## Story 3.10 : Niveau de confiance affiché sur les recos en profil incomplet

As a élève Léa qui n'a pas encore ajouté ses bulletins,
I want comprendre que mes recos sont indicatives sans pour autant me sentir "cas spécial",
So that je peux explorer le produit avec dignité et savoir ce qui s'enrichira en complétant mon profil (FR26 + UX-DR25).

**Acceptance Criteria :**

**Given** mon profil est incomplet (sans bulletins)
**When** je consulte mes recos vocationnelles
**Then** la structure visuelle est strictement identique à celle d'un profil complet (mode normal = mode dégradé)
**And** chaque score affiche un label discret "indicatif" en `text-caption color-text-muted` (pas en rouge, pas en alerte)

**Given** je tape sur une carte métier
**When** je consulte l'explicabilité (Story 3.6)
**Then** je vois quels signaux ont contribué + un message factuel "Avec tes bulletins, on pourrait préciser ton score à ±5 pts près au lieu de ±15 actuellement"
**And** un CTA discret propose "Ajouter mes bulletins" (1 tap pour ouvrir le mini-flow)

**Given** la conformité émotionnelle Step 4
**When** je suis Léa
**Then** je ne vois JAMAIS de message culpabilisant ("Tu manques de données" / "Profil insuffisant")
**And** la posture est : voilà ce qu'on a, voilà ce qui s'ajouterait. Choix libre.

## Story 3.11 : Composant `ScoreVocationnel` réutilisable

As a développeur Path-Advisor,
I want un composant `ScoreVocationnel` standardisé affichant un score métier avec phrase recopiable et chips signaux,
So that la présentation des scores soit cohérente sur tous les écrans (UX-DR5 + UX-DR23 pattern phrase recopiable).

**Acceptance Criteria :**

**Given** le composant est implémenté en suivant les tokens design
**When** je l'instancie avec props (`metierId`, `score`, `phraseRecopiable`, `signals[]`, `variant`)
**Then** il affiche :
- Header : nom métier (h3 weight 600) + score 0-100 (chip droite, couleur sémantique selon score)
- Body : phrase recopiable italic + bouton "Copier" subtil (tap-to-copy)
- Footer : 3-5 chips signaux contributifs cliquables → drawer explicabilité (Story 3.6)

**Given** les variants `compact` / `expanded` / `comparison`
**When** je l'utilise dans différents contextes
**Then** `compact` (liste recos) : tout en card 360×160 px max ; `expanded` (drill-down) : sections détaillées ; `comparison` : 2 cartes côte à côte sur mobile (swipe) / desktop (grid)

**Given** l'accessibilité
**When** un lecteur d'écran lit le composant
**Then** le score est annoncé "Compatible à 78 % avec ce métier"
**And** la phrase recopiable a un `aria-label` clair, le bouton copier indique "Copier la phrase défendable"
**And** les chips signaux sont `role="button"` avec navigation clavier

**Given** le tap-to-copy
**When** je tape sur le bouton copier
**Then** la phrase est copiée dans le presse-papier
**And** un toast 3 s confirme "Phrase copiée — colle-la où tu veux"

## Story 3.12 : Composant `FicheMetier` réutilisable

As a développeur Path-Advisor,
I want un composant `FicheMetier` page produit complète avec sections structurées,
So that chaque métier ait une présentation cohérente et exhaustive (UX-DR9).

**Acceptance Criteria :**

**Given** le composant est implémenté
**When** je le rends pour un métier donné (Story 3.4)
**Then** il affiche 6 sections : Hero / C'est quoi / Pour qui / Comment y aller / Écoles cibles / Signaux contributifs

**Given** les variants responsive
**When** je consulte sur mobile (320 px+)
**Then** sections empilées avec accordéon (sections 3, 4, 5 collapsées par défaut)
**When** je consulte sur desktop (1024 px+)
**Then** TOC sticky à gauche + sections en tabs horizontaux

**Given** la variante `print-friendly` (pour artefact conseillère, Epic 5 export)
**When** je rends le composant en mode print
**Then** les sections sont linéarisées en 1 colonne sans CTAs interactifs
**And** une mise en page A4 propre est générée

**Given** l'accessibilité
**When** un lecteur d'écran parcourt la fiche
**Then** la hiérarchie h1 → h2 → h3 est stricte
**And** chaque section a un landmark sémantique (`<section aria-labelledby="...">`)
