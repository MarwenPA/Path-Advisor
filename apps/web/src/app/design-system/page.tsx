import type { Metadata } from "next";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import { ConsentDialogDemos } from "./_components/consent-dialog-demos";
import { DialogDemo } from "./_components/dialog-demo";

export const metadata: Metadata = {
  title: "Design system — Path-Advisor",
  description: "Living reference for the R1 Vermillon tokens — colors, type, spacing, motion.",
};

type Swatch = {
  name: string;
  className: string;
  hex: string;
  note?: string;
};

type SwatchGroup = {
  title: string;
  swatches: Swatch[];
};

const COLOR_GROUPS: SwatchGroup[] = [
  {
    title: "Brand",
    swatches: [
      { name: "brand", className: "bg-brand", hex: "#C8312D", note: "5.2:1 on bg (AA)" },
      { name: "brand-hover", className: "bg-brand-hover", hex: "#A6231F" },
    ],
  },
  {
    title: "Surfaces",
    swatches: [
      { name: "bg", className: "bg-bg border border-border", hex: "#FAFAF7" },
      { name: "bg-2", className: "bg-bg-2", hex: "#F4F1ED" },
      { name: "bg-3", className: "bg-bg-3", hex: "#EBE7E1" },
    ],
  },
  {
    title: "Text",
    swatches: [
      { name: "text", className: "bg-text", hex: "#1A1A1A", note: "16.8:1 on bg (AAA)" },
      { name: "text-muted", className: "bg-text-muted", hex: "#666660", note: "5.6:1 on bg (AA)" },
      { name: "text-subtle", className: "bg-text-subtle", hex: "#8C8C86", note: "large text only" },
    ],
  },
  {
    title: "Borders",
    swatches: [
      { name: "border", className: "bg-border", hex: "#E0DDD8" },
      { name: "border-strong", className: "bg-border-strong", hex: "#C9C5BE" },
    ],
  },
  {
    title: "Semantic — admission bets",
    swatches: [
      {
        name: "semantic-audacieux",
        className: "bg-semantic-audacieux",
        hex: "#A85428",
        note: "“pari audacieux”",
      },
      {
        name: "semantic-realiste",
        className: "bg-semantic-realiste",
        hex: "#2F6B4F",
        note: "“pari réaliste”",
      },
      { name: "semantic-sur", className: "bg-semantic-sur", hex: "#3A7CA5", note: "“pari sûr”" },
    ],
  },
  {
    title: "Status",
    swatches: [
      { name: "success", className: "bg-success", hex: "#2F6B4F" },
      { name: "warning", className: "bg-warning", hex: "#C7841B" },
      { name: "danger", className: "bg-danger", hex: "#9E2A24", note: "~6.8:1 on bg (AA)" },
    ],
  },
];

type TypeSample = {
  token: string;
  mobile: string;
  desktop: string;
  className: string;
  sample: string;
};

const TYPE_SAMPLES: TypeSample[] = [
  {
    token: "display-1",
    mobile: "40 / 48",
    desktop: "56 / 64",
    className: "text-display-1 md:text-display-1-desktop font-semibold",
    sample: "Trouve ta voie",
  },
  {
    token: "display-2",
    mobile: "32 / 40",
    desktop: "40 / 48",
    className: "text-display-2 md:text-display-2-desktop font-semibold",
    sample: "Un parcours qui te ressemble",
  },
  {
    token: "h1",
    mobile: "24 / 32",
    desktop: "32 / 40",
    className: "text-h1 md:text-h1-desktop font-semibold",
    sample: "Tes 8 métiers recommandés",
  },
  {
    token: "h2",
    mobile: "20 / 28",
    desktop: "24 / 32",
    className: "text-h2 md:text-h2-desktop font-semibold",
    sample: "Ingénieur biomédical",
  },
  {
    token: "h3",
    mobile: "18 / 26",
    desktop: "20 / 28",
    className: "text-h3 md:text-h3-desktop font-semibold",
    sample: "Tes chances d'admission",
  },
  {
    token: "body",
    mobile: "16 / 24",
    desktop: "16 / 24",
    className: "text-body",
    sample:
      "Path-Advisor accompagne chaque élève de la 3ᵉ aux premières années post-bac avec une orientation continue, défendable et explicable.",
  },
  {
    token: "body-sm",
    mobile: "14 / 20",
    desktop: "14 / 20",
    className: "text-body-sm text-text-muted",
    sample: "Texte secondaire utilisé pour les annotations, hints, métadonnées.",
  },
  {
    token: "caption",
    mobile: "12 / 16",
    desktop: "12 / 16",
    className: "text-caption text-text-subtle uppercase tracking-wide",
    sample: "Mis à jour il y a 3 jours",
  },
];

type Spacing = { token: string; pixels: number; widthClass: string };

const SPACINGS: Spacing[] = [
  { token: "1", pixels: 4, widthClass: "w-1" },
  { token: "2", pixels: 8, widthClass: "w-2" },
  { token: "3", pixels: 12, widthClass: "w-3" },
  { token: "4", pixels: 16, widthClass: "w-4" },
  { token: "6", pixels: 24, widthClass: "w-6" },
  { token: "8", pixels: 32, widthClass: "w-8" },
  { token: "12", pixels: 48, widthClass: "w-12" },
  { token: "16", pixels: 64, widthClass: "w-16" },
];

type Motion = {
  token: string;
  ms: number;
  durationClass: string;
  note?: string;
};

const MOTIONS: Motion[] = [
  { token: "instant", ms: 100, durationClass: "duration-instant" },
  { token: "quick", ms: 200, durationClass: "duration-quick" },
  { token: "standard", ms: 300, durationClass: "duration-standard" },
  {
    token: "narrative",
    ms: 720,
    durationClass: "duration-narrative",
    note: "Reserved for the journey graph (Epic 4).",
  },
];

export default function DesignSystemPage() {
  return (
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-16 bg-bg px-6 py-16 text-text">
      <header className="flex flex-col gap-3">
        <p className="text-caption uppercase tracking-wide text-text-subtle">
          Story 1.2 — Living reference
        </p>
        <h1 className="text-display-2 font-semibold md:text-display-2-desktop">
          Design system R1 Vermillon
        </h1>
        <p className="max-w-2xl text-body text-text-muted">
          One source of truth for every token shipped in the foundation. If a need is not covered
          here, extend <code className="rounded bg-bg-2 px-1.5 py-0.5 text-sm">tokens.css</code> and{" "}
          <code className="rounded bg-bg-2 px-1.5 py-0.5 text-sm">tailwind.config.ts</code> in
          lockstep rather than hardcoding a value in a component.
        </p>
      </header>

      <section aria-labelledby="palette-heading" className="flex flex-col gap-8">
        <div className="flex flex-col gap-2">
          <h2 id="palette-heading" className="text-h1 font-semibold md:text-h1-desktop">
            Palette
          </h2>
          <p className="max-w-2xl text-body text-text-muted">
            17 tokens organised by intent. Contrast ratios are validated in CI via{" "}
            <code className="rounded bg-bg-2 px-1.5 py-0.5 text-sm">contrast.test.ts</code>.
          </p>
        </div>

        {COLOR_GROUPS.map((group) => (
          <div key={group.title} className="flex flex-col gap-4">
            <h3 className="text-h3 font-semibold text-text-muted md:text-h3-desktop">
              {group.title}
            </h3>
            <ul className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
              {group.swatches.map((swatch) => (
                <li
                  key={swatch.name}
                  className="flex flex-col gap-3 rounded-md border border-border bg-bg p-3"
                >
                  <div className={`${swatch.className} h-20 w-full rounded`} aria-hidden="true" />
                  <div className="flex flex-col gap-1">
                    <code className="text-body-sm font-medium text-text">{swatch.name}</code>
                    <span className="font-mono text-caption text-text-muted">{swatch.hex}</span>
                    {swatch.note ? (
                      <span className="text-caption text-text-subtle">{swatch.note}</span>
                    ) : null}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </section>

      <section aria-labelledby="type-heading" className="flex flex-col gap-8">
        <div className="flex flex-col gap-2">
          <h2 id="type-heading" className="text-h1 font-semibold md:text-h1-desktop">
            Typography
          </h2>
          <p className="max-w-2xl text-body text-text-muted">
            Inter variable, loaded via{" "}
            <code className="rounded bg-bg-2 px-1.5 py-0.5 text-sm">next/font</code>. Display and
            heading tokens ship in mobile/desktop pairs — apply the desktop variant with the{" "}
            <code className="rounded bg-bg-2 px-1.5 py-0.5 text-sm">md:</code> prefix.
          </p>
        </div>

        <ul className="flex flex-col divide-y divide-border">
          {TYPE_SAMPLES.map((sample) => (
            <li key={sample.token} className="grid gap-2 py-6 md:grid-cols-[200px_1fr] md:gap-8">
              <div className="flex flex-col gap-1">
                <code className="text-body-sm font-medium text-text">{sample.token}</code>
                <span className="font-mono text-caption text-text-muted">
                  {sample.mobile} / md:{sample.desktop}
                </span>
              </div>
              <p className={sample.className}>{sample.sample}</p>
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="spacing-heading" className="flex flex-col gap-8">
        <div className="flex flex-col gap-2">
          <h2 id="spacing-heading" className="text-h1 font-semibold md:text-h1-desktop">
            Spacing
          </h2>
          <p className="max-w-2xl text-body text-text-muted">
            Curated 4 px scale (Tailwind defaults filtered). Non-canonical values like{" "}
            <code className="rounded bg-bg-2 px-1.5 py-0.5 text-sm">p-5</code> still emit — prefer
            the scale below and flag drift in code review.
          </p>
        </div>
        <ul className="flex flex-col gap-3">
          {SPACINGS.map((s) => (
            <li key={s.token} className="grid grid-cols-[80px_80px_1fr] items-center gap-4">
              <code className="text-body-sm font-medium text-text">{s.token}</code>
              <span className="font-mono text-caption text-text-muted">{s.pixels} px</span>
              <span className={`${s.widthClass} h-4 rounded-sm bg-brand`} aria-hidden="true" />
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="motion-heading" className="flex flex-col gap-8">
        <div className="flex flex-col gap-2">
          <h2 id="motion-heading" className="text-h1 font-semibold md:text-h1-desktop">
            Motion
          </h2>
          <p className="max-w-2xl text-body text-text-muted">
            Hover each card to play the transition. All durations short-circuit to ~0 ms under{" "}
            <code className="rounded bg-bg-2 px-1.5 py-0.5 text-sm">prefers-reduced-motion</code>.
          </p>
        </div>
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {MOTIONS.map((m) => (
            <li
              key={m.token}
              className="group flex flex-col gap-3 rounded-md border border-border bg-bg p-4"
            >
              <div className="relative h-16 overflow-hidden rounded bg-bg-2">
                <span
                  className={`absolute left-2 top-1/2 h-8 w-8 -translate-y-1/2 rounded bg-brand transition-transform ease-standard group-hover:translate-x-[calc(100%+1rem)] ${m.durationClass}`}
                  aria-hidden="true"
                />
              </div>
              <div className="flex flex-col gap-1">
                <code className="text-body-sm font-medium text-text">{m.token}</code>
                <span className="font-mono text-caption text-text-muted">{m.ms} ms</span>
                {m.note ? <span className="text-caption text-text-subtle">{m.note}</span> : null}
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="components-heading" className="flex flex-col gap-8">
        <div className="flex flex-col gap-2">
          <h2 id="components-heading" className="text-h1 font-semibold md:text-h1-desktop">
            Components
          </h2>
          <p className="max-w-2xl text-body text-text-muted">
            shadcn primitives rebranded through the semantic aliases declared in{" "}
            <code className="rounded bg-bg-2 px-1.5 py-0.5 text-sm">tokens.css</code>. No component
            overrides the palette directly.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Buttons — variants</CardTitle>
              <CardDescription>
                Six variants × four sizes ship out of the box. Focus ring is brand-coloured via
                <code className="rounded bg-bg px-1 text-xs"> --color-focus-ring</code>.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <div className="flex flex-wrap gap-2">
                <Button>Default</Button>
                <Button variant="secondary">Secondary</Button>
                <Button variant="outline">Outline</Button>
                <Button variant="ghost">Ghost</Button>
                <Button variant="link">Link</Button>
                <Button variant="destructive">Destructive</Button>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <Button size="sm">Small</Button>
                <Button>Default</Button>
                <Button size="lg">Large</Button>
                <Button disabled>Disabled</Button>
              </div>
            </CardContent>
            <CardFooter>
              <p className="text-caption text-text-subtle">
                Tab through the buttons to verify the 2 px brand focus ring.
              </p>
            </CardFooter>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Form primitives</CardTitle>
              <CardDescription>
                Label + Input pairs. Labels above (UX-DR35), validation on blur — not yet shown.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <div className="flex flex-col gap-2">
                <Label htmlFor="ds-email">Email</Label>
                <Input id="ds-email" type="email" placeholder="sarah@lycee.fr" />
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="ds-school">School</Label>
                <Input id="ds-school" placeholder="Lycée Henri-IV" disabled />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Dialog</CardTitle>
              <CardDescription>
                Radix-backed primitive — focus trap, ESC to close, scroll lock. Wired for the
                ConsentDialog component (Story 1.14).
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DialogDemo />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Surfaces</CardTitle>
              <CardDescription>
                Three background tiers compose every layout. The card itself sits on{" "}
                <code className="rounded bg-bg px-1 text-xs">bg-2</code>.
              </CardDescription>
            </CardHeader>
            <CardContent className="grid grid-cols-3 gap-3">
              <div className="flex h-20 items-center justify-center rounded border border-border bg-bg">
                <code className="text-caption">bg</code>
              </div>
              <div className="flex h-20 items-center justify-center rounded bg-bg-2">
                <code className="text-caption">bg-2</code>
              </div>
              <div className="flex h-20 items-center justify-center rounded bg-bg-3">
                <code className="text-caption">bg-3</code>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      <section
        id="consent-dialog-heading"
        aria-labelledby="consent-dialog-title"
        className="flex flex-col gap-8"
      >
        <div className="flex flex-col gap-2">
          <h2 id="consent-dialog-title" className="text-h1 font-semibold md:text-h1-desktop">
            Consent dialog
          </h2>
          <p className="max-w-2xl text-body text-text-muted">
            Couche 3 composite component (Story 1.14). Three MVP cases shown live, plus a
            destructive preview of account deletion (Story 1.12). Hover, focus, keyboard and
            ESC-test the triggers — both buttons must feel equally weighted (no dark pattern), the X
            close button is intentionally absent (every dismissal is an explicit Refuse).
          </p>
          <p className="max-w-2xl text-body-sm text-text-subtle">
            Open DevTools → Console to inspect the <code>ConsentMeta</code> emitted on Accept
            (timestamp + SHA-256 content hash — Story 1.13 will persist these to the audit log).
          </p>
        </div>
        <ConsentDialogDemos />
      </section>
    </main>
  );
}
