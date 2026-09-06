/**
 * API types and fetchers for schools / admission stats.
 *
 * Story 4.4: School + Formation types + fetchSchool helper.
 * Story 4.11: `AdmissionStat` type + `fetchAdmissionStat` helper.
 * All JSON field names stay snake_case (project-wide convention).
 */

import { cache } from "react";

import { apiFetch } from "./client";

export interface AdmissionStat {
  min_proba: number; // 0-100, percentage
  expected_proba: number; // 0-100, percentage (primary display value)
  max_proba: number; // 0-100, percentage
  label: "audacieux" | "realiste" | "sur" | "estimation_indicative";
  context_line: string; // e.g. "Moyenne admise 2024 : 14,5"
  action_lever: string | null; // e.g. "+ 2 points en maths feraient passer à 58 %"
  updated_at?: string; // ISO 8601 UTC, optional
  previous_proba?: number; // Previous session probability for delta badge
  compatibility?: "compatible" | "a_renforcer" | "au_dessus" | null; // Added by Story 4.13
}

export interface Formation {
  id: string;
  name: string;
  duration_years: number;
  parcoursup_open: boolean;
  affelnet_open: boolean;
}

export interface School {
  // Story 7.2 — absent from the anonymous SEO endpoint's payload
  // (`SchoolPublicSeoSerializer`, internal PK never rendered for the
  // "expanded" variant `<FicheEcole>` uses on the public fiche); only the
  // "compare" variant's checkbox reads `.id`, unreachable from that page.
  id?: string;
  slug: string;
  name: string;
  type: string;
  city: string;
  region: string;
  postal_code: string;
  lat?: number;
  lon?: number;
  apprenticeship: boolean;
  internship: boolean;
  selectivity_index: number;
  public_private: string;
  description: string;
  top_debouches: string[];
  parcoursup_dates: Record<string, string>;
  affelnet_dates: Record<string, string>;
  official_url: string;
  tuition_min_eur?: number;
  tuition_max_eur?: number;
  formations: Formation[];
  admission_stat?: AdmissionStat;
  // Story 7.2 — cross-linking on the public fiche; only present from
  // `fetchPublicSchool`, absent from the authenticated `fetchSchool`.
  metiers_cibles?: { slug: string; name: string }[];
  similar_schools?: { slug: string; name: string; city: string }[];
}

// React.cache() deduplicates concurrent calls within a single server render,
// ensuring generateMetadata and the page component share one network request.
export const fetchSchool = cache(async (slug: string): Promise<School> => {
  return apiFetch<School>(`/api/v1/schools/${slug}/`);
});

/**
 * `GET /api/v1/public/schools/{slug}/` — Story 7.2. `AllowAny` backend
 * endpoint; used by the public `/formations/{slug}` SSR page. No
 * `admission_stat` in the payload (see `SchoolPublicSeoSerializer`), so
 * `<FicheEcole>` naturally skips the personalized admission poller.
 */
export const fetchPublicSchool = cache(async (slug: string): Promise<School> => {
  return apiFetch<School>(`/api/v1/public/schools/${slug}/`);
});

/**
 * `GET /api/v1/schools/{slug}/admission-stat/` — Story 4.2's real endpoint
 * (`AdmissionStatView`). Story 5.8 code-review fix: this previously POSTed
 * to `/api/v1/schools/predict-admission/`, a route that doesn't exist
 * server-side (404) — dead code, never actually called anywhere in the
 * app until Story 5.8's 30s polling (below) became its first real caller.
 */
export async function fetchAdmissionStat(schoolSlug: string): Promise<AdmissionStat> {
  return apiFetch<AdmissionStat>(
    `/api/v1/schools/${encodeURIComponent(schoolSlug)}/admission-stat/`,
  );
}

/**
 * Lightweight catalog row — mirrors the backend's `SchoolCatalogSerializer`
 * (deliberately narrower than `School`, the full detail type above — no
 * `formations`/`admission_stat` for a list of 70+ cards).
 */
export interface SchoolCatalogItem {
  id: string;
  slug: string;
  name: string;
  type: string;
  city: string;
  region: string;
  selectivity_index: number;
}

export interface PaginatedSchools {
  count: number;
  next: string | null;
  previous: string | null;
  results: SchoolCatalogItem[];
}

/** `GET /api/v1/schools/` — full schools catalog. */
export async function fetchSchools(page = 1): Promise<PaginatedSchools> {
  return apiFetch<PaginatedSchools>(`/api/v1/schools/?page=${page}`);
}
