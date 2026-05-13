# Path-Advisor

> Continuous career-orientation platform for youth, from middle school through the first years of higher education.

Path-Advisor turns the anxiety of post-baccalaureate decisions into a defensible decision-making narrative. Where existing tools either deliver generic information (Onisep, Diagoriente) or commercially biased recommendations (Diplomeo, L'Étudiant), Path-Advisor articulates **two moments of truth** — *who I can become* and *how to get there with my real chances* — into a continuous experience, commercially neutral, and grounded in objective school data.

**Status**: Planning complete, development starting (MVP target: 9 months, solo founder + AI-assisted dev).

---

## The problem

Each year, nearly one million French high-schoolers arrive at a critical fork — choosing what to do after the baccalaureate — without a tool designed to truly prepare them. Public platforms (Onisep, Diagoriente) deliver general information but no personalized recommendation. Parcoursup handles applications but not advice. Private comparison sites are structurally biased (their business model is based on reselling leads to schools). And the French ratio of guidance counselors to students (1 per 1,400) makes human support inaccessible at scale.

The consequence: 20% of students change course during their first year of university.

## The solution — articulated dual engine

1. **Vocational engine**: cross-referencing declarative signals (passions, values, interests) with objective school data (grades + teacher comments) to produce a list of scored careers with **native AI explainability** (GDPR Art. 22).
2. **Pathway engine**: for each selected career, an **interactive narrative graph** shows concrete academic trajectories with **personalized admission probabilities per school**.

Structural differentiators:
- **Objective school data** as the primary personalization driver (vs. purely declarative)
- **Commercial neutrality**: no reselling of leads to schools
- **Temporal continuity** from middle school through 2 years post-baccalaureate (vs. one-off snapshots)
- **Two-sided early-send**: a premium feature that creates a new orientation moment
- **Hybrid AI architecture**: explainable statistical scoring + deep learning (for growth phase)

## Who it's for

| Persona | Type | MVP status |
|---|---|---|
| **Sarah, Terminale** (Parcoursup imminent) | B2C Protagonist | 🎬 Design North Star |
| Mehdi, 3ème vocational track | B2C Witness | 🧪 Anti-stigma safeguard |
| Léa, no transcripts available | B2C Witness | 🧪 Dignity safeguard |
| Mme Dupont, B2B guidance counselor | B2B Witness | 🧪 5 MVP pilots |
| M. Martin, prescriber parent | Promise | 📦 V2 |
| Mme Garcia, partner school admissions | Promise | 📦 V2 (with minimal MVP flow) |

## Tech stack

| Layer | Choice |
|---|---|
| **Frontend** | Next.js 15 + TypeScript + Tailwind v4 + shadcn/ui + Radix UI |
| **Backend** | Modular monolith in **Django 5 + DRF + drf-spectacular** (Python 3.12+) for main app API + separate **FastAPI** AI service for ML scaling independence |
| **Data** | PostgreSQL (transactional + pgvector) + Redis (cache, queue, sessions) + encrypted S3-compatible storage (transcripts) |
| **Job queue** | Celery (Python-native) — async OCR, notifications, early-send workflows |
| **OCR** | Tesseract (local PoC) → AWS Textract / Mindee (production) |
| **Payments** | Stripe (B2C premium €10.99/month) |
| **Email** | Mailpit (local PoC) → Postmark / SendGrid (production) |
| **Analytics** | PostHog (self-hosted or Cloud EU) |
| **Hosting** | EU-mandatory (Scaleway / OVH / AWS Paris-Frankfurt), targeting SecNumCloud certification in growth phase |
| **CI/CD** | GitHub Actions + axe-core (RGAA AA in CI) + Lighthouse (Core Web Vitals) |

**Guiding principle**: *PoC local-first* — the entire stack runs via `docker-compose up` in under 5 minutes with seeded data.

## Compliance

- **GDPR** + French Data Protection Act (CNIL) — parental email opt-in consent for users under 15, documented DPIA, rights of access/portability/deletion
- **GDPR Art. 22** (automated decisions) — AI explainability + human review + opt-out
- **RGAA 4.1 Level AA** from MVP on critical user flows (NFR-A1), full RGAA AA in growth (required for B2B Education Nationale market)
- **EU-mandatory hosting** + AES-256 encryption at rest + TLS 1.3 in transit

## Planning status

✅ **Product Brief**, **complete PRD** (52 MVP FRs + 5 Fast-Follow + 35 NFRs), **Architecture Decision Document**, **UX Specification** (14 steps), **97 stories across 10 epics** with 100% coverage.

Overall MVP estimate: ~240-325 days, or ~13 sprints (solo founder + intensive AI-assisted development).

## Repo structure

```
Path-Advisor/
├── README.md                                       # This file
├── _bmad/                                          # BMAD-METHOD configuration
├── _bmad-output/
│   └── planning-artifacts/
│       ├── product-brief-Path-Advisor.md          # Product vision (executive summary)
│       ├── prd.md                                  # Complete PRD (FRs + NFRs)
│       ├── architecture.md                         # Architectural decisions
│       ├── ux-design-specification.md              # 14-step UX spec
│       ├── epics.md                                # 10 epics × 97 stories
│       └── product-ideas-backlog.md                # Deferred ideas (post-MVP)
└── docs/                                           # Project documentation (currently empty)
```

## Documentation by question

| Question | Document |
|---|---|
| *Why this product?* | [product-brief-Path-Advisor.md](_bmad-output/planning-artifacts/product-brief-Path-Advisor.md) |
| *What are we building?* | [prd.md](_bmad-output/planning-artifacts/prd.md) |
| *How is it architected technically?* | [architecture.md](_bmad-output/planning-artifacts/architecture.md) |
| *How is it designed?* | [ux-design-specification.md](_bmad-output/planning-artifacts/ux-design-specification.md) |
| *How is it broken down into dev stories?* | [epics.md](_bmad-output/planning-artifacts/epics.md) |
| *What deferred ideas should we revisit later?* | [product-ideas-backlog.md](_bmad-output/planning-artifacts/product-ideas-backlog.md) |

## MVP roadmap (13 sprints over 9 months)

| Sprints | Epic | Deliverable |
|---|---|---|
| 1-2 | **Epic 1 — Foundation** | Multi-role auth + RBAC + GDPR + Docker Compose + design tokens |
| 3-4 | **Epic 2 — Profile & Onboarding** | Sign-up + transcript OCR + 4 onboarding paths (3ème / general high school / vocational high school / no transcripts) |
| 5-6 | **Epic 3 — Vocational Recommendation (1st aha)** | 50 curated MVP careers + scoring AI service + 8 scored careers with shareable phrase |
| 6-8 | **Epic 4 — Graph & Stats (2nd aha)** | 100+ MVP programs + interactive `GraphParcours` + personalized admission stats |
| 8-9 | **Epic 5 — Premium & Early-Send** | Stripe + two-sided early-send + school workspace + 3 response actions |
| 9-10 | **Epic 6 — Third-Party Spaces** | Linked parent account + B2B counselor cohort dashboard |
| 10 | **Epic 7 — SEO** | Public SSR pages + sitemap + Schema.org + Core Web Vitals |
| 10-11 | **Epic 8 — Continuity & Notifications** | `DeltaRecap` return-on-day-30 + Parcoursup calendar notifications |
| 11-12 | **Epic 9 — Back-office Admin** | Reference data CRUD + motivation moderation + AI model versioning |
| 12-13 | **Epic 10 — Fast-Follow** | At-risk profile detection + web push + referrals + integrated video meetings |

## Getting started

⚠️ **The project is in the planning phase — coding has not yet started.** The first story to execute is `Story 1.1 — Initialize the Next.js project with the target tech stack` (see [epics.md](_bmad-output/planning-artifacts/epics.md)).

Once the project is initialized, the local startup command will be:

```bash
docker-compose up
```

The app will be accessible at `http://localhost:3000` in under 5 minutes (NFR-M1).

## Methodology

The project uses [BMAD-METHOD v6](https://github.com/bmad-code-org/BMAD-METHOD) to structure the planning phase (Product Brief → PRD → Architecture → UX Spec → Epics & Stories) and orchestrate development (story-by-story implementation with AI agents).

## Compliance & Legal

- **DPO** mutualized externally (part-time provider planned)
- **DPIA** to be produced before production deployment (Epic 1 Stories 1.3 / 1.4)
- **Data sovereignty**: strict France or EU hosting (Scaleway / OVH / AWS Paris-Frankfurt)
- **RGAA AA audit**: axe-core in CI from sprint 4 + quarterly manual audits with VoiceOver + NVDA

## Author

**Marwen Ben Dhahbia** — solo founder
*marwen.bendhahbia@doctolib.com*

## License

To be defined (project in early-stage planning).
