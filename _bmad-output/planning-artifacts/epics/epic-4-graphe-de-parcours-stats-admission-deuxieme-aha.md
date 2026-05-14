# Epic 4 : Graphe de Parcours & Stats d'Admission (Deuxième Aha)

Servir le DEUXIÈME moment "aha" et le différenciateur produit central : l'élève voit son graphe-récit interactif avec ses chances réelles d'admission par école. Animation séquentielle 720-800 ms, alternative tabulaire RGAA AA, low-data mode visuellement indiscernable.

## Story 4.1 : Référentiel formations / écoles / établissements MVP (100+ entrées)

As a content / data ops Path-Advisor,
I want un référentiel de 100+ formations et écoles curées (prépas, BTS, BUT, licences, écoles d'ingé, écoles de commerce, lycées pro),
So that les graphes de parcours puissent être construits avec des données crédibles et la carte scolaire respectée (FR28).

**Acceptance Criteria :**

**Given** une table `schools` et une table `formations` en PostgreSQL
**When** je consulte le schéma
**Then** chaque école contient : `id`, `slug`, `name`, `type`, `city`, `region`, `postal_code`, `lat/lon` (carte scolaire), `tuition_min_eur`, `tuition_max_eur`, `apprenticeship`, `internship`, `selectivity_index` (1-5), `public_private`
**And** chaque formation contient : `id`, `name`, `school_id`, `duration_years`, `parcoursup_open`, `affelnet_open`, `target_metiers` (relation many-to-many vers `professions`)

**Given** le seed initial du MVP
**When** la migration de seed s'exécute
**Then** au moins 100 formations + écoles sont créées (curation Onisep open data + Parcoursup CSV + community sourcing manuel)
**And** au moins 15 lycées pro avec leur option (avionique, ébénisterie, électromécanique…) pour servir Mehdi (FR31)
**And** la couverture géographique inclut au moins les 5 grandes métropoles + représentation rurale

**Given** la qualité éditoriale
**When** je consulte une fiche école seed
**Then** elle a au minimum description 100-200 mots, débouchés top 3, dates Parcoursup, frais réels, statut conventionné/internat, lien officiel

## Story 4.2 : Moteur de prédiction d'admission (open data Parcoursup + fourchettes)

As a service IA Path-Advisor,
I want un moteur de prédiction d'admission qui produit une proba ou fourchette par couple (profil élève, école) basé sur les datasets open data Parcoursup,
So that les élèves voient des stats d'admission crédibles sans nécessiter un modèle DL custom (FR29 + NFR-I7).

**Acceptance Criteria :**

**Given** les datasets open data Parcoursup (CSV annuels MENJS)
**When** un import batch est exécuté (job cron mensuel)
**Then** les statistiques d'admission par formation sont calculées et stockées en cache (Redis + table `admission_stats_history`)
**And** chaque formation a au minimum : taux d'admission global, distribution moyennes admises, distribution mentions admises

**Given** un appel `/v1/predict-admission` avec profil élève + école cible
**When** le moteur s'exécute
**Then** il retourne une fourchette (`min_proba`, `expected_proba`, `max_proba`) + cadrage qualitatif (audacieux / réaliste / sûr)
**And** la latence est < 2 s P95 (NFR-P2)

**Given** un profil sans bulletins (Léa)
**When** le moteur prédit
**Then** la fourchette est plus large (30-65 % au lieu de 38-45 %)
**And** le label qualitatif inclut "estimation indicative — affine avec ton profil"

**Given** la conformité éthique
**When** un profil rare ou un score bas est rencontré
**Then** le moteur ne retourne JAMAIS de probabilité < 5 % comme valeur ponctuelle (anti-humiliation)
**And** la garde-fou produit affiche plutôt "Pari très audacieux" sans chiffre cruel

## Story 4.3 : Affichage graphe de parcours par métier

As a élève,
I want voir un ou plusieurs graphes de parcours scolaires concrets menant à un métier sélectionné,
So that je comprenne comment y arriver depuis ma situation actuelle (FR27 + deuxième moment aha).

**Acceptance Criteria :**

**Given** je suis sur une fiche métier (Story 3.5) et je tape sur "Voir le parcours"
**When** la vue parcours s'ouvre
**Then** je vois 1 chemin principal par défaut (UX-DR6) avec 3-5 nœuds (lycée → étape intermédiaire 1 → étape 2 → école cible)
**And** le graphe est rendu en < 2 s P95 (NFR-P2) sur Android 3 Go RAM
**And** sous le graphe, une grille de fiches écoles (`FicheEcole` Story 4.4) est affichée

**Given** plusieurs chemins existent vers ce métier
**When** je consulte la vue
**Then** le chemin affiché par défaut est celui calculé comme le plus probable / accessible pour mon profil
**And** un bouton "Voir d'autres chemins (N)" m'affiche les alternatives

**Given** je suis Mehdi (3ème bac pro)
**When** je consulte le parcours pour "Technicien aéronautique"
**Then** le graphe commence par un lycée pro associé ("Bac Pro Aéronautique option Avionique") et non un lycée général
**And** les cartes écoles sont des lycées pro de ma carte scolaire (FR31)

## Story 4.4 : Fiche école / formation détaillée

As a élève,
I want consulter une fiche détaillée par école / formation (frais, durée, sélectivité, débouchés, dates de candidature),
So that j'aie toutes les infos pour décider d'inclure cette école dans mes vœux (FR28).

**Acceptance Criteria :**

**Given** je tape sur une fiche école dans la grille post-graphe
**When** la fiche complète s'ouvre
**Then** je vois le composant `FicheEcole` (densité Doctolib, UX-DR7) avec header (nom + ville + logo) ; métadonnée première (proba d'admission personnalisée — `CarteAdmission`) ; métadonnées secondaires en pills (durée, statut public/privé, alternance, sélectivité, internat, distance) ; body description ; débouchés top 3 ; dates Parcoursup ou Affelnet

**Given** la fiche est responsive
**When** je consulte sur mobile
**Then** card stacked full-width avec scroll
**When** je consulte sur desktop
**Then** layout deux colonnes (info + carte géographique optionnelle)

**Given** la fiche est partagée (école partenaire envoi anticipé, Epic 5)
**When** un CTA "Envoyer mon profil à cette école" est éligible
**Then** il apparaît visible (premium gating, Epic 5)

## Story 4.5 : Statistique d'admission personnalisée par école

As a élève,
I want voir, pour chaque école cible, ma probabilité personnalisée d'admission avec son cadrage qualitatif,
So that je peux faire des choix stratégiques pour Parcoursup en connaissant mes vraies chances (FR29).

**Acceptance Criteria :**

**Given** je consulte la grille d'écoles post-graphe ou une fiche école
**When** la stat d'admission s'affiche
**Then** je vois le composant `CarteAdmission` (UX-DR8) avec stat principale (display-1) + label qualitatif (audacieux / réaliste / sûr) + ligne de contexte ("moyenne admise dernière promo : 14,5") + levier d'action ("+ 2 points en maths → 58 %") + footnote si applicable

**Given** la conformité Step 7 (chiffre dominant collé au nœud cible dans le graphe)
**When** le graphe affiche le nœud école cible
**Then** la stat est rendue inline avec le nœud (display-1 48-56 px, couleur sémantique)
**And** le label qualitatif est visible directement sous le chiffre

**Given** je suis Léa (profil incomplet)
**When** je consulte mes stats
**Then** le label affiche "estimation indicative — affine avec ton profil" sans dramatiser
**And** la structure visuelle est strictement identique à un profil complet (UX-DR25 mode normal = mode dégradé)

## Story 4.6 : Filtres graphes — proximité, coût, sélectivité, alternance

As a élève,
I want filtrer les graphes de parcours selon des critères (proximité géographique, coût maximum, niveau de sélectivité, alternance possible),
So that les recommandations correspondent à mes contraintes personnelles (FR30).

**Acceptance Criteria :**

**Given** je suis sur la vue parcours d'un métier
**When** je consulte la barre de filtres persistante en haut
**Then** je vois des filtres pills multi-select : Proximité (≤ 50 km, ≤ 200 km, France entière), Coût (gratuit, < 5 000 €/an, < 10 000 €/an, sans limite), Sélectivité (très accessible, accessible, sélectif, très sélectif), Mode (alternance possible, internat)

**Given** je modifie un filtre
**When** le filtre est appliqué
**Then** la grille d'écoles se met à jour en < 1 s sans rechargement de page
**And** un compteur indique "N écoles cibles correspondent à tes filtres"
**And** "Effacer tout" est toujours visible

**Given** je teste une combinaison de filtres qui ne retourne aucune école
**When** la grille est vide
**Then** un empty state explique : "Aucune école ne correspond. Élargis tes critères, vois aussi les écoles privées ?"
**And** un CTA suggère de relâcher un filtre spécifique

**Given** l'accessibilité (UX-DR32 search & filtering pattern Doctolib)
**When** un utilisateur de lecteur d'écran navigue les filtres
**Then** chaque filtre annonce son état + le nombre de résultats appliqués

## Story 4.7 : Adaptation graphe par niveau scolaire (3ème → lycée pro)

As a élève Mehdi (3ème, bac pro),
I want que le graphe de parcours commence par un lycée pro associé à mon orientation (et non un lycée général),
So that mon parcours soit réaliste pour ma situation (FR31).

**Acceptance Criteria :**

**Given** je suis Mehdi (3ème, orientation bac pro à confirmer)
**When** je consulte le graphe pour "Technicien aéronautique"
**Then** le premier nœud est "Bac Pro Aéronautique option Avionique" (à un lycée pro spécifique de ma carte scolaire)
**And** le deuxième nœud est "BTS Aéronautique"
**And** un nœud terminal "option : poursuite école d'ingé en alternance" est inclus

**Given** je peux voir les lycées pro accessibles
**When** la grille d'écoles s'affiche pour le nœud "Bac Pro Aéronautique"
**Then** elle liste 2-3 lycées pro géographiquement accessibles depuis ma commune (carte scolaire intégrée)
**And** les ouvertures Affelnet (dates de candidature 3ème) sont visibles

**Given** je suis Sarah (Terminale)
**When** je consulte le même métier
**Then** le graphe commence par "Bac S / Spé Maths+SVT" (étape déjà accomplie)
**And** continue vers "Prépa BCPST" ou "PASS" ou "IUT Mesures Physiques"
**And** les dates Parcoursup sont affichées (pas Affelnet)

## Story 4.8 : Favoris écoles cibles + "Mes paris"

As a élève,
I want sauvegarder des écoles cibles dans une liste de favoris pour pouvoir les comparer et les retrouver,
So that je puisse construire ma stratégie Parcoursup au fil du temps (FR32).

**Acceptance Criteria :**

**Given** je suis sur une fiche école ou dans un graphe
**When** je tape sur "Ajouter à mes paris" (icône cœur ou bookmark)
**Then** l'école est ajoutée à ma liste "Mes paris" (sauvegarde immédiate, pas de validation)
**And** un toast confirme l'ajout

**Given** je consulte ma page "Mes paris"
**When** elle s'affiche
**Then** je vois toutes mes écoles cibles sous forme de `ParcoursCard` (Strava-style) regroupées par métier
**And** je peux comparer 2 écoles côte à côte en mode `compare`
**And** je peux retirer une école d'un tap

**Given** je n'ai encore aucun pari
**When** je consulte "Mes paris"
**Then** un empty state explique "Tu n'as pas encore exploré tes premiers paris. Va voir tes métiers recommandés et clique sur 'Voir le parcours'."
**And** un CTA me ramène vers la liste de métiers (Story 3.4)

## Story 4.9 : Composant `GraphParcours` (LE composant central)

As a développeur Path-Advisor,
I want un composant `GraphParcours` interactif qui rend un graphe-récit avec animation séquentielle 720-800 ms, hiérarchie visuelle stricte et alternative tabulaire RGAA AA,
So that le moment central de Path-Advisor soit servi avec qualité et conforme à toutes les contraintes (UX-DR6).

**Acceptance Criteria :**

**Given** le composant est implémenté avec react-flow ou SVG custom (décision tech à trancher au prototypage sprint 5)
**When** je l'instancie avec props (`nodes[]`, `edges[]`, `targetSchool`, `admissionStat`, `isFirstRender`)
**Then** il rend le graphe avec nœud cible 64-72 px en zone bas-droite (couleur sémantique selon proba), nœuds intermédiaires 36-44 px plus pâles, layout subtilement diagonal montant ou en arc, liens épaisseur variable plus épais sur segment final, pas d'icônes Lucide dans les nœuds, stat collée au nœud cible + label qualitatif

**Given** la première interaction de la session (`isFirstRender: true`)
**When** le composant se monte
**Then** une animation séquentielle 720-800 ms en 5 phases s'exécute (Nœud 1 lycée 120 ms + pause 60 ms + Lien 1→2 + Nœud 2 180 ms + Lien 2→3 + Nœud 3 180 ms + Lien 3→cible + Nœud cible 220 ms avec overshoot)
**And** labels intermédiaires apparaissent en fade après (+150 ms)
**And** grille écoles cibles apparaît en opacity 0.4→1 après (+200 ms hors séquence)

**Given** un retour ultérieur (`isFirstRender: false`)
**When** le composant se monte
**Then** l'animation NE se rejoue PAS (anti-cirque, UX-DR27)
**And** un très subtil highlight 100 ms sur le nœud cible peut éventuellement s'exécuter

**Given** la conformité `prefers-reduced-motion`
**When** l'utilisateur a activé reduced-motion
**Then** la séquence est remplacée par un fade global 200 ms (`motion-quick`)

**Given** la conformité RGAA AA (NFR-A5)
**When** un utilisateur navigue le composant
**Then** une alternative tabulaire est OBLIGATOIREMENT accessible via un toggle visible "Vue tableau"
**And** la table parallèle a étapes en ligne, écoles cibles en colonne, lisible au lecteur d'écran
**And** les nœuds sont focusables au clavier (tab order : lycée → étapes → cible → CTA)
**And** ARIA `role="img"` + `aria-label` descriptif du parcours est appliqué au SVG container

**Given** un profil incomplet (Léa, low-data mode)
**When** le composant se rend
**Then** la structure visuelle est strictement identique
**And** seule la stat label passe à "estimation indicative"

## Story 4.10 : Composant `FicheEcole` (densité Doctolib)

As a développeur Path-Advisor,
I want un composant `FicheEcole` densité Doctolib avec proba personnalisée comme métadonnée première,
So that les fiches écoles soient scannables en 3 secondes et cohérentes partout (UX-DR7).

**Acceptance Criteria :**

**Given** le composant est implémenté
**When** je l'instancie avec props (`schoolId`, `userProfile`, `variant`)
**Then** il rend header (logo / photo école + nom + ville) + métadonnée première `CarteAdmission` + métadonnées secondaires en pills + body (description + débouchés top 3) + footer (CTAs)

**Given** les variants `card` / `expanded` / `compare`
**When** je l'utilise dans différents contextes
**Then** `card` : grille mobile-friendly ; `expanded` : drill-down full page ; `compare` : deux écoles côte à côte

**Given** la conformité accessibilité
**When** un lecteur d'écran rencontre le composant
**Then** `role="article"` + headings hiérarchiques + métadonnées en `<dl><dt><dd>` sémantique + touch targets 44 × 44 px

**Given** un profil Léa (low-data state)
**When** le composant se rend
**Then** la `CarteAdmission` affiche "estimation indicative"
**But** la structure et toutes les métadonnées sont identiques (UX-DR25)

## Story 4.11 : Composant `CarteAdmission` (Revolut-style)

As a développeur Path-Advisor,
I want un composant atomique `CarteAdmission` réutilisable affichant stat + cadrage qualitatif + contexte + levier d'action,
So that chaque stat d'admission soit présentée de manière cohérente et défendable (UX-DR8 + UX-DR24).

**Acceptance Criteria :**

**Given** le composant est implémenté en suivant les tokens design
**When** je l'instancie avec props (`admissionStat`, `qualitativeLabel`, `contextLine`, `actionLever`, `variant`)
**Then** il rend stat principale en display-1 ou display-2 selon variant, couleur sémantique selon valeur, label qualitatif sous le chiffre + tag visuel, ligne de contexte, levier d'action calculé, footnote optionnelle

**Given** les variants `large` / `medium` / `small` / `export`
**When** utilisé dans différents contextes
**Then** `large` : graphe nœud cible ; `medium` : fiche école ; `small` : liste comparaison ; `export` : re-rendu PNG sans levier

**Given** l'accessibilité
**When** un lecteur d'écran lit le composant
**Then** annonce formatée : "38 % d'admission à INSA Lyon — pari audacieux. + 2 points en maths feraient passer à 58 %."
**And** la couleur sémantique est doublée par le label texte (color-blind safe, UX-DR33)

**Given** une stat récemment mise à jour (après réponse école envoi anticipé, Epic 5)
**When** le composant se rend
**Then** un badge "+ 14 pts" visible pendant 24 h indique le changement
**And** une animation discrète (200 ms fade-in) souligne l'évolution

## Story 4.12 : Composant `ParcoursCard` (Strava-style recap)

As a développeur Path-Advisor,
I want un composant `ParcoursCard` qui résume un parcours sauvegardé en carte capturable Strava-style,
So that la page "Mes paris" et les exports soient visuels et partageables (UX-DR19).

**Acceptance Criteria :**

**Given** le composant est implémenté
**When** je l'instancie avec props (`metier`, `parcours`, `targetSchool`, `admissionStat`)
**Then** il rend une card screenshot-friendly : header (métier visé h3) + mini-graphe (silhouette du parcours en 4-5 nœuds) + `CarteAdmission` variant `small` pour l'école cible + footer (phrase recopiable + bouton "Capturer")

**Given** la card est dense mais aérée
**When** je la rends dans "Mes paris" (Story 4.8)
**Then** elle est lisible en 3 s sans tap
**And** elle tient en 360 × 280 px max sur mobile

**Given** je consulte mes paris au retour J+30 (Epic 8 `DeltaRecap`)
**When** une stat a évolué
**Then** la `ParcoursCard` correspondante a un badge "+ 14 pts" 24 h
**And** est prioritaire en haut de liste

## Story 4.13 : Composant `StatPersonnelle` (indicateur compatibilité additif)

As a développeur Path-Advisor,
I want un composant `StatPersonnelle` optionnel et additif affichant un indicateur de compatibilité personnelle (3 états qualitatifs),
So that les utilisateurs avec bulletins voient une information enrichie sans humilier ceux qui n'en ont pas (UX-DR20).

**Acceptance Criteria :**

**Given** le composant est implémenté
**When** je l'instancie avec props (`compatibility: 'compatible' | 'a_renforcer' | 'au_dessus' | null`, `school`)
**Then** il rend un petit indicateur visuel (point coloré + label texte court "Profil compatible" / "À renforcer" / "Profil au-dessus") sous la `CarteAdmission`
**And** si `compatibility === null`, le composant ne rend RIEN (pas d'état "indisponible" — il disparaît)

**Given** un profil Sarah avec bulletins suffisants
**When** je consulte une fiche école
**Then** le composant affiche son état compatibilité ("Profil compatible" en vert sage discret)
**And** un tooltip optionnel explique en 1 phrase ce que ça veut dire

**Given** un profil Léa sans bulletins
**When** je consulte la même fiche école
**Then** le composant est strictement absent
**And** AUCUN message "Importe tes bulletins pour voir" ne stigmatise

**Given** la conformité UX-DR25 (mode normal = mode dégradé)
**When** Sarah voit son indicateur sur une école A mais pas sur une école B
**Then** l'absence sur l'école B passe inaperçue
