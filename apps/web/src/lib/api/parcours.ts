import type { Parcours } from "@/components/parcours/types";

import { apiFetch } from "./client";

/**
 * Fetch the list of parcours for a given métier slug.
 * Optionally filter by niveau_scolaire.
 *
 * Returns an empty array if the métier has no parcours yet (API returns 200 []).
 */
export async function fetchParcours(
  metiersSlug: string,
  niveauScolaire?: string,
): Promise<Parcours[]> {
  const params = niveauScolaire ? `?niveau_scolaire=${encodeURIComponent(niveauScolaire)}` : "";
  return apiFetch<Parcours[]>(`/api/v1/metiers/${metiersSlug}/parcours/${params}`);
}
