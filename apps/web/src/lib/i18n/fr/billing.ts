/**
 * FR i18n strings for premium subscription — Story 5.3.
 */
export const BILLING_COPY = {
  premium: {
    pageTitle: "Passer en premium",
    price: "10,99 € / mois",
    tagline: "Débloque l'envoi anticipé de ton profil aux écoles partenaires.",
    benefits: [
      "Envoi anticipé de ton profil aux écoles partenaires",
      "Signal d'admission précoce sous 7 jours",
      "5 envois par mois inclus",
    ],
    ctaLabel: "Passer en premium — 10,99 €/mois",
    ctaLoading: "Redirection vers le paiement…",
    errorMessage:
      "Impossible de démarrer le paiement pour le moment. Réessaie dans quelques instants.",
    alreadyPremium: "Tu es déjà abonné premium.",
    manageLink: "Gérer mon abonnement",
  },
  success: {
    pageTitle: "Abonnement activé !",
    message: "Ton abonnement premium est actif. Un email de confirmation t'a été envoyé.",
    ctaLabel: "Retour à l'accueil",
  },
  settings: {
    title: "Abonnement",
    tierFree: "Freemium",
    tierPremium: "Premium",
    statusActive: "Actif",
    statusPastDue: "Paiement en retard",
    statusCancelled: "Annulé",
    renewsOn: (date: string) => `Renouvellement le ${date}`,
    endsOn: (date: string) => `Se termine le ${date} — tu gardes l'accès premium jusque-là.`,
    upgradeCta: "Passer en premium",
    cancelCta: "Annuler mon abonnement",
    cancelDialog: {
      title: "Annuler ton abonnement premium ?",
      description:
        "Tu conserves l'accès premium jusqu'à la fin de ta période payée en cours. Ensuite, ton compte repasse en freemium.",
      duration: "Jusqu'à la fin de la période payée en cours",
      beneficiary: "Path-Advisor",
      acceptLabel: "Confirmer l'annulation",
      refuseLabel: "Garder mon abonnement",
      errorMessage: "L'annulation a échoué. Réessaie dans quelques instants.",
    },
    cancelSuccessInline: "Annulation programmée.",
    alreadyScheduled: "Ton abonnement est déjà programmé pour se terminer.",
  },
} as const;
