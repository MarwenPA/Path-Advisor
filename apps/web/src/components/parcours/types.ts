// Parcours types — Story 4.3 / 4.5

export interface AdmissionStatInline {
  expected_proba: number;
  label: "audacieux" | "realiste" | "sur" | "estimation_indicative";
  context_line?: string;
  action_lever?: string | null;
}

export interface ParcoursNode {
  id: string;
  label: string;
  /** "start" | "intermediate" | "target" | "diplome" | "ecole" | "stage" | "concours" */
  type: string;
  schoolId?: string;
  schoolSlug?: string;
  duration_label?: string;
  /** Inline admission stat injected by the backend (Story 4.5 AC2). */
  admission_stat?: AdmissionStatInline | null;
}

export interface ParcoursEdge {
  source: string;
  target: string;
  weight?: number;
}

export interface Parcours {
  id: string;
  profession: string;
  target_school: string;
  target_school_name?: string;
  target_school_slug?: string;
  target_school_city?: string;
  nodes: ParcoursNode[];
  edges: ParcoursEdge[];
  nodes_with_stats?: ParcoursNode[];
  niveau_scolaire: string;
  is_default: boolean;
  created_at?: string;
}
