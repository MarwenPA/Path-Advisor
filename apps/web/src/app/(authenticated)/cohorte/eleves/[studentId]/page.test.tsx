/**
 * `/cohorte/eleves/[studentId]` page tests — Story 6.8.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const fetchCounselorStudentProfileMock = vi.fn();
const fetchCounselorNotesMock = vi.fn();
vi.mock("@/lib/api/counselor-profile", async () => {
  const actual = await vi.importActual("@/lib/api/counselor-profile");
  return {
    ...actual,
    fetchCounselorStudentProfile: (...args: unknown[]) => fetchCounselorStudentProfileMock(...args),
    fetchCounselorNotes: (...args: unknown[]) => fetchCounselorNotesMock(...args),
  };
});

const notFoundMock = vi.fn();
vi.mock("next/navigation", () => ({
  notFound: () => notFoundMock(),
}));

vi.mock("@/components/features/establishments/counselor-notes-panel", () => ({
  CounselorNotesPanel: ({ initialNotes }: { initialNotes: { id: string }[] }) => (
    <div data-testid="notes-panel">{initialNotes.length} note(s)</div>
  ),
}));

import { ApiError } from "@/lib/api/client";

import CounselorStudentProfilePage from "./page";

const BASE_PROFILE = {
  student_id: "usr_1",
  cohort_name: "Terminale 2025-2026",
  metiers_top_recos: [
    {
      metier_id: "prof_1",
      slug: "infirmier",
      name: "Infirmier·ère",
      sector: "santé",
      score: 82,
      confidence_level: "high",
    },
  ],
  mes_paris: [{ school_id: "sch_1", slug: "bts-a", name: "BTS A", city: "Paris", type: "bts" }],
  activite_recente: { derniere_connexion: "2026-09-01T10:00:00Z" },
  voeux_en_construction: [],
};

describe("CounselorStudentProfilePage", () => {
  it("renders the profile sections and notes panel", async () => {
    fetchCounselorStudentProfileMock.mockResolvedValue(BASE_PROFILE);
    fetchCounselorNotesMock.mockResolvedValue([
      { id: "note_1", text: "RAS", created_at: "2026-09-01T10:00:00Z" },
    ]);

    render(await CounselorStudentProfilePage({ params: Promise.resolve({ studentId: "usr_1" }) }));

    expect(screen.getByText("Infirmier·ère")).toBeInTheDocument();
    expect(screen.getByText(/BTS A/)).toBeInTheDocument();
    expect(screen.getByTestId("notes-panel")).toHaveTextContent("1 note(s)");
    expect(screen.getByText("Exporter fiche entretien (PDF)")).toBeInTheDocument();
  });

  it("shows a consent-required fallback on 403", async () => {
    fetchCounselorStudentProfileMock.mockRejectedValue(new ApiError(403, "Consentement requis."));
    fetchCounselorNotesMock.mockResolvedValue([]);

    render(await CounselorStudentProfilePage({ params: Promise.resolve({ studentId: "usr_2" }) }));

    expect(screen.getByText("Consentement requis")).toBeInTheDocument();
  });

  it("calls notFound() on a 404", async () => {
    fetchCounselorStudentProfileMock.mockRejectedValue(new ApiError(404, "Pas trouvé."));
    fetchCounselorNotesMock.mockResolvedValue([]);

    await CounselorStudentProfilePage({ params: Promise.resolve({ studentId: "usr_3" }) });

    expect(notFoundMock).toHaveBeenCalled();
  });
});
