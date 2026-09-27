/**
 * QualityDashboard — Story 10.3 contracts.
 *
 * Contracts: an alerting report renders the "À traiter" chip, the warning
 * tiles and the queue CTAs; a healthy one renders the calm chip; trends
 * render one bar per month.
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

import { QualityDashboard } from "./quality-dashboard";

function withIntl(node: React.ReactElement) {
  return render(
    <NextIntlClientProvider locale="fr" messages={messages}>
      {node}
    </NextIntlClientProvider>,
  );
}

const REPORT = {
  professions: { published: 48, draft: 3, archived: 2, targets: { mvp: 50, growth: 500 } },
  schools: { published: 96, draft: 1, archived: 0, targets: { mvp: 100, growth: 1000 } },
  freshness: {
    window_days: 365,
    threshold_pct: 60,
    professions_pct: 42.5,
    schools_pct: 88.0,
    alert: true,
  },
  reports: { open: 23, overdue: 4, threshold: 20, alert: true },
  moderation: { motivations_pending: 2, school_comments_pending: 1 },
  trends: {
    months: ["2026-04", "2026-05", "2026-06", "2026-07", "2026-08", "2026-09"],
    profession_edits: [1, 0, 4, 2, 7, 3],
    school_edits: [0, 0, 1, 0, 2, 5],
    reports_opened: [2, 1, 0, 3, 5, 8],
  },
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe("QualityDashboard", () => {
  it("renders the alert chip, warning tiles and queue CTAs on alert", async () => {
    apiFetchMock.mockResolvedValue(REPORT);
    withIntl(<QualityDashboard />);

    expect(await screen.findByText("À traiter")).toBeInTheDocument();
    expect(screen.getByText("48 / 50")).toBeInTheDocument();
    expect(screen.getByText("42.5 %")).toBeInTheDocument();
    expect(screen.getByText("23")).toBeInTheDocument();
    const queueLinks = screen.getAllByRole("link", { name: "Traiter la file" });
    expect(queueLinks[0]).toHaveAttribute("href", "/admin/signalements");
    expect(queueLinks[1]).toHaveAttribute("href", "/admin/moderation");
    expect(screen.getAllByRole("img").length).toBe(3); // 3 séries de barres
  });

  it("renders the calm chip when healthy", async () => {
    apiFetchMock.mockResolvedValue({
      ...REPORT,
      freshness: { ...REPORT.freshness, professions_pct: 90, alert: false },
      reports: { ...REPORT.reports, open: 3, alert: false },
    });
    withIntl(<QualityDashboard />);
    expect(await screen.findByText("Sain")).toBeInTheDocument();
  });
});
