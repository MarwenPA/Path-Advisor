import "@testing-library/jest-dom/vitest";

// jsdom does not implement ResizeObserver, which several Radix primitives rely on
// (Checkbox, Dialog, Tooltip, …). Provide a no-op shim for the entire test run so
// components do not crash before assertions run.
if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as unknown as typeof ResizeObserver;
}
