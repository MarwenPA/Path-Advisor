"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";

import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api/client";
import { verifyEmail } from "@/lib/api/auth";

type Phase = "loading" | "success" | "error";

const COPY = {
  loadingTitle: "Vérification en cours…",
  loadingBody: "On confirme ton adresse email. Ça prend une seconde.",
  successTitle: "Email vérifié ✓",
  successBody: "Ton compte est activé. On t’emmène sur la page d’accueil.",
  errorTitle: "Lien expiré ou déjà utilisé",
  errorBody:
    "Ce lien de vérification n’est plus valide. Demande-en un nouveau et vérifie ta boîte mail (regarde aussi les spams).",
  resendCta: "Renvoyer un email",
  missingKey: "Lien incomplet — ouvre l’email reçu et clique directement sur le bouton qu’il contient.",
};

export default function VerifyEmailPage() {
  // `useSearchParams` requires a Suspense boundary for static prerendering.
  return (
    <Suspense fallback={<VerifyEmailFallback />}>
      <VerifyEmailContent />
    </Suspense>
  );
}

function VerifyEmailFallback() {
  return (
    <main className="bg-bg flex flex-1 flex-col items-center justify-center px-4 py-12">
      <section
        aria-live="polite"
        className="bg-bg-2 border-border flex w-full max-w-md flex-col gap-3 rounded-md border p-6"
      >
        <h1 className="text-h2 md:text-h2-desktop text-text font-semibold">
          {COPY.loadingTitle}
        </h1>
        <p className="text-body text-text-muted">{COPY.loadingBody}</p>
      </section>
    </main>
  );
}

function VerifyEmailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const rawKey = searchParams.get("key");
  // Empty-string `?key=` and whitespace-only values would otherwise pass the truthy check
  // and trigger a wasted POST that the API rejects with a generic 400 (cf. code review §11).
  const key = rawKey && rawKey.trim().length > 0 ? rawKey : null;
  // Initialise state at render time so React Compiler does not flag setState-in-effect for the
  // "missing key" branch (which has no async work).
  const [phase, setPhase] = useState<Phase>(key ? "loading" : "error");
  const [errorDetail, setErrorDetail] = useState<string>(key ? COPY.errorBody : COPY.missingKey);

  useEffect(() => {
    if (!key) return;
    let cancelled = false;
    verifyEmail(key)
      .then(() => {
        if (cancelled) return;
        setPhase("success");
        const timer = setTimeout(() => router.replace("/onboarding"), 1500);
        return () => clearTimeout(timer);
      })
      .catch((error) => {
        if (cancelled) return;
        setPhase("error");
        if (error instanceof ApiError && error.problem?.detail) {
          setErrorDetail(error.problem.detail);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [key, router]);

  return (
    <main className="bg-bg flex flex-1 flex-col items-center justify-center px-4 py-12">
      <section
        aria-live="polite"
        className="bg-bg-2 border-border flex w-full max-w-md flex-col gap-3 rounded-md border p-6"
      >
        {phase === "loading" && (
          <>
            <h1 className="text-h2 md:text-h2-desktop text-text font-semibold">
              {COPY.loadingTitle}
            </h1>
            <p className="text-body text-text-muted">{COPY.loadingBody}</p>
          </>
        )}
        {phase === "success" && (
          <>
            <h1 className="text-h2 md:text-h2-desktop text-text font-semibold">
              {COPY.successTitle}
            </h1>
            <p className="text-body text-text-muted">{COPY.successBody}</p>
          </>
        )}
        {phase === "error" && (
          <>
            <h1 className="text-h2 md:text-h2-desktop text-text font-semibold">
              {COPY.errorTitle}
            </h1>
            <p className="text-body text-text-muted">{errorDetail}</p>
            <div className="flex flex-wrap gap-3 pt-2">
              <Button asChild variant="outline">
                <Link href="/auth/signup">{COPY.resendCta}</Link>
              </Button>
            </div>
          </>
        )}
      </section>
    </main>
  );
}
