/**
 * `/cohorte/eleves/[studentId]` — Story 6.8 (vue profil individuel élève,
 * côté conseillère).
 *
 * Gated by a granted `CounselorConsent` (Story 6.7) — the backend returns
 * 403 (`ConsentNotGranted`) otherwise, rendered here as a "consentement
 * requis" fallback rather than a generic error page, since a counselor
 * without consent is an expected, recoverable state (they just requested
 * it and it's still pending, or haven't asked yet).
 *
 * "Vœux en construction" is intentionally not rendered (§scope decision,
 * `apps/establishments/services/counselor_profile.py` — no such data model
 * exists yet).
 */
import Link from "next/link";
import { notFound } from "next/navigation";

import { CounselorNotesPanel } from "@/components/features/establishments/counselor-notes-panel";
import { ApiError } from "@/lib/api/client";
import {
  buildInterviewSheetPdfUrl,
  fetchCounselorNotes,
  fetchCounselorStudentProfile,
} from "@/lib/api/counselor-profile";

export const metadata = { title: "Profil élève — Path Advisor" };

export default async function CounselorStudentProfilePage({
  params,
}: {
  params: Promise<{ studentId: string }>;
}) {
  const { studentId } = await params;

  let profile;
  let notes;
  try {
    [profile, notes] = await Promise.all([
      fetchCounselorStudentProfile(studentId),
      fetchCounselorNotes(studentId),
    ]);
  } catch (err) {
    if (err instanceof ApiError && err.status === 403) {
      return (
        <main className="mx-auto max-w-2xl px-4 py-8">
          <Link href="/cohorte" className="text-body-sm text-primary hover:underline">
            ← Retour à la cohorte
          </Link>
          <h1 className="mb-3 mt-3 text-2xl font-bold">Consentement requis</h1>
          <p className="text-body-sm text-text-muted">
            Vous n&apos;avez pas encore l&apos;accord de cet élève pour consulter son profil
            individuel. Demandez son consentement depuis la fiche cohorte.
          </p>
        </main>
      );
    }
    if (err instanceof ApiError && err.status === 404) {
      notFound();
      return null;
    }
    throw err;
  }

  return (
    <main className="mx-auto max-w-4xl px-4 py-8">
      <Link href="/cohorte" className="text-body-sm text-primary hover:underline">
        ← Retour à la cohorte
      </Link>

      <div className="mb-6 mt-3 flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Profil élève</h1>
          <p className="text-body-sm text-text-subtle">
            {profile.cohort_name ?? "Cohorte inconnue"}
          </p>
        </div>
        <a
          href={buildInterviewSheetPdfUrl(studentId)}
          className="rounded-lg border border-border px-3 py-1.5 text-body-sm text-text hover:bg-card"
        >
          Exporter fiche entretien (PDF)
        </a>
      </div>

      <section className="mb-6 rounded-lg border border-border bg-card p-4">
        <h2 className="mb-3 text-h3 font-semibold text-text">Métiers — top recos</h2>
        {profile.metiers_top_recos.length === 0 ? (
          <p className="text-body-sm text-text-muted">Aucune recommandation pour l&apos;instant.</p>
        ) : (
          <ul className="flex flex-col gap-1">
            {profile.metiers_top_recos.map((m) => (
              <li
                key={m.metier_id ?? m.slug}
                className="flex justify-between border-b border-border py-1 text-body-sm"
              >
                <span>{m.name}</span>
                <span className="font-medium">{m.score}%</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="mb-6 rounded-lg border border-border bg-card p-4">
        <h2 className="mb-3 text-h3 font-semibold text-text">Mes paris (écoles sauvegardées)</h2>
        {profile.mes_paris.length === 0 ? (
          <p className="text-body-sm text-text-muted">Aucune école sauvegardée.</p>
        ) : (
          <ul className="flex flex-col gap-1">
            {profile.mes_paris.map((s) => (
              <li key={s.school_id} className="border-b border-border py-1 text-body-sm">
                {s.name} — {s.city}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="mb-6 rounded-lg border border-border bg-card p-4">
        <h2 className="mb-3 text-h3 font-semibold text-text">Activité récente</h2>
        <p className="text-body-sm text-text">
          Dernière connexion :{" "}
          {profile.activite_recente.derniere_connexion
            ? new Date(profile.activite_recente.derniere_connexion).toLocaleString("fr-FR")
            : "jamais"}
        </p>
      </section>

      <CounselorNotesPanel studentId={studentId} initialNotes={notes} />
    </main>
  );
}
