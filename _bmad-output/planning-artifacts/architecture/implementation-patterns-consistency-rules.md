# Implementation Patterns & Consistency Rules

## Pattern Categories Defined

**Critical Conflict Points Identified :** 9 zones où des agents IA pourraient diverger (naming Python vs TS, format API, organisation fichiers, gestion erreurs, etc.).

## Naming Patterns

**Database Naming (PostgreSQL — Django defaults) :**
- Tables : `snake_case` + pluriel → `students`, `recommendations`, `audit_logs`
- Colonnes : `snake_case` → `tenant_id`, `created_at`, `parental_consent_verified_at`
- Foreign keys : `<entity>_id` → `student_id`, `school_id`
- Index : `idx_<table>_<columns>` → `idx_students_tenant_id`, `idx_audit_logs_actor_id_created_at`
- Booléens : préfixe `is_` ou `has_` ou `_at` pour timestamps optionnels → `is_premium`, `has_completed_onboarding`, `deleted_at`
- Enums Django : `TextChoices` avec valeurs `SCREAMING_SNAKE_CASE` → `EducationLevel.HIGH_SCHOOL_GENERAL`

**API Naming (DRF — convention REST) :**
- Endpoints : kebab-case pluriel → `/api/v1/students`, `/api/v1/early-outreach-requests`, `/api/v1/recommendations/{id}/explainability`
- Path params : `{id}` style (OpenAPI standard) → `/api/v1/students/{student_id}/profile`
- Query params : `snake_case` → `?tenant_id=...&order_by=created_at`
- Headers custom : `X-` prefix + Title-Case → `X-Tenant-Id`, `X-Request-Id`
- Verbes HTTP : strictement REST (GET liste/détail, POST création, PATCH modif partielle, PUT remplacement complet rare, DELETE)

**JSON field naming (cross-cutting critique) :**
- `snake_case` partout (côté Django ET côté JSON exposé ET côté types TS générés) — pas de conversion camelCase
- Rationale : un seul format end-to-end, lisible dans logs, OpenAPI conforme, évite les bugs de mapping

**Code Naming :**

| Contexte | Convention | Exemple |
|---|---|---|
| Python classes | `PascalCase` | `class StudentProfile`, `class EarlyOutreachService` |
| Python fonctions | `snake_case` | `def calculate_admission_score()` |
| Python variables | `snake_case` | `student_id`, `recommendations_list` |
| Python constantes | `SCREAMING_SNAKE_CASE` | `MAX_BULLETIN_FILE_SIZE = 10 * 1024 * 1024` |
| TS composants React | `PascalCase` | `StudentProfileCard`, `RecommendationGraph` |
| TS fichiers composants | `kebab-case` | `student-profile-card.tsx`, `recommendation-graph.tsx` |
| TS fonctions/hooks | `camelCase` (préfixe `use` pour hooks) | `formatBulletinDate`, `useStudentProfile` |
| TS types/interfaces | `PascalCase` (pas de préfixe `I`) | `interface StudentProfile`, `type RecommendationScore` |
| TS variables | `camelCase` | `studentId`, `recommendationsList` |
| CSS classes (Tailwind) | utility-first, pas de classes custom sauf composants shadcn | `flex items-center gap-2` |

## Structure Patterns

**Project Organization (mapping FRs A–H) :**

Django apps par zone de capacité du PRD (pas par couche technique) :

```
apps/api/apps/
├── accounts/          # FR1–FR12 — Auth, RBAC, RGPD
├── profiles/          # FR13–FR19 — Profil élève, bulletins
├── recommendations/   # FR20–FR26 — Vocationnel
├── pathways/          # FR27–FR32 — Parcours + stats
├── outreach/          # FR33–FR40 — Envoi anticipé
├── schools/           # FR36–FR40 — Espace école
├── counselors/        # FR43–FR45 — B2B conseiller
├── parents/           # FR41–FR42 — Espace parent
├── moderation/        # FR48–FR52 — Admin + modération
├── audit/             # Cross-cutting — audit log
└── core/              # Cross-cutting — RBAC, tenant middleware, helpers
```

Chaque Django app contient (convention stricte) :
```
apps/<capability>/
├── __init__.py
├── apps.py
├── models.py          # Modèles Django (data layer)
├── serializers.py     # DRF serializers (validation + output)
├── views.py           # DRF ViewSets (HTTP layer, thin)
├── urls.py            # Routes locales (incluses dans urls.py global)
├── permissions.py     # Permissions DRF custom (RBAC)
├── services/          # Business logic (pas dans views)
│   └── __init__.py
├── tasks.py           # Tâches Celery async
├── selectors.py       # Lectures complexes (équivalent repository pattern)
├── tests/
│   ├── test_models.py
│   ├── test_views.py
│   ├── test_services.py
│   └── factories.py   # factory_boy fixtures
└── admin.py           # Django admin (back-office)
```

**Front Next.js — structure feature-based :**

```
apps/web/src/
├── app/                            # App Router (routes)
│   ├── (public)/                   # Routes non-authentifiées (SEO public)
│   │   ├── metiers/[slug]/page.tsx
│   │   ├── formations/[slug]/page.tsx
│   │   └── layout.tsx
│   ├── (authenticated)/            # Routes authentifiées
│   │   ├── onboarding/page.tsx
│   │   ├── recommendations/page.tsx
│   │   ├── pathways/[occupation_id]/page.tsx
│   │   └── layout.tsx
│   ├── api/                        # Routes API Next.js (proxies vers Django uniquement)
│   ├── layout.tsx
│   └── globals.css
├── components/
│   ├── ui/                         # Composants shadcn/ui (génériques)
│   ├── features/                   # Composants métier par feature
│   │   ├── onboarding/
│   │   ├── recommendations/
│   │   ├── pathways/
│   │   ├── outreach/
│   │   └── ...
│   └── layouts/                    # Composants de mise en page
├── lib/
│   ├── api/                        # Client API généré (OpenAPI) + wrappers
│   │   ├── generated/              # Auto-généré, ne pas éditer
│   │   ├── client.ts               # Wrapper avec auth + base URL
│   │   └── hooks.ts                # Hooks TanStack Query par endpoint
│   ├── auth/                       # Helpers auth (session, CSRF)
│   ├── i18n/                       # Config next-intl + messages FR
│   ├── utils.ts                    # Helpers généraux
│   └── types/                      # Types TS partagés (extension du généré)
├── hooks/                          # Hooks React custom
└── styles/
```

**Tests — convention :**
- Python : tests dans `apps/<app>/tests/` (pas co-located), un fichier par module
- TypeScript : tests co-located avec le code (`student-profile-card.tsx` + `student-profile-card.test.tsx`)
- E2E Playwright : `apps/web/e2e/` dans dossier dédié, organisé par parcours utilisateur du PRD

## Format Patterns

**API Response Format :**

Réponse succès : directe, sans wrapper (DRF convention).

Réponse liste paginée (DRF `CursorPagination`) :
```json
{
  "next": "https://api.path-advisor.fr/api/v1/students?cursor=cD0yMDIw...",
  "previous": null,
  "results": [ {...}, {...} ]
}
```

Réponse erreur : RFC 7807 Problem Details :
```json
{
  "type": "https://path-advisor.fr/errors/insufficient-permissions",
  "title": "Permission insuffisante",
  "status": 403,
  "detail": "Vous ne pouvez pas accéder au profil de cet élève sans son consentement explicite.",
  "instance": "/api/v1/students/stu_xyz/profile",
  "request_id": "req_abc123"
}
```

**Data Exchange Formats :**

| Type | Format |
|---|---|
| Dates | ISO 8601 UTC (`2026-05-13T14:30:00Z`) — jamais de timestamps Unix dans l'API |
| Identifiants | Préfixés par type + suffixe ULID/UUID → `stu_01HXJ...`, `sch_01HXK...`, `req_01HXL...` |
| Booléens | `true` / `false` (pas 1/0) |
| Null | `null` explicite (pas string vide ni 0) |
| Decimal | String (pas float) pour montants : `"10.99"` |
| Devise | ISO 4217 → `"EUR"`, `"MAD"`, `"XOF"` |
| Locale | BCP 47 → `"fr-FR"`, `"fr-BE"`, `"fr-MA"` |

## Communication Patterns

**Event/Task Naming (Celery + audit log) :**

Format `<domain>.<action>` (point-séparé, présent simple actif) :
- `student.profile_completed`
- `recommendation.computed`
- `outreach.profile_sent`
- `outreach.school_responded`
- `school.admission_stat_updated`
- `audit.access_granted`

Payload structuré (Pydantic) :
```python
class EventPayload:
    event_name: str
    event_version: int
    actor_id: str
    tenant_id: str | None
    subject_id: str
    occurred_at: datetime
    metadata: dict[str, Any]
    correlation_id: str
```

**State Management Front :**

| Type d'état | Outil | Exemple |
|---|---|---|
| Données serveur | TanStack Query (cache + invalidation) | profil élève, liste recos, graphe parcours |
| État UI complexe | Zustand (store par feature, pas global) | étape onboarding actuelle, filtres graphe |
| État UI local | `useState` / `useReducer` React | toggle panneau, valeur input non submit |

Pattern d'actions (Zustand) : noms d'actions au présent simple actif → `setCurrentStep`, `resetOnboarding`, `selectOccupation`.

## Process Patterns

**Error Handling :**

Côté Django :
- Toute erreur métier hérite de `domain.exceptions.DomainError`
- Handlers DRF custom convertissent → RFC 7807
- structlog log avec context + correlation_id
- Sentry capture automatique si 5xx
- Jamais d'`Exception` nue (toujours typée)

Côté Next.js :
- Erreurs API captées par TanStack Query, exposées via hook `.error`
- Composants utilisent `<ErrorBoundary>` par feature
- Erreurs critiques : notification toast + Sentry capture
- Erreurs validation form : React Hook Form `.formState.errors`
- Fallback global : `app/error.tsx` avec lien retour

**Loading States :**

3 modes consistants :
- Skeleton screens (shadcn/ui Skeleton) pour listes et fiches
- Spinner inline (composant `<Spinner />`) pour actions courtes (< 2s)
- Progress bar pour opérations longues identifiées (OCR bulletins) avec polling status Celery

Pattern TanStack Query :
```typescript
const { data, isLoading, error } = useStudentProfile(studentId)
if (isLoading) return <ProfileSkeleton />
if (error) return <ErrorState error={error} />
return <Profile data={data} />
```

**Auth Flow :**

1. Login : POST `/api/v1/auth/login/` → session cookie posée par Django, CSRF token retourné en header
2. Next.js stocke le CSRF en cookie côté client, ajoute `X-CSRFToken` à toutes les mutations
3. Logout : POST `/api/v1/auth/logout/` → invalide session
4. Refresh implicite via session cookie (pas de refresh token explicite)
5. MFA challenge : si requis, l'endpoint login retourne 200 avec `{"mfa_required": true, "mfa_session": "..."}` → flow MFA séparé

**Validation Timing :**
- Côté client : Zod (form submit + on-blur sur champs sensibles)
- Côté serveur : DRF serializers (validation systématique, jamais skip)
- Schémas partagés : OpenAPI génère des types TS, Zod schémas écrits à la main miroitent les contraintes Django

## Enforcement Guidelines

**Tous les agents IA d'implémentation DOIVENT :**

1. Suivre les conventions de naming par contexte (DB snake_case, API snake_case, Python snake_case/PascalCase, TS camelCase/PascalCase)
2. Mettre la business logic dans `services/` (Django) — jamais dans les ViewSets/views
3. Toute écriture de données sensibles déclenche un audit log via décorateur `@audit_action('action_name')`
4. Toute requête côté front passe par le client `lib/api/` — jamais d'appel `fetch` brut
5. Tout nouveau modèle Django avec données personnelles inclut `tenant_id` et passe par le middleware RLS
6. Tout endpoint sensible (mutation, données PII) a un test d'autorisation explicite
7. Tout texte utilisateur passe par i18n (`useTranslations` front, `gettext` Django) — pas de string en dur

**Pattern Enforcement (automatisé) :**
- CI checks : ruff (Python), eslint (TS), mypy (Python types), tsc strict (TS)
- Linters custom :
  - Plugin ruff custom : interdit `Exception` nue, force `DomainError` dans `apps/`
  - Plugin eslint custom : interdit `fetch` direct, force usage du client `lib/api/`
- Pre-commit hooks (Lefthook) : lint + format + type-check sur fichiers modifiés
- PR checklist automatique : `audit_log` ajouté ? `tenant_id` présent ? Tests d'autorisation ? i18n des strings ?

**Documentation des patterns :**
- `docs/adr/` — chaque écart au pattern requiert un ADR justificatif
- `docs/patterns/` — guide pour onboarder un nouveau dev ou un nouvel agent IA
- `README.md` — pointe vers tous les patterns + commande `make help` pour les workflows courants

## Pattern Examples

**Good Example — Création d'une ressource avec audit + permissions :**

```python
# apps/outreach/services/outreach_service.py
class OutreachService:
    @audit_action("outreach.profile_sent")
    def send_profile_to_school(
        self, student: Student, school: School, motivation: str
    ) -> EarlyOutreachRequest:
        if not student.is_premium:
            raise InsufficientPlanError(detail="Feature reserved for premium")
        request = EarlyOutreachRequest.objects.create(
            student=student, school=school, motivation=motivation,
            tenant_id=get_current_tenant_id(),
        )
        notify_school.delay(request.id)  # Celery
        return request
```

**Anti-Pattern à éviter :**

```python
# A NE PAS FAIRE
class OutreachViewSet(viewsets.ModelViewSet):
    def create(self, request):
        # Business logic dans la vue
        if not request.user.is_premium:
            return Response({"error": "premium required"}, status=403)
        # Pas d'audit, pas de tenant_id, format erreur non RFC 7807, business logic mélangée
        outreach = EarlyOutreachRequest.objects.create(student=request.user.student, ...)
        return Response({"id": outreach.id})
```
