/**
 * `/[slug]/[metierSlug]/opengraph-image` (quel-bac-pour-{metier}) tests —
 * Story 7.5.
 */
import { beforeEach, describe, expect, it, vi } from "vitest";

const fetchPublicProfessionMock = vi.fn();
vi.mock("@/lib/api/professions", () => ({
  fetchPublicProfession: (...args: unknown[]) => fetchPublicProfessionMock(...args),
}));

import Image from "./opengraph-image";

describe("[slug]/[metierSlug] (quel-bac-pour-{metier}) opengraph-image", () => {
  beforeEach(() => {
    fetchPublicProfessionMock.mockReset();
  });

  it("renders an image using the profession name when metierSlug is prefixed", async () => {
    fetchPublicProfessionMock.mockResolvedValue({ name: "Technicien·ne aéronautique" });

    const response = await Image({
      params: Promise.resolve({ slug: "3eme", metierSlug: "quel-bac-pour-technicien-aero-test" }),
    });

    expect(response).toBeInstanceOf(Response);
    expect(fetchPublicProfessionMock).toHaveBeenCalledWith("technicien-aero-test");
  });

  it("still renders a fallback image when metierSlug isn't prefixed", async () => {
    const response = await Image({
      params: Promise.resolve({ slug: "3eme", metierSlug: "technicien-aero-test" }),
    });

    expect(response).toBeInstanceOf(Response);
    expect(fetchPublicProfessionMock).not.toHaveBeenCalled();
  });
});
