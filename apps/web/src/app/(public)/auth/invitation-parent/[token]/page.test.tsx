import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

import InvitationParentPage from "./page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }),
}));

const fetchMock = vi.fn();
vi.stubGlobal("fetch", fetchMock);

beforeEach(() => {
  fetchMock.mockReset();
});

function jsonResponse(status: number, body: unknown) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}

describe("InvitationParentPage", () => {
  it("renders the signup form for a pending, valid token", async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse(200, {
        student_first_name: "Léa",
        student_masked_email: "l***@e**.test",
        parent_email: "parent@example.test",
        relationship: "mere",
        custom_message: null,
        status: "pending",
      }),
    );

    const ui = await InvitationParentPage({ params: Promise.resolve({ token: "valid-token" }) });
    render(ui);

    expect(screen.getByText(/invitation de léa/i)).toBeInTheDocument();
    expect(screen.getByText(/crée ton compte parent/i)).toBeInTheDocument();
  });

  it("renders the invalid-link message for an expired invitation", async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse(200, {
        student_first_name: "Léa",
        student_masked_email: "l***@e**.test",
        parent_email: "parent@example.test",
        relationship: null,
        custom_message: null,
        status: "expired",
      }),
    );

    const ui = await InvitationParentPage({ params: Promise.resolve({ token: "expired-token" }) });
    render(ui);

    expect(screen.getByText(/ce lien d'invitation n'est plus valide/i)).toBeInTheDocument();
  });

  it("renders the invalid-link message for an unknown token (404)", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(404, {}));

    const ui = await InvitationParentPage({ params: Promise.resolve({ token: "unknown" }) });
    render(ui);

    expect(screen.getByText(/ce lien d'invitation n'est plus valide/i)).toBeInTheDocument();
  });
});
