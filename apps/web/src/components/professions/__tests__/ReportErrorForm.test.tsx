/**
 * Tests for ReportErrorForm — Story 3.8 AC9 frontend.
 *
 * Tests form field validation and submit behaviour in isolation.
 */

import * as React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { ReportErrorForm } from "../ReportErrorForm";

const mockOnSubmit = vi.fn();
const mockOnCancel = vi.fn();

function renderForm(props: Partial<React.ComponentProps<typeof ReportErrorForm>> = {}) {
  return render(
    <ReportErrorForm
      professionName="Infirmier·ère"
      isSubmitting={false}
      submitError={null}
      onSubmit={mockOnSubmit}
      onCancel={mockOnCancel}
      {...props}
    />,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("ReportErrorForm", () => {
  it("renders profession name as subtitle", () => {
    renderForm();
    expect(screen.getByText("Infirmier·ère")).toBeInTheDocument();
  });

  it("renders error type label", () => {
    renderForm();
    // Label contains "Type d'erreur *" — use getAllByText since the DOM may have multiple matches
    const labels = screen.getAllByText(/type d.erreur/i);
    expect(labels.length).toBeGreaterThan(0);
  });

  it("does not call onSubmit when error_type is not selected", () => {
    renderForm();
    fireEvent.click(screen.getByRole("button", { name: /envoyer le signalement/i }));
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it("shows validation error when submitted without error_type", () => {
    renderForm();
    fireEvent.click(screen.getByRole("button", { name: /envoyer le signalement/i }));
    expect(screen.getByText(/ce champ est obligatoire/i)).toBeInTheDocument();
  });

  it("shows submit error message when submitError prop is provided", () => {
    renderForm({ submitError: "Envoi échoué — réessaie dans quelques instants" });
    expect(screen.getByRole("alert")).toHaveTextContent(/envoi échoué/i);
  });

  it("calls onCancel when Annuler is clicked", () => {
    renderForm();
    fireEvent.click(screen.getByRole("button", { name: /annuler/i }));
    expect(mockOnCancel).toHaveBeenCalledOnce();
  });

  it("disables submit button when isSubmitting is true", () => {
    renderForm({ isSubmitting: true });
    expect(screen.getByRole("button", { name: /envoi…/i })).toBeDisabled();
  });

  it("shows comment character counter", () => {
    renderForm();
    expect(screen.getByText("0/500")).toBeInTheDocument();
  });

  it("updates comment counter as user types", () => {
    renderForm();
    const textarea = screen.getByPlaceholderText(/décris l'erreur/i);
    fireEvent.change(textarea, { target: { value: "abc" } });
    expect(screen.getByText("3/500")).toBeInTheDocument();
  });

  it("caps comment at 500 characters", () => {
    renderForm();
    const textarea = screen.getByPlaceholderText(/décris l'erreur/i);
    fireEvent.change(textarea, { target: { value: "x".repeat(600) } });
    expect(screen.getByText("500/500")).toBeInTheDocument();
  });
});
