/**
 * `/cohorte` page tests — Story 6.6.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const fetchCohortDashboardMock = vi.fn();
const fetchAtRiskStudentsMock = vi.fn();
vi.mock("@/lib/api/cohort-dashboard", () => ({
  fetchCohortDashboard: () => fetchCohortDashboardMock(),
  fetchAtRiskStudents: () => fetchAtRiskStudentsMock(),
  COHORT_REPORTING_EXPORT_URL: "/api/v1/establishments/cohort-dashboard/export.csv/",
}));

vi.mock("@/components/features/establishments/cohort-dashboard", () => ({
  CohortDashboard: ({ dashboard }: { dashboard: { kpis: { nb_eleves: number } } }) => (
    <div data-testid="cohort-dashboard">{dashboard.kpis.nb_eleves} élèves</div>
  ),
}));

vi.mock("@/components/features/establishments/at-risk-panel", () => ({
  AtRiskPanel: ({ initial }: { initial: { students: unknown[] } }) => (
    <div data-testid="at-risk-panel">{initial.students.length} à risque</div>
  ),
}));

import CohortDashboardPage from "./page";

describe("CohortDashboardPage", () => {
  it("fetches the dashboard and passes it to <CohortDashboard>", async () => {
    fetchCohortDashboardMock.mockResolvedValue({
      kpis: { nb_eleves: 5, taux_completion_profil: 80, nb_eleves_mode_degrade: 1 },
      top_metiers: [],
      distribution_filiere: [],
      activite_recente: [],
      eleves: [],
    });
    fetchAtRiskStudentsMock.mockResolvedValue({
      students: [{ student_id: "usr_1" }],
      students_without_consent: 0,
    });

    render(await CohortDashboardPage());

    expect(screen.getByTestId("cohort-dashboard")).toHaveTextContent("5 élèves");
    expect(screen.getByTestId("at-risk-panel")).toHaveTextContent("1 à risque");
    expect(screen.getByText("Exporter le reporting (CSV)")).toBeInTheDocument();
  });
});
