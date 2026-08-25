/**
 * Parent dashboard API client — Story 6.2 §T5.1.
 *
 * Read-only endpoints a linked parent uses to view a child's explored
 * professions, saved "mes paris" and estimated parcours costs (FR41).
 * Bulletins are NEVER exposed — the backend returns 403 on any bulletin route.
 * Mirrors the Django DTOs 1:1 (snake_case in transit).
 */
import { apiFetch } from "@/lib/api/client";

export interface LinkedChild {
  id: string;
  first_name: string;
  masked_email: string;
}

export interface ParentProfessionSignal {
  id: string;
  label: string;
}

export interface ParentProfession {
  metier_id: string;
  slug: string;
  name: string;
  sector: string | null;
  score: number;
  confidence_level: "low" | "medium" | "high";
  signals: ParentProfessionSignal[];
  phrase_recopiable: string;
}

export interface ParentMesParisItem {
  school_id: string;
  slug: string;
  name: string;
  city: string;
  type: string;
  tuition_min_eur: number | null;
  tuition_max_eur: number | null;
}

export interface ParentCostBreakdownItem {
  school_id: string;
  school_name: string;
  tuition_min_eur: number | null;
  tuition_max_eur: number | null;
}

export interface ParentCosts {
  total_min_eur: number;
  total_max_eur: number;
  count: number;
  breakdown: ParentCostBreakdownItem[];
}

export interface ParentChildDashboard {
  child: LinkedChild;
  metiers_explores: ParentProfession[];
  mes_paris: ParentMesParisItem[];
  couts_estimes: ParentCosts;
}

export async function fetchLinkedChildren(): Promise<LinkedChild[]> {
  return apiFetch<LinkedChild[]>("/api/v1/family/children/");
}

export async function fetchChildDashboard(studentId: string): Promise<ParentChildDashboard> {
  return apiFetch<ParentChildDashboard>(
    `/api/v1/family/children/${encodeURIComponent(studentId)}/dashboard/`,
  );
}
