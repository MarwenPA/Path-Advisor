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
  id: string;
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
}

// React.cache() deduplicates concurrent calls within a single server render,
// ensuring generateMetadata and the page component share one network request.
export const fetchSchool = cache(async (slug: string): Promise<School> => {
  return apiFetch<School>(`/api/v1/schools/${slug}/`);
});

export async function fetchAdmissionStat(schoolSlug: string): Promise<AdmissionStat> {
  return apiFetch<AdmissionStat>("/api/v1/schools/predict-admission/", {
    method: "POST",
    body: { school_slug: schoolSlug },
  });
}
