import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { BulletinRecap, NormalizedField } from "../onboarding-step3-machine";
import { BulletinRecapEditor } from "../bulletin-recap-editor";

function makeField(overrides?: Partial<NormalizedField>): NormalizedField {
  return {
    key: "note_0",
    label: "Mathématiques",
    value: "15",
    confidence: 0.90,
    isLowConfidence: false,
    ...overrides,
  };
}

function makeRecap(overrides?: Partial<BulletinRecap>): BulletinRecap {
  return {
    bulletinId: "b1",
    label: "Bulletin 1",
    fields: [makeField()],
    confidenceAvg: 0.9,
    validated: false,
    ...overrides,
  };
}

describe("BulletinRecapEditor — AC5/AC6", () => {
  it("renders matière label in table", () => {
    render(
      <BulletinRecapEditor
        recaps={[makeRecap()]}
        activeIndex={0}
        onActiveChange={vi.fn()}
        onFieldsChange={vi.fn()}
        onValidate={vi.fn()}
        onAllValidated={vi.fn()}
      />
    );
    expect(screen.getByText("Mathématiques")).toBeTruthy();
  });

  it("renders current note value", () => {
    render(
      <BulletinRecapEditor
        recaps={[makeRecap()]}
        activeIndex={0}
        onActiveChange={vi.fn()}
        onFieldsChange={vi.fn()}
        onValidate={vi.fn()}
        onAllValidated={vi.fn()}
      />
    );
    expect(screen.getByDisplayValue("15")).toBeTruthy();
  });

  it("calls onFieldsChange when note is edited", async () => {
    const onFieldsChange = vi.fn();
    render(
      <BulletinRecapEditor
        recaps={[makeRecap()]}
        activeIndex={0}
        onActiveChange={vi.fn()}
        onFieldsChange={onFieldsChange}
        onValidate={vi.fn()}
        onAllValidated={vi.fn()}
      />
    );
    const input = screen.getByDisplayValue("15");
    await userEvent.clear(input);
    await userEvent.type(input, "16");
    expect(onFieldsChange).toHaveBeenCalled();
  });

  it("shows low-confidence warning indicator for AC6", () => {
    render(
      <BulletinRecapEditor
        recaps={[makeRecap({ fields: [makeField({ confidence: 0.4, isLowConfidence: true })] })]}
        activeIndex={0}
        onActiveChange={vi.fn()}
        onFieldsChange={vi.fn()}
        onValidate={vi.fn()}
        onAllValidated={vi.fn()}
      />
    );
    // There should be a visual indicator (icon, aria-label, or text) for low confidence
    const lowConfWarning = document.querySelector("[data-low-confidence], [aria-label*='confidence']");
    expect(lowConfWarning).toBeTruthy();
  });

  it("renders tabs when multiple bulletins", () => {
    render(
      <BulletinRecapEditor
        recaps={[makeRecap(), makeRecap({ bulletinId: "b2", label: "Bulletin 2" })]}
        activeIndex={0}
        onActiveChange={vi.fn()}
        onFieldsChange={vi.fn()}
        onValidate={vi.fn()}
        onAllValidated={vi.fn()}
      />
    );
    expect(screen.getByText("Bulletin 1")).toBeTruthy();
    expect(screen.getByText("Bulletin 2")).toBeTruthy();
  });

  it("validate button calls onValidate with correct bulletinId", async () => {
    const onValidate = vi.fn();
    render(
      <BulletinRecapEditor
        recaps={[makeRecap()]}
        activeIndex={0}
        onActiveChange={vi.fn()}
        onFieldsChange={vi.fn()}
        onValidate={onValidate}
        onAllValidated={vi.fn()}
      />
    );
    await userEvent.click(screen.getByRole("button", { name: /valid/i }));
    expect(onValidate).toHaveBeenCalledWith("b1");
  });

  it("uses semantic table element for RGAA", () => {
    const { container } = render(
      <BulletinRecapEditor
        recaps={[makeRecap()]}
        activeIndex={0}
        onActiveChange={vi.fn()}
        onFieldsChange={vi.fn()}
        onValidate={vi.fn()}
        onAllValidated={vi.fn()}
      />
    );
    expect(container.querySelector("table")).toBeTruthy();
  });
});
