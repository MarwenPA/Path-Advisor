import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { BulletinsAddSheet } from "../bulletins-add-sheet";

function wrap(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>);
}

describe("BulletinsAddSheet", () => {
  it("does not render sheet content when closed", () => {
    wrap(
      <BulletinsAddSheet open={false} onClose={vi.fn()} onSuccess={vi.fn()} />
    );
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("renders sheet with title when open", () => {
    wrap(
      <BulletinsAddSheet open={true} onClose={vi.fn()} onSuccess={vi.fn()} />
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText(/ajoute tes bulletins/i)).toBeInTheDocument();
  });

  it("shows two action buttons: scanner and saisir", () => {
    wrap(
      <BulletinsAddSheet open={true} onClose={vi.fn()} onSuccess={vi.fn()} />
    );
    expect(
      screen.getByRole("button", { name: /scanner.*importer/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /saisir.*main/i })
    ).toBeInTheDocument();
  });

  it("calls onClose when Annuler is clicked", () => {
    const onClose = vi.fn();
    wrap(
      <BulletinsAddSheet open={true} onClose={onClose} onSuccess={vi.fn()} />
    );
    fireEvent.click(screen.getByRole("button", { name: /annuler/i }));
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("sheet has dialog role and aria-modal", () => {
    wrap(
      <BulletinsAddSheet open={true} onClose={vi.fn()} onSuccess={vi.fn()} />
    );
    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("aria-modal", "true");
  });

  it("subtitle is calm and non-coercive", () => {
    wrap(
      <BulletinsAddSheet open={true} onClose={vi.fn()} onSuccess={vi.fn()} />
    );
    const text = screen.getByRole("dialog").textContent?.toLowerCase() ?? "";
    const forbidden = ["incomplet", "débloque", "manque", "obligation", "%"];
    forbidden.forEach((w) => expect(text).not.toContain(w));
  });
});
