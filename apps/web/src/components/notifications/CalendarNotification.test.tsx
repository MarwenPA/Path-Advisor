/**
 * `CalendarNotification` tests — Story 8.7.
 *
 * Contracts: renders the backend's strings verbatim (this component writes
 * no sentence); the "dans X jours" badge is STATIC neutral text — no
 * timer (`setInterval`/`setTimeout`), no `aria-live`, no alarm styling
 * (AC1's "AUCUN compte à rebours visuel agressif" as an executable check);
 * the checklist is a plain non-blocking list (no checkboxes, no completion
 * state); exactly ONE CTA; French day agreement (0/1/n).
 */
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import messages from "../../../messages/fr.json";

import { CalendarNotification, type CalendarNotificationProps } from "./CalendarNotification";

function renderWithIntl(props: CalendarNotificationProps) {
  return render(
    <NextIntlClientProvider locale="fr" messages={messages}>
      <CalendarNotification {...props} />
    </NextIntlClientProvider>,
  );
}

const PROPS = {
  jalon: "Parcoursup : la plateforme ouvre le 14 octobre 2026",
  daysUntil: 18,
  body: "La plateforme Parcoursup ouvre le 14 octobre 2026. D'ici là, rien d'obligatoire.",
  recommendedActions: [
    "Relire tes métiers recommandés et tes paris enregistrés",
    "Vérifier que ton profil est à jour",
  ],
  ctaLabel: "Revoir mes paris",
  ctaUrl: "/mes-paris",
};

describe("CalendarNotification", () => {
  it("renders factual title, calm body and the non-blocking checklist verbatim", () => {
    renderWithIntl(PROPS);

    expect(screen.getByRole("heading", { name: PROPS.jalon })).toBeInTheDocument();
    expect(screen.getByText(PROPS.body)).toBeInTheDocument();
    for (const action of PROPS.recommendedActions) {
      expect(screen.getByText(action)).toBeInTheDocument();
    }
    // Non-blocking: plain list items, never checkboxes or completion state.
    expect(screen.queryByRole("checkbox")).not.toBeInTheDocument();
  });

  it("shows exactly one calm CTA and forwards clicks", async () => {
    const onCtaClick = vi.fn();
    const user = userEvent.setup();
    renderWithIntl({ ...PROPS, onCtaClick });

    expect(screen.getAllByRole("link")).toHaveLength(1);
    const cta = screen.getByRole("link", { name: "Revoir mes paris" });
    expect(cta).toHaveAttribute("href", "/mes-paris");
    await user.click(cta);
    expect(onCtaClick).toHaveBeenCalledTimes(1);
  });

  describe("the days badge is information, never pressure (AC1)", () => {
    beforeEach(() => {
      vi.spyOn(globalThis, "setInterval");
      vi.spyOn(globalThis, "setTimeout");
    });
    afterEach(() => {
      vi.restoreAllMocks();
    });

    it("is static muted text — no timer, no aria-live, no alarm styling", () => {
      renderWithIntl(PROPS);

      const badge = screen.getByTestId("calendar-days-until");
      expect(badge).toHaveTextContent("dans 18 jours");
      expect(badge).not.toHaveAttribute("aria-live");
      expect(badge.className).toContain("text-text-muted");
      expect(badge.className).not.toMatch(/red|destructive|animate|pulse/);
      // No countdown machinery was ever started by rendering this.
      expect(setInterval).not.toHaveBeenCalled();
    });

    it.each([
      [-3, "aujourd'hui"], // negative = upstream data bug — clamp, never show
      [0, "aujourd'hui"],
      [1, "dans 1 jour"],
      [18, "dans 18 jours"],
    ])("agrees in French (daysUntil=%s → %s)", (daysUntil, expected) => {
      renderWithIntl({ ...PROPS, daysUntil: daysUntil as number });
      expect(screen.getByTestId("calendar-days-until")).toHaveTextContent(expected as string);
    });
  });
});
