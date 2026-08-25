"""Extension snippets for seed entries whose description or daily_routine are below AC3 minimums.

Applied by seed_professions.py before creating Profession objects.
"""

# Maps slug → text appended to description if < 100 words
DESCRIPTION_EXTENSIONS: dict[str, str] = {
    "kinesitherapeute": (
        " Avec l'expérience, tu peux te lancer en libéral et organiser ton activité "
        "en toute autonomie, en choisissant tes horaires et ta clientèle."
    ),
    "pharmacien": (
        " La pharmacie est aussi un lieu de prévention et d'éducation à la santé : tu "
        "conseilles sur les dépistages, les vaccinations et les risques d'automédication. "
        "C'est un métier en constante évolution avec le numérique et la télémédecine."
    ),
    "educateur-specialise": (
        " Tu construis des projets individualisés pour chaque personne accompagnée, "
        "en mobilisant les ressources du territoire (associations, services sociaux, "
        "formations). Le réseau de partenaires est essentiel pour une insertion réussie."
    ),
    "coiffeur": (
        " La coiffure est aussi un métier d'écoute et de confiance : de nombreux clients "
        "reviennent toujours au même·à la même coiffeur·euse pendant des années."
    ),
    "data-scientist": (
        " La veille technologique est permanente : les outils et techniques évoluent vite "
        "et les meilleurs data scientists passent du temps à apprendre en dehors du bureau."
    ),
    "developpeur-web-fullstack": (
        " De nombreux développeurs se spécialisent (frontend, backend, DevOps) ou "
        "explorent le freelancing pour varier les projets et les secteurs."
    ),
    "ingenieur-biotechnologies": (
        " Le secteur recrute notamment dans des pôles de compétitivité comme Paris-Saclay "
        "ou Lyon-Gerland, et dans les nombreuses startups biotech qui émergent chaque année "
        "en France et en Europe."
    ),
    "electrotechnicien": (
        " La transition énergétique crée de nouvelles opportunités : l'installation de "
        "bornes de recharge pour véhicules électriques et de panneaux photovoltaïques est "
        "en plein développement et nécessite des compétences en électrotechnique avancée."
    ),
    "technicien-maintenance-industrielle": (
        " Avec la montée de l'industrie 4.0, les techniciens de maintenance apprennent "
        "à exploiter les capteurs connectés et les outils d'analyse prédictive pour "
        "anticiper les pannes avant qu'elles surviennent, réduisant ainsi les arrêts de production."
    ),
    "ingenieur-civil-btp": (
        " La rénovation énergétique des bâtiments existants est un chantier colossal "
        "pour les décennies à venir : les ingénieurs génie civil spécialisés en réhabilitation "
        "thermique et en matériaux biosourcés seront très demandés."
    ),
    "biologiste-medical": (
        " Les laboratoires de biologie médicale jouent un rôle essentiel dans la santé "
        "publique, notamment lors de crises sanitaires. La biologie médicale est aussi "
        "en pleine transformation numérique avec l'intelligence artificielle appliquée "
        "à l'interprétation des résultats."
    ),
    "plombier-chauffagiste": (
        " La réglementation environnementale (RE2020) impose désormais des systèmes de "
        "chauffage plus vertueux, ce qui fait du plombier-chauffagiste un acteur-clé "
        "de la transition énergétique dans le secteur résidentiel."
    ),
    "electricien-batiment": (
        " La domotique et les maisons connectées représentent un marché en plein essor : "
        "les électriciens qui se forment aux systèmes KNX, aux panneaux solaires et aux "
        "bornes de recharge ont un avantage certain sur le marché du travail."
    ),
    "mecanicien-automobile": (
        " Les véhicules hybrides et électriques représentent une part croissante du parc "
        "automobile. Se former à la haute tension (habilitation HT) est désormais "
        "indispensable pour rester employable dans les garages modernes et les concessions."
    ),
    "charpentier": (
        " Le mouvement des Compagnons du Devoir valorise la tradition charpentière "
        "à travers un tour de France formateur : une voie enrichissante pour ceux qui "
        "souhaitent maîtriser toutes les facettes du métier."
    ),
    "carrossier-peintre": (
        " Les nouvelles carrosseries en matériaux composites (fibre de carbone, plastiques "
        "techniques) sur les voitures électriques modifient les techniques de réparation "
        "et ouvrent de nouvelles spécialisations pour les carrossiers de demain."
    ),
    "macon": (
        " La maçonnerie en pierre de taille ou en matériaux anciens (brique de terre crue, "
        "tuffeau, granit) est une spécialisation précieuse pour la restauration du "
        "patrimoine architectural et est très recherchée par les Monuments Historiques."
    ),
    "comptable": (
        " La comptabilité évolue avec les outils numériques : les logiciels automatisent "
        "de plus en plus les saisies répétitives, permettant aux comptables de se "
        "concentrer sur l'analyse et le conseil, rendant le métier plus stratégique."
    ),
    "commercial-btob": (
        " La maîtrise des outils de prospection digitale (LinkedIn, Sales Navigator, "
        "emailing automatisé) est devenue indispensable pour les commerciaux modernes "
        "qui doivent combiner approche terrain et prospection en ligne."
    ),
    "charge-rh": (
        " Les enjeux de marque employeur, de diversité et d'inclusion, et de bien-être "
        "au travail font des RH un partenaire stratégique de la direction, bien au-delà "
        "de la simple gestion administrative du personnel."
    ),
    "agent-logistique": (
        " L'essor du e-commerce a multiplié les entrepôts et les plateformes logistiques. "
        "Ce secteur recrute massivement et offre des possibilités d'évolution rapide "
        "pour les personnes sérieuses et motivées, quel que soit le niveau de départ."
    ),
    "cuisinier": (
        " Les tendances actuelles (cuisine végétale, circuits courts, cuisine du monde) "
        "ouvrent de nouvelles opportunités créatives pour les cuisinier·ères qui veulent "
        "se démarquer et construire leur propre identité gastronomique."
    ),
    "designer-ux-ui": (
        " L'accessibilité numérique (RGAA, WCAG) est un enjeu croissant : les designers "
        "qui maîtrisent les normes d'accessibilité pour les personnes en situation de "
        "handicap sont particulièrement recherchés dans les organisations publiques."
    ),
    "journaliste": (
        " Le journalisme de données (data journalism) et les formats vidéo courts "
        "sur les réseaux sociaux sont des compétences de plus en plus valorisées, "
        "y compris dans la presse traditionnelle qui se transforme."
    ),
    "graphiste": (
        " La motion design — animation de visuels et de typographies — est une "
        "compétence complémentaire très recherchée qui permet aux graphistes de "
        "travailler sur des contenus vidéo pour les réseaux sociaux et la publicité."
    ),
    "charge-communication": (
        " La communication de crise et la gestion de l'e-réputation sont des compétences "
        "de plus en plus stratégiques dans les grandes organisations, notamment dans "
        "un contexte de réseaux sociaux où une information peut vite se répandre."
    ),
    "photographe": (
        " L'intelligence artificielle commence à modifier le secteur de l'image, "
        "mais la photographie de reportage, d'événements et de portraits continuera "
        "à valoriser l'humain, le regard unique et la relation de confiance avec le sujet."
    ),
    "technicien-environnement": (
        " La réglementation environnementale se durcit régulièrement, ce qui rend "
        "les compétences en conformité environnementale très recherchées dans les "
        "entreprises industrielles soumises à des obligations croissantes de reporting ESG."
    ),
    "paysagiste": (
        " La végétalisation des villes (toitures végétalisées, corridors écologiques, "
        "jardins partagés) crée de nouveaux marchés porteurs pour les paysagistes "
        "qui se forment aux enjeux de biodiversité urbaine et de gestion différenciée."
    ),
    "agriculteur-maraicher": (
        " Les circuits courts (marchés, AMAP, vente directe à la ferme) permettent "
        "de mieux valoriser son travail et de tisser un lien direct avec les consommateurs, "
        "une tendance forte qui redonne de l'attractivité au métier d'agriculteur."
    ),
    "garde-forestier": (
        " Le changement climatique pose de nouveaux défis à la gestion forestière : "
        "adaptation des essences, gestion des grands incendies, surveillance sanitaire. "
        "Les agents ONF sont en première ligne pour adapter les forêts à ces enjeux."
    ),
    "professeur-lycee": (
        " Les nouveaux outils pédagogiques numériques (ENT, tablettes, classes inversées) "
        "transforment les pratiques enseignantes et ouvrent des espaces de créativité "
        "dans la conception des cours, notamment pour engager les élèves les plus distants."
    ),
    "formateur-professionnel": (
        " Le e-learning et les classes virtuelles ont transformé la formation professionnelle : "
        "les formateurs qui maîtrisent la conception de modules en ligne et les outils "
        "d'animation à distance (Zoom, Teams, Miro) ont de nombreux débouchés."
    ),
    "auxiliaire-puericulture": (
        " Le secteur de la petite enfance est en tension de recrutement constante : "
        "les places en crèche manquent et les professionnels qualifiés sont très demandés. "
        "C'est un secteur qui recrute dans toute la France, en milieu urbain comme rural."
    ),
    "conseiller-orientation-psychologue": (
        " La montée des troubles anxieux et du décrochage scolaire rend le rôle du PsyEN "
        "de plus en plus central dans les établissements. Ce métier est au cœur des "
        "enjeux d'égalité des chances et de bien-être à l'école."
    ),
    "agent-securite-privee": (
        " Les Jeux Olympiques et les grands événements sportifs ou culturels créent "
        "des pics de recrutement importants. Ce métier peut servir de tremplin vers "
        "une carrière dans la police, la gendarmerie ou les métiers de la sécurité civile."
    ),
    "pompier-sapeur": (
        " La France compte environ 40 000 sapeurs-pompiers professionnels et 200 000 "
        "volontaires. Si tu veux découvrir le métier avant le concours, devenir "
        "sapeur-pompier volontaire dès 16 ans est une excellente première étape."
    ),
    "juriste-entreprise": (
        " Le droit numérique (RGPD, cybersécurité, IA Act) est un domaine en pleine "
        "expansion qui crée une forte demande de juristes spécialisés dans les "
        "entreprises tech, les cabinets d'avocats et les autorités de régulation."
    ),
    "gendarme": (
        " La gendarmerie est aussi très présente sur le numérique : le C3N (Centre "
        "national de lutte contre les cybermenaces) recrute des gendarmes spécialisés "
        "en cybercriminalité, ouvrant une voie pour les profils tech intéressés par "
        "la sécurité publique."
    ),
    "chauffeur-spl": (
        " Le transport routier est un secteur en tension de recrutement chronique : "
        "les entreprises proposent souvent des formations au permis prises en charge "
        "via Pôle Emploi ou l'apprentissage pour attirer de nouveaux conducteurs."
    ),
    "technicien-aeronautique": (
        " L'industrie aéronautique recrute dans le monde entier : des opportunités "
        "existent au Moyen-Orient, en Asie et aux États-Unis pour les techniciens "
        "titulaires de la licence EASA et maîtrisant l'anglais technique."
    ),
    "controleur-de-gestion": (
        " Avec la montée de la finance d'entreprise digitale, les contrôleurs de gestion "
        "qui maîtrisent les outils BI (Power BI, Tableau, SAP) et l'analyse prédictive "
        "ont un avantage concurrentiel sur le marché de l'emploi."
    ),
    "conducteur-bus": (
        " Dans les grandes métropoles, les réseaux de transport développent des lignes "
        "de bus à haut niveau de service (BHNS) et expérimentent des véhicules à "
        "hydrogène ou électriques, enrichissant les compétences des conducteurs."
    ),
    "assistant-social": (
        " La profession est réglementée et nécessite un diplôme d'État. Les travailleurs "
        "sociaux expérimentés peuvent aussi se spécialiser en protection de l'enfance, "
        "en médiation familiale, ou évoluer vers des postes de coordination et d'encadrement."
    ),
}

# Maps slug → text appended to daily_routine if < 80 words
ROUTINE_EXTENSIONS: dict[str, str] = {
    "electrotechnicien": (
        " Tu documentes chaque intervention dans le carnet de bord et tu vérifies "
        "que les habilitations électriques de ton équipe sont bien à jour."
    ),
    "kinesitherapeute": (
        " Tu prends soin de ton matériel et de tes tables de massage en fin de journée, "
        "et tu notes les observations cliniques dans le dossier patient."
    ),
    "coiffeur": (
        " Tu termines en consultant ton agenda du lendemain pour préparer les colorations "
        "et précommander les produits nécessaires."
    ),
    "data-scientist": (
        " Tu consultes aussi les résultats des expériences A/B en production pour "
        "évaluer l'impact réel de ton modèle sur le comportement des utilisateurs."
    ),
    "biologiste-medical": (
        " En fin de journée, tu supervises la garde téléphonique pour répondre aux "
        "appels urgents des médecins qui ont besoin de résultats critiques rapidement."
    ),
    "electricien-batiment": (
        " Tu vérifies que tes interventions sont bien consignées dans le carnet "
        "d'entretien et que les attestations de conformité sont à jour."
    ),
    "carrossier-peintre": (
        " Tu consignes les travaux réalisés dans le dossier véhicule pour assurer "
        "la traçabilité des interventions et faciliter les éventuelles garanties."
    ),
    "macon": (
        " Tu ranges tes outils, nettoies ta zone de travail et confirmes avec le chef "
        "de chantier le programme du lendemain avant de partir."
    ),
    "comptable": (
        " Tu archives les pièces justificatives scannées dans la GED (gestion "
        "électronique de documents) pour garantir leur accessibilité lors d'un contrôle fiscal."
    ),
    "commercial-btob": (
        " Tu prépares aussi ton pitch pour le rendez-vous client du lendemain et "
        "tu te renseignes sur l'actualité de l'entreprise que tu vas visiter."
    ),
    "charge-rh": (
        " Tu termines ta journée en répondant aux dernières questions des salariés "
        "via le portail RH et en préparant l'ordre du jour de la prochaine réunion CSE."
    ),
    "agent-logistique": (
        " En fin de shift, tu transmets les informations importantes à l'équipe "
        "suivante pour assurer la continuité du flux logistique."
    ),
    "journaliste": (
        " Tu vérifies également les notifications sur les réseaux sociaux pour "
        "repérer d'éventuels développements sur les sujets que tu suis."
    ),
    "graphiste": (
        " Tu archives les versions finales dans le serveur partagé avec les noms "
        "de fichiers conventionnels pour que les clients puissent retrouver leurs "
        "éléments facilement."
    ),
    "charge-communication": (
        " Tu surveilles également les mentions de l'organisation sur les réseaux sociaux "
        "pour détecter rapidement tout bad buzz potentiel et réagir en amont."
    ),
    "technicien-environnement": (
        " Tu classes les résultats d'analyse dans le système de traçabilité réglementaire "
        "et tu mets à jour le tableau de bord environnemental de la semaine."
    ),
    "garde-forestier": (
        " En fin de journée, tu entres tes observations dans le système d'information "
        "géographique (SIG) de l'ONF pour alimenter la cartographie forestière."
    ),
    "conseiller-orientation-psychologue": (
        " Tu notes tes observations cliniques dans le dossier de l'élève, en veillant "
        "à la confidentialité absolue des éléments recueillis durant les entretiens."
    ),
    "agent-securite-privee": (
        " Tu consignes chaque événement de la journée dans le registre de main courante "
        "avant de passer les consignes à l'équipe du service suivant."
    ),
    "juriste-entreprise": (
        " Tu archives les contrats signés dans le logiciel de gestion contractuelle "
        "et tu mets à jour les échéanciers pour les prochaines dates de renouvellement."
    ),
    "gendarme": (
        " Avant la fin de service, tu transmets un rapport de situation au chef "
        "de brigade et consignes tous les événements dans le main courante de la brigade."
    ),
    "chauffeur-spl": (
        " Tu notes dans le carnet de bord les incidents éventuels (retard, problème "
        "de livraison) et tu transmets les documents de transport au service administratif."
    ),
    "technicien-aeronautique": (
        " Tu documentes chaque action dans le logiciel de maintenance et tu t'assures "
        "que les pièces remplacées sont correctement tracées pour la navigabilité continue."
    ),
    "controleur-de-gestion": (
        " En fin de journée, tu envoies les tableaux de bord à la direction et notes "
        "les questions soulevées pour le comité de pilotage de la semaine suivante."
    ),
    "assistant-social": (
        " Tu coordonnes avec tes collègues les situations urgentes et transmets les "
        "signalements au chef de service si une situation nécessite une intervention rapide."
    ),
    "animateur-socioculturel": (
        " Tu ranges le matériel utilisé lors des ateliers et prépares "
        "le programme de la semaine suivante avec tes collègues."
    ),
}
