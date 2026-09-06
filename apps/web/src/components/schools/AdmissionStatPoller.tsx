"use client";

/**
 * <AdmissionStatPoller> — Story 5.8 AC3.
 *
 * Wraps <CarteAdmission> with a 30s poll (ADD-8 — no WebSocket in the MVP)
 * so a student looking at a school's fiche the moment the school responds
 * sees the "+N pts" badge appear in place, no manual refresh needed.
 * <CarteAdmission> already has its own fade-in animation on the badge
 * (`UpdateBadge`, Story 4.2) — this component only supplies fresh data.
 */
import { useEffect, useState } from "react";

import { fetchAdmissionStat, type AdmissionStat } from "@/lib/api/schools";

import { CarteAdmission } from "./CarteAdmission";

const POLL_INTERVAL_MS = 30_000;

export interface AdmissionStatPollerProps {
  initialStat: AdmissionStat;
  schoolSlug: string;
  schoolName: string;
  variant?: "large" | "medium" | "small" | "export";
}

export function AdmissionStatPoller({
  initialStat,
  schoolSlug,
  schoolName,
  variant = "medium",
}: AdmissionStatPollerProps) {
  const [stat, setStat] = useState(initialStat);

  useEffect(() => {
    let cancelled = false;
    const interval = setInterval(async () => {
      try {
        const fresh = await fetchAdmissionStat(schoolSlug);
        if (!cancelled) setStat(fresh);
      } catch {
        // A transient poll failure just keeps the last known value —
        // no error UI for a background refresh.
      }
    }, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [schoolSlug]);

  return (
    <CarteAdmission
      admissionStat={stat}
      variant={variant}
      schoolName={schoolName}
      schoolSlug={schoolSlug}
    />
  );
}
