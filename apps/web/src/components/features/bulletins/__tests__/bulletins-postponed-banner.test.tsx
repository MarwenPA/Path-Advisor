import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, fireEvent } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { BulletinsPostponedBanner } from "../bulletins-postponed-banner";

vi.mock("../../../../hooks/use-student-profile", () => ({
  useStudentProfile: vi.fn(),
  useDismissBulletinsBanner: vi.fn(() => ({ mutate: vi.fn() })),
  isBannerVisible: vi.fn(),
}));

import {
  isBannerVisible,
  useStudentProfile,
  useDismissBulletinsBanner,
} from "../../../../hooks/use-student-profile";

type MockStudentProfile = ReturnType<typeof useStudentProfile>;
type MockDismissBanner = ReturnType<typeof useDismissBulletinsBanner>;

function wrap(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>);
}

const onAddClick = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();
});

describe("BulletinsPostponedBanner", () => {
  it("renders when bulletins_status is postponed and banner is not dismissed", () => {
    vi.mocked(useStudentProfile).mockReturnValue({
      data: {
        bulletins_status: "postponed",
        bulletins_postponed_at: "2026-06-01T10:00:00Z",
        bulletins_postponed_banner_dismissed_until: null,
      },
      isLoading: false,
      isError: false,
    } as unknown as MockStudentProfile);
    vi.mocked(isBannerVisible).mockReturnValue(true);

    wrap(<BulletinsPostponedBanner onAddClick={onAddClick} />);

    expect(
      screen.getByText(/ajouter tes bulletins/i)
    ).toBeInTheDocument();
  });

  it("does not render when bulletins_status is completed", () => {
    vi.mocked(useStudentProfile).mockReturnValue({
      data: {
        bulletins_status: "completed",
        bulletins_postponed_at: null,
        bulletins_postponed_banner_dismissed_until: null,
      },
      isLoading: false,
      isError: false,
    } as unknown as MockStudentProfile);
    vi.mocked(isBannerVisible).mockReturnValue(false);

    wrap(<BulletinsPostponedBanner onAddClick={onAddClick} />);

    expect(screen.queryByRole("complementary")).toBeNull();
  });

  it("does not render when banner is within dismiss TTL", () => {
    vi.mocked(useStudentProfile).mockReturnValue({
      data: {
        bulletins_status: "postponed",
        bulletins_postponed_at: "2026-06-01T10:00:00Z",
        bulletins_postponed_banner_dismissed_until: new Date(
          Date.now() + 86400000
        ).toISOString(),
      },
      isLoading: false,
      isError: false,
    } as unknown as MockStudentProfile);
    vi.mocked(isBannerVisible).mockReturnValue(false);

    wrap(<BulletinsPostponedBanner onAddClick={onAddClick} />);

    expect(screen.queryByRole("complementary")).toBeNull();
  });

  it("calls onAddClick when Ajouter button is clicked", () => {
    vi.mocked(useStudentProfile).mockReturnValue({
      data: {
        bulletins_status: "postponed",
        bulletins_postponed_at: "2026-06-01T10:00:00Z",
        bulletins_postponed_banner_dismissed_until: null,
      },
      isLoading: false,
      isError: false,
    } as unknown as MockStudentProfile);
    vi.mocked(isBannerVisible).mockReturnValue(true);

    wrap(<BulletinsPostponedBanner onAddClick={onAddClick} />);

    fireEvent.click(screen.getByRole("button", { name: /ajouter/i }));
    expect(onAddClick).toHaveBeenCalledOnce();
  });

  it("calls dismiss mutation when close button is clicked", () => {
    const mutateMock = vi.fn();
    vi.mocked(useDismissBulletinsBanner).mockReturnValue({
      mutate: mutateMock,
    } as unknown as MockDismissBanner);
    vi.mocked(useStudentProfile).mockReturnValue({
      data: {
        bulletins_status: "postponed",
        bulletins_postponed_at: "2026-06-01T10:00:00Z",
        bulletins_postponed_banner_dismissed_until: null,
      },
      isLoading: false,
      isError: false,
    } as unknown as MockStudentProfile);
    vi.mocked(isBannerVisible).mockReturnValue(true);

    wrap(<BulletinsPostponedBanner onAddClick={onAddClick} />);

    fireEvent.click(screen.getByRole("button", { name: /fermer|masquer|✕/i }));
    expect(mutateMock).toHaveBeenCalledOnce();
  });

  it("has correct a11y: role=complementary and aria-label", () => {
    vi.mocked(useStudentProfile).mockReturnValue({
      data: {
        bulletins_status: "postponed",
        bulletins_postponed_at: "2026-06-01T10:00:00Z",
        bulletins_postponed_banner_dismissed_until: null,
      },
      isLoading: false,
      isError: false,
    } as unknown as MockStudentProfile);
    vi.mocked(isBannerVisible).mockReturnValue(true);

    wrap(<BulletinsPostponedBanner onAddClick={onAddClick} />);

    const aside = screen.getByRole("complementary");
    expect(aside).toHaveAttribute("aria-label");
  });

  it("does not contain forbidden words (no stigma)", () => {
    vi.mocked(useStudentProfile).mockReturnValue({
      data: {
        bulletins_status: "postponed",
        bulletins_postponed_at: "2026-06-01T10:00:00Z",
        bulletins_postponed_banner_dismissed_until: null,
      },
      isLoading: false,
      isError: false,
    } as unknown as MockStudentProfile);
    vi.mocked(isBannerVisible).mockReturnValue(true);

    const { container } = wrap(
      <BulletinsPostponedBanner onAddClick={onAddClick} />
    );

    const text = container.textContent?.toLowerCase() ?? "";
    const forbidden = ["incomplet", "manque", "débloque", "profil dégradé", "%"];
    forbidden.forEach((word) => {
      expect(text).not.toContain(word);
    });
  });

  it("renders nothing while loading", () => {
    vi.mocked(useStudentProfile).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    } as unknown as MockStudentProfile);
    vi.mocked(isBannerVisible).mockReturnValue(false);

    wrap(<BulletinsPostponedBanner onAddClick={onAddClick} />);
    expect(screen.queryByRole("complementary")).toBeNull();
  });
});
