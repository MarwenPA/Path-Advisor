/**
 * Empty state for /parametres/confidentialite/acces-tiers — Story 1.9 §AC4.
 *
 * Copy is verbatim from the epic AC. Do NOT paraphrase — wording was
 * reviewed by the CNIL-track UX writer.
 */
import { ACCESS_LIST_COPY } from "@/lib/i18n/fr/access-list";

export function AccessListEmptyState() {
  return (
    <section
      className="rounded-lg border border-dashed border-border-strong bg-bg-2 p-8 text-center"
      data-testid="access-list-empty"
    >
      <p className="text-body text-text-muted">{ACCESS_LIST_COPY.emptyState}</p>
    </section>
  );
}
