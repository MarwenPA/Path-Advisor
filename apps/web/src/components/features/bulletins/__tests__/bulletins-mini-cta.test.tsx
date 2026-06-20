import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { BulletinsMiniCTA } from "../bulletins-mini-cta";

vi.mock("../../../../hooks/use-student-profile", () => ({
  useStudentProfile: vi.fn(),
}));

import { useStudentProfile } from "../../../../hooks/use-student-profile";

type MockReturn = ReturnType<typeof useStudentProfile>;

function wrap(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>);
}

describe("BulletinsMiniCTA", () => {
  it("renders for postponed user", () => {
    vi.mocked(useStudentProfile).mockReturnValue({
      data: { bulletins_status: "postponed" },
      isLoading: false,
    } as unknown as MockReturn);

    wrap(
      <BulletinsMiniCTA
        context="graph"
        onAddClick={vi.fn()}
      />
    );

    expect(screen.getByRole("complementary")).toBeInTheDocument();
    expect(screen.getByText(/ajoute tes bulletins/i)).toBeInTheDocument();
  });

  it("does not render when bulletins_status is completed", () => {
    vi.mocked(useStudentProfile).mockReturnValue({
      data: { bulletins_status: "completed" },
      isLoading: false,
    } as unknown as MockReturn);

    wrap(
      <BulletinsMiniCTA
        context="graph"
        onAddClick={vi.fn()}
      />
    );

    expect(screen.queryByRole("complementary")).toBeNull();
  });

  it("calls onAddClick when CTA button is clicked", () => {
    vi.mocked(useStudentProfile).mockReturnValue({
      data: { bulletins_status: "postponed" },
      isLoading: false,
    } as unknown as MockReturn);
    const onAddClick = vi.fn();

    wrap(<BulletinsMiniCTA context="graph" onAddClick={onAddClick} />);

    fireEvent.click(screen.getByRole("button", { name: /ajoute mes notes/i }));
    expect(onAddClick).toHaveBeenCalledOnce();
  });

  it("renders graph context variant copy", () => {
    vi.mocked(useStudentProfile).mockReturnValue({
      data: { bulletins_status: "postponed" },
      isLoading: false,
    } as unknown as MockReturn);

    wrap(<BulletinsMiniCTA context="graph" onAddClick={vi.fn()} />);

    expect(screen.getByText(/personnalis/i)).toBeInTheDocument();
  });

  it("has correct a11y attributes", () => {
    vi.mocked(useStudentProfile).mockReturnValue({
      data: { bulletins_status: "postponed" },
      isLoading: false,
    } as unknown as MockReturn);

    wrap(<BulletinsMiniCTA context="stat" onAddClick={vi.fn()} />);

    const aside = screen.getByRole("complementary");
    expect(aside).toHaveAttribute("aria-label");
  });

  it("does not contain forbidden words", () => {
    vi.mocked(useStudentProfile).mockReturnValue({
      data: { bulletins_status: "postponed" },
      isLoading: false,
    } as unknown as MockReturn);

    const { container } = wrap(
      <BulletinsMiniCTA context="graph" onAddClick={vi.fn()} />
    );

    const text = container.textContent?.toLowerCase() ?? "";
    const forbidden = ["incomplet", "débloque", "vraies stats", "profil dégradé", "%"];
    forbidden.forEach((w) => expect(text).not.toContain(w));
  });
});
