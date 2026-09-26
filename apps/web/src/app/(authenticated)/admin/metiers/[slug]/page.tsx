/**
 * /admin/metiers/[slug] — Story 9.1 AC2/AC3 (édition + historique/rollback).
 * Server-fetched initial state (any editorial status), client form.
 */
import { notFound } from "next/navigation";

import { fetchAdminProfession } from "@/lib/api/admin-professions";

import { ProfessionForm } from "../profession-form";

export const metadata = { title: "Fiche métier — Back-office" };

export default async function AdminMetierEditPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  let profession;
  try {
    profession = await fetchAdminProfession(slug);
  } catch {
    notFound();
  }
  return <ProfessionForm initial={profession} />;
}
