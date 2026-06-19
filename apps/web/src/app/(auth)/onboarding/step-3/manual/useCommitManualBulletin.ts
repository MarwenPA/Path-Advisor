import { useMutation, useQueryClient } from "@tanstack/react-query";

interface ManualBulletinPayload {
  trimestre_label: string;
  year: string;
  level_at_save: string;
  subjects_ref_version: string;
  matieres: Array<{
    subject_id: string;
    note: number;
    appreciation: string | null;
    is_custom?: boolean;
  }>;
}

async function postManualBulletin(payload: ManualBulletinPayload) {
  const res = await fetch("/api/v1/students/me/bulletins/manual", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to commit manual bulletin");
  return res.json();
}

export function useCommitManualBulletin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: postManualBulletin,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["student-profile"] });
    },
    retry: 3,
  });
}
