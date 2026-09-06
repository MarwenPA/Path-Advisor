/**
 * <AdmissionStatPoller> tests — Story 5.8 AC3.
 */
import { render, screen, act } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

const fetchAdmissionStatMock = vi.fn();
vi.mock("@/lib/api/schools", () => ({
  fetchAdmissionStat: (...args: unknown[]) => fetchAdmissionStatMock(...args),
}));

import { AdmissionStatPoller } from "../AdmissionStatPoller";

const BASE_STAT = {
  min_proba: 30,
  expected_proba: 50,
  max_proba: 70,
  label: "realiste" as const,
  context_line: "Contexte.",
  action_lever: null,
};

beforeEach(() => {
  vi.useFakeTimers();
  fetchAdmissionStatMock.mockReset();
});

afterEach(() => {
  vi.useRealTimers();
});

describe("AdmissionStatPoller", () => {
  it("renders the initial stat immediately without polling", () => {
    render(
      <AdmissionStatPoller
        initialStat={BASE_STAT}
        schoolSlug="ecole-test"
        schoolName="École Test"
      />,
    );

    expect(screen.getByText("50 %")).toBeInTheDocument();
    expect(fetchAdmissionStatMock).not.toHaveBeenCalled();
  });

  it("polls every 30s and re-renders with the fresh value", async () => {
    fetchAdmissionStatMock.mockResolvedValue({ ...BASE_STAT, expected_proba: 65 });

    render(
      <AdmissionStatPoller
        initialStat={BASE_STAT}
        schoolSlug="ecole-test"
        schoolName="École Test"
      />,
    );

    await act(async () => {
      await vi.advanceTimersByTimeAsync(30_000);
    });

    expect(fetchAdmissionStatMock).toHaveBeenCalledWith("ecole-test");
    expect(screen.getByText("65 %")).toBeInTheDocument();
  });

  it("keeps the last known value on a transient poll failure", async () => {
    fetchAdmissionStatMock.mockRejectedValue(new Error("network down"));

    render(
      <AdmissionStatPoller
        initialStat={BASE_STAT}
        schoolSlug="ecole-test"
        schoolName="École Test"
      />,
    );

    await act(async () => {
      await vi.advanceTimersByTimeAsync(30_000);
    });

    expect(screen.getByText("50 %")).toBeInTheDocument();
  });
});
