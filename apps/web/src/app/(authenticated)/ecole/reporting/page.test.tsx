/**
 * `/ecole/reporting` page tests — Story 5.10.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const fetchEcoleReportingMock = vi.fn();
vi.mock("@/lib/api/ecole-reporting", () => ({
  fetchEcoleReporting: () => fetchEcoleReportingMock(),
  ECOLE_REPORTING_EXPORT_URL: "/api/v1/ecole/reporting/export.csv/",
}));

import EcoleReportingPage from "./page";

describe("EcoleReportingPage", () => {
  it("shows the monthly/yearly totals and the breakdowns", async () => {
    fetchEcoleReportingMock.mockResolvedValue({
      total_this_month: 3,
      total_this_year: 12,
      by_profession: [{ profession_name: "Infirmier·ère", count: 5 }],
      by_action: [
        { action: "interested", count: 4 },
        { action: "no_response", count: 8 },
      ],
      by_month: [{ month: "2026-09-01", count: 3 }],
    });

    render(await EcoleReportingPage());

    expect(screen.getAllByText("3").length).toBeGreaterThan(0);
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("Infirmier·ère")).toBeInTheDocument();
    expect(screen.getByText("Profil intéressant")).toBeInTheDocument();
    expect(screen.getByText("Pas encore répondu")).toBeInTheDocument();
  });

  it("exposes a CSV export link", async () => {
    fetchEcoleReportingMock.mockResolvedValue({
      total_this_month: 0,
      total_this_year: 0,
      by_profession: [],
      by_action: [],
      by_month: [],
    });

    render(await EcoleReportingPage());

    expect(screen.getByRole("link", { name: /exporter en csv/i })).toHaveAttribute(
      "href",
      "/api/v1/ecole/reporting/export.csv/",
    );
  });

  it("shows empty-state copy when there's no data yet", async () => {
    fetchEcoleReportingMock.mockResolvedValue({
      total_this_month: 0,
      total_this_year: 0,
      by_profession: [],
      by_action: [],
      by_month: [],
    });

    render(await EcoleReportingPage());

    expect(screen.getAllByText(/aucun.*pour l'instant/i).length).toBeGreaterThan(0);
  });
});
