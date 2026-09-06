/**
 * `/ecole/outreach` page tests — Story 5.6.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const fetchEcoleOutreachQueueMock = vi.fn();
vi.mock("@/lib/api/ecole-outreach", () => ({
  fetchEcoleOutreachQueue: (...args: unknown[]) => fetchEcoleOutreachQueueMock(...args),
}));

import EcoleOutreachQueuePage from "./page";

describe("EcoleOutreachQueuePage", () => {
  it("shows an empty state when there are no requests", async () => {
    fetchEcoleOutreachQueueMock.mockResolvedValue({
      count: 0,
      next: null,
      previous: null,
      results: [],
    });

    render(await EcoleOutreachQueuePage({ searchParams: Promise.resolve({}) }));

    expect(screen.getByText(/aucun profil reçu/i)).toBeInTheDocument();
  });

  it("lists received requests with métier, age and status", async () => {
    fetchEcoleOutreachQueueMock.mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [
        {
          id: "reach_1",
          student_age: 17,
          profession_name: "Infirmier·ère",
          parcours_label: "Bac STI2D → BUT",
          status: "pending",
          created_at: "2026-09-10T00:00:00Z",
        },
      ],
    });

    render(await EcoleOutreachQueuePage({ searchParams: Promise.resolve({}) }));

    const list = screen.getByTestId("ecole-outreach-list");
    expect(list).toHaveTextContent("Infirmier·ère");
    expect(list).toHaveTextContent("17 ans");
    expect(list).toHaveTextContent("En attente");
    expect(screen.getByRole("link", { name: /infirmier·ère/i })).toHaveAttribute(
      "href",
      "/ecole/outreach/reach_1",
    );
  });

  it("forwards the status filter to the API", async () => {
    fetchEcoleOutreachQueueMock.mockResolvedValue({
      count: 0,
      next: null,
      previous: null,
      results: [],
    });

    render(
      await EcoleOutreachQueuePage({ searchParams: Promise.resolve({ status: "responded" }) }),
    );

    expect(fetchEcoleOutreachQueueMock).toHaveBeenCalledWith({
      status: "responded",
      ordering: "-created_at",
    });
  });
});
