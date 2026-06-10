/**
 * FR i18n strings for the access-list surface — Story 1.9 §AC9.
 *
 * Co-located dict (mirrors `auth-forbidden` pattern from Story 1.7). Every
 * user-facing string in `acces-tiers/page.tsx` and `tier-access-card.tsx`
 * lives here — no inline French strings allowed elsewhere.
 */
export const ACCESS_LIST_COPY = {
  pageTitle: "Accès tiers",
  pageDescription:
    "Voici la liste des personnes et institutions qui ont actuellement accès à ton profil. Tu peux contrôler à tout moment qui voit quoi.",
  emptyState:
    "Aucun tiers n'a accès à ton profil pour le moment. Tu peux inviter un parent, accepter une demande de ta conseillère, ou envoyer ton profil à une école.",
  tierBadge: {
    parent: "Parent",
    school: "École",
    counselor: "Conseillère",
  } as const,
  visibleSectionTitle: "Données visibles",
  maskedSectionTitle: "Données masquées",
  grantedAtLabel: "Accès accordé",
  revokeButtonLabel: "Révoquer l'accès",
  revokeNotYetAvailable: "Révocation à venir",
  dataAreaLabels: {
    metiers_explores: "Métiers explorés",
    parcours_sauvegardes: "Parcours sauvegardés",
    recommandations: "Recommandations métiers",
    parcoursup_voeux: "Vœux Parcoursup",
    bulletins_detailles: "Bulletins détaillés",
    appreciations_enseignants: "Appréciations enseignants",
    motivation_libre: "Lettre de motivation",
  } as const,
};

export type DataAreaKey = keyof typeof ACCESS_LIST_COPY.dataAreaLabels;
export type TierType = keyof typeof ACCESS_LIST_COPY.tierBadge;
