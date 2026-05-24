import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { GdprExportRequest } from "@/lib/api/gdpr";

import { GdprExportCard } from "./gdpr-export-card";

function makeExport(overrides: Partial<GdprExportRequest> = {}): GdprExportRequest {
  return {
    id: "gex_01TEST",
    status: "pending",
    requested_at: "2026-05-17T14:30:00Z",
    ready_at: null,
    expires_at: null,
    download_count: 0,
    error_code: null,
    error_message: null,
    ...overrides,
  };
}

describe("GdprExportCard", () => {
  it("shows the active-export message when status is pending", () => {
    render(<GdprExportCard export_={makeExport({ status: "pending" })} />);
    expect(screen.getByText(/Préparation de ton export en cours/i)).toBeInTheDocument();
    expect(screen.queryByText(/Télécharger l'archive/i)).not.toBeInTheDocument();
  });

  it("renders the download button when status is ready", () => {
    render(
      <GdprExportCard
        export_={makeExport({
          status: "ready",
          ready_at: "2026-05-17T15:00:00Z",
          expires_at: "2026-05-24T15:00:00Z",
          download_count: 0,
        })}
      />,
    );
    const link = screen.getByRole("link", { name: /Télécharger l'export du/i });
    // Next.js Link strips the trailing slash when rendering to <a>. Django REST
    // Framework redirects unsuffixed URLs to the slashed variant, so the click
    // still reaches the right view.
    expect(link.getAttribute("href")).toMatch(
      /\/api\/v1\/me\/gdpr-exports\/gex_01TEST\/download\/?$/,
    );
    expect(link).toHaveAttribute("target", "_blank");
  });

  it("renders a clear message when status is expired", () => {
    render(<GdprExportCard export_={makeExport({ status: "expired" })} />);
    expect(screen.getByText(/Ce lien a expiré/i)).toBeInTheDocument();
  });

  it("shows error code + retry copy when status is failed", () => {
    render(
      <GdprExportCard
        export_={makeExport({ status: "failed", error_code: "gdpr.build_failed" })}
        onRetry={() => undefined}
      />,
    );
    expect(screen.getByText(/code gdpr\.build_failed/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Retenter un export/i })).toBeInTheDocument();
  });

  it("uses a text-bearing status badge (RGAA: not colour-only)", () => {
    render(<GdprExportCard export_={makeExport({ status: "ready" })} />);
    expect(screen.getByRole("status", { name: /Statut de l'export/i })).toHaveTextContent("Prêt");
  });
});
