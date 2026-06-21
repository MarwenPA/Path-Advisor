/**
 * API types and fetchers for parcours — Story 4.7.
 *
 * `Parcours` holds the pathway graph for a profession and niveau scolaire.
 * `fetchParcours` fetches the list of parcours for a given profession slug,
 * optionally filtered by niveau scolaire.
 */

import { apiFetch } from "./client";

export type NiveauScolaire =
  | "troisieme_bac_pro"
  | "terminale_generale"
  | "terminale_technologique"
  | "terminale_pro"
  | "autre";

export interface ParcoursNode {
  id: string;
  label: string;
  type: "start" | "diplome" | "intermediate" | "target";
  schoolSlug?: string | null;
}

export interface ParcoursEdge {
  source: string;
  target: string;
  weight?: number;
}

export interface Parcours {
  id: string;
  profession: string;
  target_school_slug: string | null;
  target_school_name: string | null;
  niveau_scolaire: NiveauScolaire | string;
  is_default: boolean;
  nodes: ParcoursNode[];
  edges: ParcoursEdge[];
  label: string;
  target_school_affelnet_dates: Record<string, string> | null;
  target_school_parcoursup_dates: Record<string, string> | null;
  created_at?: string;
  updated_at?: string;
}

/**
 * Fetch parcours list for a given profession slug.
 * Optionally filter by niveau scolaire (with fallback to terminale_generale on backend).
 */
export async function fetchParcours(slug: string, niveauScolaire?: string): Promise<Parcours[]> {
  const params = niveauScolaire ? `?niveau_scolaire=${encodeURIComponent(niveauScolaire)}` : "";
  return apiFetch<Parcours[]>(`/api/v1/metiers/${slug}/parcours/${params}`);
}
