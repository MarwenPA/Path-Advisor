export interface ParcoursNode {
  id: string;
  label: string;
  type: "start" | "intermediate" | "target";
  schoolId?: string;
  schoolSlug?: string;
}

export interface ParcoursEdge {
  source: string;
  target: string;
  weight?: number;
}

export interface AdmissionStatInline {
  expected_proba: number;
  label: "audacieux" | "realiste" | "sur" | "estimation_indicative";
}
