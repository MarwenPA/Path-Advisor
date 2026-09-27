"use client";

import * as React from "react";

/**
 * Shared ephemeral toast — Story 10.6.
 *
 * Extracted from the identical local copies in `ReportErrorButton` and
 * `ReviewRequestButton` (Story 3.8/3.7), now also used by `SideFlow` for its
 * resolution toast. State + aria-live only, no external dependency, no
 * portal: each consumer renders its own `<Toast>` so stacking stays a
 * non-problem (one ephemeral status message at a time per flow).
 */
export function useToast() {
  const [message, setMessage] = React.useState<string | null>(null);
  const tidRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  React.useEffect(() => {
    return () => {
      if (tidRef.current !== null) clearTimeout(tidRef.current);
    };
  }, []);

  const showToast = React.useCallback((msg: string, durationMs = 4000) => {
    if (tidRef.current !== null) clearTimeout(tidRef.current);
    setMessage(msg);
    tidRef.current = setTimeout(() => {
      setMessage(null);
      tidRef.current = null;
    }, durationMs);
  }, []);

  return { message, showToast };
}

/** Renders nothing while `message` is null. */
export function Toast({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed bottom-6 left-1/2 z-50 -translate-x-1/2 rounded-md bg-foreground px-4 py-3 text-sm text-background shadow-lg"
    >
      {message}
    </div>
  );
}
