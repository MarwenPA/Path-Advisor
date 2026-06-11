"use client";

import * as React from "react";

import { Textarea } from "@/components/ui/textarea";
import { INTERETS_SUGGESTIONS, MAX_INTERET_CHARS } from "@/lib/onboarding/referentials";
import type { OnboardingInterets } from "@/lib/api/onboarding";
import { cn } from "@/lib/utils";

/**
 * `<InteretsFreeForm>` — Story 2.1 §AC4. Sub-step 1C.
 *
 * Three optional free-form fields with suggestion chips. The orchestrator
 * passes a single `value` object indexed by field key, and a single
 * `onChange` that returns the full triplet — keeps state ownership flat
 * with the PATCH shape (no per-field plumbing in the parent).
 *
 * The character counter switches color at 90% / 97% of the cap so users
 * see the soft-warning before they actually clip. The hard validation
 * (`maxLength`) is browser-enforced.
 */

const FIELD_KEYS = ["1", "2", "3"] as const;
type FieldKey = (typeof FIELD_KEYS)[number];

const FIELD_PLACEHOLDERS: Record<FieldKey, string> = {
  "1": "Ex. La chaîne YouTube de Marie Lopez sur la chimie, ou un podcast Choses à savoir…",
  "2": "Ex. Le bouquin Sapiens, un film comme Hidden Figures, la série Mr Robot…",
  "3": "Ex. La séquence sur la photosynthèse en 2nde, un débat en HGGSP, un TP de SVT…",
};

const FIELD_LABELS: Record<FieldKey, string> = {
  "1": "Une chaîne, un podcast ou une newsletter qui t'a marqué",
  "2": "Un livre, un film, une série",
  "3": "Une matière, un TP, un projet de classe",
};

export type InteretsFreeFormProps = {
  value: OnboardingInterets;
  onChange: (next: OnboardingInterets) => void;
  /** Override the per-field copy (Story 2.1 §AC8 — copy per niveau scolaire).
   *  The fallback is the lycée variant baked above. */
  placeholdersOverride?: Readonly<[string, string, string]>;
};

export function InteretsFreeForm({ value, onChange, placeholdersOverride }: InteretsFreeFormProps) {
  const placeholders: Record<FieldKey, string> = placeholdersOverride
    ? { "1": placeholdersOverride[0], "2": placeholdersOverride[1], "3": placeholdersOverride[2] }
    : FIELD_PLACEHOLDERS;

  // Pass 1 M5 — keep a ref per textarea so the suggestion-tap can restore
  // focus on the field after injection.
  const fieldRefs = React.useRef<Record<FieldKey, HTMLTextAreaElement | null>>({
    "1": null,
    "2": null,
    "3": null,
  });

  const handleFieldChange = (key: FieldKey, newText: string) => {
    onChange({ ...value, [key]: newText.length === 0 ? null : newText });
  };

  // Pass 1 M5 — suggestion behavior: INJECT (replace) the field text and
  // return focus to the textarea. Previously appended with " · " separator,
  // which the spec doesn't ask for and accumulates noise across taps. The
  // Pass 1 M7 cap guard is now redundant for the simple replace path, but
  // kept for callers using `placeholdersOverride` with long suggestion text.
  const handleSuggestionTap = (key: FieldKey, suggestion: string) => {
    if (suggestion.length > MAX_INTERET_CHARS) return; // defensive
    onChange({ ...value, [key]: suggestion });
    // Return focus on the textarea so the SR cursor stays inside the
    // field and the user can keep typing immediately after.
    queueMicrotask(() => {
      fieldRefs.current[key]?.focus();
    });
  };

  return (
    <div className="flex flex-col gap-6" data-testid="interets-free-form">
      {FIELD_KEYS.map((key, idx) => {
        const text = value[key] ?? "";
        const length = text.length;
        const warning = length >= Math.floor(MAX_INTERET_CHARS * 0.9);
        const danger = length >= Math.floor(MAX_INTERET_CHARS * 0.975);
        const fieldId = `interet-${key}`;
        const helperId = `interet-${key}-helper`;
        return (
          <div key={key} className="flex flex-col gap-2">
            <label htmlFor={fieldId} className="text-body-sm font-medium text-text">
              {FIELD_LABELS[key]}
            </label>
            <Textarea
              id={fieldId}
              ref={(el) => {
                fieldRefs.current[key] = el;
              }}
              value={text}
              onChange={(event) => handleFieldChange(key, event.target.value)}
              placeholder={placeholders[key]}
              maxLength={MAX_INTERET_CHARS}
              rows={2}
              aria-describedby={helperId}
              data-field-key={key}
            />
            <div className="flex flex-wrap items-center justify-between gap-2">
              <ul
                role="list"
                aria-label={`Suggestions pour ${FIELD_LABELS[key]}`}
                className="flex flex-wrap gap-2"
              >
                {INTERETS_SUGGESTIONS[(idx + 1) as 1 | 2 | 3].map((suggestion) => (
                  <li key={suggestion}>
                    <button
                      type="button"
                      onClick={() => handleSuggestionTap(key, suggestion)}
                      className="inline-flex min-h-11 items-center rounded-full border border-border bg-bg px-3 py-1 text-caption text-text-muted hover:bg-bg-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                    >
                      + {suggestion}
                    </button>
                  </li>
                ))}
              </ul>
              {/* Pass 1 M3 — `aria-live` removed; visual counter only.
                  AC9 threshold messages live in the orchestrator's single
                  polite region. */}
              <p
                id={helperId}
                className={cn(
                  "text-caption",
                  danger ? "text-danger" : warning ? "text-warning" : "text-text-subtle",
                )}
                data-testid={`interet-${key}-counter`}
              >
                {length} / {MAX_INTERET_CHARS}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
