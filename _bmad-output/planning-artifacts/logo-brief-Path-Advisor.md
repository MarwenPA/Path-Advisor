---
title: "Brief logo : Path-Advisor"
status: "draft"
created: "2026-10-12"
inputs: ["product-brief-Path-Advisor.md", "ux-design-specification.md"]
---

# Brief logo — Path-Advisor

## Contexte produit

Path-Advisor est une plateforme d'orientation continue pour lycéens francophones (3ème → bac+2/3). Elle combine un moteur vocationnel (quel métier me correspond) et un moteur de parcours (comment y arriver), à partir de données scolaires objectives plutôt que de questionnaires déclaratifs.

Différenciation centrale face aux concurrents (Diplomeo, L'Étudiant, Onisep, Diagoriente) : **neutralité commerciale**. Path-Advisor ne revend pas de leads aux écoles. Cette neutralité doit se voir dans l'identité visuelle, pas seulement s'affirmer dans le discours.

Utilisateur protagoniste : Sarah, lycéenne en Terminale, sous pression Parcoursup. Le produit doit lui donner un **récit défendable**, pas un verdict — ton grand frère/grande sœur de confiance, jamais un coach ou un vendeur.

## Ce qui est déjà acté (non négociable)

Issu de `ux-design-specification.md`, direction visuelle **R1 — Vermillon sobre + blanc cassé**, déjà validée pour le produit. Le logo doit s'inscrire dans ce système, pas en créer un nouveau.

**Couleurs :**

| Rôle | Valeur |
|---|---|
| Brand (rouge) | `#C8312D` |
| Brand hover | `#A6231F` |
| Fond principal | `#FAFAF7` (blanc cassé chaud) |
| Fond carte | `#F4F1ED` (ivoire) |
| Texte principal | `#1A1A1A` (near-black) |
| Texte atténué | `#666660` |
| Bordures | `#E0DDD8` |

**Règle du rouge — la plus importante du brief** : le rouge est *rare et chirurgical*. Il apparaît sur le logo, le CTA primaire, les états de focus — jamais en surface étendue, jamais dominant. Un logo tout rouge, ou avec plusieurs éléments rouges, viole la règle de marque.

**Typographie :** Inter (variable), graisse 600 (Semi Bold) pour le poids de marque. Pas de police dédiée au logo — c'est délibéré, le produit n'a pas de budget de différenciation typographique en MVP.

**Mode clair uniquement.** Le produit n'a pas de dark mode en MVP, mais le logo doit rester lisible sur fond sombre (réseaux sociaux, avatar) — prévoir une déclinaison inversée.

## Clichés à bannir explicitement

Ce ne sont pas des préférences esthétiques, ce sont des interdits de marque actés dans le produit (`ux-design-specification.md`, anti-patterns UX étendus au logo) :

- **Bonnet de diplômé, toque, diplôme encadré** — iconographie EdTech générique, Onisep/Studyrama.
- **Stylo rouge de correction, surligneur** — connote la notation scolaire, le jugement. Évoqué nommément dans la spec produit comme piège à éviter.
- **Boussole, flèche compass-style** — cliché "orientation" trop lu, dit rien de spécifique à Path-Advisor.
- **Dégradé violet/bleu, forme organique "blob"** — esthétique startup générique, ne dit rien de la neutralité ou de la sobriété du produit.
- **Mascotte, personnage, visage souriant** — incompatible avec le ton "grand frère de confiance", pas un coach enjoué.
- **Tout logo où le rouge domine une surface** — viole la règle de marque ci-dessus.

## Le concept central : chemin → destination

Le produit a déjà une grammaire visuelle propre, définie dans la spec UX pour l'écran "graphe-récit" (la vue qui s'affiche quand un lycéen ouvre un métier recommandé) : **des étapes qui mènent à une destination**, jamais un pourcentage brut, jamais un verdict. Lycée → étape intermédiaire → école cible, avec la destination seule marquée en rouge.

Le logo devrait réutiliser ce même langage plutôt qu'inventer un symbole déconnecté du produit — c'est littéralement l'objet que l'utilisateur voit à l'écran après son premier métier ouvert. Verbe produit central : **"voir ton chemin et tes chances"**.

## Pistes explorées (pour inspiration, aucune n'est validée)

Quatre variations autour du même concept ont été esquissées en interne — à prendre comme point de départ, pas comme livrable fini :

**A — L'ascension fluide.** Une courbe continue (pas des segments droits cassés) reliant un point de départ, une étape intermédiaire, et une destination marquée d'un point plein rouge. Lecture "parcours en plusieurs étapes".

**B — Le geste minimal.** Seulement deux points : départ discret (petit point sombre), arrivée marquée (point rouge plus large). Plus sobre que A, plus robuste à très petite taille (favicon 16-24px) — moins d'éléments à dégrader.

**C — Lockup empilé.** Reprend le mark de A ou B, mais en tuile carrée au-dessus du nom plutôt qu'à côté — nécessaire pour les formats carrés (icône d'app, avatar Slack/réseaux sociaux, favicon).

**D — Mark seul.** N'importe laquelle des pistes ci-dessus, testée sans le texte "Path-Advisor" à côté — c'est ce qui apparaît dans un onglet de navigateur ou un avatar rond, le texte n'y a pas sa place.

**Constat du travail d'exploration** : la piste B (deux points, geste minimal) a mieux résisté au test de petite taille que A. Les tentatives d'ajouter de la profondeur (halo semi-transparent, reflet, ombre portée) sur le nœud de destination n'ont apporté aucune amélioration visible et ont été abandonnées — à ne pas reproduire.

## Contraintes techniques pour le livrable

- **Format vectoriel (SVG)**, pas de raster.
- **Lisible à 24px** (favicon) et à 96px+ (avatar, header produit) — tester les deux tailles avant de livrer.
- **Lockup horizontal** (icône + "Path-Advisor") pour le header du produit, **et** version icône seule pour favicon/avatar.
- **Déclinaison fond clair (`#FAFAF7`) et fond sombre (`#1A1A1A` ou proche)** — le rouge reste identique dans les deux cas, seuls le texte et les traits s'inversent.
- Le nom du produit s'écrit **"Path-Advisor"** avec trait d'union — ne pas le retirer, ne pas le remplacer par un point médian ou une espace.
- Pas plus d'une seule occurrence de rouge dans l'ensemble du lockup (une touche sur l'icône, éventuellement une touche sur le trait d'union du wordmark — pas les deux à pleine saturation en même temps si ça charge visuellement la composition).

## Ce qu'on attend de Claude Design

Explorer 2-3 directions distinctes autour du concept "chemin → destination" dans le système de marque décrit ci-dessus (couleurs, typo, règle du rouge, mode clair/sombre), en évitant les clichés listés plus haut. Livrer en SVG : lockup horizontal, icône seule, déclinaison fond sombre. Ne pas proposer de variante où le rouge domine une surface, ni de mascotte, ni d'iconographie scolaire générique (diplôme, stylo, boussole).
