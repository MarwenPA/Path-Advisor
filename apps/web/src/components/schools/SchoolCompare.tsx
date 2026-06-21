"use client";

import { useState } from "react";
import { FicheEcole } from "./FicheEcole";
import type { School } from "@/lib/api/schools";

interface SchoolCompareProps {
  schools: School[];
}

const COMPARE_FIELDS: { key: keyof School; label: string }[] = [
  { key: "type", label: "Type" },
  { key: "city", label: "Ville" },
  { key: "public_private", label: "Statut" },
  { key: "selectivity_index", label: "Selectivite" },
  { key: "tuition_min_eur", label: "Frais min" },
  { key: "tuition_max_eur", label: "Frais max" },
  { key: "apprenticeship", label: "Alternance" },
  { key: "internship", label: "Internat" },
];

const MAX_COMPARE = 3;

function renderFieldValue(school: School, key: keyof School): string {
  const value = school[key];
  if (key === "apprenticeship" || key === "internship") {
    return value ? "Oui" : "Non";
  }
  if (value === undefined || value === null) return "-";
  return String(value);
}

export function SchoolCompare({ schools }: SchoolCompareProps) {
  const [selected, setSelected] = useState<string[]>([]);

  const comparing = schools.filter((s) => selected.includes(s.id));

  function toggleSelect(id: string) {
    setSelected((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= MAX_COMPARE) return prev;
      return [...prev, id];
    });
  }

  const atMax = selected.length >= MAX_COMPARE;

  return (
    <div>
      {atMax && (
        <p role="status" className="mb-2 text-sm text-amber-600">
          Maximum {MAX_COMPARE} ecoles selectionnees. Deselectionnez une ecole pour en choisir une
          autre.
        </p>
      )}
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {schools.map((s) => (
          <FicheEcole
            key={s.id}
            school={s}
            variant="compare"
            isSelected={selected.includes(s.id)}
            onSelect={toggleSelect}
          />
        ))}
      </div>

      {comparing.length >= 2 && (
        <div className="mt-6 overflow-x-auto">
          <table className="w-full text-sm">
            <caption className="mb-2 text-left text-sm font-medium">
              Comparaison de {comparing.length} ecoles
            </caption>
            <thead>
              <tr>
                <th scope="col" className="py-2 pr-4 text-left text-muted-foreground">
                  Critere
                </th>
                {comparing.map((s) => (
                  <th key={s.id} scope="col" className="px-2 py-2 text-left">
                    {s.name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {COMPARE_FIELDS.map((field) => (
                <tr key={field.key} className="border-t">
                  <td className="py-2 pr-4 text-muted-foreground">{field.label}</td>
                  {comparing.map((s) => (
                    <td key={s.id} className="px-2 py-2">
                      {renderFieldValue(s, field.key)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
