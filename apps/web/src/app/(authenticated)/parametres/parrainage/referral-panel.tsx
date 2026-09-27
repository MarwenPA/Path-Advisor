"use client";

/**
 * ReferralPanel — Story 10.5. Le lien opaque (jamais l'usr_ id), un bouton
 * de partage NATIF (`navigator.share` — WhatsApp/Instagram/SMS via la
 * feuille de partage du système) avec repli copie, et le compteur sobre.
 */
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Toast, useToast } from "@/components/ui/toast";
import { fetchReferralInfo, type ReferralInfo } from "@/lib/api/auth";

export function ReferralPanel() {
  const [info, setInfo] = useState<ReferralInfo | null>(null);
  const [error, setError] = useState(false);
  const { message: toastMessage, showToast } = useToast();

  useEffect(() => {
    let cancelled = false;
    fetchReferralInfo()
      .then((data) => {
        if (!cancelled) setInfo(data);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return (
      <p role="alert" className="text-body text-danger">
        Ton lien n&apos;a pas pu être chargé. Réessaie dans un instant.
      </p>
    );
  }
  if (!info) return <p className="text-body-sm text-text-muted">Chargement de ton lien…</p>;

  const share = async () => {
    const payload = {
      title: "Path-Advisor",
      text: "J'explore mes pistes d'orientation sur Path-Advisor — rejoins-moi :",
      url: info.url,
    };
    try {
      if (typeof navigator.share === "function") {
        await navigator.share(payload);
        return;
      }
      throw new Error("no-share");
    } catch (err) {
      // Partage annulé par l'utilisateur : silence. Non supporté : copie.
      if (err instanceof Error && err.name === "AbortError") return;
      try {
        await navigator.clipboard.writeText(info.url);
        showToast("Lien copié — colle-le où tu veux.");
      } catch {
        showToast("Copie impossible — sélectionne le lien à la main.");
      }
    }
  };

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(info.url);
      showToast("Lien copié — colle-le où tu veux.");
    } catch {
      showToast("Copie impossible — sélectionne le lien à la main.");
    }
  };

  return (
    <section className="flex flex-col gap-4 rounded-lg border border-border bg-card p-6">
      <Toast message={toastMessage} />
      <div className="flex flex-col gap-1">
        <span className="text-xs uppercase tracking-wide text-text-muted">Ton lien</span>
        <code className="break-all rounded-md bg-bg-2 px-3 py-2 text-body-sm text-text">
          {info.url}
        </code>
      </div>
      <div className="flex flex-wrap gap-2">
        <Button type="button" onClick={() => void share()}>
          Partager
        </Button>
        <Button type="button" variant="outline" onClick={() => void copy()}>
          Copier le lien
        </Button>
      </div>
      <p className="text-body-sm text-text-muted">
        {info.referred_count === 0
          ? "Personne n'a encore utilisé ton lien — ça viendra."
          : `${info.referred_count} pote(s) ont rejoint Path-Advisor grâce à toi.`}
      </p>
    </section>
  );
}
