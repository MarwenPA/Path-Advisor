/** /admin/ecoles/nouvelle — Story 9.2 (création). */
import { SchoolForm } from "../school-form";

export const metadata = { title: "Nouvelle école — Back-office" };

export default function AdminEcoleCreatePage() {
  return <SchoolForm initial={null} />;
}
