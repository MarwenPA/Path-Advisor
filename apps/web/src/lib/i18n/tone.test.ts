/**
 * Front-side calm-tone lint — revue Epic 8 (P3/E).
 *
 * The backend lints every server-built sentence (apps/notifications/tone.py)
 * but fr.json and the error boundary are student-facing surfaces the Python
 * lints never see — a future "Attention !" in the chrome would have shipped.
 * The list mirrors `apps/api/apps/notifications/tone.py::URGENCY_MARKERS`
 * (kept in sync by hand — two runtimes; each side names the other).
 */
import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import messages from "../../../messages/fr.json";

const URGENCY_MARKERS = [
  /derni[eè]re chance/iu,
  /plus que \d+/iu,
  /\bvite\b/iu,
  /\burgent/iu,
  /!!/u,
  /d[ée]p[êe]che/iu,
  /ne (rate|manque) pas/iu,
  /attention[ !,.]/iu,
  /🎉/u,
  /bravo !/iu,
];

function collectStrings(node: unknown, into: string[]): void {
  if (typeof node === "string") {
    into.push(node);
    return;
  }
  if (node && typeof node === "object") {
    for (const value of Object.values(node)) collectStrings(value, into);
  }
}

describe("front calm-tone lint (UX-DR28)", () => {
  it("fr.json carries no urgency marker on any surface", () => {
    const strings: string[] = [];
    collectStrings(messages, strings);
    expect(strings.length).toBeGreaterThan(50); // the walk really walked
    const corpus = strings.join("\n");
    for (const pattern of URGENCY_MARKERS) {
      expect(corpus).not.toMatch(pattern);
    }
  });

  it("the global error boundary copy stays calm too", () => {
    // Deliberately outside fr.json (it must render if i18n itself crashed)
    // — so it gets its own scan.
    const source = readFileSync(path.resolve(__dirname, "../../app/error.tsx"), "utf-8");
    for (const pattern of URGENCY_MARKERS) {
      expect(source).not.toMatch(pattern);
    }
  });
});
