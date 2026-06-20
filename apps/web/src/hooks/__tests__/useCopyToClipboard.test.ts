import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useCopyToClipboard } from "../useCopyToClipboard";

describe("useCopyToClipboard", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("copies via navigator.clipboard and sets status to copied", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });

    const { result } = renderHook(() => useCopyToClipboard());
    expect(result.current.status).toBe("idle");

    await act(async () => {
      await result.current.copy("hello");
    });

    expect(writeText).toHaveBeenCalledWith("hello");
    expect(result.current.status).toBe("copied");
    expect(result.current.errorMessage).toBeNull();
  });

  it("resets status to idle after 2 s", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });

    const { result } = renderHook(() => useCopyToClipboard());

    await act(async () => {
      await result.current.copy("hello");
    });

    expect(result.current.status).toBe("copied");

    act(() => {
      vi.advanceTimersByTime(2000);
    });

    expect(result.current.status).toBe("idle");
  });

  it("falls back to execCommand when writeText rejects", async () => {
    const writeText = vi.fn().mockRejectedValue(new Error("denied"));
    Object.assign(navigator, { clipboard: { writeText } });
    const execCommand = vi.fn().mockReturnValue(true);
    Object.assign(document, { execCommand });

    const { result } = renderHook(() => useCopyToClipboard());

    await act(async () => {
      await result.current.copy("hello");
    });

    expect(writeText).toHaveBeenCalledWith("hello");
    expect(execCommand).toHaveBeenCalledWith("copy");
    expect(result.current.status).toBe("copied");
  });

  it("uses execCommand fallback when clipboard API is absent", async () => {
    // Remove the clipboard API entirely.
    Object.assign(navigator, { clipboard: undefined });
    const execCommand = vi.fn().mockReturnValue(true);
    Object.assign(document, { execCommand });

    const { result } = renderHook(() => useCopyToClipboard());

    await act(async () => {
      await result.current.copy("hello");
    });

    expect(execCommand).toHaveBeenCalledWith("copy");
    expect(result.current.status).toBe("copied");
  });

  it("sets error status when both writeText and execCommand fail", async () => {
    Object.assign(navigator, {
      clipboard: { writeText: vi.fn().mockRejectedValue(new Error("denied")) },
    });
    Object.assign(document, { execCommand: vi.fn().mockReturnValue(false) });

    const { result } = renderHook(() => useCopyToClipboard());

    await act(async () => {
      await result.current.copy("hello");
    });

    expect(result.current.status).toBe("error");
    expect(result.current.errorMessage).toMatch(/Ctrl\+C/);
  });

  it("sets error status when clipboard API is absent and execCommand throws", async () => {
    Object.assign(navigator, { clipboard: undefined });
    Object.assign(document, {
      execCommand: vi.fn().mockImplementation(() => {
        throw new Error("execCommand unsupported");
      }),
    });

    const { result } = renderHook(() => useCopyToClipboard());

    await act(async () => {
      await result.current.copy("hello");
    });

    expect(result.current.status).toBe("error");
    expect(result.current.errorMessage).toMatch(/Ctrl\+C/);
  });

  it("does not set state after unmount (async copy in flight)", async () => {
    let resolveWrite: (() => void) | undefined;
    const writeText = vi.fn().mockImplementation(
      () =>
        new Promise<void>((resolve) => {
          resolveWrite = resolve;
        }),
    );
    Object.assign(navigator, { clipboard: { writeText } });

    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    const { result, unmount } = renderHook(() => useCopyToClipboard());

    let copyPromise: Promise<void> | undefined;
    act(() => {
      copyPromise = result.current.copy("hello");
    });

    // Unmount before the clipboard write resolves.
    unmount();

    await act(async () => {
      resolveWrite?.();
      await copyPromise;
    });

    // No "state update on unmounted component" warning should be emitted.
    expect(errorSpy).not.toHaveBeenCalledWith(
      expect.stringContaining("unmounted"),
    );
  });
});
