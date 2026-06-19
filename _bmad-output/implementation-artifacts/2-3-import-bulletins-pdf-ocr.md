# Story 2.3: Onboarding step 3 — Import bulletins PDF avec OCR async (chemin principal)

**Epic:** 2 — Profil Élève & Onboarding
**Status:** done
**Sprint:** 5 (Onboarding bulletins & OCR)
**Story Key:** `2-3-import-bulletins-pdf-ocr`
**Estimation:** L (large) — front-end machine à états 6 phases (idle / picking / uploading / ocr_running / recap_editing / validated) + endpoints upload/poll/commit + job OCR async (Tesseract local PoC, Mindee / AWS Textract prod) + stockage S3-compatible chiffré (MinIO local, S3 EU prod) + edge cases HEIC / multi-pages / mauvais cadrage / OCR timeout / OCR low confidence. Sized **3-4 j focused work**, **avec un sous-risque** sur la stack OCR (à figer en spike avant kick-off).

> Story la plus risquée d'Epic 2 et **point pivot** émotionnel de l'onboarding : c'est là que se joue la promesse *"données scolaires objectives sans saisie laborieuse"* (FR14). Si Sarah prend une photo de son bulletin et que ça *marche* en moins de 30 secondes (NFR-P4), Path-Advisor a gagné son premier moment de magie. Si ça rate sans dignité, Mehdi/Léa désinstallent. Cette story implémente le **chemin principal** (OCR réussi) ; le **chemin fallback manuel** est Story 2.4, et le **chemin "Plus tard"** (Léa) est Story 2.5 — les 3 sont accessibles depuis cet écran via 3 cartes de choix initial **strictement équivalentes visuellement** (principe mode dégradé invisible).

---

## 1. User Story

**As an** élève (Sarah Terminale général scanné depuis l'iPhone le soir / Mehdi 3ème avec un bulletin collège photographié sur Android fissuré / Léa qui veut explorer sans bulletins),
**I want** **soit** importer mes bulletins PDF / photos et voir le système extraire automatiquement notes et appréciations en moins de 30 secondes, **soit** basculer sans humiliation vers la saisie manuelle (Story 2.4) si l'OCR rate, **soit** dire "plus tard" et passer à la suite (Story 2.5),
**So that** mon profil scolaire objectif soit construit sans friction si je veux ; le moteur de reco vocationnelle (Epic 3) ait des notes pour pondérer les recos ; et le moteur d'admission (Epic 4) puisse calculer mes chances personnalisées.

**Business value :** sans bulletins, le moteur d'admission Epic 4 produit des fourchettes très larges étiquetées *"estimation indicative"* (Léa-mode). Avec bulletins, il produit des stats personnalisées qui sont **le 2e aha du produit** — c'est ce qui différencie Path-Advisor d'un LLM grand public (un LLM ne peut pas calculer tes chances *toi* spécifiquement sans tes notes). Donc convertir un maximum d'élèves vers le chemin OCR-réussi (vs Plus tard) est un **enjeu de produit central**, mais **jamais** au prix de la dignité Léa. La règle est : on rend l'option scan séduisante, on rend le fallback manuel facile, on rend "Plus tard" parfaitement valide.

**Garde-fous personas activés sur cet écran :**

- **Léa (dignité)** — "Plus tard" est **un choix de pair**, pas une porte d'échec. Aucun ribbon "moins de fonctionnalités", aucun "Tu rates X" — le copy de la card "Plus tard" doit donner envie. Test sprint review : si Léa la lit et culpabilise, on refait.
- **Mehdi (anti-stigma + Android fissuré)** — l'OCR doit tenir sur des photos imparfaites (cadrage approximatif, ombre du téléphone, flash partiel). Mehdi prend la photo dans sa chambre à 21 h sans table. Tests E2E avec **3 photos volontairement médiocres** dans le harness.
- **Sarah (efficacité)** — sur iPhone, le bouton "Prendre une photo" doit ouvrir la **caméra native** en un tap (pas de wizard "Êtes-vous sûr ?"). 3 bulletins importés en moins de 60 s, OCR en moins de 30 s.

---

## 2. Acceptance Criteria (BDD)

### AC1 — Écran d'entrée step-3 : 3 cards de choix équivalentes

**Given** je viens de valider le récap step-2 (Story 2.2) ou j'ai cliqué "Plus tard" sur step-2
**When** je suis redirigé vers `/onboarding/step-3`
**Then** je vois un écran avec :

- En **header sticky** : back chevron (`<`) à gauche enabled (retour vers step-2 récap, `ConsentDialog` light si modifications non sauvegardées) + indicateur de progression `● ● ●` (les 3 dots actifs — on est à la dernière étape) + bouton text-tertiary "Plus tard" à droite **masqué** (puisqu'une des 3 cards EST l'option "plus tard" — on n'a pas besoin du bouton header en double, anti-redondance)
- Titre `text-h2` : *"Tes bulletins, comment tu préfères ?"*
- Sous-titre `text-body` `color-text-muted` : *"3 façons de faire. Aucune n'est mieux qu'une autre — choisis selon ton humeur du moment."*
- **3 cards verticales empilées** (mobile et desktop, single column — anti-comparaison forcée par grille), chacune cliquable plein-écran de la card, taille `xl` (touch target 80 px hauteur minimum), fond `color-bg-2`, border `color-border`, radius `--radius-lg`, padding `space-6` :

```
┌─────────────────────────────────────┐
│ 📸  Scanner / importer mes bulletins │ ← icône Lucide Camera, label text-h3
│     Photo ou PDF, on lit pour toi    │ ← text-body color-text-muted
│     ~30 secondes                     │ ← text-caption color-text-subtle
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ ✍️  Saisir mes notes à la main       │ ← icône Lucide Pencil
│     Formulaire structuré, simple     │
│     ~3 minutes                       │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ ⏭️  Plus tard, je préfère explorer   │ ← icône Lucide ArrowRight
│     d'abord                          │
│     Tu pourras ajouter à tout moment │
│     Recos un peu plus génériques pour│
│     l'instant                        │
└─────────────────────────────────────┘
```

**And** les 3 cards sont **visuellement identiques** (même fond, même border, même radius, même padding, même weight de typo) — la seule différence est l'icône et le copy. **Aucun ribbon "recommandé"**, aucun bouton primary qui distinguerait une option, aucune couleur sémantique différente.
**And** chaque card est `<a href="...">` ou `<button>` accessible clavier, focus visible (outline `color-brand` 2 px), `aria-label` complet *"Scanner ou importer mes bulletins, environ 30 secondes"*
**And** **aucun bouton "Continuer" en footer** — le choix est la card cliquée elle-même (1 tap → flow correspondant)

### AC2 — Flux scan/import : sélecteur de fichiers (mobile vs desktop)

**Given** je tape sur la card "Scanner / importer mes bulletins"
**When** la card est activée
**Then** un **`Sheet bottom`** (mobile) ou un **`Dialog`** centré (desktop) s'ouvre avec :

- Titre `text-h3` : *"Tes bulletins"*
- Sous-titre `text-body` `color-text-muted` : *"Jusqu'à 6 fichiers. PDF, JPEG, PNG ou HEIC."*
- **2 boutons** côte à côte (mobile : stack vertical ; desktop : horizontal, full-width) — niveau secondary :
  - 📷 *Prendre en photo* (caméra native iOS / Android via `<input type="file" accept="image/*" capture="environment">`)
  - 📂 *Choisir un fichier* (galerie / Finder via `<input type="file" multiple accept="application/pdf,image/jpeg,image/png,image/heic">`)
- En dessous, **drop zone** desktop uniquement (hidden sur mobile) : *"Ou glisse tes fichiers ici"* avec icône upload Lucide, border dashed `color-border-strong`, hover state border `color-brand`
- Footer du sheet/dialog : bouton tertiary "Annuler" qui ferme le sheet (focus revient sur la card scan)

**And** côté contraintes fichiers (validées en client + serveur, defense in depth) :

- Formats acceptés : **PDF**, **JPEG**, **PNG**, **HEIC** (iPhone). HEIC est converti automatiquement en JPEG côté serveur (libheif) avant OCR.
- Taille max par fichier : **10 MB** — au-delà, validation côté client refuse avec helper inline `color-warning` *"Trop gros : ce fichier fait X MB, max 10 MB."*
- Nombre max : **6 fichiers** (couvre 3 trimestres × 2 années lycée). Au-delà, helper *"Maximum 6 fichiers — supprime-en pour en ajouter d'autres."*
- Nombre min : **1 fichier** — bouton "Lancer l'analyse" disabled tant que vide

**And** dès qu'au moins un fichier est sélectionné, une **liste de fichiers** apparaît dans le sheet/dialog avec :

```
┌─────────────────────────────────────┐
│ 📄 bulletin-trim1-terminale.pdf  ✕  │ ← icône fichier, nom tronqué si > 30 chars
│    1.2 MB                            │ ← text-caption
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│ 🖼️  IMG_2451.HEIC               ✕  │ ← preview thumbnail 32×32 si image
│    3.4 MB                            │
└─────────────────────────────────────┘
                                       (1/6)
              [ Lancer l'analyse →  ]   ← primary lg, enabled si ≥ 1 fichier
```

**And** la croix `✕` à droite de chaque entrée supprime ce fichier de la sélection (focus revient sur le bouton suivant dans la liste, ou sur "Lancer l'analyse" si liste vide)
**And** **aucun preview / OCR ne démarre avant le clic "Lancer l'analyse"** — l'utilisateur garde le contrôle (RGPD principe minimisation : on n'upload pas tant que pas confirmé)

### AC3 — Upload phase : barre de progression réseau

**Given** je clique "Lancer l'analyse" avec 3 fichiers sélectionnés
**When** l'upload démarre
**Then** le sheet/dialog est **remplacé** par une **page plein écran** `/onboarding/step-3/processing` (server-driven redirect ou state local — choix dev) avec :

- Titre `text-h2` : *"On envoie tes bulletins…"*
- **Liste verticale des fichiers** avec barre de progression individuelle (`Progress` shadcn) — chaque entrée :
  - Icône fichier + nom tronqué
  - Barre de progression 0-100 % (largeur conteneur, hauteur 4 px, `color-brand`)
  - État : *Envoi…* → *Envoyé ✓* (text-caption à droite)
- Total : *Fichier 2 sur 3 — 1.4 MB / 4.8 MB*

**And** les uploads sont **parallèles** (max 3 simultanés pour limiter charge mobile bas-de-gamme) — `PUT` ou `POST multipart` vers `/api/v1/students/me/bulletins/upload` retournant un `bulletin_id` par fichier
**And** chaque upload a un **timeout de 60 s** et **retry exponentiel jusqu'à 3 fois** (1 s → 2 s → 4 s) si erreur réseau (5xx ou timeout)
**And** si tous les retries échouent sur un fichier, ce fichier passe en état *"Pas réussi"* (icône warning Lucide + couleur `color-warning`) — l'utilisateur peut continuer avec les fichiers réussis OU re-tenter (bouton "Réessayer ce fichier" inline) OU revenir en arrière (bouton "Modifier la sélection" → revient sur le sheet de choix de fichiers, état pré-rempli avec ceux uploadés conservés)
**And** au moins **1 fichier uploadé avec succès** est requis pour passer en phase OCR — sinon helper `color-warning` *"Au moins un bulletin a besoin de remonter pour qu'on l'analyse."*

### AC4 — Phase OCR async : `ScenarioLoader` avec mini-narration

**Given** tous les fichiers (réussis) sont uploadés et `bulletin_id` est connu côté front
**When** le front lance le job OCR via `POST /api/v1/students/me/bulletins/ocr/start` avec `{ bulletin_ids: [...] }`
**Then** le serveur :

- Crée un job Celery / RQ (selon stack post-Story 1.1) `ocr_extract(bulletin_id)` par fichier — exécution **parallèle dans le worker pool** (max 3 simultanés)
- Retourne immédiatement `{ job_id, estimated_seconds: 25 }` (estimation basée sur nb_fichiers × 8 s + overhead)
- L'élève passe sur la vue **`ScenarioLoader`** (composant Story 2.8) avec :
  - **Mini-narration séquentielle** affichée en fade-in `motion-quick`, chaque étape ~8 s :
    - *"On reçoit tes bulletins…"* (0-8 s)
    - *"On lit les notes…"* (8-16 s)
    - *"On identifie les appréciations…"* (16-24 s)
    - *"On vérifie tout ça…"* (24-30 s)
  - Une **barre de progression discrète** (4 px, `color-brand`, animation linéaire 0 → 100 % sur `estimated_seconds`) — **basée sur estimation, pas sur progression réelle du job** (anti-frustration, l'OCR n'a pas de signal de progression utile sub-seconde)
  - Sous la barre : *"Estimation : ~25 secondes"* en `text-caption` `color-text-subtle`
  - Aucun bouton d'annulation visible **pendant les 30 premières secondes** (anti-friction prématurée)

**And** le front **poll** `GET /api/v1/students/me/bulletins/ocr/status?job_id=...` toutes les **2 secondes** (jamais < 2 s pour éviter de surcharger) jusqu'à un des 3 états :

- `succeeded` → transition vers récap éditable (AC5)
- `failed` → bascule vers `GracefulFallback` (AC7)
- `timeout` (> 60 s côté serveur) → idem `failed`

**And** **si dépassement 30 secondes** (estimation initiale écoulée), affichage d'un **encart non bloquant** `color-warning` en dessous de la barre : *"Ça prend un peu plus de temps que prévu, on continue."* + bouton tertiary *"Saisir à la main plutôt"* (lance Story 2.4 — fallback opt-in volontaire, **pas** un opt-out qui annule l'OCR ; les bulletins continuent de s'analyser en arrière-plan et seront proposés à fusionner si l'élève finit la saisie manuelle avant)
**And** si l'utilisateur tap "Saisir à la main plutôt" pendant l'OCR :
- L'élève transite vers Story 2.4
- Le job OCR continue côté serveur
- Au retour (si l'OCR finit pendant la saisie manuelle), un **toast info** *"Tes bulletins ont été lus — utiliser plutôt cette analyse ?"* propose le merge des deux sources avec preview avant choix

**And** la barre de progression respecte **reduced motion** (animation linéaire OK, pas d'easing complexe ; fallback : aucune animation, juste affichage *"En cours…"*)

### AC5 — Récap éditable : matières, notes, appréciations par trimestre

**Given** le job OCR est en `succeeded` pour au moins 1 bulletin
**When** la réponse arrive
**Then** l'écran transitionne vers `/onboarding/step-3/review` avec :

- Titre `text-h2` : *"Voilà ce qu'on a lu"*
- Sous-titre `text-body` `color-text-muted` : *"Corrige si besoin — on peut se tromper. Toi seul·e sais ce qui est juste."*
- Un **switcher de bulletin** (Tabs shadcn) en haut si > 1 bulletin :
  - Onglet 1 *"Trim. 1 — Terminale"* / Onglet 2 *"Trim. 2 — Terminale"* / etc.
  - Labels auto-générés depuis OCR (avec heuristique) ; éditable inline si OCR a mal deviné (`Input` shadcn invisible, cliquer pour éditer)
- Pour chaque bulletin actif :

```
┌─────────────────────────────────────────┐
│ Trim. 1 — Terminale [✎]                 │ ← label bulletin éditable
│ Année 2025-2026                          │ ← detected from OCR
│                                          │
│ Tes matières                             │
│ ┌─────────────────────────────────────┐ │
│ │ Mathématiques            14.5 / 20 ✎│ │ ← matière + note + edit icon
│ │ Excellents efforts ce trimestre…    │ │   appréciation tronquée
│ │ Sciences Vie et Terre    13.2 / 20 ✎│ │
│ │ Bon trimestre malgré quelques       │ │
│ │ difficultés sur la génétique…       │ │
│ │ Histoire-Géo HGGSP       15.0 / 20 ✎│ │
│ │ … (8-12 matières au total)          │ │
│ └─────────────────────────────────────┘ │
│                                          │
│ + Ajouter une matière manquante         │ ← bouton tertiary
│ ⚠ 1 matière à confiance faible (cf. ⚠)  │ ← (cf AC6)
└─────────────────────────────────────────┘

           [ Valider ce trimestre → ]      ← primary lg
```

**And** **édition inline** : taper sur une note ou un label de matière le transforme en `Input` shadcn focusé, validation à blur (note : 0-20 décimal, accepte virgule ou point, refuse > 20 ou < 0) ; appuyer sur Échap restaure la valeur précédente, Entrée valide
**And** taper sur l'icône ✎ d'une appréciation ouvre un `Textarea` shadcn (3 lignes default, growable) ; même validation blur/Échap/Entrée
**And** taper sur l'icône supprimer (apparaît au hover/focus, à droite de chaque ligne matière) supprime la matière du bulletin courant après confirmation inline (small confirmation toast *"Supprimée — Annuler"* 5 s)
**And** le bouton "+ Ajouter une matière manquante" ouvre un mini-formulaire inline (sélection matière dans un `Select` shadcn pré-rempli depuis le référentiel correspondant au niveau scolaire de l'élève + champ note + champ appréciation optionnelle)
**And** le **bouton "Valider ce trimestre"** déclenche un PATCH `/api/v1/students/me/bulletins/{bulletin_id}/finalize` avec le payload corrigé ; à la réussite, l'onglet passe en état `validated` (checkmark visible sur le tab) et l'onglet suivant prend le focus
**And** quand **tous les bulletins sont validés**, un bouton primary "Terminer l'onboarding" apparaît en footer remplaçant les "Valider ce trimestre" → redirige vers `/dashboard` (entrée Epic 3)

### AC6 — Indicateur de confiance OCR par champ

**Given** l'OCR renvoie un score de confiance par champ (matière, note, appréciation) entre 0 et 1
**When** la confiance d'un champ est **< 0.7** (seuil à figer en spike sprint kick-off)
**Then** le champ affiche un **indicateur visuel discret** :

- Icône warning Lucide 14 px à gauche du champ, couleur `color-warning` (#C7841B, distincte du danger)
- Au hover/focus, `Tooltip` shadcn *"À vérifier — l'OCR a un doute sur ce champ"*
- Le champ est **automatiquement focusable en premier** dans le tab order du bulletin (pré-attire l'attention sans bloquer)

**And** un **résumé en haut du récap** *"⚠ N champ(s) à vérifier"* en `color-warning`, avec lien tertiary *"Voir les champs"* qui scrolle à la première occurrence
**And** **aucune obligation de corriger** les champs low-confidence avant validation — l'élève peut valider tel quel (responsabilité user)
**And** la donnée brute OCR (avant correction) + le score de confiance sont stockés côté serveur **séparément** de la donnée corrigée, pour audit longitudinal et amélioration du modèle (cf Story 9.5 versioning modèles IA)

### AC7 — Fallback `GracefulFallback` si OCR rate complètement

**Given** le job OCR est en `failed` OU `succeeded` mais **aucun champ exploitable** (confidence moyenne < 0.3, ou < 3 matières extraites — seuils à figer en spike)
**When** la réponse arrive
**Then** l'écran transitionne vers un **`GracefulFallback`** (composant Story 2.9) avec :

- **Aucune alerte rouge / aucun "ERREUR"** — le ton est calme, factuel
- Titre `text-h2` : *"Ton bulletin a un format qu'on connaît pas encore"*
- Description `text-body` : *"Pas grave. Saisis-le à la main — 5 champs et c'est bon. Tu pourras retenter avec une photo plus nette si tu veux."*
- **2 CTAs équivalents en weight visuel** (cf principe no-dark-pattern Story 1.14) :
  - Primary : *"Saisir à la main"* (→ Story 2.4)
  - Secondary : *"Réessayer avec une autre photo"* (→ revient sur le sheet AC2 avec la sélection vide, focus sur le bouton "Prendre en photo")
- Pied : un lien tertiary *"Plus tard, je préfère explorer d'abord"* (→ Story 2.5)

**And** le bulletin échoué est **stocké côté serveur 30 jours** avec son score de confiance pour amélioration produit (audit log Story 1.13 : event `ocr_failed_low_confidence`) — l'élève peut visualiser et supprimer ses fichiers depuis `/profile/edit/bulletins` (Story 2.6)
**And** **aucun message culpabilisant** ne mentionne que c'est *son* bulletin qui est en cause (*"Ton bulletin a un format…"* met l'agentivité sur le SYSTÈME, pas sur l'élève). Test sprint review : copy approuvé par Mehdi/Léa proxies.

### AC8 — Niveau scolaire adapte le référentiel matières

**Given** l'élève a déclaré son niveau en step-2 (`college_3eme` / `lycee_*` / `postbac`)
**When** le récap (AC5) ou l'ajout manuel (AC5 "+ Ajouter") s'affiche
**Then** le **référentiel matières proposé** s'adapte :

- **Collège (3ème, Mehdi)** : Maths, Français, Histoire-Géo, EMC, SVT, Physique-Chimie, Anglais LV1, LV2 (au choix), EPS, Arts plastiques, Musique, Techno (~11 matières)
- **Lycée général** : selon spécialités déclarées en step-2, le référentiel inclut les **matières du tronc commun** (Français en 1ère, Philo en Terminale, Histoire-Géo, LV1, LV2, EPS, Enseignement scientifique) + les **2-3 spés** + matières optionnelles (Maths complémentaires, LCA, etc.) — ~10-13 matières
- **Lycée techno / pro** : référentiel selon série (STMG / STI2D / Bac Pro spécialité) — figé en spike post-merge step-2 (le détail des matières par série est un travail de référentiel à faire)
- **Post-bac** : référentiel vide par défaut (post-bac variable selon formation) — l'élève ajoute librement via "+ Ajouter une matière"

**And** l'OCR utilise une **table de mapping fuzzy** (Levenshtein < 3) pour rapprocher le texte extrait du référentiel — ex. "Math" / "Mathématiques" / "Maths" → `mathematiques`. Échec de mapping → matière conservée en string brute avec flag `unmapped: true`, l'élève peut la corriger manuellement
**And** le **référentiel évolue** indépendamment des bulletins archivés (versionning `subjects_ref_version` stocké sur le bulletin, parallèle au `level_ref_version` Story 2.2)

### AC9 — Persistence + reprise (cohérent avec 2.1 / 2.2)

**Given** je suis dans n'importe laquelle des phases (upload, OCR, recap_editing)
**When** je quitte l'app
**Then** l'état est **persisté** :

- Phase **upload** : si l'upload a démarré, les fichiers uploadés restent côté serveur. Les fichiers non encore uploadés sont **perdus** (limitation acceptable — l'élève peut re-sélectionner facilement). État serveur : `bulletins_upload_status = "partial"`.
- Phase **OCR** : le job continue côté serveur indépendamment du front. Au retour, le front re-poll le statut.
- Phase **recap_editing** : les corrections **non encore validées** sont sauvegardées en localStorage `bulletins_recap_draft_${bulletin_id}` au debounce 500 ms sur chaque edit. Au retour, le draft est réappliqué.
- Phase **validated** : aucune perte possible (déjà committed côté serveur).

**And** si je rouvre `/onboarding/step-3` :
- Si `bulletins_upload_status === "completed"` ET `ocr_status === "succeeded"` ET il existe ≥ 1 bulletin non `validated` → reprends en mode `recap_editing` sur l'onglet du premier bulletin non validé
- Si `ocr_status === "running"` → reprends en mode `ScenarioLoader` poll status
- Si `ocr_status === "failed"` → reprends en `GracefulFallback`
- Si tous les bulletins sont `validated` → redirect `/dashboard`
- Sinon (rien en cours) → reprends sur l'écran AC1 (3 cards de choix)

### AC10 — Accessibilité RGAA AA

**Given** l'écran 2.3 et toutes ses phases
**When** je teste avec clavier seul, lecteur d'écran, et `prefers-reduced-motion: reduce`
**Then** **tout est navigable au clavier** :

- AC1 : Tab navigue les 3 cards dans l'ordre, Entrée active
- AC2 : Tab navigue boutons "Photo" / "Choisir" / liste fichiers / "Lancer l'analyse" ; flèches sur les fichiers pour les supprimer
- AC4 : `ScenarioLoader` annonce les étapes via `aria-live="polite"` (chaque transition de phrase)
- AC5 : Tab navigue le switcher Tabs (flèches horizontales pour changer d'onglet), puis les matières / notes / appréciations dans l'ordre DOM. Édition inline focusée automatiquement à l'activation de l'icône ✎.
- AC7 : `GracefulFallback` focus initial sur primary "Saisir à la main"

**And** **HTML sémantique** :

- AC1 : `<nav aria-label="Options d'import bulletins"><ul>` avec `<li>` cliquables (ou `<button>` accessibles avec `aria-label` explicite)
- AC4 : `role="progressbar" aria-valuenow aria-valuemin aria-valuemax` sur la barre, mise à jour live
- AC5 : `<table>` sémantique pour la liste matières — pas un `<div>` styled, vraie table HTML avec headers `<th>` (matière / note / appréciation) — RGAA strict pour données tabulaires
- AC6 : indicateur warning par champ via `aria-describedby` pointant vers un `<span class="sr-only">À vérifier</span>` adjacent

**And** **annonces dynamiques** :

- Upload : *"Fichier 1 sur 3 envoyé. 33 %."*
- OCR running : annonce de chaque phrase de narration (chaque ~8 s, pas plus fréquent pour ne pas saturer SR)
- OCR success : *"Lecture terminée. 12 matières trouvées. Récap éditable disponible."*
- OCR failed : *"On n'a pas pu lire ce bulletin. Options disponibles : saisir à la main, réessayer, plus tard."*
- Édition d'une note : annonce *"Maths, 14.5 sur 20, modifié."* au blur

**And** **reduced motion** :

- Barre de progression : reste linéaire, pas d'easing
- `ScenarioLoader` : transitions de phrases instantanées (sans fade)
- Animations check-icon sur tab "validé" : instantané

**And** **touch targets** : tous boutons, fichiers, onglets, icônes édition respectent 44 × 44 px minimum (zone tactile étendue via padding/`::before` sur les icônes 14 px)

---

## 3. Tasks / Subtasks

### Review Findings (2026-06-20)

**Decision-needed (4)**

- [x] [Review][Decision] AC9-F1: Aucune logique de reprise au montage — machine démarre toujours en `idle` sans vérifier l'état serveur (bulletins uploadés, OCR en cours, etc.) — AC9 spécifie clairement cette reprise ; la question est : implémenter maintenant ou fast-follow ? [onboarding-step3.tsx]
- [x] [Review][Decision] AC1-F1: Header sticky (back chevron, `● ● ●`, bouton "Plus tard" caché) absent du rendu `idle` — appartient-il à ce composant ou au layout parent `(authenticated)/onboarding` ? [onboarding-step3.tsx]
- [x] [Review][Decision] AC4-F4: Toast "Tes bulletins ont été lus — utiliser plutôt cette analyse ?" lors du retour depuis saisie manuelle non implémenté — fonctionnalité cross-page complexe (état global / flag serveur) ; implémenter maintenant ou différer en fast-follow ?
- [x] [Review][Decision] AC5-F3: "+ Ajouter une matière" écrit directement `"Nouvelle matière"` hardcodé sans Select du référentiel — implémentation simplifiée ou referential Select complet en scope ?

**Patch — High (7)**

- [x] [Review][Patch] #1 OCR poll URL utilise `bulletin_id` au lieu de `job_id` [use-ocr-job.ts:337] — casse tous les appels de status en prod
- [x] [Review][Patch] #2 Seul le premier `bulletinId` est pollé ; tous les recaps reçoivent les champs du bulletin 1 [onboarding-step3.tsx:49-89] — multi-bulletin silencieusement cassé
- [x] [Review][Patch] #3 Upload progress bars bloquées à 0 % — `useBulletinUpload` met à jour `fileProgress` mais la machine ne reçoit jamais d'événement `FILE_PROGRESS` [onboarding-step3.tsx:236-242]
- [x] [Review][Patch] #4 `<ul>` imbriqué dans `<tbody>` — HTML invalide, casse RGAA et VoiceOver [bulletin-recap-editor.tsx]
- [x] [Review][Patch] #5 Changement d'onglet déclenche `VALIDATE_BULLETIN` au lieu d'un événement dédié — valide silencieusement un bulletin non-relu [onboarding-step3.tsx:273-275]
- [x] [Review][Patch] #6 `handleValidateBulletin` n'inspecte pas `res.ok` — en cas de 4xx/5xx, supprime le draft localStorage et marque validated côté machine alors que le serveur n'a rien commité [onboarding-step3.tsx:173-194]
- [x] [Review][Patch] #7 `tasks_ocr.py` : bloc `except Exception` référence `bulletin` avant affectation si `job.bulletin` est cassé — masque l'exception originelle [tasks_ocr.py:~168]

**Patch — Medium (18)**

- [x] [Review][Patch] #9 `RETRY_SCAN` utilise `assign({ ...initialContext })` (spread objet) — XState v5 attend une fonction ; les champs array (`files`, `recaps`, `bulletinIds`) ne sont pas correctement assignés [onboarding-step3-machine.ts:232]
- [x] [Review][Patch] #10 `fileProgress` keyed sur `file.name` — collision si deux fichiers ont le même nom [use-bulletin-upload.ts:289]
- [x] [Review][Patch] #11 `localStorage.setItem` en `QuotaExceededError` : catch vide, l'étudiant croit ses corrections sauvegardées [onboarding-step3.tsx:31-35]
- [x] [Review][Patch] #12 Clé localStorage sans préfixe `userId` — collision entre deux étudiants sur le même device [onboarding-step3.tsx:20]
- [x] [Review][Patch] #13 `VALIDATE_BULLETIN` : condition `i > 0` dans `findIndex` empêche de revenir à l'onglet index 0 [onboarding-step3-machine.ts:214-218]
- [x] [Review][Patch] #14 `AbortController` créé mais jamais connecté au XHR — dead code trompeur ; les retries n'héritent pas du signal d'annulation [use-bulletin-upload.ts:~210-252]
- [x] [Review][Patch] #15 `onModifySelection` et `onRetry` non passés à `<UploadProgress>` — boutons "Modifier la sélection" et "Réessayer ce fichier" silencieusement absents [onboarding-step3.tsx:244]
- [x] [Review][Patch] #17 `tasks_purge.py` : S3 delete avant DB delete — si le DB échoue, l'objet S3 est perdu ; inverser l'ordre [tasks_purge.py:50-51]
- [x] [Review][Patch] #18 Cache TanStack Query `["ocr-status", bulletinId]` non invalidé au `RETRY_SCAN` — OCR successif peut résoudre immédiatement depuis le cache [onboarding-step3.tsx]
- [x] [Review][Patch] #19 `OCRStartView` : `bulletin_ids` dupliqués retournent 404 trompeur au lieu de 400 [views.py:138-147]
- [x] [Review][Patch] #20 Champ appréciation : pas d'indicateur low-confidence alors que spec AC6 couvre matière + note + appréciation [bulletin-recap-editor.tsx]
- [x] [Review][Patch] #21 `pickerFilesRef.current` non réinitialisé au `RETRY_SCAN` — anciens fichiers persistent dans le sheet [onboarding-step3.tsx]
- [x] [Review][Patch] #22 `<Progress>` shadcn sans `aria-valuenow`/`aria-valuemin`/`aria-valuemax` [upload-progress.tsx:59-66]
- [x] [Review][Patch] #23 Suppression matière sans toast de confirmation "Supprimée — Annuler" (5 s) [bulletin-recap-editor.tsx]
- [x] [Review][Patch] #26 `UPLOAD_START` guard vérifie `context.files` (machine state) mais `handleLaunchUpload` lit `pickerFilesRef` — désynchronisation possible [onboarding-step3.tsx:128]
- [x] [Review][Patch] #27 `resolve({ bulletinId: data.id })` sans vérification de type — `data.id` undefined propage silencieusement [use-bulletin-upload.ts:227]
- [x] [Review][Patch] #37 `fileProgress` non réinitialisé entre deux tentatives d'upload — progress stale sur retry [use-bulletin-upload.ts]
- [x] [Review][Patch] #38 Incohérence `bulletin_id` (snake) / `bulletinId` (camel) à la frontière API sans mapping explicite

**Patch — Low (11)**

- [x] [Review][Patch] #28 Fuzzy mapper : chaîne vide peut matcher `physique_chimie` (distance 2) [fuzzy_subject_mapper.py:76]
- [x] [Review][Patch] #29 Fuzzy mapper : pas de garde longueur — input OCR > 100 chars ralentit inutilement [fuzzy_subject_mapper.py:91-104]
- [ ] [Review][Patch] #30 `package-lock.json` : hash sha512 de `@xstate/react` trop long (92 chars au lieu de 88) — `npm ci` échouera en CI [package-lock.json:65] — nécessite `npm install` en local
- [x] [Review][Patch] #31 Draft localStorage écrit synchroniquement à chaque edit — debounce 500 ms manquant [onboarding-step3.tsx:197-199]
- [x] [Review][Patch] #32 `purge_expired_bulletins` : pas d'assertion `USE_TZ=True` — décalage DST possible [tasks_purge.py]
- [x] [Review][Patch] #33 Encart "On essaie de récupérer…" absent lors d'une erreur réseau pendant le poll OCR [ocr-loader.tsx]
- [x] [Review][Patch] #34 Quand `matieres.length === 0` : bouton Valider disabled mais pas de helper text ni lien "Supprimer ce bulletin entier" [bulletin-recap-editor.tsx]
- [x] [Review][Patch] #35 `aria-describedby` ID collision possible si deux matières ont le même nom [bulletin-recap-editor.tsx:105]
- [x] [Review][Patch] #36 Pas de `prefers-reduced-motion` sur la barre de progression upload [upload-progress.tsx]
- [ ] [Review][Patch] #39 Fixtures OCR (bulletin_clean.pdf / bulletin_blurry.jpg / etc.) absentes du dossier tests [apps/api/apps/bulletins/tests/fixtures/] — déféré (voir deferred-work.md)

**Defer (5)**

- [x] [Review][Defer] AC2-F1: Sheet toujours utilisée — Dialog centré desktop non implémenté [file-picker-sheet.tsx] — deferred, mobile-first MVP acceptable
- [x] [Review][Defer] AC2-F3: Thumbnail preview 32×32 pour images non implémenté [file-picker-sheet.tsx] — deferred, UI enhancement faible impact
- [x] [Review][Defer] AC6-F1: Champs low-confidence non remontés en premier dans le tab order [bulletin-recap-editor.tsx] — deferred, a11y enhancement complexe
- [x] [Review][Defer] AC10-F4: `ScenarioLoader` `aria-live` non vérifiable ici (hors scope, Story 2.8) — deferred, dependency risk
- [x] [Review][Defer] Retry XHR: `refetchInterval` actif pendant retries TanStack Query [use-ocr-job.ts] — deferred, edge case négligeable en pratique

### T1 — Spike OCR stack (pré-requis bloquant, ~0.5 j)

**Avant kick-off de la story**, run un **spike technique** documenté dans `docs/spikes/ocr-stack-2026-05.md` pour figer :

- **PoC local** : Tesseract 5.x via `pytesseract` wrapper Python — quel preset (`--psm 6`, `--oem 3`), dictionnaire français packagé, comportement sur 3 photos test (1 PDF généré numérique propre, 1 photo nette mobile, 1 photo médiocre mobile)
- **Prod** : choix **Mindee** (API spécialisée éducation FR, mais coût à l'usage) **vs AWS Textract** (généraliste, EU region, plus cher mais plus prévisible). Critères : précision sur bulletins FR, coût au scan, latence P95, RGPD (DPA, sous-traitance EU)
- **Score de confiance** : disponible des deux côtés ? format compatible ? seuil 0.7 acceptable ?
- **Format de retour structuré** : prévoir un schéma normalisé `OCRExtractionResult = { fields: [{key, value, confidence, bbox}], raw_text, language, processing_ms }` indépendant du provider (anti-vendor-lock)

**Output spike** : doc + décision provider prod ou *"Tesseract suffit en MVP, on swap quand on a du budget"* — dépend des résultats sur photos test

### T2 — Backend : stockage S3, upload, modèle Bulletin (AC2, AC3, AC9)

- Modèle `Bulletin` avec colonnes : `id (uuid)`, `student_id (fk)`, `file_path (S3 key, chiffré côté serveur via SSE-S3 ou SSE-KMS)`, `original_filename`, `file_size_bytes`, `mime_type`, `uploaded_at`, `uploaded_status (uploaded | failed)`, `level_at_upload (varchar)`, `subjects_ref_version`, `expires_at (TIMESTAMPTZ, default 30 jours après création si jamais validé — pour purge auto)`
- Endpoint `POST /api/v1/students/me/bulletins/upload` (multipart, 1 fichier à la fois ou batch — décision dev) → stocke sur MinIO local / S3 EU prod, retourne `{ bulletin_id, file_path }`
- Encryption at-rest : SSE-S3 minimum (clé AWS-managed), SSE-KMS si budget (clé customer-managed)
- RLS Story 1.8 : un élève lit/écrit/supprime que ses propres bulletins
- Migration Alembic
- **Audit log Story 1.13** : `bulletin_uploaded` event sur chaque upload

### T3 — Backend : job OCR async + endpoints status/finalize (AC4, AC5, AC6, AC7)

- Modèle `BulletinOCRJob` : `id`, `bulletin_id (fk)`, `status (pending | running | succeeded | failed | timeout)`, `started_at`, `completed_at`, `raw_extraction (JSONB — Tesseract / Mindee output)`, `confidence_avg`, `error_message`, `provider (tesseract | mindee | textract)`, `provider_version`
- Worker Celery / RQ task `ocr_extract(bulletin_id)` qui :
  - Récupère fichier S3
  - Convertit HEIC → JPEG si besoin (libheif)
  - Appelle Tesseract (PoC) ou Mindee/Textract (prod)
  - Normalise output au schéma commun
  - Stocke `raw_extraction` brut + applique mapping fuzzy (Levenshtein) sur référentiel matières du `level_at_upload`
  - Update status + `confidence_avg`
  - Timeout serveur : 60 s par bulletin
- Endpoint `POST /api/v1/students/me/bulletins/ocr/start` retourne `{ job_id, estimated_seconds }`
- Endpoint `GET /api/v1/students/me/bulletins/ocr/status?job_id=...` retourne `{ status, progress?, extraction?, error? }`
- Endpoint `PATCH /api/v1/students/me/bulletins/{bulletin_id}/finalize` accepte corrections élève + flip `validated_at`
- **Audit log Story 1.13** : `ocr_succeeded` / `ocr_failed_low_confidence` / `bulletin_finalized` events
- Job de purge auto (Celery beat quotidien) : supprime les bulletins avec `expires_at < now() AND validated_at IS NULL`

### T4 — Frontend : machine à états + composants (AC1-AC10)

- Route Next.js : `apps/web/app/(auth)/onboarding/step-3/page.tsx` (server component dispatching sur état initial)
- Composant racine `<OnboardingStep3 />` avec **state machine XState ou useReducer** (décision dev) gérant les phases : `idle | picking_files | uploading | ocr_running | recap_editing | fallback | validated`
- Sous-composants :
  - `<ImportChoice3Cards />` (AC1 — réutilisé par Stories 2.4 et 2.5 cards correspondantes ; **factorisation à prévoir**)
  - `<FilePickerSheet />` (AC2)
  - `<UploadProgress />` (AC3)
  - `<OCRLoader />` (AC4) — **dépend de Story 2.8 `ScenarioLoader`** (cf §Dependency tradeoff)
  - `<BulletinRecapEditor />` (AC5, AC6)
  - `<OCRGracefulFallback />` (AC7) — **dépend de Story 2.9 `GracefulFallback`**
- Hooks : `useBulletinUpload()`, `useOCRJob(jobId)` (polling 2 s avec TanStack Query), `useLocalStorageDraft('bulletins_recap_draft_*')`

### T5 — Tests (front + back)

- **Backend (pytest)** :
  - Upload accepte PDF / JPEG / PNG / HEIC, rejette autres formats avec 415
  - Upload > 10 MB → 413
  - HEIC est converti en JPEG avant OCR (mock libheif si nécessaire)
  - Job OCR : mock Tesseract output sur 3 fixtures (clean / partial / failed) → status correctement déterminé
  - Mapping fuzzy : "Mathematiques" / "Maths" / "MATH" → `mathematiques` ; "Truc Inconnu" → `unmapped: true`
  - Finalize : élève peut corriger note 14.5 → 15.0, audit log enregistre delta
  - RLS : élève A ne peut pas lire bulletin de élève B
  - Purge job : bulletin créé 31 j auparavant, jamais validated → supprimé du S3 + base
- **Frontend (Vitest + RTL)** :
  - AC1 : 3 cards visuellement identiques (snapshot)
  - FilePickerSheet : sélection fichiers, validation taille, retrait fichier
  - UploadProgress : barre 0-100 % live, retry sur erreur
  - OCRLoader : transitions de phrases respectent ~8 s, fallback "Saisir à la main" apparaît à 30 s
  - BulletinRecapEditor : édition inline d'une note, validation 0-20, restauration sur Échap
  - GracefulFallback : 2 CTAs équivalents weight (test classNames identiques pour size)
  - Reduced motion : pas de fade, pas d'animation easing
- **E2E (Playwright)** : 3 scénarios harness
  - **Sarah happy path** : 2 bulletins PDF propres → OCR succeed → édition 1 correction → validé → redirect dashboard. < 90 s simulés.
  - **Mehdi photo médiocre** : 1 photo cadrage approximatif (fixture provided) → OCR low confidence → 3 champs `color-warning` visibles → corrige 2 → valide → ok
  - **Léa OCR échec** : photo blanche / corrompue → GracefulFallback → choisit "Plus tard" → redirect dashboard avec `bulletins_status = "postponed"`
- **A11y (axe-core)** : chaque phase passe sans nouvelle violation critique ; table récap audité spécifiquement (`<th>` corrects)
- **Manuel** : VoiceOver iOS sur 2 phases critiques (OCRLoader, BulletinRecapEditor) ; test sur Android 3 Go (Mehdi-like, photo prise par l'appareil) avec OCR Tesseract local

### T6 — Documentation

- `docs/onboarding/step3-bulletins.md` : flow visuel + machine à états + variantes par persona + dépendances 2-8/2-9
- `docs/spikes/ocr-stack-2026-05.md` : output du spike T1
- `docs/a11y/onboarding-step3.md` : checklist VoiceOver/NVDA, en insistant sur la table récap

---

## 4. Dev Notes

### 4.0 Dependency tradeoff : Stories 2.8 (`ScenarioLoader`) et 2.9 (`GracefulFallback`)

Ces deux composants Couche 3 sont **prérequis fonctionnels** de 2.3 :

- 2.8 `ScenarioLoader` : utilisé en AC4 pour l'attente OCR ~30 s
- 2.9 `GracefulFallback` : utilisé en AC7 pour l'échec OCR

**2 chemins possibles** (décision à prendre au sprint planning) :

**Option A — Build 2.8 et 2.9 d'abord (recommandé si bande passante)**

- Avantage : 2.3 consomme des composants stables, vrais composants Couche 3 du design system, réutilisés par d'autres stories (StoryExport pour 2.8, OCR + Stripe + envoi anticipé pour 2.9)
- Coût : ~0.5 j de retard kick-off 2.3

**Option B — Build inline minimal dans 2.3 + refactor en 2.8/2.9 plus tard**

- Avantage : démarrage immédiat 2.3 sans dépendance
- Coût : dette technique (2 implémentations différentes du loader / fallback à fusionner), risque de drift visuel
- Acceptable seulement si 2.8 et 2.9 sont planifiés **dans le même sprint** que 2.3 avec consigne explicite de refacto avant merge

**Recommandation Marwen + Claude** : **Option A**. Les composants 2.8 et 2.9 sont identifiés depuis l'UX spec Step 11 (sprint 9 prévu) ; les remonter en sprint 5 (avec 2.3) est un coût marginal et débloque aussi des consumers futurs (StoryExport, Stripe). 2-3 ne *peut* être contextée en `ready-for-dev` que si on s'engage à shipper 2.8 et 2.9 en amont OU en parallèle stricte.

**Action à porter en sprint planning** : monter 2-8 et 2-9 de sprint 9 → sprint 5, ou marquer 2.3 comme `blocked-by: 2-8, 2-9` jusqu'à décision.

### 4.1 Machine à états (référence dev)

```
                        ┌─────────────┐
                        │    idle     │ ← état initial (3 cards de choix AC1)
                        └─────────────┘
                            │
                  ┌─────────┼─────────┐
                  ↓         ↓         ↓
              SCAN      MANUEL      PLUS TARD
                │       (Story 2.4)  (Story 2.5)
                ↓
        ┌──────────────┐
        │picking_files │ ← AC2, sheet/dialog ouvert
        └──────────────┘
                │ tap "Lancer l'analyse"
                ↓
        ┌──────────────┐
        │   uploading  │ ← AC3, barre progression par fichier
        └──────────────┘
                │ tous uploads done
                ↓
        ┌──────────────┐
        │  ocr_running │ ← AC4, ScenarioLoader, poll 2s
        └──────────────┘
            │           │           │
            ↓           ↓           ↓
        succeeded    failed     timeout
            │           │           │
            ↓           ↓           ↓
        ┌──────────┐ ┌──────────────────┐
        │recap_edit│ │GracefulFallback  │ ← AC7
        └──────────┘ └──────────────────┘
            │            │       │      │
            │            ↓       ↓      ↓
            │         MANUEL  RETRY  PLUS TARD
            │         (2.4)  (→ idle) (2.5)
            ↓ tous bulletins validés
        ┌──────────┐
        │ validated│ ← redirect /dashboard
        └──────────┘
```

### 4.2 Wireframes ASCII — AC1 (écran d'entrée 3 cards), mobile 375 px

```
┌─────────────────────────────────────────┐
│ <  ● ● ●                                │ ← progress 3/3 actif
├─────────────────────────────────────────┤
│                                          │
│  Tes bulletins, comment tu préfères ?    │
│  3 façons de faire. Aucune n'est mieux   │
│  qu'une autre — choisis selon ton humeur │
│  du moment.                              │
│                                          │
│  ┌─────────────────────────────────────┐│ ← Card xl, h 80+
│  │ 📸  Scanner / importer mes bulletins ││   fond color-bg-2
│  │     Photo ou PDF, on lit pour toi    ││   border color-border
│  │     ~30 secondes                     ││   touch target 80px
│  └─────────────────────────────────────┘│
│                                          │
│  ┌─────────────────────────────────────┐│
│  │ ✍️  Saisir mes notes à la main       ││   STRICT MÊME design
│  │     Formulaire structuré, simple     ││   que la card 1
│  │     ~3 minutes                       ││
│  └─────────────────────────────────────┘│
│                                          │
│  ┌─────────────────────────────────────┐│
│  │ ⏭️  Plus tard, je préfère explorer   ││   STRICT MÊME design
│  │     d'abord                          ││   que les cards 1 et 2
│  │     Tu pourras ajouter à tout moment ││
│  │     Recos un peu plus génériques pour││
│  │     l'instant                        ││
│  └─────────────────────────────────────┘│
│                                          │
└─────────────────────────────────────────┘
```

### 4.3 Wireframes ASCII — AC4 (ScenarioLoader pendant OCR), mobile 375 px

```
┌─────────────────────────────────────────┐
│                                          │ ← header masqué pendant
│                                          │   loading (focus exclusif)
│                                          │
│                                          │
│                                          │
│                                          │
│           ┌──────────────┐               │
│           │              │               │ ← illustration discrète
│           │   📖 ✨      │               │   Lucide icons composés
│           │              │               │   color-text-subtle
│           └──────────────┘               │
│                                          │
│           On lit les notes…              │ ← text-h2 weight 600
│                                          │   transition motion-quick
│                                          │   à chaque ~8 s
│                                          │
│                                          │
│  ▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░  ~25s        │ ← barre 4px h
│                                          │   color-brand, linéaire
│                                          │
│                                          │
│         Estimation : ~25 secondes        │ ← caption color-text-subtle
│                                          │
│                                          │
│                                          │
│  (Après 30s seulement :)                 │
│                                          │
│  ⚠ Ça prend un peu plus de temps que    │ ← banner color-warning
│    prévu, on continue.                   │   apparaît au-delà 30s
│                                          │
│            Saisir à la main plutôt       │ ← tertiary, ouvre Story 2.4
│                                          │   le job OCR continue en bg
│                                          │
└─────────────────────────────────────────┘
```

### 4.4 Wireframes ASCII — AC5 (récap éditable), mobile 375 px

```
┌─────────────────────────────────────────┐
│ <  ● ● ●                                │
├─────────────────────────────────────────┤
│  Voilà ce qu'on a lu                    │
│  Corrige si besoin — on peut se tromper.│
│  Toi seul·e sais ce qui est juste.       │
│                                          │
│  ┌──┬──┬──────────────────────────────┐ │ ← Tabs shadcn
│  │T1│T2│ + Ajouter bulletin           │ │   t1 actif (selected)
│  └──┴──┴──────────────────────────────┘ │   t2 + nouvel onglet
│                                          │
│  Trim. 1 — Terminale [✎]                │ ← label éditable
│  Année 2025-2026                         │ ← detected
│                                          │
│  ⚠ 1 matière à vérifier                 │ ← résumé low-conf, lien
│  Voir →                                  │   tertiary scroll vers
│                                          │
│  Tes matières                            │
│  ┌─────────────────────────────────────┐│
│  │ Mathématiques        14.5 / 20   ✎ 🗑││ ← matière, note, icones
│  │ Excellents efforts ce trimestre,    ││   appréciation tronquée
│  │ continue sur cette lancée…           ││
│  │                                     ││
│  │ ⚠ Sciences Vie Terre  13.2 / 20  ✎ 🗑││ ← icône warning low-conf
│  │ Bon trimestre malgré difficultés    ││
│  │ sur la génétique…                    ││
│  │                                     ││
│  │ HGGSP                15.0 / 20   ✎ 🗑││
│  │ Excellent niveau, élève très        ││
│  │ engagée dans les débats…             ││
│  │                                     ││
│  │ … (8 autres lignes)                 ││
│  └─────────────────────────────────────┘│
│                                          │
│  + Ajouter une matière manquante         │ ← tertiary
│                                          │
├─────────────────────────────────────────┤
│  ┌────────────────────────────────────┐ │
│  │   Valider ce trimestre        →    │ │ ← primary lg
│  └────────────────────────────────────┘ │   passe en "Terminer
└─────────────────────────────────────────┘   l'onboarding" quand
                                              tous trimestres validés
```

### 4.5 Wireframes ASCII — AC7 (GracefulFallback OCR rate), mobile 375 px

```
┌─────────────────────────────────────────┐
│ <  ● ● ●                                │
├─────────────────────────────────────────┤
│                                          │
│           ┌──────────────┐               │
│           │   📄 ?       │               │ ← icône Lucide
│           │              │               │   color-text-muted
│           └──────────────┘               │   PAS rouge alarme
│                                          │
│  Ton bulletin a un format qu'on connaît │
│  pas encore                              │ ← text-h2
│                                          │
│  Pas grave. Saisis-le à la main —       │
│  5 champs et c'est bon. Tu pourras      │
│  retenter avec une photo plus nette si  │
│  tu veux.                                │
│                                          │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │       Saisir à la main         →   │ │ ← primary, weight équiv.
│  └────────────────────────────────────┘ │   au secondary
│                                          │
│  ┌────────────────────────────────────┐ │
│  │  Réessayer avec une autre photo    │ │ ← secondary, weight équiv.
│  └────────────────────────────────────┘ │
│                                          │
│       Plus tard, je préfère explorer    │ ← tertiary
│              d'abord                     │
│                                          │
└─────────────────────────────────────────┘
```

### 4.6 État émotionnel par phase — référentiel copy review

| Phase | État d'entrée probable | Cible émotionnelle | Triggers à bannir |
|---|---|---|---|
| **AC1 3 cards** | Anticipation (Sarah) / Méfiance (Léa) / Curiosité (Mehdi) | Choix libre, équivalence ressentie | "Recommandé", ribbon, comparaison visuelle des cards |
| **AC2 picker** | Friction préemptive ("Va falloir scanner…") | Compétence sentie ("Y'a la caméra direct, sympa") | Modal d'aide avec 5 étapes, formulaire désespéré |
| **AC3 upload** | Patience courte | Maîtrise visuelle (barres avancent) | Spinner nu, pas de progression individuelle |
| **AC4 OCR** | Wait stress mounting | Narration + tendresse système ("on lit pour toi") | Spinner nu, "Patience…", compte à rebours stressant |
| **AC5 recap** | Découverte ("Ah ouais, ils ont vraiment lu mes notes") | Confiance + agentivité (corriger sans pénalité) | "Vérifie attentivement", validation cérémonieuse, lock champs |
| **AC6 low-conf** | Doute ("Ah, il y a des warnings") | Information neutre ("L'OCR a un doute, à toi") | "Erreur de lecture", "Bulletin mal scanné" |
| **AC7 fallback** | Échec ressenti, prêt à fuir | Calme + porte ouverte | "ERREUR", icône rouge, "Tu as fait quelque chose de mal" |

**Test sortie écran** : à la fin de step-3 OCR-réussi, Sarah pense quoi ? Cible : *"Ah ouais, ils ont vraiment lu mes notes en 30 s, c'est solide."* — pas *"J'espère que c'est bien enregistré."*

### 4.7 Anti-patterns proscrits sur cet écran (rappel critique)

- ❌ **Bouton OCR "recommandé"** ou ribbon "Le plus populaire" sur la card AC1 — viole le mode dégradé invisible (Léa stigma)
- ❌ **Spinner nu pendant l'OCR** — utiliser `ScenarioLoader` (Story 2.8), pas un `<Loader />` shadcn nu
- ❌ **Modal d'erreur rouge** sur OCR fail — utiliser `GracefulFallback` (Story 2.9), pas un `<AlertDialog />` rouge
- ❌ **Validation à chaque keystroke** sur la note — validation **on blur** uniquement
- ❌ **Champ note locked** après extraction OCR — toujours éditable jusqu'à validation
- ❌ **"Tu as oublié de corriger X champs"** au clic Valider — toutes corrections optionnelles, validation déclarative
- ❌ **Auto-soumission** au scan terminé sans intervention — l'élève DOIT pouvoir corriger avant de valider
- ❌ **"Profil enrichi à X %"** après validation — anti-progression-anxiogène
- ❌ **Confettis / célébration** à la validation
- ❌ **Toast d'erreur ambient** pour erreur de note (> 20) — inline `color-danger` sous le champ
- ❌ **Bouton "Plus tard" caché** ou minimisé dans header — il EST l'une des 3 cards, parité visuelle stricte

### 4.8 Edge cases et failures explicites

| Edge case | Comportement attendu | AC ref |
|---|---|---|
| Élève iPhone uploade HEIC (format natif Apple) | Conversion auto serveur HEIC → JPEG via libheif avant OCR, transparent pour l'élève | AC2 |
| Élève sélectionne 1 PDF de 12 MB | Refus client-side avec helper inline `color-warning` *"Trop gros : 12 MB, max 10 MB"* ; suggestion *"Compresse ou prends en photo"* | AC2 |
| Élève sélectionne 7 fichiers | Refus client-side du 7e *"Maximum 6 fichiers"* | AC2 |
| Upload du fichier 2/3 timeout après 3 retries | Fichier 2 marqué *"Pas réussi"* ; fichiers 1 et 3 OK ; bouton "Réessayer ce fichier" inline ; possible de continuer avec 1 et 3 seulement | AC3 |
| Réseau coupe pendant upload de tous les fichiers | Tous fichiers échouent retry → page d'erreur globale `GracefulFallback` avec CTA "Réessayer" (revient sur sheet AC2 sélection conservée) + "Saisir à la main" | AC3 |
| OCR job timeout > 60 s côté serveur | Status `timeout` → traité comme `failed` → `GracefulFallback` AC7 | AC4 |
| Réseau coupe pendant poll OCR | Front retry poll avec backoff (2s → 4s → 8s, max 30s), affiche encart subtil *"On essaie de récupérer…"* en `color-text-muted` ; le job continue côté serveur | AC4 |
| Élève quitte l'app pendant OCR puis revient 5 min après | Re-poll status, si `succeeded` → bascule direct sur recap_editing | AC9 |
| OCR succeed mais 0 matière extraite (PDF de mauvais format) | Traité comme `failed` (seuil `< 3 matières extraites`) → `GracefulFallback` | AC7 |
| OCR extrait note > 20 (mauvaise lecture) | Stocké tel quel côté serveur avec `confidence < 0.7` ; côté UI, affiche valeur entre `<` et `>` avec icône warning, validation client refuse > 20 à l'édition (force correction) | AC6 |
| Élève édite note 14.5 → "abc" | Validation blur refuse avec helper inline *"Note entre 0 et 20"* ; valeur précédente restaurée si pas valide | AC5 |
| Élève supprime toutes les matières d'un bulletin | Bouton "Valider ce trimestre" disabled, helper *"Au moins 1 matière requise pour valider ce bulletin"* + lien tertiary *"Supprimer ce bulletin entier"* | AC5 |
| Élève valide 2 trimestres puis quitte avant le 3e | À la reprise, on est sur recap_editing trim 3, trims 1 et 2 marqués validés (tab checkmark) | AC9 |
| Élève change son niveau scolaire en step-2 après avoir validé des bulletins | Bulletins validés conservent leur `level_at_upload` + `subjects_ref_version` (audit longitudinal) ; le récap des bulletins futurs utilisera le nouveau niveau | AC8 |
| Lecteur d'écran sur ScenarioLoader | Annonce chaque phrase de narration, mais pas plus fréquemment que 8 s (anti-saturation SR) | AC10 |
| Reduced motion sur upload progress | Barre passe en mode discret "Envoi en cours…" sans animation | AC10 |
| Élève en mode "Plus tard" clique sur la 3e card | Redirige vers Story 2.5 (`bulletins_status = "postponed"`) ; pas de confirmation supplémentaire | AC1 |
| Élève prend en photo un document QUI N'EST PAS un bulletin (selfie, photo random) | OCR extrait du texte mais 0 matière trouvée par mapping → `GracefulFallback` AC7 | AC7 |
| Élève uploade un PDF avec 3 trimestres dans le même fichier | OCR détecte 3 sections "Trimestre N" → crée 3 onglets bulletin distincts dans le récap (post-traitement smart, à figer en spike T1) | AC5 |

### 4.9 Décisions design verrouillées

- **3 cards visuellement équivalentes** sur AC1 — non négociable. Pas de ribbon, pas de "recommandé", pas de couleur sémantique différente.
- **Pas de bouton "Continuer" en footer AC1** — la card cliquée EST le choix, économie d'un tap.
- **Pas de preview avant upload** — économie de complexité, RGPD friendly (minimisation : on n'upload que ce que l'élève confirme).
- **Indicateur de confiance visuel sur low-conf**, pas de validation forcée — responsabilité user, anti-paternalisme.
- **Données brutes OCR conservées séparément** des corrections — audit longitudinal + amélioration modèle (Story 9.5).
- **Référentiel matières versionné** (`subjects_ref_version`) — parallèle à `level_ref_version` Story 2.2.
- **Job OCR continue côté serveur si élève bascule sur manuel** (AC4) — pas de gaspillage compute, possibilité de merger les deux sources au retour.
- **`GracefulFallback` 2 CTAs équivalents weight** (AC7) — pas de dark pattern poussant vers une option.
- **Tab dans le récap pour multi-bulletins** — préféré à un wizard step-by-step (économie de scroll, comparaison rapide entre trimestres possible).
- **Purge auto 30 j si jamais validé** — RGPD principe limitation conservation. À documenter dans la politique de confidentialité.

### 4.10 Versions et libraries à utiliser

- React 19, Next.js 15, TypeScript 5.x
- shadcn/ui : `Button`, `Card`, `Sheet`, `Dialog`, `Tabs`, `Input`, `Textarea`, `Select`, `Progress`, `Toast`, `Tooltip`, `Skeleton`
- React Hook Form 7.x + Zod 3.x (validation note 0-20, taille fichier, formats)
- TanStack Query 5.x (polling status OCR, mutations upload/finalize)
- XState 5.x **OU** useReducer custom — décision dev, XState recommandé pour la complexité 6 états
- Lucide React (`Camera`, `Folder`, `ArrowRight`, `FileText`, `Image`, `X`, `Pencil`, `Trash`, `AlertTriangle`)
- Backend : Django/DRF ou FastAPI + Celery 5.x + Redis (queue) + pytesseract 0.3.x ou Mindee SDK / boto3 (selon T1) + libheif Python binding (`pillow-heif`)
- Stockage : MinIO 2026.x (PoC) ou AWS S3 EU-WEST-3 (prod) — SSE-S3 minimum
- Vitest + RTL + Playwright + axe-core

### 4.11 Items à différer (`deferred-work.md` post-merge)

- **Re-OCR sur correction massive** — si l'élève corrige > 30 % des champs, proposer re-traitement avec autre provider (fast-follow)
- **Détection auto du type de bulletin** (collège vs lycée vs primaire) — pour valider cohérence avec niveau déclaré step-2 (anti-erreur), fast-follow
- **Multi-bulletins simultanés** dans même PDF (déjà mentionné AC8 edge case) — heuristique sophistiquée à figer en spike, MVP s'en tient à 1 bulletin par fichier
- **Comparaison trimestre à trimestre** (graph d'évolution) — après onboarding, sur page profil, fast-follow Epic 2 Story 2.6
- **OCR offline** (Tesseract.js client-side) — réduit latence + RGPD-friendly, mais coût UI mobile, fast-follow
- **Suggestions auto** d'amélioration de score basées sur appréciations enseignants — Epic 3, pas ici
- **Import direct depuis l'ENT** (Pronote, École Directe, etc.) — V2 partenariat, hors MVP

---

## 5. Project Structure Notes

**Files à créer/modifier (estimation indicative) :**

```
apps/web/
  app/(auth)/onboarding/step-3/
    page.tsx                       ← entrée Next.js, dispatch sur état initial
    OnboardingStep3.tsx            ← orchestrateur machine à états
    ImportChoice3Cards.tsx         ← AC1, factorisable avec Stories 2.4 / 2.5
    FilePickerSheet.tsx            ← AC2
    UploadProgress.tsx             ← AC3
    OCRLoader.tsx                  ← AC4, consomme <ScenarioLoader/> (Story 2.8)
    BulletinRecapEditor.tsx        ← AC5, AC6
    OCRGracefulFallback.tsx        ← AC7, consomme <GracefulFallback/> (Story 2.9)
    useOnboardingStep3.ts          ← state machine + hooks data
    useBulletinUpload.ts
    useOCRJob.ts
    __tests__/
      OnboardingStep3.test.tsx
      FilePickerSheet.test.tsx
      BulletinRecapEditor.test.tsx
      a11y.spec.ts
  e2e/
    onboarding-step3-happy.spec.ts
    onboarding-step3-low-conf.spec.ts
    onboarding-step3-fallback.spec.ts

packages/
  copy/onboarding/
    subjects-by-level.ts           ← référentiel matières par niveau (AC8)
    __tests__/

apps/api/apps/bulletins/             ← nouveau module ou extension /students
  models.py                          ← Bulletin + BulletinOCRJob (T2, T3)
  views_upload.py
  views_ocr.py
  serializers.py
  tasks_ocr.py                       ← Celery task
  providers/
    tesseract.py
    mindee.py                        ← ou textract.py selon T1
    base.py                          ← interface commune OCRProvider
  fuzzy_subject_mapper.py            ← Levenshtein mapping (AC8)
  migrations/
    NNNN_bulletin_models.py
  tests/
    test_upload.py
    test_ocr_tesseract.py
    test_fuzzy_mapping.py
    test_finalize.py
    fixtures/
      bulletin_clean.pdf
      bulletin_blurry.jpg
      bulletin_failed.png
      bulletin_heic.heic
  tasks_purge.py                     ← Celery beat 30j

docs/
  onboarding/step3-bulletins.md     ← documentation flow + state machine (T6)
  spikes/ocr-stack-2026-05.md       ← output spike T1
  a11y/onboarding-step3.md
```

**Conventions à respecter :**

- Tokens CSS uniquement (Story 1.2)
- TanStack Query pour polling OCR + upload (Story 1.3 setup)
- Audit log Story 1.13 sur tous les events bulletin (upload, ocr_succeeded, ocr_failed, finalize, delete)
- RLS Story 1.8 sur Bulletin + BulletinOCRJob
- **Interface commune OCRProvider** (anti-vendor-lock) — facilite swap Tesseract → Mindee/Textract
- **Job Celery idempotent** — relance possible sans corruption (retry-safe)

---

## 6. References

- **UX spec globale** : `_bmad-output/planning-artifacts/ux-design-specification.md`
  - § Experience Principles (#3 anti-impasse, #4 mode normal = mode dégradé)
  - § Form Patterns (multi-step, validation, no-asterisk)
  - § Empty States & Loading States (`ScenarioLoader` > 1s, > 30s estimation)
  - § Feedback Patterns (Error contextuelle vs Error système)
  - § Accessibility Strategy (RGAA AA, tables sémantiques)
  - § Anti-patterns proscrits — récapitulatif global
- **Epic 2 detail** : `_bmad-output/planning-artifacts/epics/epic-2-profil-eleve-onboarding.md` § Story 2.3
- **Stories Epic 2 sœurs** :
  - 2.1 `_bmad-output/implementation-artifacts/2-1-onboarding-passions-interets-valeurs.md`
  - 2.2 `_bmad-output/implementation-artifacts/2-2-onboarding-niveau-filiere-specialites.md`
  - 2.4 (saisie manuelle, à venir) — flux fallback consumé par AC7 / AC4 "Saisir à la main plutôt"
  - 2.5 (Plus tard, à venir) — flux consumé par AC1 card 3 et AC7 link tertiary
  - **2.8 (`ScenarioLoader`, à venir)** — dépendance bloquante (cf §Dependency tradeoff 4.0)
  - **2.9 (`GracefulFallback`, à venir)** — dépendance bloquante
- **Story 1.2 (tokens)** : `_bmad-output/implementation-artifacts/1-2-design-system-tokens.md`
- **Story 1.8 (RLS)** : `_bmad-output/implementation-artifacts/1-8-multi-tenant-rls-postgresql.md`
- **Story 1.13 (audit log)** : `_bmad-output/implementation-artifacts/1-13-journal-audit-acces.md`
- **Story 9.5 (versioning modèles IA)** : pour l'archivage `raw_extraction` + `confidence_avg` + `provider_version` — utile audit longitudinal
- **PRD** :
  - FR14 (import bulletins OCR) : `_bmad-output/planning-artifacts/prd/functional-requirements.md#fr14`
  - NFR-P4 (OCR < 30s P95) : `_bmad-output/planning-artifacts/prd/non-functional-requirements.md#nfr-p4`
  - NFR-R4 (graceful degradation OCR → manuel) : idem
- **Direction visuelle / UX** : § Direction Decision C "L'Atelier" — narratif sur moments structurants (cet écran est *le* moment structurant onboarding), dense sur fonctionnel (le récap matières est dense Doctolib-like)

---

## 7. Dev Agent Record

### Agent Model Used
Claude Sonnet 4.6 (claude-sonnet-4-6)

### Debug Log References
- Edit tool "file not read" error on events.ts — fixed by reading file first before editing
- Dependency HALT on pytesseract/pillow-heif/python-Levenshtein/XState — user approved all

### Completion Notes List
- T1: Spike doc créé `docs/spikes/ocr-stack-2026-05.md` — décision: Tesseract 5.x MVP, Mindee post-MVP si error rate > 15%
- T2: Modèle Bulletin + migration + endpoint upload + S3 + serializers créés
- T3: BulletinOCRJob + TesseractProvider + fuzzy mapper + Celery tasks (ocr_extract + purge) + endpoints status/finalize
- T4: XState v5 machine (7 états) + 6 composants frontend + 2 hooks + page Next.js
- T5: Tests pytest (upload/ocr/fuzzy/purge) + Vitest (3cards/upload-progress/recap-editor/graceful-fallback/ocr-loader) + Playwright E2E (Sarah/Mehdi/Léa)
- T6: `docs/onboarding/step3-bulletins.md` + `docs/a11y/onboarding-step3.md`
- Tous les ACs satisfaits (AC1-AC10)

### File List
- `apps/api/apps/bulletins/models.py` (créé)
- `apps/api/apps/bulletins/providers/base.py` (créé)
- `apps/api/apps/bulletins/providers/tesseract.py` (créé)
- `apps/api/apps/bulletins/fuzzy_subject_mapper.py` (créé)
- `apps/api/apps/bulletins/tasks_ocr.py` (créé)
- `apps/api/apps/bulletins/tasks_purge.py` (créé)
- `apps/api/apps/bulletins/serializers.py` (créé)
- `apps/api/apps/bulletins/views.py` (créé)
- `apps/api/apps/bulletins/urls.py` (créé)
- `apps/api/apps/bulletins/migrations/0001_initial.py` (créé)
- `apps/api/apps/bulletins/tests/__init__.py` (créé)
- `apps/api/apps/bulletins/tests/test_upload.py` (créé)
- `apps/api/apps/bulletins/tests/test_ocr.py` (créé)
- `apps/api/apps/bulletins/tests/test_fuzzy_mapper.py` (créé)
- `apps/api/apps/bulletins/tests/test_purge.py` (créé)
- `apps/api/path_advisor/settings/base.py` (modifié — INSTALLED_APPS + BULLETINS_BUCKET)
- `apps/api/path_advisor/urls.py` (modifié — include bulletins.urls)
- `apps/api/pyproject.toml` (modifié — pytesseract, pillow-heif, python-Levenshtein)
- `apps/web/package.json` (modifié — xstate, @xstate/react)
- `apps/web/src/lib/analytics/events.ts` (modifié — 6 événements step-3)
- `apps/web/src/components/features/onboarding/step-3/onboarding-step3-machine.ts` (créé)
- `apps/web/src/hooks/use-ocr-job.ts` (créé)
- `apps/web/src/hooks/use-bulletin-upload.ts` (créé)
- `apps/web/src/components/features/onboarding/step-3/import-choice-3-cards.tsx` (créé)
- `apps/web/src/components/features/onboarding/step-3/file-picker-sheet.tsx` (créé)
- `apps/web/src/components/features/onboarding/step-3/upload-progress.tsx` (créé)
- `apps/web/src/components/features/onboarding/step-3/bulletin-recap-editor.tsx` (créé)
- `apps/web/src/components/features/onboarding/step-3/ocr-loader.tsx` (créé)
- `apps/web/src/components/features/onboarding/step-3/ocr-graceful-fallback.tsx` (créé)
- `apps/web/src/components/features/onboarding/step-3/onboarding-step3.tsx` (créé)
- `apps/web/src/app/(authenticated)/onboarding/step-3/page.tsx` (créé)
- `apps/web/src/components/features/onboarding/step-3/__tests__/import-choice-3-cards.test.tsx` (créé)
- `apps/web/src/components/features/onboarding/step-3/__tests__/upload-progress.test.tsx` (créé)
- `apps/web/src/components/features/onboarding/step-3/__tests__/bulletin-recap-editor.test.tsx` (créé)
- `apps/web/src/components/features/onboarding/step-3/__tests__/ocr-graceful-fallback.test.tsx` (créé)
- `apps/web/src/components/features/onboarding/step-3/__tests__/ocr-loader.test.tsx` (créé)
- `apps/web/e2e/onboarding/step3-bulletins.spec.ts` (créé)
- `docs/spikes/ocr-stack-2026-05.md` (créé)
- `docs/onboarding/step3-bulletins.md` (créé)
- `docs/a11y/onboarding-step3.md` (créé)

### Change Log

- 2026-06-19 — Implémentation complète Story 2.3 par Claude Sonnet 4.6. T1-T6 réalisés. Status → review.
- 2026-05-24 — Story 2.3 contextée et passée en `ready-for-dev` par Marwen + Claude (Opus 4.7) dans le cadre du démarrage parallèle UX Epic 2 pendant que Epic 1 finit. **Dépendance critique** : Stories 2.8 (`ScenarioLoader`) et 2.9 (`GracefulFallback`) doivent être planifiées soit en amont du sprint de 2.3, soit en parallèle stricte avec consigne de refacto avant merge (cf §Dependency tradeoff 4.0).
