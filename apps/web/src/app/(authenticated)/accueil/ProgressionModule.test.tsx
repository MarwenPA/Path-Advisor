/**
 * `ProgressionModule` tests — Story 8.8 code-review fix.
 *
 * Added because AC2 (module hidden when `level === "complete"`, module
 * shown otherwise) previously had ZERO real assertions — `page.test.tsx`
 * mocks this component entirely.
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { ProgressionModule } from "./ProgressionModule";

const fetchCurrentUserMock = vi.fn();
vi.mock("@/lib/api/auth", () => ({
  fetchCurrentUser: () => fetchCurrentUserMock(),
}));

const fetchMock = vi.fn();
vi.stubGlobal("fetch", fetchMock);

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

beforeEach(() => {
  fetchCurrentUserMock.mockReset();
  fetchMock.mockReset();
});

describe("ProgressionModule", () => {
  it("renders nothing while the current user hasn't resolved yet", () => {
    fetchCurrentUserMock.mockReturnValue(new Promise(() => {})); // never resolves
    const { container } = render(<ProgressionModule />, { wrapper });
    expect(container).toBeEmptyDOMElement();
  });

  it("renders the progress card with its own labelled section when level is not complete", async () => {
    fetchCurrentUserMock.mockResolvedValue({ id: "u1", email: "a@test.local", role: "student" });
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({
        level: "base",
        next_actions: [{ icon: "passions", label: "Termine tes passions", benefit: "..." }],
        computed_at: new Date().toISOString(),
      }),
    });

    render(<ProgressionModule />, { wrapper });

    await waitFor(() => {
      expect(screen.getByRole("heading", { level: 2, name: "Ta progression" })).toBeInTheDocument();
    });
    const section = screen
      .getByRole("heading", { level: 2, name: "Ta progression" })
      .closest("section");
    expect(section).toHaveAttribute("aria-labelledby", "accueil-progression-title");
  });

  it("renders nothing (no empty landmark) once level is complete — AC2", async () => {
    fetchCurrentUserMock.mockResolvedValue({ id: "u1", email: "a@test.local", role: "student" });
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({
        level: "complete",
        next_actions: [],
        computed_at: new Date().toISOString(),
      }),
    });

    const { container } = render(<ProgressionModule />, { wrapper });

    // ProfileMaturityIndicator variant="dashboard-card" returns null for
    // "complete" — assert no section/heading ever appears, not just
    // "eventually equals something".
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    expect(
      screen.queryByRole("heading", { level: 2, name: "Ta progression" }),
    ).not.toBeInTheDocument();
    expect(container).toBeEmptyDOMElement();
  });

  it("renders nothing on a maturity fetch error (module stays silently hidden)", async () => {
    fetchCurrentUserMock.mockResolvedValue({ id: "u1", email: "a@test.local", role: "student" });
    fetchMock.mockResolvedValue({ ok: false, status: 500 });

    const { container } = render(<ProgressionModule />, { wrapper });

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    expect(container).toBeEmptyDOMElement();
  });
});
