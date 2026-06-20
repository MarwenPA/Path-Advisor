# Story 3.5 — Fiche métier détaillée

## Status: ready-for-dev

## Story

**As** an élève,  
**I want** to consult a detailed profession sheet (description, daily routine, prerequisites, career prospects, salary),  
**so that** I understand concretely what a profession is before exploring its pathway (FR21).

## Acceptance Criteria

**AC1 — Navigation depuis la liste :**  
Given I tap on a ScoreVocationnel card in `/mes-metiers`  
When the page `/metiers/[slug]` opens  
Then I see the `FicheMetier` component with all sections: Hero (name + score + copyable phrase) / "C'est quoi" / "Pour qui" / "Comment y aller" / "Infos pratiques" / "Signaux contributifs"  
And if score is available (passed via query params), it is shown in the hero  
And if score is not available (direct URL), the FicheMetier renders without score

**AC2 — Responsive :**  
Given the sheet is responsive  
When I view it on mobile (< 1024px)  
Then sections are stacked and accordion collapses non-priority sections  
When I view it on desktop (≥ 1024px)  
Then sticky sidebar TOC allows navigation between sections

**AC3 — Accessibilité :**  
When a screen reader user views the sheet  
Then the h1 → h2 → h3 hierarchy is strict (1 h1 per page, no skip)  
And sections are announced semantically

**AC4 — 404 gracieux :**  
Given the slug doesn't exist or the profession is inactive  
When the page loads  
Then a 404 `notFound()` page is shown (Next.js built-in)

**AC5 — Skeleton loading :**  
Given the profession is fetching  
When the page is loading  
Then a skeleton placeholder is shown via `loading.tsx`

**AC6 — Lien retour :**  
When viewing `/metiers/[slug]`  
Then a back link "← Mes métiers" navigates to `/mes-metiers`

## Tasks / Subtasks

- [ ] **Task 1 — API client Next.js**
  - [ ] 1.1 Create `apps/web/src/lib/api/professions.ts` with `fetchProfession(slug: string): Promise<Profession>`
  - [ ] 1.2 Reuse existing `Profession` interface from `@/components/professions/types`
  - [ ] 1.3 Write Vitest unit test: mock fetch, assert field mapping, 404 throws ApiError

- [ ] **Task 2 — Page `/metiers/[slug]`**
  - [ ] 2.1 Create directory `apps/web/src/app/(authenticated)/metiers/[slug]/`
  - [ ] 2.2 Create `page.tsx` (Server Component): fetch profession + read score/confidence from `searchParams`, render `FicheMetier`
  - [ ] 2.3 Create `loading.tsx`: skeleton placeholder matching FicheMetier dimensions
  - [ ] 2.4 Update `MetiersList.tsx` links to include `?score={score}&confidence={confidence_level}` in the href

- [ ] **Task 3 — Tests Vitest**
  - [ ] 3.1 Test `fetchProfession` — success case, 404 case
  - [ ] 3.2 Test `MetiersList` link hrefs include score and confidence query params

## Dev Notes

### Architecture — ce qui existe déjà (NE PAS recréer)

**Backend — 100% déjà implémenté :**
- `GET /api/v1/professions/{slug}/` → `PublicProfessionDetailView` dans `apps/api/apps/professions/views.py`
- Retourne `ProfessionPublicSerializer` (tous les champs publics)
- Audit-logged `profession_viewed` event (Story 1.13)
- Déjà inclus dans `path_advisor/urls.py` via `path("api/v1/", include("apps.professions.urls"))`
- **Aucun changement Django nécessaire pour cette story**

**Frontend — composant déjà implémenté :**
- `apps/web/src/components/professions/FicheMetier.tsx` — composant complet (638 lignes)
  - Props: `{ profession: Profession; score?: number; phraseRecopiable?: string; confidenceLevel?: "normal" | "indicative"; variant?: "default" | "mobile" | "print"; onSignalClick?: (signalId: string) => void }`
  - Responsive auto-detection via `useMediaQuery("(min-width: 1024px)")` interne
  - Mobile: accordion sur "Pour qui", "Comment y aller", "Infos pratiques"
  - Desktop: sticky TOC + scroll-spy IntersectionObserver
  - `score` et `phraseRecopiable` sont **optionnels** → rendu OK sans score

### API client pattern (REUSE — ne pas réinventer)

```ts
// apps/web/src/lib/api/professions.ts
import { apiFetch } from "./client";
import type { Profession } from "@/components/professions/types";

export async function fetchProfession(slug: string): Promise<Profession> {
  return apiFetch<Profession>(`/api/v1/professions/${slug}/`);
}
```

`apiFetch` (client.ts) :
- Gère cookies SSR via `headers()` de Next.js
- Lance `ApiError` sur 401/403/404/5xx (RFC 7807)
- Timeout 15 s

### Page pattern (Server Component avec searchParams)

```tsx
// apps/web/src/app/(authenticated)/metiers/[slug]/page.tsx
import { notFound } from "next/navigation";
import { FicheMetier } from "@/components/professions/FicheMetier";
import { ApiError } from "@/lib/api/client";
import { fetchProfession } from "@/lib/api/professions";

export default async function MetierDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ score?: string; confidence?: string }>;
}) {
  const { slug } = await params;
  const { score: scoreStr, confidence } = await searchParams;

  let profession;
  try {
    profession = await fetchProfession(slug);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err; // let error.tsx handle 5xx
  }

  const score = scoreStr ? parseInt(scoreStr, 10) : undefined;
  const confidenceLevel =
    confidence === "low" ? "indicative" : confidence ? "normal" : undefined;

  return (
    <main>
      <FicheMetier
        profession={profession}
        score={score}
        confidenceLevel={confidenceLevel}
      />
    </main>
  );
}
```

**IMPORTANT Next.js 15/16 — `params` et `searchParams` sont des Promises** et doivent être `await`-és. Voir les autres pages du projet pour confirmation.

### searchParams depuis MetiersList

Modifier le lien dans `MetiersList.tsx` :

```tsx
// Avant:
href={`/metiers/${p.slug}`}

// Après:
href={`/metiers/${p.slug}?score=${p.score}&confidence=${p.confidence_level}`}
```

### Skeleton loading pattern (cohérent avec 3.4)

```tsx
// loading.tsx
export default function MetierDetailLoading() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-8 animate-pulse">
      <div className="mb-4 h-8 w-64 rounded bg-gray-200" />
      <div className="mb-2 h-4 w-full rounded bg-gray-100" />
      <div className="mb-2 h-4 w-5/6 rounded bg-gray-100" />
      <div className="mb-8 h-4 w-4/6 rounded bg-gray-100" />
      <div className="h-40 w-full rounded-xl bg-gray-100" />
    </div>
  );
}
```

### Lien retour

Dans la page, inclure un lien "← Mes métiers" AVANT le `FicheMetier` :

```tsx
import Link from "next/link";
// ...
<Link href="/mes-metiers" className="mb-4 flex items-center gap-1 text-body-sm text-text-muted hover:text-text-primary">
  ← Mes métiers
</Link>
```

### Confidence mapping (rappel depuis 3.4)

| ai-service `confidence_level` | `FicheMetierProps.confidenceLevel` |
|---|---|
| `"low"` | `"indicative"` |
| `"medium"` | `"normal"` |
| `"high"` | `"normal"` |
| absent | `undefined` (composant n'affiche pas) |

### Interface Profession (EXISTING — ne pas redéfinir)

`apps/web/src/components/professions/types.ts` contient déjà :

```ts
export interface Profession {
  id: string;
  slug: string;
  name: string;
  description: string;
  daily_routine: string;
  requirements_json: RequirementItem[];
  prospects_text: string;
  median_salary_eur?: number | null;
  salary_range_json?: SalaryRange | null;
  signals_json: SignalsByCategory;
  level_compatibility: string[];
  sector?: string;
  rome_code?: string | null;
}
```

**Importer depuis `@/components/professions/types`** — ne pas recréer dans `lib/api/professions.ts`.

### Tests pattern (cohérent avec 3.4)

```ts
// apps/web/src/lib/api/__tests__/professions.test.ts
import { describe, it, expect, vi, afterEach } from "vitest";
import { fetchProfession } from "../professions";

vi.mock("../client", () => ({
  apiFetch: vi.fn(),
}));

// test success + 404 throw
```

### Règles de qualité

- **Pas de `"use client"` sur `page.tsx`** — c'est un Server Component pur
- **FicheMetier est déjà `"use client"`** — il gère sa propre réactivité
- **Pas de refetch côté client** — les données arrivent SSR via le Server Component
- **`notFound()` uniquement sur 404** — les erreurs 5xx doivent propager (error boundary)
- **`onSignalClick` non implémenté en 3.5** — sera branché en Story 3.6 (explicabilité)
- **`phraseRecopiable` laissé vide** — généré en Story 3.6 également
- Pas d'état local dans `page.tsx` — tout est props

### Fichiers à créer / modifier

**CRÉER :**
- `apps/web/src/lib/api/professions.ts`
- `apps/web/src/app/(authenticated)/metiers/[slug]/page.tsx`
- `apps/web/src/app/(authenticated)/metiers/[slug]/loading.tsx`
- `apps/web/src/lib/api/__tests__/professions.test.ts`

**MODIFIER :**
- `apps/web/src/app/(authenticated)/mes-metiers/MetiersList.tsx` — ajouter `?score=&confidence=` aux liens

**NE PAS CRÉER :**
- Nouveaux composants Django — tout est déjà fait
- Nouveaux serializers
- Nouvelles permissions
- Nouveaux modèles

### Commits précédents (patterns à suivre)

```
feat(story-3-4): liste métiers scorés — Django RecommendationService + ...
feat(story-3-1): activate ai-service for vocational scoring — JWT HS256 ...
```

## Dev Agent Record

### Implementation Plan
- Task 1: API client `fetchProfession` + test
- Task 2: Page SSR `/metiers/[slug]` + loading skeleton + update MetiersList links
- Task 3: Tests Vitest (fetchProfession + MetiersList link update)

### File List
<!-- populated by dev agent -->

### Change Log
<!-- populated by dev agent -->

### Debug Log
<!-- populated by dev agent -->

### Completion Notes
<!-- populated by dev agent -->
