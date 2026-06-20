"use client";

import * as React from "react";
import { Check, Plus, Search, X } from "lucide-react";

import { Input } from "@/components/ui/input";
import {
  CUSTOM_PASSION_PREFIX,
  MAX_CUSTOM_PASSIONS,
  MAX_PASSIONS_TOTAL,
  MIN_PASSIONS,
  PASSIONS_CATEGORIES,
  filterPassions,
  makeCustomPassionId,
} from "@/lib/onboarding/referentials";
import { cn } from "@/lib/utils";

/**
 * `<PassionsPicker>` — Story 2.1 §AC2. Sub-step 1A.
 *
 * Two stacked picker surfaces:
 *  - **Curated chips** (the 20 PASSIONS_CATEGORIES) — filtered live by a
 *    debounced search input (`searchDebounceMs`, default 150 ms per spec).
 *    Each chip is a toggle: tap to select, tap again to deselect.
 *  - **Custom chips** — the user can add up to `MAX_CUSTOM_PASSIONS`
 *    free-form passions via an inline `+ Ajouter` button. Slugified with
 *    `makeCustomPassionId` (lowercase ASCII, kebab-case, ≤ 30 chars).
 *
 * The orchestrator owns the `selected` state — this component is a
 * controlled input. `onChange` always receives the FULL new list so
 * the caller can persist it as-is on PATCH.
 *
 * Bounds enforced visually (atténué chips at MAX_PASSIONS_TOTAL) AND in
 * `handleToggle` — adding past the cap is silently ignored so a stray
 * double-tap on a flaky touch screen doesn't corrupt the state.
 *
 * SR announcements live in the orchestrator's `aria-live="polite"`
 * region; this component just keeps `aria-checked` and `aria-disabled`
 * accurate so RTL queries can assert state directly.
 */

export type PassionsPickerProps = {
  selected: readonly string[];
  onChange: (next: readonly string[]) => void;
  /** Override the search debounce (ms). Default 150 per AC2. Tests pass 0
   *  to drop the timer and assert synchronously. */
  searchDebounceMs?: number;
};

const DEFAULT_DEBOUNCE_MS = 150;

export function PassionsPicker({
  selected,
  onChange,
  searchDebounceMs = DEFAULT_DEBOUNCE_MS,
}: PassionsPickerProps) {
  const [rawQuery, setRawQuery] = React.useState("");
  const [debouncedQuery, setDebouncedQuery] = React.useState("");
  const [customInputOpen, setCustomInputOpen] = React.useState(false);
  const [customDraft, setCustomDraft] = React.useState("");
  const [customError, setCustomError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (searchDebounceMs <= 0) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setDebouncedQuery(rawQuery);
      return;
    }
    const handle = window.setTimeout(() => setDebouncedQuery(rawQuery), searchDebounceMs);
    return () => window.clearTimeout(handle);
  }, [rawQuery, searchDebounceMs]);

  const filtered = React.useMemo(() => filterPassions(debouncedQuery), [debouncedQuery]);

  const selectedSet = React.useMemo(() => new Set(selected), [selected]);
  const customCount = React.useMemo(
    () => selected.filter((id) => id.startsWith(CUSTOM_PASSION_PREFIX)).length,
    [selected],
  );
  const isAtMax = selected.length >= MAX_PASSIONS_TOTAL;
  const atOrAboveMinimum = selected.length >= MIN_PASSIONS;
  const customLabelOf = (id: string): string =>
    id.startsWith(CUSTOM_PASSION_PREFIX) ? id.slice(CUSTOM_PASSION_PREFIX.length) : id;

  const handleToggle = (id: string) => {
    if (selectedSet.has(id)) {
      onChange(selected.filter((existing) => existing !== id));
      return;
    }
    // Defensive max guard — UI already atténues non-selected chips at the
    // cap, but a focused-then-Enter keyboard sequence could race past the
    // visual disable.
    if (isAtMax) return;
    onChange([...selected, id]);
  };

  const handleAddCustom = () => {
    const trimmed = customDraft.trim();
    if (!trimmed) {
      setCustomError("Renseigne un mot, sinon laisse tomber.");
      return;
    }
    if (customCount >= MAX_CUSTOM_PASSIONS) {
      setCustomError(`Maximum ${MAX_CUSTOM_PASSIONS} propositions à toi.`);
      return;
    }
    if (selected.length >= MAX_PASSIONS_TOTAL) {
      setCustomError(`Maximum ${MAX_PASSIONS_TOTAL} passions — désélectionne pour en changer.`);
      return;
    }
    const id = makeCustomPassionId(trimmed);
    if (!id) {
      setCustomError("Lettres, chiffres et tirets seulement (max 30 caractères).");
      return;
    }
    if (selectedSet.has(id)) {
      setCustomError("Tu l'as déjà ajouté.");
      return;
    }
    onChange([...selected, id]);
    setCustomDraft("");
    setCustomError(null);
    setCustomInputOpen(false);
  };

  return (
    <div className="flex flex-col gap-4">
      {/* AC2 — search filter */}
      <div className="relative">
        <Search
          aria-hidden
          className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-subtle"
        />
        <Input
          type="search"
          value={rawQuery}
          onChange={(event) => setRawQuery(event.target.value)}
          placeholder="Cherche par mot-clé (ex. cinéma, sport, code…)"
          aria-label="Filtrer les passions"
          className="pl-9 pr-9"
          data-testid="passions-search"
        />
        {rawQuery ? (
          <button
            type="button"
            onClick={() => setRawQuery("")}
            aria-label="Effacer la recherche"
            className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1 text-text-subtle hover:text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <X aria-hidden className="h-4 w-4" />
          </button>
        ) : null}
      </div>

      {/* AC2 — referential chip grid */}
      <div
        role="group"
        aria-label="Catégories de passions"
        className="flex flex-wrap gap-2"
        data-testid="passions-chip-grid"
      >
        {filtered.map((category) => {
          const isSelected = selectedSet.has(category.id);
          const isDisabled = !isSelected && isAtMax;
          return (
            <button
              key={category.id}
              type="button"
              role="checkbox"
              aria-checked={isSelected}
              aria-disabled={isDisabled || undefined}
              onClick={() => handleToggle(category.id)}
              disabled={isDisabled}
              data-passion-id={category.id}
              className={cn(
                "inline-flex min-h-11 items-center gap-2 rounded-full border px-3 py-1.5 text-body-sm font-medium",
                "transition-colors duration-instant ease-standard",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                isSelected
                  ? "border-brand bg-brand text-white"
                  : "border-border bg-bg text-text hover:bg-bg-2",
                isDisabled && "cursor-not-allowed opacity-60",
              )}
            >
              {isSelected ? <Check aria-hidden className="h-4 w-4" /> : null}
              <span>{category.label}</span>
            </button>
          );
        })}
        {filtered.length === 0 ? (
          <p className="text-body-sm text-text-muted">
            Pas dans la liste ? Ajoute-le toi-même via <span className="font-medium">+ Ajouter</span>.
          </p>
        ) : null}
      </div>

      {/* AC2 — custom passions */}
      <div className="flex flex-col gap-2">
        {!customInputOpen ? (
          <button
            type="button"
            onClick={() => {
              setCustomInputOpen(true);
              setCustomError(null);
            }}
            disabled={customCount >= MAX_CUSTOM_PASSIONS || isAtMax}
            data-testid="passions-add-custom-trigger"
            className={cn(
              "inline-flex w-fit min-h-11 items-center gap-1 self-start rounded-md px-3 py-2 text-body-sm font-medium text-brand underline underline-offset-4",
              "hover:text-brand-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              (customCount >= MAX_CUSTOM_PASSIONS || isAtMax) && "cursor-not-allowed opacity-60 no-underline",
            )}
          >
            <Plus aria-hidden className="h-4 w-4" />
            Ajouter une passion à toi
          </button>
        ) : (
          <div className="flex flex-col gap-2">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-stretch">
              <Input
                value={customDraft}
                onChange={(event) => {
                  setCustomDraft(event.target.value);
                  setCustomError(null);
                }}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    event.preventDefault();
                    handleAddCustom();
                  }
                }}
                placeholder="Ta passion (ex. graphisme, escalade…)"
                aria-label="Nouvelle passion personnelle"
                maxLength={30}
                autoFocus
                data-testid="passions-custom-input"
                className="flex-1"
              />
              <button
                type="button"
                onClick={handleAddCustom}
                className="inline-flex min-h-11 items-center justify-center rounded-md border border-brand bg-brand px-4 py-2 text-body-sm font-medium text-white hover:bg-brand-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              >
                Ajouter
              </button>
              <button
                type="button"
                onClick={() => {
                  setCustomInputOpen(false);
                  setCustomDraft("");
                  setCustomError(null);
                }}
                className="inline-flex min-h-11 items-center justify-center rounded-md border border-border-strong bg-transparent px-4 py-2 text-body-sm font-medium text-text hover:bg-bg-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              >
                Annuler
              </button>
            </div>
            {customError ? (
              <p role="status" className="text-caption text-danger" data-testid="passions-custom-error">
                {customError}
              </p>
            ) : null}
          </div>
        )}

        {customCount > 0 ? (
          <ul className="flex flex-wrap gap-2" aria-label="Tes passions personnelles">
            {selected
              .filter((id) => id.startsWith(CUSTOM_PASSION_PREFIX))
              .map((id) => (
                <li key={id}>
                  <span
                    className="inline-flex min-h-11 items-center gap-2 rounded-full border border-brand bg-brand px-3 py-1.5 text-body-sm font-medium text-white"
                    data-passion-id={id}
                  >
                    <Check aria-hidden className="h-4 w-4" />
                    <span>{customLabelOf(id)}</span>
                    <button
                      type="button"
                      onClick={() => handleToggle(id)}
                      aria-label={`Retirer ${customLabelOf(id)}`}
                      className="rounded-full p-0.5 hover:bg-brand-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    >
                      <X aria-hidden className="h-3 w-3" />
                    </button>
                  </span>
                </li>
              ))}
          </ul>
        ) : null}
      </div>

      {/* AC2 + Pass 1 M4 — when the 8-max is reached, surface a dedicated
          helper in `text-warning` next to the chip grid (spec wording). Live
          announcement is owned by the orchestrator (M3 — single
          `aria-live`), so this helper is presentational only — `role="note"`
          + no `aria-live` to avoid the per-screen live-region cascade. */}
      {isAtMax ? (
        <p
          role="note"
          className="text-caption text-warning"
          data-testid="passions-max-helper"
        >
          Maximum {MAX_PASSIONS_TOTAL} — désélectionne pour en changer.
        </p>
      ) : null}

      {/* AC2 — discrete counter. Pass 1 M3 — `aria-live` removed; the
          orchestrator announces threshold transitions in one region. */}
      <p
        className={cn(
          "self-end text-caption",
          atOrAboveMinimum ? "text-success" : "text-text-subtle",
        )}
        data-testid="passions-counter"
      >
        {atOrAboveMinimum
          ? `${selected.length} / ${MIN_PASSIONS} minimum atteint`
          : `${selected.length} / ${MIN_PASSIONS} minimum`}
      </p>
    </div>
  );
}
