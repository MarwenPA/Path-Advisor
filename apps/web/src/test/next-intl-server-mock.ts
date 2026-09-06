import messages from "../../messages/fr.json";

/**
 * Story 7.7 — `next-intl/server` resolves to its `react-client` build under
 * Vitest (no `react-server` condition configured), which throws
 * ("getTranslations is not supported in Client Components") for any Server
 * Component that calls it. Real Next.js resolves the `react-server` build
 * instead — this only affects the test runner, not the app.
 *
 * Use in a test file via:
 *   vi.mock("next-intl/server", () => import("@/test/next-intl-server-mock"));
 *
 * Reads the real `messages/fr.json` (not a per-test fixture) so a
 * renamed/typo'd key fails the test the same way it fails in the app.
 */
function get(namespace: string | undefined, obj: unknown): unknown {
  if (!namespace) return obj;
  return namespace
    .split(".")
    .reduce((acc: unknown, key) => (acc as Record<string, unknown> | undefined)?.[key], obj);
}

export async function getTranslations(namespace?: string) {
  const scoped = get(namespace, messages);
  return (key: string, values?: Record<string, string | number>) => {
    let str = get(key, scoped);
    if (typeof str !== "string") {
      throw new Error(`[next-intl-server-mock] missing key "${namespace ?? ""}.${key}"`);
    }
    if (values) {
      for (const [k, v] of Object.entries(values)) {
        str = (str as string).replaceAll(`{${k}}`, String(v));
      }
    }
    return str as string;
  };
}

export async function getMessages() {
  return messages;
}
