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

// jsdom 25 ships a partial `Storage` (only `getItem` / `setItem` — no
// `removeItem`, `clear`, `key`, or `length`). Story 2.1's localStorage-draft
// logic relies on the full API; without the missing methods our hook silently
// skips its cleanup path AND tests can't reset state between cases. Install a
// Map-backed shim only when the built-in is incomplete.
if (
  typeof globalThis.localStorage === "undefined" ||
  typeof globalThis.localStorage.removeItem !== "function" ||
  typeof globalThis.localStorage.clear !== "function"
) {
  const store = new Map<string, string>();
  const shim: Storage = {
    get length() {
      return store.size;
    },
    clear() {
      store.clear();
    },
    getItem(key: string) {
      return store.get(key) ?? null;
    },
    key(index: number) {
      return Array.from(store.keys())[index] ?? null;
    },
    removeItem(key: string) {
      store.delete(key);
    },
    setItem(key: string, value: string) {
      store.set(key, String(value));
    },
  };
  Object.defineProperty(globalThis, "localStorage", {
    configurable: true,
    value: shim,
  });
  if (typeof globalThis.window !== "undefined") {
    Object.defineProperty(globalThis.window, "localStorage", {
      configurable: true,
      value: shim,
    });
  }
}
