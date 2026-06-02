/**
 * Onboarding step-1 referentials — passions, valeurs, intérêts suggestions.
 *
 * IDs are kebab-case and stored verbatim in the database. Labels and descriptions
 * are display-only and may evolve without migration. Aliases support fuzzy search.
 *
 * IMPORTANT — keep this file in sync with the Python mirror at
 * `apps/api/apps/students/onboarding/referentials.py`. The
 * `test_referentials_sync` pytest enforces ID equality across both sides.
 */

import { z } from "zod";

// --- Passions ---------------------------------------------------------------

export type PassionCategory = {
  readonly id: string;
  readonly label: string;
  readonly aliases: readonly string[];
};

export const PASSIONS_CATEGORIES: readonly PassionCategory[] = [
  { id: "sciences-nature", label: "Sciences & nature", aliases: ["bio", "biologie", "physique", "chimie", "nature"] },
  { id: "tech-code", label: "Tech & code", aliases: ["code", "informatique", "dev", "programmation", "ia"] },
  { id: "arts-creation", label: "Arts & création", aliases: ["dessin", "peinture", "art", "design"] },
  { id: "sport-corps", label: "Sport & corps", aliases: ["sport", "fitness", "danse", "yoga"] },
  { id: "aider-autres", label: "Aider les autres", aliases: ["humanitaire", "social", "associatif", "bénévolat"] },
  { id: "musique", label: "Musique", aliases: ["instrument", "chant", "compo", "rap"] },
  { id: "cinema-series", label: "Cinéma & séries", aliases: ["ciné", "film", "série", "netflix"] },
  { id: "lecture-ecriture", label: "Lecture & écriture", aliases: ["livre", "roman", "écrire", "poésie"] },
  { id: "voyage-cultures", label: "Voyage & cultures", aliases: ["voyage", "langues", "monde", "découverte"] },
  { id: "cuisine", label: "Cuisine", aliases: ["food", "pâtisserie", "cuisiner"] },
  { id: "mode-style", label: "Mode & style", aliases: ["fringues", "style", "couture", "fashion"] },
  { id: "business-argent", label: "Business & argent", aliases: ["entreprendre", "finance", "économie", "business"] },
  { id: "jeux-video", label: "Jeux vidéo", aliases: ["gaming", "esport", "jeu", "console"] },
  { id: "animaux", label: "Animaux", aliases: ["chien", "chat", "vétérinaire", "faune"] },
  { id: "education-transmission", label: "Éducation & transmission", aliases: ["enseigner", "prof", "tuto", "expliquer"] },
  { id: "sante-soin", label: "Santé & soin", aliases: ["médecine", "infirmier", "santé", "bien-être"] },
  { id: "politique-societe", label: "Politique & société", aliases: ["politique", "débat", "société", "actu"] },
  { id: "bricolage-mains", label: "Bricolage & mains", aliases: ["bricoler", "menuiserie", "mécanique", "diy"] },
  { id: "communication-media", label: "Communication & média", aliases: ["média", "journalisme", "marketing", "réseaux"] },
  { id: "spiritualite-sens", label: "Spiritualité & sens", aliases: ["philo", "méditation", "religion", "sens"] },
] as const;

export const PASSION_IDS: readonly string[] = PASSIONS_CATEGORIES.map((p) => p.id);

// --- Valeurs ----------------------------------------------------------------

export type Valeur = {
  readonly id: string;
  readonly label: string;
  readonly description: string;
};

export const VALEURS: readonly Valeur[] = [
  { id: "justice-sociale", label: "Justice sociale", description: "Que les choses soient justes pour tout le monde" },
  { id: "independance", label: "Indépendance", description: "Pouvoir bosser à ton rythme, à ta façon" },
  { id: "securite", label: "Sécurité", description: "Un cadre stable, prévisible" },
  { id: "creativite", label: "Créativité", description: "Inventer, créer, faire des trucs nouveaux" },
  { id: "defi", label: "Défi", description: "Te dépasser, viser haut" },
  { id: "contact-humain", label: "Contact humain", description: "Bosser avec les gens, pour les gens" },
  { id: "reconnaissance", label: "Reconnaissance", description: "Que ton boulot soit vu et respecté" },
  { id: "argent-confort", label: "Argent & confort", description: "Bien gagner ta vie, sans culpabiliser" },
  { id: "apprendre", label: "Apprendre", description: "Comprendre, te former toute ta vie" },
  { id: "nature-vivant", label: "Nature & vivant", description: "Travailler avec / pour le vivant" },
  { id: "aventure", label: "Aventure", description: "Bouger, découvrir, voir du pays" },
  { id: "sens-utilite", label: "Sens & utilité", description: "Faire quelque chose qui sert vraiment" },
] as const;

export const VALEUR_IDS: readonly string[] = VALEURS.map((v) => v.id);

// --- Intérêts suggestions ---------------------------------------------------
// AC4 — chips de suggestion sous chaque champ libre. Tap → injecte le label.
// 5 suggestions par champ pour ne pas saturer l'écran.

export type InteretFieldKey = 1 | 2 | 3;

export const INTERETS_SUGGESTIONS: Readonly<Record<InteretFieldKey, readonly string[]>> = {
  1: ["YouTube", "Podcast", "Livre", "Newsletter", "TikTok"],
  2: ["Film", "Série", "Documentaire", "BD", "Manga"],
  3: ["Matière", "TP", "Projet de classe", "Débat", "Stage"],
} as const;

// --- Custom passion prefix --------------------------------------------------
// AC2 — l'élève peut ajouter jusqu'à 5 passions à lui, préfixées `custom:`.
// Le slug est généré côté client (lowercase + tiret) puis stocké en base
// comme `custom:<slug>` (ex. `custom:graphql`). Validation Zod l'accepte.

export const CUSTOM_PASSION_PREFIX = "custom:" as const;
export const MAX_CUSTOM_PASSIONS = 5;
export const MAX_PASSIONS_TOTAL = 8;
export const MIN_PASSIONS = 3;

export const MIN_VALEURS = 3;
export const MAX_VALEURS = 5;

export const MAX_INTERET_CHARS = 200;

// --- Zod schemas ------------------------------------------------------------

const KNOWN_PASSION_IDS = new Set<string>(PASSION_IDS);
const KNOWN_VALEUR_IDS = new Set<string>(VALEUR_IDS);

/** Slug ASCII: lower-case letters, digits, hyphens; 1-30 chars. */
const customSlugRegex = /^[a-z0-9](?:[a-z0-9-]{0,28}[a-z0-9])?$/;

export const passionIdSchema = z
  .string()
  .min(1)
  .refine(
    (id) => {
      if (KNOWN_PASSION_IDS.has(id)) return true;
      if (!id.startsWith(CUSTOM_PASSION_PREFIX)) return false;
      const slug = id.slice(CUSTOM_PASSION_PREFIX.length);
      return customSlugRegex.test(slug);
    },
    {
      message:
        "Passion ID must be a known referential ID or a `custom:<slug>` (1-30 chars, lowercase ASCII).",
    },
  );

export const valeurIdSchema = z
  .string()
  .refine((id) => KNOWN_VALEUR_IDS.has(id), { message: "Unknown valeur ID." });

export const passionsArraySchema = z
  .array(passionIdSchema)
  .max(MAX_PASSIONS_TOTAL, `Maximum ${MAX_PASSIONS_TOTAL} passions total.`)
  .refine(
    (arr) => arr.filter((id) => id.startsWith(CUSTOM_PASSION_PREFIX)).length <= MAX_CUSTOM_PASSIONS,
    { message: `Maximum ${MAX_CUSTOM_PASSIONS} custom passions.` },
  )
  .refine((arr) => new Set(arr).size === arr.length, { message: "Passion IDs must be unique." });

export const valeursArraySchema = z
  .array(valeurIdSchema)
  .max(MAX_VALEURS, `Maximum ${MAX_VALEURS} valeurs.`)
  .refine((arr) => new Set(arr).size === arr.length, { message: "Valeur IDs must be unique." });

export const interetsRecordSchema = z.object({
  "1": z.string().max(MAX_INTERET_CHARS).nullable(),
  "2": z.string().max(MAX_INTERET_CHARS).nullable(),
  "3": z.string().max(MAX_INTERET_CHARS).nullable(),
});

// --- Search helpers ---------------------------------------------------------

/** Case-insensitive accent-insensitive match on label + aliases. */
export function filterPassions(query: string): readonly PassionCategory[] {
  const normalized = normalize(query);
  if (!normalized) return PASSIONS_CATEGORIES;
  return PASSIONS_CATEGORIES.filter((p) => {
    if (normalize(p.label).includes(normalized)) return true;
    return p.aliases.some((alias) => normalize(alias).includes(normalized));
  });
}

function normalize(s: string): string {
  return s
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .trim();
}

/** Make a custom passion ID from a user-typed label. Returns null if invalid. */
export function makeCustomPassionId(label: string): string | null {
  const slug = normalize(label).replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  if (!customSlugRegex.test(slug)) return null;
  return `${CUSTOM_PASSION_PREFIX}${slug}`;
}
