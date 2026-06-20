import Link from "next/link";
import { notFound } from "next/navigation";

import { FicheMetier } from "@/components/professions/FicheMetier";
import { ApiError } from "@/lib/api/client";
import { fetchProfession } from "@/lib/api/professions";

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  try {
    const profession = await fetchProfession(slug);
    return { title: `${profession.name} — Path Advisor` };
  } catch {
    return { title: "Fiche métier — Path Advisor" };
  }
}

export default async function MetierDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ score?: string; confidence?: string }>;
}) {
  const { slug } = await params;
  const { score: scoreStr, confidence } = await searchParams;

  let profession;
  try {
    profession = await fetchProfession(slug);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  }

  const score = scoreStr !== undefined ? parseInt(scoreStr, 10) : undefined;
  const confidenceLevel: "normal" | "indicative" | undefined =
    confidence === "low" ? "indicative" : confidence ? "normal" : undefined;

  return (
    <main className="mx-auto max-w-3xl px-4 py-6">
      <Link
        href="/mes-metiers"
        className="hover:text-text-primary mb-4 flex items-center gap-1 text-body-sm text-text-muted"
      >
        ← Mes métiers
      </Link>
      <FicheMetier
        profession={profession}
        score={Number.isFinite(score) ? score : undefined}
        confidenceLevel={confidenceLevel}
      />
    </main>
  );
}
