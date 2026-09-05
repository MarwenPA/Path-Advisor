/**
 * `/auth/invitation-conseillere/[token]` page tests — Story 6.5 §T7.1.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const fetchStatusMock = vi.fn();
vi.mock("@/lib/api/establishments", () => ({
  fetchCounselorInvitationStatus: (...args: unknown[]) => fetchStatusMock(...args),
}));

vi.mock("@/components/features/establishments/counselor-invitation-form", () => ({
  CounselorInvitationForm: ({ token }: { token: string }) => (
    <div data-testid="form">form for {token}</div>
  ),
}));

import InvitationConseillerePage from "./page";

describe("InvitationConseillerePage", () => {
  it("renders the form for a pending invitation", async () => {
    fetchStatusMock.mockResolvedValue({
      establishment_name: "Lycée Test",
      email: "conseillere@ex.test",
      status: "pending",
    });

    render(await InvitationConseillerePage({ params: Promise.resolve({ token: "tok-1" }) }));

    expect(screen.getByText(/invitation de lycée test/i)).toBeInTheDocument();
    expect(screen.getByText("conseillere@ex.test")).toBeInTheDocument();
    expect(screen.getByTestId("form")).toHaveTextContent("tok-1");
  });

  it("shows the invalid-link message when the invitation is not pending", async () => {
    fetchStatusMock.mockResolvedValue({
      establishment_name: "Lycée Test",
      email: "conseillere@ex.test",
      status: "expired",
    });

    render(await InvitationConseillerePage({ params: Promise.resolve({ token: "tok-1" }) }));

    expect(screen.getByText(/n'est plus valide/i)).toBeInTheDocument();
    expect(screen.queryByTestId("form")).not.toBeInTheDocument();
  });

  it("shows the invalid-link message when the fetch fails (unknown token / API down)", async () => {
    // Code-review regression guard (2026-09-05): this page used to call a
    // bare fetch() reading an env var that's never set, silently falling
    // back to an unreachable host inside Docker — every visit rendered
    // this exact "lien invalide" message even for a valid, pending
    // invitation. This test only proves the *degrade* path is correct;
    // the actual host-resolution fix is that fetchCounselorInvitationStatus
    // (routed through apiFetch) is now the only thing called here.
    fetchStatusMock.mockRejectedValue(new Error("network down"));

    render(await InvitationConseillerePage({ params: Promise.resolve({ token: "tok-1" }) }));

    expect(screen.getByText(/n'est plus valide/i)).toBeInTheDocument();
  });
});
