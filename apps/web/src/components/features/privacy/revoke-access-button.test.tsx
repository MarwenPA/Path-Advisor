/**
 * <RevokeAccessButton> tests — Story 1.10 §T8.1.
 *
 * Vitest + RTL : clicking opens the ConsentDialog ; confirming sends POST
 * with content_hash ; 200 calls router.refresh ; 404 surfaces toast-equivalent
 * (status flip to "not-found" + router.refresh) ; 5xx flips to "error".
 */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

import { RevokeAccessButton } from "./revoke-access-button";
import { ApiError } from "@/lib/api/client";

import type { AccessListEntry } from "@/lib/api/access-list";

// ---------------------------------------------------------------------------
// Hoisted mocks — vitest evaluates the factory before imports
// ---------------------------------------------------------------------------

const routerMock = { refresh: vi.fn() };

vi.mock("next/navigation", () => ({
  useRouter: () => routerMock,
}));

const revokeMock = vi.fn();
vi.mock("@/lib/api/access-list", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/access-list")>(
    "@/lib/api/access-list",
  );
  return {
    ...actual,
    revokeAccessListEntry: (...args: unknown[]) => revokeMock(...args),
  };
});

const _entry = (over: Partial<AccessListEntry> = {}): AccessListEntry => ({
  id: "parental_consent:abc-123",
  tier_type: "parent",
  display_name: "parent@example.test",
  granted_at: new Date(Date.now() - 7 * 86_400_000).toISOString(),
  visible_data: ["metiers_explores", "parcours_sauvegardes"],
  masked_data: ["bulletins_detailles"],
  revocable: true,
  ...over,
});

beforeEach(() => {
  vi.clearAllMocks();
});

describe("RevokeAccessButton", () => {
  it("renders an active 'Révoquer l'accès' button", () => {
    render(<RevokeAccessButton entry={_entry()} />);
    const btn = screen.getByRole("button", { name: /révoquer l'accès/i });
    expect(btn).toBeEnabled();
  });

  it("opens a confirmation dialog on click", async () => {
    render(<RevokeAccessButton entry={_entry()} />);
    fireEvent.click(screen.getByRole("button", { name: /révoquer l'accès/i }));
    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
    expect(screen.getByText(/révoquer l'accès de ton parent/i)).toBeInTheDocument();
  });

  it("calls revoke API + router.refresh on successful confirm", async () => {
    revokeMock.mockResolvedValueOnce({ revoked: true, id: "parental_consent:abc-123" });
    render(<RevokeAccessButton entry={_entry()} />);

    fireEvent.click(screen.getByRole("button", { name: /révoquer l'accès/i }));
    // Inside the dialog there is now a NEW "Révoquer l'accès" button (the
    // accept CTA). Pick the one with the destructive role.
    const dialog = await screen.findByRole("dialog");
    const acceptButtons = dialog.querySelectorAll("button");
    const acceptBtn = Array.from(acceptButtons).find((b) =>
      /révoquer l'accès/i.test(b.textContent ?? ""),
    );
    expect(acceptBtn).toBeTruthy();
    fireEvent.click(acceptBtn!);

    await waitFor(() => {
      expect(revokeMock).toHaveBeenCalledTimes(1);
    });
    const firstCall = revokeMock.mock.calls[0];
    expect(firstCall).toBeDefined();
    const [id, contentHash] = firstCall!;
    expect(id).toBe("parental_consent:abc-123");
    expect(typeof contentHash).toBe("string");
    expect((contentHash as string).length).toBeGreaterThan(0);
    await waitFor(() => {
      expect(routerMock.refresh).toHaveBeenCalled();
    });
  });

  it("on 404 : closes the dialog and refreshes (stale entry)", async () => {
    revokeMock.mockRejectedValueOnce(new ApiError(404, "Not Found", null));
    render(<RevokeAccessButton entry={_entry()} />);
    fireEvent.click(screen.getByRole("button", { name: /révoquer l'accès/i }));
    const dialog = await screen.findByRole("dialog");
    const acceptBtn = Array.from(dialog.querySelectorAll("button")).find((b) =>
      /révoquer l'accès/i.test(b.textContent ?? ""),
    );
    fireEvent.click(acceptBtn!);
    await waitFor(() => {
      expect(routerMock.refresh).toHaveBeenCalled();
    });
  });

  it("on 5xx : shows inline error message", async () => {
    revokeMock.mockRejectedValueOnce(new ApiError(500, "Internal Server Error", null));
    render(<RevokeAccessButton entry={_entry()} />);
    fireEvent.click(screen.getByRole("button", { name: /révoquer l'accès/i }));
    const dialog = await screen.findByRole("dialog");
    const acceptBtn = Array.from(dialog.querySelectorAll("button")).find((b) =>
      /révoquer l'accès/i.test(b.textContent ?? ""),
    );
    fireEvent.click(acceptBtn!);
    // findByText polls — handles the async state flip from "submitting" → "error".
    const errorEl = await screen.findByText(/réessaie/i, {}, { timeout: 3000 });
    expect(errorEl).toBeInTheDocument();
    // router.refresh must NOT be called on 5xx (only on 200 / 404).
    expect(routerMock.refresh).not.toHaveBeenCalled();
  });
});
