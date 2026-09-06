/**
 * `/formations/[slug]/opengraph-image` tests — Story 7.5.
 */
import { describe, expect, it, vi } from "vitest";

const fetchPublicSchoolMock = vi.fn();
vi.mock("@/lib/api/schools", () => ({
  fetchPublicSchool: (...args: unknown[]) => fetchPublicSchoolMock(...args),
}));

import Image from "./opengraph-image";

describe("formations/[slug] opengraph-image", () => {
  it("renders an image using the school name", async () => {
    fetchPublicSchoolMock.mockResolvedValue({ name: "INSA Lyon" });

    const response = await Image({ params: Promise.resolve({ slug: "insa-lyon" }) });

    expect(response).toBeInstanceOf(Response);
    expect(fetchPublicSchoolMock).toHaveBeenCalledWith("insa-lyon");
  });

  it("still renders a fallback image when the school fetch fails", async () => {
    fetchPublicSchoolMock.mockRejectedValue(new Error("not found"));

    const response = await Image({ params: Promise.resolve({ slug: "ecole-inexistante" }) });

    expect(response).toBeInstanceOf(Response);
  });
});
