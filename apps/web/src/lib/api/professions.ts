import { cache } from "react";

import type { Profession } from "@/components/professions/types";

import { apiFetch } from "./client";

// React.cache() deduplicates concurrent calls within a single server render,
// ensuring generateMetadata and the page component share one network request.
export const fetchProfession = cache(async (slug: string): Promise<Profession> => {
  return apiFetch<Profession>(`/api/v1/professions/${slug}/`);
});
