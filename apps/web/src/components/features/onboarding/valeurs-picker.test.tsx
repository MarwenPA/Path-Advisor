import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { VALEURS } from "@/lib/onboarding/referentials";

import { ValeursPicker } from "./valeurs-picker";

describe("ValeursPicker", () => {
  it("renders all 12 valeurs as role=checkbox", () => {
    render(<ValeursPicker selected={[]} onChange={vi.fn()} />);
    expect(screen.getAllByRole("checkbox")).toHaveLength(VALEURS.length);
  });

  it("renders the description under each label (AC3 — card with desc)", () => {
    render(<ValeursPicker selected={[]} onChange={vi.fn()} />);
    expect(
      screen.getByText(/que les choses soient justes pour tout le monde/i),
    ).toBeInTheDocument();
  });

  it("toggling a card emits the new full list", () => {
    const onChange = vi.fn();
    render(<ValeursPicker selected={[]} onChange={onChange} />);
    fireEvent.click(screen.getByRole("checkbox", { name: /justice sociale/i }));
    expect(onChange).toHaveBeenCalledWith(["justice-sociale"]);
  });

  it("atténues non-selected cards once 5-max is reached", () => {
    const five = VALEURS.slice(0, 5).map((v) => v.id);
    render(<ValeursPicker selected={five} onChange={vi.fn()} />);
    const sixth = screen.getByRole("checkbox", { name: new RegExp(VALEURS[5]!.label, "i") });
    expect(sixth).toBeDisabled();
    expect(sixth).toHaveAttribute("aria-disabled", "true");
  });

  it("counter switches to success at min 3", () => {
    const { rerender } = render(<ValeursPicker selected={[]} onChange={vi.fn()} />);
    expect(screen.getByTestId("valeurs-counter")).toHaveTextContent("0 / 3 minimum");
    rerender(
      <ValeursPicker
        selected={["justice-sociale", "creativite", "sens-utilite"]}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByTestId("valeurs-counter")).toHaveTextContent("3 / 3 minimum atteint");
  });
});
