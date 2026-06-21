import { cache } from "react";

import { apiFetch } from "./client";

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
}

// React.cache() deduplicates concurrent calls within a single server render,
// ensuring generateMetadata and the page component share one network request.
export const fetchSchool = cache(async (slug: string): Promise<School> => {
  return apiFetch<School>(`/api/v1/schools/${slug}/`);
});
