import { renderHook, act } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { useConflictHandler } from "../use-conflict-handler";

describe("useConflictHandler", () => {
  it("initializes with no conflict", () => {
    const { result } = renderHook(() => useConflictHandler());
    expect(result.current.hasConflict).toBe(false);
    expect(result.current.serverState).toBeNull();
  });

  it("registers conflict when handle409 called", () => {
    const { result } = renderHook(() => useConflictHandler());
    const serverState = { level: "lycee_terminale", updated_at: "2026-06-01T00:00:00Z" };
    act(() => {
      result.current.handle409(serverState);
    });
    expect(result.current.hasConflict).toBe(true);
    expect(result.current.serverState).toEqual(serverState);
  });

  it("clears conflict when resolve called", () => {
    const { result } = renderHook(() => useConflictHandler());
    act(() => {
      result.current.handle409({ foo: "bar" });
    });
    act(() => {
      result.current.resolve("reload");
    });
    expect(result.current.hasConflict).toBe(false);
  });
});
