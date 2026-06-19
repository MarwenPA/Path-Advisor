"use client";

import { useState } from "react";
import { ChevronLeft } from "lucide-react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { getSubjectsForLevel, SUBJECTS_REF_VERSION } from "@/lib/onboarding/subjects-by-level";
import type { MatiereDef } from "@/lib/onboarding/subjects-by-level";

import { MatiereInputRow } from "./MatiereInputRow";
import { TrimestreTabs } from "./TrimestreTabs";
import { useCommitManualBulletin } from "./useCommitManualBulletin";
import { useManualBulletinDraft } from "./useManualBulletinDraft";

interface Props {
  level?: string;
  filiere?: string;
  specialites?: string[];
  origin?: "cards" | "ocr_fallback" | "ocr_optin";
}

const FISCAL_YEAR = (() => {
  const now = new Date();
  const y = now.getFullYear();
  return now.getMonth() >= 8 ? `${y}-${y + 1}` : `${y - 1}-${y}`;
})();

function trimestreId(trim: number): string {
  return `trim_${trim}_${FISCAL_YEAR}`;
}

export function OnboardingStep3Manual({
  level = "lycee_terminale",
  filiere,
  specialites = [],
  origin = "cards",
}: Props) {
  const router = useRouter();
  const [activeTrim, setActiveTrim] = useState(1);
  const [totalTrims, setTotalTrims] = useState(3);
  const [subjects, _setSubjects] = useState<MatiereDef[]>(() =>
    getSubjectsForLevel(level, filiere, specialites)
  );
  const [removedIds, setRemovedIds] = useState<Set<string>>(new Set());
  const [footerHelper, setFooterHelper] = useState<string | null>(null);

  const { drafts, updateDraft, removeDraft, flushDraft } = useManualBulletinDraft(
    trimestreId(activeTrim)
  );
  const commit = useCommitManualBulletin();

  const activeSubjects = subjects.filter((s) => !removedIds.has(s.id));
  const filledMatieres = drafts.filter((d) => d.note !== null && d.note !== undefined);

  function handleValidate() {
    if (filledMatieres.length === 0) {
      setFooterHelper(
        "Renseigne au moins une matière, ou clique '⏭ Plus tard' pour explorer d'abord."
      );
      return;
    }
    setFooterHelper(null);

    const payload = {
      trimestre_label: `Trim. ${activeTrim}`,
      year: FISCAL_YEAR,
      level_at_save: level,
      subjects_ref_version: SUBJECTS_REF_VERSION,
      matieres: filledMatieres.map((d) => ({
        subject_id: d.subject_id,
        note: d.note!,
        appreciation: d.appreciation,
      })),
    };

    commit.mutate(payload, {
      onSuccess: () => {
        flushDraft();
        router.push("/dashboard");
      },
    });
  }

  const isOCRFallback = origin === "ocr_fallback";

  return (
    <div className="max-w-[600px] mx-auto px-4 pb-32">
      {/* Header sticky */}
      <div className="sticky top-0 bg-background z-10 py-3 flex items-center gap-3 border-b border-border">
        <button
          type="button"
          aria-label="Retour"
          onClick={() => router.push("/onboarding/step-3")}
          className="p-1 text-muted-foreground"
        >
          <ChevronLeft size={20} />
        </button>
        <div className="flex gap-1 mx-auto" aria-label="Progression">
          {[1, 2, 3].map((d) => (
            <span
              key={d}
              className="w-2 h-2 rounded-full bg-primary"
              aria-hidden="true"
            />
          ))}
        </div>
      </div>

      {/* Title */}
      <div className="mt-6 mb-4">
        <h2 className="text-h2 font-semibold">Tes notes, à la main</h2>
        {isOCRFallback && (
          <p className="text-caption text-muted/60 mb-1">
            Tu reviens du scan qui n&apos;a pas marché — on reprend ici.
          </p>
        )}
        <p className="text-body text-muted-foreground">
          {isOCRFallback
            ? "Pas grave, on continue à la main. On a préparé la liste des matières selon ton niveau — tu peux en sauter, on s'en fiche."
            : "On a préparé la liste des matières selon ton niveau. À toi de remplir — tu peux en sauter, on s'en fiche."}
        </p>
      </div>

      {/* Trimestre tabs */}
      <TrimestreTabs
        active={activeTrim}
        total={totalTrims}
        onSelect={setActiveTrim}
        onAdd={() => setTotalTrims((n) => Math.min(n + 1, 4))}
      />

      {/* Subject list */}
      <form aria-label="Saisie manuelle des notes" onSubmit={(e) => e.preventDefault()}>
        {activeSubjects.length === 0 ? (
          <p className="text-muted-foreground text-sm py-8 text-center">
            Ajoute ta première matière ci-dessous.
          </p>
        ) : (
          <div>
            {activeSubjects.map((subject) => {
              const draft = drafts.find((d) => d.subject_id === subject.id);
              return (
                <MatiereInputRow
                  key={subject.id}
                  subject={subject}
                  note={draft?.note ?? null}
                  appreciation={draft?.appreciation ?? null}
                  onNoteChange={(id, note) => updateDraft(id, { note })}
                  onAppreciationChange={(id, appreciation) =>
                    updateDraft(id, { appreciation })
                  }
                  onRemove={(id) => {
                    removeDraft(id);
                    setRemovedIds((s) => new Set([...s, id]));
                  }}
                />
              );
            })}
          </div>
        )}
      </form>

      {/* Sticky footer */}
      <div className="fixed bottom-0 left-0 right-0 bg-background border-t border-border px-4 py-4">
        <div className="max-w-[600px] mx-auto">
          {footerHelper && (
            <p className="text-sm text-muted-foreground mb-2">{footerHelper}</p>
          )}
          <Button
            size="lg"
            className="w-full"
            onClick={handleValidate}
            disabled={commit.isPending}
          >
            {commit.isPending ? "Envoi…" : "Valider et continuer"}
          </Button>
          <button
            type="button"
            className="mt-2 w-full text-sm text-brand underline"
            onClick={async () => {
              await fetch("/api/v1/students/me/bulletins/postpone", { method: "POST" });
              router.push("/dashboard");
            }}
          >
            ⏭ Plus tard, je préfère explorer d&apos;abord
          </button>
        </div>
      </div>
    </div>
  );
}
