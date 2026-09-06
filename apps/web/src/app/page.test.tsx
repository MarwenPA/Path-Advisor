/**
 * Home page (`/`) tests — Story 7.8.
 *
 * Server Component: awaited directly then rendered, mirroring the
 * `(authenticated)/layout.tsx` guard pattern this page reuses.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";

import { renderWithIntl } from "@/test/render-with-intl";

import { ApiError } from "@/lib/api/client";

// Story 7.7 — see `@/test/next-intl-server-mock` for why this is needed
// under Vitest (real Next.js needs no such mock).
vi.mock("next-intl/server", () => import("@/test/next-intl-server-mock"));

import Home, { generateMetadata } from "./page";

const fetchCurrentUserMock = vi.fn();
vi.mock("@/lib/api/auth", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/auth")>("@/lib/api/auth");
  return {
    ...actual,
    fetchCurrentUser: () => fetchCurrentUserMock(),
  };
});

const redirectMock = vi.fn((url: string) => {
  // Mirrors Next.js's real behaviour: redirect() never returns, it throws a
  // control-flow error `unstable_rethrow` is meant to let through untouched.
  throw new Error(`NEXT_REDIRECT:${url}`);
});
vi.mock("next/navigation", () => ({
  redirect: (url: string) => redirectMock(url),
  // Real `unstable_rethrow` rethrows Next's own digest-tagged control-flow
  // errors and no-ops on everything else. Our fake redirect errors are
  // recognizable by the `NEXT_REDIRECT:` prefix, so mimic that contract.
  unstable_rethrow: (error: unknown) => {
    if (error instanceof Error && error.message.startsWith("NEXT_REDIRECT:")) {
      throw error;
    }
  },
}));

beforeEach(() => {
  fetchCurrentUserMock.mockReset();
  redirectMock.mockClear();
});

describe("Home page", () => {
  it("redirects an authenticated student to their home dashboard (reuses getPostLoginPath)", async () => {
    fetchCurrentUserMock.mockResolvedValue({ role: "student", status: "active" });

    await expect(Home()).rejects.toThrow("NEXT_REDIRECT:/accueil");
    expect(redirectMock).toHaveBeenCalledWith("/accueil");
  });

  it("redirects an authenticated parent to the parent dashboard, same role-based path as post-login", async () => {
    fetchCurrentUserMock.mockResolvedValue({ role: "parent", status: "active" });

    await expect(Home()).rejects.toThrow("NEXT_REDIRECT:/parent");
  });

  it("falls back to the privacy settings page for a role without a dedicated dashboard yet", async () => {
    fetchCurrentUserMock.mockResolvedValue({ role: "counselor", status: "active" });

    await expect(Home()).rejects.toThrow("NEXT_REDIRECT:/parametres/confidentialite");
  });

  it("opens the Django admin for path_admin, matching login-form's post-login behaviour", async () => {
    fetchCurrentUserMock.mockResolvedValue({ role: "path_admin", status: "active" });

    await expect(Home()).rejects.toThrow("NEXT_REDIRECT:/admin/");
  });

  it("renders the public landing page for an anonymous visitor (401)", async () => {
    fetchCurrentUserMock.mockRejectedValue(new ApiError(401, "unauthenticated"));

    renderWithIntl(await Home());

    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /créer un compte/i })).toBeInTheDocument();
    expect(redirectMock).not.toHaveBeenCalled();
  });

  it("renders the public landing page for a 403 response", async () => {
    fetchCurrentUserMock.mockRejectedValue(new ApiError(403, "forbidden"));

    renderWithIntl(await Home());

    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
  });

  it("still renders the landing page on an unexpected API error (never 500s the front door)", async () => {
    fetchCurrentUserMock.mockRejectedValue(new ApiError(500, "boom"));

    renderWithIntl(await Home());

    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
  });

  it("still renders the landing page on a network/timeout failure (non-ApiError rejection)", async () => {
    // e.g. the client's AbortSignal.timeout() firing, or a raw fetch TypeError —
    // neither is an ApiError instance (code-review P1 regression test).
    fetchCurrentUserMock.mockRejectedValue(
      new DOMException("The operation timed out.", "TimeoutError"),
    );

    renderWithIntl(await Home());

    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
  });

  it("still renders the landing page when fetchCurrentUser resolves with a malformed payload", async () => {
    // Reading `.role` off a null/undefined user must not crash the page
    // (code-review P1 regression test).
    fetchCurrentUserMock.mockResolvedValue(null);

    renderWithIntl(await Home());

    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
  });

  it("exposes a footer link to the legal RGPD page", async () => {
    fetchCurrentUserMock.mockRejectedValue(new ApiError(401, "unauthenticated"));

    renderWithIntl(await Home());

    expect(screen.getByRole("link", { name: /mentions légales/i })).toHaveAttribute(
      "href",
      "/legal/rgpd",
    );
  });
});

describe("Home page metadata (Story 7.5 AC — OG + Twitter Card)", () => {
  it("exposes og:url/type and a Twitter summary_large_image card", async () => {
    const metadata = await generateMetadata();
    // Next's `Metadata["openGraph"]`/`["twitter"]` types are unions of many
    // subtypes (Website/Article/...) that don't individually guarantee
    // `type`/`card` — loosen to a plain record for this assertion only.
    const openGraph = metadata.openGraph as Record<string, unknown> | undefined;
    const twitter = metadata.twitter as Record<string, unknown> | undefined;

    expect(openGraph?.url).toBe("https://path-advisor.fr");
    expect(openGraph?.type).toBe("website");
    expect(twitter?.card).toBe("summary_large_image");
    // Epic 7 review fix — explicit canonical, relative to `metadataBase`.
    expect(metadata.alternates?.canonical).toBe("/");
  });
});
