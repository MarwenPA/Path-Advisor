"use client";

import * as React from "react";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import type { ReviewPayload, ReviewReason } from "@/hooks/useRequestRecommendationReview";

const REASON_OPTIONS: { value: ReviewReason; label: string }[] = [
  { value: "ne_correspond_pas", label: "Ne me correspond pas du tout" },
  { value: "choquant_inapproprie", label: "Métier choquant ou inapproprié" },
  { value: "autre", label: "Autre" },
];

const MAX_COMMENT_LENGTH = 500;

interface ReviewRequestFormProps {
  professionName: string;
  professionSlug: string;
  isSubmitting: boolean;
  submitError: string | null;
  onSubmit: (payload: ReviewPayload) => void;
  onCancel: () => void;
}

export function ReviewRequestForm({
  professionName,
  professionSlug,
  isSubmitting,
  submitError,
  onSubmit,
  onCancel,
}: ReviewRequestFormProps) {
  const [reason, setReason] = React.useState<ReviewReason | "">("");
  const [comment, setComment] = React.useState("");
  const [showReasonError, setShowReasonError] = React.useState(false);

  const selectId = React.useId();
  const commentId = React.useId();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!reason) {
      setShowReasonError(true);
      return;
    }
    onSubmit({
      profession_slug: professionSlug,
      reason,
      comment: comment.trim() || null,
    });
  }

  return (
    <form onSubmit={handleSubmit} noValidate aria-label="Formulaire de demande de revue humaine">
      <p className="mb-4 text-sm text-muted-foreground">{professionName}</p>

      {/* Raison — required */}
      <div className="mb-4">
        <Label htmlFor={selectId} className="mb-1.5 block">
          Raison <span aria-hidden>*</span>
        </Label>
        <Select
          value={reason}
          onValueChange={(v) => {
            setReason(v as ReviewReason);
            setShowReasonError(false);
          }}
        >
          <SelectTrigger
            id={selectId}
            aria-describedby={showReasonError ? `${selectId}-error` : undefined}
          >
            <SelectValue placeholder="Choisir une raison" />
          </SelectTrigger>
          <SelectContent>
            {REASON_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {showReasonError && (
          <p id={`${selectId}-error`} className="mt-1 text-sm text-destructive" role="alert">
            Ce champ est obligatoire.
          </p>
        )}
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
          placeholder="Explique pourquoi cette reco te semble incorrecte (optionnel)"
          rows={3}
          aria-describedby={`${commentId}-count`}
        />
        <p id={`${commentId}-count`} className="mt-1 text-right text-xs text-muted-foreground">
          {comment.length}/{MAX_COMMENT_LENGTH}
        </p>
      </div>

      {/* Network error — inline */}
      {submitError && (
        <p className="mb-4 text-sm text-destructive" role="alert">
          {submitError}
        </p>
      )}

      <Button type="submit" className="mb-2 w-full" disabled={isSubmitting}>
        {isSubmitting ? "Envoi…" : "Envoyer la demande"}
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
