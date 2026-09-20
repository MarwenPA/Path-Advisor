"use client";

import * as React from "react";
import { useTranslations } from "next-intl";

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

// `value` is the API payload discriminant — only the label (catalog key
// `ficheMetier.reviewRequest.form.reasonOptions.*`) is displayed.
const REASON_OPTIONS: { value: ReviewReason; labelKey: string }[] = [
  { value: "ne_correspond_pas", labelKey: "neCorrespondPas" },
  { value: "choquant_inapproprie", labelKey: "choquantInapproprie" },
  { value: "autre", labelKey: "autre" },
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
  const t = useTranslations("ficheMetier.reviewRequest.form");
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
    <form onSubmit={handleSubmit} noValidate aria-label={t("formAria")}>
      <p className="mb-4 text-sm text-muted-foreground">{professionName}</p>

      {/* Raison — required */}
      <div className="mb-4">
        <Label htmlFor={selectId} className="mb-1.5 block">
          {t("reasonLabel")} <span aria-hidden>*</span>
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
            <SelectValue placeholder={t("reasonPlaceholder")} />
          </SelectTrigger>
          <SelectContent>
            {REASON_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {t(`reasonOptions.${opt.labelKey}`)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {showReasonError && (
          <p id={`${selectId}-error`} className="mt-1 text-sm text-destructive" role="alert">
            {t("requiredField")}
          </p>
        )}
      </div>

      {/* Commentaire — optional, max 500 */}
      <div className="mb-6">
        <Label htmlFor={commentId} className="mb-1.5 block">
          {t("commentLabel")}{" "}
          <span className="font-normal text-muted-foreground">{t("optionalHint")}</span>
        </Label>
        <Textarea
          id={commentId}
          value={comment}
          onChange={(e) => setComment(e.target.value.slice(0, MAX_COMMENT_LENGTH))}
          placeholder={t("commentPlaceholder")}
          rows={3}
          aria-describedby={`${commentId}-count`}
        />
        <p id={`${commentId}-count`} className="mt-1 text-right text-xs text-muted-foreground">
          {t("charCount", { count: comment.length, max: MAX_COMMENT_LENGTH })}
        </p>
      </div>

      {/* Network error — inline */}
      {submitError && (
        <p className="mb-4 text-sm text-destructive" role="alert">
          {submitError}
        </p>
      )}

      <Button type="submit" className="mb-2 w-full" disabled={isSubmitting}>
        {isSubmitting ? t("submitting") : t("submit")}
      </Button>
      <Button
        type="button"
        variant="ghost"
        className="w-full"
        onClick={onCancel}
        disabled={isSubmitting}
      >
        {t("cancel")}
      </Button>
    </form>
  );
}
