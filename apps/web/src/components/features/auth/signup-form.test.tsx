import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

import { SignupForm } from "./signup-form";

vi.mock("@/lib/api/auth", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/auth")>("@/lib/api/auth");
  return {
    ...actual,
    signupStudent: vi.fn(),
  };
});

import { signupStudent } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";

const signupMock = vi.mocked(signupStudent);

beforeEach(() => {
  signupMock.mockReset();
});

describe("SignupForm", () => {
  it("renders the 4 fields, the consent checkbox, and the submit button", () => {
    render(<SignupForm />);

    expect(screen.getByLabelText(/adresse email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^mot de passe$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirme le mot de passe/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/date de naissance/i)).toBeInTheDocument();
    expect(screen.getByRole("checkbox")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /créer mon compte/i })).toBeInTheDocument();
  });

  it("blocks submit when consent checkbox is unchecked and surfaces the consent error", async () => {
    render(<SignupForm />);

    fireEvent.change(screen.getByLabelText(/adresse email/i), {
      target: { value: "sarah@example.test" },
    });
    fireEvent.change(screen.getByLabelText(/^mot de passe$/i), {
      target: { value: "Path-Advisor-2026!" },
    });
    fireEvent.change(screen.getByLabelText(/confirme le mot de passe/i), {
      target: { value: "Path-Advisor-2026!" },
    });
    fireEvent.change(screen.getByLabelText(/date de naissance/i), {
      target: { value: "2008-01-15" },
    });

    fireEvent.click(screen.getByRole("button", { name: /créer mon compte/i }));

    await waitFor(() => {
      expect(screen.getByText(/accepter les CGU et la politique RGPD/i)).toBeInTheDocument();
    });
    expect(signupMock).not.toHaveBeenCalled();
  });

  it("conditionally renders the parent_email field when birth_date implies age < 15", async () => {
    render(<SignupForm />);

    // Initially hidden: no birth_date entered yet.
    expect(screen.queryByLabelText(/email de ton parent/i)).not.toBeInTheDocument();

    // ≥ 15 → still hidden.
    fireEvent.change(screen.getByLabelText(/date de naissance/i), {
      target: { value: "2008-01-15" }, // ≥ 15 years old
    });
    await waitFor(() => {
      expect(screen.queryByLabelText(/email de ton parent/i)).not.toBeInTheDocument();
    });

    // < 15 → field appears.
    fireEvent.change(screen.getByLabelText(/date de naissance/i), {
      target: { value: "2014-01-15" }, // ~12 years old
    });
    await waitFor(() => {
      expect(screen.getByLabelText(/email de ton parent/i)).toBeInTheDocument();
    });
  });

  it("surfaces the API Problem detail when signup fails", async () => {
    signupMock.mockRejectedValueOnce(
      new ApiError(400, "Tu dois accepter les CGU et la politique RGPD pour continuer.", {
        type: "https://path-advisor.fr/errors/consent-rgpd-required",
        title: "Consentement RGPD requis",
        status: 400,
        detail: "Tu dois accepter les CGU et la politique RGPD pour continuer.",
      }),
    );

    render(<SignupForm />);

    fireEvent.change(screen.getByLabelText(/adresse email/i), {
      target: { value: "sarah@example.test" },
    });
    fireEvent.change(screen.getByLabelText(/^mot de passe$/i), {
      target: { value: "Path-Advisor-2026!" },
    });
    fireEvent.change(screen.getByLabelText(/confirme le mot de passe/i), {
      target: { value: "Path-Advisor-2026!" },
    });
    fireEvent.change(screen.getByLabelText(/date de naissance/i), {
      target: { value: "2008-01-15" },
    });
    fireEvent.click(screen.getByRole("checkbox"));

    fireEvent.click(screen.getByRole("button", { name: /créer mon compte/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
    expect(screen.getByRole("alert").textContent).toContain("RGPD");
  });
});
