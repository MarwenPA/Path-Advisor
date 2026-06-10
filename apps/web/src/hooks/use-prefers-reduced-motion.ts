"use client";

import * as React from "react";

/**
 * `prefers-reduced-motion: reduce` listener with SSR-safe default.
 *
 * Uses `useSyncExternalStore` so the read is pure at render time and React
 * tears down the subscription automatically on unmount. Returns `false` on
 * the server (third arg) — components that gate motion on this hook render
 * the motion-enabled tree once on hydration, then settle to the OS preference.
 *
 * Re-renders if the OS-level preference changes while the component is
 * mounted (rare but possible — macOS Accessibility toggle).
 */

const MEDIA_QUERY = "(prefers-reduced-motion: reduce)";

function subscribe(callback: () => void): () => void {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return () => {};
  }
  const mediaQuery = window.matchMedia(MEDIA_QUERY);
  mediaQuery.addEventListener("change", callback);
  return () => mediaQuery.removeEventListener("change", callback);
}

function getSnapshot(): boolean {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return false;
  }
  return window.matchMedia(MEDIA_QUERY).matches;
}

function getServerSnapshot(): boolean {
  return false;
}

export function usePrefersReducedMotion(): boolean {
  return React.useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}
