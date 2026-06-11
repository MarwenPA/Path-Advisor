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
  // Review P11 — copy referenced from the parent `/parametres/confidentialite`
  // page (was hardcoded there, AC9 i18n violation).
  parentSectionTitle: "Accès tiers",
  parentSectionDescription:
    "Voici la liste des personnes et institutions (parent, conseillère, école partenaire) qui ont actuellement accès à ton profil — avec ce qu'elles voient et ce qui leur reste masqué.",
  parentSectionCta: "Voir mes accès tiers",
  // Review P8 — inline success message after revocation (aria-live, SR-friendly).
  revokeSuccessInline: "Accès révoqué.",
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

/**
 * Per-tier `<ConsentDialog>` copy for the revocation flow — Story 1.10 §AC6.
 *
 * Each entry shapes the dialog the student sees before confirming revocation.
 * `description` explains the immediate consequence ; `duration` is the time
 * scope ("Définitif" — once revoked, the third party loses access immediately).
 * Wording is final — review with the UX writer before changing.
 */
export const REVOKE_DIALOG_COPY = {
  parent: {
    title: "Révoquer l'accès de ton parent",
    description:
      "Ton parent ne verra plus tes métiers explorés ni tes parcours sauvegardés. Ses paiements premium éventuels restent valides jusqu'à leur terme.",
    duration: "Effet immédiat — réversible si tu réinvites ton parent plus tard",
    acceptLabel: "Révoquer l'accès",
    refuseLabel: "Annuler",
    errorMessage:
      "La révocation n'a pas pu être enregistrée. Réessaie dans un instant ou contacte le support.",
  },
  school: {
    title: "Révoquer l'accès de l'école",
    description:
      "L'école perd l'accès à ta fiche profil immédiatement. Les réponses qu'elle a déjà émises restent dans ton historique.",
    duration: "Effet immédiat",
    acceptLabel: "Révoquer l'accès",
    refuseLabel: "Annuler",
    errorMessage:
      "La révocation n'a pas pu être enregistrée. Réessaie dans un instant ou contacte le support.",
  },
  counselor: {
    title: "Révoquer l'accès de ta conseillère",
    description:
      "Ta conseillère ne verra plus ton profil détaillé. Ses notes anonymisées dans son tableau de cohorte restent visibles pour elle.",
    duration: "Effet immédiat — réversible si tu réinvites ta conseillère plus tard",
    acceptLabel: "Révoquer l'accès",
    refuseLabel: "Annuler",
    errorMessage:
      "La révocation n'a pas pu être enregistrée. Réessaie dans un instant ou contacte le support.",
  },
} as const satisfies Record<
  TierType,
  {
    title: string;
    description: string;
    duration: string;
    acceptLabel: string;
    refuseLabel: string;
    errorMessage: string;
  }
>;
