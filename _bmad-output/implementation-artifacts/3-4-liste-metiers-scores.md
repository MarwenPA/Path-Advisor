# Story 3.4: Liste métiers scorés affichée à l'élève

Status: ready-for-dev

## Story

As an élève (Sarah, Mehdi, Léa),
I want to see a personalised list of 8 recommended professions with their 0–100 score,
so that I discover the professions that match me from the end of onboarding (FR20 — premier moment aha).

## Acceptance Criteria

1. **Given** onboarding is complete (passions + niveau + bulletins or skip), **When** I arrive on "Mes métiers", **Then** I see a list of exactly 8 `ScoreVocationnel` cards (top 8 scored professions), each showing: profession name, score 0–100, copyable phrase, 2–5 signal chips (compact variant).

2. **Given** the page loads, **Then** the list renders in < 3 s P95 (NFR-P1 constraint).

3. **Given** it is the first visit (no prior view), **When** the list appears, **Then** a sequential fade-in animation plays (100 ms stagger per card) — the reveal moment. Animation is skipped if `prefers-reduced-motion` is active.

4. **Given** a return visit (previously seen), **When** I navigate back to "Mes métiers", **Then** the list is shown WITHOUT animation (anti-circus UX-DR27). A "Mis à jour le [date]" indicator is visible when recommendations have changed since last view.

5. **Given** I tap a profession card, **Then** I navigate to the profession detail page (future Story 3.5): route `/professions/[slug]`.

6. **Given** the Django backend receives a request for `GET /api/v1/students/me/recommendations/`, **Then** it fetches the student's profile, calls `ai_client.score_metiers()` with ALL active professions + their signals, sorts by score descending, and returns the top 8 with full profession data.

7. **Given** the student has no profile data (fresh account), **Then** the endpoint returns 8 professions scored using bulletin_quality only (graceful degradation — passion/valeur overlap = 0, low confidence).

8. **Given** the page is server-side rendered (SSR), **Then** the page is a Next.js Server Component that fetches recommendations at request time and passes data to a Client Component for animation and interactivity.

## Tasks / Subtasks

- [ ] Task 1 — Django: `RecommendationService` + `GET /api/v1/students/me/recommendations/` (AC: 6, 7)
  - [ ] 1.1 Create `apps/recommendations/services/recommendation_service.py` with `compute_recommendations(user)` that: fetches StudentProfile + BulletinSummary, fetches all active Professions with signals, calls `ai_client.score_metiers()`, returns top 8 sorted by score desc
  - [ ] 1.2 Create `ScoredProfessionSerializer` (read-only) combining Profession fields + score/confidence/signals from ai-service response
  - [ ] 1.3 Create `RecommendationsView` (APIView, GET, `IsAuthenticatedAndActive + IsStudent`) at `GET /api/v1/students/me/recommendations/`
  - [ ] 1.4 Wire URL in `apps/recommendations/urls.py` (new file) and include in `path_advisor/urls.py`
  - [ ] 1.5 Write Django tests: success (8 results, sorted), graceful degradation (no profile), ai-service error (503 → propagates), unauthorized (401)

- [ ] Task 2 — Next.js: API client module (AC: 8)
  - [ ] 2.1 Create `apps/web/src/lib/api/recommendations.ts` with types (`ScoredProfession`, `RecommendationsResponse`) and `fetchRecommendations(signal?)` function using `apiFetch`

- [ ] Task 3 — Next.js: Server Component page (AC: 1, 2, 8)
  - [ ] 3.1 Create `apps/web/src/app/(authenticated)/mes-metiers/page.tsx` — async Server Component: calls `fetchRecommendations()`, passes data to `MetiersList` client component
  - [ ] 3.2 Add loading UI: `apps/web/src/app/(authenticated)/mes-metiers/loading.tsx` with 8 skeleton cards

- [ ] Task 4 — Next.js: `MetiersList` client component (AC: 1, 3, 4, 5)
  - [ ] 4.1 Create `apps/web/src/components/features/recommendations/MetiersList.tsx` — "use client", receives `ScoredProfession[]`, renders `ScoreVocationnel` in compact variant for each, handles first-visit animation
  - [ ] 4.2 Implement first-visit detection: `localStorage.getItem("recos_seen")` → if absent, animate stagger and set key; if present, render immediately
  - [ ] 4.3 Implement sequential fade-in animation: CSS `animation-delay: i * 100ms`, skip if `prefers-reduced-motion`
  - [ ] 4.4 On card click → `router.push(\`/professions/\${slug}\`)` (link to future 3.5)
  - [ ] 4.5 "Mis à jour le [date]" indicator using the `computed_at` timestamp from API response

- [ ] Task 5 — Tests (AC: 1, 3, 4, 5, 6, 7)
  - [ ] 5.1 Vitest + RTL: `MetiersList.test.tsx` — renders 8 cards, no animation on return visit, animation on first visit (mock localStorage), card click calls router.push
  - [ ] 5.2 Django: integration tests for `RecommendationService` with mocked `ai_client`

## Dev Notes

### Architecture Overview

**Data flow for Story 3.4:**
```
Browser → GET /mes-metiers
  → Next.js Server Component
    → apiFetch("GET /api/v1/students/me/recommendations/")
      → Django RecommendationsView
        → RecommendationService.compute_recommendations(user)
          → StudentProfile.objects.get(user=user)  [profile data]
          → Profession.objects.filter(is_active=True)  [all 50+ professions]
          → ai_client.score_metiers(student_id, profile, occupation_ids, professions_data)
          → Sort by score desc → top 8
        → ScoredProfessionSerializer × 8 → JSON response
  → MetiersList client component (animation + interaction)
```

### Django: RecommendationService

**File to CREATE:** `apps/api/apps/recommendations/services/recommendation_service.py`

The service must:
1. Fetch `StudentProfile` (may not exist if onboarding not started → use empty defaults)
2. Fetch `StudentLevelProfile` for `niveau` (may not exist → empty string)
3. Fetch bulletin summary from the profile (has_bulletins, bulletin_summary)
4. Fetch ALL `Profession.objects.filter(is_active=True)` — no pagination needed (≤ 200 professions)
5. Build `profile` dict matching `StudentProfile` schema for ai-service
6. Build `professions_data` list: `[{"occupation_id": p.id, "signals_json": p.signals_json, "level_compatibility": p.level_compatibility}]`
7. Call `ai_client.score_metiers(str(user.pk), profile_dict, occupation_ids, professions_data)`
8. Sort by score descending, take top 8
9. Merge ai-service `OccupationScore` with `Profession` DB object for the serializer

**Profile dict shape (must match ai-service `StudentProfile` Pydantic schema):**
```python
{
    "passions": profile.passions if profile else [],
    "valeurs": profile.valeurs if profile else [],
    "niveau": level_profile.level or "" if level_profile else "",
    "specialites": level_profile.specialites or [] if level_profile else [],
    "has_bulletins": profile.has_bulletins if profile else False,
    "bulletin_summary": {
        "average": profile.bulletin_summary.get("average"),
        "appreciation_keywords": profile.bulletin_summary.get("appreciation_keywords", []),
    } if profile and profile.bulletin_summary else None,
}
```

**StudentProfile model fields to use (from `apps/students/models.py`):**
- `profile.passions` — list[str] (JSONB)
- `profile.valeurs` — list[str] (JSONB)
- `profile.has_bulletins` — bool
- `profile.bulletin_summary` — dict|None (JSONB, has "average" and "appreciation_keywords" keys)

**StudentLevelProfile model fields (join via `StudentLevelProfile.objects.filter(user=user).first()`):**
- `level_profile.level` — str (e.g. "terminale_generale")
- `level_profile.specialites` — list[str]

**CRITICAL:** `ai_client.score_metiers()` is in `apps/recommendations/services/ai_client.py`. Do NOT reimport it from a different path. It returns a `dict` (the parsed JSON response) with `scored_occupations: list[dict]`.

Each `scored_occupation` dict has:
```json
{
  "occupation_id": "prof_xxx",
  "score": 72,
  "signals_contributifs": [
    {"signal": "passion_overlap", "weight": 0.35, "contribution": 25},
    ...
  ],
  "confidence_level": "high"
}
```

### Django: ScoredProfessionSerializer

**Read-only serializer** combining Profession model + ai-service score data.

The view merges them into a dict/namedtuple before serializing — the serializer does NOT hit the DB again.

```python
class ScoredProfessionSerializer(serializers.Serializer):
    """Read-only merged view: Profession fields + ai-service score."""
    id = serializers.CharField()
    slug = serializers.CharField()
    name = serializers.CharField()
    sector = serializers.CharField()
    score = serializers.IntegerField()
    confidence_level = serializers.ChoiceField(choices=["low", "medium", "high"])
    signals_contributifs = serializers.ListField(child=serializers.DictField())
    phrase_recopiable = serializers.CharField()  # MVP: empty string ""
    computed_at = serializers.DateTimeField()
```

**Note on `phrase_recopiable`:** Story 3.4 does not implement phrase generation (that's part of Story 3.6's explicability). For MVP, return `""` — `ScoreVocationnel` handles empty phrase gracefully (renders "Phrase à venir").

### Django: RecommendationsView

**File to CREATE:** `apps/api/apps/recommendations/views.py`

```python
class RecommendationsView(APIView):
    """GET /api/v1/students/me/recommendations/ — top-8 scored professions."""
    permission_classes = [IsAuthenticatedAndActive, IsStudent]

    def get(self, request: Request) -> Response:
        from apps.recommendations.services.recommendation_service import compute_recommendations
        try:
            results = compute_recommendations(request.user)
        except AIServiceUnavailableError as exc:
            return Response(
                {"type": "https://path-advisor.fr/errors/ai-service-unavailable",
                 "title": "Service IA indisponible",
                 "detail": str(exc),
                 "status": 503},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                content_type="application/problem+json",
            )
        serializer = ScoredProfessionSerializer(results, many=True)
        return Response({"results": serializer.data, "computed_at": now().isoformat()})
```

**File to CREATE:** `apps/api/apps/recommendations/urls.py`

```python
from django.urls import path
from apps.recommendations.views import RecommendationsView

app_name = "recommendations"
urlpatterns = [
    path("students/me/recommendations/", RecommendationsView.as_view(), name="list"),
]
```

**In `path_advisor/urls.py` — ADD this line after the students include:**
```python
path("api/v1/", include("apps.recommendations.urls")),
```

### Next.js: API types + client

**File to CREATE:** `apps/web/src/lib/api/recommendations.ts`

```typescript
import { apiFetch } from "@/lib/api/client";

export interface SignalContributif {
  signal: string;
  weight: number;
  contribution: number;
}

export interface ScoredProfession {
  id: string;
  slug: string;
  name: string;
  sector: string;
  score: number;
  confidence_level: "low" | "medium" | "high";
  signals_contributifs: SignalContributif[];
  phrase_recopiable: string;
}

export interface RecommendationsResponse {
  results: ScoredProfession[];
  computed_at: string;
}

export function fetchRecommendations(signal?: AbortSignal): Promise<RecommendationsResponse> {
  return apiFetch<RecommendationsResponse>("/api/v1/students/me/recommendations/", { signal });
}
```

### Next.js: Server Component page

**File to CREATE:** `apps/web/src/app/(authenticated)/mes-metiers/page.tsx`

- **Must be a Server Component** (no `"use client"` directive)
- Calls `fetchRecommendations()` directly (server-side fetch via `apiFetch` with SSR cookie forwarding)
- On `ApiError` 503 → render error state (service unavailable message)
- On success → renders `<MetiersList items={data.results} computedAt={data.computed_at} />`

**File to CREATE:** `apps/web/src/app/(authenticated)/mes-metiers/loading.tsx`

- Renders 8 skeleton cards using `<div className="animate-pulse ...">` pattern (no external lib needed)
- Matches `ScoreVocationnel` compact size: `max-h-40 max-w-[360px]` per card

### Next.js: MetiersList client component

**File to CREATE:** `apps/web/src/components/features/recommendations/MetiersList.tsx`

```typescript
"use client";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ScoreVocationnel } from "@/components/professions/ScoreVocationnel";
import { usePrefersReducedMotion } from "@/hooks/use-prefers-reduced-motion";
import type { ScoredProfession } from "@/lib/api/recommendations";

const SEEN_KEY = "recos_seen_v1";

interface MetiersListProps {
  items: ScoredProfession[];
  computedAt: string;
}

export function MetiersList({ items, computedAt }: MetiersListProps) {
  const router = useRouter();
  const reducedMotion = usePrefersReducedMotion();
  const [animate, setAnimate] = useState(false);

  useEffect(() => {
    const seen = localStorage.getItem(SEEN_KEY);
    if (!seen) {
      setAnimate(true);
      localStorage.setItem(SEEN_KEY, computedAt);
    }
  }, [computedAt]);

  // Map ScoredProfession to ScoreVocationnel props
  // signals_contributifs → Signal[] (use signal name as id and label)
  ...
}
```

**Signal mapping:** `signals_contributifs` from the API are internal model signals (`passion_overlap`, etc). For MVP display, convert them to human-readable labels:
```typescript
const SIGNAL_LABELS: Record<string, string> = {
  passion_overlap: "Passions",
  valeur_alignment: "Valeurs",
  niveau_compatibility: "Niveau",
  bulletin_quality: "Résultats",
};
```
Filter out signals with `contribution === 0` before rendering chips.

**Animation implementation:**
```tsx
<article
  style={{
    animationDelay: animate && !reducedMotion ? `${index * 100}ms` : "0ms",
    opacity: animate && !reducedMotion ? 0 : 1,
  }}
  className={animate && !reducedMotion ? "animate-fade-in" : ""}
>
```
Add `animate-fade-in` to Tailwind config: `@keyframes fade-in { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }`.

**Card click → navigation:**
```tsx
<button onClick={() => router.push(`/professions/${item.slug}`)}>
  <ScoreVocationnel ... />
</button>
```
Or wrap in `<Link href={`/professions/${item.slug}`}>`.

### Existing files to READ before touching

- `apps/api/apps/students/models.py` — `StudentProfile` and `StudentLevelProfile` field names
- `apps/api/apps/recommendations/services/ai_client.py` — `ai_client.score_metiers()` signature and return type
- `apps/web/src/components/professions/ScoreVocationnel.tsx` — props: `metierId`, `metiersName`, `score`, `phraseRecopiable`, `signals: Signal[]`, `variant`, `confidenceLevel`
- `apps/web/src/components/professions/types.ts` — `Signal` interface: `{ id: string; label: string }`
- `apps/web/src/lib/api/client.ts` — `apiFetch<T>()` signature
- `apps/web/src/app/(authenticated)/layout.tsx` — authenticated layout structure (no nav bar yet, just `{children}`)
- `apps/api/path_advisor/urls.py` — where to add recommendations URL include

### Critical constraints

1. **No new Django model** — Story 3.4 does NOT persist scores to DB. Scores are computed on demand. If caching is needed, that's a future optimization.

2. **Business logic in service layer** — `RecommendationsView` must delegate to `RecommendationService`, not compute directly in the view.

3. **`ai_client` is a singleton** — use `from apps.recommendations.services.ai_client import ai_client` (the module-level instance), not `AIClient()`.

4. **Profession IDs as occupation_ids** — `Profession.id` (type `CharField` with prefix `prof_`) is the `occupation_id` used in ai-service requests.

5. **Performance** — Fetching 50 professions from DB + 1 ai-service call = ~200ms total on warm path. The 3s P95 constraint is achievable without caching for MVP.

6. **`ScoreVocationnel` variant="compact"** — the list view MUST use `variant="compact"` (max-h-40 max-w-[360px]). Compact shows max 2 signal chips.

7. **confidenceLevel mapping** — ai-service returns `"low" | "medium" | "high"`, ScoreVocationnel expects `"normal" | "indicative"`. Mapping: `low` → `"indicative"`, `medium/high` → `"normal"`.

8. **Next.js 16 Server Component constraint** — Do NOT `"use client"` the page itself. The page is a Server Component that fetches data. Only `MetiersList` is a Client Component (for animation + router).

9. **No hardcoded strings** — Do not put French user-facing strings directly in components without checking if there's an i18n pattern. For MVP (no next-intl in use yet in this area), use string constants at the top of the file.

10. **Read AGENTS.md** at `apps/web/AGENTS.md` before writing any Next.js code — it warns about API breaking changes.

### Testing patterns

**Django tests** (pytest, in `apps/recommendations/tests/test_recommendations.py`):
- Mock `ai_client.score_metiers` using `unittest.mock.patch`
- Test: authenticated student gets 8 results sorted by score desc
- Test: no StudentProfile → graceful (empty profile dict, all zeros except bulletin)
- Test: AIServiceUnavailableError → 503 response with problem+json
- Test: non-student role → 403
- Test: unauthenticated → 401

**Frontend tests** (Vitest + RTL, in `MetiersList.test.tsx`):
- 8 `ScoreVocationnel` cards rendered
- First visit: animation classes applied, localStorage key set
- Return visit: no animation (localStorage key already set)
- Card click: router.push called with correct `/professions/[slug]`
- Mock `localStorage` with `vi.stubGlobal` or `Object.defineProperty`
- Mock `next/navigation` with `vi.mock`

### Previous story learnings

From Story 3.3 (scorer):
- `ai_client.score_metiers(student_id, profile, occupation_ids, professions_data=None)` — professions_data is optional but needed for content-based scoring
- Scores are integers [0,100], confidence_level is "low"|"medium"|"high"
- The scorer is fast (~10ms for 50 professions)

From Story 3.12 (FicheMetier component):
- `ScoreVocationnel` compact: max-h-40, max-w-[360px], shows 2 signal chips max
- Signal interface: `{ id: string; label: string }` — the `id` is also used for `data-testid`

From Story 3.2 (professions):
- `Profession.id` format: `"prof_XXXX..."` (generated via `generate_id("prof")`)
- All active professions: `Profession.objects.filter(is_active=True)`
- `signals_json` keys: `passions`, `valeurs`, `specialites`, `keywords`

### Project Structure Notes

**New files to create:**
```
apps/api/apps/recommendations/
  views.py                                    (NEW — RecommendationsView)
  urls.py                                     (NEW — URL routing)
  services/
    recommendation_service.py                 (NEW — business logic)
  tests/
    test_recommendations.py                   (NEW — integration tests)

apps/web/src/
  app/(authenticated)/mes-metiers/
    page.tsx                                  (NEW — Server Component)
    loading.tsx                               (NEW — skeleton UI)
  components/features/recommendations/
    MetiersList.tsx                           (NEW — Client Component)
    MetiersList.test.tsx                      (NEW — Vitest tests)
  lib/api/
    recommendations.ts                        (NEW — API client module)
```

**Files to MODIFY:**
```
apps/api/path_advisor/urls.py                 (ADD recommendations URLs include)
apps/web/tailwind.config.ts                   (ADD animate-fade-in keyframes if not present)
```

### References

- [Source: apps/api/apps/recommendations/services/ai_client.py] — `score_metiers()` signature
- [Source: apps/api/apps/students/models.py] — `StudentProfile`, `StudentLevelProfile` fields
- [Source: apps/api/apps/professions/models.py] — `Profession` model, `Profession.objects.filter(is_active=True)`
- [Source: apps/api/apps/professions/views.py] — APIView pattern + `record_audit` decorator pattern
- [Source: apps/web/src/components/professions/ScoreVocationnel.tsx] — component props
- [Source: apps/web/src/components/professions/types.ts] — `Signal`, `ScoreVocationnelProps`
- [Source: apps/web/src/lib/api/client.ts] — `apiFetch<T>()`, `ApiError`
- [Source: apps/web/src/lib/api/onboarding.ts] — pattern for typed API modules
- [Source: apps/web/src/app/(authenticated)/layout.tsx] — authenticated layout
- [Source: apps/web/AGENTS.md] — Next.js 16 warnings
- [Source: _bmad-output/implementation-artifacts/3-3-moteur-scoring-statistique-content-based.md] — scorer output schema

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

### File List
