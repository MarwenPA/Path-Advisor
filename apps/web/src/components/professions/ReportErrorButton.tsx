"use client";

import * as React from "react";
import { Flag } from "lucide-react";

import { cn } from "@/lib/utils";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { useReportProfessionError } from "@/hooks/useReportProfessionError";
import { ReportErrorForm } from "./ReportErrorForm";

// ─── Simple toast using state + aria-live (no external dep) ──────────────────

function useToast() {
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

// ─── Mobile detection ─────────────────────────────────────────────────────────
// Server snapshot returns false (desktop) so SSR and initial client render agree,
// avoiding hydration mismatch. The client snapshot reads the real viewport.

function useIsMobile() {
  return React.useSyncExternalStore(
    (cb) => {
      const mq = window.matchMedia("(max-width: 1023px)");
      mq.addEventListener("change", cb);
      return () => mq.removeEventListener("change", cb);
    },
    () => window.matchMedia("(max-width: 1023px)").matches,
    () => false,
  );
}

// ─── Props ────────────────────────────────────────────────────────────────────

export interface ReportErrorButtonProps {
  professionSlug: string;
  professionName: string;
  className?: string;
}

// ─── Main component ───────────────────────────────────────────────────────────

export function ReportErrorButton({
  professionSlug,
  professionName,
  className,
}: ReportErrorButtonProps) {
  const [open, setOpen] = React.useState(false);
  const [reported, setReported] = React.useState(false);
  const [submitError, setSubmitError] = React.useState<string | null>(null);

  const isMobile = useIsMobile();
  const { message: toastMessage, showToast } = useToast();
  const { mutate, isPending } = useReportProfessionError(professionSlug);

  function handleSubmit(
    payload: Parameters<ReturnType<typeof useReportProfessionError>["mutate"]>[0],
  ) {
    setSubmitError(null);
    mutate(payload, {
      onSuccess: () => {
        setOpen(false);
        setReported(true);
        showToast("Merci, ton signalement a été pris en compte");
      },
      onError: () => {
        setSubmitError("Envoi échoué — réessaie dans quelques instants");
      },
    });
  }

  const isReported = reported;

  const triggerButton = (
    <button
      type="button"
      onClick={() => {
        if (!isReported) setOpen(true);
      }}
      disabled={isReported}
      aria-label={isReported ? "Erreur déjà signalée" : "Signaler une erreur sur cette fiche"}
      className={cn(
        "inline-flex items-center gap-1.5 text-sm transition-colors",
        isReported
          ? "cursor-default text-muted-foreground"
          : "rounded-sm text-muted-foreground hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        className,
      )}
    >
      <Flag
        className={cn("size-4 shrink-0", isReported ? "fill-muted-foreground" : "")}
        aria-hidden
      />
      {isReported ? "Signalé" : "Signaler une erreur"}
    </button>
  );

  const formContent = (
    <ReportErrorForm
      professionName={professionName}
      isSubmitting={isPending}
      submitError={submitError}
      onSubmit={handleSubmit}
      onCancel={() => setOpen(false)}
    />
  );

  return (
    <>
      {triggerButton}

      {/* Toast — aria-live so screen readers announce it (AC8) */}
      {toastMessage && (
        <div
          role="status"
          aria-live="polite"
          className="fixed bottom-6 left-1/2 z-50 -translate-x-1/2 rounded-md bg-foreground px-4 py-3 text-sm text-background shadow-lg"
        >
          {toastMessage}
        </div>
      )}

      {/* Mobile: bottom sheet */}
      {isMobile ? (
        <Sheet open={open} onOpenChange={setOpen}>
          <SheetContent
            side="bottom"
            className="max-h-[90dvh] overflow-y-auto rounded-t-xl px-6 py-6"
          >
            {/* Handle visuel */}
            <div className="mx-auto mb-4 h-1 w-10 rounded-full bg-border" aria-hidden />
            <SheetHeader className="mb-4">
              <SheetTitle>Signaler une erreur sur cette fiche</SheetTitle>
            </SheetHeader>
            {formContent}
          </SheetContent>
        </Sheet>
      ) : (
        /* Desktop: dialog centré */
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Signaler une erreur sur cette fiche</DialogTitle>
            </DialogHeader>
            {formContent}
          </DialogContent>
        </Dialog>
      )}
    </>
  );
}
