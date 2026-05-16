import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <main className="bg-bg flex flex-1 flex-col items-center justify-center gap-8 p-8 text-center">
      <header className="flex flex-col gap-2">
        <h1 className="text-h1 md:text-h1-desktop text-text font-semibold">Hello Path-Advisor</h1>
        <p className="text-body text-text-muted max-w-md">
          Foundation seed — Story 1.2. Design tokens R1 Vermillon now live across the stack.
        </p>
      </header>

      <section
        aria-labelledby="design-system-showcase"
        className="bg-bg-2 border-border flex max-w-md flex-col gap-4 rounded-md border p-6"
      >
        <h2
          id="design-system-showcase"
          className="text-h3 md:text-h3-desktop text-text font-semibold"
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
