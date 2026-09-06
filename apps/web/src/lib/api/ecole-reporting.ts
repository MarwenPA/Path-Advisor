/**
 * API client for the school-side reporting dashboard — Story 5.10.
 */
import { apiFetch } from "@/lib/api/client";

export interface EcoleReportingByProfession {
  profession_name: string;
  count: number;
}

export interface EcoleReportingByAction {
  action: "interested" | "not_aligned" | "interview_requested" | "no_response";
  count: number;
}

export interface EcoleReportingByMonth {
  month: string; // ISO date, first of month
  count: number;
}

export interface EcoleReporting {
  total_this_month: number;
  total_this_year: number;
  by_profession: EcoleReportingByProfession[];
  by_action: EcoleReportingByAction[];
  by_month: EcoleReportingByMonth[];
}

export async function fetchEcoleReporting(): Promise<EcoleReporting> {
  return apiFetch<EcoleReporting>("/api/v1/ecole/reporting/");
}

/** Story 5.10 AC — CSV export URL (a plain link, not a fetch: the browser
 * handles the file download via Content-Disposition). */
export const ECOLE_REPORTING_EXPORT_URL = "/api/v1/ecole/reporting/export.csv/";
