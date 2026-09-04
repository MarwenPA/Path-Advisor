/**
 * Client for `/api/v1/mes-paris/` — Story 8.8 §4.3 / T2.
 *
 * Extracted as a small dedicated client (rather than an inline `apiFetch`
 * call as `/mes-paris/page.tsx` does today) purely for testability: the
 * `/accueil` page tests need to mock this module the same way
 * `app/page.test.tsx` mocks `@/lib/api/auth`, without reaching for a global
 * `fetch` mock. `/mes-paris/page.tsx` itself is left untouched (out of
 * scope — see story §4.3).
 */
import { apiFetch } from "./client";
import type { School } from "./schools";

export async function fetchMesParis(): Promise<School[]> {
  return apiFetch<School[]>("/api/v1/mes-paris/");
}
