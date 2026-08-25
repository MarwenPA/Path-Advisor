import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

import { InviteParentDialog } from "./invite-parent-dialog";

vi.mock("@/lib/api/family", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/family")>("@/lib/api/family");
  return {
    ...actual,
    createParentInvitation: vi.fn(),
  };
});

import { createParentInvitation } from "@/lib/api/family";

const createMock = vi.mocked(createParentInvitation);

beforeEach(() => {
  createMock.mockReset();
});

describe("InviteParentDialog", () => {
  it("opens the form, then the ConsentDialog, and does not call the API before consent", async () => {
    render(<InviteParentDialog />);

    fireEvent.click(screen.getByRole("button", { name: /inviter un parent/i }));

    await waitFor(() => {
      expect(screen.getByLabelText(/email du parent/i)).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText(/email du parent/i), {
      target: { value: "parent@example.test" },
    });
    fireEvent.click(screen.getByRole("button", { name: /continuer/i }));

    await waitFor(() => {
      expect(screen.getByText("Avant d'inviter ton parent")).toBeInTheDocument();
    });
    expect(createMock).not.toHaveBeenCalled();
  });

  it("submits the invitation once the ConsentDialog is accepted", async () => {
    createMock.mockResolvedValueOnce({
      id: "pinv_1",
      parent_email: "parent@example.test",
      relationship: null,
      custom_message: null,
      status: "pending",
      created_at: "2026-08-25T00:00:00Z",
      expires_at: "2026-09-24T00:00:00Z",
      accepted_at: null,
    });
    const onInvited = vi.fn();
    render(<InviteParentDialog onInvited={onInvited} />);

    fireEvent.click(screen.getByRole("button", { name: /inviter un parent/i }));
    await waitFor(() => screen.getByLabelText(/email du parent/i));
    fireEvent.change(screen.getByLabelText(/email du parent/i), {
      target: { value: "parent@example.test" },
    });
    fireEvent.click(screen.getByRole("button", { name: /continuer/i }));

    await waitFor(() => screen.getByText("Avant d'inviter ton parent"));
    fireEvent.click(screen.getByRole("button", { name: /envoyer l'invitation/i }));

    await waitFor(() => {
      expect(createMock).toHaveBeenCalledWith(
        expect.objectContaining({ parent_email: "parent@example.test" }),
      );
    });
    await waitFor(() => expect(onInvited).toHaveBeenCalledWith("parent@example.test"));
  });
});
