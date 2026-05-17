import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-8 bg-bg p-8 text-center">
      <header className="flex flex-col gap-2">
        <h1 className="text-h1 font-semibold text-text md:text-h1-desktop">Hello Path-Advisor</h1>
        <p className="max-w-md text-body text-text-muted">
          Foundation seed — Story 1.2. Design tokens R1 Vermillon now live across the stack.
        </p>
      </header>

      <section
        aria-labelledby="design-system-showcase"
        className="flex max-w-md flex-col gap-4 rounded-md border border-border bg-bg-2 p-6"
      >
        <h2
          id="design-system-showcase"
          className="text-h3 font-semibold text-text md:text-h3-desktop"
        >
          Design tokens
        </h2>
        <p className="text-body-sm text-text-muted">
          shadcn components are rebranded automatically through CSS variables.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-3">
          <Button>Primary</Button>
          <Button variant="outline">Outline</Button>
          <Button variant="secondary">Secondary</Button>
        </div>
        <p className="text-caption text-text-subtle font-tabular">
          Tabular nums sample: 12 345 / 67 890
        </p>
      </section>
    </main>
  );
}
