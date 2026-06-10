"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api/client";
import { loginUser } from "@/lib/api/auth";
import { getPostLoginPath } from "@/lib/auth/post-login-redirect";

/*
 * LoginForm — Story 1.5 §AC1 + §AC8.
 *
 * Renders the email + password form, posts to /api/v1/auth/login/, and
 * routes the success path through `getPostLoginPath(role, status)`. Maps
 * the 4 typed Problem Details from `PathAdvisorLoginSerializer` to
 * friendly copy:
 *
 *   - `…/account-locked` → "Connexion temporairement bloquée" (generic body
 *     so an attacker can't tell apart "wrong password" vs "just locked").
 *   - `…/account-deleted` → redirect to /auth/account-deleted (Story 1.12 flow).
 *   - `…/account-suspended` → "Compte suspendu" + DPO contact line.
 *   - `…/email-not-verified` → resend button hitting the URL from `extras`.
 *   - generic 400 (wrong password OR unknown email) → uniform "Email ou
 *     mot de passe incorrect" so we don't leak which branch hit.
 */

const COPY = {
  title: "Connexion",
  subtitle: "Accède à ton espace Path-Advisor.",
  emailLabel: "Adresse email",
  passwordLabel: "Mot de passe",
  submit: "Se connecter",
  submitting: "Connexion…",
  forgotPasswordLink: "Mot de passe oublié ?",
  signupHint: "Pas encore inscrit ?",
  signupLink: "Créer un compte",
  genericError: "Email ou mot de passe incorrect.",
  fallbackError:
    "Quelque chose n'a pas fonctionné. Vérifie ta connexion et réessaie dans un instant.",
  accountSuspended: "Ton compte est suspendu. Contacte le DPO si tu penses que c'est une erreur.",
  emailUnverifiedTitle: "Email non vérifié",
  emailUnverifiedBody:
    "Vérifie ton adresse email avant de te connecter. Le lien d'activation t'a été envoyé à l'inscription.",
  resendButton: "Renvoyer l'email de vérification",
  resending: "Envoi…",
  resendDone: "Email renvoyé — vérifie ta boîte.",
  rateLimited: "Trop de tentatives de connexion. Patiente quelques minutes avant de réessayer.",
};

interface UnverifiedState {
  resendEndpoint: string;
  email: string;
}

export function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [unverified, setUnverified] = useState<UnverifiedState | null>(null);
  const [resending, setResending] = useState(false);
  const [resendStatus, setResendStatus] = useState<string | null>(null);

  // Real `useRef` — the previous `useState<{value: boolean}>[0]` discarded
  // the setter and lived as a mutable initial-state object. That works in
  // the happy path but is not Strict-Mode-safe and races with `setSubmitting`
  // (code-review P14 — Story 1.5 review 2026-05-27).
  const isPendingRef = useRef(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (isPendingRef.current) return;
    if (!email || !password) return;
    isPendingRef.current = true;
    setSubmitting(true);
    setError(null);
    setUnverified(null);
    setResendStatus(null);
    try {
      const res = await loginUser(email, password);

      // Story 1.6 — MFA branch. The backend returns `mfa_required:true` +
      // `mfa_session` when the user has `requires_mfa=true` (staff role OR
      // already-enrolled). NO session cookie is set. We stash the token in
      // sessionStorage and route to the right MFA page.
      if (res.mfa_required && res.mfa_session) {
        const { storeMfaSession } = await import("@/lib/api/mfa");
        // Code-review P19 — storeMfaSession is defensive (returns false on
        // sessionStorage failure). If we can't store, the user can't
        // continue the MFA flow; surface a clean error rather than crashing.
        const stored = storeMfaSession(res.mfa_session);
        if (!stored) {
          setError(COPY.fallbackError);
          return;
        }
        const target = res.mfa_enrollment_required ? "/auth/mfa/enroll" : "/auth/mfa/challenge";
        router.replace(target);
        return;
      }

      // Non-MFA happy path — use router.refresh() + router.replace() instead
      // of `window.location.href` so the Set-Cookie commit on the fetch
      // response is fully settled before navigation triggers the next
      // round-trip (code-review P15 — Story 1.5 review 2026-05-27).
      const path = getPostLoginPath(res.user.role, res.user.status);
      router.refresh();
      router.replace(path);
      return;
    } catch (cause) {
      if (cause instanceof ApiError) {
        const type = cause.problem?.type ?? "";
        if (type.endsWith("/account-deleted")) {
          // Story 1.12 flow — route to the info page that explains the
          // 30-day grace + cancel-link-via-email path.
          window.location.href = "/auth/account-deleted";
          return;
        }
        if (type.endsWith("/account-suspended")) {
          setError(COPY.accountSuspended);
        } else if (type.endsWith("/email-not-verified")) {
          // `resend_endpoint` is a top-level Problem-Details extension since
          // code-review P12 (Story 1.5 review 2026-05-27). The fallback
          // covers (a) older API versions still nesting it under `errors`
          // and (b) backend regressions that drop the hint entirely.
          const problem = cause.problem as {
            resend_endpoint?: string;
            errors?: { resend_endpoint?: string };
          } | null;
          const resendEndpoint =
            problem?.resend_endpoint ??
            problem?.errors?.resend_endpoint ??
            "/api/v1/auth/registration/resend-email/";
          setUnverified({ resendEndpoint, email });
        } else if (type.endsWith("/rate-limited")) {
          setError(COPY.rateLimited);
        } else {
          // Includes account-locked (400 generic), validation errors, unknown email.
          // Uniform body so we don't leak which branch hit.
          setError(COPY.genericError);
        }
      } else {
        setError(COPY.fallbackError);
      }
      setPassword("");
    } finally {
      isPendingRef.current = false;
      setSubmitting(false);
    }
  }

  async function handleResend() {
    if (!unverified || resending) return;
    setResending(true);
    setResendStatus(null);
    try {
      const { resendVerificationEmail } = await import("@/lib/api/auth");
      await resendVerificationEmail(unverified.email);
      setResendStatus(COPY.resendDone);
    } catch (cause) {
      setResendStatus(
        cause instanceof ApiError
          ? (cause.problem?.detail ?? COPY.fallbackError)
          : COPY.fallbackError,
      );
    } finally {
      setResending(false);
    }
  }

  return (
    <section className="flex w-full max-w-md flex-col gap-6 rounded-lg border border-border bg-bg p-6 shadow-sm">
      <header className="flex flex-col gap-1 text-center">
        <h1 className="text-h1 font-semibold text-text">{COPY.title}</h1>
        <p className="text-body-sm text-text-muted">{COPY.subtitle}</p>
      </header>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
        <div className="flex flex-col gap-2">
          <Label htmlFor="login-email">{COPY.emailLabel}</Label>
          <Input
            id="login-email"
            name="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={submitting}
          />
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="login-password">{COPY.passwordLabel}</Label>
          <Input
            id="login-password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={submitting}
          />
        </div>

        {error && (
          <p role="alert" className="text-body-sm text-danger">
            {error}
          </p>
        )}

        {unverified && (
          <div
            role="alert"
            className="flex flex-col gap-2 rounded border border-warning/30 bg-warning/10 p-3 text-body-sm"
          >
            <p className="font-medium">{COPY.emailUnverifiedTitle}</p>
            <p className="text-text-muted">{COPY.emailUnverifiedBody}</p>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleResend}
              disabled={resending}
            >
              {resending ? COPY.resending : COPY.resendButton}
            </Button>
            {resendStatus && <p className="text-body-sm text-text-muted">{resendStatus}</p>}
          </div>
        )}

        <Button
          type="submit"
          disabled={submitting || !email || !password}
          aria-disabled={submitting || !email || !password}
        >
          {submitting ? COPY.submitting : COPY.submit}
        </Button>
      </form>

      <div className="flex flex-col items-center gap-2 text-body-sm">
        <Link
          href="/auth/forgot-password"
          className="text-brand underline-offset-2 hover:underline"
        >
          {COPY.forgotPasswordLink}
        </Link>
        <p className="text-text-muted">
          {COPY.signupHint}{" "}
          <Link href="/auth/signup" className="text-brand underline-offset-2 hover:underline">
            {COPY.signupLink}
          </Link>
        </p>
      </div>
    </section>
  );
}
