/** /admin/ecoles/[slug] — Story 9.2 (édition + historique/rollback). */
import { notFound } from "next/navigation";

import { fetchAdminSchool } from "@/lib/api/admin-schools";

import { SchoolForm } from "../school-form";

export const metadata = { title: "Fiche école — Back-office" };

export default async function AdminEcoleEditPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  let school;
  try {
    school = await fetchAdminSchool(slug);
  } catch {
    notFound();
  }
  return <SchoolForm initial={school} />;
}
