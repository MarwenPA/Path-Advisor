# Domain-Specific Requirements

## Conformité réglementaire (Compliance & Regulatory)

**Cadre RGPD + données de mineurs :**
- **RGPD** (UE) — base légale du traitement : exécution d'un contrat (B2C premium) et intérêt légitime + consentement (recommandations IA, partage profil aux écoles)
- **Loi Informatique et Libertés** (CNIL, France) — âge du consentement numérique abaissé à **15 ans** ; en dessous, **consentement parental requis par simple opt-in email parent** (lien de validation envoyé à l'adresse parent fournie par l'élève)
- **DPIA (Analyse d'Impact Relative à la Protection des Données)** obligatoire — déclencheurs cumulés : traitement automatisé à grande échelle + données de mineurs + impact significatif sur le sujet (orientation = décision majeure)
- **Désignation d'un DPO** (Data Protection Officer) — exigible compte tenu du volume et de la sensibilité

**Décisions automatisées (RGPD art. 22) :**
- Les recommandations vocationnelles et stats d'admission sont des **profilages** au sens RGPD
- Obligations associées : explicabilité du score, droit à l'intervention humaine, droit de contester le résultat
- Implémenté en MVP via : explications visibles "voici les signaux qui ont fait monter ce métier", lien "demander une revue humaine"

**Accessibilité légale :**
- **RGAA 4.1** (équivalent français du WCAG 2.1) — niveau **AA obligatoire** pour services publics et établissements publics (lycées, collèges). Sans RGAA AA, pas de marché B2B Éducation Nationale en growth.
- En MVP : RGAA AA sur les parcours critiques (onboarding, recos, graphes) — full RGAA en growth

**Hébergement et souveraineté :**
- **Données stockées en UE obligatoire** (RGPD)
- Hébergement **France ou UE** recommandé — pour B2B Éducation Nationale, la souveraineté française devient un argument commercial fort (alignement doctrine "Cloud au centre" et SecNumCloud)
- Cibler à terme : hébergeur certifié **SecNumCloud** (ANSSI) ou équivalent

**Cadre éducatif et institutionnel :**
- **Code de l'éducation** — articulation avec Parcoursup, Affelnet ; pas de revente de données aux écoles → important commercialement et déontologiquement
- **Doctrine numérique éducatif** (MENJS) — alignement souhaitable pour pénétrer le B2B EN
- **Référentiel général de sécurité (RGS 2.0)** — exigible pour les contractants publics en growth

## Contraintes techniques (Technical Constraints)

**Sécurité :**
- Chiffrement au repos (AES-256) et en transit (TLS 1.3 minimum)
- Authentification : MFA optionnel B2C, **MFA obligatoire** pour comptes conseiller, école, admin
- Gestion des secrets via coffre dédié (HashiCorp Vault, AWS Secrets Manager, ou équivalent)
- Logs d'audit complets pour : accès aux profils élèves par tiers (parent, conseiller, école, admin) — exigence RGPD + traçabilité
- Pen-test annuel à partir de growth

**Confidentialité par rôle (frontières strictes) :**

| Rôle | Voit | Ne voit pas |
|---|---|---|
| **Élève** | Tout son profil | — |
| **Parent** (lié) | Métiers explorés, parcours, coûts | Bulletins détaillés, appréciations enseignants |
| **Conseiller B2B** (avec consentement élève) | Profil complet + activité | Identifiants de connexion, données paiement |
| **École partenaire** (envoi anticipé, consentement élève + parent) | Profil scolaire synthétique + motivation déclarée | Autres écoles ciblées, autres recos vocationnelles |
| **Admin Path-Advisor** | Référentiel + signalements modérés | Données personnelles élèves (sauf en cas d'incident, avec workflow d'audit) |

**Performance et disponibilité :**
- Latence moteur de recommandation < 3 s en MVP, < 1,5 s en growth
- Disponibilité 99 % MVP, 99,5 % growth
- Saisonnalité forte : pic d'usage **janvier-mars** (préparation Parcoursup) et **mai-juillet** (vœux + réponses) — capacité prévisionnelle indispensable

**Modération de contenu :**
- Motivations déclarées par l'élève dans les envois anticipés → modération anti-discrimination, propos haineux, données personnelles tierces
- Files de signalements (référentiel professions/formations) → workflow back-office traité sous 7 jours

**Versioning et auditabilité des modèles IA :**
- Chaque version du moteur de recommandation est versionnée avec son dataset d'entraînement, ses signaux et son scoring
- Audit trail des décisions : pour chaque reco, on peut rejouer le scoring
- Détection et documentation des biais : audit régulier (genre, origine sociale via codes postaux, type d'établissement d'origine)

## Exigences d'intégration (Integration Requirements)

**MVP :**
- **Import bulletins par PDF + OCR** avec **saisie manuelle assistée en plan B** — un formulaire structuré permet à l'élève de recopier ses notes lorsque l'OCR échoue (PDF non standardisés selon établissements)
- **Paiement** : Stripe ou équivalent (B2C premium) + facturation classique (B2B)
- **Email transactionnel** : SendGrid / Postmark / équivalent
- **Push notifications** : web push standard

**Growth :**
- **ENT/Pronote** — API ou connecteur officiel pour import automatique des bulletins (priorité partenariale)
- **Parcoursup / Affelnet** — pas d'API publique disponible aujourd'hui ; veille produit nécessaire (le ministère publie périodiquement des datasets ouverts)
- **SI éducation nationale** (annuaire BCN/RNE pour les établissements) — référentiel public exploitable

## Risques domaine et mitigations

| Risque | Impact | Mitigation MVP |
|---|---|---|
| **Biais algorithmique** (recos qui reproduisent les inégalités sociales/territoriales) | Crédibilité produit + risque CNIL + reputational | Audit régulier des biais, explicabilité, dataset d'entraînement diversifié (comité éthique trimestriel reporté en growth) |
| **Pression école sur le scoring** (école payant pour mieux apparaître) | Perte de neutralité = perte du différenciateur central | Engagement contractuel + transparence publique du modèle de scoring + audit externe en growth |
| **Mauvaise réception parents** (perception "outil qui décide à la place") | Adoption B2C bloquée | Espace parent qui clarifie le rôle d'aide vs décision, ton produit explicite sur ce point |
| **Incident données mineurs** (fuite, accès non autorisé) | RGPD lourdes amendes + impact médiatique majeur | Chiffrement, MFA staff, audit accès, plan réponse incident, notification CNIL < 72h |
| **Refus B2B Éducation Nationale** (positionnement commercial vs public service) | Marché B2B bloqué | Neutralité commerciale documentée, hébergement souverain, RGAA, alignement doctrine MENJS |
| **Inexactitude statistiques d'admission** (élève déçu post-Parcoursup) | NPS, image, juridique | Affichage explicite de l'incertitude, fourchettes plutôt que valeurs ponctuelles, mise à jour annuelle des modèles |
| **Désengagement (saisonnalité forte)** | LTV B2C limité | Mécaniques de retour (nouvelles écoles, nouvelles formations, échéances Parcoursup) + collège (cycle plus long) |
| **Échec OCR bulletins** (formats hétérogènes selon établissements) | Friction onboarding | Saisie manuelle assistée en plan B + détection de patterns OCR par établissement émetteur pour amélioration continue |
