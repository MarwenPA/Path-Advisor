/**
 * FR i18n strings for the parent dashboard — Story 6.2 §T5.2
 * (pattern mirrors `family.ts`, Story 6.1).
 */
export const PARENT_COPY = {
  pageTitle: "Espace parent",
  pageDescription:
    "Suis le cheminement d'orientation de ton enfant : les métiers qu'il explore, les parcours qu'il sauvegarde et leur coût estimé. Les bulletins et appréciations restent privés.",
  childrenEmptyState:
    "Aucun enfant lié pour le moment. Ton enfant doit t'inviter depuis son compte.",
  childrenListTitle: "Mes enfants",
  viewDashboardLabel: "Voir le tableau de bord",
  sections: {
    professions: {
      title: "Métiers explorés",
      empty: "Aucun métier exploré pour le moment.",
    },
    mesParis: {
      title: "Mes paris",
      empty: "Aucun parcours sauvegardé pour le moment.",
    },
    costs: {
      title: "Coûts estimés des parcours sauvegardés",
      total: "Coût total estimé",
      perYear: (min: number, max: number) => (min === max ? `${min} €` : `${min} – ${max} €`),
      free: "Gratuit",
      unknown: "Coût non communiqué",
    },
  },
  privacyNote:
    "Tu ne vois jamais les bulletins ni les appréciations des enseignants de ton enfant.",
  // Dedicated detail pages (AC2, code review 2026-08).
  metierDetail: {
    backLabel: "Retour au tableau de bord",
    dailyRoutineTitle: "Une journée type",
    prospectsTitle: "Débouchés",
    salaryLabel: "Salaire médian",
    salaryUnknown: "Non communiqué",
  },
  ecoleDetail: {
    backLabel: "Retour au tableau de bord",
    formationsTitle: "Formations proposées",
    formationsEmpty: "Aucune formation référencée pour cette école.",
    costLabel: "Coût annuel",
  },
} as const;
