/** /admin/audit-ml — Story 9.6 (drift KS, biais sous-populations, alertes). */
import { MlAuditDashboard } from "./ml-audit-dashboard";

export const metadata = { title: "Audit ML — Back-office" };

export default function AdminAuditMlPage() {
  return <MlAuditDashboard />;
}
