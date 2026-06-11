import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import type { OnboardingInterets } from "@/lib/api/onboarding";
import { MAX_INTERET_CHARS } from "@/lib/onboarding/referentials";

import { InteretsFreeForm } from "./interets-free-form";

const empty: OnboardingInterets = { "1": null, "2": null, "3": null };

describe("InteretsFreeForm", () => {
  it("renders 3 labeled textareas + 3 suggestion lists", () => {
    render(<InteretsFreeForm value={empty} onChange={vi.fn()} />);
    expect(screen.getAllByRole("textbox")).toHaveLength(3);
    // Query by exact textarea id so we don't collide with placeholder text
    // (which happens to repeat the label phrasing).
    expect(document.getElementById("interet-1")).not.toBeNull();
    expect(document.getElementById("interet-2")).not.toBeNull();
    expect(document.getElementById("interet-3")).not.toBeNull();
  });

  it("typing in a field emits the full triplet with null → string", () => {
    const onChange = vi.fn();
    render(<InteretsFreeForm value={empty} onChange={onChange} />);
    fireEvent.change(document.getElementById("interet-1")!, {
      target: { value: "Choses à savoir" },
    });
    expect(onChange).toHaveBeenCalledWith({ "1": "Choses à savoir", "2": null, "3": null });
  });

  it("clearing a field down to empty string returns null in the triplet", () => {
    const onChange = vi.fn();
    render(
      <InteretsFreeForm
        value={{ "1": "podcast", "2": null, "3": null }}
        onChange={onChange}
      />,
    );
    fireEvent.change(document.getElementById("interet-1")!, { target: { value: "" } });
    expect(onChange).toHaveBeenCalledWith({ "1": null, "2": null, "3": null });
  });

  it("clicking a suggestion REPLACES the current text (Pass 1 M5)", () => {
    // Pass 1 review M5 — spec AC4 says "au tap → texte du chip injecté dans
    // le champ correspondant (focus reste sur le champ après injection)".
    // The previous behavior appended with " · " separator; fixed to replace.
    const onChange = vi.fn();
    render(
      <InteretsFreeForm
        value={{ "1": "Choses à savoir", "2": null, "3": null }}
        onChange={onChange}
      />,
    );
    const youtubeButton = screen.getAllByRole("button").find((b) => b.textContent === "+ YouTube");
    expect(youtubeButton).toBeDefined();
    fireEvent.click(youtubeButton!);
    // INJECT, not APPEND — and the prior content "Choses à savoir" is replaced.
    expect(onChange).toHaveBeenCalledWith({
      "1": "YouTube",
      "2": null,
      "3": null,
    });
  });

  it("suggestion tap on empty field replaces with raw suggestion (no leading separator)", () => {
    const onChange = vi.fn();
    render(<InteretsFreeForm value={empty} onChange={onChange} />);
    const youtubeButton = screen.getAllByRole("button").find((b) => b.textContent === "+ YouTube");
    fireEvent.click(youtubeButton!);
    expect(onChange).toHaveBeenCalledWith({ "1": "YouTube", "2": null, "3": null });
  });

  it("character counter colors turn warning then danger as it approaches the max", () => {
    const justBelowDanger = "a".repeat(Math.floor(MAX_INTERET_CHARS * 0.92));
    const { rerender } = render(
      <InteretsFreeForm
        value={{ "1": justBelowDanger, "2": null, "3": null }}
        onChange={vi.fn()}
      />,
    );
    const counter1 = screen.getByTestId("interet-1-counter");
    expect(counter1.className).toContain("text-warning");

    rerender(
      <InteretsFreeForm
        value={{ "1": "a".repeat(MAX_INTERET_CHARS), "2": null, "3": null }}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByTestId("interet-1-counter").className).toContain("text-danger");
  });

  it("uses placeholdersOverride when provided (AC8 — per niveau scolaire)", () => {
    render(
      <InteretsFreeForm
        value={empty}
        onChange={vi.fn()}
        placeholdersOverride={["A", "B", "C"]}
      />,
    );
    expect(screen.getByPlaceholderText("A")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("B")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("C")).toBeInTheDocument();
  });
});
