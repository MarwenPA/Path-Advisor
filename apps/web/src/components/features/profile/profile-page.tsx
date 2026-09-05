"use client";

import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  ProfileMaturityIndicator,
  type MaturityNextAction,
} from "@/components/features/profile/profile-maturity-indicator";
import { useMaturityLevel } from "@/hooks/use-maturity-level";
import { useStudentProfile } from "@/hooks/use-student-profile";

import { EditBulletinsSheet } from "./edit-bulletins-sheet";
import { EditLevelSheet } from "./edit-level-sheet";
import { EditPassionsSheet } from "./edit-passions-sheet";

type OpenSheet = "passions" | "level" | "bulletins" | null;

const LEVEL_LABELS: Record<string, string> = {
  lycee_terminale: "Terminale",
  lycee_premiere: "Première",
  lycee_2nde: "Seconde",
  college_3eme: "3ème",
  college_4eme: "4ème",
  postbac: "Post-bac",
};

/** Which edit sheet each `next_actions[].icon` should open when clicked. */
const ICON_TO_SHEET: Record<MaturityNextAction["icon"], OpenSheet> = {
  bulletins: "bulletins",
  level: "level",
  specialites: "level",
  passions: "passions",
};

export function ProfilePage() {
  const { data: profile, isLoading } = useStudentProfile();
  const { data: maturity } = useMaturityLevel(profile?.id);
  const [openSheet, setOpenSheet] = useState<OpenSheet>(null);

  if (isLoading || !profile) {
    return (
      <main aria-labelledby="profile-title" className="p-4">
        <h1 id="profile-title" className="mb-6 text-2xl font-bold">
          Mon profil
        </h1>
        <p className="text-muted-foreground">Chargement…</p>
      </main>
    );
  }

  const passionCount = profile.passions?.length ?? 0;
  const valeurCount = profile.valeurs?.length ?? 0;
  const levelLabel = profile.level
    ? (LEVEL_LABELS[profile.level] ?? profile.level)
    : "Non renseigné";

  function handleSaved() {
    setOpenSheet(null);
  }

  return (
    <main aria-labelledby="profile-title" className="mx-auto max-w-2xl p-4">
      <h1 id="profile-title" className="mb-6 text-2xl font-bold">
        Mon profil
      </h1>

      {/* Code-review fix (2026-09): this was called with zero props while
          `level`/`nextActions` are required — crashed the whole page
          (`nextActions is not iterable`) the moment `/profile` first got
          past its (also broken, see `use-student-profile.ts`) loading
          state. Now sourced from `useMaturityLevel` like `ProgressionModule`
          on `/accueil`, and skipped entirely while that data isn't loaded
          yet — never rendered with missing props. */}
      {maturity ? (
        <ProfileMaturityIndicator
          variant="profile-header"
          level={maturity.level}
          nextActions={maturity.next_actions.map((action) => ({
            ...action,
            onClick: () => setOpenSheet(ICON_TO_SHEET[action.icon]),
          }))}
        />
      ) : null}

      <div className="mt-6 space-y-4">
        {/* Section 1 — Passions & valeurs */}
        <section aria-labelledby="section-passions-title">
          <Card className="p-4">
            <div className="mb-2 flex items-center justify-between">
              <h2 id="section-passions-title" className="text-lg font-semibold">
                Passions, intérêts et valeurs
              </h2>
              <Button
                variant="ghost"
                size="sm"
                aria-label="Modifier passions"
                onClick={() => setOpenSheet("passions")}
              >
                Modifier
              </Button>
            </div>
            <p className="text-sm text-muted-foreground">
              {passionCount} passions · {valeurCount} valeurs
            </p>
          </Card>
        </section>

        {/* Section 2 — Niveau scolaire */}
        <section aria-labelledby="section-level-title">
          <Card className="p-4">
            <div className="mb-2 flex items-center justify-between">
              <h2 id="section-level-title" className="text-lg font-semibold">
                Niveau scolaire, filière et spécialités
              </h2>
              <Button
                variant="ghost"
                size="sm"
                aria-label="Modifier niveau"
                onClick={() => setOpenSheet("level")}
              >
                Modifier
              </Button>
            </div>
            <p className="text-sm text-muted-foreground">{levelLabel}</p>
            {!!profile.specialites?.length && (
              <p className="text-sm text-muted-foreground">{profile.specialites.join(" · ")}</p>
            )}
          </Card>
        </section>

        {/* Section 3 — Bulletins */}
        <section aria-labelledby="section-bulletins-title">
          <Card className="p-4">
            <div className="mb-2 flex items-center justify-between">
              <h2 id="section-bulletins-title" className="text-lg font-semibold">
                Bulletins
              </h2>
              <Button
                variant="ghost"
                size="sm"
                aria-label="Modifier bulletins"
                onClick={() => setOpenSheet("bulletins")}
              >
                Modifier
              </Button>
            </div>
            <p className="text-sm capitalize text-muted-foreground">{profile.bulletins_status}</p>
          </Card>
        </section>
      </div>

      <div className="mt-8 text-center">
        <Link
          href="/profile/history"
          className="text-sm text-muted-foreground hover:underline"
          aria-label="Voir l'historique des changements"
        >
          Voir l&apos;historique des changements →
        </Link>
      </div>

      {/* Edit sheets */}
      <EditPassionsSheet
        open={openSheet === "passions"}
        profile={profile}
        onClose={() => setOpenSheet(null)}
        onSaved={handleSaved}
      />
      <EditLevelSheet
        open={openSheet === "level"}
        profile={profile}
        onClose={() => setOpenSheet(null)}
        onSaved={handleSaved}
      />
      <EditBulletinsSheet
        open={openSheet === "bulletins"}
        profile={profile}
        onClose={() => setOpenSheet(null)}
        onSaved={handleSaved}
      />
    </main>
  );
}
