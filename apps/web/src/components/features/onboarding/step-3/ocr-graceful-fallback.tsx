"use client";

import { useRouter } from "next/navigation";

import { GracefulFallback } from "@/components/ui/graceful-fallback";
import { track } from "@/lib/analytics/events";

type Props = {
  onManual: () => void;
  onRetry: () => void;
};

export function OCRGracefulFallback({ onManual, onRetry }: Props) {
  const router = useRouter();

  function handleManual() {
    track({ name: "onboarding_step3_ocr_manual_fallback", trigger: "graceful_fallback_cta" });
    onManual();
    router.push("/onboarding/step-4");
  }

  function handleLater() {
    router.push("/onboarding/step-3/later");
  }

  return (
    <GracefulFallback
      context="ocr"
      title="Ton bulletin a un format qu'on connaît pas encore"
      description="Pas grave. Saisis-le à la main — 5 champs et c'est bon. Tu pourras retenter avec une photo plus nette si tu veux."
      primary={{
        label: "Saisir à la main",
        onClick: handleManual,
      }}
      secondary={{
        label: "Réessayer avec une autre photo",
        onClick: onRetry,
      }}
      tertiary={{
        label: "Plus tard, je préfère explorer d'abord",
        onClick: handleLater,
      }}
    />
  );
}
