/**
 * `/ecole/outreach/[id]` page tests — Story 5.6 + Story 5.12.
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

vi.mock("@/components/features/outreach/ecole-response-flow", () => ({
  EcoleResponseFlow: ({ outreach }: { outreach: { profession_name: string } }) => (
    <div data-testid="ecole-response-flow">{outreach.profession_name}</div>
  ),
}));

import { ApiError } from "@/lib/api/client";

import EcoleOutreachDetailPage from "./page";

describe("EcoleOutreachDetailPage", () => {
  it("fetches the detail and passes it to EcoleResponseFlow", async () => {
    fetchEcoleOutreachDetailMock.mockResolvedValue({
      id: "reach_1",
      student_age: 17,
      profession_name: "Infirmier·ère",
      parcours_label: "Bac STI2D → BUT",
      motivation_text: "Un texte de motivation détaillé.",
      status: "pending",
      response: null,
      created_at: "2026-09-10T00:00:00Z",
    });

    render(await EcoleOutreachDetailPage({ params: Promise.resolve({ id: "reach_1" }) }));

    expect(screen.getByTestId("ecole-response-flow")).toHaveTextContent("Infirmier·ère");
  });

  it("calls notFound() on a 404 (another school's request)", async () => {
    fetchEcoleOutreachDetailMock.mockRejectedValue(new ApiError(404, "Pas trouvé."));

    await EcoleOutreachDetailPage({ params: Promise.resolve({ id: "reach_2" }) });

    expect(notFoundMock).toHaveBeenCalled();
  });
});
