"use client";

import { useState } from "react";
import Link from "next/link";
import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api/client";
import { CGU_RGPD_VERSION, signupStudent } from "@/lib/api/auth";

const COPY = {
  title: "Créer ton compte",
  subtitle: "Inscription en moins d'une minute. On t'enverra un email pour confirmer ton adresse.",
  emailLabel: "Adresse email",
  emailPlaceholder: "ex. sarah@example.com",
  passwordLabel: "Mot de passe",
  passwordHelp: "12 caractères minimum. Évite les mots de passe courants ou seulement numériques.",
  birthDateLabel: "Date de naissance",
  birthDateHelp:
    "L'inscription des moins de 15 ans nécessite un consentement parental (arrive prochainement).",
  consentLabel: "J'accepte les CGU et la",
  consentLink: "politique RGPD",
  submit: "Créer mon compte",
  submitting: "Création en cours…",
  successTitle: "Vérifie ta boîte mail",
  successBody:
    "On vient de t'envoyer un email avec un lien d'activation. Clique dessus dans les 3 jours pour finaliser ton inscription.",
  errorTitle: "On n'a pas pu créer ton compte",
  fallbackError:
    "Quelque chose n'a pas fonctionné. Vérifie tes informations et réessaie dans un instant.",
};

const SignupSchema = z
  .object({
    email: z.string().email("Adresse email invalide"),
    password: z.string().min(12, "12 caractères minimum").max(128, "Mot de passe trop long"),
    passwordConfirm: z.string(),
    birth_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Format attendu : AAAA-MM-JJ"),
    consent_rgpd_accepted: z.literal(true, {
      errorMap: () => ({ message: "Tu dois accepter les CGU et la politique RGPD." }),
    }),
  })
  .refine((data) => data.password === data.passwordConfirm, {
    path: ["passwordConfirm"],
    message: "Les deux mots de passe ne correspondent pas.",
  });

type SignupFormValues = z.infer<typeof SignupSchema>;

export function SignupForm() {
  const [serverError, setServerError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const form = useForm<SignupFormValues>({
    resolver: zodResolver(SignupSchema),
    defaultValues: {
      email: "",
      password: "",
      passwordConfirm: "",
      birth_date: "",
      consent_rgpd_accepted: false as unknown as true,
    },
  });

  const onSubmit = async (values: SignupFormValues) => {
    setServerError(null);
    try {
      await signupStudent({
        email: values.email.trim().toLowerCase(),
        password1: values.password,
        password2: values.passwordConfirm,
        birth_date: values.birth_date,
        consent_rgpd_accepted: values.consent_rgpd_accepted,
        consent_cgu_version: CGU_RGPD_VERSION,
      });
      setSubmitted(true);
    } catch (error) {
      if (error instanceof ApiError) {
        setServerError(error.problem?.detail ?? error.message);
        return;
      }
      setServerError(COPY.fallbackError);
    }
  };

  if (submitted) {
    return (
      <section
        aria-labelledby="signup-success-title"
        className="flex flex-col gap-3 rounded-md border border-border bg-bg-2 p-6"
      >
        <h2
          id="signup-success-title"
          className="text-h2 font-semibold text-text md:text-h2-desktop"
        >
          {COPY.successTitle}
        </h2>
        <p className="text-body text-text-muted">{COPY.successBody}</p>
      </section>
    );
  }

  const { errors } = form.formState;

  return (
    <form
      noValidate
      onSubmit={form.handleSubmit(onSubmit)}
      className="flex w-full max-w-md flex-col gap-5"
    >
      <header className="flex flex-col gap-2">
        <h1 className="text-h1 font-semibold text-text md:text-h1-desktop">{COPY.title}</h1>
        <p className="text-body text-text-muted">{COPY.subtitle}</p>
      </header>

      <div className="flex flex-col gap-1.5">
        <Label htmlFor="signup-email">{COPY.emailLabel}</Label>
        <Input
          id="signup-email"
          type="email"
          autoComplete="email"
          placeholder={COPY.emailPlaceholder}
          aria-invalid={errors.email ? "true" : undefined}
          aria-describedby={errors.email ? "signup-email-error" : undefined}
          {...form.register("email")}
        />
        {errors.email && (
          <p id="signup-email-error" className="text-body-sm text-danger">
            {errors.email.message}
          </p>
        )}
      </div>

      <div className="flex flex-col gap-1.5">
        <Label htmlFor="signup-password">{COPY.passwordLabel}</Label>
        <Input
          id="signup-password"
          type="password"
          autoComplete="new-password"
          aria-invalid={errors.password ? "true" : undefined}
          aria-describedby="signup-password-help signup-password-error"
          {...form.register("password")}
        />
        <p id="signup-password-help" className="text-body-sm text-text-muted">
          {COPY.passwordHelp}
        </p>
        {errors.password && (
          <p id="signup-password-error" className="text-body-sm text-danger">
            {errors.password.message}
          </p>
        )}
      </div>

      <div className="flex flex-col gap-1.5">
        <Label htmlFor="signup-password-confirm">Confirme le mot de passe</Label>
        <Input
          id="signup-password-confirm"
          type="password"
          autoComplete="new-password"
          aria-invalid={errors.passwordConfirm ? "true" : undefined}
          aria-describedby={errors.passwordConfirm ? "signup-password-confirm-error" : undefined}
          {...form.register("passwordConfirm")}
        />
        {errors.passwordConfirm && (
          <p id="signup-password-confirm-error" className="text-body-sm text-danger">
            {errors.passwordConfirm.message}
          </p>
        )}
      </div>

      <div className="flex flex-col gap-1.5">
        <Label htmlFor="signup-birth-date">{COPY.birthDateLabel}</Label>
        <Input
          id="signup-birth-date"
          type="date"
          autoComplete="bday"
          aria-invalid={errors.birth_date ? "true" : undefined}
          aria-describedby="signup-birth-date-help signup-birth-date-error"
          {...form.register("birth_date")}
        />
        <p id="signup-birth-date-help" className="text-body-sm text-text-muted">
          {COPY.birthDateHelp}{" "}
          <Link href="/legal/rgpd#mineurs" className="text-brand underline">
            En savoir plus
          </Link>
          .
        </p>
        {errors.birth_date && (
          <p id="signup-birth-date-error" className="text-body-sm text-danger">
            {errors.birth_date.message}
          </p>
        )}
      </div>

      <div className="flex items-start gap-3">
        <Controller
          control={form.control}
          name="consent_rgpd_accepted"
          render={({ field }) => (
            <Checkbox
              id="signup-consent"
              checked={field.value === true}
              onCheckedChange={(checked) =>
                field.onChange(checked === true ? true : (false as unknown as true))
              }
              onBlur={field.onBlur}
              ref={field.ref}
              aria-invalid={errors.consent_rgpd_accepted ? "true" : undefined}
              aria-describedby={errors.consent_rgpd_accepted ? "signup-consent-error" : undefined}
            />
          )}
        />
        <Label htmlFor="signup-consent" className="text-body-sm leading-relaxed text-text">
          {COPY.consentLabel}{" "}
          <Link href="/legal/rgpd" className="text-brand underline">
            {COPY.consentLink}
          </Link>
          .
        </Label>
      </div>
      {errors.consent_rgpd_accepted && (
        <p id="signup-consent-error" className="-mt-3 text-body-sm text-danger">
          {errors.consent_rgpd_accepted.message}
        </p>
      )}

      {serverError && (
        <div
          role="alert"
          className="flex flex-col gap-1 rounded-md border border-danger/40 bg-danger/10 p-4 text-body-sm text-danger"
        >
          <strong className="font-semibold">{COPY.errorTitle}</strong>
          <span>{serverError}</span>
        </div>
      )}

      <Button type="submit" disabled={form.formState.isSubmitting} className="w-full">
        {form.formState.isSubmitting ? COPY.submitting : COPY.submit}
      </Button>
    </form>
  );
}
