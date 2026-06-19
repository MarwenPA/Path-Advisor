"use client";

import { useState } from "react";

export type UploadResult =
  | { status: "done"; bulletinId: string }
  | { status: "failed"; error: string };

export type UploadEntry = { id: string; file: File };

const MAX_RETRIES = 3;
const UPLOAD_TIMEOUT_MS = 60_000;

async function uploadOneFile(
  file: File,
  onProgress: (pct: number) => void,
  attempt = 0
): Promise<UploadResult> {
  return new Promise((resolve) => {
    const formData = new FormData();
    formData.append("file", file);

    const xhr = new XMLHttpRequest();
    const timeoutId = setTimeout(() => xhr.abort(), UPLOAD_TIMEOUT_MS);

    xhr.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    });

    xhr.addEventListener("load", () => {
      clearTimeout(timeoutId);
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const data = JSON.parse(xhr.responseText);
          resolve({ status: "done", bulletinId: data.id });
        } catch {
          resolve({ status: "failed", error: "Réponse serveur invalide." });
        }
      } else if (xhr.status >= 500 && attempt < MAX_RETRIES) {
        const delay = Math.pow(2, attempt) * 1000;
        setTimeout(() => uploadOneFile(file, onProgress, attempt + 1).then(resolve), delay);
      } else {
        resolve({
          status: "failed",
          error: `Erreur serveur (${xhr.status}). Réessaie ou saisir à la main.`,
        });
      }
    });

    xhr.addEventListener("error", () => {
      clearTimeout(timeoutId);
      if (attempt < MAX_RETRIES) {
        const delay = Math.pow(2, attempt) * 1000;
        setTimeout(() => uploadOneFile(file, onProgress, attempt + 1).then(resolve), delay);
      } else {
        resolve({ status: "failed", error: "Réseau indisponible après 3 essais." });
      }
    });

    xhr.addEventListener("abort", () => {
      clearTimeout(timeoutId);
      resolve({ status: "failed", error: "Upload annulé (timeout 60 s)." });
    });

    xhr.open("POST", "/api/v1/students/me/bulletins/upload");
    xhr.withCredentials = true;
    xhr.send(formData);
  });
}

/**
 * Upload up to 6 files in parallel batches of 3.
 * Accepts entries with stable IDs so progress can be keyed without name collisions.
 */
export function useBulletinUpload() {
  const [fileProgress, setFileProgress] = useState<Record<string, number>>({});

  const upload = async (
    entries: UploadEntry[]
  ): Promise<{
    results: Array<{ entry: UploadEntry; result: UploadResult }>;
    bulletinIds: string[];
  }> => {
    setFileProgress({});

    const BATCH_SIZE = 3;
    const allResults: Array<{ entry: UploadEntry; result: UploadResult }> = [];

    for (let i = 0; i < entries.length; i += BATCH_SIZE) {
      const batch = entries.slice(i, i + BATCH_SIZE);
      const batchResults = await Promise.all(
        batch.map(({ id, file }) =>
          uploadOneFile(file, (pct) => {
            setFileProgress((prev) => ({ ...prev, [id]: pct }));
          }).then((result) => ({ entry: { id, file }, result }))
        )
      );
      allResults.push(...batchResults);
    }

    const bulletinIds = allResults
      .filter((r) => r.result.status === "done")
      .map((r) => (r.result as { status: "done"; bulletinId: string }).bulletinId);

    return { results: allResults, bulletinIds };
  };

  return { upload, fileProgress };
}
