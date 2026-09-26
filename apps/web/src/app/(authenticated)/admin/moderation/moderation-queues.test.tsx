/**
 * Modération — Story 9.4 front tests.
 *
 * Contracts: prescreen chips render as an AID (with the human-decision
 * note always visible); rejecting a motivation demands the typed category
 * AND a non-empty reason before the confirm arms; the school-comments tab
 * approves/rejects through the fetcher.
 */
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { beforeEach, describe, expect, it, vi } from "vitest";

import messages from "../../../../../messages/fr.json";

const fetchMotivationsMock = vi.fn();
const fetchCommentsMock = vi.fn();
const actMotivationMock = vi.fn();
const actCommentMock = vi.fn();
vi.mock("@/lib/api/admin-moderation", () => ({
  fetchPendingMotivations: () => fetchMotivationsMock(),
  fetchPendingSchoolComments: () => fetchCommentsMock(),
  actOnMotivation: (id: string, action: string, body: unknown) =>
    actMotivationMock(id, action, body),
  actOnSchoolComment: (id: string, action: string) => actCommentMock(id, action),
}));

import { ModerationQueues } from "./moderation-queues";

function withIntl(node: React.ReactElement) {
  return render(
    <NextIntlClientProvider locale="fr" messages={messages}>
      {node}
    </NextIntlClientProvider>,
  );
}

const MOTIVATION = {
  id: "reach_1",
  student_email: "eleve@test.local",
  school: { slug: "ecole-mod", name: "École Mod" },
  profession_name: "Métier Mod",
  motivation_text: "Appelle-moi au 06 12 34 56 78.",
  created_at: new Date().toISOString(),
  business_hours_age: 30,
  overdue: true,
  prescreen: { pii: ["telephone"], risk: [] },
};

beforeEach(() => {
  vi.clearAllMocks();
  fetchMotivationsMock.mockResolvedValue({ results: [MOTIVATION], overdue_count: 1 });
  fetchCommentsMock.mockResolvedValue({
    results: [
      {
        id: "resp_1",
        school: { slug: "ecole-mod", name: "École Mod" },
        action: "interested",
        comment: "Très bon dossier.",
        created_at: new Date().toISOString(),
        business_hours_age: 2,
        overdue: false,
        prescreen: { pii: [], risk: [] },
      },
    ],
    overdue_count: 0,
  });
});

describe("ModerationQueues", () => {
  it("shows the human-decision note, the SLA badge and the prescreen chip", async () => {
    withIntl(<ModerationQueues />);

    expect(await screen.findByText(/la décision finale est toujours humaine/)).toBeInTheDocument();
    expect(screen.getByText(/SLA 24 h dépassé/)).toBeInTheDocument();
    expect(screen.getByText("Donnée personnelle : telephone")).toBeInTheDocument();
  });

  it("reject demands category AND reason before arming", async () => {
    actMotivationMock.mockResolvedValue({ id: "reach_1", status: "rejected" });
    const user = userEvent.setup();
    withIntl(<ModerationQueues />);
    await screen.findByText("École Mod");

    await user.click(screen.getByRole("button", { name: "Refuser" }));
    const confirm = screen.getByRole("button", { name: "Confirmer le refus" });
    expect(confirm).toBeDisabled(); // empty reason cannot ship

    await user.selectOptions(screen.getByLabelText("Catégorie de refus"), "donnees_tierces");
    await user.type(
      screen.getByLabelText(/Commentaire envoyé à l'élève/),
      "Le texte contient un numéro de téléphone personnel.",
    );
    await user.click(confirm);

    await waitFor(() =>
      expect(actMotivationMock).toHaveBeenCalledWith("reach_1", "reject", {
        category: "donnees_tierces",
        reason: "Le texte contient un numéro de téléphone personnel.",
      }),
    );
  });

  it("the school-comments tab approves through the fetcher", async () => {
    actCommentMock.mockResolvedValue({ id: "resp_1", comment_status: "approved" });
    const user = userEvent.setup();
    withIntl(<ModerationQueues />);
    await screen.findByText(/Motivations élèves/);

    await user.click(screen.getByRole("tab", { name: /Commentaires écoles/ }));
    expect(await screen.findByText("Très bon dossier.")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Approuver (visible pour l'élève)" }));
    await waitFor(() => expect(actCommentMock).toHaveBeenCalledWith("resp_1", "approve"));
  });
});
