/**
 * `/parent/enfants/[studentId]/ecoles/[slug]` page tests — Story 6.2 AC2
 * + Story 6.3 AC3 (admission stat shown, action_lever never present).
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const fetchChildEcoleDetailMock = vi.fn();
vi.mock("@/lib/api/parent", () => ({
  fetchChildEcoleDetail: (...args: unknown[]) => fetchChildEcoleDetailMock(...args),
}));

const redirectMock = vi.fn();
const notFoundMock = vi.fn();
vi.mock("next/navigation", () => ({
  redirect: (...args: unknown[]) => redirectMock(...args),
  notFound: () => notFoundMock(),
}));

import { ApiError } from "@/lib/api/client";

import ParentChildEcoleDetailPage from "./page";

const BASE_ECOLE = {
  school_id: "sch_1",
  slug: "ecole-test",
  name: "École Test",
  type: "ecole_ingenieur",
  city: "Lyon",
  region: "Auvergne-Rhône-Alpes",
  description: "Une belle école.",
  tuition_min_eur: 1000,
  tuition_max_eur: 2000,
  formations: [{ name: "BTS SIO", duration_years: 2, parcoursup_open: true, affelnet_open: false }],
  admission_stat: null,
};

describe("ParentChildEcoleDetailPage", () => {
  it("renders school info without an admission stat when none exists", async () => {
    fetchChildEcoleDetailMock.mockResolvedValue(BASE_ECOLE);

    render(
      await ParentChildEcoleDetailPage({
        params: Promise.resolve({ studentId: "stu_1", slug: "ecole-test" }),
      }),
    );

    expect(screen.getByText("École Test")).toBeInTheDocument();
    expect(screen.queryByLabelText(/chances d'admission/i)).not.toBeInTheDocument();
  });

  it("shows the admission stat (CarteAdmission) but never an action_lever line", async () => {
    fetchChildEcoleDetailMock.mockResolvedValue({
      ...BASE_ECOLE,
      admission_stat: {
        min_proba: 30,
        expected_proba: 45,
        max_proba: 60,
        label: "realiste",
        context_line: "Tu as de bonnes chances d'être admis·e.",
        previous_proba: null,
        updated_at: "2026-09-10T00:00:00Z",
      },
    });

    render(
      await ParentChildEcoleDetailPage({
        params: Promise.resolve({ studentId: "stu_1", slug: "ecole-test" }),
      }),
    );

    expect(screen.getByLabelText(/chances d'admission/i)).toBeInTheDocument();
    expect(screen.getByText("45 %")).toBeInTheDocument();
    expect(screen.queryByText(/feraient passer/i)).not.toBeInTheDocument();
  });

  it("redirects to /auth/forbidden on a 403", async () => {
    fetchChildEcoleDetailMock.mockRejectedValue(new ApiError(403, "Interdit."));

    await ParentChildEcoleDetailPage({
      params: Promise.resolve({ studentId: "stu_1", slug: "ecole-test" }),
    });

    expect(redirectMock).toHaveBeenCalledWith("/auth/forbidden?from=/parent/enfants/stu_1");
  });

  it("calls notFound() on a 404", async () => {
    fetchChildEcoleDetailMock.mockRejectedValue(new ApiError(404, "Pas trouvé."));

    await ParentChildEcoleDetailPage({
      params: Promise.resolve({ studentId: "stu_1", slug: "ecole-inexistante" }),
    });

    expect(notFoundMock).toHaveBeenCalled();
  });
});
