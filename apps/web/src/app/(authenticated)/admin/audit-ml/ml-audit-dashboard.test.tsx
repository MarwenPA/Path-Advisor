/**
 * Audit ML — Story 9.6 front tests.
 *
 * Contracts: an alerting report renders the review chip and the warning
 * tiles; a healthy one renders the calm chip; subpopulation groups land in
 * the table with their counts.
 */
import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { beforeEach, describe, expect, it, vi } from "vitest";

import messages from "../../../../../messages/fr.json";

const apiFetchMock = vi.fn();
vi.mock("@/lib/api/client", () => ({
  apiFetch: (path: string) => apiFetchMock(path),
  readCsrfCookie: () => "csrf",
}));

import { MlAuditDashboard } from "./ml-audit-dashboard";

function withIntl(node: React.ReactElement) {
  return render(
    <NextIntlClientProvider locale="fr" messages={messages}>
      {node}
    </NextIntlClientProvider>,
  );
}

const REPORT = {
  model: {
    version: "0.3.0-statistical",
    deployed_at: null,
    baseline_size: 120,
    requires_ethics_review: false,
  },
  monthly: [
    { month: "2026-08", count: 40, mean: 0.61, min: 0.2, max: 0.9 },
    { month: "2026-09", count: 55, mean: 0.63, min: 0.2, max: 0.9 },
  ],
  drift: { statistic: 0.31, threshold: 0.19, alert: true, n_baseline: 120, n_current: 80 },
  subpopulations: {
    dimensions: {
      niveau: {
        groups: { lycee_terminale: 0.8, postbac: 0.6 },
        gap: 0.25,
        counts: { lycee_terminale: 40, postbac: 40 },
      },
      filiere: { groups: {}, gap: 0, counts: {} },
    },
    max_gap: 0.25,
    alert: true,
  },
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe("MlAuditDashboard", () => {
  it("renders the review chip, warning tiles and the subpop table on alert", async () => {
    apiFetchMock.mockResolvedValue(REPORT);
    withIntl(<MlAuditDashboard />);

    expect(await screen.findByText("Revue requise")).toBeInTheDocument();
    expect(screen.getByText("25 %")).toBeInTheDocument(); // max gap tile
    expect(screen.getByText("0.31")).toBeInTheDocument(); // KS statistic
    const table = screen.getAllByRole("table")[0] as HTMLElement;
    expect(table).toHaveTextContent("lycee_terminale");
    expect(table).toHaveTextContent("0.8");
    expect(
      screen.getByText("Aucun groupe n'atteint 30 décisions sur la fenêtre."),
    ).toBeInTheDocument();
  });

  it("renders the calm chip when healthy", async () => {
    apiFetchMock.mockResolvedValue({
      ...REPORT,
      drift: { statistic: 0.05, threshold: 0.19, alert: false },
      subpopulations: { ...REPORT.subpopulations, max_gap: 0.03, alert: false },
    });
    withIntl(<MlAuditDashboard />);
    expect(await screen.findByText("Sain")).toBeInTheDocument();
  });
});
