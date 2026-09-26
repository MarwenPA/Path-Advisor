/** /admin/metiers/nouveau — Story 9.1 AC1 (création). */
import { ProfessionForm } from "../profession-form";

export const metadata = { title: "Nouveau métier — Back-office" };

export default function AdminMetierCreatePage() {
  return <ProfessionForm initial={null} />;
}
