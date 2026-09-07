/**
 * `serializeJsonLd` tests — Epic 7 review fix (stored XSS via JSON-LD).
 */
import { describe, expect, it } from "vitest";

import { serializeJsonLd } from "./json-ld";

describe("serializeJsonLd", () => {
  it("neutralises a </script> breakout payload", () => {
    const payload = {
      "@type": "Occupation",
      description: `innocuous</script><script>alert("xss")</script>`,
    };
    const html = serializeJsonLd(payload);
    // No literal "<" may survive — "</script>" anywhere inside the block
    // would close the JSON-LD script element and start executing markup.
    expect(html).not.toContain("<");
    expect(html).toContain("\\u003c/script>");
  });

  it("stays strictly-equivalent JSON after escaping", () => {
    const payload = { name: "a<b & </script>", nested: { arr: ["<", 1, null] } };
    expect(JSON.parse(serializeJsonLd(payload))).toEqual(payload);
  });
});
