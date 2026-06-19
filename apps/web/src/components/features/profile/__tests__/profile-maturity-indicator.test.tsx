/**
 * ProfileMaturityIndicator tests — Story 2.7 AC1 + AC3 + AC4 + AC5 + AC6 + AC7 + AC9.
 */

import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import {
  ProfileMaturityIndicator,
  type MaturityNextAction,
} from "../profile-maturity-indicator";

const BASE_ACTIONS: MaturityNextAction[] = [
  {
    icon: "bulletins",
    label: "Ajoute un bulletin",
    benefit: "Tu débloques les stats personnalisées",
    onClick: vi.fn(),
  },
  {
    icon: "passions",
    label: "Affine tes passions et valeurs",
    benefit: "Tes recos métiers seront plus précises",
    onClick: vi.fn(),
  },
];

const ENRICHED_ACTIONS: MaturityNextAction[] = [
  {
    icon: "bulletins",
    label: "Ajoute un autre trimestre",
    benefit: "Tes stats deviennent encore plus précises",
    onClick: vi.fn(),
  },
];

// ---------------------------------------------------------------------------
// AC1 — TypeScript API contract
// ---------------------------------------------------------------------------

describe("ProfileMaturityIndicator — API contract (AC1)", () => {
  it("renders with minimal required props", () => {
    render(<ProfileMaturityIndicator level="base" nextActions={BASE_ACTIONS} />);
    expect(screen.getByText("Profil de base")).toBeInTheDocument();
  });

  it("renders enriched level label", () => {
    render(<ProfileMaturityIndicator level="enriched" nextActions={ENRICHED_ACTIONS} />);
    expect(screen.getByText("Profil enrichi")).toBeInTheDocument();
  });

  it("renders complete level label", () => {
    render(<ProfileMaturityIndicator level="complete" nextActions={[]} />);
    expect(screen.getByText("Profil complet")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// AC3 — variant profile-header layout
// ---------------------------------------------------------------------------

describe("ProfileMaturityIndicator variant profile-header (AC3)", () => {
  it("shows description and CTA button for non-complete levels", () => {
    render(
      <ProfileMaturityIndicator
        level="base"
        nextActions={BASE_ACTIONS}
        variant="profile-header"
      />
    );
    expect(
      screen.getByText(/Tu as l'essentiel pour des recos indicatives/i)
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Voir comment compléter/i })
    ).toBeInTheDocument();
  });

  it("does not show CTA button when level is complete", () => {
    render(
      <ProfileMaturityIndicator
        level="complete"
        nextActions={[]}
        variant="profile-header"
        showCallToAction={false}
      />
    );
    expect(
      screen.queryByRole("button", { name: /Voir comment compléter/i })
    ).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// AC4 — nextActions list expand / collapse
// ---------------------------------------------------------------------------

describe("ProfileMaturityIndicator — nextActions expand (AC4)", () => {
  it("expands list on CTA click and shows actions", () => {
    render(
      <ProfileMaturityIndicator
        level="base"
        nextActions={BASE_ACTIONS}
        variant="profile-header"
      />
    );
    fireEvent.click(screen.getByRole("button", { name: /Voir comment compléter/i }));
    expect(screen.getByText("Ajoute un bulletin")).toBeInTheDocument();
    expect(screen.getByText("Affine tes passions et valeurs")).toBeInTheDocument();
  });

  it("calls onClick when action card is tapped", () => {
    const handler = vi.fn();
    const actions: MaturityNextAction[] = [
      { icon: "bulletins", label: "Ajoute un bulletin", benefit: "Tes stats", onClick: handler },
    ];
    render(
      <ProfileMaturityIndicator level="base" nextActions={actions} variant="profile-header" />
    );
    fireEvent.click(screen.getByRole("button", { name: /Voir comment compléter/i }));
    fireEvent.click(screen.getByText("Ajoute un bulletin"));
    expect(handler).toHaveBeenCalledTimes(1);
  });

  it("collapses list on Plier click", () => {
    render(
      <ProfileMaturityIndicator
        level="base"
        nextActions={BASE_ACTIONS}
        variant="profile-header"
      />
    );
    fireEvent.click(screen.getByRole("button", { name: /Voir comment compléter/i }));
    expect(screen.getByText("Ajoute un bulletin")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Plier/i }));
    expect(screen.queryByText("Ajoute un bulletin")).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// AC5 — variant dashboard-card
// ---------------------------------------------------------------------------

describe("ProfileMaturityIndicator variant dashboard-card (AC5)", () => {
  it("renders compact layout without expand", () => {
    render(
      <ProfileMaturityIndicator
        level="enriched"
        nextActions={ENRICHED_ACTIONS}
        variant="dashboard-card"
      />
    );
    expect(screen.getByText(/Profil enrichi/i)).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Voir comment compléter/i })
    ).not.toBeInTheDocument();
  });

  it("returns null when level is complete (anti-noise AC5)", () => {
    const { container } = render(
      <ProfileMaturityIndicator
        level="complete"
        nextActions={[]}
        variant="dashboard-card"
      />
    );
    expect(container.firstChild).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// AC6 — variant inline-compact
// ---------------------------------------------------------------------------

describe("ProfileMaturityIndicator variant inline-compact (AC6)", () => {
  it("shows only the level pill", () => {
    render(
      <ProfileMaturityIndicator
        level="enriched"
        nextActions={ENRICHED_ACTIONS}
        variant="inline-compact"
      />
    );
    expect(screen.getByText("Profil enrichi")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Voir comment compléter/i })
    ).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// AC3 — runtime dev validation (forbidden words)
// ---------------------------------------------------------------------------

describe("ProfileMaturityIndicator — forbidden words runtime check (AC3)", () => {
  it("warns in dev when a nextAction benefit contains a forbidden word", () => {
    const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
    const badActions: MaturityNextAction[] = [
      {
        icon: "bulletins",
        label: "Complète ton profil",
        benefit: "Il te manque tes bulletins",
        onClick: vi.fn(),
      },
    ];
    render(<ProfileMaturityIndicator level="base" nextActions={badActions} variant="profile-header" />);
    expect(warnSpy).toHaveBeenCalled();
    warnSpy.mockRestore();
  });
});

// ---------------------------------------------------------------------------
// AC7 — accessibility
// ---------------------------------------------------------------------------

describe("ProfileMaturityIndicator — accessibility (AC7)", () => {
  it("CTA button has aria-expanded false initially", () => {
    render(
      <ProfileMaturityIndicator level="base" nextActions={BASE_ACTIONS} variant="profile-header" />
    );
    const btn = screen.getByRole("button", { name: /Voir comment compléter/i });
    expect(btn).toHaveAttribute("aria-expanded", "false");
  });

  it("CTA button has aria-expanded true after click", () => {
    render(
      <ProfileMaturityIndicator level="base" nextActions={BASE_ACTIONS} variant="profile-header" />
    );
    const btn = screen.getByRole("button", { name: /Voir comment compléter/i });
    fireEvent.click(btn);
    expect(btn).toHaveAttribute("aria-expanded", "true");
  });

  it("container has role region with label", () => {
    render(
      <ProfileMaturityIndicator level="base" nextActions={BASE_ACTIONS} variant="profile-header" />
    );
    expect(screen.getByRole("region")).toBeInTheDocument();
  });
});
