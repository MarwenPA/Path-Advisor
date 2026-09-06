import { getRequestConfig } from "next-intl/server";

import { DEFAULT_LOCALE } from "./config";

/**
 * `next-intl` request configuration — Story 7.7.
 *
 * No `[locale]` route segment exists (see `./config.ts` for why), so
 * there is no real per-request locale to read from the URL — this
 * always resolves to the single MVP locale (`fr`). When a second
 * locale is actually routed (growth phase), this is the file that
 * gains a real `requestLocale` read.
 */
export default getRequestConfig(async () => {
  const locale = DEFAULT_LOCALE;

  return {
    locale,
    messages: (await import(`../../messages/${locale}.json`)).default,
  };
});
