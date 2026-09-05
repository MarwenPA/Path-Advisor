import { cache } from "react";

import type { Profession } from "@/components/professions/types";

import { apiFetch } from "./client";

// React.cache() deduplicates concurrent calls within a single server render,
// ensuring generateMetadata and the page component share one network request.
export const fetchProfession = cache(async (slug: string): Promise<Profession> => {
  return apiFetch<Profession>(`/api/v1/professions/${slug}/`);
});

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
