import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { FicheEcole } from "../FicheEcole";
import type { School } from "@/lib/api/schools";

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

describe("FicheEcole", () => {
  it("renders school name and city", () => {
    render(<FicheEcole school={SCHOOL} />);
    expect(screen.getByText("Lycée Aéronautique Toulouse")).toBeInTheDocument();
    // city appears in the subtitle paragraph (Toulouse · Occitanie)
    expect(screen.getAllByText(/Toulouse/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Toulouse\s*·\s*Occitanie/)).toBeInTheDocument();
  });

  it("renders selectivity stars with aria-label", () => {
    render(<FicheEcole school={SCHOOL} />);
    expect(screen.getByLabelText(/Sélectivité : 4 sur 5/i)).toBeInTheDocument();
  });

  it("variant card does NOT show formations list", () => {
    render(<FicheEcole school={SCHOOL} variant="card" />);
    expect(screen.queryByRole("listitem", { name: /Bac Pro Avionique/i })).not.toBeInTheDocument();
    expect(screen.queryByText("Bac Pro Avionique")).not.toBeInTheDocument();
  });

  it("variant expanded shows formations list", () => {
    render(<FicheEcole school={SCHOOL} variant="expanded" />);
    expect(screen.getByText("Bac Pro Avionique")).toBeInTheDocument();
  });

  it("variant expanded shows top_debouches", () => {
    render(<FicheEcole school={SCHOOL} variant="expanded" />);
    expect(screen.getByText("Technicien avionique")).toBeInTheDocument();
  });

  it("tuition 0-0 shows 'Gratuit'", () => {
    render(<FicheEcole school={SCHOOL} />);
    expect(screen.getByText("Gratuit")).toBeInTheDocument();
  });

  it("article has aria-label with school name", () => {
    render(<FicheEcole school={SCHOOL} />);
    expect(
      screen.getByRole("article", { name: /Fiche de Lycée Aéronautique Toulouse/i }),
    ).toBeInTheDocument();
  });

  it("dl has dt/dd pairs for Type and Accès", () => {
    render(<FicheEcole school={SCHOOL} />);
    expect(screen.getByText("Type")).toBeInTheDocument();
    expect(screen.getByText("lycee_pro")).toBeInTheDocument();
    expect(screen.getByText("Accès")).toBeInTheDocument();
    expect(screen.getByText("public")).toBeInTheDocument();
  });
});
