/**
 * <AccessHistoryModal> tests — Story 6.11.
 */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const fetchAccessHistoryMock = vi.fn();
vi.mock("@/lib/api/access-list", () => ({
  fetchAccessHistory: (...args: unknown[]) => fetchAccessHistoryMock(...args),
  buildAccessHistoryExportUrl: (id: string) => `/api/v1/profile/access-list/${id}/history.csv/`,
}));

import { AccessHistoryModal } from "./access-history-modal";

beforeEach(() => {
  fetchAccessHistoryMock.mockReset();
});

describe("AccessHistoryModal", () => {
  it("shows the empty state when there is no history", async () => {
    fetchAccessHistoryMock.mockResolvedValue({ results: [] });
    render(<AccessHistoryModal entryId="counselor_consent:cnc_1" onClose={vi.fn()} />);

    await waitFor(() =>
      expect(
        screen.getByText("Aucune consultation sur les 90 derniers jours."),
      ).toBeInTheDocument(),
    );
  });

  it("lists timestamped consultations", async () => {
    fetchAccessHistoryMock.mockResolvedValue({
      results: [{ consulted_at: "2026-09-01T10:00:00Z", metadata: {} }],
    });
    render(<AccessHistoryModal entryId="counselor_consent:cnc_1" onClose={vi.fn()} />);

    await waitFor(() => expect(screen.getAllByRole("listitem")).toHaveLength(1));
  });

  it("calls onClose when the close button is clicked", async () => {
    fetchAccessHistoryMock.mockResolvedValue({ results: [] });
    const onClose = vi.fn();
    render(<AccessHistoryModal entryId="counselor_consent:cnc_1" onClose={onClose} />);
    await waitFor(() => expect(screen.getByText(/Aucune consultation/)).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "Fermer" }));

    expect(onClose).toHaveBeenCalled();
  });

  it("renders a CSV export link pointing at the entry's history export URL", async () => {
    fetchAccessHistoryMock.mockResolvedValue({ results: [] });
    render(<AccessHistoryModal entryId="counselor_consent:cnc_1" onClose={vi.fn()} />);

    const link = await screen.findByRole("link", { name: "Exporter en CSV" });
    expect(link).toHaveAttribute(
      "href",
      "/api/v1/profile/access-list/counselor_consent:cnc_1/history.csv/",
    );
  });
});
