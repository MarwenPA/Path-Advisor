/**
 * <CohortDashboard> tests — Story 6.6/6.10.
 */
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const pushMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

import { CohortDashboard } from "./cohort-dashboard";

const DASHBOARD = {
  kpis: { nb_eleves: 2, taux_completion_profil: 50, nb_eleves_mode_degrade: 1 },
  top_metiers: [{ name: "Infirmier·ère", count: 2 }],
  distribution_filiere: [{ filiere: "Générale", count: 2 }],
  activite_recente: [{ student_id: "usr_1", derniere_connexion: "2026-09-01T10:00:00Z" }],
  eleves: [
    { student_id: "usr_1", cohort_name: "Terminale" },
    { student_id: "usr_2", cohort_name: "Terminale" },
  ],
};

describe("CohortDashboard", () => {
  it("renders KPIs and sections", () => {
    render(<CohortDashboard dashboard={DASHBOARD} />);

    expect(screen.getAllByText("2").length).toBeGreaterThan(0);
    expect(screen.getByText("50%")).toBeInTheDocument();
    expect(screen.getByText("Infirmier·ère")).toBeInTheDocument();
    expect(screen.getByText("Générale")).toBeInTheDocument();
  });

  it("filters the student list via the search box", () => {
    render(<CohortDashboard dashboard={DASHBOARD} />);

    fireEvent.change(screen.getByPlaceholderText("Rechercher un élève (/)"), {
      target: { value: "usr_2" },
    });

    expect(screen.getAllByText("usr_1")).toHaveLength(1); // still in "activité récente"
    expect(screen.getByRole("link", { name: "usr_2" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "usr_1" })).not.toBeInTheDocument();
  });

  it("navigates to the selected student's profile on 'e'", () => {
    render(<CohortDashboard dashboard={DASHBOARD} />);

    fireEvent.keyDown(window, { key: "e" });

    expect(pushMock).toHaveBeenCalledWith("/cohorte/eleves/usr_1");
  });

  it("moves selection down with 'j' then opens the second student on 'e'", () => {
    render(<CohortDashboard dashboard={DASHBOARD} />);

    fireEvent.keyDown(window, { key: "j" });
    fireEvent.keyDown(window, { key: "e" });

    expect(pushMock).toHaveBeenCalledWith("/cohorte/eleves/usr_2");
  });
});
