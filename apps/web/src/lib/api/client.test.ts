// @vitest-environment node
/**
 * `apiFetch` cookie-forwarding tests — Epic 7 review fix: calling
 * `cookies()` (even inside try/catch) opts the route into dynamic
 * rendering, so the public SEO fetchers must be able to skip it entirely
 * via `forwardCookies: false`. Node environment (no `window`) so the
 * server-side branch of `getServerCookieHeader` actually runs.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const cookiesMock = vi.fn();
vi.mock("next/headers", () => ({
  cookies: () => cookiesMock(),
}));

import { apiFetch } from "./client";

describe("apiFetch cookie forwarding (server-side)", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    cookiesMock.mockReturnValue({
      get: (name: string) => (name === "sessionid" ? { value: "abc" } : undefined),
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    cookiesMock.mockReset();
  });

  it("forwards sessionid/csrftoken by default (authenticated fetchers)", async () => {
    await apiFetch("/api/v1/me/");

    expect(cookiesMock).toHaveBeenCalled();
    const headers = fetchMock.mock.calls[0]![1].headers as Record<string, string>;
    expect(headers.Cookie).toBe("sessionid=abc");
  });

  it("never touches cookies() with forwardCookies: false (public SEO fetchers stay static)", async () => {
    await apiFetch("/api/v1/public/professions/x/", { forwardCookies: false });

    expect(cookiesMock).not.toHaveBeenCalled();
    const headers = fetchMock.mock.calls[0]![1].headers as Record<string, string>;
    expect(headers.Cookie).toBeUndefined();
  });
});
