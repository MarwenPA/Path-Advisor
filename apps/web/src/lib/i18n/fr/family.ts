/**
 * FR i18n strings for the "Mes proches" / parent-invitation surfaces —
 * Story 6.1 §T7.5 (pattern mirrors `access-list.ts`, Story 1.9 §AC9).
 */
export const FAMILY_COPY = {
  pageTitle: "Mes proches",
  pageDescription:
    "Invite un parent à créer un compte lié au tien. Il pourra suivre les métiers que tu explores et les parcours que tu sauvegardes — jamais tes bulletins ni tes appréciations.",
  inviteButtonLabel: "Inviter un parent",
  emptyState: "Tu n'as invité aucun parent pour le moment.",
  statusLabels: {
    pending: "En attente",
    accepted: "Accepté",
    expired: "Expirée",
    revoked: "Révoquée",
  } as const,
  resendButtonLabel: "Renvoyer",
  toastInvitationSent: (maskedEmail: string) => `Invitation envoyée à ${maskedEmail}`,
  form: {
    emailLabel: "Email du parent",
    emailPlaceholder: "parent@exemple.fr",
    relationshipLabel: "Lien de parenté",
    relationshipOptions: {
      mere: "Mère",
      pere: "Père",
      tuteur: "Tuteur",
      autre: "Autre",
    } as const,
    messageLabel: "Message personnalisé (optionnel)",
    messagePlaceholder: "Un petit mot pour ton parent...",
    messageMaxLength: 200,
    submitLabel: "Continuer",
  },
  consentDialog: {
    title: "Avant d'inviter ton parent",
    description:
      "Ton parent aura accès à certaines informations de ton profil Path-Advisor. Voici ce qu'il verra et ce qui restera privé.",
    dataMentioned: [
      "Visible pour ton parent : métiers explorés, parcours sauvegardés, coûts estimés",
      "Reste privé : bulletins détaillés, appréciations des enseignants, lettres de motivation",
    ],
    duration: "Jusqu'à ce que tu révoques son accès",
    beneficiary: "Ton parent (une fois qu'il aura créé son compte)",
    acceptLabel: "Envoyer l'invitation",
    refuseLabel: "Annuler",
  },
  errors: {
    alreadyPending:
      "Une invitation est déjà en attente pour cet email — tu peux la renvoyer depuis 'Mes proches'.",
    generic: "L'envoi de l'invitation a échoué. Réessaie dans un instant.",
  },
} as const;

export const PARENT_SIGNUP_COPY = {
  invalidLinkTitle: "Ce lien d'invitation n'est plus valide",
  invalidLinkDescription:
    "Ce lien a peut-être déjà été utilisé ou a expiré. Contacte l'élève qui t'a invité pour qu'il t'en envoie un nouveau, ou écris-nous.",
  contactSupportLabel: "Contacter le support",
  formTitle: "Crée ton compte parent",
  emailLabel: "Email",
  passwordLabel: "Mot de passe",
  firstNameLabel: "Prénom",
  lastNameLabel: "Nom",
  submitLabel: "Créer mon compte",
  emailTakenMessage:
    "Un compte existe déjà avec cet email — connecte-toi puis accepte l'invitation depuis ton compte.",
  loginCta: "Se connecter",
} as const;
