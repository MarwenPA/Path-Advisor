"use client";

/**
 * <ParentSignupForm> — Story 6.1 §T7.3 client half.
 *
 * Submits `POST /parent-invitations/{token}/accept/` with the anonymous
 * account-creation payload (AC3). On 409 (AC4, email already taken) offers
 * a "Se connecter" link instead of retrying the form.
 */
import { useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api/client";
import { acceptInvitation } from "@/lib/api/family";
import { PARENT_SIGNUP_COPY } from "@/lib/i18n/fr/family";

type Status = "idle" | "submitting" | "email-taken" | "error";

export function ParentSignupForm({ token, prefillEmail }: { token: string; prefillEmail: string }) {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [status, setStatus] = useState<Status>("idle");

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setStatus("submitting");
    try {
      await acceptInvitation(token, {
        email: prefillEmail,
        password,
        first_name: firstName,
        last_name: lastName,
      });
      router.push("/");
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setStatus("email-taken");
        return;
      }
      setStatus("error");
    }
  };

  if (status === "email-taken") {
    return (
      <div role="alert" className="flex flex-col gap-3 rounded-md border border-border p-4">
        <p className="text-body text-text">{PARENT_SIGNUP_COPY.emailTakenMessage}</p>
        <Button asChild>
          <a href="/auth/login">{PARENT_SIGNUP_COPY.loginCta}</a>
        </Button>
      </div>
    );
  }

  return (
    <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
      <h2 className="text-h2 font-semibold text-text md:text-h2-desktop">
        {PARENT_SIGNUP_COPY.formTitle}
      </h2>
      <div className="flex flex-col gap-1">
        <Label htmlFor="parent-signup-email">{PARENT_SIGNUP_COPY.emailLabel}</Label>
        <Input id="parent-signup-email" type="email" value={prefillEmail} disabled readOnly />
      </div>
      <div className="flex flex-col gap-1">
        <Label htmlFor="parent-signup-first-name">{PARENT_SIGNUP_COPY.firstNameLabel}</Label>
        <Input
          id="parent-signup-first-name"
          value={firstName}
          onChange={(event) => setFirstName(event.target.value)}
        />
      </div>
      <div className="flex flex-col gap-1">
        <Label htmlFor="parent-signup-last-name">{PARENT_SIGNUP_COPY.lastNameLabel}</Label>
        <Input
          id="parent-signup-last-name"
          value={lastName}
          onChange={(event) => setLastName(event.target.value)}
        />
      </div>
      <div className="flex flex-col gap-1">
        <Label htmlFor="parent-signup-password">{PARENT_SIGNUP_COPY.passwordLabel}</Label>
        <Input
          id="parent-signup-password"
          type="password"
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
      </div>
      {status === "error" ? (
        <p role="alert" className="text-text-error text-sm">
          Une erreur est survenue. Réessaie dans un instant.
        </p>
      ) : null}
      <Button type="submit" disabled={status === "submitting"}>
        {PARENT_SIGNUP_COPY.submitLabel}
      </Button>
    </form>
  );
}

export default ParentSignupForm;
