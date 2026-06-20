export interface Signal {
  id: string;
  label: string;
}

export interface ScoreVocationnelProps {
  metierId: string;
  metiersName: string;
  score: number;
  phraseRecopiable: string;
  signals: Signal[];
  variant: "compact" | "expanded" | "comparison";
  confidenceLevel?: "normal" | "indicative";
  onSignalClick?: (signalId: string) => void;
  onExplainClick?: () => void;
}

// ─── Profession (Story 3.2 schema) ───────────────────────────────────────────

export interface RequirementItem {
  type: "studies" | "skill" | "quality";
  label: string;
}

export interface SignalsByCategory {
  passions: string[];
  valeurs: string[];
  specialites: string[];
}

export interface SalaryRange {
  min: number;
  max: number;
  source?: string;
}

export interface Profession {
  id: string;
  slug: string;
  name: string;
  description: string;
  daily_routine: string;
  requirements_json: RequirementItem[];
  prospects_text: string;
  median_salary_eur?: number | null;
  salary_range_json?: SalaryRange | null;
  signals_json: SignalsByCategory;
  level_compatibility: string[];
  sector?: string;
  rome_code?: string | null;
}

// ─── FicheMetier (Story 3.12) ────────────────────────────────────────────────

export interface FicheMetierProps {
  profession: Profession;
  score?: number;
  phraseRecopiable?: string;
  confidenceLevel?: "normal" | "indicative";
  variant?: "default" | "mobile" | "print";
  onSignalClick?: (signalId: string) => void;
}
