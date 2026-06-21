import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SchoolCompare } from "../SchoolCompare";
import type { School } from "@/lib/api/schools";

function makeSchool(id: string, name: string): School {
  return {
    id,
    slug: id,
    name,
    type: "IUT",
    city: "Paris",
    region: "Ile-de-France",
    postal_code: "75000",
    apprenticeship: true,
    internship: false,
    selectivity_index: 3,
    public_private: "public",
    description: "",
    top_debouches: [],
    parcoursup_dates: {},
    affelnet_dates: {},
    official_url: "",
    tuition_min_eur: 0,
    tuition_max_eur: 0,
    formations: [],
  };
}

const SCHOOL_A = makeSchool("a", "IUT Paris A");
const SCHOOL_B = makeSchool("b", "IUT Paris B");
const SCHOOL_C = makeSchool("c", "IUT Paris C");
const SCHOOL_D = makeSchool("d", "IUT Paris D");

describe("SchoolCompare", () => {
  it("renders list of schools in compare mode (checkboxes)", () => {
    render(<SchoolCompare schools={[SCHOOL_A, SCHOOL_B]} />);
    expect(screen.getByRole("checkbox", { name: /IUT Paris A/i })).toBeInTheDocument();
    expect(screen.getByRole("checkbox", { name: /IUT Paris B/i })).toBeInTheDocument();
  });

  it("does not show comparison table when fewer than 2 schools selected", () => {
    render(<SchoolCompare schools={[SCHOOL_A, SCHOOL_B]} />);
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });

  it("selecting 2 schools shows comparison table", async () => {
    const user = userEvent.setup();
    render(<SchoolCompare schools={[SCHOOL_A, SCHOOL_B]} />);
    await user.click(screen.getByRole("checkbox", { name: /IUT Paris A/i }));
    await user.click(screen.getByRole("checkbox", { name: /IUT Paris B/i }));
    expect(screen.getByRole("table")).toBeInTheDocument();
  });

  it("comparison table has correct field rows", async () => {
    const user = userEvent.setup();
    render(<SchoolCompare schools={[SCHOOL_A, SCHOOL_B]} />);
    await user.click(screen.getByRole("checkbox", { name: /IUT Paris A/i }));
    await user.click(screen.getByRole("checkbox", { name: /IUT Paris B/i }));
    const table = screen.getByRole("table");
    expect(table).toBeInTheDocument();
    // Check expected field labels
    expect(screen.getByText("Type")).toBeInTheDocument();
    expect(screen.getByText("Ville")).toBeInTheDocument();
    expect(screen.getByText("Statut")).toBeInTheDocument();
    expect(screen.getByText("Selectivite")).toBeInTheDocument();
    expect(screen.getByText("Alternance")).toBeInTheDocument();
    expect(screen.getByText("Internat")).toBeInTheDocument();
  });

  it("selecting more than 3 is prevented (max 3)", async () => {
    const user = userEvent.setup();
    render(<SchoolCompare schools={[SCHOOL_A, SCHOOL_B, SCHOOL_C, SCHOOL_D]} />);
    await user.click(screen.getByRole("checkbox", { name: /IUT Paris A/i }));
    await user.click(screen.getByRole("checkbox", { name: /IUT Paris B/i }));
    await user.click(screen.getByRole("checkbox", { name: /IUT Paris C/i }));
    // 4th click should be ignored
    await user.click(screen.getByRole("checkbox", { name: /IUT Paris D/i }));
    // D should remain unchecked
    expect(screen.getByRole("checkbox", { name: /IUT Paris D/i })).not.toBeChecked();
    // A, B, C should be checked
    expect(screen.getByRole("checkbox", { name: /IUT Paris A/i })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: /IUT Paris B/i })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: /IUT Paris C/i })).toBeChecked();
  });

  it("shows max-selection status message when 3 schools selected", async () => {
    const user = userEvent.setup();
    render(<SchoolCompare schools={[SCHOOL_A, SCHOOL_B, SCHOOL_C, SCHOOL_D]} />);
    await user.click(screen.getByRole("checkbox", { name: /IUT Paris A/i }));
    await user.click(screen.getByRole("checkbox", { name: /IUT Paris B/i }));
    await user.click(screen.getByRole("checkbox", { name: /IUT Paris C/i }));
    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent(/Maximum 3/i);
  });

  it("table column headers include school names", async () => {
    const user = userEvent.setup();
    render(<SchoolCompare schools={[SCHOOL_A, SCHOOL_B]} />);
    await user.click(screen.getByRole("checkbox", { name: /IUT Paris A/i }));
    await user.click(screen.getByRole("checkbox", { name: /IUT Paris B/i }));
    expect(
      screen.getAllByRole("columnheader").some((th) => th.textContent?.includes("IUT Paris A")),
    ).toBe(true);
    expect(
      screen.getAllByRole("columnheader").some((th) => th.textContent?.includes("IUT Paris B")),
    ).toBe(true);
  });
});
