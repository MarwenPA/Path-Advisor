import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { FicheMetier } from "../FicheMetier";
import type { Profession } from "../types";

// Wrap renders with QueryClientProvider for ReportErrorButton (Story 3.8)
function withQueryClient(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{ui}</QueryClientProvider>;
}

// ─── Mock data ────────────────────────────────────────────────────────────────

const profession: Profession = {
  id: "abc-123",
  slug: "infirmier-de-bloc-operatoire",
  name: "Infirmier·ère de bloc opératoire",
  description:
    "L'infirmier de bloc opératoire est un professionnel de santé spécialisé qui assiste les chirurgiens.",
  daily_routine:
    "Tu commences ta matinée en vérifiant le matériel stérile. Tu assistes ensuite le chirurgien pendant les interventions.",
  requirements_json: [
    { type: "studies", label: "BTS IBODE" },
    { type: "skill", label: "Gestion du stress en urgence" },
    { type: "quality", label: "Précision et rigueur" },
  ],
  prospects_text: "Tu peux évoluer vers infirmier coordinateur ou cadre de santé.",
  median_salary_eur: 34000,
  salary_range_json: { min: 28000, max: 50000, source: "Onisep 2025" },
  signals_json: {
    passions: ["SVT", "biologie", "soins"],
    valeurs: ["utilité sociale", "contact humain"],
    specialites: ["SVT", "chimie"],
  },
  level_compatibility: ["lycee_1ere_tle_general", "postbac"],
  sector: "Santé",
};

// ─── matchMedia helpers ───────────────────────────────────────────────────────

function mockMatchMedia(matches: boolean) {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: query === "(min-width: 1024px)" ? matches : false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
}

function mockReducedMotion(active: boolean) {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: query === "(prefers-reduced-motion: reduce)" ? active : false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
}

// ─── Setup ────────────────────────────────────────────────────────────────────

beforeEach(() => {
  // Default: mobile viewport
  mockMatchMedia(false);

  // D2: IntersectionObserver mock (jsdom doesn't implement it)
  // Use a class so vi.restoreAllMocks() doesn't clear the implementation
  class MockIO {
    observe = vi.fn();
    unobserve = vi.fn();
    disconnect = vi.fn();
     
    constructor(..._: unknown[]) {}
  }
  vi.stubGlobal("IntersectionObserver", MockIO);

  // scrollIntoView mock
  Element.prototype.scrollIntoView = vi.fn();
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

// ─── AC8 — Render de base ─────────────────────────────────────────────────────

describe("AC8 — render de base", () => {
  it("affiche les 6 sections sur mobile (Hero, C'est quoi, 3 accordéons, Signaux)", () => {
    render(withQueryClient(<FicheMetier profession={profession} />));

    expect(
      screen.getByRole("heading", { level: 1, name: /Infirmier·ère de bloc opératoire/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2, name: /C'est quoi/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Pour qui/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Comment y aller/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Infos pratiques/i })).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 2, name: /Signaux contributifs/i }),
    ).toBeInTheDocument();
  });

  it("le h1 contient le nom du métier", () => {
    render(withQueryClient(<FicheMetier profession={profession} />));
    const h1 = screen.getByRole("heading", { level: 1 });
    expect(h1).toHaveTextContent("Infirmier·ère de bloc opératoire");
  });
});

// ─── AC8 — Mobile : accordéons collapsés par défaut ──────────────────────────

describe("AC8 — mobile : sections 3-5 en accordéon, collapsées par défaut", () => {
  it("les sections accordéon ont aria-expanded=false par défaut", () => {
    render(withQueryClient(<FicheMetier profession={profession} />));

    expect(screen.getByRole("button", { name: /Pour qui/i })).toHaveAttribute(
      "aria-expanded",
      "false",
    );
    expect(screen.getByRole("button", { name: /Comment y aller/i })).toHaveAttribute(
      "aria-expanded",
      "false",
    );
    expect(screen.getByRole("button", { name: /Infos pratiques/i })).toHaveAttribute(
      "aria-expanded",
      "false",
    );
  });

  // P4: panel always in DOM with hidden attr → toBeVisible() instead of toBeInTheDocument()
  it("le contenu des sections accordéon est masqué par défaut", () => {
    render(withQueryClient(<FicheMetier profession={profession} />));

    // "BTS IBODE" is in the DOM (hidden attr) — must not be visible
    expect(screen.getByText("BTS IBODE")).not.toBeVisible();
    expect(screen.getByText(/évoluer vers infirmier coordinateur/i)).not.toBeVisible();
  });

  it("Hero et 'C'est quoi' sont toujours visibles", () => {
    render(withQueryClient(<FicheMetier profession={profession} />));

    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
    expect(screen.getByText(/professionnel de santé spécialisé/i)).toBeInTheDocument();
  });
});

// ─── AC8 — Accordéon : tap → expand ──────────────────────────────────────────

describe("AC8 — accordéon : tap sur section 3 → expand, aria-expanded=true", () => {
  it("clic sur 'Pour qui' → aria-expanded=true et contenu visible", () => {
    render(withQueryClient(<FicheMetier profession={profession} />));

    const btn = screen.getByRole("button", { name: /Pour qui/i });
    fireEvent.click(btn);

    expect(btn).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByText("BTS IBODE")).toBeVisible();
  });

  it("'Tout afficher' déploie les 3 accordéons", () => {
    render(withQueryClient(<FicheMetier profession={profession} />));

    fireEvent.click(screen.getByRole("button", { name: /Tout afficher/i }));

    expect(screen.getByRole("button", { name: /Pour qui/i })).toHaveAttribute(
      "aria-expanded",
      "true",
    );
    expect(screen.getByRole("button", { name: /Comment y aller/i })).toHaveAttribute(
      "aria-expanded",
      "true",
    );
    expect(screen.getByRole("button", { name: /Infos pratiques/i })).toHaveAttribute(
      "aria-expanded",
      "true",
    );
  });
});

// ─── AC8 — Desktop : TOC + scrollable sections (D2) ──────────────────────────

describe("AC8 — desktop : TOC présente, toutes sections visibles (scrollable)", () => {
  beforeEach(() => {
    mockMatchMedia(true); // viewport ≥ 1024 px
  });

  it("affiche la nav TOC avec aria-label", () => {
    render(withQueryClient(<FicheMetier profession={profession} />));
    expect(screen.getByRole("navigation", { name: /sections de la fiche/i })).toBeInTheDocument();
  });

  it("pas de tablist en desktop (D2 — scrollable sections, pas de tabs)", () => {
    render(withQueryClient(<FicheMetier profession={profession} />));
    expect(screen.queryByRole("tablist")).not.toBeInTheDocument();
  });

  it("les 5 sections sont toutes visibles en desktop", () => {
    render(withQueryClient(<FicheMetier profession={profession} />));
    // Toutes sections rendues sans accordéon ni tabs
    expect(screen.getByText(/professionnel de santé spécialisé/i)).toBeInTheDocument();
    expect(screen.getByText("BTS IBODE")).toBeInTheDocument();
    expect(screen.getByText(/évoluer vers infirmier coordinateur/i)).toBeInTheDocument();
    expect(screen.getByText(/34 000/)).toBeInTheDocument();
  });

  it("clic sur TOC link appelle scrollIntoView", () => {
    render(withQueryClient(<FicheMetier profession={profession} />));
    const links = screen.getAllByRole("link");
    const pourQuiLink = links.find((l) => /pour qui/i.test(l.textContent ?? ""));
    expect(pourQuiLink).toBeTruthy();
    fireEvent.click(pourQuiLink!);
    expect(Element.prototype.scrollIntoView).toHaveBeenCalled();
  });
});

// ─── D3 — variant="mobile" force mobile layout ───────────────────────────────

describe("D3 — variant='mobile' force le layout mobile même sur desktop", () => {
  it("variant='mobile' sur desktop → affiche accordéons (pas de TOC)", () => {
    mockMatchMedia(true); // viewport ≥ 1024 px
    render(withQueryClient(<FicheMetier profession={profession} variant="mobile" />));

    // Mobile layout: accordion buttons présents
    expect(screen.getByRole("button", { name: /Pour qui/i })).toBeInTheDocument();
    // Pas de TOC
    expect(screen.queryByRole("navigation")).not.toBeInTheDocument();
  });
});

// ─── AC8 — Score fourni → chip score présent ─────────────────────────────────

describe("AC8 — score fourni vs absent", () => {
  it("score fourni → chip score présent (aria-label score)", () => {
    render(
      withQueryClient(
        <FicheMetier
          profession={profession}
          score={78}
          phraseRecopiable="Mon projet est de travailler en salle d'op."
        />,
      ),
    );
    expect(screen.getByRole("generic", { name: /compatible à 78 %/i })).toBeInTheDocument();
  });

  it("score absent → chip score absent", () => {
    render(withQueryClient(<FicheMetier profession={profession} />));
    expect(screen.queryByRole("generic", { name: /compatible/i })).not.toBeInTheDocument();
  });
});

// ─── AC8 — Variant print ─────────────────────────────────────────────────────

describe("AC8 — variant print", () => {
  it("pas d'accordéons en mode print", () => {
    render(withQueryClient(<FicheMetier profession={profession} variant="print" />));
    expect(screen.queryByRole("button", { name: /Pour qui/i })).not.toBeInTheDocument();
  });

  it("pas de tablist en mode print", () => {
    render(withQueryClient(<FicheMetier profession={profession} variant="print" />));
    expect(screen.queryByRole("tablist")).not.toBeInTheDocument();
  });

  it("pas de TOC en mode print", () => {
    render(withQueryClient(<FicheMetier profession={profession} variant="print" />));
    expect(screen.queryByRole("navigation")).not.toBeInTheDocument();
  });

  it("toutes les sections sont linéarisées en print", () => {
    render(withQueryClient(<FicheMetier profession={profession} variant="print" />));

    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
    const headings = screen.getAllByRole("heading", { level: 2 });
    expect(headings.length).toBeGreaterThanOrEqual(5);
  });

  // P5: print + score → pas de CopyButton (ScoreVocationnel non rendu)
  it("print + score → affichage statique, pas de CopyButton", () => {
    render(
      withQueryClient(
        <FicheMetier
          profession={profession}
          score={82}
          phraseRecopiable="Mon projet est de devenir infirmier."
          variant="print"
        />,
      ),
    );

    // Score statique visible
    expect(screen.getByText(/Score : 82\/100/)).toBeInTheDocument();
    // Phrase recopiable visible
    expect(screen.getByText(/Mon projet est de devenir infirmier/)).toBeInTheDocument();
    // Pas de CopyButton (ScoreVocationnel non rendu en print)
    expect(screen.queryByRole("button", { name: /copier/i })).not.toBeInTheDocument();
  });
});

// ─── AC8 — onSignalClick ─────────────────────────────────────────────────────

describe("AC8 — onSignalClick", () => {
  // D1: signalId inclut le préfixe catégorie → "passions-biologie"
  it("chip signal déclenche onSignalClick avec id préfixé par catégorie", () => {
    const onSignalClick = vi.fn();
    render(withQueryClient(<FicheMetier profession={profession} onSignalClick={onSignalClick} />));

    // "biologie" uniquement dans Passions → id = "passions-biologie"
    const chip = screen.getByRole("button", { name: /Signal contributif : biologie/i });
    fireEvent.click(chip);

    expect(onSignalClick).toHaveBeenCalledOnce();
    expect(onSignalClick).toHaveBeenCalledWith(expect.stringContaining("passions-biologie"));
  });

  it("sans onSignalClick, les chips sont en lecture seule (span, pas button)", () => {
    render(withQueryClient(<FicheMetier profession={profession} />));

    const signalButtons = screen
      .queryAllByRole("button")
      .filter((btn) => /signal contributif/i.test(btn.getAttribute("aria-label") ?? ""));

    expect(signalButtons).toHaveLength(0);
  });
});

// ─── AC8 — Hiérarchie heading ─────────────────────────────────────────────────

describe("AC8 — hiérarchie heading", () => {
  it("exactement 1 h1 sur mobile", () => {
    render(withQueryClient(<FicheMetier profession={profession} />));
    const h1s = screen.getAllByRole("heading", { level: 1 });
    expect(h1s).toHaveLength(1);
  });

  it("h2 pour chaque section visible sur mobile (C'est quoi + 3 accordéons + Signaux = 5 h2)", () => {
    render(withQueryClient(<FicheMetier profession={profession} />));
    const h2s = screen.getAllByRole("heading", { level: 2 });
    expect(h2s.length).toBeGreaterThanOrEqual(5);
  });

  it("exactement 1 h1 sur desktop", () => {
    mockMatchMedia(true);
    render(withQueryClient(<FicheMetier profession={profession} />));
    const h1s = screen.getAllByRole("heading", { level: 1 });
    expect(h1s).toHaveLength(1);
  });
});

// ─── AC8 — Reduced motion ─────────────────────────────────────────────────────

describe("AC8 — reduced motion", () => {
  it("pas de classe transition-* sur les chevrons accordéon si prefers-reduced-motion", () => {
    mockReducedMotion(true);
    render(withQueryClient(<FicheMetier profession={profession} />));

    const btn = screen.getByRole("button", { name: /Pour qui/i });
    const chevron = btn.querySelector("svg");

    expect(chevron?.getAttribute("class") ?? "").not.toMatch(/transition-/);
  });
});

// ─── FicheMetierTOC ───────────────────────────────────────────────────────────

describe("FicheMetierTOC — TOC autonome", () => {
  it("TOC a aria-label='Sections de la fiche'", () => {
    mockMatchMedia(true);
    render(withQueryClient(<FicheMetier profession={profession} />));
    const nav = screen.getByRole("navigation", { name: /sections de la fiche/i });
    expect(nav).toBeInTheDocument();
  });

  it("TOC contient des liens <a> vers chaque section", () => {
    mockMatchMedia(true);
    render(withQueryClient(<FicheMetier profession={profession} />));
    const links = screen.getAllByRole("link");
    expect(links.length).toBeGreaterThanOrEqual(5);
    expect(links[0]).toHaveAttribute("href", expect.stringContaining("#section-"));
  });
});
