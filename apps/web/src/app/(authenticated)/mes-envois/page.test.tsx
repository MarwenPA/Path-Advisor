/**
 * `/mes-envois` page tests — Story 5.4 §AC4 + Story 5.5 (rejected + resubmit).
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const fetchOutreachRequestsMock = vi.fn();
vi.mock("@/lib/api/outreach", () => ({
  fetchOutreachRequests: () => fetchOutreachRequestsMock(),
}));

vi.mock("@/components/features/outreach/resubmit-motivation-form", () => ({
  ResubmitMotivationForm: ({ rejectionReason }: { rejectionReason: string }) => (
    <div data-testid="resubmit-form">{rejectionReason}</div>
  ),
}));

import MesEnvoisPage from "./page";

describe("MesEnvoisPage", () => {
  it("shows the empty state with a link to /schools when there are no requests", async () => {
    fetchOutreachRequestsMock.mockResolvedValue({
      count: 0,
      next: null,
      previous: null,
      results: [],
    });

    render(await MesEnvoisPage());

    expect(screen.getByText(/tu n'as pas encore envoyé ton profil/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /voir les écoles partenaires/i })).toHaveAttribute(
      "href",
      "/schools",
    );
  });

  it("lists each request with school, métier visé, status and date", async () => {
    fetchOutreachRequestsMock.mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [
        {
          id: "reach_1",
          school_name: "École Test",
          profession_name: "Infirmier·ère",
          status: "pending",
          created_at: "2026-09-10T00:00:00Z",
        },
      ],
    });

    render(await MesEnvoisPage());

    const list = screen.getByTestId("mes-envois-list");
    expect(list).toHaveTextContent("École Test");
    expect(list).toHaveTextContent("Infirmier·ère");
    expect(list).toHaveTextContent("En attente");
  });

  it("shows the resubmit form for a rejected request", async () => {
    fetchOutreachRequestsMock.mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [
        {
          id: "reach_2",
          school_name: "École Test",
          profession_name: "Infirmier·ère",
          status: "rejected",
          rejection_reason: "Trop générique.",
          created_at: "2026-09-10T00:00:00Z",
        },
      ],
    });

    render(await MesEnvoisPage());

    const list = screen.getByTestId("mes-envois-list");
    expect(list).toHaveTextContent("Motivation refusée");
    expect(screen.getByTestId("resubmit-form")).toHaveTextContent("Trop générique.");
  });
});
