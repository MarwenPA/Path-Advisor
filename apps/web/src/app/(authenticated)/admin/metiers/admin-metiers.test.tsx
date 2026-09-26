/**
 * Back-office métiers — Story 9.1 front tests.
 *
 * Contracts: the table lists every status with badges and drives
 * search/filter through the fetcher; the form parses JSON fields and
 * surfaces a calm error on bad JSON instead of submitting; rollback calls
 * the endpoint of the CHOSEN revision and refreshes the draft.
 */
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { beforeEach, describe, expect, it, vi } from "vitest";

import messages from "../../../../../messages/fr.json";

import type { AdminProfession } from "@/lib/api/admin-professions";

const fetchListMock = vi.fn();
const createMock = vi.fn();
const updateMock = vi.fn();
const archiveMock = vi.fn();
const revisionsMock = vi.fn();
const rollbackMock = vi.fn();
vi.mock("@/lib/api/admin-professions", () => ({
  fetchAdminProfessions: (query: unknown) => fetchListMock(query),
  fetchAdminProfession: vi.fn(),
  createAdminProfession: (payload: unknown) => createMock(payload),
  updateAdminProfession: (slug: string, payload: unknown) => updateMock(slug, payload),
  archiveAdminProfession: (slug: string) => archiveMock(slug),
  fetchProfessionRevisions: (slug: string) => revisionsMock(slug),
  rollbackAdminProfession: (slug: string, id: string) => rollbackMock(slug, id),
}));

const routerPush = vi.fn();
const routerReplace = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: routerPush, replace: routerReplace }),
}));

import { ProfessionForm } from "./profession-form";
import { ProfessionsTable } from "./professions-table";

function withIntl(node: React.ReactElement) {
  return render(
    <NextIntlClientProvider locale="fr" messages={messages}>
      {node}
    </NextIntlClientProvider>,
  );
}

function makeProfession(overrides: Partial<AdminProfession> = {}): AdminProfession {
  return {
    id: "prof_1",
    slug: "cartographe-marin",
    name: "Cartographe marin",
    description: "d".repeat(120),
    daily_routine: "Tu commences…",
    requirements_json: [],
    prospects_text: "Trois débouchés.",
    median_salary_eur: 32000,
    salary_range_json: null,
    signals_json: { passions: ["mer"], valeurs: [], specialites: [] },
    level_compatibility: ["postbac"],
    sector: "environnement",
    rome_code: null,
    sources_json: ["Onisep"],
    is_active: true,
    status: "published",
    created_at: "2026-09-26T10:00:00Z",
    updated_at: "2026-09-26T10:00:00Z",
    ...overrides,
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  fetchListMock.mockResolvedValue({
    count: 2,
    next: null,
    previous: null,
    results: [
      makeProfession(),
      makeProfession({ id: "prof_2", slug: "brouillon-x", name: "Vulcanologue", status: "draft" }),
    ],
  });
  revisionsMock.mockResolvedValue({ revisions: [] });
});

describe("ProfessionsTable", () => {
  it("lists every status with its badge and links to the fiche", async () => {
    withIntl(<ProfessionsTable />);
    expect(await screen.findByRole("link", { name: "Cartographe marin" })).toHaveAttribute(
      "href",
      "/admin/metiers/cartographe-marin",
    );
    // "Publié"/"Brouillon" also exist as <option>s of the filter — target
    // the badges inside the table body.
    const table = screen.getByRole("table");
    expect(table).toHaveTextContent("Publié");
    expect(table).toHaveTextContent("Brouillon");
  });

  it("drives the status filter through the fetcher", async () => {
    const user = userEvent.setup();
    withIntl(<ProfessionsTable />);
    await screen.findByText("Vulcanologue");

    await user.selectOptions(screen.getByLabelText("Statut"), "draft");
    await waitFor(() =>
      expect(fetchListMock).toHaveBeenLastCalledWith(
        expect.objectContaining({ status: "draft", page: 1 }),
      ),
    );
  });
});

describe("ProfessionForm", () => {
  it("refuses to submit malformed JSON with a calm inline error", async () => {
    const user = userEvent.setup();
    withIntl(<ProfessionForm initial={makeProfession()} />);

    const signals = screen.getByLabelText("Signaux (passions / valeurs / spécialités)");
    await user.clear(signals);
    await user.type(signals, "{{pas du json");
    await user.click(screen.getByRole("button", { name: "Enregistrer" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Un des champs JSON est mal formé");
    expect(updateMock).not.toHaveBeenCalled();
  });

  it("saves an edit through the PATCH fetcher", async () => {
    updateMock.mockResolvedValue(makeProfession({ median_salary_eur: 35000 }));
    const user = userEvent.setup();
    withIntl(<ProfessionForm initial={makeProfession()} />);

    const salary = screen.getByLabelText("Salaire médian (EUR/an)");
    await user.clear(salary);
    await user.type(salary, "35000");
    await user.click(screen.getByRole("button", { name: "Enregistrer" }));

    await waitFor(() => expect(updateMock).toHaveBeenCalledTimes(1));
    expect(updateMock.mock.calls[0][1]).toMatchObject({ median_salary_eur: 35000 });
    expect(await screen.findByRole("status")).toHaveTextContent("enregistrées");
  });

  it("rollback targets the chosen revision and refreshes the draft", async () => {
    revisionsMock.mockResolvedValue({
      revisions: [
        {
          id: "prev_new",
          action: "updated",
          snapshot: {},
          editor_email: "karim@test.local",
          restored_from_id: null,
          created_at: "2026-09-26T11:00:00Z",
        },
        {
          id: "prev_old",
          action: "created",
          snapshot: {},
          editor_email: "karim@test.local",
          restored_from_id: null,
          created_at: "2026-09-26T10:00:00Z",
        },
      ],
    });
    rollbackMock.mockResolvedValue(makeProfession({ name: "Cartographe marin (v1)" }));
    const user = userEvent.setup();
    withIntl(<ProfessionForm initial={makeProfession()} />);

    // The newest revision (index 0) is the current state — no rollback
    // button; the older one restores.
    const buttons = await screen.findAllByRole("button", { name: "Restaurer cette version" });
    expect(buttons).toHaveLength(1);
    await user.click(buttons[0] as HTMLElement);

    await waitFor(() => expect(rollbackMock).toHaveBeenCalledWith("cartographe-marin", "prev_old"));
    expect(screen.getByLabelText("Nom")).toHaveValue("Cartographe marin (v1)");
  });

  it("archive is the delete: posts then returns to the list", async () => {
    archiveMock.mockResolvedValue(makeProfession({ status: "archived" }));
    const user = userEvent.setup();
    withIntl(<ProfessionForm initial={makeProfession()} />);

    await user.click(screen.getByRole("button", { name: /Archiver/ }));
    await waitFor(() => expect(archiveMock).toHaveBeenCalledWith("cartographe-marin"));
    expect(routerPush).toHaveBeenCalledWith("/admin/metiers");
  });
});
