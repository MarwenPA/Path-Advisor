/**
 * `/ecole/outreach/[id]` page tests — Story 5.6.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const fetchEcoleOutreachDetailMock = vi.fn();
vi.mock("@/lib/api/ecole-outreach", () => ({
  fetchEcoleOutreachDetail: (...args: unknown[]) => fetchEcoleOutreachDetailMock(...args),
}));

const notFoundMock = vi.fn();
vi.mock("next/navigation", () => ({
  notFound: () => notFoundMock(),
}));

import { ApiError } from "@/lib/api/client";

import EcoleOutreachDetailPage from "./page";

describe("EcoleOutreachDetailPage", () => {
  it("shows the synthetic profile: age, métier, parcours, motivation, status", async () => {
    fetchEcoleOutreachDetailMock.mockResolvedValue({
      id: "reach_1",
      student_age: 17,
      profession_name: "Infirmier·ère",
      parcours_label: "Bac STI2D → BUT",
      motivation_text: "Un texte de motivation détaillé.",
      status: "pending",
      created_at: "2026-09-10T00:00:00Z",
    });

    render(await EcoleOutreachDetailPage({ params: Promise.resolve({ id: "reach_1" }) }));

    expect(screen.getByText("17 ans")).toBeInTheDocument();
    expect(screen.getByText("Infirmier·ère")).toBeInTheDocument();
    expect(screen.getByText("Bac STI2D → BUT")).toBeInTheDocument();
    expect(screen.getByText("Un texte de motivation détaillé.")).toBeInTheDocument();
    expect(screen.getByText("En attente")).toBeInTheDocument();
  });

  it("calls notFound() on a 404 (another school's request)", async () => {
    fetchEcoleOutreachDetailMock.mockRejectedValue(new ApiError(404, "Pas trouvé."));

    await EcoleOutreachDetailPage({ params: Promise.resolve({ id: "reach_2" }) });

    expect(notFoundMock).toHaveBeenCalled();
  });
});
