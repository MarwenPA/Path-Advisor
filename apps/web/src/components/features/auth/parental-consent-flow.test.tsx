import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

import { ParentalConsentFlow } from "./parental-consent-flow";
import type { ParentalConsentStatus } from "@/lib/api/auth";

vi.mock("@/lib/api/auth", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/auth")>("@/lib/api/auth");
  return {
    ...actual,
    decideParentalConsent: vi.fn(),
  };
});

import { decideParentalConsent } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";

const decideMock = vi.mocked(decideParentalConsent);

const PENDING_STATUS: ParentalConsentStatus = {
  student_email_masked: "m***@e**.test",
  child_age: 14,
  requested_at: "2026-05-17T12:00:00Z",
  expires_at: "2026-07-16T12:00:00Z",
  status: "pending",
};

beforeEach(() => {
  decideMock.mockReset();
});

describe("ParentalConsentFlow", () => {
  it("renders the masked email and opens the grant ConsentDialog on click", async () => {
    render(<ParentalConsentFlow token="t0k3n" initial={PENDING_STATUS} />);

    // Dialog hidden by default.
    expect(screen.queryByText("Autoriser l'inscription de votre enfant")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /^autoriser$/i }));

    // ConsentDialog opens — its title appears.
    await waitFor(() => {
      expect(screen.getByText("Autoriser l'inscription de votre enfant")).toBeInTheDocument();
    });
    // Masked email is reused as the dialog's beneficiary line.
    expect(screen.getByText(/m\*\*\*@e\*\*\.test/i)).toBeInTheDocument();
  });

  it("sends a decide payload and shows the confirmation screen on success", async () => {
    decideMock.mockResolvedValueOnce({ decision: "granted", child_status: "active" });
    render(<ParentalConsentFlow token="t0k3n" initial={PENDING_STATUS} />);

    fireEvent.click(screen.getByRole("button", { name: /^autoriser$/i }));
    await waitFor(() => {
      expect(screen.getByText("Autoriser l'inscription de votre enfant")).toBeInTheDocument();
    });

    // Confirm inside the ConsentDialog.
    fireEvent.click(screen.getByRole("button", { name: /j'autorise/i }));

    await waitFor(() => {
      expect(decideMock).toHaveBeenCalledTimes(1);
    });
    const firstCall = decideMock.mock.calls[0];
    if (!firstCall) throw new Error("Expected decideMock to have been called");
    const [token, payload] = firstCall;
    expect(token).toBe("t0k3n");
    expect(payload.decision).toBe("granted");
    expect(payload.content_hash).toMatch(/^[0-9a-f]{64}$/);

    await waitFor(() => {
      expect(screen.getByText(/votre enfant a maintenant accès/i)).toBeInTheDocument();
    });
  });

  it("produces different content_hash payloads for different beneficiaries (anti-regression)", async () => {
    // Story 1.4 review §P11: the .toMatch(/^[0-9a-f]{64}$/) assertion in the
    // previous test would pass even if ConsentDialog hashed a constant string.
    // This test makes regression visible by submitting two flows with different
    // initial status (which feeds the dialog's `beneficiary` line through
    // `student_email_masked`) and asserts the resulting hashes differ.
    decideMock.mockResolvedValueOnce({ decision: "granted", child_status: "active" });
    const { unmount } = render(<ParentalConsentFlow token="t0k3n-A" initial={PENDING_STATUS} />);
    fireEvent.click(screen.getByRole("button", { name: /^autoriser$/i }));
    await waitFor(() => {
      expect(screen.getByText("Autoriser l'inscription de votre enfant")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("button", { name: /j'autorise/i }));
    await waitFor(() => expect(decideMock).toHaveBeenCalledTimes(1));
    const callA = decideMock.mock.calls[0];
    if (!callA) throw new Error("Expected decideMock call A");
    const hashA = callA[1].content_hash;
    unmount();
    decideMock.mockReset();

    // Same flow with a different masked email → different beneficiary → different hash.
    decideMock.mockResolvedValueOnce({ decision: "granted", child_status: "active" });
    render(
      <ParentalConsentFlow
        token="t0k3n-B"
        initial={{ ...PENDING_STATUS, student_email_masked: "a***@b**.com" }}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /^autoriser$/i }));
    await waitFor(() => {
      expect(screen.getByText("Autoriser l'inscription de votre enfant")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("button", { name: /j'autorise/i }));
    await waitFor(() => expect(decideMock).toHaveBeenCalledTimes(1));
    const callB = decideMock.mock.calls[0];
    if (!callB) throw new Error("Expected decideMock call B");
    const hashB = callB[1].content_hash;

    expect(hashA).not.toBe(hashB);
  });

  it("shows the expired error state when the API returns 409", async () => {
    decideMock.mockRejectedValueOnce(
      new ApiError(409, "Cette demande a déjà reçu une décision ou a expiré.", {
        type: "https://path-advisor.fr/errors/parental-consent-already-decided",
        title: "Décision déjà enregistrée",
        status: 409,
        detail: "Cette demande a déjà reçu une décision ou a expiré.",
      }),
    );

    render(<ParentalConsentFlow token="t0k3n" initial={PENDING_STATUS} />);

    fireEvent.click(screen.getByRole("button", { name: /^autoriser$/i }));
    await waitFor(() => {
      expect(screen.getByText("Autoriser l'inscription de votre enfant")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("button", { name: /j'autorise/i }));

    await waitFor(() => {
      expect(screen.getByText(/lien expiré ou déjà utilisé/i)).toBeInTheDocument();
    });
  });
});
