import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { HowItWorksSection } from "./how-it-works-section";

describe("HowItWorksSection", () => {
  it("renders a heading and 4 sequential steps", () => {
    render(<HowItWorksSection />);

    expect(
      screen.getByRole("heading", { level: 2, name: /comment ça marche/i }),
    ).toBeInTheDocument();

    const items = screen.getAllByRole("listitem");
    expect(items).toHaveLength(4);
  });
});
