---
title: "Product Ideas Backlog — Path-Advisor"
status: "living document"
created: "2026-05-13"
purpose: "Parking lot pour idées produit qui surgissent hors du workflow PRD/UX en cours. À ré-arbitrer à la prochaine itération PRD."
---

# Product Ideas Backlog — Path-Advisor

Idées produit captées en cours de workflow UX, à ré-arbitrer plus tard pour intégration au PRD (fast-follow, V2, ou rejet motivé).

Statuts possibles :

- 🟢 **À porter au PRD MVP** — décision prise, à intégrer au prochain refresh PRD
- 🟡 **Fast-follow** — post-MVP immédiat (mois 9-12)
- 🔵 **V2 / Growth** — à évaluer en phase croissance
- 🔴 **Danger zone** — idée intéressante mais avec risque structurel à designer avant validation
- ⏸️ **Parked** — à ré-arbitrer plus tard avec plus d'éléments

---

## Idée #1 — Moteur inverse : "Je vise déjà X, quelle est ma proba ?"

**Statut :** 🟢 À porter au PRD MVP (proposition forte)
**Source :** Conversation UX 2026-05-13 (Step 4)

### Description

Compléter le moteur forward (signaux → métiers proposés) par un **moteur inverse** : l'élève déclare un métier visé, le produit retourne :

- Une probabilité de faisabilité conditionnée sur le profil actuel
- Le ou les parcours scolaires concrets pour y arriver
- Les écoles cibles avec stats d'admission personnalisées
- Les écarts éventuels à combler (matières, expériences)

### Justification

Cas d'usage réel et fréquent. Sarah rêve médecine, Mehdi vise mécanicien aéronautique — ils n'ont pas besoin qu'on leur *propose* un métier, ils ont besoin qu'on leur dise *combien c'est faisable et par quel chemin*.

Atouts :

- Moins paternaliste que la reco proposée — "je déclare mon ambition, tu me confrontes au réel"
- Réutilise la même donnée et le même moteur de scoring, sens inverse
- Sert directement le **job narratif-défensif** (John, party Step 2) : permet à Sarah de défendre un choix qu'elle a *déjà fait* avec des données

### Impact UX (à porter)

- **Architecture d'information** : entrée alternative dans l'onboarding ("je sais déjà ce que je veux faire" vs "j'explore"). Décision à prendre en Step 7+ du workflow UX en cours.
- **Wording produit** : tonalité différente — *confronter une ambition au réel* vs *aider à découvrir*
- **Affichage** : la probabilité métier devient un export first-class, aux côtés de la probabilité école

### Questions ouvertes

- Faut-il deux flows d'onboarding distincts ou un seul flow qui branche après les premiers signaux ?
- Comment gérer le cas où l'élève vise un métier hors du référentiel (50 métiers MVP) ?
- Est-ce qu'on désigne ça comme deux *modes* (Explorer / Confronter) ou comme deux *outils* dans un même produit ?

---

## Idée #2 — Probabilité d'admission par école comme export first-class

**Statut :** 🟡 Fast-follow UX (couvert techniquement par PRD FR29, mais à promouvoir au niveau UX)
**Source :** Conversation UX 2026-05-13 (Step 4)

### Description

La statistique d'admission personnalisée par école (déjà prévue PRD FR29) doit devenir un **artefact partageable autonome**, pas seulement un nœud du graphe de parcours.

Exemple visuel cible : une carte exportable *"Ma proba à Polytech Marseille : 38 % — pari audacieux"* avec :

- Le pourcentage et son cadrage qualitatif (audacieux / réaliste / sûr)
- La phrase recopiable défendable ("Avec ton profil scolaire et tes spés, tu es dans la zone d'admission")
- Les leviers d'action ("+ 2 points en maths → 58 %")

### Justification

Dovetail parfait avec le **job narratif-défensif** identifié par John : la munition que Sarah recopie dans WhatsApp pour défendre son choix à sa mère, à sa prof principale, à son groupe.

C'est aussi la **forme la plus virale** du produit — une capture d'écran d'une carte de proba école est partageable sans légende.

### Impact UX (à porter)

- À designer en Step 11 (Component Strategy) comme un **composant cartouche** autonome
- À porter en Step 10 (User Journeys) comme un **artefact d'export** des trois types (story ado, résumé parent, fiche conseillère)

### Questions ouvertes

- Sur quelles écoles autorise-t-on cet export ? Toutes (risque de spam d'écoles affichées) ou top 5 du parcours actif ?
- Quel cadrage qualitatif quand la proba est très basse (5 %) — comment ne pas humilier ?

---

## Idée #3 — Recommandation de soutien scolaire si gap matière (Acadomia, etc.)

**Statut :** 🔴 Danger zone — idée à fort potentiel mais avec risque structurel
**Source :** Conversation UX 2026-05-13 (Step 4)

### Description

Quand le profil scolaire de l'élève montre un gap dans une matière critique pour le métier ou l'école visée, recommander des ressources de soutien — gratuites (Khan Academy, Lumni…) et/ou payantes (Acadomia, Superprof, GoStudent…).

### Risque structurel à designer avant validation

**Le piège central : violation potentielle de la promesse de neutralité commerciale.**

Path-Advisor a fondé son USP sur "aucune revente de leads, aucune école ne nous paie pour t'apparaître". Pousser Acadomia ou tout autre fournisseur payant = revendre des leads à un prestataire tiers. **C'est structurellement le modèle Diplomeo que le PRD identifie comme contre-modèle.**

Si exécuté naïvement → la promesse de neutralité s'effondre, la différenciation produit avec elle.

**Risque émotionnel transversal** : pour Mehdi / Léa (Témoins UX), "tu n'as pas le niveau, paie un prof" peut devenir un **message de stratification sociale** ("le système te dit que t'es pas assez bon, sors le chéquier"). À designer avec rigueur de dignité — sinon stigmate.

### Trois pistes pour sauver l'idée

| Piste | Description | Risque résiduel | Recommandation |
|---|---|---|---|
| **A. Diagnostic seul, sans fournisseur** | Montrer le gap et son impact ("12 en maths → 38 % à Polytech ; 14 en maths → 58 %"). Aucune reco de fournisseur. | Neutralité préservée. "Moins utile" mais déjà énorme valeur ajoutée. | ✅ **MVP** |
| **B. Marketplace ouvert et transparent** | Lister *toutes* les ressources (gratuites + payantes) avec leurs prix, sans favoritisme. Aucune commission par défaut. | Faisable, demande un référentiel curé. Neutralité tenue si exécution propre. | 🟡 Fast-follow / V2 |
| **C. Partenariat commercial assumé** | Annoncer publiquement le partenariat, montrer la commission, donner le choix de désactiver. | Honnête mais affaiblit la promesse de neutralité — argument commercial difficile à tenir. | 🔵 V2 sous conditions strictes |

### Décision provisoire (à valider)

- **MVP : piste A uniquement** (diagnostic gap sans recommandation de fournisseur)
- **Fast-follow : piste B** (marketplace transparent, commission nulle ou symbolique, sans favoritisme)
- **V2 / Growth : piste C uniquement si** la marque a établi sa neutralité par d'autres preuves auditables (audit externe, publication des méthodologies, etc.)

### Questions ouvertes

- Comment afficher un gap matière sans démoraliser ni stigmatiser ?
- À partir de quel niveau de gap on déclenche l'affichage (sinon on bombarde Mehdi de signaux d'insuffisance) ?
- Quel partenariat associatif est possible pour offrir du soutien *gratuit* aux profils défavorisés (mitigation du risque inégalité Sarah-first identifié par Sally) ?

---

## Idée #4 — Dark mode

**Statut :** 🟡 Fast-follow post-MVP
**Source :** Décision Marwen post-workflow UX 2026-05-13

### Description

Mode sombre de l'interface, complémentaire au mode clair actuel (palette R1 Vermillon sobre + blanc cassé).

### Justification du report

- **Économie solo founder** : maintenir un design system parallèle (light + dark) double la charge de design, de tests visuels et de revue d'accessibilité sur chaque composant Couche 3
- **MVP focus** : la priorité est de livrer un produit lisible et accessible en mode clair, validé en user testing, avant d'investir sur une variante visuelle
- **Pas une exigence légale** : aucune obligation RGAA / RGPD ne requiert un mode sombre
- **Pattern reportable** : l'adoption shadcn/CSS-vars rend l'ajout futur du dark mode relativement peu coûteux (créer un set de tokens parallèle, basculement via `prefers-color-scheme` + override manuel)

### Conditions de réintroduction

- Après PMF MVP (≥ 500 MAU stables) — signal que le produit core fonctionne
- Avant la fin de la phase Growth (24 mois) — surtout si Mehdi-type users (mobile bas-de-gamme le soir, batterie limitée) remontent une demande terrain

### Effort estimé

- 2-3 sprints : audit visuel parallèle de tous les composants + création des tokens dark + tests cross-mode
- Composants `GraphParcours` et `StoryExport` demanderont une attention particulière (gradients, ombres, semantique couleur)

### Questions ouvertes

- Variantes spécifiques nécessaires : OLED-friendly true black ou charcoal doux ?
- Comportement du re-rendu `StoryExport` PNG : forcer mode clair (le destinataire est en mode clair par défaut sur sa galerie), ou adapter ?
- Test du téléphone fissuré (Step 13) en mode sombre : tient-il sur OLED vieillissant ?

---

## Process de revue

Ce backlog est ré-arbitré à chaque refresh PRD ou en début de phase Growth. À chaque revue :

1. Vérifier que les statuts sont toujours valides
2. Promouvoir au PRD les idées 🟢 décidées
3. Re-prioriser les 🟡 fast-follow par rapport au backlog produit
4. Documenter les nouvelles questions ouvertes
