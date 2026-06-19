import { assign, createMachine } from "xstate";

export type UploadFile = {
  id: string;
  file: File;
  progress: number;
  status: "pending" | "uploading" | "done" | "failed";
  bulletinId?: string;
  error?: string;
};

export type NormalizedField = {
  key: "matiere" | "note" | "appreciation" | "trimestre" | "annee";
  value: string;
  confidence: number;
  isLowConfidence?: boolean;
  unmapped?: boolean;
  canonical_id?: string | null;
  raw?: string;
};

export type BulletinRecap = {
  bulletinId: string;
  label: string;
  fields: NormalizedField[];
  confidenceAvg: number;
  validated: boolean;
  draftFields?: NormalizedField[];
};

export type Step3Context = {
  files: UploadFile[];
  bulletinIds: string[];
  estimatedSeconds: number;
  recaps: BulletinRecap[];
  activeRecapIndex: number;
  ocrError: string | null;
  navigateTo: "manual" | "later" | null;
};

export type Step3Event =
  | { type: "SELECT_SCAN" }
  | { type: "SELECT_MANUAL" }
  | { type: "SELECT_LATER" }
  | { type: "CANCEL_PICKER" }
  | { type: "FILES_SELECTED"; files: File[] }
  | { type: "UPLOAD_START" }
  | { type: "FILE_PROGRESS"; fileId: string; progress: number }
  | { type: "FILE_DONE"; fileId: string; bulletinId: string }
  | { type: "FILE_FAILED"; fileId: string; error: string }
  | { type: "UPLOADS_COMPLETE"; bulletinIds: string[] }
  | { type: "OCR_STARTED"; estimatedSeconds: number }
  | { type: "OCR_SUCCESS"; recaps: BulletinRecap[] }
  | { type: "OCR_FAILED"; error: string }
  | { type: "MANUAL_FALLBACK" }
  | { type: "RETRY_SCAN" }
  | { type: "FIELD_EDITED"; bulletinId: string; fields: NormalizedField[] }
  | { type: "VALIDATE_BULLETIN"; bulletinId: string }
  | { type: "ACTIVATE_TAB"; index: number }
  | { type: "ALL_VALIDATED" }
  | {
      type: "HYDRATE";
      serverState: "idle" | "ocr_running" | "recap_editing" | "fallback";
      bulletinIds?: string[];
      recaps?: BulletinRecap[];
      ocrError?: string;
    };

export const initialContext: Step3Context = {
  files: [],
  bulletinIds: [],
  estimatedSeconds: 25,
  recaps: [],
  activeRecapIndex: 0,
  ocrError: null,
  navigateTo: null,
};

export const onboardingStep3Machine = createMachine(
  {
    id: "onboardingStep3",
    initial: "idle",
    types: {} as { context: Step3Context; events: Step3Event },
    context: initialContext,

    states: {
      idle: {
        on: {
          SELECT_SCAN: "picking_files",
          SELECT_MANUAL: {
            actions: assign({ navigateTo: () => "manual" as const }),
          },
          SELECT_LATER: {
            actions: assign({ navigateTo: () => "later" as const }),
          },
          HYDRATE: [
            {
              guard: ({ event }) => event.serverState === "ocr_running",
              target: "ocr_running",
              actions: assign({
                bulletinIds: ({ event }) => event.bulletinIds ?? [],
              }),
            },
            {
              guard: ({ event }) => event.serverState === "recap_editing",
              target: "recap_editing",
              actions: assign({
                bulletinIds: ({ event }) => event.bulletinIds ?? [],
                recaps: ({ event }) => event.recaps ?? [],
              }),
            },
            {
              guard: ({ event }) => event.serverState === "fallback",
              target: "fallback",
              actions: assign({
                bulletinIds: ({ event }) => event.bulletinIds ?? [],
                ocrError: ({ event }) => event.ocrError ?? null,
              }),
            },
          ],
        },
      },

      picking_files: {
        on: {
          CANCEL_PICKER: "idle",
          FILES_SELECTED: {
            actions: assign({
              files: ({ event }) =>
                event.files.map((f) => ({
                  id: crypto.randomUUID(),
                  file: f,
                  progress: 0,
                  status: "pending" as const,
                })),
            }),
          },
          UPLOAD_START: {
            // Guard: files must have been selected via FILES_SELECTED (#26)
            guard: ({ context }) => context.files.length > 0,
            target: "uploading",
          },
        },
      },

      uploading: {
        on: {
          FILE_PROGRESS: {
            actions: assign({
              files: ({ context, event }) =>
                context.files.map((f) =>
                  f.id === event.fileId ? { ...f, progress: event.progress } : f
                ),
            }),
          },
          FILE_DONE: {
            actions: assign({
              files: ({ context, event }) =>
                context.files.map((f) =>
                  f.id === event.fileId
                    ? { ...f, status: "done" as const, bulletinId: event.bulletinId, progress: 100 }
                    : f
                ),
            }),
          },
          FILE_FAILED: {
            actions: assign({
              files: ({ context, event }) =>
                context.files.map((f) =>
                  f.id === event.fileId
                    ? { ...f, status: "failed" as const, error: event.error }
                    : f
                ),
            }),
          },
          UPLOADS_COMPLETE: {
            target: "ocr_running",
            actions: assign({
              bulletinIds: ({ event }) => event.bulletinIds,
            }),
          },
        },
      },

      ocr_running: {
        on: {
          OCR_STARTED: {
            actions: assign({
              estimatedSeconds: ({ event }) => event.estimatedSeconds,
            }),
          },
          OCR_SUCCESS: {
            target: "recap_editing",
            actions: assign({
              recaps: ({ event }) => event.recaps,
              activeRecapIndex: () => 0,
            }),
          },
          OCR_FAILED: {
            target: "fallback",
            actions: assign({ ocrError: ({ event }) => event.error }),
          },
          MANUAL_FALLBACK: {
            actions: assign({ navigateTo: () => "manual" as const }),
          },
        },
      },

      recap_editing: {
        on: {
          FIELD_EDITED: {
            actions: assign({
              recaps: ({ context, event }) =>
                context.recaps.map((r) =>
                  r.bulletinId === event.bulletinId
                    ? { ...r, draftFields: event.fields }
                    : r
                ),
            }),
          },
          VALIDATE_BULLETIN: {
            actions: assign({
              recaps: ({ context, event }) =>
                context.recaps.map((r) =>
                  r.bulletinId === event.bulletinId ? { ...r, validated: true } : r
                ),
              activeRecapIndex: ({ context, event }) => {
                // Find first unvalidated recap that isn't the one just validated (#13: removed i > 0)
                const updatedRecaps = context.recaps.map((r) =>
                  r.bulletinId === event.bulletinId ? { ...r, validated: true } : r
                );
                const next = updatedRecaps.findIndex((r) => !r.validated);
                return next >= 0 ? next : context.activeRecapIndex;
              },
            }),
          },
          ACTIVATE_TAB: {
            actions: assign({
              activeRecapIndex: ({ event }) => event.index,
            }),
          },
          ALL_VALIDATED: "validated",
        },
      },

      fallback: {
        on: {
          MANUAL_FALLBACK: {
            actions: assign({ navigateTo: () => "manual" as const }),
          },
          RETRY_SCAN: {
            target: "picking_files",
            // #9: use function form for assign in XState v5
            actions: assign(() => ({ ...initialContext })),
          },
          SELECT_LATER: {
            actions: assign({ navigateTo: () => "later" as const }),
          },
        },
      },

      validated: {
        type: "final",
      },
    },
  }
);
