# Path-Advisor

> Plateforme d'orientation continue pour les jeunes francophones, de la 3ème aux premières années post-bac.

Path-Advisor transforme l'angoisse du choix Parcoursup en récit décisionnel défendable. Là où les outils existants (Onisep, Diagoriente) livrent de l'information générique ou (Diplomeo, L'Étudiant) une incitation commerciale biaisée, Path-Advisor articule **deux moments de vérité** — *qui je peux devenir* et *comment y arriver avec mes chances réelles* — dans une expérience continue, neutre commercialement, et fondée sur des données scolaires objectives.

**Statut** : Planification complète, démarrage du développement (MVP cible 9 mois, solo founder + dev assisté IA).

---

## Le problème

Chaque année, près d'un million de lycéens français arrivent à un carrefour décisif — le choix de leur orientation post-bac — sans outil adapté pour les y préparer vraiment. Les plateformes publiques (Onisep, Diagoriente) délivrent de l'information générale mais aucune recommandation personnalisée. Parcoursup gère les candidatures mais pas le conseil. Les comparateurs privés sont structurellement biaisés (leur modèle repose sur la revente de leads aux écoles). Et le ratio conseillers d'orientation / élèves en France (1 pour 1 400) rend l'accompagnement humain inaccessible à l'échelle.

Conséquence : 20 % des étudiants se réorientent en cours de licence.

## La solution — double moteur articulé

1. **Moteur vocationnel** : croisement de signaux déclaratifs (passions, valeurs, intérêts) et de données scolaires objectives (notes + appréciations enseignants) pour produire une liste de métiers scorés avec **explicabilité IA native** (RGPD art. 22).
2. **Moteur de parcours** : pour chaque métier sélectionné, un **graphe-récit interactif** affiche les trajectoires scolaires concrètes avec **statistiques d'admission personnalisées par école**.

Différenciateurs structurels :
- **Données scolaires objectives** comme moteur principal de personnalisation (vs déclaratif pur)
- **Neutralité commerciale** : aucune revente de leads aux écoles
- **Continuité temporelle** 3ème → bac+2/3 (vs snapshot ponctuel)
- **Envoi anticipé biface** : feature premium qui crée un nouveau moment d'orientation
- **Architecture IA hybride** : statistique explicable + deep learning (pour growth)

## À qui ça s'adresse

| Persona | Type | Statut MVP |
|---|---|---|
| **Sarah, Terminale** (Parcoursup imminent) | Protagoniste B2C | 🎬 North Star design |
| Mehdi, 3ème bac pro | Témoin B2C | 🧪 Garde-fou anti-stigma |
| Léa, sans bulletins | Témoin B2C | 🧪 Garde-fou dignité |
| Mme Dupont, conseillère B2B | Témoin B2B | 🧪 5 pilotes MVP |
| M. Martin, parent prescripteur | Promesse | 📦 V2 |
| Mme Garcia, école partenaire | Promesse | 📦 V2 (mais flow MVP minimal) |

## Stack technique

| Couche | Choix |
|---|---|
| **Front** | Next.js 15 + TypeScript + Tailwind v4 + shadcn/ui + Radix UI |
| **Back** | Monolithe modulaire Node.js + Service IA séparé Python/FastAPI |
| **Données** | PostgreSQL (transactionnel + pgvector) + Redis (cache, queue, sessions) + S3-compatible chiffré (bulletins) |
| **Job queue** | BullMQ / Sidekiq / Celery (selon stack équipe) — OCR async, notifications, envois anticipés |
| **OCR** | Tesseract (PoC local) → AWS Textract / Mindee (production) |
| **Paiement** | Stripe (B2C premium 10,99 €/mois) |
| **Email** | Mailpit (PoC local) → Postmark / SendGrid (production) |
| **Analytics** | PostHog (self-hosted ou Cloud EU) |
| **Hébergement** | UE obligatoire (Scaleway / OVH / AWS Paris-Frankfurt), cible SecNumCloud en growth |
| **CI/CD** | GitHub Actions + axe-core (RGAA AA en CI) + Lighthouse (Core Web Vitals) |

**Principe directeur** : *PoC local-first* — toute la stack lance en `docker-compose up < 5 min` avec données de seed.

## Conformité

- **RGPD** + Loi Informatique et Libertés (CNIL) — consentement parental email opt-in < 15 ans, DPIA documentée, droits accès/portabilité/suppression
- **RGPD art. 22** (décisions automatisées) — explicabilité IA + revue humaine + opt-out
- **RGAA 4.1 niveau AA** dès le MVP sur parcours critiques (NFR-A1), full RGAA AA en growth (prérequis B2B Éducation Nationale)
- **Hébergement UE obligatoire** + chiffrement AES-256 at-rest + TLS 1.3 in-transit

## État de la planification

✅ **Product Brief**, **PRD complet** (52 FRs MVP + 5 Fast-Follow + 35 NFRs), **Architecture Decision Document**, **Spécification UX** (14 étapes), **97 stories en 10 épics** avec coverage 100 %.

Estimation globale MVP : ~240-325 jours soit ~13 sprints (solo founder + dev assisté IA intensif).

## Structure du repo

```
Path-Advisor/
├── README.md                                       # Ce fichier
├── _bmad/                                          # Configuration BMAD-METHOD
├── _bmad-output/
│   └── planning-artifacts/
│       ├── product-brief-Path-Advisor.md          # Vision produit (executive summary)
│       ├── prd.md                                  # PRD complet (FRs + NFRs)
│       ├── architecture.md                         # Décisions architecturales
│       ├── ux-design-specification.md              # Spec UX 14 étapes
│       ├── epics.md                                # 10 épics × 97 stories
│       └── product-ideas-backlog.md                # Idées différées (post-MVP)
└── docs/                                           # Documentation projet (vide pour l'instant)
```

## Documentation par étape de réflexion

| Question | Document |
|---|---|
| *Pourquoi ce produit ?* | [product-brief-Path-Advisor.md](_bmad-output/planning-artifacts/product-brief-Path-Advisor.md) |
| *Qu'est-ce qu'on construit ?* | [prd.md](_bmad-output/planning-artifacts/prd.md) |
| *Comment c'est architecturé techniquement ?* | [architecture.md](_bmad-output/planning-artifacts/architecture.md) |
| *Comment ça se design ?* | [ux-design-specification.md](_bmad-output/planning-artifacts/ux-design-specification.md) |
| *Comment c'est découpé en stories de dev ?* | [epics.md](_bmad-output/planning-artifacts/epics.md) |
| *Quelles idées différées à reprendre plus tard ?* | [product-ideas-backlog.md](_bmad-output/planning-artifacts/product-ideas-backlog.md) |

## Roadmap MVP (13 sprints sur 9 mois)

| Sprints | Epic | Livrable |
|---|---|---|
| 1-2 | **Epic 1 — Foundation** | Auth multi-rôle + RBAC + RGPD + Docker Compose + tokens design |
| 3-4 | **Epic 2 — Profil & Onboarding** | Inscription + bulletins OCR + 4 chemins onboarding (3ème / lycée général / lycée pro / sans bulletins) |
| 5-6 | **Epic 3 — Reco Vocationnelle (1er aha)** | 50 métiers MVP curés + service IA scoring + 8 métiers scorés avec phrase recopiable |
| 6-8 | **Epic 4 — Graphe & Stats (2e aha)** | 100+ formations MVP + `GraphParcours` interactif + stats admission personnalisées |
| 8-9 | **Epic 5 — Premium & Envoi Anticipé** | Stripe + envoi anticipé biface + espace école + 3 actions de réponse |
| 9-10 | **Epic 6 — Espaces Tiers** | Compte parent lié + dashboard cohorte conseillère B2B |
| 10 | **Epic 7 — SEO** | Pages publiques SSR + sitemap + Schema.org + Core Web Vitals |
| 10-11 | **Epic 8 — Continuité & Notifications** | `DeltaRecap` retour J+30 + notifications calendrier Parcoursup |
| 11-12 | **Epic 9 — Back-office Admin** | CRUD référentiel + modération motivations + versioning modèles IA |
| 12-13 | **Epic 10 — Fast-Follow** | Profils à risque + push web + parrainage + RDV visio intégré |

## Démarrage

⚠️ **Le projet est en phase de planification — le code n'a pas encore commencé.** La première story à exécuter est `Story 1.1 — Initialisation du projet Next.js avec stack technique cible` (voir [epics.md](_bmad-output/planning-artifacts/epics.md)).

Une fois le projet initialisé, la commande de démarrage local sera :

```bash
docker-compose up
```

L'app sera accessible sur `http://localhost:3000` en moins de 5 minutes (NFR-M1).

## Méthodologie

Le projet utilise [BMAD-METHOD v6](https://github.com/bmad-code-org/BMAD-METHOD) pour structurer la phase de planification (Product Brief → PRD → Architecture → UX Spec → Epics & Stories) et orchestrer le développement (story-by-story implementation avec agents IA).

## Compliance & Léga­l

- **DPO** mutualisé externalisé (prestataire à temps partagé prévu)
- **DPIA** à produire avant déploiement production (Epic 1 Story 1.3 / 1.4)
- **Souveraineté** : hébergement France ou UE strict (Scaleway / OVH / AWS Paris-Frankfurt)
- **Audit RGAA AA** : axe-core en CI dès sprint 4 + audit trimestriel manuel VoiceOver + NVDA

## Auteur

**Marwen Ben Dhahbia** — solo founder
*marwen.bendhahbia@doctolib.com*

## Licence

À définir (projet en phase de démarrage).
