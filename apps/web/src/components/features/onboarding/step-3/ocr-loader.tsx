"use client";

import { WifiOff } from "lucide-react";
import { useRouter } from "next/navigation";
import { useRef } from "react";

import { ScenarioLoader } from "@/components/ui/scenario-loader";
import { track } from "@/lib/analytics/events";

const OCR_PHRASES = [
  "On reçoit tes bulletins…",
  "On lit les notes…",
  "On identifie les appréciations…",
  "On vérifie tout ça…",
] as const;

type Props = {
  bulletinIds: string[];
  estimatedSeconds: number;
  ocrStatus: "pending" | "running" | "succeeded" | "failed" | "timeout" | undefined;
  isNetworkError: boolean;
  isError: boolean;
  isComplete: boolean;
  onManualFallback: () => void;
};

export function OCRLoader({
  bulletinIds: _bulletinIds,
  estimatedSeconds,
  isNetworkError,
  isError,
  isComplete,
  onManualFallback,
}: Props) {
  const router = useRouter();
  const fallbackCalledRef = useRef(false);

  function handleFallback() {
    if (fallbackCalledRef.current) return;
    fallbackCalledRef.current = true;
    track({ name: "onboarding_step3_ocr_manual_fallback", trigger: "overrun_button" });
    onManualFallback();
    router.push("/onboarding/step-4");
  }

  if (isNetworkError) {
    return (
      <div className="flex flex-col items-center gap-4 text-center py-8">
        <WifiOff className="size-8 text-[var(--color-text-muted)]" aria-hidden />
        <p className="text-[var(--text-body)] text-[var(--color-text-muted)]">
          On essaie de récupérer les résultats…
          <br />
          Vérifie ta connexion ou attends quelques secondes.
        </p>
        <button
          type="button"
          onClick={handleFallback}
          className="text-sm text-[var(--color-brand)] underline underline-offset-2"
        >
          Saisir à la main plutôt
        </button>
      </div>
    );
  }

  return (
    <ScenarioLoader
      phrases={OCR_PHRASES}
      estimatedSeconds={estimatedSeconds}
      context="ocr"
      isComplete={isComplete}
      isError={isError}
      onFallback={handleFallback}
      fallbackLabel="Saisir à la main plutôt"
    />
  );
}
