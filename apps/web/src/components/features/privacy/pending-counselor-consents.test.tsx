/**
 * <PendingCounselorConsents> tests — Story 6.7.
 */
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

const fetchPendingMock = vi.fn();
const decideMock = vi.fn();
vi.mock("@/lib/api/counselor-consent", () => ({
  fetchPendingCounselorConsents: () => fetchPendingMock(),
  decideCounselorConsent: (...args: unknown[]) => decideMock(...args),
}));

import { PendingCounselorConsents } from "./pending-counselor-consents";

const PENDING = {
  id: "cnc_1",
  counselor_email: "conseillere@lycee.test",
  status: "pending" as const,
  requested_at: "2026-09-10T00:00:00Z",
  decided_at: null,
};

beforeEach(() => {
  fetchPendingMock.mockReset();
  decideMock.mockReset();
});

describe("PendingCounselorConsents", () => {
  it("renders nothing when there are no pending requests", async () => {
    fetchPendingMock.mockResolvedValue([]);
    const { container } = render(<PendingCounselorConsents />);

    await waitFor(() => expect(fetchPendingMock).toHaveBeenCalled());
    expect(container).toBeEmptyDOMElement();
  });

  it("shows a card for a pending request and opens the ConsentDialog", async () => {
    fetchPendingMock.mockResolvedValue([PENDING]);
    render(<PendingCounselorConsents />);

    expect(await screen.findByText(/conseillere@lycee.test/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /voir la demande/i }));

    expect(
      await screen.findByText(/ta conseillère souhaite consulter ton profil/i),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/bulletins détaillés/i).length).toBeGreaterThan(0);
  });

  it("removes the card after accepting", async () => {
    fetchPendingMock.mockResolvedValue([PENDING]);
    decideMock.mockResolvedValue({ ...PENDING, status: "granted" });
    render(<PendingCounselorConsents />);

    fireEvent.click(await screen.findByRole("button", { name: /voir la demande/i }));
    fireEvent.click(await screen.findByRole("button", { name: /^accepter$/i }));

    await waitFor(() => expect(decideMock).toHaveBeenCalledWith("cnc_1", true));
    await waitFor(() =>
      expect(screen.queryByText(/conseillere@lycee.test/i)).not.toBeInTheDocument(),
    );
  });

  it("removes the card after refusing", async () => {
    fetchPendingMock.mockResolvedValue([PENDING]);
    decideMock.mockResolvedValue({ ...PENDING, status: "refused" });
    render(<PendingCounselorConsents />);

    fireEvent.click(await screen.findByRole("button", { name: /voir la demande/i }));
    fireEvent.click(await screen.findByRole("button", { name: /^refuser$/i }));

    await waitFor(() => expect(decideMock).toHaveBeenCalledWith("cnc_1", false));
  });
});
