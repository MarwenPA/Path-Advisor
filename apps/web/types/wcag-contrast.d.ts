/**
 * Minimal type declarations for `wcag-contrast` (no @types package upstream).
 * Story 1.2 uses only `hex(fg, bg)`; extend here if other helpers are needed.
 */
declare module "wcag-contrast" {
  export function hex(fg: string, bg: string): number;
  export function rgb(fg: [number, number, number], bg: [number, number, number]): number;
  export function score(ratio: number): "AAA" | "AA" | "AA Large" | "Fail";
}
