/**
 * next-intl configuration stub.
 *
 * Story 1.1 seed: locale skeleton only. Story 7.7 will wire actual routing
 * (`/fr/...`) and message files under `messages/{locale}.json`.
 */

export const defaultLocale = "fr" as const;
export const locales = ["fr"] as const;

export type Locale = (typeof locales)[number];
