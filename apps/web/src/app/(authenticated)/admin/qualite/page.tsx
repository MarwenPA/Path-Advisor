/**
 * /admin/qualite — Story 10.3 (FR-FF3). Tableau de qualité éditoriale du
 * référentiel : couverture vs cibles FR48, fraîcheur, files à traiter,
 * tendances 6 mois. Guard path_admin hérité du préfixe /admin.
 */
import { QualityDashboard } from "./quality-dashboard";

export const metadata = { title: "Qualité référentiel — Back-office" };

export default function AdminQualitePage() {
  return <QualityDashboard />;
}
