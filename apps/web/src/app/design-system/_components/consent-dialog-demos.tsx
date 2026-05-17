"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { ConsentDialog, type ConsentMeta } from "@/components/ui/consent-dialog";

type DemoCase = {
  key: string;
  trigger: string;
  triggerVariant?: "default" | "outline" | "destructive";
  title: string;
  description: string;
  dataMentioned: string[];
  duration: string;
  beneficiary: string;
  acceptLabel?: string;
  isAcceptDestructive?: boolean;
};

const CASES: DemoCase[] = [
  {
    key: "parental",
    trigger: "Parental < 15 ans",
    title: "Autorisation d'inscription de votre enfant",
    description:
      "Path-Advisor demande votre accord pour que votre enfant Mehdi (14 ans) puisse utiliser le service. Vous pouvez retirer cette autorisation à tout moment.",
    dataMentioned: [
      "Profil scolaire (niveau, filière, spécialités)",
      "Métiers explorés et parcours sauvegardés",
      "Adresse email de l'enfant",
    ],
    duration: "Tant que l'inscription est active ; révocable à tout moment",
    beneficiary: "Mehdi, 14 ans (votre enfant)",
  },
  {
    key: "counselor",
    trigger: "Conseillère B2B",
    title: "Donner accès à votre conseillère d'orientation",
    description:
      "Mme Dupont pourra consulter les éléments listés ci-dessous pour préparer votre prochain entretien. Elle n'aura jamais accès à vos bulletins ni à vos motivations libres.",
    dataMentioned: [
      "Métiers recommandés",
      "Parcours sauvegardés",
      "Échéances Parcoursup pertinentes",
    ],
    duration: "12 mois ; révocable à tout moment depuis Paramètres → Accès tiers",
    beneficiary: "Mme Dupont, Lycée Henri-IV",
  },
  {
    key: "school",
    trigger: "École partenaire",
    title: "Envoyer votre profil à HEC Paris",
    description:
      "HEC Paris recevra une copie de votre profil pour vous proposer une réponse anticipée. La révocation reste possible, mais l'école conservera les réponses qu'elle aura émises avant la révocation.",
    dataMentioned: [
      "Nom, prénom, niveau scolaire actuel",
      "Profil scolaire complet (bulletins + spécialités)",
      "Motivation libre (modérée a priori)",
      "Parcours visé et projet professionnel",
    ],
    duration: "Une seule consultation par l'école ; révocable sans rétroactivité",
    beneficiary: "HEC Paris (école partenaire)",
    acceptLabel: "Envoyer mon profil",
  },
  {
    key: "destructive",
    trigger: "Suppression de compte",
    triggerVariant: "outline",
    title: "Supprimer définitivement votre compte",
    description:
      "Cette action est irréversible après 30 jours. Vous perdrez vos métiers explorés, vos parcours sauvegardés et toutes vos données. Le journal d'audit pseudonymisé reste conservé 3 ans pour conformité légale.",
    dataMentioned: [
      "Profil complet, recommandations, parcours sauvegardés",
      "Historique des envois anticipés",
      "Compte de paiement Stripe (si premium)",
    ],
    duration:
      "Délai de grâce 30 jours (réversible par contact support) ; effacement définitif après",
    beneficiary: "Personne — suppression au profit de votre droit à l'oubli (RGPD art. 17)",
    acceptLabel: "Supprimer mon compte",
    isAcceptDestructive: true,
  },
];

export function ConsentDialogDemos() {
  const [openKey, setOpenKey] = useState<string | null>(null);

  const handleAccept = (caseKey: string) => async (meta: ConsentMeta) => {
    console.info(`[consent] accepted (${caseKey})`, meta);
    setOpenKey(null);
  };

  const handleRefuse = (caseKey: string) => () => {
    console.info(`[consent] refused (${caseKey})`);
  };

  return (
    <ul className="grid gap-3 sm:grid-cols-2">
      {CASES.map((demo) => (
        <li key={demo.key}>
          <Button
            variant={demo.triggerVariant ?? "outline"}
            onClick={() => setOpenKey(demo.key)}
            className="w-full justify-start"
          >
            {demo.trigger}
          </Button>
          <ConsentDialog
            open={openKey === demo.key}
            onOpenChange={(next) => setOpenKey(next ? demo.key : null)}
            title={demo.title}
            description={demo.description}
            dataMentioned={demo.dataMentioned}
            duration={demo.duration}
            beneficiary={demo.beneficiary}
            acceptLabel={demo.acceptLabel}
            isAcceptDestructive={demo.isAcceptDestructive}
            onAccept={handleAccept(demo.key)}
            onRefuse={handleRefuse(demo.key)}
          />
        </li>
      ))}
    </ul>
  );
}
