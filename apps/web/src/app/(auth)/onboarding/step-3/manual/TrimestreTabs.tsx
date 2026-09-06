"use client";

import { Tabs, TabsList, TabsTrigger } from "@radix-ui/react-tabs";

interface TrimestreTabsProps {
  active: number;
  total: number;
  validatedTrims?: number[];
  onSelect: (trim: number) => void;
  onAdd: () => void;
}

export function TrimestreTabs({
  active,
  total,
  validatedTrims = [],
  onSelect,
  onAdd,
}: TrimestreTabsProps) {
  return (
    <Tabs value={String(active)} onValueChange={(v) => onSelect(Number(v))}>
      <TabsList className="mb-4 flex gap-1" role="tablist">
        {Array.from({ length: total }, (_, i) => i + 1).map((t) => (
          <TabsTrigger
            key={t}
            value={String(t)}
            role="tab"
            aria-selected={active === t}
            className="rounded px-3 py-1.5 text-sm data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
          >
            Trim. {t} {validatedTrims.includes(t) ? "✓" : ""}
          </TabsTrigger>
        ))}
        {total < 4 && (
          <button
            type="button"
            onClick={onAdd}
            className="rounded border border-dashed px-3 py-1.5 text-sm text-muted-foreground"
          >
            + Ajouter
          </button>
        )}
      </TabsList>
    </Tabs>
  );
}
