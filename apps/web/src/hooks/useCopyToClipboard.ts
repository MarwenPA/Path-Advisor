"use client";

import * as React from "react";

type CopyStatus = "idle" | "copied" | "error";

interface UseCopyToClipboardReturn {
  copy: (text: string) => Promise<void>;
  status: CopyStatus;
  errorMessage: string | null;
}

const RESET_DELAY_MS = 2000;

/**
 * Synchronous `execCommand` fallback for non-HTTPS contexts or browsers where
 * `navigator.clipboard.writeText` is unavailable or rejected (e.g. permission
 * denied). Wrapped in try/finally so the off-screen textarea is always removed
 * and the previously focused element is restored (keyboard users keep focus on
 * the Copy button).
 *
 * @returns `true` if the copy succeeded.
 */
function legacyCopy(text: string): boolean {
  const activeElement = document.activeElement as HTMLElement | null;
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.style.position = "fixed";
  textarea.style.top = "-9999px";
  textarea.setAttribute("readonly", "");
  document.body.appendChild(textarea);

  try {
    textarea.focus();
    textarea.select();
    return document.execCommand("copy");
  } finally {
    document.body.removeChild(textarea);
    // Restore focus to the element that triggered the copy (keyboard a11y).
    if (activeElement && typeof activeElement.focus === "function") {
      activeElement.focus();
    }
  }
}

export function useCopyToClipboard(): UseCopyToClipboardReturn {
  const [status, setStatus] = React.useState<CopyStatus>("idle");
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);
  const timeoutRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);
  const isMountedRef = React.useRef(true);

  React.useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      if (timeoutRef.current !== null) clearTimeout(timeoutRef.current);
    };
  }, []);

  const copy = React.useCallback(async (text: string) => {
    if (timeoutRef.current !== null) clearTimeout(timeoutRef.current);

    let ok = false;
    try {
      if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
        try {
          await navigator.clipboard.writeText(text);
          ok = true;
        } catch {
          // writeText rejected (permission denied, insecure context, …) —
          // fall through to the legacy execCommand path before giving up.
          ok = legacyCopy(text);
        }
      } else {
        // Clipboard API absent (non-HTTPS or old browser).
        ok = legacyCopy(text);
      }
    } catch {
      ok = false;
    }

    // Component unmounted while the async copy was in flight — bail out before
    // touching state.
    if (!isMountedRef.current) return;

    if (ok) {
      setStatus("copied");
      setErrorMessage(null);
      timeoutRef.current = setTimeout(() => {
        if (!isMountedRef.current) return;
        setStatus("idle");
      }, RESET_DELAY_MS);
    } else {
      setStatus("error");
      setErrorMessage("Copie manuelle : sélectionne la phrase et appuie sur Ctrl+C");
      timeoutRef.current = setTimeout(() => {
        if (!isMountedRef.current) return;
        setStatus("idle");
        setErrorMessage(null);
      }, RESET_DELAY_MS);
    }
  }, []);

  return { copy, status, errorMessage };
}
