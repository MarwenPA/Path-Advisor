"use client";

/**
 * <OutreachSection> — Story 5.4 §AC1/AC3 (+ Story 5.11 paywall).
 *
 * Client wrapper on `/schools/[slug]` that decides, based on the current
 * user's subscription + monthly quota:
 * - not premium → `<PaywallContextuel>` (Story 5.11's generic component).
 * - premium, quota available → <SendOutreachButton>.
 * - premium, quota exhausted → the non-anxiogenic AC3 copy, no button.
 *
 * Fetches on mount rather than being passed server-side props: keeps the
 * (already Server Component) school page simple, and this section degrades
 * to "nothing" on any fetch error rather than blocking the page render.
 */
import { useEffect, useState } from "react";

import { PaywallContextuel } from "@/components/features/premium/paywall-contextuel";
import { fetchCurrentUser, type CurrentUser } from "@/lib/api/auth";
import { fetchOutreachQuota, type OutreachQuota } from "@/lib/api/outreach";
import { fetchRecommendations, type ScoredProfession } from "@/lib/api/recommendations";

import { SendOutreachButton } from "./send-outreach-button";

export interface OutreachSectionProps {
  schoolSlug: string;
  schoolName: string;
}

export function OutreachSection({ schoolSlug, schoolName }: OutreachSectionProps) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [quota, setQuota] = useState<OutreachQuota | null>(null);
  const [professions, setProfessions] = useState<ScoredProfession[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchCurrentUser()
      .then((u) => {
        if (cancelled) return;
        setUser(u);
        if (!u.is_premium) {
          setLoaded(true);
          return;
        }
        Promise.allSettled([fetchOutreachQuota(), fetchRecommendations()]).then(
          ([quotaResult, recoResult]) => {
            if (cancelled) return;
            if (quotaResult.status === "fulfilled") setQuota(quotaResult.value);
            if (recoResult.status === "fulfilled") {
              setProfessions(
                Array.isArray(recoResult.value?.results) ? recoResult.value.results : [],
              );
            }
            setLoaded(true);
          },
        );
      })
      .catch(() => setLoaded(true));
    return () => {
      cancelled = true;
    };
  }, []);

  if (!loaded || !user) return null;

  if (!user.is_premium) {
    return (
      <PaywallContextuel
        feature="envoi-anticipe"
        title="Envoyer ton profil aux écoles est une feature premium"
        description="Les élèves premium peuvent envoyer leur profil en avant-première aux écoles partenaires, avant les résultats Parcoursup."
        benefits={[
          "5 envois par mois vers les écoles de ton choix",
          "Un retour direct de l'école (intéressant, entretien...)",
          "Un impact potentiel sur ta stat d'admission",
        ]}
      >
        <span className="cursor-pointer text-body-sm text-primary hover:underline">
          Passe en premium
        </span>{" "}
        <span className="text-body-sm text-text-muted">
          pour envoyer ton profil à cette école en avant-première.
        </span>
      </PaywallContextuel>
    );
  }

  if (quota && quota.remaining <= 0) {
    return (
      <p className="text-body-sm text-text-muted">
        Tu as utilisé tes 5 envois ce mois — ta limite repart le 1er du mois prochain.
      </p>
    );
  }

  if (professions.length === 0) return null;

  return (
    <SendOutreachButton schoolSlug={schoolSlug} schoolName={schoolName} professions={professions} />
  );
}
