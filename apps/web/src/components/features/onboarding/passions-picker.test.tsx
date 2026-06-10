import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { PASSIONS_CATEGORIES } from "@/lib/onboarding/referentials";

import { PassionsPicker } from "./passions-picker";

describe("PassionsPicker", () => {
  it("renders all 20 referential chips on first paint", () => {
    render(<PassionsPicker selected={[]} onChange={vi.fn()} searchDebounceMs={0} />);
    const chips = screen.getAllByRole("checkbox");
    expect(chips).toHaveLength(PASSIONS_CATEGORIES.length);
  });

  it("toggles a chip and emits the new full selection", () => {
    const onChange = vi.fn();
    render(<PassionsPicker selected={[]} onChange={onChange} searchDebounceMs={0} />);
    fireEvent.click(screen.getByRole("checkbox", { name: /musique/i }));
    expect(onChange).toHaveBeenCalledWith(["musique"]);
  });

  it("filters chips on search input (debounce 0 in tests)", () => {
    render(<PassionsPicker selected={[]} onChange={vi.fn()} searchDebounceMs={0} />);
    fireEvent.change(screen.getByTestId("passions-search"), { target: { value: "cinéma" } });
    const visible = screen.getAllByRole("checkbox");
    expect(visible.length).toBeLessThan(PASSIONS_CATEGORIES.length);
    expect(screen.getByRole("checkbox", { name: /cinéma & séries/i })).toBeInTheDocument();
  });

  it("alias search matches a chip (e.g. 'code' → Tech & code)", () => {
    render(<PassionsPicker selected={[]} onChange={vi.fn()} searchDebounceMs={0} />);
    fireEvent.change(screen.getByTestId("passions-search"), { target: { value: "code" } });
    expect(screen.getByRole("checkbox", { name: /tech & code/i })).toBeInTheDocument();
  });

  it("atténues non-selected chips once the 8-max cap is reached", () => {
    const fullSelection = PASSIONS_CATEGORIES.slice(0, 8).map((c) => c.id);
    render(
      <PassionsPicker
        selected={fullSelection}
        onChange={vi.fn()}
        searchDebounceMs={0}
      />,
    );
    const nineth = screen.getByRole("checkbox", { name: PASSIONS_CATEGORIES[8]!.label });
    expect(nineth).toBeDisabled();
    expect(nineth).toHaveAttribute("aria-disabled", "true");
  });

  it("counter switches to success state once min 3 reached", () => {
    const { rerender } = render(
      <PassionsPicker selected={[]} onChange={vi.fn()} searchDebounceMs={0} />,
    );
    expect(screen.getByTestId("passions-counter")).toHaveTextContent("0 / 3 minimum");
    rerender(
      <PassionsPicker
        selected={["musique", "tech-code", "sport-corps"]}
        onChange={vi.fn()}
        searchDebounceMs={0}
      />,
    );
    expect(screen.getByTestId("passions-counter")).toHaveTextContent("3 / 3 minimum atteint");
  });

  it("adds a custom passion with valid slug and emits custom:<slug>", () => {
    const onChange = vi.fn();
    render(<PassionsPicker selected={[]} onChange={onChange} searchDebounceMs={0} />);
    fireEvent.click(screen.getByTestId("passions-add-custom-trigger"));
    const input = screen.getByTestId("passions-custom-input");
    fireEvent.change(input, { target: { value: "Justice clima" } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(onChange).toHaveBeenCalledWith(["custom:justice-clima"]);
  });

  it("rejects an empty custom slug with an inline error", () => {
    const onChange = vi.fn();
    render(<PassionsPicker selected={[]} onChange={onChange} searchDebounceMs={0} />);
    fireEvent.click(screen.getByTestId("passions-add-custom-trigger"));
    fireEvent.click(screen.getByRole("button", { name: "Ajouter" }));
    expect(screen.getByTestId("passions-custom-error")).toBeInTheDocument();
    expect(onChange).not.toHaveBeenCalled();
  });

  it("removes a previously added custom passion via its X button", () => {
    const onChange = vi.fn();
    render(
      <PassionsPicker
        selected={["custom:graphisme", "musique"]}
        onChange={onChange}
        searchDebounceMs={0}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Retirer graphisme" }));
    expect(onChange).toHaveBeenCalledWith(["musique"]);
  });
});
