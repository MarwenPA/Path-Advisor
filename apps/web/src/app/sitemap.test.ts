/**
 * `/sitemap.xml` tests — Story 7.4.
 */
import { describe, expect, it, vi } from "vitest";

const fetchPublicProfessionSlugsMock = vi.fn();
const fetchPublicSchoolSlugsMock = vi.fn();

vi.mock("@/lib/api/professions", () => ({
  fetchPublicProfessionSlugs: () => fetchPublicProfessionSlugsMock(),
}));
vi.mock("@/lib/api/schools", () => ({
  fetchPublicSchoolSlugs: () => fetchPublicSchoolSlugsMock(),
}));

import sitemap from "./sitemap";

describe("sitemap", () => {
  it("includes the homepage plus métier/devenir/formation entries", async () => {
    fetchPublicProfessionSlugsMock.mockResolvedValue([
      { slug: "infirmier", updated_at: "2026-01-01T00:00:00Z" },
    ]);
    fetchPublicSchoolSlugsMock.mockResolvedValue([
      { slug: "insa-lyon", updated_at: "2026-01-02T00:00:00Z" },
    ]);

    const entries = await sitemap();
    const urls = entries.map((e) => e.url);

    expect(urls).toContain("https://path-advisor.fr");
    expect(urls).toContain("https://path-advisor.fr/metiers/infirmier");
    expect(urls).toContain("https://path-advisor.fr/devenir-infirmier");
    expect(urls).toContain("https://path-advisor.fr/formations/insa-lyon");
  });

  it("does not throw when a fetch fails (graceful degradation)", async () => {
    fetchPublicProfessionSlugsMock.mockRejectedValue(new Error("network"));
    fetchPublicSchoolSlugsMock.mockResolvedValue([]);

    const entries = await sitemap();

    expect(entries.some((e) => e.url === "https://path-advisor.fr")).toBe(true);
  });
});
