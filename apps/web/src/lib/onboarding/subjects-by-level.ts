export const SUBJECTS_REF_VERSION = "2026-06-v1";

export interface MatiereDef {
  id: string;
  label: string;
  is_specialite: boolean;
  is_optional: boolean;
}

// ─── Tronc commun ──────────────────────────────────────────────────────────

const TRONC_COLLEGE_3EME: MatiereDef[] = [
  { id: "mathematiques", label: "Mathématiques", is_specialite: false, is_optional: false },
  { id: "francais", label: "Français", is_specialite: false, is_optional: false },
  { id: "histoire_geo", label: "Histoire-Géographie", is_specialite: false, is_optional: false },
  { id: "emc", label: "EMC", is_specialite: false, is_optional: false },
  { id: "svt", label: "SVT", is_specialite: false, is_optional: false },
  { id: "physique_chimie", label: "Physique-Chimie", is_specialite: false, is_optional: false },
  { id: "technologie", label: "Technologie", is_specialite: false, is_optional: false },
  { id: "anglais_lv1", label: "Anglais LV1", is_specialite: false, is_optional: false },
  { id: "lv2", label: "LV2", is_specialite: false, is_optional: false },
  { id: "eps", label: "EPS", is_specialite: false, is_optional: false },
  { id: "arts_plastiques", label: "Arts plastiques", is_specialite: false, is_optional: false },
  { id: "musique", label: "Éducation musicale", is_specialite: false, is_optional: false },
];

const TRONC_LYCEE_2NDE: MatiereDef[] = [
  { id: "mathematiques", label: "Mathématiques", is_specialite: false, is_optional: false },
  { id: "francais", label: "Français", is_specialite: false, is_optional: false },
  { id: "histoire_geo", label: "Histoire-Géographie", is_specialite: false, is_optional: false },
  { id: "emc", label: "EMC", is_specialite: false, is_optional: false },
  { id: "svt", label: "SVT", is_specialite: false, is_optional: false },
  { id: "physique_chimie", label: "Physique-Chimie", is_specialite: false, is_optional: false },
  { id: "ses", label: "SES", is_specialite: false, is_optional: false },
  { id: "anglais_lv1", label: "Anglais LV1", is_specialite: false, is_optional: false },
  { id: "lv2", label: "LV2", is_specialite: false, is_optional: false },
  { id: "eps", label: "EPS", is_specialite: false, is_optional: false },
  { id: "enseignement_scientifique", label: "Enseignement scientifique", is_specialite: false, is_optional: false },
];

const TRONC_LYCEE_GENERAL_1ERE_TLE: MatiereDef[] = [
  { id: "francais", label: "Français (Bac anticipé)", is_specialite: false, is_optional: false },
  { id: "philosophie", label: "Philosophie", is_specialite: false, is_optional: false },
  { id: "histoire_geo", label: "Histoire-Géographie", is_specialite: false, is_optional: false },
  { id: "anglais_lv1", label: "Anglais LV1", is_specialite: false, is_optional: false },
  { id: "lv2", label: "LV2", is_specialite: false, is_optional: false },
  { id: "eps", label: "EPS", is_specialite: false, is_optional: false },
  { id: "enseignement_scientifique", label: "Enseignement scientifique", is_specialite: false, is_optional: false },
];

// ─── Spécialités lycée général ─────────────────────────────────────────────

const GENERAL_SPECIALITES: Record<string, MatiereDef> = {
  mathematiques: { id: "mathematiques", label: "Mathématiques", is_specialite: true, is_optional: false },
  svt: { id: "svt", label: "SVT", is_specialite: true, is_optional: false },
  physique_chimie: { id: "physique_chimie", label: "Physique-Chimie", is_specialite: true, is_optional: false },
  hggsp: { id: "hggsp", label: "HGGSP", is_specialite: true, is_optional: false },
  ses: { id: "ses", label: "SES", is_specialite: true, is_optional: false },
  humanites_litterature_philosophie: {
    id: "humanites_litterature_philosophie",
    label: "Humanités, Littérature et Philosophie",
    is_specialite: true,
    is_optional: false,
  },
  llcer: { id: "llcer", label: "LLCER", is_specialite: true, is_optional: false },
  arts: { id: "arts", label: "Arts", is_specialite: true, is_optional: false },
  numerique_sciences_informatiques: {
    id: "numerique_sciences_informatiques",
    label: "Numérique et Sciences Informatiques",
    is_specialite: true,
    is_optional: false,
  },
  education_physique_pratiques_sportives: {
    id: "education_physique_pratiques_sportives",
    label: "EPPS",
    is_specialite: true,
    is_optional: false,
  },
  biologie_ecologie: {
    id: "biologie_ecologie",
    label: "Biologie-Écologie",
    is_specialite: true,
    is_optional: false,
  },
  droit_grands_enjeux_monde_contemporain: {
    id: "droit_grands_enjeux_monde_contemporain",
    label: "DGEMC",
    is_specialite: true,
    is_optional: false,
  },
};

// ─── Branches technologiques ───────────────────────────────────────────────

const TRONC_TECHNO_STMG: MatiereDef[] = [
  { id: "management", label: "Management", is_specialite: false, is_optional: false },
  { id: "gestion_finance", label: "Gestion-Finance", is_specialite: false, is_optional: false },
  { id: "mercatique", label: "Mercatique", is_specialite: false, is_optional: false },
  { id: "systemes_info_gestion", label: "Systèmes d'information de gestion", is_specialite: false, is_optional: false },
  { id: "anglais_lv1", label: "Anglais LV1", is_specialite: false, is_optional: false },
  { id: "eps", label: "EPS", is_specialite: false, is_optional: false },
  { id: "histoire_geo", label: "Histoire-Géographie", is_specialite: false, is_optional: false },
  { id: "mathematiques", label: "Mathématiques", is_specialite: false, is_optional: false },
];

const TRONC_TECHNO_STI2D: MatiereDef[] = [
  { id: "innovation_technologique", label: "Innovation technologique", is_specialite: false, is_optional: false },
  { id: "physique_chimie", label: "Physique-Chimie", is_specialite: false, is_optional: false },
  { id: "mathematiques", label: "Mathématiques", is_specialite: false, is_optional: false },
  { id: "anglais_lv1", label: "Anglais LV1", is_specialite: false, is_optional: false },
  { id: "eps", label: "EPS", is_specialite: false, is_optional: false },
  { id: "histoire_geo", label: "Histoire-Géographie", is_specialite: false, is_optional: false },
];

// ─── Optional subjects (addable via "+ Ajouter matière manquante") ─────────

const OPTIONAL_LYCEE: MatiereDef[] = [
  { id: "latin", label: "Latin", is_specialite: false, is_optional: true },
  { id: "grec", label: "Grec", is_specialite: false, is_optional: true },
  { id: "maths_complementaires", label: "Maths complémentaires", is_specialite: false, is_optional: true },
  { id: "maths_expertes", label: "Maths expertes", is_specialite: false, is_optional: true },
  { id: "section_europeenne", label: "Section européenne", is_specialite: false, is_optional: true },
  { id: "lv3", label: "LV3", is_specialite: false, is_optional: true },
  { id: "arts_plastiques", label: "Arts plastiques", is_specialite: false, is_optional: true },
  { id: "cinema_audiovisuel", label: "Cinéma-Audiovisuel", is_specialite: false, is_optional: true },
  { id: "musique", label: "Éducation musicale", is_specialite: false, is_optional: true },
  { id: "theatre", label: "Théâtre", is_specialite: false, is_optional: true },
];

const OPTIONAL_COLLEGE: MatiereDef[] = [
  { id: "latin", label: "Latin", is_specialite: false, is_optional: true },
  { id: "grec", label: "Grec", is_specialite: false, is_optional: true },
  { id: "lv3", label: "LV3", is_specialite: false, is_optional: true },
];

// ─── Public API ───────────────────────────────────────────────────────────

export type SupportedLevel =
  | "college_3eme"
  | "lycee_2nde"
  | "lycee_1ere"
  | "lycee_terminale"
  | "postbac";

export type SupportedFiliere = "general" | "technologique" | "professionnel" | undefined;

export function getSubjectsForLevel(
  level: string,
  filiere?: string,
  specialites: string[] = [],
  sousFiliereTechno?: string
): MatiereDef[] {
  if (level === "college_3eme") {
    return TRONC_COLLEGE_3EME;
  }

  if (level === "lycee_2nde") {
    return TRONC_LYCEE_2NDE;
  }

  if (level === "postbac") {
    return [];
  }

  if (level === "lycee_1ere" || level === "lycee_terminale") {
    if (filiere === "technologique") {
      const troncByBranch: Record<string, MatiereDef[]> = {
        STMG: TRONC_TECHNO_STMG,
        STI2D: TRONC_TECHNO_STI2D,
      };
      return troncByBranch[sousFiliereTechno ?? ""] ?? TRONC_TECHNO_STMG;
    }

    // General (default)
    const tronc = [...TRONC_LYCEE_GENERAL_1ERE_TLE];
    const specDefs = specialites
      .map((id) => GENERAL_SPECIALITES[id])
      .filter(Boolean) as MatiereDef[];
    return [...tronc, ...specDefs];
  }

  // Unknown level — return empty
  return [];
}

export function getOptionalSubjectsForLevel(
  level: string,
  _filiere?: string
): MatiereDef[] {
  if (level.startsWith("lycee_") || level === "lycee_2nde") {
    return OPTIONAL_LYCEE;
  }
  if (level === "college_3eme") {
    return OPTIONAL_COLLEGE;
  }
  return [];
}
