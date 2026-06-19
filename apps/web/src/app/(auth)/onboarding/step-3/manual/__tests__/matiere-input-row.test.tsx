import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { MatiereInputRow } from "../MatiereInputRow";

const defaultProps = {
  subject: { id: "mathematiques", label: "Mathématiques", is_specialite: true, is_optional: false },
  onNoteChange: vi.fn(),
  onAppreciationChange: vi.fn(),
  onRemove: vi.fn(),
  note: null,
  appreciation: null,
};

describe("MatiereInputRow", () => {
  it("renders subject label", () => {
    render(<MatiereInputRow {...defaultProps} />);
    expect(screen.getAllByText("Mathématiques").length).toBeGreaterThan(0);
  });

  it("renders note input with placeholder", () => {
    render(<MatiereInputRow {...defaultProps} />);
    expect(screen.getByPlaceholderText(/—\.—/)).toBeInTheDocument();
  });

  it("calls onNoteChange on blur with valid decimal note", async () => {
    const onNoteChange = vi.fn();
    render(<MatiereInputRow {...defaultProps} onNoteChange={onNoteChange} />);
    const input = screen.getByPlaceholderText(/—\.—/);
    await userEvent.type(input, "14.5");
    fireEvent.blur(input);
    expect(onNoteChange).toHaveBeenCalledWith("mathematiques", 14.5);
  });

  it("shows error on blur when note > 20", async () => {
    render(<MatiereInputRow {...defaultProps} />);
    const input = screen.getByPlaceholderText(/—\.—/);
    await userEvent.type(input, "21");
    fireEvent.blur(input);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("shows error on blur when note is non-numeric", async () => {
    render(<MatiereInputRow {...defaultProps} />);
    const input = screen.getByPlaceholderText(/—\.—/);
    await userEvent.type(input, "abc");
    fireEvent.blur(input);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("does NOT show error when field is empty (blank is allowed)", () => {
    render(<MatiereInputRow {...defaultProps} />);
    const input = screen.getByPlaceholderText(/—\.—/);
    fireEvent.blur(input);
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("normalizes comma to dot (14,5 → 14.5)", async () => {
    const onNoteChange = vi.fn();
    render(<MatiereInputRow {...defaultProps} onNoteChange={onNoteChange} />);
    const input = screen.getByPlaceholderText(/—\.—/);
    await userEvent.type(input, "14,5");
    fireEvent.blur(input);
    expect(onNoteChange).toHaveBeenCalledWith("mathematiques", 14.5);
  });

  it("expands appreciation textarea when button is clicked", async () => {
    render(<MatiereInputRow {...defaultProps} />);
    const expandButton = screen.getByRole("button", { name: /appréciation/i });
    await userEvent.click(expandButton);
    expect(screen.getByRole("textbox", { name: /appréciation/i })).toBeInTheDocument();
  });

  it("calls onRemove when delete button is clicked", async () => {
    const onRemove = vi.fn();
    render(<MatiereInputRow {...defaultProps} onRemove={onRemove} />);
    const removeButton = screen.getByRole("button", { name: /supprimer/i });
    await userEvent.click(removeButton);
    expect(onRemove).toHaveBeenCalledWith("mathematiques");
  });

  it("has accessible fieldset with sr-only legend", () => {
    render(<MatiereInputRow {...defaultProps} />);
    const fieldset = screen.getByRole("group");
    expect(fieldset.querySelector("legend")).toBeTruthy();
  });
});
