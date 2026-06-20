import { clsx, type ClassValue } from "clsx";
import { extendTailwindMerge } from "tailwind-merge";

// Register the custom font-size tokens from tailwind.config.ts so tailwind-merge
// classifies them as `font-size` utilities (not generic `text-*`). Without this,
// a custom color token like `text-success` and a custom size like `text-body-sm`
// land in the same conflict group and the last one silently wins — dropping the
// semantic colour. Listing the sizes here keeps `text-{color}` and `text-{size}`
// in distinct groups so both survive a merge.
const twMerge = extendTailwindMerge({
  extend: {
    classGroups: {
      "font-size": [
        {
          text: [
            "display-1",
            "display-1-desktop",
            "display-2",
            "display-2-desktop",
            "h1",
            "h1-desktop",
            "h2",
            "h2-desktop",
            "h3",
            "h3-desktop",
            "body",
            "body-sm",
            "caption",
          ],
        },
      ],
    },
  },
});

/** Conditionally merge Tailwind class names — shadcn's `cn` helper. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
