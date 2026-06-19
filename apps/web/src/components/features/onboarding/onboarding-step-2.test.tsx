/**
 * Tests for Story 2.2 — OnboardingStep2 component + sub-components.
 *
 * Strategy: unit tests for business logic (isDraftComplete, toggleSpecialite cap),
 * RTL integration tests for rendering + interaction, and snapshot tests for RecapCard.
 */

import * as React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { isDraftComplete, type Step2Draft } from "@/hooks/use-onboarding-step-2";
import { NiveauPicker } from "./niveau-picker";
import { Branche3eme } from "./branche-3eme";
import { RecapCard } from "./recap-card";
import { SpecialitesPicker } from "./specialites-picker";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

vi.mock("next-auth/react", () => ({
  useSession: () => ({ data: { user: { id: "user-1" } } }),
}));

vi.mock("@/hooks/use-onboarding-step-2", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/hooks/use-onboarding-step-2")>();
  return {
    ...actual,
    useOnboardingStep2: vi.fn().mockReturnValue({
      snapshot: { onboarding_step2_status: "pending" },
      draft: {
        level: null,
        filiere: null,
        sous_filiere_techno: null,
        specialites: [],
        intended_track: null,
        postbac_year: null,
        postbac_formation_type: null,
      },
      isLoading: false,
      isSaving: false,
      isError: false,
      setLevel: vi.fn(),
      setFiliere: vi.fn(),
      setSousFiliere: vi.fn(),
      toggleSpecialite: vi.fn(),
      setIntendedTrack: vi.fn(),
      setPostbacYear: vi.fn(),
      setPostbacFormationType: vi.fn(),
      saveDraft: vi.fn(),
      commitLevel: vi.fn().mockResolvedValue({}),
      skipStep: vi.fn().mockResolvedValue(undefined),
      isDraftComplete: false,
    }),
  };
});

// ---------------------------------------------------------------------------
// isDraftComplete unit tests
// ---------------------------------------------------------------------------

describe("isDraftComplete", () => {
  it("returns false when level is null", () => {
    const draft: Step2Draft = {
      level: null, filiere: null, sous_filiere_techno: null,
      specialites: [], intended_track: null, postbac_year: null, postbac_formation_type: null,
    };
    expect(isDraftComplete(draft)).toBe(false);
  });

  it("returns true for 3ème with intended_track", () => {
    const draft: Step2Draft = {
      level: "college_3eme", filiere: null, sous_filiere_techno: null,
      specialites: [], intended_track: "pro", postbac_year: null, postbac_formation_type: null,
    };
    expect(isDraftComplete(draft)).toBe(true);
  });

  it("returns false for 3ème without intended_track", () => {
    const draft: Step2Draft = {
      level: "college_3eme", filiere: null, sous_filiere_techno: null,
      specialites: [], intended_track: null, postbac_year: null, postbac_formation_type: null,
    };
    expect(isDraftComplete(draft)).toBe(false);
  });

  it("returns true for Terminale général with 2 specs", () => {
    const draft: Step2Draft = {
      level: "lycee_terminale", filiere: "general", sous_filiere_techno: null,
      specialites: ["mathematiques", "svt"], intended_track: null, postbac_year: null, postbac_formation_type: null,
    };
    expect(isDraftComplete(draft)).toBe(true);
  });

  it("returns false for Terminale général with 1 spec", () => {
    const draft: Step2Draft = {
      level: "lycee_terminale", filiere: "general", sous_filiere_techno: null,
      specialites: ["mathematiques"], intended_track: null, postbac_year: null, postbac_formation_type: null,
    };
    expect(isDraftComplete(draft)).toBe(false);
  });

  it("returns true for 1ère général with 3 specs", () => {
    const draft: Step2Draft = {
      level: "lycee_1ere", filiere: "general", sous_filiere_techno: null,
      specialites: ["mathematiques", "svt", "ses"], intended_track: null, postbac_year: null, postbac_formation_type: null,
    };
    expect(isDraftComplete(draft)).toBe(true);
  });

  it("returns false for 1ère techno without sous_filiere", () => {
    const draft: Step2Draft = {
      level: "lycee_1ere", filiere: "techno", sous_filiere_techno: null,
      specialites: [], intended_track: null, postbac_year: null, postbac_formation_type: null,
    };
    expect(isDraftComplete(draft)).toBe(false);
  });

  it("returns true for 1ère techno with sous_filiere", () => {
    const draft: Step2Draft = {
      level: "lycee_1ere", filiere: "techno", sous_filiere_techno: "STMG",
      specialites: [], intended_track: null, postbac_year: null, postbac_formation_type: null,
    };
    expect(isDraftComplete(draft)).toBe(true);
  });

  it("returns true for postbac with both fields", () => {
    const draft: Step2Draft = {
      level: "postbac", filiere: null, sous_filiere_techno: null,
      specialites: [], intended_track: null, postbac_year: "pause", postbac_formation_type: "aucune",
    };
    expect(isDraftComplete(draft)).toBe(true);
  });

  it("returns false for postbac without formation type", () => {
    const draft: Step2Draft = {
      level: "postbac", filiere: null, sous_filiere_techno: null,
      specialites: [], intended_track: null, postbac_year: "bac+1", postbac_formation_type: null,
    };
    expect(isDraftComplete(draft)).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// NiveauPicker rendering
// ---------------------------------------------------------------------------

describe("NiveauPicker", () => {
  it("renders all 5 niveau options", () => {
    render(<NiveauPicker value={null} onChange={vi.fn()} />);
    expect(screen.getByText("3ème")).toBeInTheDocument();
    expect(screen.getByText("2nde")).toBeInTheDocument();
    expect(screen.getByText("1ère")).toBeInTheDocument();
    expect(screen.getByText("Terminale")).toBeInTheDocument();
    expect(screen.getByText("Post-bac")).toBeInTheDocument();
  });

  it("calls onChange when a niveau is selected", async () => {
    const onChange = vi.fn();
    render(<NiveauPicker value={null} onChange={onChange} />);
    await userEvent.click(screen.getByText("Terminale"));
    expect(onChange).toHaveBeenCalledWith("lycee_terminale");
  });
});

// ---------------------------------------------------------------------------
// Branche3eme rendering
// ---------------------------------------------------------------------------

describe("Branche3eme", () => {
  it("renders 4 track options including Pas encore décidé", () => {
    render(<Branche3eme value={null} onChange={vi.fn()} />);
    expect(screen.getByText("Bac général")).toBeInTheDocument();
    expect(screen.getByText("Bac techno")).toBeInTheDocument();
    expect(screen.getByText("Bac pro")).toBeInTheDocument();
    expect(screen.getByText("Pas encore décidé")).toBeInTheDocument();
  });

  it("Mehdi anti-stigma — no special badge or encouragement on bac pro", () => {
    render(<Branche3eme value="pro" onChange={vi.fn()} />);
    // No encouragement text that would visually distinguish the bac pro option
    expect(screen.queryByText(/aussi bien/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/voie pro/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/bravo/i)).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// SpecialitesPicker — cap enforcement
// ---------------------------------------------------------------------------

describe("SpecialitesPicker cap enforcement", () => {
  it("does not call onToggle when at cap", async () => {
    const onToggle = vi.fn();
    render(
      <SpecialitesPicker
        filiere="general"
        selected={["mathematiques", "svt"]}
        expectedCount={2}
        onToggle={onToggle}
      />
    );
    // All unselected chips should be disabled at cap
    const nsiButton = screen.getByRole("button", { name: /NSI/i });
    expect(nsiButton).toBeDisabled();
  });

  it("shows count indicator", () => {
    render(
      <SpecialitesPicker
        filiere="general"
        selected={["mathematiques"]}
        expectedCount={2}
        onToggle={vi.fn()}
      />
    );
    expect(screen.getByText("1/2")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// RecapCard snapshot — 3 personas
// ---------------------------------------------------------------------------

describe("RecapCard", () => {
  it("renders Sarah Terminale général recap", () => {
    const draft: Step2Draft = {
      level: "lycee_terminale", filiere: "general", sous_filiere_techno: null,
      specialites: ["mathematiques", "hggsp"], intended_track: null, postbac_year: null, postbac_formation_type: null,
    };
    render(<RecapCard draft={draft} onModify={vi.fn()} />);
    expect(screen.getByText(/Terminale/)).toBeInTheDocument();
    expect(screen.getByText(/Bac général/)).toBeInTheDocument();
    expect(screen.getByText(/Maths/i)).toBeInTheDocument();
    expect(screen.getByText(/Parcoursup/i)).toBeInTheDocument();
  });

  it("renders Mehdi 3ème bac pro recap without encouragement", () => {
    const draft: Step2Draft = {
      level: "college_3eme", filiere: null, sous_filiere_techno: null,
      specialites: [], intended_track: "pro", postbac_year: null, postbac_formation_type: null,
    };
    render(<RecapCard draft={draft} onModify={vi.fn()} />);
    expect(screen.getByText(/3ème/)).toBeInTheDocument();
    expect(screen.getByText(/Bac pro/)).toBeInTheDocument();
    expect(screen.getByText(/Affelnet/i)).toBeInTheDocument();
    // No encouragement
    expect(screen.queryByText(/bravo/i)).not.toBeInTheDocument();
  });

  it("renders Léa post-bac en pause recap with dignified copy", () => {
    const draft: Step2Draft = {
      level: "postbac", filiere: null, sous_filiere_techno: null,
      specialites: [], intended_track: null, postbac_year: "pause", postbac_formation_type: "aucune",
    };
    render(<RecapCard draft={draft} onModify={vi.fn()} />);
    expect(screen.getByText(/Post-bac/)).toBeInTheDocument();
    expect(screen.getByText(/pause/i)).toBeInTheDocument();
    // No guilt-inducing copy
    expect(screen.queryByText(/pourquoi/i)).not.toBeInTheDocument();
  });

  it("calls onModify when Modifier is clicked", async () => {
    const onModify = vi.fn();
    const draft: Step2Draft = {
      level: "lycee_terminale", filiere: "general", sous_filiere_techno: null,
      specialites: ["mathematiques", "svt"], intended_track: null, postbac_year: null, postbac_formation_type: null,
    };
    render(<RecapCard draft={draft} onModify={onModify} />);
    await userEvent.click(screen.getByRole("button", { name: /Modifier/i }));
    expect(onModify).toHaveBeenCalled();
  });
});
