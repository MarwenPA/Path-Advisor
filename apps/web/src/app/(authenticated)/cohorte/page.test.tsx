/**
 * `/cohorte` page tests — Story 6.6.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const fetchCohortDashboardMock = vi.fn();
vi.mock("@/lib/api/cohort-dashboard", () => ({
  fetchCohortDashboard: () => fetchCohortDashboardMock(),
}));

vi.mock("@/components/features/establishments/cohort-dashboard", () => ({
  CohortDashboard: ({ dashboard }: { dashboard: { kpis: { nb_eleves: number } } }) => (
    <div data-testid="cohort-dashboard">{dashboard.kpis.nb_eleves} élèves</div>
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

    render(await CohortDashboardPage());

    expect(screen.getByTestId("cohort-dashboard")).toHaveTextContent("5 élèves");
  });
});
