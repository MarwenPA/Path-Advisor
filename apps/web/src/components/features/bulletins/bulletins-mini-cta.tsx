"use client";

import { FileText } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useStudentProfile } from "@/hooks/use-student-profile";

interface BulletinsMiniCTAProps {
  context: "graph" | "stat" | "fiche_metier";
  metier_id?: string;
  onAddClick: () => void;
}

export function BulletinsMiniCTA({
  context,
  onAddClick,
}: BulletinsMiniCTAProps) {
  const { data: profile, isLoading } = useStudentProfile();

  if (isLoading || !profile || profile.bulletins_status === "completed") {
    return null;
  }

  return (
    <aside
      role="complementary"
      aria-label="Compléter ton profil"
      className="my-4"
    >
      <Card className="bg-bg-2 border-border p-6">
        <div className="flex items-start gap-3">
          <FileText
            size={20}
            className="text-muted-foreground shrink-0 mt-0.5"
            aria-hidden="true"
          />
          <div className="flex-1">
            <p className="font-medium text-sm">Ajoute tes bulletins</p>
            <p className="text-sm text-muted-foreground mt-1">
              {context === "graph"
                ? "Tes stats deviendront personnalisées en moins d'une minute."
                : "Affine ton estimation avec tes bulletins scolaires."}
            </p>
          </div>
        </div>
        <Button
          variant="secondary"
          size="sm"
          className="mt-4 w-full"
          onClick={onAddClick}
        >
          J&apos;ajoute mes notes →
        </Button>
      </Card>
    </aside>
  );
}
