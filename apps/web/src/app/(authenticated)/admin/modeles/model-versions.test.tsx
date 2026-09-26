/**
 * Versions du modèle IA — Story 9.5 front tests.
 *
 * Contracts: a version above the ethics gap renders the review badge and
 * its activation DEMANDS a note (button disarmed while empty); a clean
 * version activates directly.
 */
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { beforeEach, describe, expect, it, vi } from "vitest";

import messages from "../../../../../messages/fr.json";

const apiFetchMock = vi.fn();
vi.mock("@/lib/api/client", () => ({
  apiFetch: (path: string, init?: unknown) => apiFetchMock(path, init),
  readCsrfCookie: () => "csrf",
}));

import { ModelVersions } from "./model-versions";

function withIntl(node: React.ReactElement) {
  return render(
    <NextIntlClientProvider locale="fr" messages={messages}>
      {node}
    </NextIntlClientProvider>,
  );
}

const VERSIONS = {
  versions: [
    {
      id: "mv_active",
      name: "Scorer statistique 3.3",
      version: "0.3.0-statistical",
      dataset_hash: "unversioned-legacy",
      hyperparameters: { passion_overlap: 0.3 },
      max_subpopulation_gap: 0,
      is_active: true,
      requires_ethics_review: false,
      ethics_review_note: "",
      deployed_at: null,
      deployed_by: null,
      decisions_count: 12,
    },
    {
      id: "mv_biased",
      name: "v4",
      version: "0.4.0-test",
      dataset_hash: "a".repeat(64),
      hyperparameters: {},
      max_subpopulation_gap: 0.17,
      is_active: false,
      requires_ethics_review: true,
      ethics_review_note: "",
      deployed_at: null,
      deployed_by: null,
      decisions_count: 0,
    },
  ],
};

beforeEach(() => {
  vi.clearAllMocks();
  apiFetchMock.mockImplementation((path: string) => {
    if (path === "/api/v1/admin/model-versions/") return Promise.resolve(VERSIONS);
    return Promise.resolve({});
  });
});

describe("ModelVersions", () => {
  it("shows the ethics badge with the gap and the active chip", async () => {
    withIntl(<ModelVersions />);
    expect(
      await screen.findByText("Écart inter-groupes 17 % — revue éthique requise"),
    ).toBeInTheDocument();
    expect(screen.getByText("Active")).toBeInTheDocument();
  });

  it("gated activation demands a non-empty ethics note, then posts it", async () => {
    const user = userEvent.setup();
    withIntl(<ModelVersions />);
    await screen.findByText("0.4.0-test");

    await user.click(screen.getByRole("button", { name: "Activer (revue éthique requise)" }));
    const confirm = screen.getByRole("button", { name: "Activer avec cette note" });
    expect(confirm).toBeDisabled();

    await user.type(
      screen.getByLabelText(/Note de revue éthique/),
      "Biais d'échantillonnage analysé et documenté.",
    );
    await user.click(confirm);

    await waitFor(() =>
      expect(apiFetchMock).toHaveBeenCalledWith(
        "/api/v1/admin/model-versions/mv_biased/activate/",
        expect.objectContaining({
          method: "POST",
          body: { ethics_note: "Biais d'échantillonnage analysé et documenté." },
        }),
      ),
    );
  });
});
