/**
 * <TierAccessCard> tests — Story 1.9 §T8.2.
 *
 * Assert accessible name, aria-describedby wiring, disabled-button
 * semantics, badge rendering, relative-date output.
 */
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { TierAccessCard } from "./tier-access-card";

import type { AccessListEntry } from "@/lib/api/access-list";

const _entry = (over: Partial<AccessListEntry> = {}): AccessListEntry => ({
  id: "parental_consent:abc-123",
  tier_type: "parent",
  display_name: "parent@example.test",
  granted_at: new Date(Date.now() - 3 * 7 * 24 * 60 * 60 * 1000).toISOString(),
  visible_data: ["metiers_explores", "parcours_sauvegardes"],
  masked_data: ["bulletins_detailles", "appreciations_enseignants"],
  revocable: true,
  ...over,
});

describe("TierAccessCard", () => {
  it("renders the display name as the article's accessible name", () => {
    render(<TierAccessCard entry={_entry()} />);
    const article = screen.getByRole("article", { name: /parent@example.test/i });
    expect(article).toBeInTheDocument();
  });

  it("renders the tier badge with the FR label", () => {
    render(<TierAccessCard entry={_entry()} />);
    // The badge has an aria-label "Type d'accès : Parent"
    expect(screen.getByLabelText(/type d'accès : parent/i)).toBeInTheDocument();
  });

  it("translates known data areas to FR labels", () => {
    render(<TierAccessCard entry={_entry()} />);
    expect(screen.getByText("Métiers explorés")).toBeInTheDocument();
    expect(screen.getByText("Parcours sauvegardés")).toBeInTheDocument();
    expect(screen.getByText("Bulletins détaillés")).toBeInTheDocument();
  });

  it("renders revoke button as disabled with the aria-label fallback", () => {
    render(<TierAccessCard entry={_entry()} />);
    const btn = screen.getByRole("button", { name: /révocation à venir/i });
    expect(btn).toBeDisabled();
  });

  it("wires aria-describedby on the revoke button to the visibility section", () => {
    render(<TierAccessCard entry={_entry()} />);
    const btn = screen.getByRole("button", { name: /révocation à venir/i });
    const describedBy = btn.getAttribute("aria-describedby");
    expect(describedBy).toBeTruthy();
    expect(document.getElementById(describedBy!)).toBeInTheDocument();
  });

  it("renders a <time> element with both absolute (title) and relative text", () => {
    const iso = new Date(Date.now() - 3 * 7 * 24 * 60 * 60 * 1000).toISOString();
    render(<TierAccessCard entry={_entry({ granted_at: iso })} />);
    const time = document.querySelector("time");
    expect(time).not.toBeNull();
    expect(time!.getAttribute("datetime")).toBe(iso);
    expect(time!.getAttribute("title")).toBeTruthy();
    // Output should be in the form "il y a X semaines/jours/heures/..."
    expect(time!.textContent).toMatch(/il y a|à l'instant|hier|aujourd/i);
  });

  it("applies tier-specific badge style for non-parent tiers", () => {
    const { rerender } = render(<TierAccessCard entry={_entry({ tier_type: "school" })} />);
    expect(screen.getByLabelText(/type d'accès : école/i)).toBeInTheDocument();
    rerender(<TierAccessCard entry={_entry({ tier_type: "counselor" })} />);
    expect(screen.getByLabelText(/type d'accès : conseillère/i)).toBeInTheDocument();
  });
});
