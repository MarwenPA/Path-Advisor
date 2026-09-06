/**
 * <ResubmitMotivationForm> tests — Story 5.5.
 */
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

const routerMock = { refresh: vi.fn() };
vi.mock("next/navigation", () => ({
  useRouter: () => routerMock,
}));

const resubmitMock = vi.fn();
vi.mock("@/lib/api/outreach", () => ({
  resubmitOutreachRequest: (...args: unknown[]) => resubmitMock(...args),
}));

import { ResubmitMotivationForm } from "./resubmit-motivation-form";

beforeEach(() => {
  routerMock.refresh.mockClear();
  resubmitMock.mockReset();
});

describe("ResubmitMotivationForm", () => {
  it("shows the rejection reason and opens the rewrite textarea", () => {
    render(<ResubmitMotivationForm outreachId="reach_1" rejectionReason="Trop générique." />);

    expect(screen.getByText(/trop générique/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /réécrire ma motivation/i }));
    expect(screen.getByPlaceholderText(/réécris ta motivation/i)).toBeInTheDocument();
  });

  it("submits the new motivation and refreshes the page", async () => {
    resubmitMock.mockResolvedValue({ id: "reach_1", status: "pending_moderation" });
    render(<ResubmitMotivationForm outreachId="reach_1" rejectionReason="Trop générique." />);

    fireEvent.click(screen.getByRole("button", { name: /réécrire ma motivation/i }));
    fireEvent.change(screen.getByPlaceholderText(/réécris ta motivation/i), {
      target: { value: "Une motivation plus détaillée." },
    });
    fireEvent.click(screen.getByRole("button", { name: /soumettre à nouveau/i }));

    await waitFor(() => expect(routerMock.refresh).toHaveBeenCalled());
    expect(resubmitMock).toHaveBeenCalledWith("reach_1", "Une motivation plus détaillée.");
  });

  it("shows an error message on failure", async () => {
    resubmitMock.mockRejectedValue(new Error("network down"));
    render(<ResubmitMotivationForm outreachId="reach_1" rejectionReason="Trop générique." />);

    fireEvent.click(screen.getByRole("button", { name: /réécrire ma motivation/i }));
    fireEvent.change(screen.getByPlaceholderText(/réécris ta motivation/i), {
      target: { value: "Une motivation plus détaillée." },
    });
    fireEvent.click(screen.getByRole("button", { name: /soumettre à nouveau/i }));

    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
    expect(routerMock.refresh).not.toHaveBeenCalled();
  });
});
