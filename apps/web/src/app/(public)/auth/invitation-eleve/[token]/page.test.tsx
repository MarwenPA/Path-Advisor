/**
 * `/auth/invitation-eleve/[token]` page tests — Story 6.5 §T7.2.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const fetchStatusMock = vi.fn();
vi.mock("@/lib/api/establishments", () => ({
  fetchStudentInvitationStatus: (...args: unknown[]) => fetchStatusMock(...args),
}));

vi.mock("@/components/features/establishments/student-invitation-form", () => ({
  StudentInvitationForm: ({ token }: { token: string }) => (
    <div data-testid="form">form for {token}</div>
  ),
}));

import InvitationElevePage from "./page";

describe("InvitationElevePage", () => {
  it("renders the form for a pending invitation", async () => {
    fetchStatusMock.mockResolvedValue({ establishment_name: "Lycée Test", status: "pending" });

    render(await InvitationElevePage({ params: Promise.resolve({ token: "tok-2" }) }));

    expect(screen.getByText("Lycée Test")).toBeInTheDocument();
    expect(screen.getByTestId("form")).toHaveTextContent("tok-2");
  });

  it("shows the invalid-link message when the invitation is not pending", async () => {
    fetchStatusMock.mockResolvedValue({ establishment_name: "Lycée Test", status: "accepted" });

    render(await InvitationElevePage({ params: Promise.resolve({ token: "tok-2" }) }));

    expect(screen.getByText(/n'est plus valide/i)).toBeInTheDocument();
    expect(screen.queryByTestId("form")).not.toBeInTheDocument();
  });

  it("shows the invalid-link message when the fetch fails", async () => {
    // Same wrong-host regression guard as the counselor invitation page.
    fetchStatusMock.mockRejectedValue(new Error("network down"));

    render(await InvitationElevePage({ params: Promise.resolve({ token: "tok-2" }) }));

    expect(screen.getByText(/n'est plus valide/i)).toBeInTheDocument();
  });
});
