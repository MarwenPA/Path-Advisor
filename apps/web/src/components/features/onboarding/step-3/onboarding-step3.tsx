"use client";

import { useMachine } from "@xstate/react";
import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { track } from "@/lib/analytics/events";
import { useBulletinUpload } from "@/hooks/use-bulletin-upload";
import { useOCRJobs } from "@/hooks/use-ocr-job";

import { BulletinRecapEditor } from "./bulletin-recap-editor";
import { FilePickerSheet, type PickedFile } from "./file-picker-sheet";
import { ImportChoice3Cards, type CardChoice } from "./import-choice-3-cards";
import type { BulletinRecap, NormalizedField, UploadFile } from "./onboarding-step3-machine";
import { onboardingStep3Machine } from "./onboarding-step3-machine";
import { OCRGracefulFallback } from "./ocr-graceful-fallback";
import { OCRLoader } from "./ocr-loader";
import { UploadProgress } from "./upload-progress";

const LOW_CONF_THRESHOLD = 0.7;

// --- localStorage helpers (userId-prefixed, debounced, QuotaExceededError-safe) ---

const DRAFT_KEY = (userId: string | null, bulletinId: string) =>
  `bulletins_recap_draft_${userId ?? "anon"}_${bulletinId}`;

function loadDraft(userId: string | null, bulletinId: string): NormalizedField[] | null {
  try {
    const raw = localStorage.getItem(DRAFT_KEY(userId, bulletinId));
    return raw ? (JSON.parse(raw) as NormalizedField[]) : null;
  } catch {
    return null;
  }
}

// --- Main component ---

export function OnboardingStep3() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { upload, fileProgress } = useBulletinUpload();
  const [state, send] = useMachine(onboardingStep3Machine);

  // Current user ID for localStorage key namespacing
  const [userId, setUserId] = useState<string | null>(null);
  useEffect(() => {
    fetch("/api/v1/students/me", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((d: { id?: string } | null) => setUserId(d?.id ?? null))
      .catch(() => {});
  }, []);

  // DN1: Hydrate machine from server state on mount (resume after page reload)
  const hydratedRef = useRef(false);
  useEffect(() => {
    if (hydratedRef.current) return;
    hydratedRef.current = true;
    fetch("/api/v1/students/me/bulletins/onboarding/status", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then(
        (data: {
          state: string;
          bulletin_ids?: string[];
          recaps?: Array<{
            bulletinId: string;
            normalizedFields: NormalizedField[];
            confidenceAvg: number;
            isLowQuality: boolean;
          }>;
        } | null) => {
          if (!data || data.state === "idle") return;
          const serverState = data.state as "ocr_running" | "recap_editing" | "fallback";
          const bulletinIds = data.bulletin_ids ?? [];
          const recaps: BulletinRecap[] =
            serverState === "recap_editing" && data.recaps
              ? data.recaps.map((r, i) => ({
                  bulletinId: r.bulletinId,
                  label: `Bulletin ${i + 1}`,
                  fields: r.normalizedFields.map((f) => ({
                    ...f,
                    isLowConfidence: f.confidence < LOW_CONF_THRESHOLD,
                  })),
                  confidenceAvg: r.confidenceAvg,
                  validated: false,
                  draftFields: loadDraft(userId, r.bulletinId) ?? undefined,
                }))
              : [];
          send({ type: "HYDRATE", serverState, bulletinIds, recaps });
        }
      )
      .catch(() => {});
  }, [send, userId]);

  // Picker files local state
  const pickerFilesRef = useRef<PickedFile[]>([]);

  // Multi-bulletin OCR polling (#2)
  const { queries: ocrQueries, allDone, allSucceeded, anyFailed } = useOCRJobs(
    state.matches("ocr_running") ? state.context.bulletinIds : []
  );

  // Detect network errors from OCR queries
  const hasNetworkError = ocrQueries.some((q) => q.isError && !q.data);

  // Navigate when machine emits navigateTo
  useEffect(() => {
    const { navigateTo } = state.context;
    if (navigateTo === "manual") {
      router.push("/onboarding/step-4");
    } else if (navigateTo === "later") {
      fetch("/api/v1/students/me/onboarding/bulletins/postpone", {
        method: "POST",
        credentials: "include",
      }).catch(() => {});
      router.push("/dashboard");
    }
  }, [state.context.navigateTo, router]);

  // React to multi-bulletin OCR completion
  useEffect(() => {
    if (!state.matches("ocr_running") || !allDone) return;

    if (allSucceeded) {
      const bulletinIds = state.context.bulletinIds;
      const recaps: (BulletinRecap | null)[] = ocrQueries.map((q, i) => {
        const bulletinId = bulletinIds[i];
        if (!bulletinId) return null;
        const extraction = q.data?.extraction;
        if (!extraction || extraction.is_low_quality) return null;
        const draft = loadDraft(userId, bulletinId);
        return {
          bulletinId,
          label: `Bulletin ${i + 1}`,
          fields: extraction.normalized_fields.map((f) => ({
            ...f,
            key: f.key as NormalizedField["key"],
            isLowConfidence: f.confidence < LOW_CONF_THRESHOLD,
          })),
          confidenceAvg: extraction.confidence_avg,
          validated: false,
          draftFields: draft ?? undefined,
        };
      });

      const valid = recaps.filter((r): r is BulletinRecap => r !== null);
      if (valid.length !== bulletinIds.length) {
        send({ type: "OCR_FAILED", error: "Qualité d'extraction insuffisante." });
      } else {
        send({ type: "OCR_SUCCESS", recaps: valid });
      }
    } else if (anyFailed) {
      const failedQuery = ocrQueries.find(
        (q) => q.data?.status === "failed" || q.data?.status === "timeout"
      );
      send({
        type: "OCR_FAILED",
        error: failedQuery?.data?.error ?? "L'analyse a échoué sur un ou plusieurs bulletins.",
      });
    }
  }, [allDone, allSucceeded, anyFailed, ocrQueries, state, send, userId]);

  // Auto-detect all-validated
  useEffect(() => {
    if (!state.matches("recap_editing")) return;
    if (state.context.recaps.every((r) => r.validated)) {
      track({ name: "onboarding_step3_completed", bulletin_count: state.context.recaps.length });
      send({ type: "ALL_VALIDATED" });
    }
  }, [state, send]);

  // Redirect on validated
  useEffect(() => {
    if (state.matches("validated")) {
      router.push("/dashboard");
    }
  }, [state, router]);

  // Debounce ref for localStorage saves
  const saveDraftTimers = useRef<Record<string, ReturnType<typeof setTimeout>>>({});

  function saveDraftDebounced(bulletinId: string, fields: NormalizedField[]) {
    clearTimeout(saveDraftTimers.current[bulletinId]);
    saveDraftTimers.current[bulletinId] = setTimeout(() => {
      try {
        localStorage.setItem(DRAFT_KEY(userId, bulletinId), JSON.stringify(fields));
      } catch (e) {
        if (e instanceof DOMException && e.name === "QuotaExceededError") {
          console.warn("localStorage quota exceeded — draft not saved for", bulletinId);
        }
      }
    }, 500);
  }

  // --- Handlers ---

  function handleCardSelect(choice: CardChoice) {
    track({ name: "onboarding_step3_card_selected", card: choice });
    if (choice === "scan") send({ type: "SELECT_SCAN" });
    else if (choice === "manual") send({ type: "SELECT_MANUAL" });
    else send({ type: "SELECT_LATER" });
  }

  async function handleLaunchUpload() {
    const validEntries = pickerFilesRef.current
      .filter((f) => !f.error)
      .map((f) => ({ id: f.id, file: f.file }));

    if (!validEntries.length) return;

    send({ type: "UPLOAD_START" });
    track({
      name: "onboarding_step3_upload_started",
      file_count: validEntries.length,
      total_size_bytes: validEntries.reduce((s, e) => s + e.file.size, 0),
    });

    const { results, bulletinIds } = await upload(validEntries);

    track({
      name: "onboarding_step3_upload_completed",
      file_count: validEntries.length,
      success_count: bulletinIds.length,
      failed_count: results.filter((r) => r.result.status === "failed").length,
    });

    if (!bulletinIds.length) return;

    send({ type: "UPLOADS_COMPLETE", bulletinIds });

    const ocrRes = await fetch("/api/v1/students/me/bulletins/ocr/start", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ bulletin_ids: bulletinIds }),
    });
    if (ocrRes.ok) {
      const data = await ocrRes.json();
      send({ type: "OCR_STARTED", estimatedSeconds: data.estimated_seconds });
    } else {
      send({ type: "OCR_FAILED", error: "Erreur lors du démarrage de l'analyse." });
    }
  }

  async function handleValidateBulletin(bulletinId: string) {
    const recap = state.context.recaps.find((r) => r.bulletinId === bulletinId);
    if (!recap) return;

    const fields = recap.draftFields ?? recap.fields;
    const res = await fetch(`/api/v1/students/me/bulletins/${bulletinId}/finalize`, {
      method: "PATCH",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fields }),
    });

    // Abort if the server rejected — don't mark as validated
    if (!res.ok) return;

    const corrections = fields.filter(
      (f, i) => f.value !== (recap.fields[i]?.value ?? "")
    ).length;
    track({
      name: "onboarding_step3_bulletin_finalized",
      bulletin_id: bulletinId,
      corrections_made: corrections,
    });

    localStorage.removeItem(DRAFT_KEY(userId, bulletinId));
    clearTimeout(saveDraftTimers.current[bulletinId]);
    send({ type: "VALIDATE_BULLETIN", bulletinId });
  }

  function handleFieldsChange(bulletinId: string, fields: NormalizedField[]) {
    send({ type: "FIELD_EDITED", bulletinId, fields });
    saveDraftDebounced(bulletinId, fields);
  }

  function handleRetryScan() {
    queryClient.removeQueries({ queryKey: ["ocr-status"] });
    pickerFilesRef.current = []; // #21: clear stale picker files
    send({ type: "RETRY_SCAN" });
  }

  function handleManualFallback() {
    // DN3: signal to manual entry screen that OCR data may be available
    try {
      localStorage.setItem(
        "ocr_pending_merge",
        JSON.stringify({ bulletinIds: state.context.bulletinIds })
      );
    } catch {
      // Storage full — silently skip
    }
    send({ type: "MANUAL_FALLBACK" });
  }

  // --- Render ---

  if (state.matches("idle")) {
    return (
      <div className="flex flex-col gap-6 px-4 py-8 max-w-lg mx-auto">
        <div className="flex flex-col gap-2">
          <h1 className="text-[var(--text-h2)] font-semibold text-[var(--color-text)]">
            Tes bulletins, comment tu préfères ?
          </h1>
          <p className="text-[var(--text-body)] text-[var(--color-text-muted)]">
            3 façons de faire. Aucune n&apos;est mieux qu&apos;une autre — choisis selon ton humeur du moment.
          </p>
        </div>
        <ImportChoice3Cards onSelect={handleCardSelect} />
      </div>
    );
  }

  if (state.matches("picking_files")) {
    return (
      <FilePickerSheet
        open
        // eslint-disable-next-line react-hooks/refs
        files={pickerFilesRef.current}
        onFilesChange={(files) => {
          pickerFilesRef.current = files;
          send({
            type: "FILES_SELECTED",
            files: files.filter((f) => !f.error).map((f) => f.file),
          });
        }}
        onLaunch={handleLaunchUpload}
        onCancel={() => send({ type: "CANCEL_PICKER" })}
      />
    );
  }

  if (state.matches("uploading")) {
    // Live progress from hook, keyed by picker file ID
    // eslint-disable-next-line react-hooks/refs
    const uploadFiles: UploadFile[] = pickerFilesRef.current.map((pf) => {
      const progress = fileProgress[pf.id] ?? 0;
      return {
        id: pf.id,
        file: pf.file,
        progress,
        status: progress === 100 ? ("done" as const) : pf.error ? ("failed" as const) : ("uploading" as const),
        error: pf.error,
      };
    });
    return (
      <div className="px-4 py-8 max-w-lg mx-auto">
        <UploadProgress
          files={uploadFiles}
          onModifySelection={() => send({ type: "CANCEL_PICKER" })}
        />
      </div>
    );
  }

  if (state.matches("ocr_running")) {
    const firstStatus = ocrQueries[0]?.data?.status;
    const isComplete = allSucceeded;
    const isError = anyFailed;
    return (
      <div className="px-4 py-8 max-w-lg mx-auto">
        <OCRLoader
          bulletinIds={state.context.bulletinIds}
          estimatedSeconds={state.context.estimatedSeconds}
          ocrStatus={firstStatus}
          isNetworkError={hasNetworkError}
          isComplete={isComplete}
          isError={isError}
          onManualFallback={handleManualFallback}
        />
      </div>
    );
  }

  if (state.matches("recap_editing")) {
    return (
      <div className="px-4 py-8 max-w-lg mx-auto">
        <BulletinRecapEditor
          recaps={state.context.recaps}
          activeIndex={state.context.activeRecapIndex}
          onActiveChange={(i) => send({ type: "ACTIVATE_TAB", index: i })}
          onFieldsChange={handleFieldsChange}
          onValidate={handleValidateBulletin}
          onAllValidated={() => send({ type: "ALL_VALIDATED" })}
        />
      </div>
    );
  }

  if (state.matches("fallback")) {
    return (
      <div className="px-4 py-8 max-w-lg mx-auto">
        <OCRGracefulFallback
          onManual={handleManualFallback}
          onRetry={handleRetryScan}
        />
      </div>
    );
  }

  return null;
}
