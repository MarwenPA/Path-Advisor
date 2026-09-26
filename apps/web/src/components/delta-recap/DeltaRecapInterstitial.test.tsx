/**
 * `DeltaRecapInterstitial` tests — Story 8.6.
 *
 * Contracts: stable state renders NOTHING (the AC's silent fall-through to
 * the home); cards render with ONE primary CTA each and the backend's own
 * strings verbatim; the before/after stat chip only shows when 5.8 applied
 * a delta; "Tout vu, continuer" acks then unmounts; a card CTA click also
 * acks (navigating through a card = having seen the recap); no emoji ever
 * (anti-cirque is backend-linted, but the chrome strings are ours).
 */
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { beforeEach, describe, expect, it, vi } from "vitest";

import messages from "../../../messages/fr.json";

import type { DeltaRecapCard } from "@/lib/api/delta-recap";

const ackMock = vi.fn().mockResolvedValue(undefined);
vi.mock("@/lib/api/delta-recap", () => ({
  acknowledgeDeltaRecap: () => ackMock(),
}));

import { DeltaRecapInterstitial } from "./DeltaRecapInterstitial";

function renderWithIntl(cards: DeltaRecapCard[]) {
  return render(
    <NextIntlClientProvider locale="fr" messages={messages}>
      <DeltaRecapInterstitial cards={cards} />
    </NextIntlClientProvider>,
  );
}

function makeCard(overrides: Partial<DeltaRecapCard> = {}): DeltaRecapCard {
  return {
    kind: "school_response",
    title: "École Test a répondu — profil intéressant",
    body: "Une réponse encourageante est arrivée pendant ton absence.",
    cta_label: "Voir le parcours mis à jour",
    cta_url: "/mes-envois/eor_x",
    stat_before: null,
    stat_after: null,
    ...overrides,
  };
}

beforeEach(() => {
  ackMock.mockClear();
});

describe("DeltaRecapInterstitial", () => {
  it("renders nothing at all in the stable state (silent fall-through)", () => {
    const { container } = renderWithIntl([]);
    expect(container.innerHTML).toBe("");
  });

  it("shows a full-screen dialog with one card per delta and the backend's strings verbatim", () => {
    renderWithIntl([
      makeCard(),
      makeCard({
        kind: "new_schools",
        title: "2 nouvelles écoles correspondent à ton profil",
        body: "Ajoutées depuis ta dernière visite.",
        cta_label: "Voir les nouvelles écoles",
        cta_url: "/schools",
        count: 2,
      }),
    ]);

    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("aria-modal", "true");
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "Depuis ta dernière visite",
    );
    expect(
      screen.getByRole("heading", { name: "École Test a répondu — profil intéressant" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Voir les nouvelles écoles" })).toHaveAttribute(
      "href",
      "/schools",
    );
  });

  it("shows the before/after stat chip only when 5.8 applied a delta", () => {
    renderWithIntl([makeCard({ stat_before: 45, stat_after: 55 })]);
    expect(screen.getByText("45 % → 55 %")).toBeInTheDocument();

    renderWithIntl([makeCard()]);
    expect(screen.getAllByText(/%\s*→\s*/)).toHaveLength(1); // no second chip
  });

  it("renders the milestone checklist as non-blocking suggestions", () => {
    renderWithIntl([
      makeCard({
        kind: "parcoursup_milestone",
        title: "Parcoursup : la plateforme ouvre le 15 janvier 2027",
        cta_label: "Revoir mes paris",
        cta_url: "/mes-paris",
        days_until: 18,
        recommended_actions: ["Relire tes métiers recommandés", "Vérifier ton profil"],
      }),
    ]);
    expect(screen.getByText("Relire tes métiers recommandés")).toBeInTheDocument();
    expect(screen.getByText("Vérifier ton profil")).toBeInTheDocument();
  });

  it("« Tout vu, continuer » acks then unmounts, revealing the home underneath", async () => {
    const user = userEvent.setup();
    renderWithIntl([makeCard()]);

    await user.click(screen.getByRole("button", { name: "Tout vu, continuer" }));

    expect(ackMock).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("a card CTA click also acks (navigating through a card = seen)", async () => {
    const user = userEvent.setup();
    renderWithIntl([makeCard()]);

    await user.click(screen.getByRole("link", { name: "Voir le parcours mis à jour" }));

    expect(ackMock).toHaveBeenCalledTimes(1);
  });

  it("chrome strings carry no emoji (anti-cirque applies to our copy too)", () => {
    renderWithIntl([makeCard()]);
    const dialogText = screen.getByRole("dialog").textContent ?? "";
    expect(/[\u{1F300}-\u{1FAFF}\u{2700}-\u{27BF}]/u.test(dialogText)).toBe(false);
  });
});
