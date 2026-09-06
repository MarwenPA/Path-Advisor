import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";

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
});
