/**
 * <EcoleRespondForm> tests — Story 5.7.
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

import { EcoleRespondForm } from "./ecole-respond-form";

beforeEach(() => {
  routerMock.refresh.mockClear();
  respondMock.mockReset();
});

describe("EcoleRespondForm", () => {
  it("submits 'interested' directly", async () => {
    respondMock.mockResolvedValue({});
    render(<EcoleRespondForm outreachId="reach_1" />);

    fireEvent.click(screen.getByRole("button", { name: /profil intéressant/i }));

    await waitFor(() => expect(routerMock.refresh).toHaveBeenCalled());
    expect(respondMock).toHaveBeenCalledWith(
      "reach_1",
      expect.objectContaining({ action: "interested" }),
    );
  });

  it("shows a confirmation step for 'not aligned' before submitting", async () => {
    respondMock.mockResolvedValue({});
    render(<EcoleRespondForm outreachId="reach_1" />);

    fireEvent.click(screen.getByRole("button", { name: /profil non aligné/i }));
    expect(screen.getByText(/respectueux et constructif/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /confirmer/i }));

    await waitFor(() =>
      expect(respondMock).toHaveBeenCalledWith(
        "reach_1",
        expect.objectContaining({ action: "not_aligned" }),
      ),
    );
  });

  it("requires at least 2 slots for an interview request", () => {
    render(<EcoleRespondForm outreachId="reach_1" />);

    fireEvent.click(screen.getByRole("button", { name: /demande d'entretien/i }));

    expect(screen.getByRole("button", { name: /proposer ces créneaux/i })).toBeDisabled();
  });

  it("shows an error message on failure", async () => {
    respondMock.mockRejectedValue(new Error("network down"));
    render(<EcoleRespondForm outreachId="reach_1" />);

    fireEvent.click(screen.getByRole("button", { name: /profil intéressant/i }));

    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
  });
});
