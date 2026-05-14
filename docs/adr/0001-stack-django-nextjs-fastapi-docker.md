# ADR 0001 — Stack technique : Django + Next.js + FastAPI + Docker Compose

- **Status:** Accepted
- **Date:** 2026-05-14
- **Story:** [Story 1.1 — Initialisation du projet](../../_bmad-output/implementation-artifacts/1-1-initialisation-projet.md)
- **Source decisions:** [architecture/core-architectural-decisions.md](../../_bmad-output/planning-artifacts/architecture/core-architectural-decisions.md), [architecture/starter-template-evaluation.md](../../_bmad-output/planning-artifacts/architecture/starter-template-evaluation.md)

## Context

Path-Advisor est un produit web full-stack avec une forte composante IA (scoring vocationnel,
prédiction d'admission, embeddings, NLP). L'équipe est très restreinte (solo founder + AI-assisted
dev) et doit livrer un MVP en ~9 mois. Les contraintes structurantes :

- **Souveraineté FR/UE** sur l'hébergement (NFR-S3, NFR-I4) — orientation vers Scaleway Paris.
- **PoC local-first** (NFR-M1) — la stack complète doit démarrer en `docker compose up < 5 min`.
- **Scaling IA indépendant** — le moteur de recommandation doit pouvoir évoluer séparément du
  back applicatif.
- **Type-safety end-to-end** — un seul format de données (snake_case) front-back, contrat OpenAPI auto-généré.
- **Conformité RGPD/RGAA AA** dès le MVP sur les parcours critiques.

Les alternatives évaluées (`starter-template-evaluation.md`) :

| Option | Verdict |
|---|---|
| ~~T3 Stack (Next + tRPC + Prisma)~~ | Écarté — Node back + Python IA = 2 langages serveur |
| **Django 5 + DRF + Next.js + FastAPI** | Retenu |
| Django Ninja + Next.js | Considéré — écosystème plus petit |
| Django full-stack templates + HTMX | Écarté — UX du graphe de parcours trop limitée |

## Decision

Le mono-repo Path-Advisor est structuré en 3 apps Dockerisées qui partagent le même PostgreSQL :

1. **`apps/web`** — Next.js 16 + TypeScript strict + Tailwind v3 + shadcn/ui, App Router avec
   Server Components par défaut. Vitest pour les unit tests, Playwright en growth (Sprint 4+).
2. **`apps/api`** — Django 5.1 + DRF + drf-spectacular, Python 3.12 via `uv`. Apps Django
   organisées par capacité fonctionnelle (mapping direct FR A-H du PRD).
3. **`apps/ai-service`** — FastAPI + Pydantic v2, Python 3.12 via `uv`. Scoring statistique
   (scikit-learn) + embeddings (pgvector + sentence-transformers) + NLP (Mistral / Ollama).

L'orchestration locale : un seul `docker compose up` lance les 3 apps + PostgreSQL 16 + pgvector +
Redis 7 + Mailpit + MinIO. PostHog est sous profil optionnel `analytics` pour préserver le NFR-M1.

Le contrat front ↔ back passe par OpenAPI : Django génère `packages/openapi/openapi.json` via
`drf-spectacular`, et `openapi-typescript` produit `apps/web/src/lib/api/generated/schema.ts`
(gitignore, régénéré en CI).

## Tooling notes

- **Tailwind v3** (et non v4) — décision tranchée Story 1.1 §4.10. v4 est récent et l'écosystème
  shadcn/ui n'est pas encore stabilisé dessus. v3 (`^3.4`) reste mature, full-compat, et la
  bascule pourra se faire plus tard via une story dédiée.
- **Racine `docker-compose.yml` via `include`** — pas de symlink. Compatible Windows, explicite,
  prérequis Compose v2.20+.
- **PostHog en profil Compose optionnel** — activable via `docker compose --profile analytics up`.
- **Doppler reporté** — `.env` + `.env.example` suffisent pour la story d'amorçage. Doppler sera
  intégré quand un vrai secret (Stripe sandbox, Postmark) sera nécessaire.
- **Next 16 + next-intl** — incompatibilité de peer dependency déclarative (next-intl 3.x déclare
  Next ≤ 15). Résolu via `legacy-peer-deps=true` dans `apps/web/.npmrc`. À retirer dès qu'une
  version de next-intl publie le support officiel Next 16.

## Consequences

**Positives :**
- Python unique côté serveur → pas de jonglage mental entre langages back vs IA.
- Django admin gratuit couvre ~80 % du back-office (FR48-FR52).
- OpenAPI auto-généré → contrat toujours à jour entre front et back.
- Service IA isolé → scaling horizontal indépendant possible dès le MVP.
- Stack 100 % open source et largement documentée (AI-friendly).

**Négatives à accepter :**
- 3 langages au total (TS, Python serveur, Python IA) — atténué par le fait que Python serveur et
  IA partagent les conventions.
- `legacy-peer-deps` côté npm tant que next-intl ne supporte pas Next 16 officiellement.
- pgvector exige PostgreSQL ≥ 13 et l'extension activée à l'init — `infra/postgres/init.sql` gère
  ça automatiquement, mais reste un point de vigilance pour les migrations prod.
- Couche FastAPI ajoute un service à opérer — justifié par le scaling IA séparé, mais hors MVP on
  pourrait être tenté de l'absorber dans Django si la volumétrie reste faible.

## Compliance

- Hébergement EU (Scaleway Paris) → ✓ NFR-I4
- TLS 1.3 + AES-256 at rest → adressé en prod via Caddy + chiffrement disque cloud (story deploy)
- Audit log immuable → ADR séparé (Story 1.13) ; structure prête (`apps.audit` viendra avec)
- RGAA AA → outillage axe-core à intégrer en CI Sprint 4
