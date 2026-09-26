/** /admin/ecoles — Story 9.2 (liste + filtres + import CSV). */
import { SchoolsTable } from "./schools-table";

export const metadata = { title: "Référentiel écoles — Back-office" };

export default function AdminEcolesPage() {
  return <SchoolsTable />;
}
