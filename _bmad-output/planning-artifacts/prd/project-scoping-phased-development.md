# Project Scoping & Phased Development

## MVP Strategy & Philosophy

**Approche MVP retenue : Problem-Solving × Experience (double accent)**

Path-Advisor est un produit où la valeur naît de l'expérience — les deux moments "aha" sont le cœur de la promesse. Mais le produit doit aussi *fonctionner de bout en bout* dès le MVP : un élève doit pouvoir, en moins de 20 minutes, passer de l'inscription à un graphe de parcours actionnable. Pas de demi-mesure :

- **Problem-solving non négociable** : l'élève résout son problème d'orientation, même avec un référentiel limité (50 métiers / 100 formations) et un modèle prédictif simplifié (open data Parcoursup, pas de DL custom)
- **Experience non négociable** : les 2 aha moments sont *polis* — UI travaillée, copywriting soigné, explicabilité visuelle, animations qui rendent la révélation tangible

Ce qu'on **sacrifie volontairement en MVP** pour tenir cette ambition en équipe restreinte :
- Pas de modèle de DL custom sur les stats d'admission (open data Parcoursup + fourchettes d'incertitude assumées)
- Pas d'app mobile native (PWA installable)
- Pas d'intégration ENT (import PDF/saisie manuelle uniquement)
- Pas de marché hors France
- Pas d'accompagnement post-bac (Phase 2)
- Pas de mentorat professionnels (Phase 2)

## Resource Requirements & Realistic Timeline

**Configuration équipe : Solo / 1-2 personnes**

| Rôle nécessaire | Solution réaliste avec 1-2 personnes |
|---|---|
| **Dev full-stack** (front + back) | Le ou les fondateurs, fortement assistés par **dev IA (Claude Code, Cursor, agents)** |
| **Data/ML** (moteur vocationnel + scoring) | Stack Python + bibliothèques standard (scikit-learn, sentence-transformers) ; modèles simples mais bien évalués ; pas de R&D ML |
| **Content/Référentiel** (50 métiers + 100 formations) | **Bootstrap LLM** : génération assistée à partir d'Onisep open data + Parcoursup + scraping responsable, **revue éditoriale humaine** systématique |
| **UX/Design** | Système de design lean (Tailwind + composants headless, ex. shadcn/ui) ; pas de designer dédié |
| **Commercial B2B** (5 pilotes) | Fait par le fondateur en sourcing direct (réseau + LinkedIn + appels) — 5 pilotes gratuits = pitch facile |
| **RGPD/DPO** | DPO mutualisé externalisé (prestataire à temps partagé, ~200-400€/mois) |

**Timeline réaliste : 9 mois** (au lieu de 6) pour MVP avec 1-2 personnes + dev assisté IA intensif. Compressible à 6-7 mois si :
- Vraiment 2 personnes à temps plein (pas 1 + extras)
- Aucun pivot de scope mid-route
- Stack technique connue par l'équipe (pas d'apprentissage à l'aveugle)

## MVP Feature Set (Phase 1 — 0 à 9 mois)

**Parcours utilisateur essentiel servi :**
- Parcours 1 (Sarah, happy path lycéen) ✅
- Parcours 3 (Léa, profil dégradé sans bulletins) ✅
- Parcours 5 (parent prescripteur, version basique) ✅
- Parcours 6 (école partenaire envoi anticipé) ✅ — version simplifiée

**Parcours partiellement servis :**
- Parcours 2 (Mehdi, 3ème bac pro) — *cas servi mais avec référentiel bac pro limité (10-15 formations bac pro sur 100)*
- Parcours 4 (conseiller B2B) — *dashboard fonctionnel mais minimaliste : cohorte + vue élève, pas de détection profils à risque en MVP*
- Parcours 7 (admin Path-Advisor) — *back-office basique : CRUD référentiel + signalements, pas de tableau qualité données*

**Must-Have Capabilities :**

| Capability | Justification MVP |
|---|---|
| Auth multi-rôle + RBAC + multi-tenant hybride | Fondation conformité + B2B + différenciation par rôle |
| Onboarding élève (profil + OCR bulletins + saisie manuelle fallback + consentement parental email) | Sans bulletins, pas de stats personnalisées = pas de différenciation |
| Moteur vocationnel (statistique + 50 métiers curés) | Premier moment aha |
| Moteur parcours (100 formations + graphe interactif + stats admission open data) | Deuxième moment aha |
| Mode "profil dégradé" (sans bulletins) | Anti-friction onboarding, pas un dead-end |
| Premium B2C + Stripe + gating fonctionnalités | Validation revenue B2C dès MVP |
| Envoi anticipé écoles (premium) + flow complet école (auth, réception, 3 actions, MAJ stat) | Différenciateur premium clé + accrochage B2B |
| Dashboard conseiller B2B basique (cohorte + vue élève consentie) | 5 pilotes nécessitent un produit utilisable, même minimaliste |
| Vue parent (lecture restreinte + paiement) | Levier conversion premium + adoption |
| RGPD complet (DPIA, consentement parental, art. 22 explicabilité) | Non négociable légalement |
| RGAA AA sur parcours critiques | Exigence B2B EN |
| SEO B2C (SSR + Schema.org + sitemap) | Acquisition organique = vital sans budget pub |
| Monitoring + observabilité (Sentry, PostHog, Grafana) | Détection précoce des dérives |

**Nice-to-Have (descopable si retard) :**
- Détection profils à risque dans dashboard conseiller → reporter à fast-follow (mois 9-12)
- Tableau qualité données admin → reporter à fast-follow
- Notifications push proactives (mensuelles, nouvelles écoles, etc.) → premier release email only, push en fast-follow

## Phase 2 — Growth (mois 9 à 24)

**Capacités ajoutées :**
- Intégration ENT/Pronote (import automatique bulletins)
- Modèle prédictif d'admission custom (deep learning sur historiques)
- App mobile native (iOS + Android)
- Mise en relation professionnels (mentorat + témoignages)
- Aide recherche de stages
- Lancement Belgique **ou** Maroc (1 marché)
- Dashboard conseiller enrichi (détection profils à risque, recommandations cohorte)
- Comité éthique trimestriel (audit biais formalisé)
- Audit RGPD externe certifié
- Migration RGAA AA full (toutes pages, pas seulement parcours critiques)
- Licence B2B Enterprise (multi-établissements + tenancy dédiée option)

**Cibles business croissance :**
- 10 000 MAU, 5-15 % premium
- 30+ établissements payants (incluant 3+ ex-pilotes convertis)
- 50 % des MAU postulent à au moins 1 école recommandée

## Phase 3 — Vision (mois 24+)

- Couverture francophone complète (Tunisie, Sénégal, Canada francophone, Suisse romande)
- Plateforme matching jeunes diplômés / premiers employeurs (extension continuité jusqu'à la vie active)
- API publique pour intégrations tierces (établissements, ministères, plateformes publiques)
- Outil conseiller enrichi IA (assistance entretien d'orientation)

## Risk Mitigation Strategy

**Risques techniques :**
- **Stack inconnue** → choisir une stack maîtrisée par l'équipe (pas d'apprentissage à l'aveugle), même si moins "tendance"
- **OCR bulletins échoue** → fallback manuel assistée intégrée dès le MVP (déjà décidé)
- **Stats admission inexactes** → assumer l'incertitude visuellement (fourchettes, pas valeurs ponctuelles) + recalibrage post-Parcoursup année 1
- **Performance moteur reco sous charge saisonnière** → load testing simulé sur 500 utilisateurs concurrents avant le pic janvier-mars

**Risques marché :**
- **B2B EN refuse Path-Advisor (RGAA, souveraineté)** → conformité RGAA AA + hébergement français acté dès MVP
- **Premium B2C ne convertit pas à 5 %** → revue trimestrielle de la proposition de valeur premium ; si < 2 %, repenser les features premium ou le pricing
- **Envoi anticipé n'attire pas les écoles** → bundle B2B pilote = écoles partenaires côté envoi anticipé (volume garanti dès le lancement)
- **Désintermédiation LLM grand public** → veille active + accent sur ce que ChatGPT ne fait pas (bulletins, stats par école, neutralité auditée)

**Risques ressources (criticité élevée — équipe 1-2 personnes) :**
- **Une seule personne tombe malade / s'épuise** → documentation système rigoureuse, code commentaire dense, mémoires partagées (CLAUDE.md, README, ADR) ; sous-traitance ponctuelle envisageable (référentiel content)
- **Budget content (50 métiers + 100 formations) sous-estimé** → bootstrap LLM + revue humaine, pas de rédaction from scratch ; partenariat éventuel avec un journaliste/rédacteur orientation freelance
- **Manque de feedback utilisateur précoce** → cohorte beta de 30-50 lycéens recrutés AVANT le lancement public (LinkedIn, réseau perso, écoles pilotes)
- **Curation du référentiel devient un travail à temps plein** → automatisation maximum (Onisep open data + scraping responsable) + community sourcing (les utilisateurs signalent les corrections, traité dans le back-office admin)
- **Manque de commercial B2B** → pitcher pendant la phase de construction (mois 3-6) pour avoir les 5 pilotes prêts à activer dès le launch (mois 9)

**Risques produit non négociables (à surveiller chaque sprint) :**
- Les 2 aha moments **fonctionnent vraiment** (tester sur 5 utilisateurs minimum à chaque release)
- La complétion d'onboarding reste **> 70 %** (si elle chute, l'OCR ou le wizard sont en cause)
- La latence du moteur reco reste **< 3 s** (si elle dérive, dette technique à régler avant feature)
