import { describe, expect, it } from "vitest";
import { screen, within } from "@testing-library/react";

import { renderWithIntl } from "@/test/render-with-intl";

import { AhaMomentsSection } from "./aha-moments-section";

describe("AhaMomentsSection", () => {
  it("highlights the two flagship product moments", () => {
    renderWithIntl(<AhaMomentsSection />);

    expect(
      screen.getByRole("heading", { level: 2, name: /ce qui change tout/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 3, name: /métiers faits pour toi/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 3, name: /chances d'admission/i }),
    ).toBeInTheDocument();
  });

  it("illustrates each moment with example professions and a described parcours graph", () => {
    renderWithIntl(<AhaMomentsSection />);

    const examples = screen.getByRole("list", { name: /exemples de métiers/i });
    expect(within(examples).getAllByRole("listitem")).toHaveLength(4);

    const legend = screen.getByRole("list", { name: /légende des paris/i });
    expect(
      within(legend)
        .getAllByRole("listitem")
        .map((li) => li.textContent),
    ).toEqual(["Pari sûr", "Pari réaliste", "Pari audacieux"]);

    expect(screen.getByRole("img", { name: /graphe de parcours/i })).toBeInTheDocument();
  });
});
