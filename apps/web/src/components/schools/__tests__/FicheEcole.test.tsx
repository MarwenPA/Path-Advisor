import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithIntl } from "@/test/render-with-intl";
import { FicheEcole } from "../FicheEcole";
import type { School, AdmissionStat } from "@/lib/api/schools";

const SCHOOL: School = {
  id: "abc",
  slug: "lycee-pro-aeronautique-toulouse",
  name: "Lycée Aéronautique Toulouse",
  type: "lycee_pro",
  city: "Toulouse",
  region: "Occitanie",
  postal_code: "31000",
  apprenticeship: false,
  internship: true,
  selectivity_index: 4,
  public_private: "public",
  description: "",
  top_debouches: ["Technicien avionique"],
  parcoursup_dates: {},
  affelnet_dates: {},
  official_url: "",
  tuition_min_eur: 0,
  tuition_max_eur: 0,
  formations: [
    {
      id: "f1",
      name: "Bac Pro Avionique",
      duration_years: 3,
      parcoursup_open: false,
      affelnet_open: true,
    },
  ],
};

const ADMISSION_STAT: AdmissionStat = {
  min_proba: 30,
  expected_proba: 55,
  max_proba: 75,
  label: "realiste",
  context_line: "Tu as de bonnes chances d'être admis·e.",
  action_lever: "Continue à maintenir tes résultats actuels.",
};

describe("FicheEcole", () => {
  it("renders school name and city", () => {
    renderWithIntl(<FicheEcole school={SCHOOL} />);
    expect(screen.getByText("Lycée Aéronautique Toulouse")).toBeInTheDocument();
    // city appears in the subtitle paragraph (Toulouse · Occitanie)
    expect(screen.getAllByText(/Toulouse/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Toulouse\s*·\s*Occitanie/)).toBeInTheDocument();
  });

  it("renders selectivity stars with aria-label", () => {
    renderWithIntl(<FicheEcole school={SCHOOL} />);
    expect(screen.getByLabelText(/Sélectivité : 4 sur 5/i)).toBeInTheDocument();
  });

  it("variant card does NOT show formations list", () => {
    renderWithIntl(<FicheEcole school={SCHOOL} variant="card" />);
    expect(screen.queryByRole("listitem", { name: /Bac Pro Avionique/i })).not.toBeInTheDocument();
    expect(screen.queryByText("Bac Pro Avionique")).not.toBeInTheDocument();
  });

  it("variant expanded shows formations list", () => {
    renderWithIntl(<FicheEcole school={SCHOOL} variant="expanded" />);
    expect(screen.getByText("Bac Pro Avionique")).toBeInTheDocument();
  });

  it("variant expanded shows top_debouches", () => {
    renderWithIntl(<FicheEcole school={SCHOOL} variant="expanded" />);
    expect(screen.getByText("Technicien avionique")).toBeInTheDocument();
  });

  it("tuition 0-0 shows 'Gratuit'", () => {
    renderWithIntl(<FicheEcole school={SCHOOL} />);
    expect(screen.getByText("Gratuit")).toBeInTheDocument();
  });

  it("article has aria-label with school name", () => {
    renderWithIntl(<FicheEcole school={SCHOOL} />);
    expect(
      screen.getByRole("article", { name: /Fiche de Lycée Aéronautique Toulouse/i }),
    ).toBeInTheDocument();
  });

  it("dl has dt/dd pairs for Type and Accès", () => {
    renderWithIntl(<FicheEcole school={SCHOOL} />);
    expect(screen.getByText("Type")).toBeInTheDocument();
    expect(screen.getByText("lycee_pro")).toBeInTheDocument();
    expect(screen.getByText("Accès")).toBeInTheDocument();
    expect(screen.getByText("public")).toBeInTheDocument();
  });

  // ── RGAA 9.1 — heading levels per variant ──────────────────────────────────

  it("expanded variant renders the school name as <h1> (page-level heading)", () => {
    renderWithIntl(<FicheEcole school={SCHOOL} variant="expanded" />);
    expect(
      screen.getByRole("heading", { level: 1, name: "Lycée Aéronautique Toulouse" }),
    ).toBeInTheDocument();
    // sub-sections follow as <h2> — no skipped level
    expect(screen.getByRole("heading", { level: 2, name: "Formations" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2, name: "Débouchés" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { level: 3 })).not.toBeInTheDocument();
  });

  it("card variant renders the school name as <h2> (lives under a page <h1>)", () => {
    renderWithIntl(<FicheEcole school={SCHOOL} variant="card" />);
    expect(
      screen.getByRole("heading", { level: 2, name: "Lycée Aéronautique Toulouse" }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("heading", { level: 1 })).not.toBeInTheDocument();
  });

  // ── Null tuition (Django serializes JSON null, not undefined) ──────────────

  it("null tuition hides the Frais row instead of rendering 'null–null €/an'", () => {
    const schoolNullTuition = {
      ...SCHOOL,
      tuition_min_eur: null,
      tuition_max_eur: null,
    } as unknown as School;
    renderWithIntl(<FicheEcole school={schoolNullTuition} variant="expanded" />);
    expect(screen.queryByText("Frais")).not.toBeInTheDocument();
    expect(screen.queryByText(/null/)).not.toBeInTheDocument();
  });

  it("non-zero tuition renders the range", () => {
    const schoolPaid = { ...SCHOOL, tuition_min_eur: 500, tuition_max_eur: 1200 };
    renderWithIntl(<FicheEcole school={schoolPaid} variant="expanded" />);
    expect(screen.getByText("500–1200 €/an")).toBeInTheDocument();
  });

  // ── ICU plural for formation duration ───────────────────────────────────────

  it("pluralises duration ('3 ans' vs '1 an')", () => {
    const school = {
      ...SCHOOL,
      formations: [
        { id: "f1", name: "A", duration_years: 3, parcoursup_open: false, affelnet_open: true },
        { id: "f2", name: "B", duration_years: 1, parcoursup_open: false, affelnet_open: true },
      ],
    };
    renderWithIntl(<FicheEcole school={school} variant="expanded" />);
    expect(screen.getByText("3 ans")).toBeInTheDocument();
    expect(screen.getByText("1 an")).toBeInTheDocument();
  });

  // ── Story 4.5 — admission stat block ────────────────────────────────────────

  it("expanded shows CarteAdmission when admission_stat present", () => {
    const schoolWithStat: School = { ...SCHOOL, admission_stat: ADMISSION_STAT };
    renderWithIntl(<FicheEcole school={schoolWithStat} variant="expanded" />);
    expect(screen.getByRole("region", { name: /statistique d'admission/i })).toBeInTheDocument();
    // CarteAdmission renders the proba and label
    expect(screen.getByText(/55 %/)).toBeInTheDocument();
    expect(screen.getByText(/pari réaliste/i)).toBeInTheDocument();
  });

  it("expanded HIDES the admission section entirely when the field is absent (anonymous public payload)", () => {
    // JSON.parse of the public SEO payload never yields the key at all
    const anonymousSchool: School = { ...SCHOOL };
    delete anonymousSchool.admission_stat;
    renderWithIntl(<FicheEcole school={anonymousSchool} variant="expanded" />);
    expect(
      screen.queryByRole("region", { name: /statistique d'admission/i }),
    ).not.toBeInTheDocument();
    expect(screen.queryByText(/tes chances d'admission/i)).not.toBeInTheDocument();
  });

  it("expanded shows fallback text when admission_stat is explicitly null (authenticated, not computed yet)", () => {
    const schoolNoStat = { ...SCHOOL, admission_stat: null } as unknown as School;
    renderWithIntl(<FicheEcole school={schoolNoStat} variant="expanded" />);
    expect(screen.getByRole("region", { name: /statistique d'admission/i })).toBeInTheDocument();
    expect(screen.getByText(/données d'admission non disponibles/i)).toBeInTheDocument();
  });

  it("card variant does NOT show admission stat section", () => {
    const schoolWithStat: School = { ...SCHOOL, admission_stat: ADMISSION_STAT };
    renderWithIntl(<FicheEcole school={schoolWithStat} variant="card" />);
    expect(
      screen.queryByRole("region", { name: /statistique d'admission/i }),
    ).not.toBeInTheDocument();
  });

  // ── Story 4.10 — compare variant ────────────────────────────────────────────

  it("compare variant renders checkbox with accented aria-label", () => {
    renderWithIntl(<FicheEcole school={SCHOOL} variant="compare" />);
    expect(
      screen.getByRole("checkbox", {
        name: /Sélectionner Lycée Aéronautique Toulouse pour comparer/i,
      }),
    ).toBeInTheDocument();
  });

  it("compare variant checkbox is checked when isSelected=true", () => {
    renderWithIntl(<FicheEcole school={SCHOOL} variant="compare" isSelected={true} />);
    expect(screen.getByRole("checkbox", { name: /Sélectionner/i })).toBeChecked();
  });

  it("compare variant checkbox is unchecked by default", () => {
    renderWithIntl(<FicheEcole school={SCHOOL} variant="compare" />);
    expect(screen.getByRole("checkbox", { name: /Sélectionner/i })).not.toBeChecked();
  });

  it("compare variant calls onSelect with school id when checkbox clicked", () => {
    const onSelect = vi.fn();
    renderWithIntl(<FicheEcole school={SCHOOL} variant="compare" onSelect={onSelect} />);
    screen.getByRole("checkbox", { name: /Sélectionner/i }).click();
    expect(onSelect).toHaveBeenCalledWith("abc");
  });
});
