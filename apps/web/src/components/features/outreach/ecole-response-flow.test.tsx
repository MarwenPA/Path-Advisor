/**
 * <EcoleResponseFlow> tests — Story 5.12.
 */
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

const routerMock = { refresh: vi.fn() };
vi.mock("next/navigation", () => ({
  useRouter: () => routerMock,
}));

const respondMock = vi.fn();
vi.mock("@/lib/api/ecole-outreach", () => ({
  respondToOutreachRequest: (...args: unknown[]) => respondMock(...args),
}));

import { EcoleResponseFlow } from "./ecole-response-flow";

const BASE = {
  id: "reach_1",
  student_age: 17,
  profession_name: "Infirmier·ère",
  parcours_label: "Bac STI2D → BUT",
  motivation_text: "Un texte de motivation.",
  status: "pending",
  created_at: "2026-09-10T00:00:00Z",
  response: null,
};

beforeEach(() => {
  routerMock.refresh.mockClear();
  respondMock.mockReset();
});

describe("EcoleResponseFlow", () => {
  it("renders the header, profil scolaire, motivation and métier/parcours sections", () => {
    render(<EcoleResponseFlow outreach={BASE} />);

    expect(screen.getAllByText("17 ans").length).toBeGreaterThan(0);
    expect(screen.getByText("Infirmier·ère")).toBeInTheDocument();
    expect(screen.getByText("Bac STI2D → BUT")).toBeInTheDocument();
    expect(screen.getByText("Un texte de motivation.")).toBeInTheDocument();
  });

  it("always shows the privacy reminder", () => {
    render(<EcoleResponseFlow outreach={BASE} />);

    expect(
      screen.getByText(/tu vois uniquement ce que l'élève a choisi de partager/i),
    ).toBeInTheDocument();
  });

  it("shows the 3-action footer for a pending request", () => {
    render(<EcoleResponseFlow outreach={BASE} />);

    expect(screen.getByRole("button", { name: /profil intéressant/i })).toBeInTheDocument();
  });

  it("shows the read-only response summary once answered", () => {
    render(
      <EcoleResponseFlow
        outreach={{
          ...BASE,
          status: "responded",
          response: {
            action: "interested",
            comment: "Beau profil.",
            accepted_slot: "",
            alternative_note: "",
          },
        }}
      />,
    );

    expect(screen.getByText(/réponse envoyée/i)).toBeInTheDocument();
    expect(screen.getByText("Beau profil.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /profil intéressant/i })).not.toBeInTheDocument();
  });

  it("supports the 'i' keyboard shortcut to answer interested", async () => {
    respondMock.mockResolvedValue({});
    render(<EcoleResponseFlow outreach={BASE} />);

    fireEvent.keyDown(window, { key: "i" });

    await waitFor(() => expect(routerMock.refresh).toHaveBeenCalled());
    expect(respondMock).toHaveBeenCalledWith(
      "reach_1",
      expect.objectContaining({ action: "interested" }),
    );
  });
});
