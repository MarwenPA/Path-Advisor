/**
 * `/mes-envois/[id]` page tests — Story 5.9.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const fetchOutreachRequestDetailMock = vi.fn();
vi.mock("@/lib/api/outreach", () => ({
  fetchOutreachRequestDetail: (...args: unknown[]) => fetchOutreachRequestDetailMock(...args),
}));

const notFoundMock = vi.fn();
vi.mock("next/navigation", () => ({
  notFound: () => notFoundMock(),
}));

import { ApiError } from "@/lib/api/client";

import MesEnvoisDetailPage from "./page";

describe("MesEnvoisDetailPage", () => {
  it("shows the motivation, the school's response, and the stat impact", async () => {
    fetchOutreachRequestDetailMock.mockResolvedValue({
      id: "reach_1",
      school_name: "École Test",
      school_slug: "ecole-test",
      profession_name: "Infirmier·ère",
      status: "responded",
      rejection_reason: "",
      motivation_text: "Ma motivation détaillée.",
      response: {
        action: "interested",
        comment: "Beau profil !",
        proposed_slots: [],
        accepted_slot: "",
        alternative_note: "",
        stat_delta: 15,
        created_at: "2026-09-10T00:00:00Z",
      },
      created_at: "2026-09-10T00:00:00Z",
    });

    render(await MesEnvoisDetailPage({ params: Promise.resolve({ id: "reach_1" }) }));

    expect(screen.getByText("Ma motivation détaillée.")).toBeInTheDocument();
    expect(screen.getByText(/profil intéressant/i)).toBeInTheDocument();
    expect(screen.getByText("Beau profil !")).toBeInTheDocument();
    expect(screen.getByText(/\+15 pts/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /voir la fiche de école test/i })).toHaveAttribute(
      "href",
      "/schools/ecole-test",
    );
  });

  it("calls notFound() on a 404", async () => {
    fetchOutreachRequestDetailMock.mockRejectedValue(new ApiError(404, "Pas trouvé."));

    await MesEnvoisDetailPage({ params: Promise.resolve({ id: "reach_2" }) });

    expect(notFoundMock).toHaveBeenCalled();
  });
});
