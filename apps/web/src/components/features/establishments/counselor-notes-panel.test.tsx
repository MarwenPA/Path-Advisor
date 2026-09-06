/**
 * <CounselorNotesPanel> tests — Story 6.8.
 */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const addNoteMock = vi.fn();
vi.mock("@/lib/api/counselor-profile", () => ({
  addCounselorNote: (...args: unknown[]) => addNoteMock(...args),
}));

import { CounselorNotesPanel } from "./counselor-notes-panel";

beforeEach(() => {
  addNoteMock.mockReset();
});

describe("CounselorNotesPanel", () => {
  it("shows the empty state with no notes", () => {
    render(<CounselorNotesPanel studentId="usr_1" initialNotes={[]} />);

    expect(screen.getByText("Aucune note pour l'instant.")).toBeInTheDocument();
  });

  it("renders existing notes", () => {
    render(
      <CounselorNotesPanel
        studentId="usr_1"
        initialNotes={[
          { id: "note_1", text: "Bon relationnel", created_at: "2026-09-01T10:00:00Z" },
        ]}
      />,
    );

    expect(screen.getByText("Bon relationnel")).toBeInTheDocument();
  });

  it("adds a new note and prepends it to the list", async () => {
    addNoteMock.mockResolvedValue({
      id: "note_2",
      text: "Motivé pour la filière santé",
      created_at: "2026-09-02T10:00:00Z",
    });
    render(<CounselorNotesPanel studentId="usr_1" initialNotes={[]} />);

    fireEvent.change(screen.getByPlaceholderText("Ajouter une note…"), {
      target: { value: "Motivé pour la filière santé" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Ajouter/ }));

    await waitFor(() =>
      expect(screen.getByText("Motivé pour la filière santé")).toBeInTheDocument(),
    );
    expect(addNoteMock).toHaveBeenCalledWith("usr_1", "Motivé pour la filière santé");
  });

  it("shows an error message when the add fails", async () => {
    addNoteMock.mockRejectedValue(new Error("boom"));
    render(<CounselorNotesPanel studentId="usr_1" initialNotes={[]} />);

    fireEvent.change(screen.getByPlaceholderText("Ajouter une note…"), {
      target: { value: "Une note" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Ajouter/ }));

    await waitFor(() =>
      expect(screen.getByText("Impossible d'enregistrer la note. Réessayez.")).toBeInTheDocument(),
    );
  });
});
