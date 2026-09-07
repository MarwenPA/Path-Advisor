import { describe, expect, it } from "vitest";
import { hex } from "wcag-contrast";

/**
 * WCAG 2.1 contrast audit — runs as a unit test, gating regressions.
 *
 * Thresholds (WCAG 1.4.3 / NFR-A4):
 *  - 4.5:1 minimum for normal text          (AA)
 *  - 3.0:1 minimum for large text (≥ 18 px) (AA Large)
 *  - 7.0:1 AAA — intentionally enforced on the most pervasive pair (`text` on `bg`)
 *    since regressing it would dim the entire body copy.
 *
 * Hex values are duplicated from `tokens.css` on purpose: this test exists to
 * catch drift, so it must read the value independently. If you change a hex in
 * `tokens.css`, update the matching row here.
 *
 * If a ratio drifts below threshold, DO NOT relax the test — escalate to a
 * design decision: the spec value either changed (intentional) or the hex was
 * mis-copied (bug).
 */
const PAIRS: Array<{
  fg: string;
  bg: string;
  name: string;
  minRatio: number;
}> = [
  { fg: "#1A1A1A", bg: "#FAFAF7", name: "text on bg", minRatio: 7 },
  { fg: "#666660", bg: "#FAFAF7", name: "text-muted on bg", minRatio: 4.5 },
  // Review adversariale 2026-09-06 : #8C8C86 ne faisait que 3.19:1, sous le
  // 4.5:1 requis pour du texte normal — or ce token sert au lien légal du
  // footer et aux "— {ville}" en petit corps sur les pages publiques, pas à
  // du grand texte. Assoupli à tort en "large only" à l'origine ; le token
  // a été assombri en #71716A et l'exigence remonte à AA texte normal.
  { fg: "#71716A", bg: "#FAFAF7", name: "text-subtle on bg", minRatio: 4.5 },
  { fg: "#C8312D", bg: "#FAFAF7", name: "brand on bg", minRatio: 4.5 },
  { fg: "#C8312D", bg: "#F4F1ED", name: "brand on bg-2", minRatio: 4.5 },
  { fg: "#9E2A24", bg: "#FAFAF7", name: "danger on bg", minRatio: 4.5 },
];

describe("Design tokens — WCAG contrast", () => {
  for (const { fg, bg, name, minRatio } of PAIRS) {
    it(`${name} (${fg} / ${bg}) ≥ ${minRatio}:1`, () => {
      const ratio = hex(fg, bg);
      expect(ratio).toBeGreaterThanOrEqual(minRatio);
    });
  }
});
