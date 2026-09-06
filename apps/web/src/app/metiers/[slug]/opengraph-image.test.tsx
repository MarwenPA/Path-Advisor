/**
 * `/metiers/[slug]/opengraph-image` tests — Story 7.5.
 */
import { describe, expect, it, vi } from "vitest";

const fetchPublicProfessionMock = vi.fn();
vi.mock("@/lib/api/professions", () => ({
  fetchPublicProfession: (...args: unknown[]) => fetchPublicProfessionMock(...args),
}));

import Image from "./opengraph-image";

describe("metiers/[slug] opengraph-image", () => {
  it("renders an image using the profession name", async () => {
    fetchPublicProfessionMock.mockResolvedValue({ name: "Infirmier·ère" });

    const response = await Image({ params: Promise.resolve({ slug: "infirmier-test" }) });

    expect(response).toBeInstanceOf(Response);
    expect(fetchPublicProfessionMock).toHaveBeenCalledWith("infirmier-test");
  });

  it("still renders a fallback image when the profession fetch fails", async () => {
    fetchPublicProfessionMock.mockRejectedValue(new Error("not found"));

    const response = await Image({ params: Promise.resolve({ slug: "metier-inexistant" }) });

    expect(response).toBeInstanceOf(Response);
  });
});
