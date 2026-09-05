/**
 * <StudentInvitationForm> tests — Story 6.5 §T7.2.
 */
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

const acceptMock = vi.fn();
vi.mock("@/lib/api/establishments", () => ({
  acceptStudentInvitation: (...args: unknown[]) => acceptMock(...args),
}));

import { StudentInvitationForm } from "./student-invitation-form";

beforeEach(() => {
  acceptMock.mockReset();
});

describe("StudentInvitationForm", () => {
  it("shows the 'active' message when the backend returns status=active (majeur)", async () => {
    acceptMock.mockResolvedValue({ detail: "ok", status: "active" });
    render(<StudentInvitationForm token="tok-456" />);

    fireEvent.change(screen.getByLabelText(/choisis ton mot de passe/i), {
      target: { value: "Strong-Pass-2026!" },
    });
    fireEvent.click(screen.getByRole("button", { name: /activer mon compte/i }));

    await waitFor(() => expect(screen.getByText(/ton compte est activé/i)).toBeInTheDocument());
    expect(acceptMock).toHaveBeenCalledWith("tok-456", "Strong-Pass-2026!");
  });

  it("shows the pending-parental-consent message when the backend returns a non-active status (mineur)", async () => {
    acceptMock.mockResolvedValue({ detail: "ok", status: "pending_parental_consent" });
    render(<StudentInvitationForm token="tok-456" />);

    fireEvent.change(screen.getByLabelText(/choisis ton mot de passe/i), {
      target: { value: "Strong-Pass-2026!" },
    });
    fireEvent.click(screen.getByRole("button", { name: /activer mon compte/i }));

    await waitFor(() =>
      expect(screen.getByText(/réponse d'un parent ou tuteur/i)).toBeInTheDocument(),
    );
  });

  it("shows an error message on failure and stays on the form", async () => {
    acceptMock.mockRejectedValue(new Error("network down"));
    render(<StudentInvitationForm token="tok-456" />);

    fireEvent.change(screen.getByLabelText(/choisis ton mot de passe/i), {
      target: { value: "Strong-Pass-2026!" },
    });
    fireEvent.click(screen.getByRole("button", { name: /activer mon compte/i }));

    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent(/erreur/i));
  });

  it("has no email field — the account already exists from the CSV import (§4.4)", () => {
    render(<StudentInvitationForm token="tok-456" />);
    expect(screen.queryByLabelText(/email/i)).not.toBeInTheDocument();
  });
});
