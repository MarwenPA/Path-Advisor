"""Seed data part 3/3 — Environnement/Agriculture (4) + Enseignement (4) + Sécurité (4) + Transport (4)."""

PROFESSIONS_PART3 = [
    # ── ENVIRONNEMENT / AGRICULTURE (4) ─────────────────────────────────────
    {
        "slug": "technicien-environnement",
        "name": "Technicien·ne en environnement",
        "sector": "environnement",
        "description": (
            "Le·la technicien·ne en environnement mesure, surveille et réduit les impacts "
            "des activités humaines sur la nature : qualité de l'air, de l'eau, des sols, "
            "gestion des déchets. Tu travailles pour des collectivités (stations de "
            "traitement des eaux), des industries (conformité environnementale), des "
            "bureaux d'études ou des associations environnementales. Ce métier est en "
            "plein essor avec les réglementations environnementales qui se renforcent et "
            "la prise de conscience collective sur les enjeux climatiques. Tu combines "
            "terrain (prélèvements, mesures) et bureau (analyses, rapports)."
        ),
        "daily_routine": (
            "Ta matinée commence sur le terrain : tu te rends au bord d'une rivière "
            "pour prélever des échantillons d'eau. Tu mesures in situ le pH, la "
            "température et l'oxygène dissous. De retour au laboratoire, tu analyses "
            "les échantillons pour détecter d'éventuels polluants. L'après-midi, tu "
            "rédiges un rapport pour la collectivité cliente et tu prépares une "
            "présentation pour la commission environnementale locale. Tu participes "
            "aussi à la mise à jour de la veille réglementaire environnementale."
        ),
        "requirements_json": [
            {"type": "studies", "label": "BTS Métiers des Services à l'Environnement ou GEMEAU"},
            {
                "type": "studies",
                "label": "Licence Pro ou BUT Génie Biologique spécialité Environnement",
            },
            {"type": "skill", "label": "Techniques de prélèvement et d'analyse (eau, air, sol)"},
            {"type": "skill", "label": "Réglementation environnementale (ICPE, eau, déchets)"},
            {"type": "quality", "label": "Goût pour le terrain et les sciences naturelles"},
            {"type": "quality", "label": "Rigueur dans les mesures et la rédaction de rapports"},
            {"type": "quality", "label": "Engagement pour l'environnement"},
        ],
        "prospects_text": (
            "1. Chargé·e de mission environnement en collectivité. "
            "2. Ingénieur·e HSE (Hygiène-Sécurité-Environnement). "
            "3. Expert·e en transition écologique pour des entreprises."
        ),
        "median_salary_eur": 28000,
        "salary_range_json": {"min": 23000, "max": 45000, "source": "Onisep 2025"},
        "signals_json": {
            "passions": ["nature", "environnement", "sciences", "écologie"],
            "valeurs": ["écologie", "durabilité", "responsabilité", "nature"],
            "specialites": ["svt", "chimie", "physique", "geographie"],
            "keywords": ["environnement", "eau", "écologie", "pollution", "nature", "durabilité"],
        },
        "level_compatibility": ["lycee_1ere_tle_general", "lycee_1ere_tle_techno", "postbac"],
        "rome_code": "A1303",
        "sources_json": ["Onisep 2025", "ROME v4.0 A1303", "validation humaine 2026-06"],
    },
    {
        "slug": "paysagiste",
        "name": "Paysagiste",
        "sector": "environnement",
        "description": (
            "Le·la paysagiste crée et entretient des espaces verts : jardins privés, parcs "
            "publics, espaces de loisirs, abords de bâtiments. Tu plantes des arbres et "
            "des fleurs, tailles les haies, tonds les pelouses, installes des systèmes "
            "d'irrigation. En conception paysagère, tu dessines les plans des espaces "
            "verts pour des projets d'aménagement. Ce métier s'exerce principalement en "
            "plein air, en toutes saisons. Il est physique mais gratifiant : voir pousser "
            "ce que tu as planté est une vraie satisfaction. Avec les enjeux de biodiversité "
            "et de végétalisation des villes, ce métier prend de plus en plus d'importance."
        ),
        "daily_routine": (
            "Ta journée commence de bonne heure dans les espaces verts de la commune. "
            "Tu commences par la tonte des pelouses avec le tracteur tondeuse, puis tu "
            "tailles les massifs de rosiers. L'après-midi, tu plantes les bulbes de la "
            "saison avec ton équipe et tu installes un système de goutte-à-goutte. "
            "En hiver, tu élagues les arbres et tu prépares les massifs pour la saison "
            "suivante. En dehors du terrain, tu rédiges des devis ou prépares les plans "
            "d'un nouveau jardin client."
        ),
        "requirements_json": [
            {"type": "studies", "label": "CAP Jardinier Paysagiste — accessible dès la 3ème"},
            {
                "type": "studies",
                "label": "Bac Pro Aménagements Paysagers ou BTSA Aménagements Paysagers",
            },
            {"type": "skill", "label": "Conduite d'engins (tracteur tondeuse, mini-pelle)"},
            {"type": "skill", "label": "Reconnaissance des végétaux et techniques de plantation"},
            {"type": "quality", "label": "Goût pour le travail en plein air et les plantes"},
            {"type": "quality", "label": "Endurance physique et résistance aux conditions météo"},
            {"type": "quality", "label": "Sens esthétique pour créer de beaux espaces"},
        ],
        "prospects_text": (
            "1. Chef d'équipe ou chef de chantier paysager. "
            "2. Créateur·rice de jardins indépendant·e. "
            "3. Concepteur·rice paysagiste (DPLG ou master paysage)."
        ),
        "median_salary_eur": 23000,
        "salary_range_json": {"min": 19000, "max": 38000, "source": "Onisep 2025"},
        "signals_json": {
            "passions": ["nature", "jardinage", "plantes", "plein air"],
            "valeurs": ["nature", "bien-être", "esthétique", "durabilité"],
            "specialites": ["svt", "arts"],
            "keywords": ["paysage", "jardin", "plantes", "nature", "espaces verts", "végétal"],
        },
        "level_compatibility": ["college_3eme", "lycee_1ere_tle_pro", "lycee_2nde"],
        "rome_code": "A1202",
        "sources_json": ["Onisep 2025", "ROME v4.0 A1202", "validation humaine 2026-06"],
    },
    {
        "slug": "agriculteur-maraicher",
        "name": "Agriculteur·rice maraîcher·ère",
        "sector": "environnement",
        "description": (
            "L'agriculteur·rice maraîcher·ère cultive des légumes et des fruits pour les "
            "vendre sur les marchés, aux grandes surfaces, ou en circuit court (AMAP, "
            "vente directe). Tu prépares les sols, plantes ou sèmes, irrigues, traites "
            "les cultures contre les maladies, récoltes et conditionnes. Avec l'agriculture "
            "biologique en fort développement, de nombreux maraîchers travaillent sans "
            "produits chimiques. C'est un métier de plein air, physique, qui demande de "
            "l'autonomie et des connaissances agronomiques. L'installation est possible "
            "via des programmes d'aide à la transmission (jeunes agriculteurs)."
        ),
        "daily_routine": (
            "Tu commences ta matinée à l'aube pour profiter de la fraîcheur : récolte "
            "des courgettes et des tomates. Tu charges le camion pour le marché du "
            "vendredi. Retour aux champs : tu prépares un nouveau lit de semence, "
            "tu plantes des salades sous tunnel. L'après-midi, tu surveilles l'irrigation "
            "automatique et tu traites les pieds de tomates contre le mildiou avec "
            "du cuivre (autorisé en bio). En fin de journée, tu gères tes commandes "
            "en ligne pour la livraison de la semaine."
        ),
        "requirements_json": [
            {"type": "studies", "label": "Bac Pro Conduite des Productions Agricoles ou BPREA"},
            {"type": "studies", "label": "BTSA Productions Végétales — accessible après Bac"},
            {"type": "skill", "label": "Techniques culturales (semis, plantation, taille)"},
            {"type": "skill", "label": "Conduite de tracteur et petits matériels agricoles"},
            {"type": "quality", "label": "Résistance physique et aux conditions climatiques"},
            {"type": "quality", "label": "Autonomie et sens de l'observation des cultures"},
            {"type": "quality", "label": "Esprit entrepreneur (gestion d'exploitation)"},
        ],
        "prospects_text": (
            "1. Installation en exploitation propre. "
            "2. Responsable technique dans une coopérative agricole. "
            "3. Conseiller·ère agronomique auprès des agriculteurs."
        ),
        "median_salary_eur": 22000,
        "salary_range_json": {"min": 15000, "max": 45000, "source": "France Travail 2025"},
        "signals_json": {
            "passions": ["nature", "agriculture", "alimentation", "plein air"],
            "valeurs": ["nature", "autonomie", "durabilité", "alimentation saine"],
            "specialites": ["svt", "chimie"],
            "keywords": ["agriculture", "maraîchage", "légumes", "nature", "bio", "alimentation"],
        },
        "level_compatibility": ["college_3eme", "lycee_1ere_tle_pro", "lycee_2nde", "postbac"],
        "rome_code": "A1412",
        "sources_json": ["France Travail 2025", "ROME v4.0 A1412", "validation humaine 2026-06"],
    },
    {
        "slug": "garde-forestier",
        "name": "Garde forestier·ère / Agent ONF",
        "sector": "environnement",
        "description": (
            "Le·la garde forestier·ère (agent de l'Office National des Forêts ou des "
            "collectivités) surveille et gère les forêts publiques. Tu contrôles les "
            "coupes de bois pour qu'elles respectent les plans d'aménagement, tu surveilles "
            "les incendies et braconnage, tu organises des chantiers d'entretien. Tu es "
            "aussi un·e éducateur·rice : tu sensibilises le public à la forêt lors "
            "de visites. Ce métier est une vocation pour ceux qui aiment la nature et le "
            "plein air. Il est accessible via des concours de la fonction publique et "
            "demande des connaissances en sylviculture et en droit de l'environnement."
        ),
        "daily_routine": (
            "Ta journée commence en forêt : tu inspectes une parcelle après une tempête "
            "pour évaluer les dégâts et décider si une coupe de chablis est nécessaire. "
            "Tu notes tes observations dans ton carnet de terrain. Vers 10h, tu reçois "
            "un groupe scolaire que tu emmènes découvrir les essences d'arbres et les "
            "espèces protégées. L'après-midi, tu rédiges un rapport d'intervention et "
            "tu coordonnes une équipe de bûcherons pour un chantier de sylviculture "
            "prévu la semaine suivante."
        ),
        "requirements_json": [
            {"type": "studies", "label": "Bac Pro Forêt ou BTSA Gestion Forestière"},
            {"type": "studies", "label": "Concours d'agent technique forestier (Bac min.)"},
            {"type": "skill", "label": "Sylviculture et dendrologie (connaissance des arbres)"},
            {"type": "skill", "label": "Droit de l'environnement et police forestière"},
            {"type": "quality", "label": "Amour de la nature et aptitude au terrain"},
            {"type": "quality", "label": "Rigueur administrative et rédaction de rapports"},
            {"type": "quality", "label": "Pédagogie et communication avec le public"},
        ],
        "prospects_text": (
            "1. Chef de district ou responsable de massif forestier. "
            "2. Ingénieur·e des Eaux et Forêts. "
            "3. Expert·e en évaluation environnementale et biodiversité."
        ),
        "median_salary_eur": 26000,
        "salary_range_json": {"min": 22000, "max": 40000, "source": "Onisep 2025"},
        "signals_json": {
            "passions": ["nature", "forêt", "environnement", "plein air"],
            "valeurs": ["nature", "protection environnement", "service public", "durabilité"],
            "specialites": ["svt", "geographie"],
            "keywords": ["forêt", "nature", "environnement", "biodiversité", "sylviculture"],
        },
        "level_compatibility": ["college_3eme", "lycee_1ere_tle_pro", "lycee_2nde", "postbac"],
        "rome_code": "A1205",
        "sources_json": ["Onisep 2025", "ROME v4.0 A1205", "validation humaine 2026-06"],
    },
    # ── ENSEIGNEMENT / FORMATION (4) ─────────────────────────────────────────
    {
        "slug": "professeur-lycee",
        "name": "Professeur·e de lycée",
        "sector": "enseignement",
        "description": (
            "Le·la professeur·e de lycée enseigne une ou plusieurs matières à des élèves "
            "de Seconde, Première et Terminale. Tu transmets des connaissances, "
            "accompagnes les élèves dans leur orientation et prépares les classes aux "
            "examens (bac). Tu conçois tes cours, évalues les élèves, participes aux "
            "conseils de classe et collabores avec les familles. L'enseignement est un "
            "métier de vocation, avec beaucoup de liberté pédagogique mais aussi de "
            "responsabilités. Les enseignants fonctionnaires bénéficient d'une bonne "
            "stabilité de l'emploi. Le métier est accessible via les concours du CAPES "
            "ou de l'agrégation."
        ),
        "daily_routine": (
            "Ta matinée commence par deux heures de cours en Terminale sur les forces "
            "et la mécanique. Tu distribues un exercice, circulais dans les rangs pour "
            "aider les élèves bloqués. La pause est courte : tu corriges quelques copies "
            "dans la salle des profs. L'après-midi, tu as une heure libre pour préparer "
            "ton cours de demain, puis deux heures de cours en Seconde sur l'électricité. "
            "Tu participes en fin de journée à un conseil pédagogique sur le projet "
            "d'orientation de l'établissement."
        ),
        "requirements_json": [
            {
                "type": "studies",
                "label": "Master MEEF (Métiers de l'Enseignement) dans la discipline",
            },
            {"type": "studies", "label": "CAPES ou Agrégation (concours de la fonction publique)"},
            {"type": "skill", "label": "Maîtrise approfondie de la discipline enseignée"},
            {"type": "skill", "label": "Conception de séquences pédagogiques différenciées"},
            {"type": "quality", "label": "Pédagogie et patience avec les élèves"},
            {"type": "quality", "label": "Clarté d'expression et capacité à vulgariser"},
            {"type": "quality", "label": "Autorité bienveillante et gestion de classe"},
        ],
        "prospects_text": (
            "1. Professeur agrégé·e (plus haute qualification de l'enseignement secondaire). "
            "2. Inspecteur·rice de l'Éducation Nationale (IEN/IA-IPR). "
            "3. Chef·fe d'établissement (proviseur·e) après concours."
        ),
        "median_salary_eur": 32000,
        "salary_range_json": {"min": 26000, "max": 52000, "source": "Onisep 2025"},
        "signals_json": {
            "passions": ["éducation", "transmission", "jeunesse", "pédagogie"],
            "valeurs": ["service public", "transmission", "jeunesse", "égalité des chances"],
            "specialites": ["selon la discipline enseignée"],
            "keywords": ["enseignement", "éducation", "lycée", "professeur", "pédagogie"],
        },
        "level_compatibility": ["lycee_1ere_tle_general", "lycee_1ere_tle_techno", "postbac"],
        "rome_code": "K2107",
        "sources_json": ["Onisep 2025", "ROME v4.0 K2107", "validation humaine 2026-06"],
    },
    {
        "slug": "formateur-professionnel",
        "name": "Formateur·rice professionnel·le",
        "sector": "enseignement",
        "description": (
            "Le·la formateur·rice professionnel·le conçoit et anime des formations "
            "destinées à des adultes dans des organismes de formation, des entreprises "
            "ou des écoles de formation continue. Tu transmets des compétences "
            "techniques ou transversales (management, informatique, langues, sécurité). "
            "Tu dois maîtriser ton domaine d'expertise mais aussi les techniques "
            "pédagogiques pour adultes. Ce métier offre beaucoup d'indépendance "
            "(beaucoup de formateurs sont freelance) et la satisfaction de voir "
            "les apprenants progresser. Il est accessible à des professionnels "
            "expérimentés qui souhaitent transmettre leur savoir."
        ),
        "daily_routine": (
            "Ta journée commence par la préparation de ta salle et de tes supports "
            "pour une formation Excel de 2 jours pour des assistantes administratives. "
            "Tu lances la session en évaluant le niveau du groupe avec un quizz. "
            "Tu adaptes le contenu en temps réel : certains sont déjà à l'aise, d'autres "
            "peinent sur les formules. L'après-midi, tu animes des exercices pratiques "
            "et tu réponds aux questions. En fin de formation, tu distribues les "
            "évaluations à chaud et tu prépares le bilan pour le donneur d'ordre."
        ),
        "requirements_json": [
            {
                "type": "studies",
                "label": "Titre Professionnel Formateur pour Adultes (RNCP Niv. 5)",
            },
            {
                "type": "studies",
                "label": "Expertise métier dans le domaine enseigné (5+ ans d'expérience)",
            },
            {"type": "skill", "label": "Ingénierie pédagogique et conception de modules"},
            {
                "type": "skill",
                "label": "Animation de groupes (dynamique de groupe, gestion des profils)",
            },
            {"type": "quality", "label": "Pédagogie et adaptation aux niveaux des apprenants"},
            {"type": "quality", "label": "Enthousiasme et capacité à motiver"},
            {"type": "quality", "label": "Maîtrise du domaine enseigné"},
        ],
        "prospects_text": (
            "1. Responsable pédagogique ou directeur·rice d'organisme de formation. "
            "2. Concepteur·rice e-learning et digital learning. "
            "3. Consultant·e formateur·rice indépendant·e."
        ),
        "median_salary_eur": 32000,
        "salary_range_json": {"min": 24000, "max": 55000, "source": "France Travail 2025"},
        "signals_json": {
            "passions": ["transmission", "pédagogie", "formation", "partage"],
            "valeurs": ["transmission", "développement humain", "autonomie", "impact"],
            "specialites": ["selon la spécialité"],
            "keywords": ["formation", "pédagogie", "adultes", "enseignement", "transmission"],
        },
        "level_compatibility": ["lycee_1ere_tle_general", "lycee_1ere_tle_techno", "postbac"],
        "rome_code": "K2111",
        "sources_json": ["France Travail 2025", "ROME v4.0 K2111", "validation humaine 2026-06"],
    },
    {
        "slug": "auxiliaire-puericulture",
        "name": "Auxiliaire de puériculture",
        "sector": "enseignement",
        "description": (
            "L'auxiliaire de puériculture s'occupe des enfants de moins de 3 ans dans "
            "les crèches, haltes-garderies, PMI (Protection Maternelle et Infantile) et "
            "pouponnières. Tu prends soin de leur hygiène, de leur alimentation, tu "
            "organises des activités d'éveil et tu participes au développement psychomoteur "
            "et affectif de l'enfant. Tu travailles en étroite collaboration avec les "
            "éducateurs de jeunes enfants et les puériculteurs. Ce métier est très "
            "accessible dès la 3ème et offre une belle insertion. L'amour des bébés "
            "et des jeunes enfants est indispensable, tout comme la patience et la "
            "bienveillance."
        ),
        "daily_routine": (
            "Tu arrives le matin pour accueillir les enfants avec leurs parents. Tu "
            "prépares les biberons, changes les nourrissons et organises les activités "
            "de la matinée : peinture avec les mains, comptines, parcours moteur. "
            "Tu surveilles les repas et les siestes, en veillant à ce que chaque enfant "
            "se repose suffisamment. L'après-midi, tu animes des jeux d'éveil sensoriel "
            "et tu prépares les bilans de journée à transmettre aux parents. Tu range "
            "et nettoies les espaces de vie en fin de journée."
        ),
        "requirements_json": [
            {
                "type": "studies",
                "label": "DEAP (Diplôme d'État d'Auxiliaire de Puériculture) — accessible dès 3ème",
            },
            {"type": "studies", "label": "CAP AEPE (Accompagnant Éducatif Petite Enfance)"},
            {"type": "skill", "label": "Soins de base aux nourrissons et jeunes enfants"},
            {"type": "skill", "label": "Techniques d'éveil psychomoteur et sensoriel"},
            {"type": "quality", "label": "Patience et douceur avec les tout-petits"},
            {"type": "quality", "label": "Observation et vigilance (sécurité des enfants)"},
            {"type": "quality", "label": "Communication avec les parents"},
        ],
        "prospects_text": (
            "1. Éducateur·rice de jeunes enfants (EJE) après 3 ans de formation. "
            "2. Puériculteur·rice (infirmier·ère spécialisé·e petite enfance). "
            "3. Directeur·rice de crèche après expérience et formation complémentaire."
        ),
        "median_salary_eur": 22000,
        "salary_range_json": {"min": 19000, "max": 28000, "source": "Onisep 2025"},
        "signals_json": {
            "passions": ["enfants", "petite enfance", "éveil", "éducation"],
            "valeurs": ["bienveillance", "enfance", "développement", "soin"],
            "specialites": ["svt", "sciences sociales"],
            "keywords": ["petite enfance", "crèche", "enfants", "bébés", "éveil", "puériculture"],
        },
        "level_compatibility": ["college_3eme", "lycee_1ere_tle_pro", "lycee_2nde"],
        "rome_code": "J1303",
        "sources_json": ["Onisep 2025", "ROME v4.0 J1303", "validation humaine 2026-06"],
    },
    {
        "slug": "conseiller-orientation-psychologue",
        "name": "Psychologue de l'Éducation Nationale",
        "sector": "enseignement",
        "description": (
            "Le·la psychologue de l'Éducation Nationale (PsyEN) accompagne les élèves "
            "en difficulté scolaire ou personnelle. Tu réalises des bilans psychologiques, "
            "aides les élèves à construire leur projet d'orientation, et soutiens les "
            "familles. Tu collabores avec les enseignants, les médecins scolaires et les "
            "services sociaux. Ce métier est particulièrement utile pour les élèves "
            "en situation de handicap, d'anxiété scolaire ou de questionnements sur leur "
            "avenir. Tu interviens dans les lycées, collèges et CIO (Centres d'Information "
            "et d'Orientation). C'est un métier engageant socialement, à l'intersection "
            "de la psychologie et de l'éducation."
        ),
        "daily_routine": (
            "Ta matinée commence par deux entretiens d'orientation avec des élèves de "
            "Terminale : l'un hésite entre médecine et ingénierie, l'autre ne sait pas "
            "du tout ce qu'il veut faire. Tu les écoutes, explores leurs intérêts et "
            "leurs représentations des métiers. L'après-midi, tu administres un bilan "
            "cognitif à un élève de CM2 suspecté de haut potentiel, puis tu participes "
            "à une équipe éducative avec l'enseignant, les parents et le médecin scolaire "
            "pour un enfant en grande difficulté."
        ),
        "requirements_json": [
            {"type": "studies", "label": "Master 2 Psychologie + Master MEEF Psychologie de l'EN"},
            {"type": "studies", "label": "Concours PsyEN (CAPEJS ou EDO selon spécialité)"},
            {"type": "skill", "label": "Passation et interprétation de tests psychologiques"},
            {"type": "skill", "label": "Entretiens cliniques et techniques d'écoute active"},
            {"type": "quality", "label": "Empathie et neutralité bienveillante"},
            {"type": "quality", "label": "Confidentialité et éthique professionnelle"},
            {"type": "quality", "label": "Travail en réseau pluridisciplinaire"},
        ],
        "prospects_text": (
            "1. Psychologue clinicien·ne en libéral ou en institution. "
            "2. Conseiller·ère d'orientation en CIO ou en entreprise. "
            "3. Formateur·rice ou chercheur·se en psychologie de l'éducation."
        ),
        "median_salary_eur": 34000,
        "salary_range_json": {"min": 28000, "max": 50000, "source": "Onisep 2025"},
        "signals_json": {
            "passions": ["psychologie", "écoute", "orientation", "éducation"],
            "valeurs": ["écoute", "empathie", "service public", "égalité des chances"],
            "specialites": ["sciences sociales", "philosophie", "svt"],
            "keywords": ["psychologie", "orientation", "éducation", "scolaire", "accompagnement"],
        },
        "level_compatibility": ["lycee_1ere_tle_general", "postbac"],
        "rome_code": "K1104",
        "sources_json": ["Onisep 2025", "ROME v4.0 K1104", "validation humaine 2026-06"],
    },
    # ── SÉCURITÉ / DÉFENSE / JURIDIQUE (4) ───────────────────────────────────
    {
        "slug": "agent-securite-privee",
        "name": "Agent·e de sécurité privée",
        "sector": "securite",
        "description": (
            "L'agent·e de sécurité privée surveille et protège des personnes, des biens "
            "et des lieux : centres commerciaux, entreprises, événements, aéroports. "
            "Tu contrôles les accès, surveilles les écrans de vidéosurveillance, effectues "
            "des rondes et interviens en cas d'incident. Ce métier est accessible "
            "rapidement (formation de quelques semaines) et recrute massivement. Il peut "
            "être exigeant physiquement et psychologiquement (nuits, gestion de conflits), "
            "mais offre de réelles opportunités d'évolution. La carte professionnelle "
            "délivrée par le CNAPS est obligatoire. C'est un premier emploi possible "
            "dès la sortie du lycée."
        ),
        "daily_routine": (
            "Tu prends ton poste en début de service et consultes le cahier de "
            "consignes. Tu effectues une ronde du périmètre, vérifies que toutes les "
            "issues sont sécurisées. À l'accueil, tu contrôles les badges des employés "
            "et visiteurs. En milieu d'après-midi, une alarme se déclenche dans une "
            "zone : tu interviens, constate qu'il s'agit d'une fausse alerte (bris de "
            "vitre accidentel) et rédiges le rapport d'incident. Tu transmets les "
            "consignes au collègue qui prend le relais."
        ),
        "requirements_json": [
            {
                "type": "studies",
                "label": "CQP Agent de Prévention et de Sécurité (APS) — formation courte",
            },
            {"type": "studies", "label": "Carte professionnelle CNAPS obligatoire"},
            {"type": "skill", "label": "Techniques de surveillance et de ronde"},
            {"type": "skill", "label": "Gestion des conflits et premiers secours (SST)"},
            {"type": "quality", "label": "Vigilance et sens de l'observation"},
            {"type": "quality", "label": "Calme et maîtrise de soi face au stress"},
            {"type": "quality", "label": "Rigueur et respect des procédures"},
        ],
        "prospects_text": (
            "1. Chef de poste ou agent de sécurité incendie (SSIAP). "
            "2. Responsable d'agence de sécurité. "
            "3. Reconversion en police nationale ou gendarmerie."
        ),
        "median_salary_eur": 22000,
        "salary_range_json": {"min": 19000, "max": 32000, "source": "France Travail 2025"},
        "signals_json": {
            "passions": ["sécurité", "protection", "ordre", "vigilance"],
            "valeurs": ["protection", "ordre", "service public", "responsabilité"],
            "specialites": ["eps"],
            "keywords": ["sécurité", "surveillance", "protection", "garde", "agent"],
        },
        "level_compatibility": ["college_3eme", "lycee_1ere_tle_pro", "lycee_2nde", "postbac"],
        "rome_code": "K2503",
        "sources_json": ["France Travail 2025", "ROME v4.0 K2503", "validation humaine 2026-06"],
    },
    {
        "slug": "pompier-sapeur",
        "name": "Sapeur-pompier professionnel·le",
        "sector": "securite",
        "description": (
            "Le·la sapeur-pompier professionnel·le lutte contre les incendies, porte "
            "secours aux victimes d'accidents, intervient lors de catastrophes naturelles "
            "et réalise des opérations de secours à personnes (accidents de la route, "
            "malaises). Tu es à la fois pompier, secouriste (tu peux pratiquer des gestes "
            "médicaux de premier niveau), et parfois plongeur ou technicien hauteur. "
            "C'est un métier de passion et d'engagement au service des citoyens, avec "
            "une forte cohésion d'équipe. L'accès se fait par concours. La condition "
            "physique est une exigence non négociable."
        ),
        "daily_routine": (
            "Tu prends garde à la caserne avec ton équipe. La matinée commence par "
            "la vérification du matériel et des véhicules : tout doit être opérationnel "
            "à tout moment. Une alerte sonne : intervention pour un accident de la route. "
            "En 90 secondes le camion est parti. Sur place, tu prends en charge une "
            "victime, assures les premiers secours et coordonnes avec le SAMU. De retour "
            "à la caserne, tu participes à un exercice de sauvetage déblaiement. "
            "Les gardes durent 24 heures."
        ),
        "requirements_json": [
            {
                "type": "studies",
                "label": "Concours de sapeur-pompier professionnel (Bac min. requis)",
            },
            {"type": "studies", "label": "Formation initiale de 6 mois à l'ENSOSP"},
            {"type": "skill", "label": "Techniques de lutte contre l'incendie"},
            {"type": "skill", "label": "Secours à victimes (SAV) et défibrillation"},
            {"type": "quality", "label": "Excellente condition physique"},
            {"type": "quality", "label": "Sang-froid et prise de décision rapide"},
            {"type": "quality", "label": "Esprit d'équipe et solidarité"},
        ],
        "prospects_text": (
            "1. Sergent, lieutenant et progression dans la hiérarchie militaire. "
            "2. Spécialisation (plongeur, technicien feux de forêt, GRIMP). "
            "3. Officier sapeur-pompier (après concours interne)."
        ),
        "median_salary_eur": 28000,
        "salary_range_json": {"min": 24000, "max": 45000, "source": "Onisep 2025"},
        "signals_json": {
            "passions": ["secours", "sport", "protection", "engagement"],
            "valeurs": ["courage", "service public", "solidarité", "protection des autres"],
            "specialites": ["eps", "svt"],
            "keywords": ["pompier", "secours", "incendie", "urgences", "sécurité civile"],
        },
        "level_compatibility": [
            "college_3eme",
            "lycee_1ere_tle_pro",
            "lycee_2nde",
            "lycee_1ere_tle_general",
            "postbac",
        ],
        "rome_code": "K2401",
        "sources_json": ["Onisep 2025", "ROME v4.0 K2401", "validation humaine 2026-06"],
    },
    {
        "slug": "juriste-entreprise",
        "name": "Juriste d'entreprise",
        "sector": "securite",
        "description": (
            "Le·la juriste d'entreprise conseille et protège légalement l'organisation "
            "qui l'emploie. Tu rédiges et analyses des contrats, gères les litiges, "
            "veilles au respect des réglementations, et conseilles la direction sur "
            "les risques juridiques. Tu peux être spécialisé·e en droit des affaires, "
            "droit social (droit du travail), droit de la propriété intellectuelle, "
            "ou droit de la conformité (RGPD, compliance). C'est un métier qui combine "
            "rigueur intellectuelle, capacité de rédaction et sens du conseil stratégique. "
            "Il est présent dans toutes les grandes entreprises et les cabinets d'avocats."
        ),
        "daily_routine": (
            "Ta matinée commence par la revue d'un contrat de partenariat avec une "
            "entreprise étrangère : tu repères les clauses problématiques (limitation "
            "de responsabilité, juridiction compétente en cas de litige). Tu rédiges "
            "tes annotations et proposes des modifications. À 11h, réunion avec la "
            "direction pour expliquer les risques d'un projet d'acquisition. L'après-midi, "
            "tu travailles sur la mise à jour des clauses RGPD des contrats clients "
            "et tu formes l'équipe commerciale sur les nouvelles règles."
        ),
        "requirements_json": [
            {
                "type": "studies",
                "label": "Master 2 Droit des Affaires, Droit Social ou Droit des Contrats",
            },
            {"type": "studies", "label": "Doubles compétences droit + gestion très recherchées"},
            {"type": "skill", "label": "Rédaction juridique et analyse contractuelle"},
            {"type": "skill", "label": "Veille réglementaire dans son domaine de spécialité"},
            {"type": "quality", "label": "Rigueur analytique et logique juridique"},
            {"type": "quality", "label": "Capacité à vulgariser le droit pour des non-juristes"},
            {"type": "quality", "label": "Discrétion et confidentialité absolue"},
        ],
        "prospects_text": (
            "1. Responsable juridique ou directeur·rice juridique. "
            "2. Avocat·e d'affaires en cabinet après passage au barreau. "
            "3. Expert·e conformité (compliance officer) — très recherché."
        ),
        "median_salary_eur": 48000,
        "salary_range_json": {"min": 35000, "max": 85000, "source": "Apec 2025"},
        "signals_json": {
            "passions": ["droit", "argumentation", "justice", "analyse"],
            "valeurs": ["justice", "rigueur", "responsabilité", "éthique"],
            "specialites": ["francais", "histoire", "economie", "philosophie"],
            "keywords": ["droit", "juridique", "contrat", "loi", "compliance", "entreprise"],
        },
        "level_compatibility": ["lycee_1ere_tle_general", "postbac"],
        "rome_code": "K1903",
        "sources_json": ["Apec 2025", "ROME v4.0 K1903", "validation humaine 2026-06"],
    },
    {
        "slug": "gendarme",
        "name": "Gendarme",
        "sector": "securite",
        "description": (
            "Le·la gendarme est un·e militaire qui assure les missions de sécurité "
            "publique, de maintien de l'ordre et d'investigation judiciaire, "
            "principalement dans les zones rurales et péri-urbaines. Tu patrouilles, "
            "verbalises, enquêtes sur des affaires criminelles, et interviens lors "
            "d'urgences. La gendarmerie propose de nombreuses spécialités : brigade "
            "criminelle, brigade motorisée, groupe d'intervention (GIGN), police "
            "judiciaire. Ce métier offre une carrière stable, un logement de fonction, "
            "et un fort sentiment d'utilité. L'accès se fait par concours à différents "
            "niveaux (gendarme, officier)."
        ),
        "daily_routine": (
            "Tu prends le service en brigade : briefing sur les événements de la nuit, "
            "répartition des missions. Tu pars en patrouille avec ton binôme : contrôle "
            "routier sur la nationale, vérification d'une plainte pour vol. L'après-midi, "
            "tu reçois une victime de violences domestiques pour prendre sa déposition "
            "avec toute la bienveillance nécessaire. Tu rédigis ensuite le procès-verbal "
            "d'audition et transmets le dossier au parquet. En soirée, tu pourrais avoir "
            "une intervention sur un accident de la route."
        ),
        "requirements_json": [
            {
                "type": "studies",
                "label": "Concours de gendarme adjoint volontaire (GAV) — dès 17 ans, sans bac",
            },
            {"type": "studies", "label": "Concours gendarme sous-officier — Bac requis"},
            {"type": "skill", "label": "Techniques d'investigation et de police judiciaire"},
            {"type": "skill", "label": "Rédaction d'actes judiciaires (PV, rapports)"},
            {"type": "quality", "label": "Sang-froid et autorité naturelle"},
            {"type": "quality", "label": "Sens du service public et intégrité"},
            {"type": "quality", "label": "Condition physique (tests obligatoires au concours)"},
        ],
        "prospects_text": (
            "1. Brigadier, maréchal des logis-chef, adjudant. "
            "2. Officier de gendarmerie (concours OAGN après expérience). "
            "3. Spécialisation GIGN, PJ, cyber, ou IRCGN (expertise technique)."
        ),
        "median_salary_eur": 28000,
        "salary_range_json": {"min": 23000, "max": 48000, "source": "Onisep 2025"},
        "signals_json": {
            "passions": ["justice", "service public", "sport", "enquête"],
            "valeurs": ["justice", "ordre", "service public", "engagement", "protection"],
            "specialites": ["eps", "histoire", "francais"],
            "keywords": [
                "gendarmerie",
                "sécurité",
                "police judiciaire",
                "service public",
                "enquête",
            ],
        },
        "level_compatibility": [
            "college_3eme",
            "lycee_1ere_tle_pro",
            "lycee_2nde",
            "lycee_1ere_tle_general",
            "postbac",
        ],
        "rome_code": "K2503",
        "sources_json": ["Onisep 2025", "ROME v4.0 K2503", "validation humaine 2026-06"],
    },
    # ── ARTS / COMMUNICATION (1 additional to reach 6 minimum) ──────────────
    {
        "slug": "animateur-socioculturel",
        "name": "Animateur·rice socioculturel·le",
        "sector": "arts",
        "description": (
            "L'animateur·rice socioculturel·le conçoit et anime des activités culturelles, "
            "sportives et de loisirs pour des publics variés : enfants, adolescents, adultes, "
            "personnes âgées. Tu travailles dans des centres de loisirs, des MJC (Maisons "
            "des Jeunes et de la Culture), des centres sociaux, des clubs de vacances ou "
            "des associations. Tu organises des ateliers créatifs, des sorties, des événements "
            "festifs, des projets collectifs. Ce métier est très polyvalent et demande "
            "une grande énergie, de la créativité et un fort sens du collectif. Il est "
            "accessible dès le Bac via le BPJEPS et offre une belle opportunité de "
            "travailler avec des personnes de tous âges."
        ),
        "daily_routine": (
            "Ta journée commence à la MJC par la préparation des ateliers de la journée. "
            "Tu accueilles un groupe d'adolescents pour un atelier rap : tu leur expliques "
            "les bases de l'écriture de texte, tu les laisses créer et tu les enregistres "
            "avec un micro. L'après-midi, tu animes une sortie cinéma pour des seniors "
            "du quartier. En soirée, tu prépares le programme de la semaine prochaine "
            "et tu contactes les partenaires locaux (associations, artistes) pour "
            "co-construire le festival de quartier du mois prochain."
        ),
        "requirements_json": [
            {"type": "studies", "label": "BPJEPS Animation culturelle — accessible après Bac"},
            {
                "type": "studies",
                "label": "DEUST Animation et Gestion des Activités Physiques, Sportives et Sociales",
            },
            {
                "type": "skill",
                "label": "Conception et animation d'activités pour différents publics",
            },
            {"type": "skill", "label": "Gestion de projets culturels ou sportifs"},
            {"type": "quality", "label": "Énergie et enthousiasme communicatifs"},
            {"type": "quality", "label": "Créativité et sens de l'improvisation"},
            {"type": "quality", "label": "Écoute des besoins du public et adaptation"},
        ],
        "prospects_text": (
            "1. Directeur·rice de centre de loisirs ou de MJC. "
            "2. Coordonnateur·rice de projets culturels en collectivité. "
            "3. Formateur·rice en animation ou DEJEPS (encadrement)."
        ),
        "median_salary_eur": 22000,
        "salary_range_json": {"min": 18000, "max": 32000, "source": "France Travail 2025"},
        "signals_json": {
            "passions": ["animation", "culture", "créativité", "contact humain"],
            "valeurs": ["solidarité", "créativité", "partage", "inclusion"],
            "specialites": ["arts", "eps", "sciences sociales"],
            "keywords": ["animation", "culture", "loisirs", "jeunesse", "créativité", "social"],
        },
        "level_compatibility": [
            "college_3eme",
            "lycee_1ere_tle_pro",
            "lycee_2nde",
            "lycee_1ere_tle_general",
            "postbac",
        ],
        "rome_code": "G1204",
        "sources_json": ["France Travail 2025", "ROME v4.0 G1204", "validation humaine 2026-06"],
    },
    # ── TRANSPORT / LOGISTIQUE / AUTRES (4) ──────────────────────────────────
    {
        "slug": "chauffeur-spl",
        "name": "Chauffeur·euse SPL (Super Poids Lourd)",
        "sector": "transport",
        "description": (
            "Le·la chauffeur·euse SPL (Super Poids Lourd) transporte des marchandises "
            "sur de longues distances au volant d'un camion articulé (44 tonnes). Tu "
            "assures la livraison à temps en respectant les réglementations sur les temps "
            "de conduite (tachygraphe) et les règles de sécurité routière. Tu charges "
            "et vérifies le chargement, tiens à jour les documents de transport, et "
            "effectues les vérifications de base du véhicule. Ce métier offre beaucoup "
            "d'autonomie et une bonne rémunération. Il est en tension de recrutement "
            "constant : les chauffeurs SPL sont très recherchés. La conduite de nuit "
            "est fréquente."
        ),
        "daily_routine": (
            "Tu prends le camion au dépôt à 5h du matin après avoir vérifié les niveaux "
            "et les éclairages. Tu charges la remorque avec les palettes destinées à "
            "trois clients différents. Sur la route, tu respectes scrupuleusement les "
            "temps de conduite et pauses réglementaires (suivi par le tachygraphe). "
            "Tu livres les clients, fais signer les bons de livraison, et récupères "
            "les palettes vides. Tu rentres au dépôt en fin d'après-midi et remets ton "
            "véhicule en état."
        ),
        "requirements_json": [
            {"type": "studies", "label": "Permis C + CE (poids lourd et semi-remorque)"},
            {
                "type": "studies",
                "label": "FCO (Formation Continue Obligatoire) et carte conducteur",
            },
            {"type": "skill", "label": "Conduite en sécurité de véhicules articulés"},
            {"type": "skill", "label": "Connaissance de la réglementation transport (RSE)"},
            {"type": "quality", "label": "Sens de l'orientation et gestion du temps"},
            {"type": "quality", "label": "Fiabilité et sens des responsabilités"},
            {"type": "quality", "label": "Résistance à la fatigue et vigilance continue"},
        ],
        "prospects_text": (
            "1. Chauffeur·euse grand routier ou international. "
            "2. Chef de parc ou responsable d'exploitation transport. "
            "3. Formateur·rice à la conduite ou contrôleur·euse technique véhicules."
        ),
        "median_salary_eur": 28000,
        "salary_range_json": {"min": 23000, "max": 40000, "source": "France Travail 2025"},
        "signals_json": {
            "passions": ["conduite", "voyage", "autonomie", "transport"],
            "valeurs": ["autonomie", "liberté", "responsabilité", "efficacité"],
            "specialites": ["mathematiques", "geographie"],
            "keywords": ["transport", "camion", "chauffeur", "logistique", "livraison"],
        },
        "level_compatibility": ["college_3eme", "lycee_1ere_tle_pro", "lycee_2nde"],
        "rome_code": "N4101",
        "sources_json": ["France Travail 2025", "ROME v4.0 N4101", "validation humaine 2026-06"],
    },
    {
        "slug": "technicien-aeronautique",
        "name": "Technicien·ne de maintenance aéronautique",
        "sector": "transport",
        "description": (
            "Le·la technicien·ne de maintenance aéronautique assure la navigabilité des "
            "avions en effectuant les révisions, les réparations et les contrôles "
            "imposés par les réglementations aériennes. Tu travailles sur des "
            "systèmes mécaniques, électriques, avioniques et hydrauliques des aéronefs. "
            "Ce métier s'exerce dans des compagnies aériennes, des MRO (centres de "
            "maintenance), ou chez des constructeurs comme Airbus. C'est un secteur "
            "technologiquement très exigeant, réglementé et valorisant. "
            "La licence EASA Part-66 est le sésame indispensable. "
            "Les débouchés internationaux sont nombreux."
        ),
        "daily_routine": (
            "Tu arrives en hangar à 6h du matin pour l'inspection journalière d'un "
            "A320 avant son premier vol. Tu vérifies les fluides, les trains d'atterrissage, "
            "les commandes de vol et signes le carnet de bord. Lors d'une visite de "
            "maintenance programmée, tu démontes un moteur avec ton équipe, remplaces "
            "les pièces conformément aux SB (Service Bulletins) et effectues les "
            "tests fonctionnels avant la remise en service. Tu signes et tu certifies "
            "chaque intervention réalisée sous ta responsabilité."
        ),
        "requirements_json": [
            {"type": "studies", "label": "Bac Pro Aéronautique ou MAVA orientation aéro"},
            {"type": "studies", "label": "BTS Aéronautique ou formation agréée EASA Part-147"},
            {
                "type": "skill",
                "label": "Licence EASA Part-66 (catégorie B1 mécanique ou B2 avionique)",
            },
            {"type": "skill", "label": "Documentation technique aéronautique (AMM, SRM)"},
            {
                "type": "quality",
                "label": "Rigueur absolue (la sécurité aérienne ne tolère aucune erreur)",
            },
            {"type": "quality", "label": "Habileté manuelle et sens du détail"},
            {"type": "quality", "label": "Travail en équipe et communication claire"},
        ],
        "prospects_text": (
            "1. Technicien·ne confirmé·e et chef d'équipe maintenance. "
            "2. Ingénieur·e de navigabilité continue. "
            "3. Instructeur·rice dans un centre de formation agréé EASA."
        ),
        "median_salary_eur": 38000,
        "salary_range_json": {"min": 28000, "max": 60000, "source": "Onisep 2025"},
        "signals_json": {
            "passions": ["aviation", "technologie", "précision", "mécanique"],
            "valeurs": ["rigueur", "sécurité", "excellence", "technique"],
            "specialites": ["physique", "mathematiques", "technologie"],
            "keywords": [
                "aéronautique",
                "avion",
                "maintenance",
                "technique",
                "sécurité",
                "aviation",
            ],
        },
        "level_compatibility": ["lycee_1ere_tle_pro", "lycee_1ere_tle_techno", "postbac"],
        "rome_code": "I1304",
        "sources_json": ["Onisep 2025", "ROME v4.0 I1304", "validation humaine 2026-06"],
    },
    {
        "slug": "controleur-de-gestion",
        "name": "Contrôleur·euse de gestion",
        "sector": "business",
        "description": (
            "Le·la contrôleur·euse de gestion analyse la performance financière de "
            "l'entreprise pour aider la direction à prendre de bonnes décisions. Tu "
            "construis les tableaux de bord, suis les budgets, analyses les écarts entre "
            "prévu et réalisé, et produis les reportings mensuels. Tu travailles en lien "
            "étroit avec tous les services (commercial, production, RH) pour comprendre "
            "les chiffres derrière les activités. C'est un métier stratégique qui "
            "demande une double compétence : maîtrise des chiffres ET compréhension "
            "du business. Il est présent dans toutes les grandes entreprises et évolue "
            "vers plus d'analytique et de data."
        ),
        "daily_routine": (
            "Ta matinée est consacrée à la clôture mensuelle : tu collectes les données "
            "des différents services, vérifies leur cohérence et calcules les indicateurs "
            "de performance (CA, marges, coûts). Tu construis ensuite le tableau de bord "
            "de la direction. L'après-midi, tu présentes les résultats du mois à ton "
            "directeur financier et tu identifies les écarts significatifs. Tu travailles "
            "aussi sur le budget de l'année suivante avec les managers opérationnels."
        ),
        "requirements_json": [
            {"type": "studies", "label": "Master CCA, contrôle de gestion ou finance"},
            {"type": "studies", "label": "École de commerce avec spécialisation finance/gestion"},
            {"type": "skill", "label": "Excel avancé, Power BI ou outils BI similaires"},
            {"type": "skill", "label": "Comptabilité analytique et budgétisation"},
            {"type": "quality", "label": "Rigueur analytique et esprit de synthèse"},
            {
                "type": "quality",
                "label": "Curiosité pour comprendre le business au-delà des chiffres",
            },
            {"type": "quality", "label": "Communication claire avec des non-financiers"},
        ],
        "prospects_text": (
            "1. Responsable contrôle de gestion. "
            "2. Directeur·rice financier·ère (DAF). "
            "3. Business analyst ou consultant finance."
        ),
        "median_salary_eur": 42000,
        "salary_range_json": {"min": 32000, "max": 70000, "source": "Apec 2025"},
        "signals_json": {
            "passions": ["chiffres", "analyse", "gestion", "finance"],
            "valeurs": ["rigueur", "performance", "stratégie", "impact"],
            "specialites": ["mathematiques", "economie", "gestion"],
            "keywords": [
                "finance",
                "contrôle de gestion",
                "budget",
                "analyse",
                "performance",
                "entreprise",
            ],
        },
        "level_compatibility": ["lycee_1ere_tle_general", "lycee_1ere_tle_techno", "postbac"],
        "rome_code": "M1204",
        "sources_json": ["Apec 2025", "ROME v4.0 M1204", "validation humaine 2026-06"],
    },
    {
        "slug": "conducteur-bus",
        "name": "Conducteur·rice de bus / tramway",
        "sector": "transport",
        "description": (
            "Le·la conducteur·rice de bus ou de tramway assure le transport des voyageurs "
            "en toute sécurité sur des lignes urbaines ou interurbaines. Tu conduis, "
            "vérifies ton véhicule avant le départ, accueilles les passagers, leur "
            "indiques les arrêts et gères d'éventuels incidents à bord. Tu travailles "
            "pour des réseaux de transport public (RATP, TCL, réseau Astuce…) ou des "
            "entreprises de transport scolaire ou touristique. Les horaires sont "
            "décalés (nuits, week-ends, jours fériés) mais les conditions d'emploi "
            "dans le public sont stables avec de bonnes protections sociales. "
            "C'est un métier accessible rapidement avec le permis D."
        ),
        "daily_routine": (
            "Tu prends ton service au dépôt, vérifies les niveaux du bus et son état "
            "général. Tu effectues ton premier trajet en respectant horaires et arrêts. "
            "Tu accueilles les passagers, vérifies les titres de transport et les aides "
            "si besoin (personnes âgées, valises). Entre deux services, tu fais une "
            "pause au terminus. Tu gères calmement les situations de retard liées à "
            "la circulation et tu informes les voyageurs. En fin de service, tu "
            "ramènes le véhicule au dépôt et transmets les incidents au chef de parc."
        ),
        "requirements_json": [
            {"type": "studies", "label": "Permis D (transport en commun) + FIMO Voyageurs"},
            {
                "type": "studies",
                "label": "Titre Professionnel Conducteur·rice de Transport en Commun sur Route",
            },
            {"type": "skill", "label": "Conduite sécurisée d'un véhicule articulé"},
            {"type": "skill", "label": "Gestion des situations d'urgence à bord"},
            {"type": "quality", "label": "Calme et maîtrise de soi en toutes circonstances"},
            {"type": "quality", "label": "Sens du service et amabilité avec les voyageurs"},
            {"type": "quality", "label": "Ponctualité et fiabilité"},
        ],
        "prospects_text": (
            "1. Conducteur·rice de tramway ou de métro. "
            "2. Chef de bord ou conducteur·rice-receveur senior. "
            "3. Formateur·rice conduite ou inspecteur·rice de ligne."
        ),
        "median_salary_eur": 25000,
        "salary_range_json": {"min": 21000, "max": 34000, "source": "France Travail 2025"},
        "signals_json": {
            "passions": ["conduite", "service public", "contact humain", "transport"],
            "valeurs": ["service public", "responsabilité", "fiabilité", "contact humain"],
            "specialites": ["geographie"],
            "keywords": ["bus", "transport", "conduite", "service public", "voyageurs", "urbain"],
        },
        "level_compatibility": ["college_3eme", "lycee_1ere_tle_pro", "lycee_2nde", "postbac"],
        "rome_code": "N4102",
        "sources_json": ["France Travail 2025", "ROME v4.0 N4102", "validation humaine 2026-06"],
    },
    {
        "slug": "assistant-social",
        "name": "Assistant·e de service social",
        "sector": "social",
        "description": (
            "L'assistant·e de service social aide les personnes en difficulté à surmonter "
            "leurs problèmes sociaux : pauvreté, violences, exclusion, handicap, dépendance. "
            "Tu évalues les situations, orientes vers les aides existantes (CAF, logements "
            "sociaux, aides alimentaires), et fais le lien entre les personnes et les "
            "institutions. Tu peux exercer dans des mairies, des hôpitaux, des caisses "
            "d'allocations familiales, des entreprises (service social du travail), ou "
            "des associations. C'est un métier exigeant émotionnellement mais "
            "profondément utile socialement. La formation DEASS est accessible après le Bac."
        ),
        "daily_routine": (
            "Ta matinée commence par la réception d'une famille en grande précarité : "
            "tu écoutes leur situation, identifies les droits auxquels ils peuvent "
            "prétendre (RSA, APL, aide alimentaire) et construis avec eux un plan d'action. "
            "Vers 10h, tu reçois un jeune en rupture familiale que tu orientes vers un "
            "hébergement d'urgence. L'après-midi, tu fais une visite à domicile pour "
            "évaluer la situation d'un enfant signalé, puis tu rédiges ton rapport "
            "pour le conseil départemental."
        ),
        "requirements_json": [
            {
                "type": "studies",
                "label": "DEASS (Diplôme d'État d'Assistant·e de Service Social) — 3 ans",
            },
            {"type": "skill", "label": "Connaissance du droit social et des dispositifs d'aide"},
            {
                "type": "skill",
                "label": "Conduite d'entretiens sociaux et évaluation des situations",
            },
            {"type": "quality", "label": "Empathie et distance professionnelle"},
            {"type": "quality", "label": "Résistance aux situations émotionnellement difficiles"},
            {"type": "quality", "label": "Organisation et rigueur administrative"},
        ],
        "prospects_text": (
            "1. Responsable de service social ou coordinateur·rice d'équipe. "
            "2. Conseiller·ère technique en travail social. "
            "3. Formateur·rice en école du travail social."
        ),
        "median_salary_eur": 27000,
        "salary_range_json": {"min": 23000, "max": 38000, "source": "Onisep 2025"},
        "signals_json": {
            "passions": ["aider les autres", "justice sociale", "psychologie", "droit"],
            "valeurs": ["solidarité", "justice sociale", "engagement", "humanité"],
            "specialites": ["sciences sociales", "philosophie"],
            "keywords": [
                "social",
                "travail social",
                "aide",
                "inclusion",
                "précarité",
                "accompagnement",
            ],
        },
        "level_compatibility": [
            "lycee_1ere_tle_general",
            "lycee_1ere_tle_techno",
            "lycee_1ere_tle_pro",
            "postbac",
        ],
        "rome_code": "K1201",
        "sources_json": ["Onisep 2025", "ROME v4.0 K1201", "validation humaine 2026-06"],
    },
]
