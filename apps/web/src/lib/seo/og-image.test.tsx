/**
 * `renderOgImage` tests — Story 7.5.
 */
import { describe, expect, it } from "vitest";

import { OG_IMAGE_CONTENT_TYPE, OG_IMAGE_SIZE, renderOgImage } from "./og-image";

describe("renderOgImage", () => {
  it("returns a 1200×630 PNG image response", () => {
    const response = renderOgImage({ eyebrow: "Fiche métier", title: "Infirmier·ère" });

    expect(response).toBeInstanceOf(Response);
    expect(response.headers.get("content-type")).toBe(OG_IMAGE_CONTENT_TYPE);
  });

  it("exposes the expected 1200×630 size constant", () => {
    expect(OG_IMAGE_SIZE).toEqual({ width: 1200, height: 630 });
  });
});
