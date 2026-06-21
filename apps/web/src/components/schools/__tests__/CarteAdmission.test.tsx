import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { CarteAdmission, buildAriaLabel, getLabelText, getSemanticColor } from "../CarteAdmission";
import type { AdmissionStat } from "@/lib/api/schools";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const baseStat: AdmissionStat = {
  min_proba: 20,
  expected_proba: 38,
  max_proba: 55,
  label: "audacieux",
  context_line: "Moyenne admise 2024 : 14,5",
  action_lever: "+ 2 points en maths feraient passer à 58 %",
};

function makeCarteAdmission(
  overrides: Partial<AdmissionStat> = {},
  props: {
    variant?: "large" | "medium" | "small" | "export";
    schoolName?: string;
    schoolSlug?: string;
    className?: string;
  } = {},
) {
  const stat = { ...baseStat, ...overrides };
  return render(
    <CarteAdmission
      admissionStat={stat}
      variant={props.variant ?? "medium"}
      schoolName={props.schoolName ?? "INSA Lyon"}
      schoolSlug={props.schoolSlug}
      className={props.className}
    />,
  );
}

// ---------------------------------------------------------------------------
// sessionStorage shim
// ---------------------------------------------------------------------------

const sessionStorageStore = new Map<string, string>();

beforeEach(() => {
  sessionStorageStore.clear();
  Object.defineProperty(globalThis, "sessionStorage", {
    configurable: true,
    value: {
      getItem: (key: string) => sessionStorageStore.get(key) ?? null,
      setItem: (key: string, value: string) => sessionStorageStore.set(key, value),
      removeItem: (key: string) => sessionStorageStore.delete(key),
      clear: () => sessionStorageStore.clear(),
      get length() {
        return sessionStorageStore.size;
      },
      key: (index: number) => Array.from(sessionStorageStore.keys())[index] ?? null,
    } satisfies Storage,
  });
});

afterEach(() => {
  vi.restoreAllMocks();
});

// ---------------------------------------------------------------------------
// 1. Core rendering
// ---------------------------------------------------------------------------

describe("core rendering", () => {
  it("renders expected_proba percentage", () => {
    makeCarteAdmission({ expected_proba: 38 });
    expect(screen.getByText(/38\s*%/)).toBeInTheDocument();
  });

  it("renders label text for audacieux", () => {
    makeCarteAdmission({ label: "audacieux" });
    expect(screen.getByText("pari audacieux")).toBeInTheDocument();
  });

  it("renders label text for realiste", () => {
    makeCarteAdmission({ label: "realiste" });
    expect(screen.getByText("pari réaliste")).toBeInTheDocument();
  });

  it("renders label text for sur", () => {
    makeCarteAdmission({ label: "sur" });
    expect(screen.getByText("pari sûr")).toBeInTheDocument();
  });

  it("renders label text for estimation_indicative", () => {
    makeCarteAdmission({ label: "estimation_indicative" });
    expect(screen.getByText("estimation indicative")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// 2. Aria-label (AC3)
// ---------------------------------------------------------------------------

describe("aria-label", () => {
  it("has correct aria-label including school name and label", () => {
    makeCarteAdmission(
      {
        expected_proba: 38,
        label: "audacieux",
        action_lever: "+ 2 points en maths feraient passer à 58 %",
      },
      { schoolName: "INSA Lyon" },
    );
    const region = screen.getByRole("region");
    expect(region).toHaveAttribute(
      "aria-label",
      "38 % d'admission à INSA Lyon — pari audacieux. + 2 points en maths feraient passer à 58 %.",
    );
  });

  it("aria-label omits action_lever when null", () => {
    makeCarteAdmission(
      { expected_proba: 70, label: "sur", action_lever: null },
      { schoolName: "École Polytechnique" },
    );
    const region = screen.getByRole("region");
    expect(region).toHaveAttribute(
      "aria-label",
      "70 % d'admission à École Polytechnique — pari sûr.",
    );
  });

  it("aria-label strips trailing period from action_lever to avoid double-period", () => {
    const result = buildAriaLabel(38, "INSA Lyon", "audacieux", "Améliore tes maths.");
    expect(result).toBe("38 % d'admission à INSA Lyon — pari audacieux. Améliore tes maths.");
    expect(result).not.toMatch(/\.\./);
  });
});

// ---------------------------------------------------------------------------
// 3. Variant sizing
// ---------------------------------------------------------------------------

describe("variant sizing", () => {
  it("variant large renders text-5xl class on stat", () => {
    makeCarteAdmission({}, { variant: "large" });
    const stat = screen.getByText(/38\s*%/);
    expect(stat).toHaveClass("text-5xl");
  });

  it("variant small renders text-2xl class on stat", () => {
    makeCarteAdmission({}, { variant: "small" });
    const stat = screen.getByText(/38\s*%/);
    expect(stat).toHaveClass("text-2xl");
  });

  it("variant medium renders text-3xl class on stat", () => {
    makeCarteAdmission({}, { variant: "medium" });
    const stat = screen.getByText(/38\s*%/);
    expect(stat).toHaveClass("text-3xl");
  });

  it("variant export renders text-3xl class on stat", () => {
    makeCarteAdmission({}, { variant: "export" });
    const stat = screen.getByText(/38\s*%/);
    expect(stat).toHaveClass("text-3xl");
  });

  it("variant small applies line-clamp-2 to context_line", () => {
    makeCarteAdmission({}, { variant: "small" });
    const contextP = screen.getByText("Moyenne admise 2024 : 14,5");
    expect(contextP).toHaveClass("line-clamp-2");
  });

  it("variant medium does NOT apply line-clamp-2 to context_line", () => {
    makeCarteAdmission({}, { variant: "medium" });
    const contextP = screen.getByText("Moyenne admise 2024 : 14,5");
    expect(contextP).not.toHaveClass("line-clamp-2");
  });
});

// ---------------------------------------------------------------------------
// 4. Export variant specifics (AC1)
// ---------------------------------------------------------------------------

describe("export variant", () => {
  it("variant export does not render action_lever", () => {
    makeCarteAdmission(
      { action_lever: "+ 2 points en maths feraient passer à 58 %" },
      { variant: "export" },
    );
    expect(
      screen.queryByText("+ 2 points en maths feraient passer à 58 %"),
    ).not.toBeInTheDocument();
  });

  it("variant export has data-export attribute on wrapper", () => {
    makeCarteAdmission({}, { variant: "export" });
    const region = screen.getByRole("region");
    expect(region).toHaveAttribute("data-export");
  });

  it("variant export has pointer-events-none class", () => {
    makeCarteAdmission({}, { variant: "export" });
    const region = screen.getByRole("region");
    expect(region).toHaveClass("pointer-events-none");
  });
});

// ---------------------------------------------------------------------------
// 5. Action lever
// ---------------------------------------------------------------------------

describe("action_lever", () => {
  it("action_lever rendered for non-export variant when present", () => {
    makeCarteAdmission(
      { action_lever: "+ 2 points en maths feraient passer à 58 %" },
      { variant: "medium" },
    );
    expect(screen.getByText("+ 2 points en maths feraient passer à 58 %")).toBeInTheDocument();
  });

  it("action_lever not rendered when null", () => {
    makeCarteAdmission({ action_lever: null }, { variant: "medium" });
    // No action lever text — just verify the component renders without it
    expect(screen.getByText("Moyenne admise 2024 : 14,5")).toBeInTheDocument();
    // No extra paragraph between context_line and footnote area
    const paragraphs = screen.getAllByRole("region");
    expect(paragraphs).toHaveLength(1);
  });
});

// ---------------------------------------------------------------------------
// 6. Indicative footnote (AC5)
// ---------------------------------------------------------------------------

describe("estimation_indicative footnote", () => {
  it("footnote shown for estimation_indicative", () => {
    makeCarteAdmission({ label: "estimation_indicative" });
    expect(
      screen.getByText(
        "Estimation basée sur ton profil actuel — ajoute tes bulletins pour affiner.",
      ),
    ).toBeInTheDocument();
  });

  it("footnote NOT shown for realiste", () => {
    makeCarteAdmission({ label: "realiste" });
    expect(
      screen.queryByText(
        "Estimation basée sur ton profil actuel — ajoute tes bulletins pour affiner.",
      ),
    ).not.toBeInTheDocument();
  });

  it("footnote NOT shown for audacieux", () => {
    makeCarteAdmission({ label: "audacieux" });
    expect(
      screen.queryByText(
        "Estimation basée sur ton profil actuel — ajoute tes bulletins pour affiner.",
      ),
    ).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// 7. Semantic colors (AC2)
// ---------------------------------------------------------------------------

describe("semantic colors", () => {
  it("green color class for proba > 70", () => {
    makeCarteAdmission({ expected_proba: 80 });
    const stat = screen.getByText(/80\s*%/);
    expect(stat).toHaveClass("text-green-600");
  });

  it("slate/neutral color class for proba 50-70", () => {
    makeCarteAdmission({ expected_proba: 60 });
    const stat = screen.getByText(/60\s*%/);
    expect(stat).toHaveClass("text-slate-600");
  });

  it("orange color class for proba 30-49", () => {
    makeCarteAdmission({ expected_proba: 40 });
    const stat = screen.getByText(/40\s*%/);
    expect(stat).toHaveClass("text-orange-500");
  });

  it("red color class for proba < 30", () => {
    makeCarteAdmission({ expected_proba: 25 });
    const stat = screen.getByText(/25\s*%/);
    expect(stat).toHaveClass("text-red-600");
  });
});

// ---------------------------------------------------------------------------
// 8. getSemanticColor unit tests
// ---------------------------------------------------------------------------

describe("getSemanticColor helper", () => {
  it("proba=0 returns red", () => {
    const colors = getSemanticColor(0);
    expect(colors.text).toBe("text-red-600");
    expect(colors.badge).toBe("text-red-700");
    expect(colors.bgBadge).toBe("bg-red-50");
  });

  it("proba=29 returns red", () => {
    const colors = getSemanticColor(29);
    expect(colors.text).toBe("text-red-600");
  });

  it("proba=30 returns orange", () => {
    const colors = getSemanticColor(30);
    expect(colors.text).toBe("text-orange-500");
    expect(colors.badge).toBe("text-orange-700");
    expect(colors.bgBadge).toBe("bg-orange-50");
  });

  it("proba=49 returns orange", () => {
    const colors = getSemanticColor(49);
    expect(colors.text).toBe("text-orange-500");
  });

  it("proba=50 returns slate/neutral", () => {
    const colors = getSemanticColor(50);
    expect(colors.text).toBe("text-slate-600");
    expect(colors.badge).toBe("text-slate-700");
    expect(colors.bgBadge).toBe("bg-slate-50");
  });

  it("proba=70 returns slate/neutral", () => {
    const colors = getSemanticColor(70);
    expect(colors.text).toBe("text-slate-600");
  });

  it("proba=71 returns green", () => {
    const colors = getSemanticColor(71);
    expect(colors.text).toBe("text-green-600");
    expect(colors.badge).toBe("text-green-700");
    expect(colors.bgBadge).toBe("bg-green-50");
  });

  it("proba=100 returns green", () => {
    const colors = getSemanticColor(100);
    expect(colors.text).toBe("text-green-600");
  });

  // [High] Guard against NaN/Infinity/negative
  it("proba=NaN falls back to red (0)", () => {
    const colors = getSemanticColor(NaN);
    expect(colors.text).toBe("text-red-600");
  });

  it("proba=Infinity falls back to red (0)", () => {
    const colors = getSemanticColor(Infinity);
    expect(colors.text).toBe("text-red-600");
  });

  it("proba=-Infinity falls back to red (0)", () => {
    const colors = getSemanticColor(-Infinity);
    expect(colors.text).toBe("text-red-600");
  });

  it("proba=-50 (negative) is clamped to 0, returns red", () => {
    const colors = getSemanticColor(-50);
    expect(colors.text).toBe("text-red-600");
  });

  it("proba=150 (over 100) is clamped to 100, returns green", () => {
    const colors = getSemanticColor(150);
    expect(colors.text).toBe("text-green-600");
  });
});

// ---------------------------------------------------------------------------
// 9. buildAriaLabel unit tests
// ---------------------------------------------------------------------------

describe("buildAriaLabel helper", () => {
  it("formats correctly with action_lever", () => {
    const result = buildAriaLabel(
      38,
      "INSA Lyon",
      "audacieux",
      "+ 2 points en maths feraient passer à 58 %",
    );
    expect(result).toBe(
      "38 % d'admission à INSA Lyon — pari audacieux. + 2 points en maths feraient passer à 58 %.",
    );
  });

  it("formats correctly without action_lever", () => {
    const result = buildAriaLabel(75, "Centrale Paris", "sur", null);
    expect(result).toBe("75 % d'admission à Centrale Paris — pari sûr.");
  });

  it("formats correctly for estimation_indicative", () => {
    const result = buildAriaLabel(45, "EPITA", "estimation_indicative", null);
    expect(result).toBe("45 % d'admission à EPITA — estimation indicative.");
  });

  // [Medium] double-period guard
  it("does not produce double-period when action_lever ends with period", () => {
    const result = buildAriaLabel(38, "INSA Lyon", "audacieux", "Améliore tes maths.");
    expect(result).not.toMatch(/\.\./);
    expect(result).toBe("38 % d'admission à INSA Lyon — pari audacieux. Améliore tes maths.");
  });

  it("strips trailing exclamation mark from action_lever", () => {
    const result = buildAriaLabel(38, "INSA Lyon", "audacieux", "Bonne chance!");
    expect(result).toBe("38 % d'admission à INSA Lyon — pari audacieux. Bonne chance.");
  });
});

// ---------------------------------------------------------------------------
// 10. getLabelText unit tests
// ---------------------------------------------------------------------------

describe("getLabelText helper", () => {
  it("returns pari audacieux", () => {
    expect(getLabelText("audacieux")).toBe("pari audacieux");
  });

  it("returns pari réaliste", () => {
    expect(getLabelText("realiste")).toBe("pari réaliste");
  });

  it("returns pari sûr", () => {
    expect(getLabelText("sur")).toBe("pari sûr");
  });

  it("returns estimation indicative", () => {
    expect(getLabelText("estimation_indicative")).toBe("estimation indicative");
  });
});

// ---------------------------------------------------------------------------
// 11. Update badge (AC4)
// ---------------------------------------------------------------------------

describe("update badge (AC4)", () => {
  it("badge shown when updated_at < 24h and previous_proba differs", async () => {
    const recentTime = new Date(Date.now() - 60 * 60 * 1000).toISOString(); // 1h ago
    makeCarteAdmission(
      {
        expected_proba: 38,
        previous_proba: 24,
        updated_at: recentTime,
      },
      { schoolSlug: "insa-lyon" },
    );
    // Badge renders asynchronously via useEffect
    const badge = await screen.findByText(/\+\s*14\s*pts/);
    expect(badge).toBeInTheDocument();
  });

  it("badge NOT shown when updated_at > 24h", () => {
    const oldTime = new Date(Date.now() - 25 * 60 * 60 * 1000).toISOString(); // 25h ago
    makeCarteAdmission(
      {
        expected_proba: 38,
        previous_proba: 24,
        updated_at: oldTime,
      },
      { schoolSlug: "insa-lyon" },
    );
    expect(screen.queryByText(/\+\s*14\s*pts/)).not.toBeInTheDocument();
  });

  it("badge NOT shown when previous_proba is absent", () => {
    const recentTime = new Date(Date.now() - 60 * 60 * 1000).toISOString();
    makeCarteAdmission({
      expected_proba: 38,
      updated_at: recentTime,
      // no previous_proba
    });
    expect(screen.queryByText(/pts/)).not.toBeInTheDocument();
  });

  it("badge NOT shown when already seen this session", async () => {
    const recentTime = new Date(Date.now() - 60 * 60 * 1000).toISOString();
    // Pre-set the session key to simulate "already seen"
    sessionStorageStore.set("carte_admission_badge_seen_insa-lyon", "1");

    makeCarteAdmission(
      {
        expected_proba: 38,
        previous_proba: 24,
        updated_at: recentTime,
      },
      { schoolSlug: "insa-lyon" },
    );

    // Give useEffect time to run
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(screen.queryByText(/pts/)).not.toBeInTheDocument();
  });

  it("badge shows negative delta when proba decreased", async () => {
    const recentTime = new Date(Date.now() - 30 * 60 * 1000).toISOString(); // 30m ago
    makeCarteAdmission(
      {
        expected_proba: 30,
        previous_proba: 45,
        updated_at: recentTime,
      },
      { schoolSlug: "ecp" },
    );
    const badge = await screen.findByText(/-15\s*pts/);
    expect(badge).toBeInTheDocument();
  });

  // [Medium] delta === 0 should NOT show badge
  it("badge NOT shown when delta is 0 (proba unchanged)", async () => {
    const recentTime = new Date(Date.now() - 60 * 60 * 1000).toISOString();
    makeCarteAdmission(
      {
        expected_proba: 38,
        previous_proba: 38, // same value → delta = 0
        updated_at: recentTime,
      },
      { schoolSlug: "insa-lyon" },
    );
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(screen.queryByText(/pts/)).not.toBeInTheDocument();
  });

  // [High] Invalid updatedAt date should not crash and badge should not appear
  it("badge NOT shown when updated_at is an invalid date string", async () => {
    makeCarteAdmission(
      {
        expected_proba: 38,
        previous_proba: 24,
        updated_at: "not-a-valid-date",
      },
      { schoolSlug: "insa-lyon" },
    );
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(screen.queryByText(/pts/)).not.toBeInTheDocument();
  });

  // [High] schoolName fallback when schoolSlug is absent
  it("uses schoolName as sessionStorage fallback when schoolSlug absent", async () => {
    const recentTime = new Date(Date.now() - 60 * 60 * 1000).toISOString();
    makeCarteAdmission(
      {
        expected_proba: 38,
        previous_proba: 24,
        updated_at: recentTime,
      },
      // No schoolSlug — should fall back to schoolName "INSA Lyon"
    );
    const badge = await screen.findByText(/\+\s*14\s*pts/);
    expect(badge).toBeInTheDocument();
    // Key should use schoolName, not 'unknown'
    expect(sessionStorageStore.has("carte_admission_badge_seen_INSA Lyon")).toBe(true);
    expect(sessionStorageStore.has("carte_admission_badge_seen_unknown")).toBe(false);
  });

  // [Low] Float delta should be rounded
  it("renders rounded integer delta for float probabilities", async () => {
    const recentTime = new Date(Date.now() - 60 * 60 * 1000).toISOString();
    makeCarteAdmission(
      {
        expected_proba: 38,
        previous_proba: 23.4, // delta = 14.6 → rounds to 15
        updated_at: recentTime,
      },
      { schoolSlug: "insa-lyon" },
    );
    const badge = await screen.findByText(/\+\s*15\s*pts/);
    expect(badge).toBeInTheDocument();
  });
});
