export interface AdmissionStatInline {
  expected_proba: number;
  label: "audacieux" | "realiste" | "sur" | "estimation_indicative";
  context_line?: string;
  action_lever?: string | null;
}

export interface ParcoursNode {
  id: string;
  label: string;
  type: "start" | "intermediate" | "target";
  schoolId?: string;
  schoolSlug?: string;
  /** Inline admission stat injected by the backend (Story 4.5 AC2). */
  admission_stat?: AdmissionStatInline | null;
}

export interface ParcoursEdge {
  source: string;
  target: string;
  weight?: number;
}
