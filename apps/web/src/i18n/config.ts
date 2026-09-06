/**
 * i18n locale configuration — Story 7.7 (foundation).
 *
 * MVP: a single locale (`fr`), served at the root with no `/fr/` URL
 * prefix (no `next-intl` routing/middleware) — see the story's §4 for
 * why: every public SEO route shipped in Epic 7 (7.1-7.6, 7.8:
 * sitemap, canonical URLs, Open Graph) is already indexed unprefixed,
 * and adding locale-prefixed routing now would break all of it for an
 * AC that only asks for a single `fr` catalog.
 *
 * Growth-phase francophonie (Belgium, Morocco, Tunisia, Senegal — see
 * epics/epic-7-decouverte-publique-seo.md, Story 7.7 AC3): adding a
 * country is `messages/{locale}.json` with overrides, no app code
 * change — but *routing* a second locale (e.g. `/fr-BE/`) is a
 * separate, deliberate story with its own SEO migration (301s), not
 * automatic just because a JSON file exists.
 */
export const LOCALES = ["fr"] as const;
export type AppLocale = (typeof LOCALES)[number];
export const DEFAULT_LOCALE: AppLocale = "fr";
