import { afterEach, describe, expect, it, vi } from "vitest";
import { act, renderHook } from "@testing-library/react";

import { usePrefersReducedMotion } from "./use-prefers-reduced-motion";

type ChangeListener = (event: { matches: boolean }) => void;

function mockMatchMedia(initial: boolean) {
  const listeners = new Set<ChangeListener>();
  const mq = {
    matches: initial,
    addEventListener: (_: string, listener: ChangeListener) => {
      listeners.add(listener);
    },
    removeEventListener: (_: string, listener: ChangeListener) => {
      listeners.delete(listener);
    },
  };
  vi.stubGlobal(
    "matchMedia",
    vi.fn(() => mq),
  );
  return {
    emit(matches: boolean) {
      mq.matches = matches;
      for (const listener of listeners) listener({ matches });
    },
  };
}

describe("usePrefersReducedMotion", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns the initial matchMedia value after mount", () => {
    mockMatchMedia(true);
    const { result } = renderHook(() => usePrefersReducedMotion());
    expect(result.current).toBe(true);
  });

  it("updates when the OS-level preference flips", () => {
    const mq = mockMatchMedia(false);
    const { result } = renderHook(() => usePrefersReducedMotion());
    expect(result.current).toBe(false);
    act(() => {
      mq.emit(true);
    });
    expect(result.current).toBe(true);
  });
});
