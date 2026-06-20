import type { Profession } from "@/components/professions/types";

import { apiFetch } from "./client";

export async function fetchProfession(slug: string): Promise<Profession> {
  return apiFetch<Profession>(`/api/v1/professions/${slug}/`);
}
