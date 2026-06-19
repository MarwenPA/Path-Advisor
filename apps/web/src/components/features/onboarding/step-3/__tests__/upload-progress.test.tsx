import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { UploadFile } from "../onboarding-step3-machine";
import { UploadProgress } from "../upload-progress";

function makeFile(overrides?: Partial<UploadFile>): UploadFile {
  return {
    id: "file-1",
    file: new File(["content"], "bulletin.pdf", { type: "application/pdf" }),
    progress: 0,
    status: "uploading",
    ...overrides,
  };
}

describe("UploadProgress — AC3", () => {
  it("shows filename", () => {
    render(<UploadProgress files={[makeFile()]} />);
    expect(screen.getByText("bulletin.pdf")).toBeTruthy();
  });

  it("renders progress bar with correct aria-valuenow", () => {
    render(<UploadProgress files={[makeFile({ progress: 42 })]} />);
    const bar = screen.getByRole("progressbar");
    expect(bar.getAttribute("aria-valuenow")).toBe("42");
  });

  it("shows success state when done", () => {
    render(<UploadProgress files={[makeFile({ progress: 100, status: "done" })]} />);
    expect(screen.getByText(/terminé|done|✓/i)).toBeTruthy();
  });

  it("shows retry button on error", () => {
    render(<UploadProgress files={[makeFile({ status: "failed" })]} />);
    expect(screen.getByRole("button", { name: /retry|réessayer/i })).toBeTruthy();
  });

  it("has aria-live region for screen readers", () => {
    const { container } = render(<UploadProgress files={[makeFile()]} />);
    const liveRegion = container.querySelector("[aria-live]");
    expect(liveRegion).toBeTruthy();
  });
});
