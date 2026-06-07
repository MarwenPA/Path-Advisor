import type { Config } from "tailwindcss";
import animate from "tailwindcss-animate";

import { pathAdvisorPlugin } from "./src/lib/design-system/tailwind-plugin";

// R1 Vermillon tokens — Story 1.2.
// Decision §4.10: Tailwind v3 (mature, shadcn-compatible).
// Spacing not extended: we curate from Tailwind's default scale (4/8/12/16/24/32/48/64).
// Non-canonical Tailwind defaults like p-5 (20px) and p-10 (40px) still emit — prefer the
// canonical scale documented in the UX spec and call out drift in code review.
const config: Config = {
  content: ["./src/**/*.{ts,tsx,js,jsx,mdx}"],
  theme: {
    extend: {
      // ---------- Colors ----------
      // Every color token is HSL space-separated in tokens.css. Wrapping with
      // `hsl(var(--*))` here lets Tailwind apply opacity modifiers uniformly
      // (`bg-brand/50`, `text-text-muted/80`, etc.) across the whole palette.
      colors: {
        // shadcn semantic palette
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",

        // Path-Advisor custom palette (HSL via CSS vars; supports `/<alpha>` modifiers)
        brand: {
          DEFAULT: "hsl(var(--color-brand))",
          hover: "hsl(var(--color-brand-hover))",
        },
        bg: {
          DEFAULT: "hsl(var(--color-bg))",
          2: "hsl(var(--color-bg-2))",
          3: "hsl(var(--color-bg-3))",
        },
        text: {
          DEFAULT: "hsl(var(--color-text))",
          muted: "hsl(var(--color-text-muted))",
          subtle: "hsl(var(--color-text-subtle))",
        },
        "border-strong": "hsl(var(--color-border-strong))",
        semantic: {
          audacieux: "hsl(var(--color-semantic-audacieux))",
          realiste: "hsl(var(--color-semantic-realiste))",
          sur: "hsl(var(--color-semantic-sur))",
        },
        success: "hsl(var(--color-success))",
        warning: {
          DEFAULT: "hsl(var(--color-warning))",
          bg: "hsl(var(--color-warning-bg))",
        },
        danger: "hsl(var(--color-danger))",
      },

      // ---------- Type scale (mobile-first; use md:text-*-desktop for larger viewports) ----------
      // Usage: <h1 className="text-h1 md:text-h1-desktop font-semibold">
      // Decision §4.10 #1: mobile/desktop twins for the 5 displays that change.
      // fontWeight intentionally omitted from tuples — declare it explicitly per usage
      // so `font-normal` / `font-bold` are no longer order-dependent.
      fontSize: {
        "display-1": ["2.5rem", { lineHeight: "3rem", letterSpacing: "-0.02em" }],
        "display-1-desktop": ["3.5rem", { lineHeight: "4rem", letterSpacing: "-0.02em" }],
        "display-2": ["2rem", { lineHeight: "2.5rem", letterSpacing: "-0.02em" }],
        "display-2-desktop": ["2.5rem", { lineHeight: "3rem", letterSpacing: "-0.02em" }],
        h1: ["1.5rem", { lineHeight: "2rem" }],
        "h1-desktop": ["2rem", { lineHeight: "2.5rem" }],
        h2: ["1.25rem", { lineHeight: "1.75rem" }],
        "h2-desktop": ["1.5rem", { lineHeight: "2rem" }],
        h3: ["1.125rem", { lineHeight: "1.625rem" }],
        "h3-desktop": ["1.25rem", { lineHeight: "1.75rem" }],
        // body / body-sm / caption: identical mobile and desktop (UX spec).
        body: ["1rem", { lineHeight: "1.5rem" }],
        "body-sm": ["0.875rem", { lineHeight: "1.25rem" }],
        caption: ["0.75rem", { lineHeight: "1rem" }],
      },

      // ---------- Font family ----------
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },

      // ---------- Motion ----------
      // Anti-cirque rule: `duration-narrative` is reserved for the journey graph (Epic 4).
      transitionDuration: {
        instant: "100ms",
        quick: "200ms",
        standard: "300ms",
        narrative: "720ms",
      },
      transitionTimingFunction: {
        standard: "cubic-bezier(0.16, 1, 0.3, 1)",
      },

      // ---------- Radius (shadcn standard) ----------
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },

      // ---------- Custom keyframes / animations ----------
      // `scenario-loader-particle`: Story 2.8 AC2 — minimal "signal de vie"
      // pulse on the loader illustration. Disabled by the global
      // reduced-motion reset (tokens.css §reduced-motion).
      keyframes: {
        "scenario-loader-particle": {
          "0%, 100%": { transform: "scale(0.8)", opacity: "0.4" },
          "50%": { transform: "scale(1.1)", opacity: "1" },
        },
        // Story 2.8 AC4 — overrun warning banner enters with fade + 8 px
        // slide-up over motion-quick. Global reduced-motion reset collapses
        // the duration to ~0, leaving the end state visible without movement.
        "scenario-warning-in": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "scenario-loader-particle": "scenario-loader-particle 1800ms ease-out infinite",
        "scenario-warning-in":
          "scenario-warning-in var(--motion-quick) cubic-bezier(0.16,1,0.3,1) forwards",
      },
    },
  },
  plugins: [animate, pathAdvisorPlugin],
};

export default config;
