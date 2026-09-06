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

// --- Dedicated detail views (AC2, code review 2026-08) ---------------------

export interface ParentMetierDetail {
  metier_id: string;
  slug: string;
  name: string;
  sector: string | null;
  description: string;
  daily_routine: string;
  median_salary_eur: number | null;
  prospects_text: string;
  score: number | null;
  confidence_level: "low" | "medium" | "high" | null;
  signals: ParentProfessionSignal[];
}

export interface ParentEcoleFormation {
  name: string;
  duration_years: number;
  parcoursup_open: boolean;
  affelnet_open: boolean;
}

/** Story 6.3 §AC3 — every `AdmissionStat` field except `action_lever` (it
 * names a subject + grade delta, indirectly revealing a bulletin figure). */
export interface ParentAdmissionStat {
  min_proba: number;
  expected_proba: number;
  max_proba: number;
  label: "audacieux" | "realiste" | "sur" | "estimation_indicative";
  context_line: string;
  previous_proba: number | null;
  updated_at: string;
}

export interface ParentEcoleDetail {
  school_id: string;
  slug: string;
  name: string;
  type: string;
  city: string;
  region: string;
  description: string;
  tuition_min_eur: number | null;
  tuition_max_eur: number | null;
  formations: ParentEcoleFormation[];
  admission_stat: ParentAdmissionStat | null;
}

export async function fetchChildMetierDetail(
  studentId: string,
  slug: string,
): Promise<ParentMetierDetail> {
  return apiFetch<ParentMetierDetail>(
    `/api/v1/family/children/${encodeURIComponent(studentId)}/metiers/${encodeURIComponent(slug)}/`,
  );
}

export async function fetchChildEcoleDetail(
  studentId: string,
  slug: string,
): Promise<ParentEcoleDetail> {
  return apiFetch<ParentEcoleDetail>(
    `/api/v1/family/children/${encodeURIComponent(studentId)}/ecoles/${encodeURIComponent(slug)}/`,
  );
}
