import plugin from "tailwindcss/plugin";

/**
 * Path-Advisor custom Tailwind utilities.
 *
 * Add new utilities here rather than in `tokens.css` so they remain composable
 * with Tailwind variants (`hover:`, `md:`, future `dark:`, etc.) and surface in
 * IntelliSense.
 *
 * Note: `font-tabular` and letter-spacing utilities (`tracking-*`) conflict —
 * tabular numerals are designed to align in fixed columns, while tracking
 * stretches them apart. Use one or the other on the same element.
 */
export const pathAdvisorPlugin = plugin(({ addUtilities }) => {
  addUtilities({
    ".font-tabular": {
      "font-feature-settings": '"tnum"',
      "font-variant-numeric": "tabular-nums",
    },
  });
});
