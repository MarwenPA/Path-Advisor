/**
 * <CounselorInvitationForm> tests — Story 6.5 §T7.1.
 */
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

const routerMock = { push: vi.fn() };
vi.mock("next/navigation", () => ({
  useRouter: () => routerMock,
}));

const acceptMock = vi.fn();
vi.mock("@/lib/api/establishments", () => ({
  acceptCounselorInvitation: (...args: unknown[]) => acceptMock(...args),
}));

import { CounselorInvitationForm } from "./counselor-invitation-form";

beforeEach(() => {
  routerMock.push.mockClear();
  acceptMock.mockReset();
});

describe("CounselorInvitationForm", () => {
  it("submits the password (only) and redirects to /auth/login on success", async () => {
    acceptMock.mockResolvedValue({ detail: "ok" });
    render(<CounselorInvitationForm token="tok-123" />);

    fireEvent.change(screen.getByLabelText(/mot de passe/i), {
      target: { value: "Strong-Pass-2026!" },
    });
    fireEvent.click(screen.getByRole("button", { name: /créer mon compte/i }));

    await waitFor(() => expect(routerMock.push).toHaveBeenCalledWith("/auth/login"));
    expect(acceptMock).toHaveBeenCalledWith("tok-123", "Strong-Pass-2026!");
    expect(screen.getByText(/compte créé/i)).toBeInTheDocument();
  });

  it("shows an error message on failure and stays on the form", async () => {
    acceptMock.mockRejectedValue(new Error("network down"));
    render(<CounselorInvitationForm token="tok-123" />);

    fireEvent.change(screen.getByLabelText(/mot de passe/i), {
      target: { value: "Strong-Pass-2026!" },
    });
    fireEvent.click(screen.getByRole("button", { name: /créer mon compte/i }));

    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent(/erreur/i));
    expect(routerMock.push).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: /créer mon compte/i })).toBeInTheDocument();
  });

  it("has no email field — the account email is locked to the invitation (§4.4)", () => {
    render(<CounselorInvitationForm token="tok-123" />);
    expect(screen.queryByLabelText(/email/i)).not.toBeInTheDocument();
  });
});
