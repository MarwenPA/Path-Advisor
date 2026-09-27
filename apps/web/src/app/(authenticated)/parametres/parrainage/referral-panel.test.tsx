/**
 * ReferralPanel — Story 10.5 contracts.
 *
 * Contracts: the opaque link renders with a sober count, native share is
 * used when available, the clipboard fallback fires otherwise (toast), and
 * a cancelled share stays silent.
 */
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api/auth", async () => ({
  ...(await vi.importActual<typeof import("@/lib/api/auth")>("@/lib/api/auth")),
  fetchReferralInfo: vi.fn(),
}));

import { fetchReferralInfo } from "@/lib/api/auth";

import { ReferralPanel } from "./referral-panel";

const INFO = { code: "aBc123Xy", url: "http://localhost:3000/r/aBc123Xy", referred_count: 0 };

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(fetchReferralInfo).mockResolvedValue(INFO);
});

describe("ReferralPanel", () => {
  it("renders the opaque link and the sober empty state", async () => {
    render(<ReferralPanel />);
    expect(await screen.findByText("http://localhost:3000/r/aBc123Xy")).toBeInTheDocument();
    expect(screen.getByText(/Personne n'a encore utilisé ton lien/)).toBeInTheDocument();
  });

  it("uses the native share sheet when available", async () => {
    const share = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { share });
    render(<ReferralPanel />);

    await userEvent.click(await screen.findByRole("button", { name: "Partager" }));
    await waitFor(() => expect(share).toHaveBeenCalledOnce());
    expect(share.mock.calls[0]?.[0]?.url).toBe(INFO.url);
    Reflect.deleteProperty(navigator, "share");
  });

  it("falls back to clipboard copy with a toast when share is unsupported", async () => {
    Reflect.deleteProperty(navigator, "share");
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    render(<ReferralPanel />);

    await userEvent.click(await screen.findByRole("button", { name: "Partager" }));
    await waitFor(() => expect(writeText).toHaveBeenCalledWith(INFO.url));
    expect(await screen.findByText(/Lien copié/)).toBeInTheDocument();
  });

  it("shows the count once someone joined", async () => {
    vi.mocked(fetchReferralInfo).mockResolvedValue({ ...INFO, referred_count: 3 });
    render(<ReferralPanel />);
    expect(
      await screen.findByText("3 pote(s) ont rejoint Path-Advisor grâce à toi."),
    ).toBeInTheDocument();
  });
});
