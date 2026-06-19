/**
 * Story 2.3 — E2E: Bulletin import (OCR)
 * Personas: Sarah (happy path), Mehdi (low confidence), Léa (OCR fail)
 */

import { expect, test } from "@playwright/test";

const STEP3_URL = "/onboarding/step-3";

test.describe("Story 2.3 — Bulletin OCR", () => {
  test.describe("Sarah — happy path (clean OCR)", () => {
    test.beforeEach(async ({ page }) => {
      // Intercept API calls
      await page.route("**/api/v1/students/me/bulletins/upload", async (route) => {
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({ bulletin_id: "b1", file_path: "bulletins/b1.pdf" }),
        });
      });

      await page.route("**/api/v1/students/me/bulletins/ocr/start", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ job_ids: ["j1"], estimated_seconds: 8 }),
        });
      });

      let pollCount = 0;
      await page.route("**/api/v1/students/me/bulletins/ocr/status*", async (route) => {
        pollCount++;
        if (pollCount >= 2) {
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({
              status: "succeeded",
              extraction: {
                is_low_quality: false,
                confidence_avg: 0.88,
                normalized_fields: [
                  { key: "matiere_0", label: "Mathématiques", value: "15.5", confidence: 0.9, isLowConfidence: false },
                  { key: "matiere_1", label: "Français", value: "13", confidence: 0.85, isLowConfidence: false },
                  { key: "matiere_2", label: "Histoire-Géo", value: "14", confidence: 0.88, isLowConfidence: false },
                ],
              },
            }),
          });
        } else {
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({ status: "running" }),
          });
        }
      });

      await page.route("**/api/v1/students/me/bulletins/b1/finalize", async (route) => {
        await route.fulfill({ status: 200, contentType: "application/json", body: "{}" });
      });

      await page.goto(STEP3_URL);
    });

    test("shows 3 equal cards", async ({ page }) => {
      const cards = page.locator("button").filter({ hasText: /./ });
      await expect(cards).toHaveCount(3);
    });

    test("scan card → file picker → upload → OCR → recap → validate → dashboard", async ({ page }) => {
      // 1. Select scan card (first card)
      await page.locator("button").nth(0).click();

      // 2. FilePickerSheet should open
      await expect(page.locator("[role='dialog'], [data-state='open']").first()).toBeVisible();

      // 3. Upload a fake PDF
      const [fileChooser] = await Promise.all([
        page.waitForEvent("filechooser"),
        page.getByRole("button", { name: /ajouter|choisir|select/i }).click(),
      ]);
      await fileChooser.setFiles({
        name: "bulletin.pdf",
        mimeType: "application/pdf",
        buffer: Buffer.from("%PDF-1.4 test"),
      });

      // 4. Launch upload
      await page.getByRole("button", { name: /analyser|lancer|upload/i }).click();

      // 5. OCR loader appears
      await expect(page.getByTestId("scenario-loader")).toBeVisible({ timeout: 10_000 });

      // 6. OCR succeeds → recap editor appears
      await expect(page.locator("table")).toBeVisible({ timeout: 15_000 });
      await expect(page.getByText("Mathématiques")).toBeVisible();

      // 7. Validate
      await page.getByRole("button", { name: /valid/i }).click();

      // 8. Should redirect to dashboard
      await expect(page).toHaveURL(/dashboard/, { timeout: 5_000 });
    });
  });

  test.describe("Mehdi — low confidence", () => {
    test.beforeEach(async ({ page }) => {
      await page.route("**/api/v1/students/me/bulletins/upload", async (route) => {
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({ bulletin_id: "b2", file_path: "bulletins/b2.pdf" }),
        });
      });

      await page.route("**/api/v1/students/me/bulletins/ocr/start", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ job_ids: ["j2"], estimated_seconds: 8 }),
        });
      });

      await page.route("**/api/v1/students/me/bulletins/ocr/status*", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            status: "succeeded",
            extraction: {
              is_low_quality: false,
              confidence_avg: 0.55,
              normalized_fields: [
                { key: "matiere_0", label: "Maths", value: "?", confidence: 0.45, isLowConfidence: true },
              ],
            },
          }),
        });
      });

      await page.route("**/api/v1/students/me/bulletins/b2/finalize", async (route) => {
        await route.fulfill({ status: 200, contentType: "application/json", body: "{}" });
      });

      await page.goto(STEP3_URL);
    });

    test("shows low-confidence indicators in recap editor", async ({ page }) => {
      await page.locator("button").nth(0).click();

      const [fileChooser] = await Promise.all([
        page.waitForEvent("filechooser"),
        page.getByRole("button", { name: /ajouter|choisir|select/i }).click(),
      ]);
      await fileChooser.setFiles({
        name: "bulletin.pdf",
        mimeType: "application/pdf",
        buffer: Buffer.from("%PDF-1.4 test"),
      });

      await page.getByRole("button", { name: /analyser|lancer|upload/i }).click();
      await expect(page.locator("table")).toBeVisible({ timeout: 15_000 });

      // Low-confidence indicator must be present
      const lowConfEl = page.locator("[data-low-confidence], [aria-label*='confidence']").first();
      await expect(lowConfEl).toBeVisible();
    });
  });

  test.describe("Léa — OCR failure → graceful fallback", () => {
    test.beforeEach(async ({ page }) => {
      await page.route("**/api/v1/students/me/bulletins/upload", async (route) => {
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({ bulletin_id: "b3", file_path: "bulletins/b3.pdf" }),
        });
      });

      await page.route("**/api/v1/students/me/bulletins/ocr/start", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ job_ids: ["j3"], estimated_seconds: 8 }),
        });
      });

      await page.route("**/api/v1/students/me/bulletins/ocr/status*", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ status: "failed", error: "Extraction impossible." }),
        });
      });

      await page.goto(STEP3_URL);
    });

    test("shows graceful fallback with 2 equivalent CTAs", async ({ page }) => {
      await page.locator("button").nth(0).click();

      const [fileChooser] = await Promise.all([
        page.waitForEvent("filechooser"),
        page.getByRole("button", { name: /ajouter|choisir|select/i }).click(),
      ]);
      await fileChooser.setFiles({
        name: "bulletin.pdf",
        mimeType: "application/pdf",
        buffer: Buffer.from("%PDF-1.4 test"),
      });

      await page.getByRole("button", { name: /analyser|lancer|upload/i }).click();

      // Graceful fallback should appear
      await expect(page.getByRole("button", { name: /main|saisir/i })).toBeVisible({ timeout: 15_000 });
      await expect(page.getByRole("button", { name: /réessayer|retry/i })).toBeVisible();
    });
  });
});
