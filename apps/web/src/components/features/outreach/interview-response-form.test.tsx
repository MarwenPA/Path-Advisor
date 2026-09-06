/**
 * <InterviewResponseForm> tests — Story 5.7.
 */
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

const routerMock = { refresh: vi.fn() };
vi.mock("next/navigation", () => ({
  useRouter: () => routerMock,
}));

const acceptMock = vi.fn();
const alternativeMock = vi.fn();
vi.mock("@/lib/api/outreach", () => ({
  acceptInterviewSlot: (...args: unknown[]) => acceptMock(...args),
  proposeInterviewAlternative: (...args: unknown[]) => alternativeMock(...args),
}));

import { InterviewResponseForm } from "./interview-response-form";

const SLOTS = ["2026-10-01T10:00:00Z", "2026-10-02T14:00:00Z"];

beforeEach(() => {
  routerMock.refresh.mockClear();
  acceptMock.mockReset();
  alternativeMock.mockReset();
});

describe("InterviewResponseForm", () => {
  it("accepts a proposed slot", async () => {
    acceptMock.mockResolvedValue({});
    render(<InterviewResponseForm outreachId="reach_1" proposedSlots={SLOTS} />);

    const slotLabel = new Date(SLOTS[0] as string).toLocaleString("fr-FR");
    fireEvent.click(screen.getByRole("button", { name: slotLabel }));

    await waitFor(() => expect(routerMock.refresh).toHaveBeenCalled());
    expect(acceptMock).toHaveBeenCalledWith("reach_1", SLOTS[0]);
  });

  it("lets the student propose an alternative instead", async () => {
    alternativeMock.mockResolvedValue({});
    render(<InterviewResponseForm outreachId="reach_1" proposedSlots={SLOTS} />);

    fireEvent.click(screen.getByRole("button", { name: /aucun de ces créneaux/i }));
    fireEvent.change(screen.getByPlaceholderText(/explique tes disponibilités/i), {
      target: { value: "Après 16h uniquement." },
    });
    fireEvent.click(screen.getByRole("button", { name: /envoyer/i }));

    await waitFor(() => expect(routerMock.refresh).toHaveBeenCalled());
    expect(alternativeMock).toHaveBeenCalledWith("reach_1", "Après 16h uniquement.");
  });
});
