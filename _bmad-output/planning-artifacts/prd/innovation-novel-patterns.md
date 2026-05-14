# Innovation & Novel Patterns

## Detected Innovation Areas

**1. Architecture en double moteur articulé**

Le cœur d'innovation de Path-Advisor n'est pas l'existence séparée de recommandation vocationnelle (RIASEC depuis les années 1970) ni de recommandation de parcours (sites de comparaison d'écoles depuis 2000). C'est l'**articulation produit** des deux dans une expérience continue :

> Profil → recommandation vocationnelle → sélection d'un métier → recommandation de parcours scolaires → stats d'admission par école → action (candidature, envoi anticipé)

Aucun acteur ne livre aujourd'hui ce flux complet dans un seul produit. Onisep s'arrête au métier (et donne des fiches statiques). Diplomeo commence à l'école (sans contexte vocationnel). Parcoursup gère la candidature (sans conseil amont). Path-Advisor est le premier à traiter le flux *bout en bout*.

**2. Donnée scolaire objective comme moteur principal de personnalisation**

Tous les outils d'orientation existants (Onisep, Diagoriente, les tests métier MOOC) reposent sur du **déclaratif pur** : l'élève répond à des questionnaires (RIASEC, intérêts, valeurs). Path-Advisor croise ce déclaratif avec des **données scolaires objectives** : bulletins, notes, appréciations enseignants. Cela permet :

- de pondérer le déclaratif par la réalité scolaire (l'élève qui *dit* aimer les maths mais qui a 8/20 doit voir ses recommandations ajustées)
- de calculer des **statistiques d'admission personnalisées** pour chaque école cible (impossible sans le profil scolaire réel)
- de créer un avantage défensif structurel : l'élève ne peut pas reconstruire ce profil sur une plateforme concurrente sans réimporter ses bulletins

C'est cette objectivité qui rend les recommandations crédibles et le scoring auditable.

**3. Envoi anticipé du profil aux écoles — biface assumé**

L'idée du *"profil envoyé en avance de phase à une école pour augmenter les chances d'admission"* est une nouveauté de marché. Aucun équivalent en orientation post-bac francophone. Le pattern le plus proche conceptuellement vient du recrutement professionnel (LinkedIn Recruiter, Welcome to the Jungle) où le candidat envoie un profil à des employeurs avant un job ouvert. Path-Advisor importe cette mécanique dans le domaine scolaire.

Innovation produit : la **réponse de l'école** (intéressant / non aligné / RDV) devient un signal qui **modifie en temps réel la statistique d'admission** affichée à l'élève. Le profil n'est plus statique — il vit, il interagit, il se déplace.

Innovation business : Path-Advisor crée un **marketplace biface** sans tomber dans le piège du "lead seller" (cf. Diplomeo). L'école *ne paie pas* pour mieux apparaître ; elle paie (en growth) pour répondre à un volume plus large de profils qualifiés. C'est l'élève qui choisit où envoyer, pas un algorithme orienté revenus.

**4. Continuité temporelle "compagnon" 3ème → bac+2/3**

La pratique de marché actuelle traite l'orientation comme un **événement ponctuel** centré sur Parcoursup en Terminale. Path-Advisor adopte le pattern *"compagnon continu"* qu'on retrouve dans la santé (apps de fitness/sommeil), la finance personnelle (Linxo, YNAB), ou l'apprentissage des langues (Duolingo). Le profil évolue, les recommandations s'adaptent, la plateforme apprend de l'élève au fil des années.

C'est un **engagement model** rare en EdTech orientation, et il transforme l'économie : LTV étalée sur plusieurs années plutôt qu'un pic d'usage de 3 mois.

**5. Explicabilité IA en première intention (pas en option)**

Là où la plupart des produits IA grand public traitent l'explicabilité comme une feature avancée ou une exigence légale subie, Path-Advisor en fait un **élément central de l'UX** : chaque score est accompagné d'une visualisation "voici les signaux qui ont fait monter ce métier". Cette transparence est :

- une obligation RGPD (art. 22 sur les décisions automatisées)
- un avantage produit (la confiance vient de la compréhension, pas du marketing)
- un différenciateur vs. les outils déclaratifs opaques

**6. Architecture IA hybride — recommandation statistique + deep learning**

Path-Advisor est nativement un produit *AI-first*, pas un produit "avec une couche IA en option". Le moteur de recommandation est conçu comme une **architecture hybride** combinant deux approches complémentaires :

**a) Moteur de recommandation statistique** (filtrage collaboratif + content-based + facteurs explicites)
- Scoring vocationnel basé sur des features structurées : notes, appréciations enseignants (NLP), passions déclarées, valeurs, type d'établissement, parcours académique
- Filtrage collaboratif sur les cohortes : *"des élèves au profil similaire ont aussi exploré ces métiers / ont effectivement intégré ces écoles"*
- Explicabilité native par construction (poids des features visibles → respect RGPD art. 22)
- Adapté au MVP : pas besoin de gros volumes de données pour démarrer (cold-start gérable via le content-based)

**b) Moteur de deep learning** (modèles de représentation et prédiction d'admission)
- **Embeddings** des profils élèves et des couples métier/formation pour capturer des similarités non triviales (un élève passionné de jeux vidéo + bon en maths peut matcher avec "ingénieur en game design" sans qu'aucune feature explicite ne le code)
- **Modèles prédictifs d'admission** : probabilité d'admission par école cible, conditionnée sur le profil scolaire + historique des admissions
- **NLP sur appréciations enseignants** : transformer les phrases libres ("élève sérieux, manque de confiance", "très créatif mais inégal") en signaux exploitables
- Modèles versionnés avec dataset d'entraînement traçable + audit de biais régulier

**Architecture combinée :** le moteur statistique produit des recommandations explicables servies en premier (transparence, confiance, conformité). Le deep learning enrichit les recommandations avec des cas que les règles manquent + alimente le scoring d'admission. L'utilisateur voit toujours une explication structurée ; le DL fonctionne en *renforcement*, pas en remplacement.

**Pourquoi cette architecture maintenant :**
- **Maturité de l'IA grand public** rend acceptable et attendu d'avoir un produit IA en EdTech (le scepticisme post-LLM est plus faible qu'il y a 5 ans)
- **Volume de données scolaires** suffisant en open data (Parcoursup, ONISEP) pour entraîner les premiers modèles d'admission
- **Coût d'inférence** abordable : les modèles peuvent tourner sur de l'infrastructure cloud standard, pas besoin de GPU dédié pour le scoring d'un élève

## Market Context & Competitive Landscape

| Acteur | Couverture | Modèle | Faiblesse |
|---|---|---|---|
| **Onisep** | Information générique métiers + formations | Public, gratuit | Aucune personnalisation, contenu statique, format vieillissant |
| **Diagoriente** | Questionnaire compétences + recommandation métier | Public, gratuit | Pas de parcours scolaire, pas de stats d'admission, profil purement déclaratif |
| **Parcoursup** | Candidature post-bac | Public, obligatoire | Outil de candidature, pas de conseil amont |
| **Diplomeo** | Annuaire formations + mise en relation école | Privé, **lead seller** | Conflit d'intérêt structurel, pas de moteur vocationnel, pas de scoring objectif |
| **L'Étudiant / Studyrama** | Annuaire formations + classements | Privé, publicitaire | Snapshot statique, pas de personnalisation par profil scolaire |
| **MyJobGlasses, Mentor Goal** | Mise en relation lycéen ↔ professionnel | Privé, freemium | Mentorat ponctuel, pas de recommandation, pas de parcours |
| **Inspire (ex-Frateli)** | Mentorat orientation pour boursiers | Associatif | Niche, sans technologie de reco |

**Position unique de Path-Advisor :** seul acteur combinant (a) moteur vocationnel + (b) moteur parcours + (c) données scolaires objectives + (d) neutralité commerciale + (e) continuité temporelle + (f) feature levier d'admission + (g) architecture IA hybride. Chacun pris isolément existe ailleurs ; la combinaison est inédite en francophonie.

**Veille à exercer :**
- **Aux États-Unis** : Niche.com (data-driven choix d'université), Naviance/Cialfo (B2B high schools), CommonApp — pas d'équivalent francophone des moteurs vocationnels intégrés
- **France** : surveiller émergence d'acteurs IA grand public sur l'orientation (les LLMs grand public commencent à être utilisés comme conseillers d'orientation par les élèves → risque de désintermédiation si Path-Advisor n'apporte pas plus que ChatGPT + un PDF Onisep)

## Validation Approach

**Phase 1 — Validation différenciateur sur le MVP (mois 0-6) :**

- **Test du double moment "aha"** : enquête utilisateurs sur 50 lycéens avant lancement public, mesurer le taux d'élèves qui rapportent une découverte significative (métier ou parcours inconnu) après usage
- **Test de fiabilité du scoring vocationnel** : panel test avec 20 lycéens ayant un projet d'orientation déjà clair → la reco top-3 du moteur inclut-elle leur projet déclaré ? Cible : ≥ 80 %
- **Test des modèles de recommandation** : benchmark sur dataset annoté (profils + métiers cibles validés humainement) → cible précision top-5 ≥ 75 % en MVP
- **Audit de biais ML initial** : test du modèle sur sous-populations (genre, type d'établissement, code postal) → écart inter-groupes < 10 % avant mise en production
- **Test de la valeur perçue des stats d'admission** : A/B test sur l'affichage avec/sans stats personnalisées → mesure d'engagement (consultation graphe complet, retour à 7j)

**Phase 2 — Validation business sur 6-12 mois :**

- **Conversion premium** : 5 % cible (modèle bouche-à-oreille + parents). Si < 2 %, repenser la proposition de valeur premium
- **Conversion B2B pilote → payant** : 3 sur 5 cible. Si < 2, ajuster soit le dashboard conseiller, soit le pricing, soit le pitch
- **Adoption "envoi anticipé"** : % d'utilisateurs premium qui activent au moins 1 envoi. Cible : 60 %. Si faible, la feature premium ne justifie pas le prix

**Phase 3 — Validation impact (mois 12-24) :**

- **Taux d'admission effectif** dans les écoles recommandées (suivi cohorte post-Parcoursup, données déclaratives)
- **Réduction de la réorientation à 1 an** : comparer les cohortes utilisateurs vs population générale (20 % de réorientation en licence en France) — cible : -5 points

## Risk Mitigation (innovation-specific)

| Risque innovation | Mitigation |
|---|---|
| **Le double moteur n'est pas perçu comme une innovation par l'élève** (il voit "encore un test métier") | Onboarding qui scénarise les deux aha moments, copywriting explicite sur l'enchaînement, démos visuelles avant inscription |
| **Les stats d'admission sont fausses ou peu fiables** (modèle prédictif insuffisant) | MVP basé sur données publiques agrégées (Parcoursup open data) ; modèle prédictif personnalisé en growth seulement, avec fourchettes d'incertitude |
| **L'envoi anticipé échoue à attirer les écoles** (pas assez de profils, pas assez de volume) | Bundle B2B pilote + envoi anticipé : les 5 écoles pilotes B2B sont aussi les premières écoles partenaires côté envoi anticipé → garantie de volume initial |
| **Désintermédiation par LLMs grand public** (l'élève va sur ChatGPT) | Différenciation par la donnée scolaire intégrée (un LLM grand public n'a pas accès aux bulletins) + référentiel curé + neutralité auditée |
| **Pression réglementaire sur les décisions automatisées en éducation** (CNIL, MENJS, AI Act UE) | Mise en conformité RGPD art. 22 + AI Act dès le MVP (explicabilité, opt-out, revue humaine), positionnement éthique défendable |
| **Effet réseau biface lent à démarrer côté écoles** (peu d'écoles → faible valeur envoi anticipé → peu de premium) | Démarrage régional ciblé (ex. Île-de-France ou Auvergne-Rhône-Alpes) pour atteindre une densité d'écoles partenaires localement avant d'étendre |
| **Drift des modèles ML** (la pertinence se dégrade avec le temps : nouveaux métiers, évolution des formations, changements Parcoursup) | Pipeline de réentraînement régulier (tous les 6 mois ou trigger statistique sur métriques de qualité), monitoring de la distribution des prédictions en production |
| **Hallucination ou recommandation aberrante** (métier inadapté, école inexistante, stat d'admission grotesque) | Garde-fous post-modèle : règles métier en sortie (vérification cohérence prérequis métier ↔ profil), liste blanche du référentiel curé, seuil de confiance minimum sous lequel on n'affiche pas la reco |
