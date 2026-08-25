"""Seed data part 2/3 — BTP/Artisanat (6) + Business/Commerce (6) + Arts/Culture (6)."""

PROFESSIONS_PART2 = [
    # ── BTP / INDUSTRIE / ARTISANAT (6) ─────────────────────────────────────
    {
        "slug": "plombier-chauffagiste",
        "name": "Plombier·ère chauffagiste",
        "sector": "btp",
        "description": (
            "Le·la plombier·ère chauffagiste installe et entretient les réseaux d'eau, "
            "de gaz, et les systèmes de chauffage dans les bâtiments. Tu poses des tuyauteries, "
            "installes des chaudières, des chauffe-eau, des radiateurs et des systèmes de "
            "climatisation. Tu interviens aussi pour les dépannages d'urgence (fuite d'eau, "
            "panne de chaudière en hiver). Ce métier est très demandé et offre une "
            "excellente insertion professionnelle. Avec la transition énergétique, les "
            "compétences en pompes à chaleur, panneaux solaires thermiques et systèmes "
            "géothermiques sont de plus en plus valorisées. Tu peux travailler pour une "
            "entreprise ou t'installer à ton compte."
        ),
        "daily_routine": (
            "Ta journée commence dans le camion avec ton outillage : tu te rends chez le "
            "premier client pour installer une nouvelle chaudière à condensation. Tu "
            "démontes l'ancienne, adaptes les raccordements, poses et règles la nouvelle "
            "installation. L'après-midi, une urgence : une fuite sous un évier chez un "
            "autre client. Tu diagnostiques le problème (joint usé), remplaces la pièce et "
            "vérifies qu'il n'y a pas de dégâts des eaux cachés. En fin de journée, tu "
            "vérifies ton stock de pièces dans le camion et passes ta commande."
        ),
        "requirements_json": [
            {"type": "studies", "label": "CAP Installateur Sanitaire — accessible dès la 3ème"},
            {
                "type": "studies",
                "label": "Bac Pro TISEC (Technicien en Installation des Systèmes Énergétiques et Climatiques)",
            },
            {"type": "skill", "label": "Soudure (cuivre, acier, plastique) et raccordements"},
            {"type": "skill", "label": "Installation et réglage de chaudières et PAC"},
            {"type": "quality", "label": "Habileté manuelle et sens pratique"},
            {"type": "quality", "label": "Autonomie et sens du service client"},
            {"type": "quality", "label": "Capacité à travailler dans des espaces confinés"},
        ],
        "prospects_text": (
            "1. Chef·fe d'équipe plomberie-chauffage. "
            "2. Artisan indépendant (création d'entreprise). "
            "3. Technicien·ne spécialisé·e en énergies renouvelables (PAC, solaire thermique)."
        ),
        "median_salary_eur": 28000,
        "salary_range_json": {"min": 22000, "max": 45000, "source": "Onisep 2025"},
        "signals_json": {
            "passions": ["bricolage", "mécanique", "eau", "énergie"],
            "valeurs": ["travail concret", "service", "autonomie", "artisanat"],
            "specialites": ["physique", "technologie", "mathematiques"],
            "keywords": ["plomberie", "chauffage", "énergie", "BTP", "artisan", "installation"],
        },
        "level_compatibility": ["college_3eme", "lycee_1ere_tle_pro", "lycee_2nde"],
        "rome_code": "F1603",
        "sources_json": ["Onisep 2025", "ROME v4.0 F1603", "validation humaine 2026-06"],
    },
    {
        "slug": "electricien-batiment",
        "name": "Électricien·ne du bâtiment",
        "sector": "btp",
        "description": (
            "L'électricien·ne du bâtiment installe et entretient les réseaux électriques "
            "dans les maisons, appartements, bureaux et commerces. Tu poses les câbles, "
            "installes les tableaux électriques, poses les prises et interrupteurs, et "
            "mets aux normes des installations existantes. Avec la montée des objets "
            "connectés et des bornes de recharge pour véhicules électriques, ce métier "
            "évolue vers des installations de plus en plus technologiques. Tu travailles "
            "en neuf (construction) ou en rénovation. Le métier est très recherché et "
            "l'emploi est garanti. En artisan indépendant, les revenus peuvent être "
            "très bons."
        ),
        "daily_routine": (
            "Tu commences ta journée sur le chantier d'une maison en construction : "
            "tu poses les gaines et passes les câbles dans les saignées prévues dans "
            "les murs. Tu travailles en coordination avec les plâtriers et les maçons. "
            "L'après-midi, tu te rends chez un particulier pour vérifier sa conformité "
            "électrique (diagnostic obligatoire à la vente). Tu constates quelques "
            "anomalies et rédiges le rapport. En fin de semaine, tu géres les devis et "
            "les factures si tu es à ton compte."
        ),
        "requirements_json": [
            {"type": "studies", "label": "CAP Électricien — accessible dès la 3ème, 2 ans"},
            {"type": "studies", "label": "Bac Pro MELEC ou BEP Électrotechnique"},
            {"type": "skill", "label": "Lecture de plans et schémas électriques"},
            {"type": "skill", "label": "Habilitations électriques obligatoires (B1V, BR)"},
            {"type": "quality", "label": "Rigueur et respect des normes (NF C 15-100)"},
            {"type": "quality", "label": "Sens pratique et organisation sur chantier"},
            {"type": "quality", "label": "Autonomie et contact client"},
        ],
        "prospects_text": (
            "1. Maître artisan et création de sa propre entreprise. "
            "2. Chef·fe de chantier électricité. "
            "3. Spécialisation domotique, smart home ou bornes de recharge VE."
        ),
        "median_salary_eur": 27000,
        "salary_range_json": {"min": 21000, "max": 42000, "source": "Onisep 2025"},
        "signals_json": {
            "passions": ["électricité", "bricolage", "technologie", "construction"],
            "valeurs": ["travail concret", "autonomie", "artisanat", "sécurité"],
            "specialites": ["physique", "technologie"],
            "keywords": ["électricité", "BTP", "chantier", "installation", "artisan", "bâtiment"],
        },
        "level_compatibility": ["college_3eme", "lycee_1ere_tle_pro", "lycee_2nde"],
        "rome_code": "F1602",
        "sources_json": ["Onisep 2025", "ROME v4.0 F1602", "validation humaine 2026-06"],
    },
    {
        "slug": "mecanicien-automobile",
        "name": "Mécanicien·ne automobile",
        "sector": "industrie",
        "description": (
            "Le·la mécanicien·ne automobile diagnostique et répare les pannes des véhicules "
            "à moteur. Tu effectues les entretiens courants (vidanges, changements de pneus, "
            "freins), tu diagnostiques les pannes avec des valises électroniques, et tu "
            "répares ou remplaces les pièces défectueuses. Ce métier évolue rapidement : "
            "les voitures modernes sont bourrées d'électronique, et les véhicules électriques "
            "et hybrides nécessitent de nouvelles compétences. Tu peux travailler dans un "
            "garage indépendant, une concession officielle, ou une chaîne de réparation rapide. "
            "La passion pour les moteurs est indispensable, et la curiosité technique aussi."
        ),
        "daily_routine": (
            "Ta matinée commence par le planning des véhicules à traiter. Tu accueilles "
            "le premier client, écoutes sa description de la panne, puis tu branches la "
            "valise de diagnostic sur le véhicule. Le code erreur indique un capteur O2 "
            "défaillant — tu le localises, le démontes et le remplaces. L'après-midi, tu "
            "effectues une révision complète : vidange, filtres, bougies, vérification des "
            "freins. Tu testes le véhicule sur la route avant de le rendre au client. "
            "Tu expliques ce que tu as fait et conseilles sur le prochain entretien."
        ),
        "requirements_json": [
            {"type": "studies", "label": "CAP Maintenance des Véhicules — accessible dès la 3ème"},
            {"type": "studies", "label": "Bac Pro MAVA (Maintenance Auto Véhicules Automobiles)"},
            {"type": "skill", "label": "Diagnostic électronique avec valise OBD"},
            {"type": "skill", "label": "Mécanique moteur, transmission, freinage et suspension"},
            {"type": "quality", "label": "Curiosité technique et mise à jour continue"},
            {"type": "quality", "label": "Méthode et rigueur dans le diagnostic"},
            {"type": "quality", "label": "Sens du service et communication avec les clients"},
        ],
        "prospects_text": (
            "1. Chef d'atelier ou responsable après-vente. "
            "2. Expert automobile (assurances, contrôle technique). "
            "3. Spécialiste véhicules électriques et hybrides (habilitation HT)."
        ),
        "median_salary_eur": 25000,
        "salary_range_json": {"min": 20000, "max": 38000, "source": "Onisep 2025"},
        "signals_json": {
            "passions": ["voitures", "mécanique", "technologie", "résolution de problèmes"],
            "valeurs": ["travail concret", "précision", "service", "technique"],
            "specialites": ["physique", "technologie", "mathematiques"],
            "keywords": ["mécanique", "automobile", "voiture", "moteur", "réparation", "garage"],
        },
        "level_compatibility": ["college_3eme", "lycee_1ere_tle_pro", "lycee_2nde"],
        "rome_code": "I1604",
        "sources_json": ["Onisep 2025", "ROME v4.0 I1604", "validation humaine 2026-06"],
    },
    {
        "slug": "charpentier",
        "name": "Charpentier·ère",
        "sector": "btp",
        "description": (
            "Le·la charpentier·ère fabrique et pose les structures en bois qui constituent "
            "l'ossature des toitures, planchers et charpentes des bâtiments. Tu travailles "
            "le bois avec des outils manuels et des machines, tu assembles des pièces selon "
            "des plans précis et tu les installais sur les chantiers. La charpente bois "
            "connaît un regain d'intérêt avec la construction durable et les bâtiments à "
            "ossature bois. Tu peux te spécialiser en charpente traditionnelle (restauration "
            "de monuments historiques), charpente industrielle ou construction à ossature "
            "bois (COB). Ce métier artisanal demande une vraie maîtrise du bois et un sens "
            "de l'espace en trois dimensions."
        ),
        "daily_routine": (
            "Ta journée commence à l'atelier : tu prépares les pièces de bois en les "
            "débitant et en les assemblant selon les plans. Tu utilises la scie, la "
            "raboteuse et les outils à main pour tracer et couper avec précision. "
            "Sur chantier, tu lèves la charpente avec une grue, poses les fermes et "
            "assembles les chevrons. Le travail en hauteur fait partie du quotidien. "
            "Tu termines par la vérification que l'ensemble est bien fixé et conforme "
            "aux plans avant de couvrir avec les tuiles ou l'isolation."
        ),
        "requirements_json": [
            {"type": "studies", "label": "CAP Charpentier bois — accessible dès la 3ème"},
            {"type": "studies", "label": "Bac Pro Technicien Constructeur Bois"},
            {"type": "skill", "label": "Lecture de plans et traçage"},
            {"type": "skill", "label": "Maîtrise des machines à bois et assemblages"},
            {"type": "quality", "label": "Habileté manuelle et sens du détail"},
            {"type": "quality", "label": "Capacité à travailler en hauteur sans vertige"},
            {"type": "quality", "label": "Rigueur géométrique (calcul de pentes, angles)"},
        ],
        "prospects_text": (
            "1. Maître compagnon et chef d'équipe charpente. "
            "2. Artisan indépendant — charpente traditionnelle ou COB. "
            "3. Conducteur·rice de travaux en entreprise de construction bois."
        ),
        "median_salary_eur": 27000,
        "salary_range_json": {"min": 21000, "max": 40000, "source": "Onisep 2025"},
        "signals_json": {
            "passions": ["bois", "construction", "artisanat", "travail en plein air"],
            "valeurs": ["artisanat", "travail concret", "tradition", "durabilité"],
            "specialites": ["mathematiques", "technologie", "arts"],
            "keywords": ["charpente", "bois", "BTP", "artisan", "construction", "toit"],
        },
        "level_compatibility": ["college_3eme", "lycee_1ere_tle_pro", "lycee_2nde"],
        "rome_code": "F1601",
        "sources_json": ["Onisep 2025", "ROME v4.0 F1601", "validation humaine 2026-06"],
    },
    {
        "slug": "carrossier-peintre",
        "name": "Carrossier·ère-peintre",
        "sector": "industrie",
        "description": (
            "Le·la carrossier·ère-peintre répare et remet en état la carrosserie des "
            "véhicules endommagés suite à des accidents ou des détériorations. Tu "
            "redresses les tôles, remplaces les pièces trop abîmées, puis tu prépares "
            "la surface et appliques la peinture en plusieurs couches pour obtenir un "
            "résultat identique à l'origine. Le travail est à la fois technique "
            "(redressage, remplacement de pièces) et artistique (mélange des teintes, "
            "finitions). Tu travailles dans des garages spécialisés, des concessions "
            "automobiles ou des ateliers de restauration de véhicules anciens. La "
            "précision et le perfectionnisme sont des atouts majeurs dans ce métier."
        ),
        "daily_routine": (
            "Ta matinée commence par l'évaluation d'un véhicule accidenté : tu mesures "
            "les déformations et établis le devis des réparations. Tu commences ensuite "
            "le débosselage d'une aile froissée avec tes outils. L'après-midi, tu prépares "
            "la surface d'un capot en ponçant et appliquant l'apprêt. Dans la cabine de "
            "peinture, tu mélanges avec précision la teinte et tu appliques la couleur "
            "en plusieurs passes. Tu vérifies la qualité du rendu sous plusieurs angles "
            "de lumière avant de remettre le véhicule au client."
        ),
        "requirements_json": [
            {
                "type": "studies",
                "label": "CAP Réparation des Carrosseries — accessible dès la 3ème",
            },
            {"type": "studies", "label": "Bac Pro Réparation des Carrosseries"},
            {"type": "skill", "label": "Techniques de redressage et débosselage"},
            {"type": "skill", "label": "Préparation de surface et application de peinture"},
            {"type": "skill", "label": "Mélange et dosage des teintes"},
            {"type": "quality", "label": "Sens esthétique et perfectionnisme"},
            {"type": "quality", "label": "Habileté manuelle et patience"},
        ],
        "prospects_text": (
            "1. Chef d'atelier carrosserie. "
            "2. Expert automobile pour les assurances. "
            "3. Restaurateur·rice de véhicules anciens — métier artisanal très valorisé."
        ),
        "median_salary_eur": 25000,
        "salary_range_json": {"min": 20000, "max": 38000, "source": "Onisep 2025"},
        "signals_json": {
            "passions": ["voitures", "peinture", "perfectionnisme", "artisanat"],
            "valeurs": ["précision", "esthétique", "travail concret", "artisanat"],
            "specialites": ["arts", "physique", "technologie"],
            "keywords": ["carrosserie", "peinture", "automobile", "réparation", "artisan"],
        },
        "level_compatibility": ["college_3eme", "lycee_1ere_tle_pro", "lycee_2nde"],
        "rome_code": "I1601",
        "sources_json": ["Onisep 2025", "ROME v4.0 I1601", "validation humaine 2026-06"],
    },
    {
        "slug": "macon",
        "name": "Maçon·ne",
        "sector": "btp",
        "description": (
            "Le·la maçon·ne construit les murs, fondations et dalles des bâtiments en "
            "utilisant des matériaux comme la brique, le parpaing, le béton et la pierre. "
            "Tu prépares les fondations, montes les murs et réalises les finitions. "
            "La maçonnerie est le métier de base du BTP, et ses compétences sont "
            "demandées sur tous les chantiers. Tu peux te spécialiser en maçonnerie "
            "traditionnelle (pierre, tuffeau), en restauration du patrimoine ou en béton "
            "armé pour les grandes structures. C'est un métier physique, en extérieur, "
            "qui demande de l'endurance. Les chantiers varient : maisons individuelles, "
            "immeubles, monuments historiques."
        ),
        "daily_routine": (
            "Ta journée commence à 7h sur le chantier avec le briefing du chef. Tu prépares "
            "ton mortier, poses tes fils à plomb et commences à monter les parpaings rangée "
            "par rangée en vérifiant constamment l'aplomb et le niveau. Le matin est souvent "
            "le plus productif : il fait moins chaud. L'après-midi, tu coffres une dalle "
            "béton avec tes collègues avant la coulée prévue demain matin. Tu nettoies tes "
            "outils avant de quitter le chantier."
        ),
        "requirements_json": [
            {"type": "studies", "label": "CAP Maçonnerie — accessible dès la 3ème"},
            {"type": "studies", "label": "Bac Pro Technicien du Bâtiment ou BTS Bâtiment"},
            {"type": "skill", "label": "Lecture de plans et traçage d'implantation"},
            {"type": "skill", "label": "Techniques de coffrage et ferraillage"},
            {"type": "quality", "label": "Endurance physique (travail en extérieur)"},
            {"type": "quality", "label": "Précision et souci du travail bien fait"},
            {"type": "quality", "label": "Travail en équipe sur chantier"},
        ],
        "prospects_text": (
            "1. Chef d'équipe maçonnerie. "
            "2. Conducteur·rice de travaux. "
            "3. Artisan maçon indépendant spécialisé en rénovation ou patrimoine."
        ),
        "median_salary_eur": 26000,
        "salary_range_json": {"min": 21000, "max": 40000, "source": "Onisep 2025"},
        "signals_json": {
            "passions": ["construction", "bâtiment", "travail en plein air", "physique"],
            "valeurs": ["travail concret", "effort", "construire", "équipe"],
            "specialites": ["mathematiques", "physique"],
            "keywords": ["maçonnerie", "BTP", "construction", "chantier", "béton", "bâtiment"],
        },
        "level_compatibility": ["college_3eme", "lycee_1ere_tle_pro", "lycee_2nde"],
        "rome_code": "F1703",
        "sources_json": ["Onisep 2025", "ROME v4.0 F1703", "validation humaine 2026-06"],
    },
    # ── BUSINESS / COMMERCE / GESTION (6) ────────────────────────────────────
    {
        "slug": "comptable",
        "name": "Comptable",
        "sector": "business",
        "description": (
            "Le·la comptable enregistre, classe et analyse les opérations financières d'une "
            "entreprise ou d'un organisme. Tu tiens les livres de compte, prépares les "
            "bilans et comptes de résultat, gères les déclarations fiscales et sociales. "
            "Ce métier est indispensable dans toute structure, quelle que soit sa taille. "
            "Tu peux travailler dans un cabinet d'expertise comptable (qui conseille "
            "plusieurs clients) ou en entreprise (comptabilité interne). La rigueur et "
            "la confidentialité sont primordiales. Le métier évolue vers plus d'analyse "
            "et de conseil avec l'automatisation des tâches répétitives par les logiciels."
        ),
        "daily_routine": (
            "Ta matinée commence par le traitement du courrier et des factures reçues : "
            "tu les saisies dans le logiciel de comptabilité (Sage, Ciel, QuickBooks). "
            "Tu vérifies les rapprochements bancaires et tu réponds aux relances fournisseurs. "
            "L'après-midi, tu prépares la déclaration de TVA du mois ou tu travailles sur "
            "le bilan de fin d'année. En cabinet, tu reçois un client PME pour lui présenter "
            "ses résultats et répondre à ses questions sur sa situation fiscale."
        ),
        "requirements_json": [
            {"type": "studies", "label": "BTS Comptabilité et Gestion (CG) — 2 ans après Bac"},
            {"type": "studies", "label": "DCG (Diplôme de Comptabilité et Gestion) — Bac +3"},
            {"type": "skill", "label": "Maîtrise d'un logiciel de comptabilité (Sage, QuickBooks)"},
            {"type": "skill", "label": "Droit fiscal, droit des sociétés, normes comptables"},
            {
                "type": "quality",
                "label": "Rigueur et précision (une erreur peut avoir des conséquences fiscales)",
            },
            {"type": "quality", "label": "Discrétion et confidentialité"},
            {"type": "quality", "label": "Organisation et gestion des délais"},
        ],
        "prospects_text": (
            "1. Expert·e-comptable après DSCG + stage (Bac +8). "
            "2. Directeur·rice financier·ère (DAF) en entreprise. "
            "3. Commissaire aux comptes (CAC) — métier réglementé."
        ),
        "median_salary_eur": 30000,
        "salary_range_json": {"min": 24000, "max": 55000, "source": "Apec 2025"},
        "signals_json": {
            "passions": ["chiffres", "organisation", "gestion", "rigueur"],
            "valeurs": ["précision", "ordre", "responsabilité", "fiabilité"],
            "specialites": ["mathematiques", "economie", "gestion"],
            "keywords": ["comptabilité", "finance", "gestion", "chiffres", "entreprise", "bilan"],
        },
        "level_compatibility": ["lycee_1ere_tle_general", "lycee_1ere_tle_techno", "postbac"],
        "rome_code": "M1203",
        "sources_json": ["Apec 2025", "ROME v4.0 M1203", "validation humaine 2026-06"],
    },
    {
        "slug": "commercial-btob",
        "name": "Commercial·e B2B",
        "sector": "business",
        "description": (
            "Le·la commercial·e B2B (business-to-business) vend des produits ou services "
            "à des entreprises clientes. Tu prospectes de nouveaux clients, présentes tes "
            "offres, négocies les prix et conditions, et fidélises ton portefeuille. "
            "Tu peux travailler dans des secteurs très variés : logiciels, assurances, "
            "équipements industriels, services aux entreprises. Ce métier demande un "
            "excellent relationnel, de la persévérance face aux refus, et une bonne "
            "compréhension du business de tes clients pour leur proposer la solution la "
            "plus adaptée. Les perspectives de revenus sont attractives avec un variable "
            "lié aux performances."
        ),
        "daily_routine": (
            "Ta matinée commence par les appels de prospection : tu contactes des "
            "entreprises cibles pour décrocher des rendez-vous. Vers 10h, tu te rends "
            "chez un prospect pour présenter ta solution. Tu écoutes ses besoins, "
            "argumentes et réponds aux objections. L'après-midi, tu rédiges une "
            "proposition commerciale personnalisée, puis tu rappelles un client existant "
            "pour faire le point sur sa satisfaction et détecter des opportunités "
            "d'upsell. Tu termine en mettant à jour ton CRM (outil de suivi client)."
        ),
        "requirements_json": [
            {
                "type": "studies",
                "label": "BTS NDRC (Négociation et Digitalisation de la Relation Client) ou MCO",
            },
            {"type": "studies", "label": "Licence Pro Commerce ou Bachelor Commerce / Marketing"},
            {"type": "skill", "label": "Techniques de vente et négociation"},
            {"type": "skill", "label": "Maîtrise d'un CRM (Salesforce, HubSpot)"},
            {"type": "quality", "label": "Excellente communication orale et écoute active"},
            {"type": "quality", "label": "Persévérance et résistance aux refus"},
            {"type": "quality", "label": "Organisation et gestion de son agenda"},
        ],
        "prospects_text": (
            "1. Responsable commercial·e ou Key Account Manager (grands comptes). "
            "2. Directeur·rice commercial·e. "
            "3. Business developer dans une startup tech (très recherché)."
        ),
        "median_salary_eur": 38000,
        "salary_range_json": {"min": 28000, "max": 70000, "source": "Apec 2025"},
        "signals_json": {
            "passions": ["contact humain", "persuasion", "business", "négociation"],
            "valeurs": ["performance", "autonomie", "ambition", "service client"],
            "specialites": ["economie", "gestion", "langues"],
            "keywords": ["commerce", "vente", "négociation", "client", "business", "entreprise"],
        },
        "level_compatibility": [
            "lycee_1ere_tle_general",
            "lycee_1ere_tle_techno",
            "lycee_1ere_tle_pro",
            "postbac",
        ],
        "rome_code": "D1403",
        "sources_json": ["Apec 2025", "ROME v4.0 D1403", "validation humaine 2026-06"],
    },
    {
        "slug": "chef-de-projet-digital",
        "name": "Chef·fe de projet digital",
        "sector": "business",
        "description": (
            "Le·la chef·fe de projet digital coordonne la réalisation de projets "
            "numériques : création de sites web, développement d'applications, campagnes "
            "digitales. Tu fais le lien entre les clients (ou la direction), les équipes "
            "techniques (développeurs, designers) et les parties prenantes. Tu planifies, "
            "suis l'avancement, gères les budgets et t'assures que le projet est livré à "
            "temps et dans les bonnes conditions. Ce métier demande à la fois des "
            "compétences de gestion (planning, budget, risques) et une culture tech "
            "suffisante pour communiquer avec les équipes. Il est très répandu dans les "
            "agences web, les directions marketing des grandes entreprises et les startups."
        ),
        "daily_routine": (
            "Ta matinée commence par la lecture des emails et Slack : tu identifies les "
            "blocages de l'équipe et les demandes clients. Tu animates ensuite un point "
            "d'équipe pour faire avancer les tâches en retard. Vers 11h, un appel client "
            "pour faire le point sur l'avancement et gérer une demande de modification "
            "de dernière minute. L'après-midi, tu mets à jour le planning, réalises une "
            "recette (tests fonctionnels) sur une nouvelle version de l'application, "
            "puis tu prépares le compte-rendu de réunion client."
        ),
        "requirements_json": [
            {"type": "studies", "label": "Bachelor ou Master Management de Projets digitaux"},
            {"type": "studies", "label": "École de commerce avec spécialisation digital"},
            {"type": "skill", "label": "Gestion de projet (Agile, Scrum, Kanban)"},
            {"type": "skill", "label": "Maîtrise d'outils de PM (Jira, Notion, Asana)"},
            {
                "type": "quality",
                "label": "Communication et médiation entre profils techniques et non-techniques",
            },
            {"type": "quality", "label": "Organisation et gestion des priorités"},
            {"type": "quality", "label": "Curiosité et culture digitale"},
        ],
        "prospects_text": (
            "1. Directeur·rice de projets ou PMO. "
            "2. Product Manager (gestion de produit). "
            "3. Directeur·rice digital·e."
        ),
        "median_salary_eur": 42000,
        "salary_range_json": {"min": 32000, "max": 65000, "source": "Apec 2025"},
        "signals_json": {
            "passions": ["organisation", "digital", "gestion", "coordination"],
            "valeurs": ["efficacité", "innovation", "travail en équipe", "résultats"],
            "specialites": ["mathematiques", "economie", "informatique"],
            "keywords": ["projet", "digital", "coordination", "agile", "management", "web"],
        },
        "level_compatibility": ["lycee_1ere_tle_general", "lycee_1ere_tle_techno", "postbac"],
        "rome_code": "M1805",
        "sources_json": ["Apec 2025", "ROME v4.0 M1805", "validation humaine 2026-06"],
    },
    {
        "slug": "charge-rh",
        "name": "Chargé·e de ressources humaines",
        "sector": "business",
        "description": (
            "Le·la chargé·e RH gère tout ce qui concerne les salarié·e·s d'une entreprise : "
            "recrutement, formation, paie, relations sociales, droit du travail. Tu rédiges "
            "les offres d'emploi, conduis les entretiens, accueilles les nouveaux arrivants "
            "et accompagnes les managers. En cas de conflit, tu joues un rôle de médiateur·rice. "
            "Ce métier est à la croisée du droit, de la psychologie et du management. "
            "Il est présent dans toutes les grandes entreprises et peut aussi s'exercer "
            "en cabinet de conseil RH. La transformation numérique (SIRH, outils RH) "
            "et les questions de bien-être au travail rendent ce métier de plus en plus "
            "stratégique."
        ),
        "daily_routine": (
            "Ta matinée commence par l'examen des CV reçus pour un poste ouvert. Tu "
            "contactes les candidats sélectionnés pour les entretiens téléphoniques. "
            "Vers 10h, tu animes une session d'onboarding pour deux nouveaux arrivants. "
            "L'après-midi, tu prépares les éléments de paie du mois, réponds à des "
            "questions de salarié·e·s sur leurs congés ou leur mutuelle, puis tu "
            "travailles sur le plan de formation annuel avec un manager. La journée "
            "RH est faite de tâches très variées."
        ),
        "requirements_json": [
            {"type": "studies", "label": "Licence RH ou droit social — Bac +3"},
            {"type": "studies", "label": "Master RH, Management ou droit du travail"},
            {"type": "skill", "label": "Droit du travail et paie (DSN)"},
            {"type": "skill", "label": "Maîtrise d'un SIRH (SAP HCM, Workday, Payfit)"},
            {"type": "quality", "label": "Empathie et écoute active"},
            {"type": "quality", "label": "Discrétion et confidentialité"},
            {"type": "quality", "label": "Adaptabilité et gestion des priorités"},
        ],
        "prospects_text": (
            "1. Responsable RH ou HRBP (Business Partner). "
            "2. Directeur·rice des Ressources Humaines (DRH). "
            "3. Consultant·e RH en cabinet de conseil."
        ),
        "median_salary_eur": 35000,
        "salary_range_json": {"min": 28000, "max": 60000, "source": "Apec 2025"},
        "signals_json": {
            "passions": ["psychologie", "organisation", "management", "droit"],
            "valeurs": ["empathie", "justice", "bien-être au travail", "développement humain"],
            "specialites": ["economie", "sciences sociales", "langues", "gestion"],
            "keywords": ["RH", "recrutement", "ressources humaines", "management", "droit social"],
        },
        "level_compatibility": ["lycee_1ere_tle_general", "lycee_1ere_tle_techno", "postbac"],
        "rome_code": "M1502",
        "sources_json": ["Apec 2025", "ROME v4.0 M1502", "validation humaine 2026-06"],
    },
    {
        "slug": "agent-logistique",
        "name": "Agent·e logistique",
        "sector": "transport",
        "description": (
            "L'agent·e logistique organise le flux des marchandises : réception, stockage, "
            "préparation de commandes et expédition. Tu travailles en entrepôt, sur les "
            "quais, dans des centres de distribution. Tu utilises des chariots élévateurs, "
            "des scanners, des logiciels de gestion des stocks (WMS). Ce métier est "
            "indispensable dans le commerce (e-commerce en fort développement), la grande "
            "distribution, l'industrie. La logistique représente plusieurs millions d'emplois "
            "en France et recrute à tous les niveaux, du préparateur de commandes au "
            "directeur de supply chain. C'est un secteur très accessible à la sortie du "
            "lycée ou d'un CAP."
        ),
        "daily_routine": (
            "Ta journée débute par la prise de poste en entrepôt : tu consultes les "
            "commandes à préparer sur ton terminal. Tu parcours les allées de stockage "
            "avec ton chariot et scanner, prélèves les articles indiqués et les places "
            "dans les bacs de préparation. Une fois la commande complète, tu la filmes et "
            "la prépares pour l'expédition. Tu gères aussi les réceptions : tu contrôles "
            "la conformité des livraisons fournisseurs et mets à jour les stocks dans "
            "le système informatique."
        ),
        "requirements_json": [
            {"type": "studies", "label": "CAP ou BEP Logistique — accessible dès la 3ème"},
            {"type": "studies", "label": "Bac Pro Logistique ou BTS Supply Chain Management"},
            {"type": "skill", "label": "Conduite de chariots élévateurs (CACES R489)"},
            {"type": "skill", "label": "Utilisation d'un WMS (logiciel de gestion d'entrepôt)"},
            {"type": "quality", "label": "Rigueur et précision dans la préparation de commandes"},
            {"type": "quality", "label": "Endurance physique et résistance au froid"},
            {"type": "quality", "label": "Ponctualité et esprit d'équipe"},
        ],
        "prospects_text": (
            "1. Chef d'équipe logistique ou responsable d'entrepôt. "
            "2. Responsable supply chain après formation ou expérience. "
            "3. Responsable achat ou approvisionnement."
        ),
        "median_salary_eur": 23000,
        "salary_range_json": {"min": 19000, "max": 35000, "source": "France Travail 2025"},
        "signals_json": {
            "passions": ["organisation", "efficacité", "transport", "gestion"],
            "valeurs": ["rigueur", "travail en équipe", "efficacité", "service"],
            "specialites": ["mathematiques", "gestion"],
            "keywords": [
                "logistique",
                "entrepôt",
                "stock",
                "supply chain",
                "transport",
                "commandes",
            ],
        },
        "level_compatibility": ["college_3eme", "lycee_1ere_tle_pro", "lycee_2nde", "postbac"],
        "rome_code": "N1103",
        "sources_json": ["France Travail 2025", "ROME v4.0 N1103", "validation humaine 2026-06"],
    },
    {
        "slug": "cuisinier",
        "name": "Cuisinier·ère",
        "sector": "business",
        "description": (
            "Le·la cuisinier·ère prépare et dresse les plats dans des restaurants, hôtels, "
            "cantines, entreprises de restauration collective ou à domicile. Tu maîtrises "
            "les techniques culinaires (tailles, cuissons, sauces, pâtisserie de base), "
            "tu gères les stocks et les commandes, et tu respectes les normes d'hygiène "
            "(HACCP). La cuisine est un métier de passion et de créativité, mais aussi "
            "de rigueur et de résistance physique (chaleur, station debout, horaires "
            "décalés). Tu peux progresser rapidement : de commis à chef de partie, "
            "de chef de cuisine à chef étoilé. L'entrepreneuriat (food truck, restaurant) "
            "est aussi une voie courante."
        ),
        "daily_routine": (
            "Ta matinée commence par la réception des produits frais que tu vérifies et "
            "ranges. Tu prépares ensuite le mise en place : épluchage, découpe, "
            "préparation des fonds de sauce, dressage des entrées froides. À l'approche "
            "du service du midi, l'adrénaline monte : tu t'organises avec tes collègues "
            "pour sortir les plats chauds à temps. Après le service, tu nettoies ton "
            "poste scrupuleusement, gères les restes, et prépares certains éléments "
            "pour le soir. L'après-midi peut être consacré à la création de nouvelles "
            "recettes avec le chef."
        ),
        "requirements_json": [
            {"type": "studies", "label": "CAP Cuisine — accessible dès la 3ème, 2 ans"},
            {"type": "studies", "label": "Bac Pro Cuisine ou BTS Hôtellerie-Restauration"},
            {"type": "skill", "label": "Techniques culinaires de base (tailles, cuissons, sauces)"},
            {"type": "skill", "label": "Normes HACCP et hygiène alimentaire"},
            {"type": "quality", "label": "Créativité et sens esthétique du dressage"},
            {"type": "quality", "label": "Résistance physique et rapidité d'exécution"},
            {"type": "quality", "label": "Travail en équipe en brigade"},
        ],
        "prospects_text": (
            "1. Chef de partie, sous-chef, chef de cuisine. "
            "2. Création d'un restaurant ou food truck. "
            "3. Chef cuisinier dans un grand groupe (collectivité, hôtellerie internationale)."
        ),
        "median_salary_eur": 22000,
        "salary_range_json": {"min": 19000, "max": 50000, "source": "Onisep 2025"},
        "signals_json": {
            "passions": ["cuisine", "gastronomie", "créativité", "saveurs"],
            "valeurs": ["créativité", "artisanat", "plaisir", "partage"],
            "specialites": ["arts", "chimie"],
            "keywords": [
                "cuisine",
                "restaurant",
                "gastronomie",
                "chef",
                "alimentation",
                "créativité",
            ],
        },
        "level_compatibility": ["college_3eme", "lycee_1ere_tle_pro", "lycee_2nde"],
        "rome_code": "G1602",
        "sources_json": ["Onisep 2025", "ROME v4.0 G1602", "validation humaine 2026-06"],
    },
    # ── ARTS / CULTURE / COMMUNICATION (6) ───────────────────────────────────
    {
        "slug": "designer-ux-ui",
        "name": "Designer UX/UI",
        "sector": "arts",
        "description": (
            "Le·la designer UX/UI conçoit l'expérience et l'interface des applications "
            "numériques pour qu'elles soient à la fois belles, intuitives et efficaces. "
            "L'UX (User Experience) s'intéresse au parcours de l'utilisateur et à la "
            "facilité d'usage, tandis que l'UI (User Interface) concerne le design "
            "visuel : couleurs, typographies, composants graphiques. Tu mènes des "
            "recherches utilisateurs, crées des maquettes (wireframes), testes tes "
            "prototypes et travailles en étroite collaboration avec les développeurs. "
            "Ce métier est très recherché dans les startups, agences digitales et grandes "
            "entreprises. La créativité et l'empathie pour les utilisateurs sont tes "
            "principales compétences."
        ),
        "daily_routine": (
            "Ta matinée commence par une session de recherche utilisateurs : tu analyses "
            "les résultats d'un test UX réalisé la veille et identifies les points de "
            "friction. Puis tu ouvres Figma pour retravailler le parcours d'onboarding "
            "d'une application en tenant compte des retours. L'après-midi, tu présentes "
            "tes maquettes à l'équipe produit et tu itères en direct sur les retours. "
            "Tu prépares ensuite les specs (spécifications) pour les développeurs et tu "
            "te rends sur un salon design pour t'inspirer de tendances émergentes."
        ),
        "requirements_json": [
            {"type": "studies", "label": "Bachelor Design, Gobelins, Strate ou équivalent"},
            {
                "type": "studies",
                "label": "Master UX/Interaction Design ou école numérique (HETIC, 42, ESAD)",
            },
            {"type": "skill", "label": "Maîtrise de Figma, Sketch ou Adobe XD"},
            {
                "type": "skill",
                "label": "Méthodes de recherche UX (entretiens, tests utilisateurs, heuristiques)",
            },
            {"type": "quality", "label": "Empathie pour comprendre les besoins utilisateurs"},
            {"type": "quality", "label": "Sens esthétique et créativité"},
            {"type": "quality", "label": "Communication claire pour défendre ses choix de design"},
        ],
        "prospects_text": (
            "1. Lead designer ou head of design. "
            "2. Product designer ou design system lead. "
            "3. Freelance UX/UI — très courant dans ce domaine."
        ),
        "median_salary_eur": 42000,
        "salary_range_json": {"min": 30000, "max": 70000, "source": "Apec 2025"},
        "signals_json": {
            "passions": ["design", "créativité", "technologie", "esthétique"],
            "valeurs": ["créativité", "innovation", "empathie", "impact utilisateur"],
            "specialites": ["arts", "informatique", "mathematiques"],
            "keywords": ["design", "UX", "UI", "interface", "créativité", "digital"],
        },
        "level_compatibility": ["lycee_1ere_tle_general", "lycee_1ere_tle_techno", "postbac"],
        "rome_code": "E1205",
        "sources_json": ["Apec 2025", "ROME v4.0 E1205", "validation humaine 2026-06"],
    },
    {
        "slug": "journaliste",
        "name": "Journaliste",
        "sector": "arts",
        "description": (
            "Le·la journaliste informe le public en collectant, vérifiant et diffusant des "
            "informations via la presse écrite, la radio, la télévision ou le web. Tu mènes "
            "des enquêtes, interviews des sources, vérifies les faits et rédiges des articles "
            "ou reportages. La liberté de la presse et la rigueur dans la vérification des "
            "informations (fact-checking) sont au cœur du métier. Tu peux te spécialiser : "
            "journaliste sportif·ve, politique, économique, scientifique, de guerre. "
            "Le marché est compétitif et la précarité est réelle en début de carrière. "
            "Mais le journalisme est un métier de conviction, au service de la démocratie "
            "et du droit à l'information."
        ),
        "daily_routine": (
            "Ta matinée commence par la revue de presse : tu lis les journaux, sites et "
            "réseaux sociaux pour identifier les sujets du jour. Tu assistes à la "
            "conférence de rédaction où les sujets sont distribués. Tu pars interviewer "
            "un élu local sur un projet d'urbanisme. L'après-midi, tu rédiges ton "
            "article en vérifiant chaque information auprès de plusieurs sources. "
            "Tu soumets ton texte au rédacteur en chef pour relecture et publication "
            "le lendemain matin."
        ),
        "requirements_json": [
            {"type": "studies", "label": "École de journalisme reconnue (CFJ, ESJ, Sciences Po…)"},
            {"type": "studies", "label": "Master journalisme ou communication"},
            {"type": "skill", "label": "Rédaction, synthèse et respect des genres journalistiques"},
            {"type": "skill", "label": "Techniques d'interview et de recueil de sources"},
            {"type": "quality", "label": "Curiosité insatiable et culture générale solide"},
            {"type": "quality", "label": "Rigueur dans la vérification des faits"},
            {"type": "quality", "label": "Résistance à la pression et aux délais serrés"},
        ],
        "prospects_text": (
            "1. Rédacteur·rice en chef. "
            "2. Grand reporter ou correspondant·e à l'étranger. "
            "3. Journaliste indépendant·e (pigiste) ou YouTubeur·euse journaliste."
        ),
        "median_salary_eur": 30000,
        "salary_range_json": {"min": 20000, "max": 60000, "source": "Onisep 2025"},
        "signals_json": {
            "passions": ["écriture", "actualité", "enquête", "communication"],
            "valeurs": ["liberté", "vérité", "démocratie", "curiosité"],
            "specialites": ["francais", "histoire", "sciences sociales", "langues"],
            "keywords": ["journalisme", "presse", "information", "écriture", "médias", "reportage"],
        },
        "level_compatibility": ["lycee_1ere_tle_general", "postbac"],
        "rome_code": "E1106",
        "sources_json": ["Onisep 2025", "ROME v4.0 E1106", "validation humaine 2026-06"],
    },
    {
        "slug": "graphiste",
        "name": "Graphiste",
        "sector": "arts",
        "description": (
            "Le·la graphiste crée des visuels pour des supports de communication : affiches, "
            "logos, livres, emballages, sites web. Tu traduis un message ou une identité de "
            "marque en images, en choisissant les couleurs, typographies et mises en page "
            "adaptées. Tu travailles à partir d'un brief client, proposes plusieurs pistes "
            "créatives et aboutis à un produit finalisé. Tu peux exercer en agence de "
            "communication, en studio de design, dans le service communication d'une "
            "entreprise, ou en freelance. Les outils du quotidien : Adobe Photoshop, "
            "Illustrator et InDesign. Ce métier mêle créativité artistique et contraintes "
            "techniques (impression, formats numériques)."
        ),
        "daily_routine": (
            "Ta matinée commence par la lecture d'un nouveau brief : une startup te "
            "demande de créer son identité visuelle complète (logo, charte graphique, "
            "carte de visite). Tu explores plusieurs univers graphiques, crées des "
            "moodboards et proposes trois directions différentes. L'après-midi, tu "
            "travailles sur la mise en page d'un catalogue produit pour un autre client : "
            "tu aligns les textes, places les photos et vérifies que l'ensemble est "
            "cohérent visuellement. Tu prépares les fichiers pour l'imprimeur avant "
            "la fermeture."
        ),
        "requirements_json": [
            {"type": "studies", "label": "BTS Design Graphique ou Communication Visuelle"},
            {"type": "studies", "label": "École des Beaux-Arts ou école de design privée"},
            {"type": "skill", "label": "Adobe Creative Suite (Photoshop, Illustrator, InDesign)"},
            {"type": "skill", "label": "Identité visuelle, typographie et mise en page"},
            {
                "type": "quality",
                "label": "Sens esthétique et culture graphique (références visuelles)",
            },
            {"type": "quality", "label": "Créativité et originalité"},
            {"type": "quality", "label": "Respect des contraintes techniques et des délais"},
        ],
        "prospects_text": (
            "1. Directeur·rice artistique en agence. "
            "2. Motion designer ou illustrateur·rice. "
            "3. Freelance graphiste — très courant dans ce domaine."
        ),
        "median_salary_eur": 28000,
        "salary_range_json": {"min": 22000, "max": 50000, "source": "Apec 2025"},
        "signals_json": {
            "passions": ["arts", "design", "esthétique", "création visuelle"],
            "valeurs": ["créativité", "esthétique", "expression artistique", "innovation"],
            "specialites": ["arts", "informatique"],
            "keywords": ["graphisme", "design", "visuel", "créativité", "arts", "communication"],
        },
        "level_compatibility": ["lycee_1ere_tle_general", "lycee_1ere_tle_techno", "postbac"],
        "rome_code": "E1205",
        "sources_json": ["Apec 2025", "ROME v4.0 E1205", "validation humaine 2026-06"],
    },
    {
        "slug": "charge-communication",
        "name": "Chargé·e de communication",
        "sector": "arts",
        "description": (
            "Le·la chargé·e de communication conçoit et met en œuvre la stratégie de "
            "communication d'une organisation (entreprise, collectivité, association). "
            "Tu rédiges des contenus, gères les réseaux sociaux, organises des événements, "
            "et coordonnes les prestataires (agences, imprimeurs). Tu assures la cohérence "
            "de l'image de l'organisation auprès de ses différents publics. Ce métier "
            "demande une grande polyvalence : écriture, créativité visuelle, relation "
            "presse, digital. Il existe dans tous les types d'organisations et offre "
            "une belle variété de missions."
        ),
        "daily_routine": (
            "Ta matinée commence par la gestion des réseaux sociaux : tu réponds aux "
            "commentaires, planifies les posts de la semaine et analyses les statistiques "
            "d'engagement. Tu travailles ensuite sur un communiqué de presse pour un "
            "événement à venir. L'après-midi, tu organises les détails logistiques d'une "
            "conférence (salle, intervenants, supports), puis tu briefes une agence "
            "graphique sur une nouvelle campagne d'affichage. Tu termines par la "
            "rédaction de la newsletter mensuelle."
        ),
        "requirements_json": [
            {"type": "studies", "label": "Licence ou Master Communication des organisations"},
            {"type": "studies", "label": "École de communication ou Sciences Po"},
            {"type": "skill", "label": "Rédaction tous supports (web, print, presse)"},
            {
                "type": "skill",
                "label": "Community management et outils analytics (Google Analytics)",
            },
            {"type": "quality", "label": "Créativité et culture générale"},
            {"type": "quality", "label": "Organisation et gestion simultanée de plusieurs projets"},
            {"type": "quality", "label": "Aisance relationnelle et sens de la diplomatie"},
        ],
        "prospects_text": (
            "1. Responsable communication ou directeur·rice de la communication. "
            "2. Consultant·e en agence de relations publiques. "
            "3. Spécialisation content marketing, influence ou RP."
        ),
        "median_salary_eur": 33000,
        "salary_range_json": {"min": 26000, "max": 55000, "source": "Apec 2025"},
        "signals_json": {
            "passions": ["communication", "écriture", "créativité", "médias"],
            "valeurs": ["créativité", "expression", "impact", "relations humaines"],
            "specialites": ["francais", "histoire", "arts", "langues"],
            "keywords": [
                "communication",
                "médias",
                "rédaction",
                "événementiel",
                "réseaux sociaux",
                "relations publiques",
            ],
        },
        "level_compatibility": ["lycee_1ere_tle_general", "lycee_1ere_tle_techno", "postbac"],
        "rome_code": "E1103",
        "sources_json": ["Apec 2025", "ROME v4.0 E1103", "validation humaine 2026-06"],
    },
    {
        "slug": "photographe",
        "name": "Photographe professionnel·le",
        "sector": "arts",
        "description": (
            "Le·la photographe professionnel·le capture des images pour des clients ou "
            "des médias : reportages, portraits, photographie de mariage, mode, publicité, "
            "photojournalisme. Tu maîtrises les techniques de prise de vue (composition, "
            "lumière, exposition) et le post-traitement (retouche sous Lightroom et "
            "Photoshop). La photographie professionnelle demande un sens artistique certain, "
            "mais aussi des compétences commerciales pour trouver des clients, négocier "
            "ses tarifs et gérer son activité. La plupart des photographes exercent en "
            "freelance. C'est un métier de passion qui peut être difficile économiquement "
            "au départ, mais très épanouissant."
        ),
        "daily_routine": (
            "Ta journée varie beaucoup selon les missions. Un lundi de mariage : tu arrives "
            "à 10h pour le maquillage, tu suis les mariés toute la journée en cherchant la "
            "lumière et les moments authentiques. La semaine suivante : un shooting "
            "publicitaire en studio pour une marque de prêt-à-porter. Tu dirige le modèle, "
            "ajuste les éclairages, prend plusieurs centaines de photos. En soirée et le "
            "lendemain, tu sélectionnes et retouches les meilleures images. Tu gères aussi "
            "ta comptabilité et ta prospection client."
        ),
        "requirements_json": [
            {"type": "studies", "label": "BTS Photographie ou école des arts (Gobelins)"},
            {"type": "studies", "label": "Formation autodidacte possible avec portfolio solide"},
            {"type": "skill", "label": "Maîtrise de l'appareil photo (exposition, focale, flash)"},
            {"type": "skill", "label": "Retouche photo (Lightroom, Photoshop)"},
            {"type": "quality", "label": "Œil artistique et sens de la composition"},
            {"type": "quality", "label": "Capacité à mettre les personnes à l'aise"},
            {"type": "quality", "label": "Autonomie et esprit entrepreneurial (souvent freelance)"},
        ],
        "prospects_text": (
            "1. Photographe de presse ou reporter photo. "
            "2. Directeur·rice artistique dans une agence. "
            "3. Formation ou enseignement de la photographie."
        ),
        "median_salary_eur": 25000,
        "salary_range_json": {"min": 15000, "max": 60000, "source": "Onisep 2025"},
        "signals_json": {
            "passions": ["photographie", "arts visuels", "créativité", "voyages"],
            "valeurs": ["expression artistique", "liberté", "créativité", "authenticité"],
            "specialites": ["arts", "physique"],
            "keywords": ["photographie", "image", "arts", "créativité", "visuel", "culture"],
        },
        "level_compatibility": [
            "lycee_1ere_tle_general",
            "lycee_1ere_tle_techno",
            "lycee_1ere_tle_pro",
            "postbac",
        ],
        "rome_code": "B1042",
        "sources_json": ["Onisep 2025", "ROME v4.0 B1042", "validation humaine 2026-06"],
    },
]
