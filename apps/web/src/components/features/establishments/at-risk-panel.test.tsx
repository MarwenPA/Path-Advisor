/**
 * AtRiskPanel — Story 10.1 contracts.
 *
 * Contracts: constructive wording per reason code (never "en échec"), the
 * consent limitation is stated, marking an intervention moves the card to
 * "Intervention en cours" (optimistic, reverted on failure), and the
 * profile CTA navigates.
 */
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const pushMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

vi.mock("@/lib/api/cohort-dashboard", async () => ({
  ...(await vi.importActual<typeof import("@/lib/api/cohort-dashboard")>(
    "@/lib/api/cohort-dashboard",
  )),
  markIntervention: vi.fn(),
  resolveIntervention: vi.fn(),
}));

import { markIntervention } from "@/lib/api/cohort-dashboard";
import type { AtRiskResponse } from "@/lib/api/cohort-dashboard";

import { AtRiskPanel } from "./at-risk-panel";

const INITIAL: AtRiskResponse = {
  students: [
    {
      student_id: "usr_risk_1",
      cohort_name: "Terminale A",
      reasons: [
        { code: "faible_engagement", days_inactive: 45 },
        { code: "baisse_moyenne", drop: 3.0, from_average: 14.0, to_average: 11.0 },
      ],
      consent_granted: true,
      intervention_in_progress: false,
    },
    {
      student_id: "usr_risk_2",
      cohort_name: "Terminale A",
      reasons: [{ code: "profil_incoherent", nb_passions: 3 }],
      consent_granted: false,
      intervention_in_progress: false,
    },
  ],
  students_without_consent: 4,
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe("AtRiskPanel", () => {
  it("renders constructive reasons and the consent limitation note", () => {
    render(<AtRiskPanel initial={INITIAL} />);

    expect(screen.getByText("Nécessite ton attention")).toBeInTheDocument();
    expect(screen.getByText(/Pas de connexion depuis 45 jours/)).toBeInTheDocument();
    expect(screen.getByText(/Sa moyenne est passée de 14 à 11/)).toBeInTheDocument();
    expect(
      screen.getByText(/4 élève\(s\) sans consentement : seuls les signaux/),
    ).toBeInTheDocument();
    // Dignité : jamais de vocabulaire stigmatisant.
    expect(screen.queryByText(/échec|risque/i)).not.toBeInTheDocument();
  });

  it("moves a student under 'Intervention en cours' on mark", async () => {
    vi.mocked(markIntervention).mockResolvedValue();
    render(<AtRiskPanel initial={INITIAL} />);

    await userEvent.click(
      screen.getAllByRole("button", { name: "Marquer l'intervention en cours" })[0] as HTMLElement,
    );

    await waitFor(() => expect(markIntervention).toHaveBeenCalledWith("usr_risk_1"));
    expect(screen.getByText("Intervention en cours")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Intervention terminée" })).toBeInTheDocument();
  });

  it("reverts the optimistic mark and alerts on failure", async () => {
    vi.mocked(markIntervention).mockRejectedValue(new Error("réseau"));
    render(<AtRiskPanel initial={INITIAL} />);

    await userEvent.click(
      screen.getAllByRole("button", { name: "Marquer l'intervention en cours" })[0] as HTMLElement,
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(/n'a pas pu être enregistré/);
    expect(screen.queryByText("Intervention en cours")).not.toBeInTheDocument();
  });

  it("navigates to the student profile from the interview CTA", async () => {
    render(<AtRiskPanel initial={INITIAL} />);

    await userEvent.click(
      screen.getAllByRole("button", { name: /Suggérer un entretien/ })[0] as HTMLElement,
    );
    expect(pushMock).toHaveBeenCalledWith("/cohorte/eleves/usr_risk_1");
  });

  it("renders nothing when there is nothing to show", () => {
    const { container } = render(
      <AtRiskPanel initial={{ students: [], students_without_consent: 0 }} />,
    );
    expect(container).toBeEmptyDOMElement();
  });
});
