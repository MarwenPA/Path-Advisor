import { describe, it, expect, vi, afterEach } from "vitest";

import type { Profession } from "@/components/professions/types";

// Mock apiFetch before importing the module under test
vi.mock("../client", () => ({
  apiFetch: vi.fn(),
  ApiError: class ApiError extends Error {
    status: number;
    constructor(message: string, status: number) {
      super(message);
      this.status = status;
    }
  },
}));

const SAMPLE_PROFESSION: Profession = {
  id: "prof_01",
  slug: "infirmier-ssr",
  name: "Infirmier·ère SSR",
  description: "Prend en charge des patients en soins de suite.",
  daily_routine: "Tu commences ta matinée en faisant le tour des chambres.",
  requirements_json: [
    { type: "studies", label: "Diplôme d'État infirmier (3 ans)" },
    { type: "quality", label: "Empathie" },
  ],
  prospects_text: "Évolution vers cadre de santé possible.",
  median_salary_eur: 28000,
  salary_range_json: { min: 24000, max: 38000, source: "Onisep 2025" },
  signals_json: {
    passions: ["soins", "aide aux personnes"],
    valeurs: ["entraide"],
    specialites: ["svt"],
  },
  level_compatibility: ["lycee_1ere_tle_general"],
  sector: "santé",
};

describe("fetchProfession", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("returns profession data on success", async () => {
    const { apiFetch } = await import("../client");
    vi.mocked(apiFetch).mockResolvedValueOnce(SAMPLE_PROFESSION);

    const { fetchProfession } = await import("../professions");
    const result = await fetchProfession("infirmier-ssr");

    expect(apiFetch).toHaveBeenCalledWith("/api/v1/professions/infirmier-ssr/");
    expect(result.slug).toBe("infirmier-ssr");
    expect(result.name).toBe("Infirmier·ère SSR");
    expect(result.signals_json.passions).toContain("soins");
  });

  it("propagates ApiError on 404", async () => {
    const { apiFetch, ApiError } = await import("../client");
    vi.mocked(apiFetch).mockRejectedValueOnce(new ApiError("Not found", 404));

    const { fetchProfession } = await import("../professions");
    await expect(fetchProfession("slug-inconnu")).rejects.toThrow();
  });

  it("passes slug correctly in URL", async () => {
    const { apiFetch } = await import("../client");
    vi.mocked(apiFetch).mockResolvedValueOnce(SAMPLE_PROFESSION);

    const { fetchProfession } = await import("../professions");
    await fetchProfession("medecin-generaliste");

    expect(apiFetch).toHaveBeenCalledWith("/api/v1/professions/medecin-generaliste/");
  });
});
