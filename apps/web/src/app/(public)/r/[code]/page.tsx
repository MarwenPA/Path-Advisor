/**
 * /r/[code] — Story 10.5. Le lien de parrainage partagé (WhatsApp, SMS…) :
 * redirection serveur vers l'inscription avec le code en paramètre. Le code
 * est opaque (jamais un identifiant utilisateur) et n'est validé qu'au
 * signal d'inscription, en silence — cette page ne confirme donc jamais
 * l'existence d'un code (pas d'oracle d'énumération).
 */
import { redirect } from "next/navigation";

export const metadata = { title: "Rejoins Path-Advisor" };

export default async function ReferralRedirectPage({
  params,
}: {
  params: Promise<{ code: string }>;
}) {
  const { code } = await params;
  redirect(`/auth/signup?ref=${encodeURIComponent(code)}`);
}
