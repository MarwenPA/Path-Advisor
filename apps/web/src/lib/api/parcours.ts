/**
 * API types and fetchers for parcours — Story 4.3 / 4.7.
 *
 * Re-exports Parcours type from the canonical types.ts for convenience.
 * `fetchParcours` fetches the list of parcours for a given profession slug,
 * optionally filtered by niveau scolaire (with backend fallback to terminale_generale).
 */

import type { Parcours } from "@/components/parcours/types";

import { apiFetch } from "./client";

export type { Parcours };
export type { ParcoursNode, ParcoursEdge } from "@/components/parcours/types";

/**
 * Fetch parcours list for a given profession slug.
 * Optionally filter by niveau scolaire (with fallback to terminale_generale on backend).
 */
export async function fetchParcours(
  metiersSlug: string,
  niveauScolaire?: string,
): Promise<Parcours[]> {
  const params = niveauScolaire ? `?niveau_scolaire=${encodeURIComponent(niveauScolaire)}` : "";
  return apiFetch<Parcours[]>(`/api/v1/metiers/${metiersSlug}/parcours/${params}`);
}
