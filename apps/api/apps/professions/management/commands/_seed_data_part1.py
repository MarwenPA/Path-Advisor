"""Seed data part 1/3 — Santé/Social (10) + Sciences/Tech (8)."""

PROFESSIONS_PART1 = [
    # ── SANTÉ / SOCIAL / MÉDICO-SOCIAL (10) ─────────────────────────────────
    {
        "slug": "aide-soignant",
        "name": "Aide-soignant·e",
        "sector": "santé",
        "description": (
            "L'aide-soignant·e accompagne les patients dans les actes essentiels de la vie "
            "quotidienne : toilette, habillage, alimentation, déplacement. Tu travailles en "
            "étroite collaboration avec les infirmiers et les médecins pour assurer le confort "
            "et la sécurité des personnes soignées. Tu peux exercer dans des hôpitaux, des "
            "maisons de retraite (EHPAD), des services de soins à domicile, ou des cliniques. "
            "Ce métier demande une grande résistance physique et émotionnelle, mais il est "
            "profondément humain. Chaque jour, tu contribues directement au bien-être de "
            "personnes vulnérables : personnes âgées, malades, ou en situation de handicap. "
            "Tu observes l'état de santé des patients et transmets tes observations à l'équipe "
            "infirmière. La bienveillance, la discrétion et le sens du service sont des qualités "
            "indispensables pour réussir dans ce métier."
        ),
        "daily_routine": (
            "Tu commences ta matinée en prenant connaissance du dossier des patients dont tu "
            "as la charge. Tu assistes ensuite les patients pour la toilette et l'habillage, "
            "en respectant leur dignité et leur rythme. À midi, tu les accompagnes au repas ou "
            "tu leur apportes leur plateau. L'après-midi, tu effectues des soins de confort, "
            "changes de position pour prévenir les escarres, et tu participes aux transmissions "
            "d'équipe. Tu termines ta journée en notant dans le dossier de soin tout ce que tu "
            "as observé sur l'état des patients."
        ),
        "requirements_json": [
            {"type": "studies", "label": "DEAS (Diplôme d'État d'Aide-Soignant·e) — 1 an"},
            {"type": "studies", "label": "Accessible depuis le CAP AEPE ou le Bac Pro ASSP"},
            {"type": "studies", "label": "Possible après une 3ème via apprentissage"},
            {
                "type": "skill",
                "label": "Techniques de soins de base (toilette, pansements simples)",
            },
            {"type": "skill", "label": "Observation et transmission d'informations cliniques"},
            {"type": "quality", "label": "Empathie et bienveillance"},
            {"type": "quality", "label": "Résistance physique et émotionnelle"},
            {"type": "quality", "label": "Travail en équipe pluridisciplinaire"},
        ],
        "prospects_text": (
            "1. Infirmier·ère (après formation IDE 3 ans) via la passerelle AS→IDE. "
            "2. Aide-soignant·e coordinateur·rice en EHPAD. "
            "3. Auxiliaire de puériculture ou accompagnant éducatif et social (AES). "
            "4. Formation continue vers ambulancier·ère ou assistant·e de soins en gérontologie."
        ),
        "median_salary_eur": 24000,
        "salary_range_json": {"min": 21000, "max": 32000, "source": "Onisep 2025"},
        "signals_json": {
            "passions": ["aider les autres", "médecine", "contact humain", "bienveillance"],
            "valeurs": ["utilité sociale", "solidarité", "service aux autres", "empathie"],
            "specialites": ["svt", "biologie"],
            "keywords": ["soin", "patient", "hôpital", "santé", "accompagnement", "soignant"],
        },
        "level_compatibility": [
            "college_3eme",
            "lycee_1ere_tle_pro",
            "lycee_1ere_tle_techno",
            "postbac",
        ],
        "rome_code": "J1502",
        "sources_json": ["Onisep 2025", "ROME v4.0 J1502", "validation humaine 2026-06"],
    },
    {
        "slug": "infirmier-de-bloc-operatoire",
        "name": "Infirmier·ère de bloc opératoire",
        "sector": "santé",
        "description": (
            "L'infirmier·ère de bloc opératoire (IBODE) est un·e professionnel·le de santé "
            "spécialisé·e qui intervient avant, pendant et après les opérations chirurgicales. "
            "Tu prépares la salle d'opération, tu instrumentes le chirurgien en lui passant "
            "les outils nécessaires, et tu assures la sécurité et l'asepsie tout au long de "
            "l'intervention. Ce métier exige une précision absolue, une grande résistance au "
            "stress et une connaissance approfondie des protocoles chirurgicaux. Tu peux exercer "
            "dans des hôpitaux publics, des cliniques privées ou des centres chirurgicaux "
            "ambulatoires. C'est un métier technique et valorisant, au cœur de l'acte médical. "
            "La formation IBODE dure deux ans après le diplôme infirmier de base et ouvre des "
            "perspectives de carrière dans toutes les spécialités chirurgicales, de l'orthopédie "
            "à la chirurgie cardiaque, en passant par la neurochirurgie."
        ),
        "daily_routine": (
            "Ta journée commence bien avant l'heure du premier patient : tu vérifies le matériel "
            "stérile, prépares les champs opératoires et contrôles les équipements. Pendant "
            "l'intervention, tu passes les instruments au chirurgien avec précision et tu comptes "
            "les compresses pour éviter tout oubli. Entre deux blocs, tu participas à la "
            "décontamination de la salle. En fin de journée, tu complètes le dossier de soins "
            "et tu prépares le programme du lendemain avec l'équipe. Tu signales également "
            "toute anomalie dans le registre de traçabilité du bloc."
        ),
        "requirements_json": [
            {"type": "studies", "label": "Diplôme d'État Infirmier (DEI) — 3 ans après Bac"},
            {"type": "studies", "label": "Spécialisation IBODE — 24 mois après DEI"},
            {"type": "skill", "label": "Maîtrise des protocoles d'asepsie chirurgicale"},
            {"type": "skill", "label": "Instrumentation chirurgicale (orthopédie, digestif…)"},
            {"type": "quality", "label": "Précision et rigueur absolue"},
            {"type": "quality", "label": "Résistance au stress en situation d'urgence"},
            {"type": "quality", "label": "Concentration prolongée"},
        ],
        "prospects_text": (
            "1. IBODE cadre de santé au bloc opératoire. "
            "2. Formateur·rice en IFSI (Institut de Formation en Soins Infirmiers). "
            "3. Infirmier·ère anesthésiste (IADE) après spécialisation complémentaire."
        ),
        "median_salary_eur": 36000,
        "salary_range_json": {"min": 28000, "max": 50000, "source": "Onisep 2025"},
        "signals_json": {
            "passions": ["médecine", "chirurgie", "précision", "technologie médicale"],
            "valeurs": ["utilité sociale", "excellence", "rigueur", "sauver des vies"],
            "specialites": ["svt", "biologie", "chimie"],
            "keywords": ["bloc opératoire", "chirurgie", "infirmier", "hôpital", "soins"],
        },
        "level_compatibility": ["lycee_1ere_tle_general", "lycee_1ere_tle_techno", "postbac"],
        "rome_code": "J1307",
        "sources_json": ["Onisep 2025", "ROME v4.0 J1307", "validation humaine 2026-06"],
    },
    {
        "slug": "medecin-generaliste",
        "name": "Médecin généraliste",
        "sector": "santé",
        "description": (
            "Le·la médecin généraliste est souvent le premier interlocuteur des patients pour "
            "tout problème de santé. Tu diagnostiques, prescris des traitements, suis les "
            "maladies chroniques et orientes vers des spécialistes si nécessaire. Tu joues un "
            "rôle central dans la prévention (vaccinations, dépistages) et dans "
            "l'accompagnement des patients sur le long terme. Ce métier est à la fois "
            "intellectuellement stimulant (résoudre des problèmes médicaux complexes) et "
            "profondément humain (relation de confiance avec les patients). Tu peux exercer en "
            "cabinet libéral, en maison de santé pluridisciplinaire, ou à l'hôpital. "
            "Les études sont longues (9 ans minimum) mais ouvrent des perspectives variées et "
            "une carrière épanouissante."
        ),
        "daily_routine": (
            "Ta matinée démarre par des consultations : tu écoutes les patients, poses des "
            "questions, examines et établis un diagnostic. Entre deux consultations, tu "
            "rappelles des patients pour des résultats d'analyses. L'après-midi peut inclure "
            "des visites à domicile pour les patients à mobilité réduite, ou des consultations "
            "de suivi pour des maladies chroniques comme le diabète ou l'hypertension. Tu "
            "termines par la gestion administrative : ordonnances, certificats, courriers aux "
            "spécialistes. Chaque jour est différent, et tu ne sais jamais à l'avance ce que "
            "la prochaine consultation va t'apporter."
        ),
        "requirements_json": [
            {"type": "studies", "label": "PASS (Parcours Accès Santé Spécifique) ou LAS après Bac"},
            {
                "type": "studies",
                "label": "6 ans d'études de médecine + 3 ans de DES médecine générale",
            },
            {"type": "skill", "label": "Diagnostic médical et raisonnement clinique"},
            {"type": "skill", "label": "Prescription et pharmacologie de base"},
            {"type": "quality", "label": "Écoute active et empathie"},
            {
                "type": "quality",
                "label": "Rigueur scientifique et mise à jour continue des connaissances",
            },
            {"type": "quality", "label": "Gestion du stress et prise de décision rapide"},
        ],
        "prospects_text": (
            "1. Médecin spécialiste (cardiologue, dermatologue…) après surspécialisation. "
            "2. Médecin coordonnateur en EHPAD. "
            "3. Médecin du travail après DES spécialisé. "
            "4. Recherche clinique ou santé publique."
        ),
        "median_salary_eur": 75000,
        "salary_range_json": {"min": 50000, "max": 120000, "source": "Onisep 2025"},
        "signals_json": {
            "passions": ["médecine", "sciences", "aider les autres", "biologie humaine"],
            "valeurs": ["utilité sociale", "excellence", "responsabilité", "empathie"],
            "specialites": ["svt", "chimie", "physique", "mathematiques"],
            "keywords": ["médecin", "santé", "diagnostic", "patient", "consultation", "soin"],
        },
        "level_compatibility": ["lycee_1ere_tle_general", "postbac"],
        "rome_code": "J1101",
        "sources_json": ["Onisep 2025", "ROME v4.0 J1101", "validation humaine 2026-06"],
    },
    {
        "slug": "kinesitherapeute",
        "name": "Kinésithérapeute",
        "sector": "santé",
        "description": (
            "Le·la kinésithérapeute rééduque les patients après une blessure, une opération "
            "chirurgicale ou une maladie affectant leurs capacités motrices. Tu utilises des "
            "techniques manuelles (massages, mobilisations) et des appareils (électrostimulation, "
            "ultrasons) pour aider tes patients à retrouver leurs fonctions physiques. Tu peux "
            "exercer dans un cabinet libéral, dans un hôpital, dans un centre sportif, ou à "
            "domicile. Ce métier est très polyvalent : tu peux te spécialiser en kinésithérapie "
            "du sport, pédiatrique, respiratoire (pour les asthmatiques ou les mucoviscidosiques) "
            "ou neurologique. La relation thérapeutique avec le patient est centrale, et voir "
            "quelqu'un retrouver sa mobilité est une grande source de satisfaction."
        ),
        "daily_routine": (
            "Ta journée est rythmée par des séances de rééducation de 30 à 45 minutes avec "
            "chaque patient. Le matin, tu accueilles tes premiers patients, évalues leur "
            "progression depuis la dernière séance et adaptes ton programme de soins. Tu "
            "pratiques des massages, des exercices de mobilisation ou de renforcement musculaire. "
            "L'après-midi, tu continues les séances et complètes les dossiers patients. "
            "Tu peux aussi conseiller tes patients sur les exercices à faire chez eux pour "
            "accélérer leur rééducation."
        ),
        "requirements_json": [
            {
                "type": "studies",
                "label": "Diplôme d'État de Masseur-Kinésithérapeute (DEMK) — 5 ans",
            },
            {"type": "studies", "label": "Entrée via PASS/LAS ou sélection en IFMK après L1/L2"},
            {"type": "skill", "label": "Techniques de massage et mobilisation articulaire"},
            {"type": "skill", "label": "Électrothérapie et techniques instrumentales"},
            {"type": "quality", "label": "Mains habiles et sens du toucher"},
            {"type": "quality", "label": "Patience et pédagogie avec les patients"},
            {"type": "quality", "label": "Endurance physique (rester debout toute la journée)"},
        ],
        "prospects_text": (
            "1. Kinésithérapeute du sport (clubs professionnels, fédérations). "
            "2. Ostéopathe après formation complémentaire. "
            "3. Cadre de santé ou formateur·rice en IFMK."
        ),
        "median_salary_eur": 42000,
        "salary_range_json": {"min": 30000, "max": 65000, "source": "Onisep 2025"},
        "signals_json": {
            "passions": ["sport", "corps humain", "aider les autres", "anatomie"],
            "valeurs": ["utilité sociale", "contact humain", "bien-être", "soin"],
            "specialites": ["svt", "eps", "physique"],
            "keywords": ["kiné", "rééducation", "massage", "santé", "sport", "patient"],
        },
        "level_compatibility": ["lycee_1ere_tle_general", "lycee_1ere_tle_techno", "postbac"],
        "rome_code": "J1402",
        "sources_json": ["Onisep 2025", "ROME v4.0 J1402", "validation humaine 2026-06"],
    },
    {
        "slug": "pharmacien",
        "name": "Pharmacien·ne",
        "sector": "santé",
        "description": (
            "Le·la pharmacien·ne est le·la spécialiste du médicament. En officine (pharmacie "
            "de quartier), tu délivres les médicaments sur ordonnance ou sans ordonnance, tu "
            "conseilles les clients sur leur traitement et surveilles les interactions "
            "médicamenteuses. En pharmacie hospitalière, tu gères les stocks de médicaments, "
            "prépares des traitements personnalisés et collabores étroitement avec les médecins. "
            "Tu peux aussi travailler dans l'industrie pharmaceutique (développement de nouveaux "
            "médicaments) ou dans la recherche. C'est un métier à la croisée de la chimie, de "
            "la biologie et du conseil de santé, avec une forte dimension humaine en officine."
        ),
        "daily_routine": (
            "En officine, ta matinée commence par l'ouverture de la pharmacie et la réception "
            "des premières ordonnances. Tu vérifiais chaque prescription, choisis le médicament "
            "adapté et expliques au patient comment le prendre. Tu gères aussi les demandes "
            "sans ordonnance : conseils pour un rhume, une douleur, une plaie. L'après-midi, "
            "tu passes les commandes aux grossistes, gères les retours et formes les "
            "préparateurs. En fin de journée, tu t'assures que la caisse correspond aux ventes "
            "et que les stocks sont bien rangés."
        ),
        "requirements_json": [
            {"type": "studies", "label": "PASS/LAS puis 6 ans d'études de pharmacie"},
            {"type": "studies", "label": "Diplôme d'État de Docteur en Pharmacie"},
            {"type": "skill", "label": "Connaissance approfondie en pharmacologie et chimie"},
            {"type": "skill", "label": "Maîtrise des interactions médicamenteuses"},
            {
                "type": "quality",
                "label": "Rigueur et sens des responsabilités (enjeux santé publique)",
            },
            {"type": "quality", "label": "Pédagogie pour expliquer les traitements"},
            {"type": "quality", "label": "Organisation et gestion de stock"},
        ],
        "prospects_text": (
            "1. Pharmacien·ne hospitalier·ère ou industriel·le. "
            "2. Spécialisation en pharmacovigilance ou essais cliniques. "
            "3. Ouverture de sa propre officine. "
            "4. Inspecteur·rice de pharmacie (Agence nationale de sécurité du médicament)."
        ),
        "median_salary_eur": 55000,
        "salary_range_json": {"min": 38000, "max": 90000, "source": "Onisep 2025"},
        "signals_json": {
            "passions": ["chimie", "biologie", "médecine", "sciences"],
            "valeurs": ["rigueur", "santé publique", "responsabilité", "conseil"],
            "specialites": ["chimie", "svt", "physique", "mathematiques"],
            "keywords": ["médicament", "pharmacie", "santé", "chimie", "patient", "ordonnance"],
        },
        "level_compatibility": ["lycee_1ere_tle_general", "postbac"],
        "rome_code": "J1205",
        "sources_json": ["Onisep 2025", "ROME v4.0 J1205", "validation humaine 2026-06"],
    },
    {
        "slug": "ergotherapeute",
        "name": "Ergothérapeute",
        "sector": "santé",
        "description": (
            "L'ergothérapeute aide les personnes ayant des difficultés physiques, cognitives "
            "ou psychiques à retrouver leur autonomie dans la vie quotidienne. Tu analyses "
            "les activités que la personne a du mal à réaliser (s'habiller, cuisiner, écrire) "
            "et tu proposes des solutions : rééducation, adaptation du domicile, aides "
            "techniques (fauteuil roulant adapté, ustensiles ergonomiques). Tu interviens "
            "auprès de personnes âgées, de personnes en situation de handicap, d'enfants "
            "avec des troubles du développement, ou de victimes d'accidents. Ce métier combine "
            "la créativité, la technique et la relation humaine. Tu es souvent un·e acteur·rice "
            "clé dans le retour à domicile des patients après une hospitalisation."
        ),
        "daily_routine": (
            "Ta matinée commence par une évaluation avec un nouveau patient : tu observes ses "
            "mouvements, testes ses capacités et discutes de ses objectifs de vie. Ensuite, "
            "tu mènes une séance de rééducation avec une personne en situation de handicap : "
            "tu lui apprends à utiliser une orthèse ou à adapter ses gestes. L'après-midi, "
            "tu fais une visite au domicile d'une personne âgée pour recommander des "
            "aménagements (barres d'appui, mobilier adapté). Tu termines par la rédaction "
            "des comptes-rendus et les échanges avec les autres professionnels de santé."
        ),
        "requirements_json": [
            {"type": "studies", "label": "Diplôme d'État d'Ergothérapeute — 3 ans après Bac"},
            {"type": "skill", "label": "Analyse de l'activité et bilan ergothérapique"},
            {"type": "skill", "label": "Connaissance des aides techniques et du cadre de vie"},
            {"type": "quality", "label": "Créativité pour trouver des solutions adaptées"},
            {"type": "quality", "label": "Empathie et écoute des besoins du patient"},
            {"type": "quality", "label": "Capacité à travailler en équipe pluridisciplinaire"},
        ],
        "prospects_text": (
            "1. Ergothérapeute spécialisé·e (pédiatrie, neurologie, gérontologie). "
            "2. Cadre de santé ou coordinateur·rice de soins. "
            "3. Consultant·e en accessibilité et conception universelle."
        ),
        "median_salary_eur": 30000,
        "salary_range_json": {"min": 25000, "max": 42000, "source": "Onisep 2025"},
        "signals_json": {
            "passions": ["aider les autres", "créativité", "corps humain", "psychologie"],
            "valeurs": ["autonomie", "solidarité", "bien-être", "inclusion"],
            "specialites": ["svt", "eps", "sciences sociales"],
            "keywords": [
                "ergothérapie",
                "handicap",
                "autonomie",
                "rééducation",
                "soin",
                "adaptation",
            ],
        },
        "level_compatibility": ["lycee_1ere_tle_general", "lycee_1ere_tle_techno", "postbac"],
        "rome_code": "J1406",
        "sources_json": ["Onisep 2025", "ROME v4.0 J1406", "validation humaine 2026-06"],
    },
    {
        "slug": "educateur-specialise",
        "name": "Éducateur·rice spécialisé·e",
        "sector": "social",
        "description": (
            "L'éducateur·rice spécialisé·e accompagne des personnes en difficulté sociale, "
            "familiale ou liée à un handicap, afin de favoriser leur insertion et leur "
            "épanouissement. Tu interviens auprès d'enfants, d'adolescents ou d'adultes dans "
            "des foyers éducatifs, des IME (instituts médico-éducatifs), des centres "
            "d'hébergement, ou en milieu ouvert. Tu crées des activités éducatives, tu "
            "accompagnes dans les démarches administratives et tu travailles étroitement "
            "avec les familles et les autres professionnels. Ce métier exige une grande "
            "stabilité émotionnelle et une capacité à créer du lien avec des personnes "
            "parfois en grande souffrance. Il est profondément utile socialement."
        ),
        "daily_routine": (
            "Ta matinée commence par une réunion d'équipe pour faire le point sur les "
            "résidents ou les suivis en cours. Tu accompagnes ensuite un jeune dans ses "
            "démarches : inscription à une formation, rendez-vous médical. L'après-midi, "
            "tu animes un atelier créatif ou sportif avec un groupe. En soirée (si tu "
            "travailles en internat), tu assures l'accompagnement au coucher, gères les "
            "conflits qui surgissent et rassures les plus anxieux. Tu notes tout dans le "
            "cahier de liaison pour assurer la continuité avec tes collègues."
        ),
        "requirements_json": [
            {"type": "studies", "label": "DEES (Diplôme d'État d'Éducateur Spécialisé) — 3 ans"},
            {
                "type": "studies",
                "label": "Accessible après Bac (sélection sur dossier + entretien)",
            },
            {"type": "skill", "label": "Techniques éducatives et animation de groupe"},
            {"type": "skill", "label": "Connaissance du cadre légal de la protection de l'enfance"},
            {"type": "quality", "label": "Empathie et distance professionnelle"},
            {"type": "quality", "label": "Créativité pour concevoir des projets éducatifs"},
            {"type": "quality", "label": "Résistance au stress et gestion des conflits"},
        ],
        "prospects_text": (
            "1. Chef·fe de service éducatif après expérience + formation CAFERUIS. "
            "2. Directeur·rice d'établissement médico-social (CAFDES). "
            "3. Formateur·rice en école du travail social."
        ),
        "median_salary_eur": 28000,
        "salary_range_json": {"min": 24000, "max": 40000, "source": "Onisep 2025"},
        "signals_json": {
            "passions": ["aider les autres", "éducation", "psychologie", "jeunesse"],
            "valeurs": ["solidarité", "justice sociale", "inclusion", "engagement"],
            "specialites": ["sciences sociales", "philosophie", "svt"],
            "keywords": [
                "éducation",
                "social",
                "handicap",
                "enfance",
                "accompagnement",
                "insertion",
            ],
        },
        "level_compatibility": [
            "lycee_1ere_tle_general",
            "lycee_1ere_tle_techno",
            "lycee_1ere_tle_pro",
            "postbac",
        ],
        "rome_code": "K1207",
        "sources_json": ["Onisep 2025", "ROME v4.0 K1207", "validation humaine 2026-06"],
    },
    {
        "slug": "aide-domicile",
        "name": "Aide à domicile",
        "sector": "social",
        "description": (
            "L'aide à domicile accompagne des personnes âgées, malades ou en situation de "
            "handicap dans leur vie quotidienne, directement à leur domicile. Tu les aides "
            "pour la toilette, les repas, le ménage, les courses, et tu leur apportes une "
            "présence humaine précieuse. Ce métier répond à un besoin social considérable : "
            "permettre aux personnes de rester chez elles le plus longtemps possible. "
            "Tu travailles pour des associations d'aide à domicile, des services à la personne "
            "ou en emploi direct. Les horaires sont souvent décalés (matins tôt, fins "
            "d'après-midi) mais la flexibilité est possible selon les employeurs. C'est un "
            "métier accessible rapidement et très utile."
        ),
        "daily_routine": (
            "Tu commences ta journée chez une personne âgée : tu l'aides à se lever, à faire "
            "sa toilette et à prendre son petit-déjeuner. Ensuite, tu te rends chez un "
            "deuxième bénéficiaire pour faire les courses et préparer le repas du midi. "
            "L'après-midi, tu reviens chez une dame âgée pour faire le ménage et lui tenir "
            "compagnie un moment — ce temps d'échange est souvent très important pour les "
            "personnes isolées. Tu termines ta journée en renseignant le cahier de liaison "
            "que lira le prochain·e intervenant·e."
        ),
        "requirements_json": [
            {
                "type": "studies",
                "label": "CAP AEPE ou Titre ADVF (Assistant·e de Vie aux Familles) — accessible sans diplôme",
            },
            {
                "type": "studies",
                "label": "DEAES (Diplôme d'État d'Accompagnant Éducatif et Social) pour progresser",
            },
            {"type": "skill", "label": "Aide à la toilette et aux actes essentiels"},
            {"type": "skill", "label": "Préparation des repas selon régimes alimentaires"},
            {"type": "quality", "label": "Bienveillance et patience"},
            {"type": "quality", "label": "Discrétion et respect de l'intimité"},
            {"type": "quality", "label": "Autonomie et sens de l'organisation"},
        ],
        "prospects_text": (
            "1. Aide-soignant·e après DEAS en apprentissage. "
            "2. Responsable de secteur dans une association. "
            "3. Auxiliaire de vie sociale spécialisée (handicap, Alzheimer)."
        ),
        "median_salary_eur": 20000,
        "salary_range_json": {"min": 18000, "max": 25000, "source": "Onisep 2025"},
        "signals_json": {
            "passions": ["aider les autres", "contact humain", "personnes âgées"],
            "valeurs": ["solidarité", "humanité", "utilité sociale", "engagement"],
            "specialites": ["sciences sociales"],
            "keywords": ["aide à domicile", "personnes âgées", "accompagnement", "social", "soin"],
        },
        "level_compatibility": ["college_3eme", "lycee_1ere_tle_pro", "lycee_2nde", "postbac"],
        "rome_code": "K1302",
        "sources_json": ["Onisep 2025", "ROME v4.0 K1302", "validation humaine 2026-06"],
    },
    {
        "slug": "veterinaire",
        "name": "Vétérinaire",
        "sector": "santé",
        "description": (
            "Le·la vétérinaire soigne les animaux et veille à la santé publique en contrôlant "
            "les maladies transmissibles entre animaux et humains (zoonoses). Tu peux exercer "
            "en clinique pour animaux de compagnie, en milieu rural pour les élevages, ou "
            "dans l'industrie agroalimentaire et la recherche. En clinique, tu consultes des "
            "chats, chiens et NAC (nouveaux animaux de compagnie), poses des diagnostics, "
            "opères et prescris des traitements. Ce métier allie la passion des animaux à la "
            "rigueur scientifique et à une forte dimension relationnelle avec leurs propriétaires. "
            "Les études sont sélectives (5 ans après intégration en école nationale vétérinaire) "
            "mais offrent de nombreux débouchés."
        ),
        "daily_routine": (
            "Ta matinée est consacrée aux consultations : un chien pour une vaccination, un "
            "chat avec une plaie à suturer, un lapin qui ne mange plus. Tu interroges les "
            "propriétaires, examines les animaux, prescris des examens si nécessaire. "
            "L'après-midi, tu interviens au bloc opératoire pour stériliser un chien ou "
            "retirer une tumeur. Tu passes ensuite voir les animaux hospitalisés et tu les "
            "surveilles. En fin de journée, tu contactes les propriétaires pour les résultats "
            "des analyses. Parfois, tu assures les urgences nocturnes à rotation avec tes "
            "collègues."
        ),
        "requirements_json": [
            {"type": "studies", "label": "Bac S (ou équivalent scientifique) + 2-3 ans de prépa"},
            {"type": "studies", "label": "5 ans en École Nationale Vétérinaire (ENV)"},
            {"type": "skill", "label": "Diagnostic clinique et chirurgie animale"},
            {"type": "skill", "label": "Analyses biologiques et imagerie vétérinaire"},
            {"type": "quality", "label": "Amour des animaux ET des propriétaires"},
            {"type": "quality", "label": "Sang-froid face à des situations d'urgence"},
            {"type": "quality", "label": "Pédagogie pour expliquer les soins aux propriétaires"},
        ],
        "prospects_text": (
            "1. Vétérinaire spécialisé·e (chirurgie, ophtalmologie vétérinaire, oncologie). "
            "2. Vétérinaire inspecteur en santé publique (concours fonction publique). "
            "3. Recherche et développement en industrie pharmaceutique vétérinaire."
        ),
        "median_salary_eur": 48000,
        "salary_range_json": {"min": 32000, "max": 80000, "source": "Onisep 2025"},
        "signals_json": {
            "passions": ["animaux", "biologie", "médecine", "nature"],
            "valeurs": ["bien-être animal", "rigueur scientifique", "responsabilité", "nature"],
            "specialites": ["svt", "chimie", "physique", "mathematiques"],
            "keywords": ["animaux", "vétérinaire", "santé animale", "clinique", "biologie"],
        },
        "level_compatibility": ["lycee_1ere_tle_general", "postbac"],
        "rome_code": "A1501",
        "sources_json": ["Onisep 2025", "ROME v4.0 A1501", "validation humaine 2026-06"],
    },
    {
        "slug": "coiffeur",
        "name": "Coiffeur·euse",
        "sector": "santé",
        "description": (
            "Le·la coiffeur·euse réalise des coupes, colorations, permanentes et soins "
            "capillaires pour ses clients. Au-delà du geste technique, tu joues un rôle "
            "important de confiance et de relation humaine : le salon de coiffure est souvent "
            "un lieu de bien-être où les clients se confient. Tu peux travailler en salon "
            "traditionnel, dans des instituts de beauté, à domicile, ou créer ton propre salon. "
            "Ce métier offre une vraie créativité (colorations, coiffures événementielles) "
            "et une excellente insertion professionnelle dès l'obtention du CAP. "
            "Avec l'expérience, tu peux devenir gérant·e de salon ou te spécialiser en "
            "coiffure artistique pour le cinéma ou la mode."
        ),
        "daily_routine": (
            "Ta journée commence par la préparation du salon : nettoyage des postes, "
            "préparation des produits. Dès les premiers clients, tu accueilles, tu écoutes "
            "leurs souhaits et tu conseilles sur la coupe ou la couleur adaptée. Tu réalises "
            "les shampoings, coupes, et séchages. Certains créneaux sont dédiés aux "
            "colorations (qui demandent plus de temps). Entre deux clients, tu balais, ranges "
            "et prépares ton prochain rendez-vous. En fin de journée, tu encaisses, pris les "
            "rendez-vous suivants et nettoies tout le matériel."
        ),
        "requirements_json": [
            {"type": "studies", "label": "CAP Coiffure — accessible dès la 3ème, 2 ans"},
            {
                "type": "studies",
                "label": "Brevet Professionnel (BP) Coiffure — spécialisation après CAP",
            },
            {"type": "skill", "label": "Techniques de coupe, coloration et permanente"},
            {"type": "skill", "label": "Diagnostic capillaire et conseil client"},
            {"type": "quality", "label": "Habileté manuelle et sens esthétique"},
            {"type": "quality", "label": "Relationnel et écoute des clients"},
            {"type": "quality", "label": "Résistance à la station debout prolongée"},
        ],
        "prospects_text": (
            "1. Gérant·e ou propriétaire de salon de coiffure. "
            "2. Coiffeur·euse artistique (mode, cinéma, théâtre). "
            "3. Formateur·rice dans une école de coiffure."
        ),
        "median_salary_eur": 20000,
        "salary_range_json": {"min": 18000, "max": 35000, "source": "Onisep 2025"},
        "signals_json": {
            "passions": ["mode", "esthétique", "créativité", "contact humain"],
            "valeurs": ["créativité", "bien-être", "service", "autonomie"],
            "specialites": ["arts"],
            "keywords": ["coiffure", "beauté", "bien-être", "esthétique", "créativité", "mode"],
        },
        "level_compatibility": ["college_3eme", "lycee_1ere_tle_pro", "lycee_2nde"],
        "rome_code": "D1202",
        "sources_json": ["Onisep 2025", "ROME v4.0 D1202", "validation humaine 2026-06"],
    },
    # ── SCIENCES / INGÉNIERIE / TECH (8) ────────────────────────────────────
    {
        "slug": "data-scientist",
        "name": "Data scientist",
        "sector": "tech",
        "description": (
            "Le·la data scientist extrait des informations utiles à partir de grandes quantités "
            "de données. Tu conçois des algorithmes de machine learning, analyser des données "
            "complexes et présentes tes résultats à des décideurs non-techniques. Tu travailles "
            "dans des entreprises tech, des banques, des assurances, des hôpitaux, ou dans "
            "le secteur public. Les outils du métier : Python, R, SQL, bibliothèques comme "
            "scikit-learn, TensorFlow ou PyTorch. Ce métier est à la frontière de la "
            "statistique, de l'informatique et du domaine métier. Il est très recherché et "
            "bien rémunéré. Mais attention : une grande partie du travail est de la "
            "préparation et du nettoyage de données (data wrangling), pas seulement de "
            "l'IA spectaculaire."
        ),
        "daily_routine": (
            "Ta matinée commence par une réunion avec l'équipe produit pour comprendre le "
            "problème business à résoudre. Tu passes ensuite à l'exploration des données : "
            "tu importes un dataset, analyses les distributions, repères les valeurs "
            "aberrantes et nettoies les données manquantes. L'après-midi, tu entraînes ton "
            "modèle, évalues ses performances et l'optimises. Tu prépares une présentation "
            "visuelle de tes résultats pour le lendemain. Le soir, tu fais de la veille sur "
            "les nouvelles techniques ou participes à des discussions en ligne."
        ),
        "requirements_json": [
            {"type": "studies", "label": "Master en data science, statistiques ou informatique"},
            {"type": "studies", "label": "Écoles d'ingénieurs avec spécialisation IA/data"},
            {"type": "skill", "label": "Python/R et bibliothèques ML (scikit-learn, TensorFlow)"},
            {"type": "skill", "label": "Statistiques et probabilités avancées"},
            {"type": "skill", "label": "SQL et manipulation de bases de données"},
            {"type": "quality", "label": "Curiosité intellectuelle et esprit analytique"},
            {"type": "quality", "label": "Communication claire de résultats complexes"},
        ],
        "prospects_text": (
            "1. Machine learning engineer (déploiement de modèles en production). "
            "2. Chief Data Officer ou responsable data. "
            "3. Chercheur·se en IA dans un laboratoire ou chez un GAFAM."
        ),
        "median_salary_eur": 52000,
        "salary_range_json": {"min": 38000, "max": 90000, "source": "Apec 2025"},
        "signals_json": {
            "passions": ["mathématiques", "informatique", "données", "intelligence artificielle"],
            "valeurs": ["innovation", "rigueur", "curiosité", "impact"],
            "specialites": ["mathematiques", "informatique", "physique"],
            "keywords": ["data", "IA", "machine learning", "Python", "statistiques", "algorithme"],
        },
        "level_compatibility": ["lycee_1ere_tle_general", "postbac"],
        "rome_code": "M1805",
        "sources_json": ["Apec 2025", "ROME v4.0 M1805", "validation humaine 2026-06"],
    },
    {
        "slug": "developpeur-web-fullstack",
        "name": "Développeur·euse web fullstack",
        "sector": "tech",
        "description": (
            "Le·la développeur·euse web fullstack crée des applications web de A à Z : "
            "l'interface visible par l'utilisateur (front-end) et la logique serveur cachée "
            "derrière (back-end). Tu conçois des bases de données, développes des API, "
            "construis des interfaces réactives et t'assures que tout fonctionne ensemble. "
            "Tu peux travailler en agence web, dans une startup, une grande entreprise ou "
            "en freelance. Le secteur recrute massivement. Ce métier offre beaucoup "
            "d'autonomie et de créativité : tu vois ton travail prendre vie directement dans "
            "le navigateur. La formation continue est essentielle car les technologies évoluent "
            "très vite. Des autodidactes réussissent dans ce domaine."
        ),
        "daily_routine": (
            "Ta journée démarre par un stand-up meeting de 15 minutes avec l'équipe : "
            "chacun dit ce qu'il fait, ses blocages. Tu ouvres ensuite ton éditeur de code "
            "et tu travailles sur la nouvelle fonctionnalité assignée la veille. Parfois tu "
            "debugges un bug mystérieux pendant deux heures — c'est frustrant mais la "
            "satisfaction de le trouver est grande. L'après-midi, tu fais une revue de code "
            "avec un collègue, puis tu déploies ta feature en environnement de test. "
            "Tu termines par la rédaction de tests automatisés."
        ),
        "requirements_json": [
            {
                "type": "studies",
                "label": "BTS SIO, DUT info, Licence ou Bachelor développement web",
            },
            {"type": "studies", "label": "Bootcamp développement web (3-6 mois) + portfolio"},
            {"type": "skill", "label": "HTML/CSS/JavaScript + un framework front (React, Vue)"},
            {"type": "skill", "label": "Langage back-end (Python, Node.js, PHP, Java…)"},
            {"type": "skill", "label": "Bases de données SQL/NoSQL et Git"},
            {"type": "quality", "label": "Autonomie et curiosité technique"},
            {"type": "quality", "label": "Persévérance face aux bugs"},
        ],
        "prospects_text": (
            "1. Lead developer ou tech lead. "
            "2. Freelance ou création de sa propre startup. "
            "3. Architecte logiciel ou CTO (après plusieurs années d'expérience)."
        ),
        "median_salary_eur": 42000,
        "salary_range_json": {"min": 30000, "max": 75000, "source": "Apec 2025"},
        "signals_json": {
            "passions": ["informatique", "création web", "résolution de problèmes", "technologie"],
            "valeurs": ["autonomie", "innovation", "créativité", "logique"],
            "specialites": ["mathematiques", "informatique", "physique"],
            "keywords": ["web", "code", "développement", "informatique", "programmation", "tech"],
        },
        "level_compatibility": [
            "lycee_1ere_tle_general",
            "lycee_1ere_tle_techno",
            "lycee_1ere_tle_pro",
            "postbac",
        ],
        "rome_code": "M1805",
        "sources_json": ["Apec 2025", "ROME v4.0 M1805", "validation humaine 2026-06"],
    },
    {
        "slug": "ingenieur-biotechnologies",
        "name": "Ingénieur·e en biotechnologies",
        "sector": "sciences",
        "description": (
            "L'ingénieur·e en biotechnologies applique les sciences du vivant (biologie, "
            "génétique, microbiologie) pour développer de nouveaux produits ou procédés dans "
            "des secteurs variés : médicaments, alimentation, agriculture, environnement. "
            "Tu peux travailler dans des laboratoires de recherche, dans l'industrie "
            "pharmaceutique (développement de médicaments biologiques), dans "
            "l'agroalimentaire (levures, fermentations), ou dans des startups de la biotech. "
            "Ce métier combine la rigueur scientifique, la créativité de la recherche et "
            "les enjeux industriels. Les biotechnologies sont un secteur en forte croissance, "
            "notamment autour de la thérapie génique et des vaccins ARNm."
        ),
        "daily_routine": (
            "Ta matinée commence au laboratoire : tu prépares tes cultures cellulaires, "
            "lances des expériences et analyses les résultats de la veille sous microscope "
            "ou par spectrophotométrie. Tu consignes tout dans ton cahier de labo. "
            "L'après-midi, tu assistes à une réunion de projet avec l'équipe R&D, puis tu "
            "rédiges un rapport d'avancement. Certains jours, tu travailles sur l'optimisation "
            "d'un procédé de fermentation ou tu analyses des données avec des outils "
            "bioinformatiques. La recherche demande de la patience : les résultats prennent "
            "du temps."
        ),
        "requirements_json": [
            {"type": "studies", "label": "École d'ingénieurs en sciences du vivant / biochimie"},
            {"type": "studies", "label": "Master en biotechnologies ou biochimie"},
            {
                "type": "skill",
                "label": "Techniques de biologie moléculaire (PCR, CRISPR, culture cellulaire)",
            },
            {"type": "skill", "label": "Bioinformatique et analyse de données biologiques"},
            {"type": "quality", "label": "Rigueur expérimentale et esprit critique"},
            {"type": "quality", "label": "Curiosité scientifique et veille technologique"},
            {"type": "quality", "label": "Travail en équipe pluridisciplinaire"},
        ],
        "prospects_text": (
            "1. Doctorat et carrière en recherche académique. "
            "2. Chef·fe de projet R&D en industrie pharmaceutique. "
            "3. Fondateur·rice d'une startup biotech."
        ),
        "median_salary_eur": 46000,
        "salary_range_json": {"min": 35000, "max": 70000, "source": "Apec 2025"},
        "signals_json": {
            "passions": ["biologie", "sciences", "recherche", "innovations médicales"],
            "valeurs": ["rigueur", "innovation", "impact", "curiosité scientifique"],
            "specialites": ["svt", "chimie", "physique", "mathematiques"],
            "keywords": [
                "biotechnologies",
                "biologie",
                "laboratoire",
                "recherche",
                "médicament",
                "sciences du vivant",
            ],
        },
        "level_compatibility": ["lycee_1ere_tle_general", "postbac"],
        "rome_code": "M1703",
        "sources_json": ["Apec 2025", "ROME v4.0 M1703", "validation humaine 2026-06"],
    },
    {
        "slug": "electrotechnicien",
        "name": "Électrotechnicien·ne",
        "sector": "tech",
        "description": (
            "L'électrotechnicien·ne installe, entretient et répare les équipements électriques "
            "dans les bâtiments, les usines ou sur les réseaux électriques. Tu lire des "
            "schémas électriques, câbles des armoires électriques, effectues des mesures et "
            "diagnostiques les pannes. Tu peux travailler pour des entreprises du bâtiment "
            "(électricité tertiaire et industrielle), dans l'énergie (EDF, gestionnaires de "
            "réseaux), ou dans la maintenance industrielle. Ce métier est très concret et "
            "manuel, avec des enjeux de sécurité importants. Il offre une excellente "
            "employabilité car les compétences en électricité sont demandées dans tous les "
            "secteurs, notamment avec la transition énergétique (panneaux solaires, bornes "
            "de recharge VE)."
        ),
        "daily_routine": (
            "Ta journée commence à l'atelier ou sur le chantier : tu prends connaissance des "
            "plans et du cahier des charges. Tu installes les chemins de câbles, poses les "
            "prises et interrupteurs, câbles l'armoire électrique et effectues les tests de "
            "continuité et d'isolement. En cas de dépannage, tu diagnostiques la panne à "
            "l'aide d'un multimètre, identifies la pièce défectueuse et la remplaces. "
            "Tu tiens un registre des interventions et t'assures que ton travail respecte "
            "les normes électriques en vigueur."
        ),
        "requirements_json": [
            {
                "type": "studies",
                "label": "Bac Pro MELEC (Métiers de l'Électricité et de ses Environnements Connectés)",
            },
            {"type": "studies", "label": "BTS Électrotechnique ou DUT Génie Électrique"},
            {"type": "skill", "label": "Lecture de schémas électriques et plans"},
            {"type": "skill", "label": "Habilitations électriques (B1, H1, BR)"},
            {
                "type": "skill",
                "label": "Utilisation d'appareils de mesure (multimètre, pinces ampèremétriques)",
            },
            {"type": "quality", "label": "Rigueur et respect des normes de sécurité"},
            {"type": "quality", "label": "Sens pratique et habileté manuelle"},
        ],
        "prospects_text": (
            "1. Chef·fe d'équipe ou de chantier en électricité. "
            "2. Chargé·e d'affaires en entreprise d'installation électrique. "
            "3. Technicien·ne spécialisé en énergies renouvelables (photovoltaïque, bornes VE)."
        ),
        "median_salary_eur": 30000,
        "salary_range_json": {"min": 22000, "max": 45000, "source": "Onisep 2025"},
        "signals_json": {
            "passions": ["électricité", "technologie", "bricolage", "résolution de problèmes"],
            "valeurs": ["rigueur", "sécurité", "travail concret", "autonomie"],
            "specialites": ["physique", "mathematiques", "technologie"],
            "keywords": [
                "électricité",
                "technique",
                "installation",
                "énergie",
                "maintenance",
                "chantier",
            ],
        },
        "level_compatibility": [
            "college_3eme",
            "lycee_1ere_tle_pro",
            "lycee_1ere_tle_techno",
            "postbac",
        ],
        "rome_code": "F1602",
        "sources_json": ["Onisep 2025", "ROME v4.0 F1602", "validation humaine 2026-06"],
    },
    {
        "slug": "technicien-maintenance-industrielle",
        "name": "Technicien·ne de maintenance industrielle",
        "sector": "industrie",
        "description": (
            "Le·la technicien·ne de maintenance industrielle assure le bon fonctionnement "
            "des machines et équipements dans les usines et sites de production. Tu "
            "interviens pour prévenir les pannes (maintenance préventive) ou les réparer "
            "le plus vite possible quand elles surviennent (maintenance corrective). Tu "
            "travailles sur des systèmes mécaniques, électriques, hydrauliques ou "
            "pneumatiques. Tu peux exercer dans l'industrie agroalimentaire, "
            "pharmaceutique, automobile, aéronautique ou dans les usines de traitement "
            "de l'eau. Ce métier est essentiel : chaque heure d'arrêt machine coûte "
            "cher. Les techniciens de maintenance expérimentés sont très recherchés."
        ),
        "daily_routine": (
            "Ta journée commence par le tour de maintenance préventive : tu vérifies les "
            "niveaux d'huile, inspectes les courroies et les filtres, consignes les mesures "
            "dans le logiciel de GMAO. Vers 10h, une alarme signale une panne sur une ligne "
            "de production : tu interviens rapidement, diagnostiques un capteur défaillant "
            "et le remplaces. Tu documentes l'intervention. L'après-midi, tu travailles sur "
            "un plan de maintenance amélioratrice pour réduire les pannes récurrentes. "
            "Tu collabores avec les opérateurs de production pour comprendre ce qu'ils ont "
            "observé sur les machines."
        ),
        "requirements_json": [
            {"type": "studies", "label": "Bac Pro Maintenance des Équipements Industriels (MEI)"},
            {"type": "studies", "label": "BTS Maintenance des Systèmes ou DUT Génie Industriel"},
            {"type": "skill", "label": "Diagnostic de pannes électriques et mécaniques"},
            {"type": "skill", "label": "Lecture de plans mécaniques et schémas électriques"},
            {
                "type": "skill",
                "label": "Utilisation d'outils de GMAO (Gestion de Maintenance Assistée par Ordinateur)",
            },
            {"type": "quality", "label": "Réactivité et sang-froid face aux pannes urgentes"},
            {"type": "quality", "label": "Sens pratique et rigueur de diagnostic"},
        ],
        "prospects_text": (
            "1. Responsable maintenance (chef d'équipe, planification). "
            "2. Ingénieur·e fiabilité et amélioration continue. "
            "3. Technico-commercial·e pour un fabricant de machines industrielles."
        ),
        "median_salary_eur": 32000,
        "salary_range_json": {"min": 24000, "max": 48000, "source": "Onisep 2025"},
        "signals_json": {
            "passions": ["mécanique", "électronique", "résolution de problèmes", "technologie"],
            "valeurs": ["rigueur", "travail concret", "réactivité", "efficacité"],
            "specialites": ["physique", "mathematiques", "technologie"],
            "keywords": ["maintenance", "industrie", "machine", "panne", "technique", "usine"],
        },
        "level_compatibility": [
            "college_3eme",
            "lycee_1ere_tle_pro",
            "lycee_1ere_tle_techno",
            "postbac",
        ],
        "rome_code": "I1304",
        "sources_json": ["Onisep 2025", "ROME v4.0 I1304", "validation humaine 2026-06"],
    },
    {
        "slug": "ingenieur-civil-btp",
        "name": "Ingénieur·e en génie civil",
        "sector": "btp",
        "description": (
            "L'ingénieur·e en génie civil conçoit, planifie et supervise la construction "
            "d'infrastructures : routes, ponts, tunnels, barrages, bâtiments. Tu réalises "
            "des calculs de structure pour garantir la solidité et la sécurité des ouvrages, "
            "tu gères des chantiers et coordonnes les équipes d'ouvriers et de techniciens. "
            "Tu travailles pour des bureaux d'études, des entreprises de BTP, ou dans le "
            "secteur public (ministère, collectivités). Avec l'urgence climatique, ce métier "
            "évolue vers des constructions plus durables et sobres en énergie. C'est un "
            "métier de terrain autant que de bureau, avec une forte responsabilité sur la "
            "sécurité publique."
        ),
        "daily_routine": (
            "Ta matinée commence au bureau : tu révises les plans du chantier, vérifies "
            "les calculs de charge et prépares les réunions de coordination. Vers 11h, tu "
            "vas sur le chantier pour constater l'avancement, résoudre un problème imprévu "
            "(sol différent de ce que les études de sol indiquaient) et ajuster le planning. "
            "L'après-midi, tu participes à une réunion de chantier avec les sous-traitants, "
            "puis tu travailles sur le rapport d'avancement pour le maître d'ouvrage. "
            "Tu dois constamment arbitrer entre délais, coûts et qualité."
        ),
        "requirements_json": [
            {
                "type": "studies",
                "label": "École d'ingénieurs spécialisée en génie civil (ESTP, EIVP, INSA…)",
            },
            {"type": "studies", "label": "Master Génie Civil à l'université"},
            {"type": "skill", "label": "Calculs de structure et mécanique des sols"},
            {"type": "skill", "label": "Logiciels de CAO/BIM (AutoCAD, Revit)"},
            {"type": "quality", "label": "Rigueur technique et sens des responsabilités"},
            {"type": "quality", "label": "Leadership pour gérer des équipes sur le terrain"},
            {"type": "quality", "label": "Résolution de problèmes sous pression et dans l'urgence"},
        ],
        "prospects_text": (
            "1. Directeur·rice de projet ou de travaux. "
            "2. Expert·e en structures ou géotechnique. "
            "3. Directeur·rice technique dans un groupe de BTP."
        ),
        "median_salary_eur": 48000,
        "salary_range_json": {"min": 35000, "max": 80000, "source": "Apec 2025"},
        "signals_json": {
            "passions": ["mathématiques", "physique", "construction", "urbanisme"],
            "valeurs": ["rigueur", "impact concret", "sécurité", "durabilité"],
            "specialites": ["mathematiques", "physique", "si"],
            "keywords": [
                "BTP",
                "construction",
                "génie civil",
                "chantier",
                "ingénierie",
                "infrastructure",
            ],
        },
        "level_compatibility": ["lycee_1ere_tle_general", "lycee_1ere_tle_techno", "postbac"],
        "rome_code": "F1106",
        "sources_json": ["Apec 2025", "ROME v4.0 F1106", "validation humaine 2026-06"],
    },
    {
        "slug": "biologiste-medical",
        "name": "Biologiste médical·e",
        "sector": "sciences",
        "description": (
            "Le·la biologiste médical·e est responsable des analyses biologiques réalisées "
            "dans les laboratoires de biologie médicale. Tu supervises les analyses de sang, "
            "d'urine, les tests bactériologiques et interprètes les résultats pour aider les "
            "médecins dans leurs diagnostics. Tu peux exercer dans des laboratoires privés, "
            "des hôpitaux ou des laboratoires spécialisés (génétique, virologie, toxicologie). "
            "Ce métier est moins visible que celui de médecin mais tout aussi crucial : "
            "les analyses biologiques participent à plus de 70 % des décisions médicales. "
            "Il faut de longues études mais c'est un métier stable et valorisant, souvent "
            "exercé en libéral avec une bonne qualité de vie."
        ),
        "daily_routine": (
            "Ta matinée commence par la validation des résultats d'analyses arrivés la nuit "
            "(prélevés en urgences). Tu regardes les valeurs anormales, vérifies les contrôles "
            "qualité, puis valides ou bloques les résultats pour leur transmission aux "
            "médecins. Tu reçois ensuite des appels de médecins souhaitant discuter d'un "
            "résultat inhabituel. L'après-midi, tu supervises l'équipe de techniciens de "
            "labo, participes à une réunion sur un nouveau test à implémenter, et prépares "
            "les accréditations réglementaires du laboratoire."
        ),
        "requirements_json": [
            {
                "type": "studies",
                "label": "Double cursus médecine + pharmacie (DES biologie médicale — 9 ans)",
            },
            {"type": "studies", "label": "Master biologie médicale + inter-ARHs"},
            {
                "type": "skill",
                "label": "Techniques analytiques (immunologie, hématologie, microbiologie)",
            },
            {"type": "skill", "label": "Interprétation clinique des résultats biologiques"},
            {
                "type": "quality",
                "label": "Rigueur absolue (engagement de résultats fiables pour les patients)",
            },
            {"type": "quality", "label": "Leadership pour manager l'équipe technique"},
            {"type": "quality", "label": "Mise à jour continue des connaissances scientifiques"},
        ],
        "prospects_text": (
            "1. Directeur·rice de laboratoire de biologie médicale. "
            "2. Spécialisation (génétique médicale, anatomo-pathologie). "
            "3. Industrie du diagnostic in vitro (développement de tests)."
        ),
        "median_salary_eur": 80000,
        "salary_range_json": {"min": 55000, "max": 130000, "source": "Onisep 2025"},
        "signals_json": {
            "passions": ["biologie", "sciences", "médecine", "recherche"],
            "valeurs": ["rigueur scientifique", "précision", "santé publique", "responsabilité"],
            "specialites": ["svt", "chimie", "physique", "mathematiques"],
            "keywords": [
                "biologie médicale",
                "analyses",
                "laboratoire",
                "diagnostic",
                "sciences du vivant",
            ],
        },
        "level_compatibility": ["lycee_1ere_tle_general", "postbac"],
        "rome_code": "J1102",
        "sources_json": ["Onisep 2025", "ROME v4.0 J1102", "validation humaine 2026-06"],
    },
]
