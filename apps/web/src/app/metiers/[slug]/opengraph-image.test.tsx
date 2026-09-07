/**
 * `/metiers/[slug]/opengraph-image` tests — Story 7.5.
 */
import { describe, expect, it, vi } from "vitest";

const fetchPublicProfessionMock = vi.fn();
vi.mock("@/lib/api/professions", () => ({
  fetchPublicProfession: (...args: unknown[]) => fetchPublicProfessionMock(...args),
}));

import Image, { generateImageMetadata } from "./opengraph-image";

describe("metiers/[slug] opengraph-image", () => {
  it("renders an image using the profession name", async () => {
    fetchPublicProfessionMock.mockResolvedValue({ name: "Infirmier·ère" });

    const response = await Image({ params: Promise.resolve({ slug: "infirmier-test" }) });

    expect(response).toBeInstanceOf(Response);
    expect(fetchPublicProfessionMock).toHaveBeenCalledWith("infirmier-test");
  });

  it("names the profession in the image alt (Epic 7 review — generic alt fix)", async () => {
    fetchPublicProfessionMock.mockResolvedValue({ name: "Infirmier·ère" });

    const [meta] = await generateImageMetadata({
      params: Promise.resolve({ slug: "infirmier-test" }),
    });

    expect(meta!.alt).toBe("Fiche métier Infirmier·ère — Path-Advisor");
  });

  it("falls back to a generic alt when the profession fetch fails", async () => {
    fetchPublicProfessionMock.mockRejectedValue(new Error("not found"));

    const [meta] = await generateImageMetadata({
      params: Promise.resolve({ slug: "metier-inexistant" }),
    });

    expect(meta!.alt).toBe("Fiche métier — Path-Advisor");
  });

  it("still renders a fallback image when the profession fetch fails", async () => {
    fetchPublicProfessionMock.mockRejectedValue(new Error("not found"));

    const response = await Image({ params: Promise.resolve({ slug: "metier-inexistant" }) });

    expect(response).toBeInstanceOf(Response);
  });
});
