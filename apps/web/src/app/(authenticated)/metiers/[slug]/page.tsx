import Link from "next/link";
import { notFound } from "next/navigation";

import { ApiError } from "@/lib/api/client";
import { fetchProfession } from "@/lib/api/professions";
import type { SignalContributif } from "@/lib/api/recommendations";

import { FicheMetierClient } from "./FicheMetierClient";

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  try {
    const profession = await fetchProfession(slug);
    return { title: `${profession.name} — Path Advisor` };
  } catch {
    return { title: "Fiche métier — Path Advisor" };
  }
}

function parseSignals(raw: string | undefined): SignalContributif[] {
  if (!raw) return [];
  try {
    const parsed = JSON.parse(decodeURIComponent(raw));
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(
      (s) =>
        typeof s === "object" &&
        s !== null &&
        typeof s.signal === "string" &&
        typeof s.contribution === "number" &&
        typeof s.weight === "number",
    );
  } catch {
    return [];
  }
}

export default async function MetierDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ score?: string; confidence?: string; signals?: string }>;
}) {
  const { slug } = await params;
  const { score: scoreStr, confidence, signals: rawSignals } = await searchParams;

  let profession;
  try {
    profession = await fetchProfession(slug);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  }

  const score = scoreStr !== undefined ? parseInt(scoreStr, 10) : undefined;
  const VALID_CONFIDENCE = new Set(["low", "medium", "high"]);
  const rawConfidence =
    confidence && VALID_CONFIDENCE.has(confidence)
      ? (confidence as "low" | "medium" | "high")
      : undefined;
  const confidenceLevel: "normal" | "indicative" | undefined =
    rawConfidence === "low" ? "indicative" : rawConfidence ? "normal" : undefined;

  const signalsContributifs = parseSignals(rawSignals);

  return (
    <main className="mx-auto max-w-3xl px-4 py-6">
      <Link
        href="/mes-metiers"
        className="hover:text-text-primary mb-4 flex items-center gap-1 text-body-sm text-text-muted"
      >
        ← Mes métiers
      </Link>
      <FicheMetierClient
        profession={profession}
        score={Number.isFinite(score) ? score : undefined}
        confidenceLevel={confidenceLevel}
        drawerConfidenceLevel={rawConfidence}
        signalsContributifs={signalsContributifs}
      />
    </main>
  );
}
