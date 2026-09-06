/**
 * `/[slug]/opengraph-image` (devenir-{metier}) tests — Story 7.5.
 */
import { beforeEach, describe, expect, it, vi } from "vitest";

const fetchPublicProfessionMock = vi.fn();
vi.mock("@/lib/api/professions", () => ({
  fetchPublicProfession: (...args: unknown[]) => fetchPublicProfessionMock(...args),
}));

import Image from "./opengraph-image";

describe("[slug] (devenir-{metier}) opengraph-image", () => {
  beforeEach(() => {
    fetchPublicProfessionMock.mockReset();
  });

  it("renders an image using the profession name when the slug is prefixed", async () => {
    fetchPublicProfessionMock.mockResolvedValue({ name: "Infirmier·ère" });

    const response = await Image({ params: Promise.resolve({ slug: "devenir-infirmier-test" }) });

    expect(response).toBeInstanceOf(Response);
    expect(fetchPublicProfessionMock).toHaveBeenCalledWith("infirmier-test");
  });

  it("still renders a fallback image when the slug isn't prefixed", async () => {
    const response = await Image({ params: Promise.resolve({ slug: "infirmier-test" }) });

    expect(response).toBeInstanceOf(Response);
    expect(fetchPublicProfessionMock).not.toHaveBeenCalled();
  });
});
