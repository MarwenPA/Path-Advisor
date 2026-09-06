/**
 * <SendOutreachButton> tests — Story 5.4 §AC2.
 */
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

const routerMock = { push: vi.fn() };
vi.mock("next/navigation", () => ({
  useRouter: () => routerMock,
}));

const createMock = vi.fn();
vi.mock("@/lib/api/outreach", () => ({
  createOutreachRequest: (...args: unknown[]) => createMock(...args),
}));

import { SendOutreachButton } from "./send-outreach-button";

const PROFESSIONS = [
  {
    id: "prof_01",
    slug: "infirmier",
    name: "Infirmier·ère",
    sector: "santé",
    score: 85,
    confidence_level: "high" as const,
    signals_contributifs: [],
    phrase_recopiable: "",
  },
  {
    id: "prof_02",
    slug: "developpeur",
    name: "Développeur·se",
    sector: "tech",
    score: 70,
    confidence_level: "high" as const,
    signals_contributifs: [],
    phrase_recopiable: "",
  },
];

beforeEach(() => {
  routerMock.push.mockClear();
  createMock.mockReset();
});

describe("SendOutreachButton", () => {
  it("opens the sheet with the métier picker pre-filled to the first recommendation", () => {
    render(
      <SendOutreachButton
        schoolSlug="ecole-test"
        schoolName="École Test"
        professions={PROFESSIONS}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /envoyer mon profil à cette école/i }));

    expect(screen.getByText(/envoyer mon profil à école test/i)).toBeInTheDocument();
  });

  it("moves to the confirmation step listing what will be shared, not the other recommendations", () => {
    render(
      <SendOutreachButton
        schoolSlug="ecole-test"
        schoolName="École Test"
        professions={PROFESSIONS}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /envoyer mon profil à cette école/i }));
    fireEvent.click(screen.getByRole("button", { name: /continuer/i }));

    expect(screen.getByText(/vérifie avant d'envoyer/i)).toBeInTheDocument();
    expect(screen.getByText(/infirmier·ère/i)).toBeInTheDocument();
    expect(screen.queryByText(/développeur/i)).not.toBeInTheDocument();
  });

  it("confirms, calls createOutreachRequest, and redirects to /mes-envois", async () => {
    createMock.mockResolvedValue({ id: "reach_1", status: "pending" });
    render(
      <SendOutreachButton
        schoolSlug="ecole-test"
        schoolName="École Test"
        professions={PROFESSIONS}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /envoyer mon profil à cette école/i }));
    fireEvent.click(screen.getByRole("button", { name: /continuer/i }));
    fireEvent.click(screen.getByRole("button", { name: /confirmer l'envoi/i }));

    await waitFor(() => expect(routerMock.push).toHaveBeenCalledWith("/mes-envois"));
    expect(createMock).toHaveBeenCalledWith("ecole-test", {
      profession_id: "prof_01",
      motivation_text: "",
    });
  });

  it("shows an error message on failure and stays on the confirmation step", async () => {
    createMock.mockRejectedValue(new Error("network down"));
    render(
      <SendOutreachButton
        schoolSlug="ecole-test"
        schoolName="École Test"
        professions={PROFESSIONS}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /envoyer mon profil à cette école/i }));
    fireEvent.click(screen.getByRole("button", { name: /continuer/i }));
    fireEvent.click(screen.getByRole("button", { name: /confirmer l'envoi/i }));

    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
    expect(routerMock.push).not.toHaveBeenCalled();
  });

  it("is disabled when the student has no recommendations to pick from", () => {
    render(<SendOutreachButton schoolSlug="ecole-test" schoolName="École Test" professions={[]} />);
    expect(
      screen.getByRole("button", { name: /envoyer mon profil à cette école/i }),
    ).toBeDisabled();
  });
});
