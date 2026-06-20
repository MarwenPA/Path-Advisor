"use client";

import * as React from "react";
import { ChevronDown } from "lucide-react";

import { usePrefersReducedMotion } from "@/hooks/use-prefers-reduced-motion";
import { cn } from "@/lib/utils";
import { ScoreVocationnel } from "./ScoreVocationnel";
import { FicheMetierTOC } from "./FicheMetierTOC";
import { ReportErrorButton } from "./ReportErrorButton";
import { ReviewRequestButton } from "./ReviewRequestButton";
import type { FicheMetierProps, Profession, RequirementItem, SignalsByCategory } from "./types";

// ─── Utilities ────────────────────────────────────────────────────────────────

// P6: fallback for empty slug (all-non-alphanumeric input)
function slugify(text: string): string {
  const slug = text
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
  return slug || text.toLowerCase().replace(/\s+/g, "-") || "signal";
}

const SECTION_DEFS = [
  { key: "cest-quoi", label: "C'est quoi" },
  { key: "pour-qui", label: "Pour qui" },
  { key: "comment-y-aller", label: "Comment y aller" },
  { key: "infos-pratiques", label: "Infos pratiques" },
  { key: "signaux", label: "Signaux contributifs" },
] as const;

type SectionKey = (typeof SECTION_DEFS)[number]["key"];

const ACCORDION_KEYS: SectionKey[] = ["pour-qui", "comment-y-aller", "infos-pratiques"];

// D1: category keys for signal IDs
const SIGNAL_CATEGORIES: [string, string, keyof SignalsByCategory][] = [
  ["passions", "Passions", "passions"],
  ["valeurs", "Valeurs", "valeurs"],
  ["specialites", "Spécialités", "specialites"],
];

// ─── useMediaQuery ────────────────────────────────────────────────────────────

function useMediaQuery(query: string): boolean {
  return React.useSyncExternalStore(
    (callback) => {
      if (typeof window === "undefined") return () => {};
      const mq = window.matchMedia(query);
      mq.addEventListener("change", callback);
      return () => mq.removeEventListener("change", callback);
    },
    () => (typeof window !== "undefined" ? window.matchMedia(query).matches : false),
    () => false,
  );
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function SectorBadge({ sector }: { sector: string }) {
  return (
    <span className="inline-flex items-center rounded-full border border-border px-2.5 py-0.5 text-body-sm text-text-muted">
      {sector}
    </span>
  );
}

function RequirementsList({ requirements }: { requirements: RequirementItem[] }) {
  const grouped = requirements.reduce<Record<string, string[]>>((acc, item) => {
    if (!acc[item.type]) acc[item.type] = [];
    acc[item.type].push(item.label);
    return acc;
  }, {});

  const typeLabels: Record<string, string> = {
    studies: "Études",
    skill: "Compétences",
    quality: "Qualités",
  };

  return (
    <div className="flex flex-col gap-4">
      {Object.entries(grouped).map(([type, labels]) => (
        <div key={type}>
          <h3 className="mb-1 text-body font-semibold text-text">{typeLabels[type] ?? type}</h3>
          <ul className="list-inside list-disc space-y-0.5 text-body text-text-muted">
            {labels.map((label) => (
              <li key={label}>{label}</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

function SalaryInfo({ profession }: { profession: Profession }) {
  const { median_salary_eur, salary_range_json, level_compatibility } = profession;

  return (
    <div className="flex flex-col gap-4">
      {median_salary_eur != null && (
        <div>
          <p className="text-body-sm text-text-muted">Salaire médian brut annuel</p>
          <p className="text-body font-semibold text-text">
            {median_salary_eur.toLocaleString("fr-FR")} €
          </p>
        </div>
      )}
      {salary_range_json && (
        <div>
          <p className="text-body-sm text-text-muted">Fourchette</p>
          <p className="text-body text-text">
            {salary_range_json.min.toLocaleString("fr-FR")} €&nbsp;–&nbsp;
            {salary_range_json.max.toLocaleString("fr-FR")} €
            {salary_range_json.source && (
              <span className="ml-1 text-caption text-text-muted">
                ({salary_range_json.source})
              </span>
            )}
          </p>
        </div>
      )}
      {level_compatibility.length > 0 && (
        <div>
          <p className="text-body-sm text-text-muted">Niveaux compatibles</p>
          <div className="mt-1 flex flex-wrap gap-1.5">
            {level_compatibility.map((level) => (
              <span
                key={level}
                className="inline-flex items-center rounded-full border border-border px-2.5 py-0.5 text-body-sm text-text-muted"
              >
                {level.replace(/_/g, " ")}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

interface SignalChipsGroupedProps {
  signalsJson: SignalsByCategory;
  onSignalClick?: (signalId: string) => void;
  interactive?: boolean;
}

// D1: signalId includes category key → "passions-svt", "valeurs-contact", etc.
function SignalChipsGrouped({
  signalsJson,
  onSignalClick,
  interactive = true,
}: SignalChipsGroupedProps) {
  return (
    <div className="flex flex-col gap-4">
      {SIGNAL_CATEGORIES.map(([catKey, catLabel, jsonKey]) => {
        const signals = signalsJson[jsonKey] ?? [];
        if (!signals.length) return null;
        return (
          <div key={catKey}>
            <h3 className="mb-2 text-body font-semibold text-text">{catLabel}</h3>
            <div className="flex flex-wrap gap-1.5">
              {signals.map((signal) => {
                const signalId = `${catKey}-${slugify(signal)}`;
                const itemKey = `${catKey}-${signal}`;
                if (interactive && onSignalClick) {
                  return (
                    <button
                      key={itemKey}
                      type="button"
                      aria-label={`Signal contributif : ${signal}`}
                      onClick={() => onSignalClick(signalId)}
                      className={cn(
                        "inline-flex items-center rounded-full border border-border px-2.5 py-0.5",
                        "text-body-sm text-text-muted",
                        "hover:border-border-strong hover:text-text",
                        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                        "transition-colors duration-instant",
                      )}
                    >
                      {signal}
                    </button>
                  );
                }
                return (
                  <span
                    key={itemKey}
                    className="inline-flex items-center rounded-full border border-border px-2.5 py-0.5 text-body-sm text-text-muted"
                  >
                    {signal}
                  </span>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ─── Section content renderer ─────────────────────────────────────────────────

function SectionContent({
  sectionKey,
  profession,
  onSignalClick,
  interactive = true,
}: {
  sectionKey: SectionKey;
  profession: Profession;
  onSignalClick?: (signalId: string) => void;
  interactive?: boolean;
}) {
  switch (sectionKey) {
    case "cest-quoi":
      return <p className="text-body text-text">{profession.description}</p>;

    case "pour-qui":
      return (
        <div className="flex flex-col gap-6">
          <RequirementsList requirements={profession.requirements_json} />
          <div>
            <h3 className="mb-1 text-body font-semibold text-text">Journée type</h3>
            <p className="text-body text-text-muted">{profession.daily_routine}</p>
          </div>
        </div>
      );

    case "comment-y-aller":
      return <p className="whitespace-pre-line text-body text-text">{profession.prospects_text}</p>;

    case "infos-pratiques":
      return <SalaryInfo profession={profession} />;

    case "signaux":
      return (
        <SignalChipsGrouped
          signalsJson={profession.signals_json}
          onSignalClick={onSignalClick}
          interactive={interactive}
        />
      );
  }
}

// ─── Hero section ─────────────────────────────────────────────────────────────

interface HeroSectionProps {
  profession: Profession;
  score?: number;
  phraseRecopiable?: string;
  confidenceLevel?: "normal" | "indicative";
  onSignalClick?: (signalId: string) => void;
  isPrint?: boolean;
}

function HeroSection({
  profession,
  score,
  phraseRecopiable,
  confidenceLevel,
  onSignalClick,
  isPrint = false,
}: HeroSectionProps) {
  const genericPhrase = `${profession.name} est un métier ${profession.sector ? `du secteur ${profession.sector}` : "varié et enrichissant"}.`;

  // D1: flat signals deduped by slug, category-prefixed ids (first occurrence wins)
  const flatSignals: { id: string; label: string }[] = [];
  const seenSlugs = new Set<string>();
  outer: for (const [catKey, , jsonKey] of SIGNAL_CATEGORIES) {
    for (const s of profession.signals_json[jsonKey] ?? []) {
      const slug = slugify(s);
      if (!seenSlugs.has(slug)) {
        seenSlugs.add(slug);
        flatSignals.push({ id: `${catKey}-${slug}`, label: s });
        if (flatSignals.length >= 8) break outer;
      }
    }
  }

  const heroLabel = `section-hero-${profession.slug}`;

  return (
    <section aria-labelledby={heroLabel}>
      <div className="flex flex-wrap items-start gap-2">
        <h1 id={heroLabel} className="text-h1 font-bold leading-tight text-text">
          {profession.name}
        </h1>
        {profession.sector && <SectorBadge sector={profession.sector} />}
      </div>

      {score !== undefined ? (
        isPrint ? (
          // P5: static print view — no interactive CTAs (CopyButton, Explain)
          <div className="mt-4 flex flex-col gap-2">
            <p className="text-body font-semibold text-text">
              Score : {score}/100
              {confidenceLevel === "indicative" && (
                <span className="ml-2 text-body-sm font-normal text-text-muted">(indicatif)</span>
              )}
            </p>
            <p className="text-body italic text-text-muted">{phraseRecopiable ?? genericPhrase}</p>
          </div>
        ) : (
          <div className="mt-4">
            <ScoreVocationnel
              metierId={profession.slug}
              metiersName={profession.name}
              score={score}
              phraseRecopiable={phraseRecopiable ?? genericPhrase}
              signals={flatSignals}
              variant="expanded"
              confidenceLevel={confidenceLevel}
              onSignalClick={onSignalClick}
            />
          </div>
        )
      ) : (
        <p className="mt-3 text-body text-text-muted">{genericPhrase}</p>
      )}
    </section>
  );
}

// ─── Mobile layout (accordion) ────────────────────────────────────────────────

function FicheMetierMobile({
  profession,
  score,
  phraseRecopiable,
  confidenceLevel,
  onSignalClick,
}: Omit<FicheMetierProps, "variant">) {
  const [expanded, setExpanded] = React.useState<Set<SectionKey>>(new Set());
  const reducedMotion = usePrefersReducedMotion();

  function toggle(key: SectionKey) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  function expandAll() {
    setExpanded(new Set(ACCORDION_KEYS));
  }

  return (
    <div className="flex flex-col gap-6 px-4 py-6">
      {/* Hero — always visible */}
      <HeroSection
        profession={profession}
        score={score}
        phraseRecopiable={phraseRecopiable}
        confidenceLevel={confidenceLevel}
        onSignalClick={onSignalClick}
      />

      {/* C'est quoi — always visible */}
      <section aria-labelledby="section-cest-quoi">
        <h2 id="section-cest-quoi" className="mb-3 text-h2 font-semibold text-text">
          C&apos;est quoi
        </h2>
        <SectionContent
          sectionKey="cest-quoi"
          profession={profession}
          onSignalClick={onSignalClick}
        />
      </section>

      {/* Accordion sections: Pour qui, Comment y aller, Infos pratiques */}
      {ACCORDION_KEYS.map((key) => {
        const def = SECTION_DEFS.find((s) => s.key === key)!;
        const isOpen = expanded.has(key);
        const panelId = `panel-${key}`;
        const headingId = `section-${key}`;

        return (
          <section key={key} aria-labelledby={headingId}>
            <h2 id={headingId} className="text-h2 font-semibold text-text">
              <button
                type="button"
                aria-expanded={isOpen}
                aria-controls={panelId}
                onClick={() => toggle(key)}
                className={cn(
                  "flex w-full items-center justify-between py-2 text-left",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
                )}
              >
                <span>{def.label}</span>
                <ChevronDown
                  size={20}
                  aria-hidden
                  className={cn(
                    "shrink-0 text-text-muted",
                    !reducedMotion && "transition-transform duration-quick",
                    isOpen && "rotate-180",
                  )}
                />
              </button>
            </h2>

            {/* P4: always in DOM — aria-controls resolves even when collapsed */}
            <div
              id={panelId}
              role="region"
              aria-labelledby={headingId}
              hidden={!isOpen}
              className={cn("overflow-hidden", !reducedMotion && "transition-all duration-quick")}
            >
              <div className="pb-4 pt-2">
                <SectionContent
                  sectionKey={key}
                  profession={profession}
                  onSignalClick={onSignalClick}
                />
              </div>
            </div>
          </section>
        );
      })}

      {/* Signaux contributifs — always visible */}
      <section aria-labelledby="section-signaux">
        <h2 id="section-signaux" className="mb-3 text-h2 font-semibold text-text">
          Signaux contributifs
        </h2>
        <SectionContent
          sectionKey="signaux"
          profession={profession}
          onSignalClick={onSignalClick}
        />
      </section>

      {/* Tout afficher */}
      <button
        type="button"
        onClick={expandAll}
        className={cn(
          "self-center rounded-md border border-border px-4 py-2 text-body-sm text-text-muted",
          "hover:border-border-strong hover:text-text",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          "transition-colors duration-instant",
        )}
      >
        Tout afficher
      </button>

      {/* Pied de fiche — boutons signalement (hors print) */}
      <div className="mt-4 flex flex-wrap justify-center gap-3">
        <ReportErrorButton professionSlug={profession.slug} professionName={profession.name} />
        <ReviewRequestButton
          professionSlug={profession.slug}
          professionName={profession.name}
          hasScore={score !== undefined}
        />
      </div>
    </div>
  );
}

// ─── Desktop layout (D2: scrollable sections + IntersectionObserver) ──────────

function FicheMetierDesktop({
  profession,
  score,
  phraseRecopiable,
  confidenceLevel,
  onSignalClick,
}: Omit<FicheMetierProps, "variant">) {
  const [activeSection, setActiveSection] = React.useState<SectionKey>("cest-quoi");
  const reducedMotion = usePrefersReducedMotion();

  // D2: IntersectionObserver highlights TOC as user scrolls
  React.useEffect(() => {
    if (typeof IntersectionObserver === "undefined") return;

    const observer = new IntersectionObserver(
      (entries) => {
        const firstVisible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
        if (firstVisible) {
          const key = firstVisible.target.getAttribute("data-section");
          if (key) setActiveSection(key as SectionKey);
        }
      },
      { rootMargin: "-10% 0px -80% 0px", threshold: 0 },
    );

    SECTION_DEFS.forEach((def) => {
      const el = document.querySelector<HTMLElement>(`[data-section="${def.key}"]`);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);

  function handleTocClick(key: string) {
    setActiveSection(key as SectionKey);
    const el = document.getElementById(`section-${key}`);
    if (el) {
      el.scrollIntoView({ behavior: reducedMotion ? "instant" : "smooth" });
    }
  }

  return (
    <div className="py-8">
      {/* Hero — always visible above grid */}
      <div className="mx-auto max-w-4xl px-6">
        <HeroSection
          profession={profession}
          score={score}
          phraseRecopiable={phraseRecopiable}
          confidenceLevel={confidenceLevel}
          onSignalClick={onSignalClick}
        />
      </div>

      {/* Grid: TOC sticky + scrollable sections */}
      <div
        className="mx-auto mt-8 max-w-4xl px-6"
        style={{ display: "grid", gridTemplateColumns: "200px 1fr", gap: "2rem" }}
      >
        <FicheMetierTOC
          sections={SECTION_DEFS}
          activeSection={activeSection}
          onSectionClick={handleTocClick}
        />

        {/* All sections scrollable — D2 */}
        <div className="flex flex-col gap-16">
          {SECTION_DEFS.map((def) => (
            <section key={def.key} data-section={def.key} aria-labelledby={`section-${def.key}`}>
              <h2 id={`section-${def.key}`} className="mb-4 text-h2 font-semibold text-text">
                {def.label}
              </h2>
              <SectionContent
                sectionKey={def.key}
                profession={profession}
                onSignalClick={onSignalClick}
              />
            </section>
          ))}
        </div>
      </div>

      {/* Pied de fiche — boutons signalement (hors print) */}
      <div className="mx-auto mt-8 flex max-w-4xl flex-wrap justify-end gap-3 px-6">
        <ReportErrorButton professionSlug={profession.slug} professionName={profession.name} />
        <ReviewRequestButton
          professionSlug={profession.slug}
          professionName={profession.name}
          hasScore={score !== undefined}
        />
      </div>
    </div>
  );
}

// ─── Print layout (P5: no interactive CTAs) ───────────────────────────────────

function FicheMetierPrint({
  profession,
  score,
  phraseRecopiable,
  confidenceLevel,
}: Omit<FicheMetierProps, "variant" | "onSignalClick">) {
  return (
    <div
      className="flex flex-col gap-8 bg-white text-black"
      style={{ maxWidth: "210mm", margin: "0 auto", padding: "15mm" }}
    >
      {/* P5: isPrint=true → static score display, no ScoreVocationnel CTAs */}
      <HeroSection
        profession={profession}
        score={score}
        phraseRecopiable={phraseRecopiable}
        confidenceLevel={confidenceLevel}
        isPrint
      />

      {SECTION_DEFS.map((def) => (
        <section key={def.key} aria-labelledby={`section-print-${def.key}`}>
          <h2 id={`section-print-${def.key}`} className="mb-3 text-h2 font-semibold">
            {def.label}
          </h2>
          <SectionContent sectionKey={def.key} profession={profession} interactive={false} />
        </section>
      ))}
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

export function FicheMetier({
  profession,
  score,
  phraseRecopiable,
  confidenceLevel,
  variant = "default",
  onSignalClick,
}: FicheMetierProps) {
  const isDesktop = useMediaQuery("(min-width: 1024px)");

  if (variant === "print") {
    return (
      <FicheMetierPrint
        profession={profession}
        score={score}
        phraseRecopiable={phraseRecopiable}
        confidenceLevel={confidenceLevel}
      />
    );
  }

  // D3: explicit mobile override or viewport < 1024px
  if (variant === "mobile" || !isDesktop) {
    return (
      <FicheMetierMobile
        profession={profession}
        score={score}
        phraseRecopiable={phraseRecopiable}
        confidenceLevel={confidenceLevel}
        onSignalClick={onSignalClick}
      />
    );
  }

  return (
    <FicheMetierDesktop
      profession={profession}
      score={score}
      phraseRecopiable={phraseRecopiable}
      confidenceLevel={confidenceLevel}
      onSignalClick={onSignalClick}
    />
  );
}
