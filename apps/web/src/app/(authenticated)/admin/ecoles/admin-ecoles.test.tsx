/**
 * Back-office écoles + calendrier — Story 9.2 front tests.
 *
 * Contracts: the CSV import renders the drill-down report (created as
 * drafts, conflicts with a manual-resolution link, per-line errors); the
 * filters drive the fetcher; a notified milestone renders locked (no date
 * input) while a pending one stays editable.
 */
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { beforeEach, describe, expect, it, vi } from "vitest";

import messages from "../../../../../messages/fr.json";

const fetchSchoolsMock = vi.fn();
const importCsvMock = vi.fn();
const fetchMilestonesMock = vi.fn();
const createMilestoneMock = vi.fn();
const updateMilestoneMock = vi.fn();
vi.mock("@/lib/api/admin-schools", () => ({
  fetchAdminSchools: (query: unknown) => fetchSchoolsMock(query),
  importSchoolsCsv: (file: unknown) => importCsvMock(file),
  fetchAdminMilestones: () => fetchMilestonesMock(),
  createAdminMilestone: (payload: unknown) => createMilestoneMock(payload),
  updateAdminMilestone: (id: number, payload: unknown) => updateMilestoneMock(id, payload),
}));

import { CalendarAdmin } from "../calendrier/calendar-admin";
import { SchoolsTable } from "./schools-table";

function withIntl(node: React.ReactElement) {
  return render(
    <NextIntlClientProvider locale="fr" messages={messages}>
      {node}
    </NextIntlClientProvider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  fetchSchoolsMock.mockResolvedValue({
    count: 1,
    next: null,
    previous: null,
    results: [
      {
        id: "sch_1",
        slug: "lycee-maritime",
        name: "Lycée maritime",
        type: "lycee_pro",
        city: "Ciboure",
        region: "Nouvelle-Aquitaine",
        status: "published",
      },
    ],
  });
});

describe("SchoolsTable", () => {
  it("drives the type filter through the fetcher", async () => {
    const user = userEvent.setup();
    withIntl(<SchoolsTable />);
    await screen.findByRole("link", { name: "Lycée maritime" });

    await user.selectOptions(screen.getByLabelText("Type"), "bts");
    await waitFor(() =>
      expect(fetchSchoolsMock).toHaveBeenLastCalledWith(
        expect.objectContaining({ type: "bts", page: 1 }),
      ),
    );
  });

  it("renders the CSV report: drafts note, conflict with manual drill-down, errors", async () => {
    importCsvMock.mockResolvedValue({
      created: ["nouvelle-92"],
      conflicts: [
        {
          line: 3,
          slug: "existante-92",
          existing: { name: "Existante", city: "Rennes", status: "published" },
          incoming: { name: "Version CSV" },
        },
      ],
      errors: [{ line: 4, errors: { slug: ["Doublon dans le fichier."] } }],
    });
    const user = userEvent.setup();
    withIntl(<SchoolsTable />);
    await screen.findByRole("link", { name: "Lycée maritime" });

    const file = new File(["slug;name"], "import.csv", { type: "text/csv" });
    await user.upload(screen.getByLabelText("Importer un CSV"), file);

    const report = await screen.findByRole("status");
    expect(report).toHaveTextContent("1 créée(s) · 1 conflit(s) · 1 erreur(s)");
    expect(report).toHaveTextContent("brouillon");
    expect(screen.getByRole("link", { name: "Ouvrir la fiche pour arbitrer" })).toHaveAttribute(
      "href",
      "/admin/ecoles/existante-92",
    );
    expect(report).toHaveTextContent("Ligne 4 invalide");
  });
});

describe("CalendarAdmin", () => {
  it("locks a notified milestone and keeps a pending one editable", async () => {
    fetchMilestonesMock.mockResolvedValue({
      milestones: [
        {
          id: 1,
          kind: "ouverture",
          kind_label: "Ouverture Parcoursup",
          campaign: "2027-2028",
          date: "2027-01-20",
          notify_days_before: 18,
          notified_at: "2027-01-02T07:00:00Z",
        },
        {
          id: 2,
          kind: "fermeture_voeux",
          kind_label: "Fermeture des vœux",
          campaign: "2027-2028",
          date: "2027-03-11",
          notify_days_before: 7,
          notified_at: null,
        },
      ],
    });
    withIntl(<CalendarAdmin />);

    expect(await screen.findByText("Notifié aux élèves — date verrouillée")).toBeInTheDocument();
    // Exactly ONE editable date input in the list (the pending milestone) —
    // plus the creation form's date field.
    const dateInputs = screen
      .getAllByLabelText("Date")
      .filter((input) => (input as HTMLInputElement).type === "date");
    expect(dateInputs).toHaveLength(2); // form + pending row, never the locked one
  });

  it("creates a milestone through the fetcher", async () => {
    fetchMilestonesMock.mockResolvedValue({ milestones: [] });
    createMilestoneMock.mockResolvedValue({ id: 7 });
    const user = userEvent.setup();
    withIntl(<CalendarAdmin />);
    await screen.findByText("Aucun jalon — ajoute la campagne à venir.");

    await user.type(screen.getByLabelText("Campagne"), "2027-2028");
    await user.type(screen.getByLabelText("Date"), "2027-01-20");
    await user.click(screen.getByRole("button", { name: "Ajouter le jalon" }));

    await waitFor(() =>
      expect(createMilestoneMock).toHaveBeenCalledWith({
        kind: "ouverture",
        campaign: "2027-2028",
        date: "2027-01-20",
        notify_days_before: 18,
      }),
    );
  });
});
