import { notFound } from "next/navigation";
import { ApiError } from "@/lib/api/client";
import { fetchSchool } from "@/lib/api/schools";
import { FicheEcole } from "@/components/schools/FicheEcole";

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  try {
    const school = await fetchSchool(slug);
    return { title: `${school.name} — Path Advisor` };
  } catch {
    return { title: "École — Path Advisor" };
  }
}

export default async function SchoolPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  let school;
  try {
    school = await fetchSchool(slug);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-6">
      <FicheEcole school={school} variant="expanded" />
    </main>
  );
}
