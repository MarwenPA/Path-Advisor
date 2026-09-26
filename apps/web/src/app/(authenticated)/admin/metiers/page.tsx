/**
 * /admin/metiers — Story 9.1 AC1 (liste + recherche + tri + filtre statut).
 * Client-fetched: the table drives its own query params against the admin
 * API (`IsPathAdmin` + MFA re-checked server-side on every call).
 */
import { ProfessionsTable } from "./professions-table";

export const metadata = { title: "Référentiel métiers — Back-office" };

export default function AdminMetiersPage() {
  return <ProfessionsTable />;
}
