/**
 * Adapt onboarding copy to the student's presumed school level (UX-DR30).
 *
 * Bounds — French school system mapped to civil age:
 *   < 15 yo  → `college`  (Mehdi persona)
 *   15-18 yo → `lycee`    (Sarah / Léa personas) — DEFAULT FALLBACK
 *   ≥ 18 yo  → `postbac`  (B2C élargi)
 *
 * The fallback is `lycee` for missing / invalid dates — most statistically
 * neutral. The function is side-effect-free and dependency-free; the
 * caller injects `today` for deterministic testing.
 */

export type SchoolLevel = "college" | "lycee" | "postbac";

const COLLEGE_MAX_AGE_EXCLUSIVE = 15;
const POSTBAC_MIN_AGE_INCLUSIVE = 18;

/**
 * Compute the presumed school level from a birth date.
 * Returns `lycee` as the safe fallback if `birthDate` is null/invalid or in the future.
 */
export function getPresumedLevel(
  birthDate: Date | string | null | undefined,
  today: Date,
): SchoolLevel {
  const dob = parseDate(birthDate);
  if (!dob) return "lycee";
  const age = yearsBetween(dob, today);
  if (age < 0) return "lycee"; // future birth date → corrupted, fallback
  if (age < COLLEGE_MAX_AGE_EXCLUSIVE) return "college";
  if (age >= POSTBAC_MIN_AGE_INCLUSIVE) return "postbac";
  return "lycee";
}

function parseDate(value: Date | string | null | undefined): Date | null {
  if (value == null) return null;
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value;
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function yearsBetween(from: Date, to: Date): number {
  let age = to.getFullYear() - from.getFullYear();
  const monthDiff = to.getMonth() - from.getMonth();
  if (monthDiff < 0 || (monthDiff === 0 && to.getDate() < from.getDate())) {
    age -= 1;
  }
  return age;
}

// --- Copy variants ----------------------------------------------------------
// AC8 — vocabulary changes per presumed level. Referential entries (passions,
// valeurs) stay identical across levels — only enveloping copy varies.

export type OnboardingCopyBundle = {
  readonly passionsTitle: string;
  readonly passionsSubtitle: string;
  readonly valeursTitle: string;
  readonly valeursSubtitle: string;
  readonly interetsTitle: string;
  readonly interetsSubtitle: string;
  readonly interetsPlaceholders: readonly [string, string, string];
};

const COPY_BUNDLES: Readonly<Record<SchoolLevel, OnboardingCopyBundle>> = {
  college: {
    passionsTitle: "Ce qui te branche, en vrai",
    passionsSubtitle: "Choisis-en au moins 3. T'inquiète, tu pourras changer.",
    valeursTitle: "Ce qui te tient à cœur",
    valeursSubtitle: "Choisis 3 à 5 valeurs. Y'a pas de bonne réponse.",
    interetsTitle: "Ce que tu suis, écoutes, regardes",
    interetsSubtitle:
      "3 lignes max, format libre. Une chaîne YouTube, un podcast, un livre, une matière qui t'a marqué — ce que tu veux.",
    interetsPlaceholders: [
      "Ex. La chaîne YouTube de Marie Lopez sur la chimie, ou un podcast Choses à savoir…",
      "Ex. Le bouquin Sapiens, un film comme Hidden Figures, la série Mr Robot…",
      "Ex. La leçon où tu t'es pas ennuyé(e), un débat en cours…",
    ],
  },
  lycee: {
    passionsTitle: "Qu'est-ce qui te plaît, vraiment ?",
    passionsSubtitle: "Choisis-en au moins 3. T'inquiète, tu pourras changer.",
    valeursTitle: "Ce qui compte le plus pour toi",
    valeursSubtitle: "Choisis 3 à 5 valeurs. Y'a pas de bonne réponse.",
    interetsTitle: "Ce que tu suis, écoutes, regardes",
    interetsSubtitle:
      "3 lignes max, format libre. Une chaîne YouTube, un podcast, un livre, une matière qui t'a marqué — ce que tu veux.",
    interetsPlaceholders: [
      "Ex. La chaîne YouTube de Marie Lopez sur la chimie, ou un podcast Choses à savoir…",
      "Ex. Le bouquin Sapiens, un film comme Hidden Figures, la série Mr Robot…",
      "Ex. La séquence sur la photosynthèse en 2nde, un débat en HGGSP, un TP de SVT…",
    ],
  },
  postbac: {
    passionsTitle: "Ce qui t'inspire en ce moment",
    passionsSubtitle: "Choisis-en au moins 3. Tu pourras revenir les modifier à tout moment.",
    valeursTitle: "Ce qui compte le plus pour toi",
    valeursSubtitle: "Choisis 3 à 5 valeurs. Pas de bonne ou mauvaise réponse.",
    interetsTitle: "Ce que tu suis, écoutes, regardes",
    interetsSubtitle:
      "3 lignes max, format libre. Une newsletter, un podcast, un livre pro, un cours qui t'a marqué — ce que tu veux.",
    interetsPlaceholders: [
      "Ex. Une newsletter pro, un podcast comme Génération Do It Yourself…",
      "Ex. Un essai marquant, un film, une série…",
      "Ex. Un cours marquant en L1, un projet de stage, une lecture pro…",
    ],
  },
};

export function getOnboardingCopy(level: SchoolLevel): OnboardingCopyBundle {
  return COPY_BUNDLES[level];
}
