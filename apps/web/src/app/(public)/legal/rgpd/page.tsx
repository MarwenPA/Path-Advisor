import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Politique de confidentialité (RGPD) | Path-Advisor",
  description:
    "Comment Path-Advisor collecte, traite et protège tes données personnelles. Conformité RGPD, durées de conservation, et tes droits.",
};

export const dynamic = "force-static";

const Placeholder = ({ children }: { children: React.ReactNode }) => (
  <mark className="bg-warning/20 px-1 font-medium">{children}</mark>
);

export default function RgpdPolicyPage() {
  return (
    <main className="flex flex-1 flex-col items-center bg-bg px-4 py-12">
      <article className="prose-tokens flex w-full max-w-3xl flex-col gap-6">
        <p
          role="note"
          className="border-l-4 border-warning bg-warning/10 p-4 text-body-sm text-text"
        >
          ⚠️ Cette page contient des sections marquées{" "}
          <Placeholder>[À DÉFINIR avant production]</Placeholder>. Ne pas déployer en l’état dans un
          environnement non-local — les mentions légales définitives doivent être validées par un
          juriste / DPO avant mise en production.
        </p>

        <header className="flex flex-col gap-2">
          <h1 className="text-display-2 font-semibold text-text md:text-display-2-desktop">
            Politique de confidentialité
          </h1>
          <p className="text-body text-text-muted">
            Cette politique décrit comment Path-Advisor collecte, traite et protège tes données
            personnelles, et comment tu peux exercer tes droits. Version applicable :{" "}
            <strong>2026-05-15</strong>.
          </p>
        </header>

        <nav aria-label="Sommaire" className="rounded-md border border-border p-4">
          <h2 className="mb-2 text-h3 font-semibold text-text md:text-h3-desktop">Sommaire</h2>
          <ol className="flex flex-col gap-1 text-body-sm">
            <li>
              <a className="text-brand underline" href="#responsable">
                1. Responsable du traitement
              </a>
            </li>
            <li>
              <a className="text-brand underline" href="#finalites">
                2. Finalités du traitement
              </a>
            </li>
            <li>
              <a className="text-brand underline" href="#base-legale">
                3. Base légale
              </a>
            </li>
            <li>
              <a className="text-brand underline" href="#donnees">
                4. Données collectées
              </a>
            </li>
            <li>
              <a className="text-brand underline" href="#conservation">
                5. Durées de conservation
              </a>
            </li>
            <li>
              <a className="text-brand underline" href="#droits">
                6. Tes droits RGPD
              </a>
            </li>
            <li>
              <a className="text-brand underline" href="#dpo">
                7. Contact DPO
              </a>
            </li>
            <li>
              <a className="text-brand underline" href="#cnil">
                8. Autorité de contrôle (CNIL)
              </a>
            </li>
            <li>
              <a className="text-brand underline" href="#mineurs">
                9. Inscription des moins de 15 ans
              </a>
            </li>
          </ol>
        </nav>

        <section id="responsable" className="flex flex-col gap-2">
          <h2 className="text-h2 font-semibold text-text md:text-h2-desktop">
            1. Responsable du traitement
          </h2>
          <p className="text-body">
            Le responsable du traitement des données personnelles collectées via Path-Advisor est{" "}
            <Placeholder>[Raison sociale à définir]</Placeholder>, dont le siège social est situé au{" "}
            <Placeholder>[Adresse postale à définir]</Placeholder>, France. Représenté par{" "}
            <Placeholder>[Représentant légal à définir]</Placeholder>.
          </p>
        </section>

        <section id="finalites" className="flex flex-col gap-2">
          <h2 className="text-h2 font-semibold text-text md:text-h2-desktop">
            2. Finalités du traitement
          </h2>
          <p className="text-body">Nous traitons tes données pour :</p>
          <ul className="list-inside list-disc text-body">
            <li>
              <strong>Fournir le service d’orientation</strong> — recommandations vocationnelles
              personnalisées, graphes de parcours, statistiques d’admission.
            </li>
            <li>
              <strong>Communication transactionnelle</strong> — vérification d’email,
              réinitialisation de mot de passe, notifications produit que tu choisis d’activer.
            </li>
            <li>
              <strong>Amélioration produit</strong> — analytics anonymisé (PostHog) pour comprendre
              comment le produit est utilisé. Tu peux refuser cette finalité à tout moment.
            </li>
          </ul>
        </section>

        <section id="base-legale" className="flex flex-col gap-2">
          <h2 className="text-h2 font-semibold text-text md:text-h2-desktop">3. Base légale</h2>
          <ul className="list-inside list-disc text-body">
            <li>
              <strong>Ton consentement explicite</strong>, recueilli lors de l’inscription via une
              case à cocher dédiée (preuve d’horodatage conservée).
            </li>
            <li>
              <strong>L’exécution du contrat</strong> qui nous lie (CGU), pour les traitements
              indispensables à la fourniture du service.
            </li>
          </ul>
        </section>

        <section id="donnees" className="flex flex-col gap-2">
          <h2 className="text-h2 font-semibold text-text md:text-h2-desktop">
            4. Catégories de données collectées
          </h2>
          <ul className="list-inside list-disc text-body">
            <li>
              <strong>Données d’identité</strong> : email, date de naissance, mot de passe (haché —
              jamais stocké en clair).
            </li>
            <li>
              <strong>Données scolaires</strong> (lorsque tu les renseignes) : bulletins, niveau,
              filière, spécialités, passions et intérêts.
            </li>
            <li>
              <strong>Données d’interaction</strong> : métiers consultés, écoles favorisées,
              parcours sauvegardés.
            </li>
            <li>
              <strong>Données techniques</strong> : adresse IP, type de navigateur, logs d’accès
              (limités à 90 jours).
            </li>
          </ul>
        </section>

        <section id="conservation" className="flex flex-col gap-2">
          <h2 className="text-h2 font-semibold text-text md:text-h2-desktop">
            5. Durées de conservation
          </h2>
          <ul className="list-inside list-disc text-body">
            <li>
              <strong>Compte actif</strong> : tant que tu utilises le service. Aucune limite de
              durée tant que ton compte est actif.
            </li>
            <li>
              <strong>Compte inactif &gt; 24 mois</strong> : un email d’avertissement est envoyé,
              puis suppression complète sous 30 jours en l’absence de réponse.
            </li>
            <li>
              <strong>Journal d’audit pseudonymisé</strong> : 3 ans après la suppression du compte,
              conformément à nos obligations légales.
            </li>
            <li>
              <strong>Bulletins scolaires originaux</strong> : supprimés immédiatement après
              extraction des données nécessaires aux recommandations (OCR), sauf si tu choisis de
              les conserver dans ton espace.
            </li>
          </ul>
        </section>

        <section id="droits" className="flex flex-col gap-2">
          <h2 className="text-h2 font-semibold text-text md:text-h2-desktop">6. Tes droits RGPD</h2>
          <p className="text-body">
            Conformément aux articles 15 à 22 du RGPD, tu disposes des droits suivants :
          </p>
          <ul className="list-inside list-disc text-body">
            <li>
              <strong>Droit d’accès</strong> : consulter toutes les données que nous détenons sur
              toi.
            </li>
            <li>
              <strong>Droit de rectification</strong> : corriger les informations inexactes.
            </li>
            <li>
              <strong>Droit à la portabilité</strong> : récupérer tes données dans un format
              structuré et lisible par machine.
            </li>
            <li>
              <strong>Droit à l’effacement</strong> (« droit à l’oubli ») : demander la suppression
              de l’intégralité de tes données.
            </li>
            <li>
              <strong>Droit d’opposition</strong> : t’opposer à certains traitements (notamment
              l’analytics produit).
            </li>
            <li>
              <strong>Droit à la limitation du traitement</strong>.
            </li>
            <li>
              <strong>
                Droit de ne pas faire l’objet d’une décision exclusivement automatisée
              </strong>{" "}
              (RGPD art. 22) : tu peux demander une revue humaine de toute recommandation IA.
            </li>
          </ul>
          <p className="text-body">
            Pour exercer ces droits, contacte notre DPO (section 7). Nous répondons dans un délai
            maximum de 30 jours.
          </p>
        </section>

        <section id="dpo" className="flex flex-col gap-2">
          <h2 className="text-h2 font-semibold text-text md:text-h2-desktop">
            7. Contact du Délégué à la Protection des Données (DPO)
          </h2>
          <p className="text-body">
            Pour toute question relative à tes données personnelles ou pour exercer tes droits RGPD,
            contacte notre DPO :{" "}
            <Placeholder>[Adresse DPO à définir — placeholder : dpo@path-advisor.fr]</Placeholder>.
          </p>
        </section>

        <section id="cnil" className="flex flex-col gap-2">
          <h2 className="text-h2 font-semibold text-text md:text-h2-desktop">
            8. Autorité de contrôle
          </h2>
          <p className="text-body">
            Tu disposes du droit d’introduire une réclamation auprès de la{" "}
            <strong>Commission Nationale de l’Informatique et des Libertés (CNIL)</strong>, autorité
            de contrôle française :
          </p>
          <address className="text-body not-italic">
            CNIL — 3 Place de Fontenoy, TSA 80715, 75334 PARIS CEDEX 07
            <br />
            Téléphone : 01 53 73 22 22
            <br />
            <Link
              href="https://www.cnil.fr/fr/plaintes"
              target="_blank"
              rel="noopener noreferrer"
              className="text-brand underline"
            >
              cnil.fr/fr/plaintes
              <span className="sr-only"> (ouvre une nouvelle fenêtre)</span>
            </Link>
          </address>
        </section>

        <section id="mineurs" className="flex flex-col gap-2">
          <h2 className="text-h2 font-semibold text-text md:text-h2-desktop">
            9. Inscription des moins de 15 ans
          </h2>
          <p className="text-body">
            Conformément à l’article 8 du RGPD et à l’article 45 de la loi Informatique et Libertés,
            les utilisateurs de moins de 15 ans doivent obtenir le consentement préalable de l’un de
            leurs représentants légaux pour s’inscrire.
          </p>
          <p className="text-body">
            Le flow d’inscription parental (validation par email du parent) arrive prochainement
            avec la Story 1.4. Pour l’instant, l’inscription est réservée aux utilisateurs ≥ 15 ans.
          </p>
          <p className="text-body">
            Si tu as moins de 15 ans, demande à un parent ou tuteur de te recontacter via{" "}
            <Placeholder>[Adresse DPO à définir]</Placeholder>.
          </p>
        </section>

        <footer className="border-t border-border pt-4 text-body-sm text-text-muted">
          Version : 2026-05-15 — Cette politique peut être mise à jour. Nous t’informerons par email
          de toute modification substantielle, et te demanderons de re-confirmer ton consentement si
          nécessaire.
        </footer>
      </article>
    </main>
  );
}
