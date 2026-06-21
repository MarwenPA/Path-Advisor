import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { StatPersonnelle } from "../StatPersonnelle";
import type { StatPersonnelleState } from "../StatPersonnelle";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function renderStat(
  state: StatPersonnelleState | undefined,
  props: {
    subject?: string;
    currentGrade?: number;
    targetGrade?: number;
    className?: string;
  } = {},
) {
  // Cast to satisfy TS when passing `undefined` for testing defensive path
  return render(
    <StatPersonnelle
      state={state as StatPersonnelleState}
      subject={props.subject}
      currentGrade={props.currentGrade}
      targetGrade={props.targetGrade}
      className={props.className}
    />,
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("StatPersonnelle", () => {
  // 1. null state renders nothing
  it("returns null when state is null", () => {
    const { container } = renderStat(null);
    expect(container.firstChild).toBeNull();
  });

  // 2. undefined state renders nothing (defensive)
  it("returns null when state is undefined", () => {
    const { container } = renderStat(undefined);
    expect(container.firstChild).toBeNull();
  });

  // 3. compatible label
  it("renders 'Compatible' label for compatible state", () => {
    renderStat("compatible");
    expect(screen.getByText("Compatible")).toBeInTheDocument();
  });

  // 4. a_renforcer label
  it("renders 'A renforcer' label for a_renforcer state", () => {
    renderStat("a_renforcer");
    expect(screen.getByText("A renforcer")).toBeInTheDocument();
  });

  // 5. au_dessus label
  it("renders 'Au-dessus' label for au_dessus state", () => {
    renderStat("au_dessus");
    expect(screen.getByText("Au-dessus")).toBeInTheDocument();
  });

  // 6. subject appended to label
  it("shows subject in label when provided", () => {
    renderStat("compatible", { subject: "Mathematiques" });
    expect(screen.getByText("Compatible en Mathematiques")).toBeInTheDocument();
  });

  // 7. grades shown when both provided
  it("shows grades when currentGrade and targetGrade provided", () => {
    renderStat("compatible", { currentGrade: 14, targetGrade: 12 });
    expect(screen.getByText("14/20 vs 12/20 requis")).toBeInTheDocument();
  });

  // 8. grades not shown when not provided
  it("does not show grades when not provided", () => {
    renderStat("compatible");
    expect(screen.queryByText(/\/20 requis/)).not.toBeInTheDocument();
  });

  // 9. role=region for semantic landmark
  it("has role=region", () => {
    renderStat("compatible");
    expect(screen.getByRole("region")).toBeInTheDocument();
  });

  // 10. aria-label includes state label
  it("has aria-label including state label", () => {
    renderStat("compatible");
    expect(screen.getByRole("region", { name: /Compatible/ })).toBeInTheDocument();
  });

  // 11. aria-label includes subject when provided
  it("has aria-label including subject when provided", () => {
    renderStat("a_renforcer", { subject: "Physique" });
    expect(screen.getByRole("region", { name: /A renforcer en Physique/ })).toBeInTheDocument();
  });

  // 12. green color classes for compatible
  it("applies green color classes for compatible state", () => {
    renderStat("compatible");
    const region = screen.getByRole("region");
    expect(region.className).toMatch(/bg-green-50/);
    expect(region.className).toMatch(/border-green-200/);
  });

  // 13. yellow color classes for a_renforcer
  it("applies yellow color classes for a_renforcer state", () => {
    renderStat("a_renforcer");
    const region = screen.getByRole("region");
    expect(region.className).toMatch(/bg-yellow-50/);
    expect(region.className).toMatch(/border-yellow-200/);
  });

  // 14. blue color classes for au_dessus
  it("applies blue color classes for au_dessus state", () => {
    renderStat("au_dessus");
    const region = screen.getByRole("region");
    expect(region.className).toMatch(/bg-blue-50/);
    expect(region.className).toMatch(/border-blue-200/);
  });

  // 15. icon is aria-hidden
  it("icon has aria-hidden", () => {
    renderStat("compatible");
    // Find all elements with aria-hidden; the icon span should be among them
    const region = screen.getByRole("region");
    const hiddenSpans = region.querySelectorAll('[aria-hidden="true"]');
    expect(hiddenSpans.length).toBeGreaterThan(0);
    // The first aria-hidden span is the icon
    expect(hiddenSpans[0].textContent).toBe("✓");
  });
});
