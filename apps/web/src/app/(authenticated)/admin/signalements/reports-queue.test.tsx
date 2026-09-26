/**
 * File de signalements — Story 9.3 front tests.
 *
 * Contracts: overdue banner + per-row badge; "corriger" links to the 9.1
 * fiche; dismiss/request-info demand a non-empty text before the confirm
 * button arms; resolve refreshes the queue.
 */
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { beforeEach, describe, expect, it, vi } from "vitest";

import messages from "../../../../../messages/fr.json";

const fetchReportsMock = vi.fn();
const actMock = vi.fn();
vi.mock("@/lib/api/admin-reports", () => ({
  fetchAdminReports: (query: unknown) => fetchReportsMock(query),
  actOnReport: (id: string, action: string, body: unknown) => actMock(id, action, body),
}));

import { ReportsQueue } from "./reports-queue";

function withIntl(node: React.ReactElement) {
  return render(
    <NextIntlClientProvider locale="fr" messages={messages}>
      {node}
    </NextIntlClientProvider>,
  );
}

const REPORT = {
  id: "rep_1",
  profession_slug: "metier-signale",
  profession_name: "Métier Signalé",
  reporter_id: "usr_x",
  error_type: "debouches_perimes",
  error_type_label: "Débouchés ou informations périmées",
  location: null,
  comment: "Les débouchés datent de 2019.",
  status: "pending" as const,
  created_at: new Date(Date.now() - 10 * 86_400_000).toISOString(),
  overdue: true,
  admin_note: "",
};

beforeEach(() => {
  vi.clearAllMocks();
  fetchReportsMock.mockResolvedValue({
    count: 1,
    next: null,
    previous: null,
    overdue_count: 1,
    results: [REPORT],
  });
});

describe("ReportsQueue", () => {
  it("shows the SLA banner, the overdue badge and the fix-fiche link", async () => {
    withIntl(<ReportsQueue />);

    expect(await screen.findByText("1 signalement(s) au-delà de 7 jours")).toBeInTheDocument();
    expect(screen.getByText("> 7 jours")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Corriger la fiche" })).toHaveAttribute(
      "href",
      "/admin/metiers/metier-signale",
    );
  });

  it("dismiss demands a reason before confirming, then posts it", async () => {
    actMock.mockResolvedValue({ id: "rep_1", status: "dismissed" });
    const user = userEvent.setup();
    withIntl(<ReportsQueue />);
    await screen.findByText("Métier Signalé");

    await user.click(screen.getByRole("button", { name: "Rejeter" }));
    const confirm = screen.getByRole("button", { name: "Confirmer" });
    expect(confirm).toBeDisabled(); // empty reason cannot ship

    await user.type(
      screen.getByLabelText(/Motif du rejet/),
      "Information déjà à jour sur la fiche.",
    );
    await user.click(confirm);

    await waitFor(() =>
      expect(actMock).toHaveBeenCalledWith("rep_1", "dismiss", {
        note: undefined,
        reason: "Information déjà à jour sur la fiche.",
        message: undefined,
      }),
    );
  });

  it("resolve refreshes the queue", async () => {
    actMock.mockResolvedValue({ id: "rep_1", status: "resolved" });
    const user = userEvent.setup();
    withIntl(<ReportsQueue />);
    await screen.findByText("Métier Signalé");

    fetchReportsMock.mockResolvedValue({
      count: 0,
      next: null,
      previous: null,
      overdue_count: 0,
      results: [],
    });
    await user.click(screen.getByRole("button", { name: "Marquer résolu" }));

    expect(await screen.findByText(/la file est à jour/)).toBeInTheDocument();
    expect(actMock).toHaveBeenCalledWith("rep_1", "resolve", {
      note: "",
      reason: undefined,
      message: undefined,
    });
  });
});
