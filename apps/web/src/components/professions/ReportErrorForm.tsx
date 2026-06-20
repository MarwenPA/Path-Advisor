"use client";

import * as React from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import type { ErrorType, ReportPayload } from "@/hooks/useReportProfessionError";

const ERROR_TYPE_OPTIONS: { value: ErrorType; label: string }[] = [
  { value: "description_inexacte", label: "Description inexacte ou trompeuse" },
  { value: "debouches_perimes", label: "Débouchés ou informations périmées" },
  { value: "lien_casse", label: "Lien ou ressource cassé(e)" },
  { value: "autre", label: "Autre" },
];

const MAX_COMMENT_LENGTH = 500;

interface ReportErrorFormProps {
  professionName: string;
  isSubmitting: boolean;
  submitError: string | null;
  onSubmit: (payload: ReportPayload) => void;
  onCancel: () => void;
}

export function ReportErrorForm({
  professionName,
  isSubmitting,
  submitError,
  onSubmit,
  onCancel,
}: ReportErrorFormProps) {
  const [errorType, setErrorType] = React.useState<ErrorType | "">("");
  const [location, setLocation] = React.useState("");
  const [comment, setComment] = React.useState("");
  const [showTypeError, setShowTypeError] = React.useState(false);

  const selectId = React.useId();
  const locationId = React.useId();
  const commentId = React.useId();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!errorType) {
      setShowTypeError(true);
      return;
    }
    onSubmit({
      error_type: errorType,
      location: location || null,
      comment: comment || null,
    });
  }

  return (
    <form onSubmit={handleSubmit} noValidate aria-label="Formulaire de signalement">
      <p className="mb-4 text-sm text-muted-foreground">{professionName}</p>

      {/* Type d'erreur — required */}
      <div className="mb-4">
        <Label htmlFor={selectId} className="mb-1.5 block">
          Type d&apos;erreur <span aria-hidden>*</span>
        </Label>
        <Select
          value={errorType}
          onValueChange={(v) => {
            setErrorType(v as ErrorType);
            setShowTypeError(false);
          }}
        >
          <SelectTrigger
            id={selectId}
            aria-describedby={showTypeError ? `${selectId}-error` : undefined}
          >
            <SelectValue placeholder="Choisir un type d'erreur" />
          </SelectTrigger>
          <SelectContent>
            {ERROR_TYPE_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {showTypeError && (
          <p id={`${selectId}-error`} className="mt-1 text-sm text-destructive" role="alert">
            Ce champ est obligatoire.
          </p>
        )}
      </div>

      {/* Localisation — optional */}
      <div className="mb-4">
        <Label htmlFor={locationId} className="mb-1.5 block">
          Où exactement ? <span className="font-normal text-muted-foreground">(optionnel)</span>
        </Label>
        <Input
          id={locationId}
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          placeholder="Ex. : section 'Comment y aller', paragraphe 2"
        />
      </div>

      {/* Commentaire — optional, max 500 */}
      <div className="mb-6">
        <Label htmlFor={commentId} className="mb-1.5 block">
          Commentaire <span className="font-normal text-muted-foreground">(optionnel)</span>
        </Label>
        <Textarea
          id={commentId}
          value={comment}
          onChange={(e) => setComment(e.target.value.slice(0, MAX_COMMENT_LENGTH))}
          placeholder="Décris l'erreur ou propose une correction"
          rows={3}
          aria-describedby={`${commentId}-count`}
        />
        <p id={`${commentId}-count`} className="mt-1 text-right text-xs text-muted-foreground">
          {comment.length}/{MAX_COMMENT_LENGTH}
        </p>
      </div>

      {/* Network error message — inline */}
      {submitError && (
        <p className="mb-4 text-sm text-destructive" role="alert">
          {submitError}
        </p>
      )}

      <Button type="submit" className="mb-2 w-full" disabled={isSubmitting}>
        {isSubmitting ? "Envoi…" : "Envoyer le signalement"}
      </Button>
      <Button
        type="button"
        variant="ghost"
        className="w-full"
        onClick={onCancel}
        disabled={isSubmitting}
      >
        Annuler
      </Button>
    </form>
  );
}
