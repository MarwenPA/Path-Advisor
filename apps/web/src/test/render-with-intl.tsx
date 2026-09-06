import { render, type RenderOptions } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import type { ReactElement, ReactNode } from "react";

import messages from "../../messages/fr.json";

/**
 * Test helper — Story 7.7. Any component migrated to `useTranslations`
 * needs a `NextIntlClientProvider` ancestor or it throws at render time
 * ("No intl context found"). Wraps the real `messages/fr.json` (not a
 * per-test mock) so a typo'd/renamed key fails the test the same way it
 * would fail in the real app, instead of silently passing against a
 * stale hand-rolled fixture.
 */
export function renderWithIntl(ui: ReactElement, options?: Omit<RenderOptions, "wrapper">) {
  return render(ui, {
    wrapper: ({ children }: { children: ReactNode }) => (
      <NextIntlClientProvider locale="fr" messages={messages}>
        {children}
      </NextIntlClientProvider>
    ),
    ...options,
  });
}
