import type { Config } from "tailwindcss";

// Tokens R1 Vermillon will be wired here in Story 1.2.
// Story 1.1 §4.10 decision: Tailwind v3 (mature, shadcn-compatible).
const config: Config = {
  content: ["./src/**/*.{ts,tsx,js,jsx,mdx}"],
  theme: {
    extend: {},
  },
  plugins: [],
};

export default config;
