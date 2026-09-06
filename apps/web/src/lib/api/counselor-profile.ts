/**
 * API client for the counselor-side individual student profile view —
 * Story 6.8.
 */
import { apiFetch, readCsrfCookie } from "@/lib/api/client";

export interface CounselorProfileProfession {
  metier_id: string | null;
  slug: string | null;
  name: string | null;
  sector: string | null;
  score: number;
  confidence_level: string;
}

export interface CounselorProfileEcole {
  school_id: string;
  slug: string;
  name: string;
  city: string;
  type: string;
}

export interface CounselorStudentProfile {
  student_id: string;
  cohort_name: string | null;
  metiers_top_recos: CounselorProfileProfession[];
  mes_paris: CounselorProfileEcole[];
  activite_recente: { derniere_connexion: string | null };
  voeux_en_construction: unknown[];
}

export interface CounselorNote {
  id: string;
  text: string;
  created_at: string;
}

export async function fetchCounselorStudentProfile(
  studentId: string,
): Promise<CounselorStudentProfile> {
  return apiFetch<CounselorStudentProfile>(
    `/api/v1/establishments/students/${encodeURIComponent(studentId)}/profile/`,
  );
}

export async function fetchCounselorNotes(studentId: string): Promise<CounselorNote[]> {
  return apiFetch<CounselorNote[]>(
    `/api/v1/establishments/students/${encodeURIComponent(studentId)}/notes/`,
  );
}

export async function addCounselorNote(studentId: string, text: string): Promise<CounselorNote> {
  return apiFetch<CounselorNote>(
    `/api/v1/establishments/students/${encodeURIComponent(studentId)}/notes/`,
    { method: "POST", body: { text }, csrfToken: readCsrfCookie() ?? undefined },
  );
}

/** A plain link, not a fetch — the browser handles the file download via
 * Content-Disposition, same pattern as `ECOLE_REPORTING_EXPORT_URL`. */
export function buildInterviewSheetPdfUrl(studentId: string): string {
  return `/api/v1/establishments/students/${encodeURIComponent(studentId)}/interview-sheet.pdf/`;
}
