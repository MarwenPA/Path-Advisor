"use client";

import * as React from "react";
import { Flag } from "lucide-react";
import { useTranslations } from "next-intl";

import { cn } from "@/lib/utils";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Toast, useToast } from "@/components/ui/toast";
import { useReportProfessionError } from "@/hooks/useReportProfessionError";
import { ReportErrorForm } from "./ReportErrorForm";

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
  const t = useTranslations("ficheMetier.reportError");
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
        showToast(t("successToast"));
      },
      onError: () => {
        setSubmitError(t("submitFailed"));
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
      aria-label={isReported ? t("triggerReportedAria") : t("triggerAria")}
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
      {isReported ? t("triggerReported") : t("trigger")}
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
      <Toast message={toastMessage} />

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
              <SheetTitle>{t("dialogTitle")}</SheetTitle>
            </SheetHeader>
            {formContent}
          </SheetContent>
        </Sheet>
      ) : (
        /* Desktop: dialog centré */
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>{t("dialogTitle")}</DialogTitle>
            </DialogHeader>
            {formContent}
          </DialogContent>
        </Dialog>
      )}
    </>
  );
}
