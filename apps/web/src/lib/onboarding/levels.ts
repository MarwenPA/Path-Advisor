/**
 * Onboarding step-2 referentials — niveau scolaire, filières, spécialités.
 *
 * IDs are kebab-case and stored verbatim in the database. Labels may evolve
 * without migration. The `REF_VERSION` is stored server-side for audit
 * longitudinal (Story 2.2 §T1, §T2).
 *
 * MIRROR: keep in sync with `apps/api/apps/students/onboarding/levels.py`.
 * The pytest `test_levels_sync` enforces ID equality across both sides.
 */

export const REF_VERSION = "2026-05-v1" as const;

// ---------------------------------------------------------------------------
// Niveau scolaire (AC2)
// ---------------------------------------------------------------------------

export type NiveauId =
  | "college_3eme"
  | "lycee_2nde"
  | "lycee_1ere"
  | "lycee_terminale"
  | "postbac";

export type NiveauItem = {
  readonly id: NiveauId;
  readonly label: string;
  readonly description: string;
};

export const LEVELS: readonly NiveauItem[] = [
  {
    id: "college_3eme",
    label: "3ème",
    description: "Année d'orientation (Affelnet, choix lycée)",
  },
  {
    id: "lycee_2nde",
    label: "2nde",
    description: "Découverte des matières, choix de spés à venir",
  },
  {
    id: "lycee_1ere",
    label: "1ère",
    description: "Première année de spés, Bac Français",
  },
  {
    id: "lycee_terminale",
    label: "Terminale",
    description: "Année de Parcoursup, Bac complet",
  },
  {
    id: "postbac",
    label: "Post-bac",
    description: "Tu as déjà ton bac, tu cherches une (ré)orientation",
  },
] as const;

// ---------------------------------------------------------------------------
// Intended track — branche 3ème (AC3)
// ---------------------------------------------------------------------------

export type Track3emeId = "general" | "techno" | "pro" | "undecided";

export type Track3emeItem = {
  readonly id: Track3emeId;
  readonly label: string;
  readonly description: string;
};

export const TRACKS_3EME: readonly Track3emeItem[] = [
  {
    id: "general",
    label: "Bac général",
    description: "Filière classique, suite naturelle si tu vises des études longues",
  },
  {
    id: "techno",
    label: "Bac techno",
    description: "Filières STMG / STI2D / ST2S / etc., entre théorie et concret",
  },
  {
    id: "pro",
    label: "Bac pro",
    description: "Apprendre un métier en formation, souvent en alternance",
  },
  {
    id: "undecided",
    label: "Pas encore décidé",
    description: "Pas de pression, on garde les options ouvertes — tes recos incluront tout.",
  },
] as const;

// ---------------------------------------------------------------------------
// Filières lycée (AC4)
// ---------------------------------------------------------------------------

export type FiliereId = "general" | "techno" | "pro";

export type FiliereItem = {
  readonly id: FiliereId;
  readonly label: string;
  readonly description: string;
};

export const FILIERES_LYCEE: readonly FiliereItem[] = [
  {
    id: "general",
    label: "Bac général",
    description: "Filière classique avec spécialités",
  },
  {
    id: "techno",
    label: "Bac techno",
    description: "STMG / STI2D / ST2S / STL / STD2A / STAV / STHR",
  },
  {
    id: "pro",
    label: "Bac pro",
    description: "Apprendre un métier en formation, souvent en alternance",
  },
] as const;

// ---------------------------------------------------------------------------
// Sous-filières techno (AC4)
// ---------------------------------------------------------------------------

export type SousFiliereId =
  | "STMG"
  | "STI2D"
  | "ST2S"
  | "STL"
  | "STD2A"
  | "STAV"
  | "STHR";

export type SousFiliereItem = {
  readonly id: SousFiliereId;
  readonly label: string;
  readonly description: string;
};

export const SOUS_FILIERES_TECHNO: readonly SousFiliereItem[] = [
  { id: "STMG", label: "STMG", description: "Sciences et Technologies du Management et de la Gestion" },
  { id: "STI2D", label: "STI2D", description: "Sciences et Technologies de l'Industrie et du Développement Durable" },
  { id: "ST2S", label: "ST2S", description: "Sciences et Technologies de la Santé et du Social" },
  { id: "STL", label: "STL", description: "Sciences et Technologies de Laboratoire" },
  { id: "STD2A", label: "STD2A", description: "Sciences et Technologies du Design et des Arts Appliqués" },
  { id: "STAV", label: "STAV", description: "Sciences et Technologies de l'Agronomie et du Vivant" },
  { id: "STHR", label: "STHR", description: "Sciences et Technologies de l'Hôtellerie et de la Restauration" },
] as const;

// ---------------------------------------------------------------------------
// Spécialités lycée général (AC4) — 13 entrées officielles ÉN 2026
// ---------------------------------------------------------------------------

export type SpecialiteId =
  | "mathematiques"
  | "physique-chimie"
  | "svt"
  | "ses"
  | "hggsp"
  | "hlp"
  | "llcer"
  | "llca"
  | "nsi"
  | "arts"
  | "si"
  | "bio-ecologie"
  | "eppcs";

export type SpecialiteItem = {
  readonly id: SpecialiteId;
  readonly label: string;
  readonly shortLabel: string;
};

export const SPECIALITES_LYCEE: readonly SpecialiteItem[] = [
  { id: "mathematiques", label: "Mathématiques", shortLabel: "Maths" },
  { id: "physique-chimie", label: "Physique-Chimie", shortLabel: "Physique-Chimie" },
  { id: "svt", label: "Sciences de la Vie et de la Terre (SVT)", shortLabel: "SVT" },
  { id: "ses", label: "Sciences Économiques et Sociales (SES)", shortLabel: "SES" },
  { id: "hggsp", label: "Histoire-Géo, Géopolitique et Sciences Politiques (HGGSP)", shortLabel: "HGGSP" },
  { id: "hlp", label: "Humanités, Littérature et Philosophie (HLP)", shortLabel: "HLP" },
  { id: "llcer", label: "Langues, Littératures et Cultures Étrangères (LLCER)", shortLabel: "LLCER" },
  { id: "llca", label: "Littérature, Langues et Cultures de l'Antiquité (LLCA)", shortLabel: "LLCA" },
  { id: "nsi", label: "Numérique et Sciences Informatiques (NSI)", shortLabel: "NSI" },
  { id: "arts", label: "Arts (plastiques / théâtre / musique / cinéma / danse)", shortLabel: "Arts" },
  { id: "si", label: "Sciences de l'Ingénieur (SI)", shortLabel: "SI" },
  { id: "bio-ecologie", label: "Biologie-Écologie (lycées agricoles)", shortLabel: "Bio-Écologie" },
  { id: "eppcs", label: "Éducation Physique, Pratiques et Culture Sportives (EPPCS)", shortLabel: "EPPCS" },
] as const;

// ---------------------------------------------------------------------------
// Spécialités bac pro (AC4 — branche 2nde pro / 1ère pro / Terminale pro)
// MVP: liste courte à affiner avec les équipes métier
// ---------------------------------------------------------------------------

export type SpecialiteProId =
  | "vente-action-commerciale"
  | "accompagnement-soins-aide"
  | "cuisine"
  | "systemes-numeriques"
  | "gestion-administration"
  | "metiers-electricite"
  | "maintenance-vehicules"
  | "metiers-batiment-tp"
  | "metiers-bois"
  | "conduite-transport"
  | "agro-alimentation-bio"
  | "metiers-mode"
  | "securite-prevention"
  | "services-proximite"
  | "metiers-production";

export type SpecialiteProItem = {
  readonly id: SpecialiteProId;
  readonly label: string;
};

export const SPECIALITES_BAC_PRO: readonly SpecialiteProItem[] = [
  { id: "vente-action-commerciale", label: "Vente et action commerciale" },
  { id: "accompagnement-soins-aide", label: "Accompagnement, soins et services à la personne" },
  { id: "cuisine", label: "Cuisine" },
  { id: "systemes-numeriques", label: "Systèmes numériques" },
  { id: "gestion-administration", label: "Gestion-Administration" },
  { id: "metiers-electricite", label: "Métiers de l'électricité et de ses environnements connectés" },
  { id: "maintenance-vehicules", label: "Maintenance des véhicules" },
  { id: "metiers-batiment-tp", label: "Métiers du bâtiment et des travaux publics" },
  { id: "metiers-bois", label: "Métiers du bois" },
  { id: "conduite-transport", label: "Conduite et transport routier marchandises" },
  { id: "agro-alimentation-bio", label: "Bio-industries de transformation" },
  { id: "metiers-mode", label: "Métiers de la mode — Vêtement" },
  { id: "securite-prevention", label: "Sécurité, prévention" },
  { id: "services-proximite", label: "Services de proximité et vie locale" },
  { id: "metiers-production", label: "Pilote de ligne de production" },
] as const;

// ---------------------------------------------------------------------------
// Post-bac (AC5)
// ---------------------------------------------------------------------------

export type PostbacYearId =
  | "bac_year"
  | "bac+1"
  | "bac+2"
  | "bac+3"
  | "bac+4_plus"
  | "pause";

export type PostbacYearItem = {
  readonly id: PostbacYearId;
  readonly label: string;
};

export const POSTBAC_YEARS: readonly PostbacYearItem[] = [
  { id: "bac_year", label: "Bac année en cours (juste obtenu)" },
  { id: "bac+1", label: "Bac+1" },
  { id: "bac+2", label: "Bac+2" },
  { id: "bac+3", label: "Bac+3" },
  { id: "bac+4_plus", label: "Bac+4 ou +" },
  { id: "pause", label: "En pause / Recherche" },
] as const;

export type PostbacFormationId =
  | "universite"
  | "but"
  | "bts"
  | "cpge"
  | "ecole_ingenieur"
  | "ecole_commerce"
  | "ecole_specialisee"
  | "alternance"
  | "aucune";

export type PostbacFormationItem = {
  readonly id: PostbacFormationId;
  readonly label: string;
};

export const POSTBAC_FORMATIONS: readonly PostbacFormationItem[] = [
  { id: "universite", label: "Université (Licence / Master)" },
  { id: "but", label: "BUT (ex-DUT)" },
  { id: "bts", label: "BTS" },
  { id: "cpge", label: "Classe prépa (CPGE)" },
  { id: "ecole_ingenieur", label: "École d'ingénieur" },
  { id: "ecole_commerce", label: "École de commerce" },
  { id: "ecole_specialisee", label: "École spécialisée (design, journalisme, etc.)" },
  { id: "alternance", label: "Formation en alternance / apprentissage" },
  { id: "aucune", label: "Aucune formation actuellement" },
] as const;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** How many specialties are expected for a given (level, filiere) combo. */
export function expectedSpecCount(
  level: NiveauId,
  filiere: FiliereId | null,
): number | null {
  if (filiere === "general") {
    if (level === "lycee_1ere") return 3;
    if (level === "lycee_terminale") return 2;
  }
  if (filiere === "pro") {
    // 2nde pro, 1ère pro, Terminale pro → 1 bac pro spécialité
    if (level === "lycee_2nde" || level === "lycee_1ere" || level === "lycee_terminale") return 1;
  }
  return null; // techno, 2nde général/techno, 3ème, postbac → no general spec
}

/** Whether the level requires sous_filiere_techno. */
export function requiresSousFiliere(level: NiveauId, filiere: FiliereId | null): boolean {
  return (
    filiere === "techno" &&
    (level === "lycee_1ere" || level === "lycee_terminale")
  );
}

/** Calendar label for the recap card (AC6). */
export function calendarHint(level: NiveauId, intendedTrack: Track3emeId | null): string {
  if (level === "college_3eme") {
    return "Tu seras notifié(e) du calendrier Affelnet à partir de mars.";
  }
  if (level === "lycee_terminale") {
    return "Tu seras notifié(e) du calendrier Parcoursup à partir de novembre.";
  }
  if (level === "lycee_1ere") {
    return "Tu seras notifié(e) des étapes importantes Parcoursup l'année prochaine.";
  }
  if (level === "lycee_2nde") {
    return "On t'informera des prochaines étapes d'orientation.";
  }
  if (level === "postbac") {
    return "On t'aidera à découvrir des pistes, à ton rythme.";
  }
  return "";
}
