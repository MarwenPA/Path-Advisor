"use client";

import { useMutation } from "@tanstack/react-query";

import { apiFetch, readCsrfCookie } from "@/lib/api/client";

export type ReviewReason = "ne_correspond_pas" | "choquant_inapproprie" | "autre";

export interface ReviewPayload {
  profession_slug: string;
  reason: ReviewReason;
  comment?: string | null;
}

interface ReviewResponse {
  id: string;
  status: string;
}

async function submitReviewRequest(payload: ReviewPayload): Promise<ReviewResponse> {
  const csrf = readCsrfCookie() ?? "";
  return apiFetch<ReviewResponse>("/api/v1/students/me/recommendation-reviews/", {
    method: "POST",
    body: payload,
    headers: { "X-CSRFToken": csrf },
  });
}

export function useRequestRecommendationReview() {
  return useMutation({
    mutationFn: (payload: ReviewPayload) => submitReviewRequest(payload),
  });
}
