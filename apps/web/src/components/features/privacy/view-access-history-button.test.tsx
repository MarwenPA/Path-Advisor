/**
 * <ViewAccessHistoryButton> tests — Story 6.11.
 */
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/components/features/privacy/access-history-modal", () => ({
  AccessHistoryModal: ({ entryId }: { entryId: string }) => (
    <div data-testid="modal">Historique {entryId}</div>
  ),
}));

import { ViewAccessHistoryButton } from "./view-access-history-button";

describe("ViewAccessHistoryButton", () => {
  it("opens the modal on click", () => {
    render(<ViewAccessHistoryButton entryId="counselor_consent:cnc_1" />);

    expect(screen.queryByTestId("modal")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /voir l'historique d'accès/i }));
    expect(screen.getByTestId("modal")).toHaveTextContent("counselor_consent:cnc_1");
  });
});
