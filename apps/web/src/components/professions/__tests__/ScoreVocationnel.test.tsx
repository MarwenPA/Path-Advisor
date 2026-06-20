import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

import { ScoreVocationnel, ScoreVocationnelComparison } from "../ScoreVocationnel";
import type { Signal } from "../types";

const signals: Signal[] = [
  { id: "svt", label: "SVT" },
  { id: "aider", label: "aider les autres" },
  { id: "hopital", label: "hôpital" },
  { id: "equipe", label: "travail d'équipe" },
  { id: "precision", label: "précision" },
];

const baseProps = {
  metierId: "infirmier-bloc",
  metiersName: "Infirmier·ère de bloc opératoire",
  score: 78,
  phraseRecopiable: "Mon projet est de travailler en salle d'op car j'aime la précision.",
  signals,
  variant: "compact" as const,
};

// ---------------------------------------------------------------------------
// Global mock state — saved/restored so mutations never leak across tests
// ---------------------------------------------------------------------------

const originalClipboard = Object.getOwnPropertyDescriptor(navigator, "clipboard");
const originalExecCommand = (document as unknown as { execCommand?: unknown }).execCommand;
const originalMatchMedia = window.matchMedia;

afterEach(() => {
  // Restore navigator.clipboard
  if (originalClipboard) {
    Object.defineProperty(navigator, "clipboard", originalClipboard);
  } else {
    delete (navigator as unknown as { clipboard?: unknown }).clipboard;
  }
  // Restore document.execCommand
  if (originalExecCommand === undefined) {
    delete (document as unknown as { execCommand?: unknown }).execCommand;
  } else {
    (document as unknown as { execCommand?: unknown }).execCommand = originalExecCommand;
  }
  // Restore matchMedia
  window.matchMedia = originalMatchMedia;
  vi.restoreAllMocks();
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function setup(
  props: Partial<Omit<typeof baseProps, "variant">> & {
    variant?: "compact" | "expanded" | "comparison";
    confidenceLevel?: "normal" | "indicative";
    onSignalClick?: (id: string) => void;
    onExplainClick?: () => void;
  } = {},
) {
  return render(<ScoreVocationnel {...baseProps} {...props} />);
}

/** The phrase paragraph (the visible italic <p>, not the tooltip bubble copy). */
function getPhraseParagraph(): HTMLElement {
  // The <p> carries the aria-label "Phrase défendable pour …".
  return screen.getByText(
    (_, el) => el?.tagName === "P" && /Mon projet/.test(el.textContent ?? ""),
  );
}

// ---------------------------------------------------------------------------
// AC1 — rendu de base
// ---------------------------------------------------------------------------

describe("AC1 — rendu de base", () => {
  it("affiche le nom du métier dans un h3", () => {
    setup();
    expect(screen.getByRole("heading", { level: 3, name: /infirmier/i })).toBeInTheDocument();
  });

  it("affiche le chip score avec aria-label correct", () => {
    setup({ score: 78 });
    expect(
      screen.getByRole("generic", { name: /compatible à 78 % avec ce métier/i }),
    ).toBeInTheDocument();
  });

  it("affiche le bouton Copier", () => {
    setup();
    expect(
      screen.getByRole("button", { name: /copier la phrase défendable/i }),
    ).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// AC1 — chip score couleur sémantique (décision 3a : fond teinté conservé)
// ---------------------------------------------------------------------------

describe("AC1 — couleurs sémantiques du chip score", () => {
  it("score ≥70 → classe bg-success/10 text-success", () => {
    setup({ score: 70 });
    const chip = screen.getByRole("generic", { name: /compatible à 70 %/i });
    expect(chip.className).toMatch(/text-success/);
    expect(chip.className).toMatch(/bg-success\/10/);
  });

  it("score 40–69 → classe text-warning", () => {
    setup({ score: 55 });
    const chip = screen.getByRole("generic", { name: /compatible à 55 %/i });
    expect(chip.className).toMatch(/text-warning/);
  });

  it("score <40 → classe text-muted-foreground", () => {
    setup({ score: 30 });
    const chip = screen.getByRole("generic", { name: /compatible à 30 %/i });
    expect(chip.className).toMatch(/text-muted-foreground/);
  });
});

// ---------------------------------------------------------------------------
// AC1 — garde sur score hors plage / NaN / non-entier
// ---------------------------------------------------------------------------

describe("AC1 — garde sur le score", () => {
  it("clamp les valeurs > 100 à 100", () => {
    setup({ score: 150 });
    expect(
      screen.getByRole("generic", { name: /compatible à 100 % avec ce métier/i }),
    ).toBeInTheDocument();
  });

  it("clamp les valeurs négatives à 0", () => {
    setup({ score: -5 });
    expect(
      screen.getByRole("generic", { name: /compatible à 0 % avec ce métier/i }),
    ).toBeInTheDocument();
  });

  it("arrondit les valeurs non-entières", () => {
    setup({ score: 78.6 });
    expect(
      screen.getByRole("generic", { name: /compatible à 79 % avec ce métier/i }),
    ).toBeInTheDocument();
  });

  it("traite NaN comme 0 (pas de 'NaN / 100')", () => {
    setup({ score: NaN });
    const chip = screen.getByRole("generic", { name: /compatible à 0 %/i });
    expect(chip.textContent).not.toMatch(/NaN/);
  });
});

// ---------------------------------------------------------------------------
// AC2 — variant compact
// ---------------------------------------------------------------------------

describe("AC2 — variant compact", () => {
  it("la card a max-w-[360px] et max-h-40", () => {
    const { container } = setup({ variant: "compact" });
    const article = container.querySelector("article");
    expect(article?.className).toMatch(/max-w-\[360px\]/);
    expect(article?.className).toMatch(/max-h-40/);
  });

  it("la phrase recopiable a line-clamp-1", () => {
    setup({ variant: "compact" });
    expect(getPhraseParagraph().className).toMatch(/line-clamp-1/);
  });

  it("la phrase tronquée a un tooltip avec le texte complet", () => {
    setup({ variant: "compact" });
    const tooltip = screen.getByRole("tooltip");
    expect(tooltip).toHaveTextContent(/Mon projet est de travailler en salle d'op/);
  });

  it("affiche au plus 2 chips signal + chip +N", () => {
    setup({ variant: "compact" });
    expect(screen.getByText("SVT")).toBeInTheDocument();
    expect(screen.getByText("aider les autres")).toBeInTheDocument();
    expect(screen.getByText("+3 autres")).toBeInTheDocument();
  });

  it("le bouton Copier est visible en compact", () => {
    setup({ variant: "compact" });
    expect(screen.getByRole("button", { name: /copier la phrase/i })).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// AC3 — variant expanded
// ---------------------------------------------------------------------------

describe("AC3 — variant expanded", () => {
  it("affiche la phrase complète sans troncature", () => {
    setup({ variant: "expanded" });
    expect(getPhraseParagraph().className).not.toMatch(/line-clamp/);
  });

  it("affiche tous les chips signal (jusqu'à 8)", () => {
    setup({ variant: "expanded" });
    expect(screen.getByText("SVT")).toBeInTheDocument();
    expect(screen.getByText("précision")).toBeInTheDocument();
    expect(screen.queryByText(/\+\d+ autres/)).toBeNull();
  });

  it("affiche le lien 'Pourquoi ce score ?' et appelle onExplainClick", () => {
    const onExplainClick = vi.fn();
    setup({ variant: "expanded", onExplainClick });
    const btn = screen.getByRole("button", { name: /pourquoi ce score/i });
    fireEvent.click(btn);
    expect(onExplainClick).toHaveBeenCalledOnce();
  });

  it("affiche le lien 'Pourquoi ce score ?' même sans onExplainClick (AC3)", () => {
    setup({ variant: "expanded" });
    const btn = screen.getByRole("button", { name: /pourquoi ce score/i });
    expect(btn).toBeInTheDocument();
    // Ne doit pas lever au clic même sans callback.
    fireEvent.click(btn);
  });

  it("onSignalClick appelé au clic d'un chip signal", () => {
    const onSignalClick = vi.fn();
    setup({ variant: "expanded", onSignalClick });
    fireEvent.click(screen.getByRole("button", { name: /signal contributif : SVT/i }));
    expect(onSignalClick).toHaveBeenCalledWith("svt");
  });
});

// ---------------------------------------------------------------------------
// AC4 — variant comparison (décision 1b : layout porté par le composant)
// ---------------------------------------------------------------------------

describe("AC4 — variant comparison", () => {
  it("le chip score est agrandi (text-body) en comparison", () => {
    setup({ variant: "comparison" });
    const chip = screen.getByRole("generic", { name: /compatible à 78 %/i });
    expect(chip.className).toMatch(/text-body(?!-sm)/);
    expect(chip.className).not.toMatch(/text-body-sm/);
  });

  it("la card comparison occupe toute la hauteur (h-full)", () => {
    const { container } = setup({ variant: "comparison" });
    expect(container.querySelector("article")?.className).toMatch(/h-full/);
  });

  it("ScoreVocationnelComparison rend 2 cartes en snap-scroll + grid lg", () => {
    const { variant: _variant, ...itemBase } = baseProps;
    const { container } = render(
      <ScoreVocationnelComparison
        items={[
          { ...itemBase, metierId: "a" },
          { ...itemBase, metierId: "b", metiersName: "Autre métier" },
        ]}
      />,
    );
    const wrapper = screen.getByRole("group", { name: /comparaison de deux métiers/i });
    expect(wrapper.className).toMatch(/snap-x/);
    expect(wrapper.className).toMatch(/lg:grid-cols-2/);
    expect(wrapper.className).toMatch(/lg:items-stretch/);
    expect(container.querySelectorAll("article")).toHaveLength(2);
  });
});

// ---------------------------------------------------------------------------
// AC5 — tap-to-copy
// ---------------------------------------------------------------------------

describe("AC5 — tap-to-copy", () => {
  it("appelle navigator.clipboard.writeText et affiche le toast", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });

    setup({ variant: "expanded" });
    fireEvent.click(screen.getByRole("button", { name: /copier la phrase/i }));

    await waitFor(() => {
      expect(writeText).toHaveBeenCalledWith(baseProps.phraseRecopiable);
    });

    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent(/Phrase copiée/);
    });
  });

  it("tombe sur le fallback execCommand quand writeText est rejeté", async () => {
    const writeText = vi.fn().mockRejectedValue(new Error("denied"));
    Object.assign(navigator, { clipboard: { writeText } });
    const execCommand = vi.fn().mockReturnValue(true);
    Object.assign(document, { execCommand });

    setup({ variant: "expanded" });
    fireEvent.click(screen.getByRole("button", { name: /copier la phrase/i }));

    await waitFor(() => {
      expect(execCommand).toHaveBeenCalledWith("copy");
    });
    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent(/Phrase copiée/);
    });
  });

  it("affiche le message d'erreur si clipboard et fallback échouent", async () => {
    Object.assign(navigator, {
      clipboard: { writeText: vi.fn().mockRejectedValue(new Error("denied")) },
    });
    Object.assign(document, { execCommand: vi.fn().mockReturnValue(false) });

    setup({ variant: "expanded" });
    fireEvent.click(screen.getByRole("button", { name: /copier la phrase/i }));

    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent(/Ctrl\+C/);
    });
  });
});

// ---------------------------------------------------------------------------
// AC1 — phrase vide
// ---------------------------------------------------------------------------

describe("AC1 — phrase recopiable vide", () => {
  it("affiche un placeholder et désactive le bouton Copier", () => {
    setup({ phraseRecopiable: "   ", variant: "expanded" });
    expect(screen.getByText(/Phrase à venir/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /copier la phrase/i })).toBeDisabled();
  });
});

// ---------------------------------------------------------------------------
// AC6 — accessibilité
// ---------------------------------------------------------------------------

describe("AC6 — accessibilité", () => {
  it("aria-label score = 'Compatible à 78 % avec ce métier'", () => {
    setup({ score: 78 });
    expect(
      screen.getByRole("generic", { name: "Compatible à 78 % avec ce métier" }),
    ).toBeInTheDocument();
  });

  it("la phrase a aria-label avec nom métier", () => {
    setup();
    expect(getPhraseParagraph()).toHaveAttribute(
      "aria-label",
      expect.stringContaining("Infirmier·ère de bloc opératoire"),
    );
  });

  it("les chips signaux ont role=button et aria-label", () => {
    setup({ variant: "expanded" });
    expect(
      screen.getByRole("button", { name: "Signal contributif : SVT" }),
    ).toBeInTheDocument();
  });

  it("le bouton copier n'a pas de role=button redondant (ARIA-in-HTML)", () => {
    setup();
    const btn = screen.getByRole("button", { name: /copier la phrase/i });
    expect(btn.tagName).toBe("BUTTON");
    expect(btn).not.toHaveAttribute("role");
  });

  it("navigation clavier : header → bouton copier → chips → lien explain (AC8)", () => {
    setup({ variant: "expanded", onExplainClick: vi.fn() });

    const copyBtn = screen.getByRole("button", { name: /copier la phrase/i });
    const firstSignal = screen.getByRole("button", { name: /signal contributif : SVT/i });
    const explainLink = screen.getByRole("button", { name: /pourquoi ce score/i });

    // Tous focusables (élément <button> natif), aucun trap, ordre DOM = ordre Tab.
    for (const el of [copyBtn, firstSignal, explainLink]) {
      el.focus();
      expect(el).toHaveFocus();
      expect(el.tabIndex).toBeGreaterThanOrEqual(0);
    }

    // L'ordre DOM (= ordre de tabulation natif) respecte copier → chip → explain.
    expect(
      copyBtn.compareDocumentPosition(firstSignal) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(
      firstSignal.compareDocumentPosition(explainLink) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// AC7 — confidenceLevel="indicative"
// ---------------------------------------------------------------------------

describe("AC7 — confidenceLevel", () => {
  it("affiche le label 'indicatif' si confidenceLevel=indicative", () => {
    setup({ confidenceLevel: "indicative" });
    expect(screen.getByText("indicatif")).toBeInTheDocument();
  });

  it("n'affiche pas le label si confidenceLevel=normal", () => {
    setup({ confidenceLevel: "normal" });
    expect(screen.queryByText("indicatif")).toBeNull();
  });

  it("n'affiche pas le label si confidenceLevel est absent", () => {
    setup();
    expect(screen.queryByText("indicatif")).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// AC8 — reduced motion
// ---------------------------------------------------------------------------

describe("AC8 — reduced motion", () => {
  function mockReducedMotion(active: boolean) {
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: active && query === "(prefers-reduced-motion: reduce)",
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })) as unknown as typeof window.matchMedia;
  }

  it("n'ajoute pas de classe transition sur le chip score si reduced motion", () => {
    mockReducedMotion(true);
    setup({ score: 78 });
    const chip = screen.getByRole("generic", { name: /compatible à 78 %/i });
    expect(chip.className).not.toMatch(/transition-colors/);
  });

  it("ajoute la transition sur le chip score si motion autorisé", () => {
    mockReducedMotion(false);
    setup({ score: 78 });
    const chip = screen.getByRole("generic", { name: /compatible à 78 %/i });
    expect(chip.className).toMatch(/transition-colors/);
  });
});
