import { cache } from "react";

import type { Profession } from "@/components/professions/types";

import { apiFetch } from "./client";

// React.cache() deduplicates concurrent calls within a single server render,
// ensuring generateMetadata and the page component share one network request.
export const fetchProfession = cache(async (slug: string): Promise<Profession> => {
  return apiFetch<Profession>(`/api/v1/professions/${slug}/`);
});

/**
 * `GET /api/v1/public/professions/{slug}/` — Story 7.1. AllowAny backend
 * endpoint; used by the public `/metiers/{slug}` SSR page so an anonymous
 * visitor (and Google/Bing) never depends on the auth-gated endpoint above.
 * `forwardCookies: false` — Epic 7 review fix: forwarding cookies calls
 * `cookies()`, which forced every public page dynamic and made their
 * `revalidate = 3600` inert (see `apiFetch`'s docstring).
 */
export const fetchPublicProfession = cache(async (slug: string): Promise<Profession> => {
  return apiFetch<Profession>(`/api/v1/public/professions/${slug}/`, { forwardCookies: false });
});

/** Story 7.4 — `{slug, updated_at}` rows for `app/sitemap.ts`. */
export interface ProfessionSlugRow {
  slug: string;
  updated_at: string;
}

export async function fetchPublicProfessionSlugs(): Promise<ProfessionSlugRow[]> {
  // AllowAny endpoint — no cookies, same rationale as fetchPublicProfession.
  return apiFetch<ProfessionSlugRow[]>("/api/v1/public/professions/slugs/", {
    forwardCookies: false,
  });
}

/**
 * Lightweight catalog row — Story 3.13. Mirrors the backend's
 * `ProfessionCatalogSerializer` (deliberately narrower than `Profession`,
 * the full detail type above — no `daily_routine`/`requirements_json`/
 * `prospects_text`/`signals_json` for a list of 50+ cards).
 */
export interface ProfessionCatalogItem {
  id: string;
  slug: string;
  name: string;
  description: string;
  sector?: string;
  median_salary_eur?: number | null;
}

export interface PaginatedProfessions {
  count: number;
  next: string | null;
  previous: string | null;
  results: ProfessionCatalogItem[];
}

/** `GET /api/v1/professions/` — full catalog (Story 3.13 repli, AC1). */
export async function fetchProfessions(page = 1): Promise<PaginatedProfessions> {
  return apiFetch<PaginatedProfessions>(`/api/v1/professions/?page=${page}`);
}
