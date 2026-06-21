import { apiFetch } from "./client";

export interface SignalContributif {
  signal: string;
  weight: number;
  contribution: number;
}

export interface ScoredProfession {
  id: string;
  slug: string;
  name: string;
  sector: string;
  score: number;
  confidence_level: "low" | "medium" | "high";
  signals_contributifs: SignalContributif[];
  phrase_recopiable: string;
}

export interface RecommendationsResponse {
  results: ScoredProfession[];
  niveau_adapted?: boolean;
  computed_at: string;
}

export async function fetchRecommendations(): Promise<RecommendationsResponse> {
  return apiFetch<RecommendationsResponse>("/api/v1/students/me/recommendations/");
}
