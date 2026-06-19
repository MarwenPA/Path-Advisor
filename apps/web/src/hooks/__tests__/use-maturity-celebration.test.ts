/**
 * useMaturityCelebration tests — Story 2.7 AC8.
 */

import { renderHook, act } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useMaturityCelebration } from "../use-maturity-celebration";

// Stub fetch so markCelebrationSeen doesn't throw
vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: true })));

afterEach(() => {
  sessionStorage.clear();
  vi.clearAllMocks();
});

describe("useMaturityCelebration (AC8)", () => {
  it("returns no message on first render (no previous level)", () => {
    const { result } = renderHook(() =>
      useMaturityCelebration("base", "user-1")
    );
    expect(result.current.message).toBeNull();
  });

  it("fires toast on base → enriched transition", () => {
    sessionStorage.setItem("maturity_prev_level:user-1", "base");
    const { result } = renderHook(() =>
      useMaturityCelebration("enriched", "user-1")
    );
    expect(result.current.message).toContain("Profil enrichi débloqué");
  });

  it("fires toast on enriched → complete transition", () => {
    sessionStorage.setItem("maturity_prev_level:user-1", "enriched");
    const { result } = renderHook(() =>
      useMaturityCelebration("complete", "user-1")
    );
    expect(result.current.message).toContain("Profil complet débloqué");
  });

  it("does NOT fire toast on downgrade (enriched → base)", () => {
    sessionStorage.setItem("maturity_prev_level:user-1", "enriched");
    const { result } = renderHook(() =>
      useMaturityCelebration("base", "user-1")
    );
    expect(result.current.message).toBeNull();
  });

  it("dismiss clears the message", () => {
    sessionStorage.setItem("maturity_prev_level:user-1", "base");
    const { result } = renderHook(() =>
      useMaturityCelebration("enriched", "user-1")
    );
    expect(result.current.message).not.toBeNull();
    act(() => result.current.dismiss());
    expect(result.current.message).toBeNull();
  });

  it("does not fire if same level (no transition)", () => {
    sessionStorage.setItem("maturity_prev_level:user-1", "enriched");
    const { result } = renderHook(() =>
      useMaturityCelebration("enriched", "user-1")
    );
    expect(result.current.message).toBeNull();
  });
});
