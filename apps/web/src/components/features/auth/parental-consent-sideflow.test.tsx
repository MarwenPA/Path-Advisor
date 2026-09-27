/**
 * ParentalConsentSideFlow — Story 10.6 instance contracts.
 *
 * Contracts: copy + CTA are keyed on `parental_consent_state` (resend only
 * where it can succeed), the 429 rate-limit is surfaced calmly, non-pending
 * users see nothing, and resolution (status flips to active on a refetch)
 * hides the banner and shows the confirmation toast.
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { beforeEach, describe, expect, it, vi } from "vitest";

import messages from "../../../../messages/fr.json";
import { ApiError } from "@/lib/api/client";
import type { CurrentUser } from "@/lib/api/auth";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));
const pushMock = vi.fn();

vi.mock("@/lib/api/auth", async () => ({
  ...(await vi.importActual<typeof import("@/lib/api/auth")>("@/lib/api/auth")),
  fetchCurrentUser: vi.fn(),
  resendParentalConsentEmail: vi.fn(),
}));

import { fetchCurrentUser, resendParentalConsentEmail } from "@/lib/api/auth";

import { ParentalConsentSideFlow } from "./parental-consent-sideflow";

const BASE_USER: CurrentUser = {
  id: "usr_1",
  email: "sarah@test.local",
  role: "student",
  status: "pending_parental_consent",
  is_fully_active: false,
  is_premium: false,
  mfa_required_by_role: false,
  mfa_enrolled: false,
  mfa_recovery_codes_remaining: 0,
  parental_consent_state: "pending",
};

function renderFlow() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const utils = render(
    <QueryClientProvider client={queryClient}>
      <NextIntlClientProvider locale="fr" messages={messages}>
        <ParentalConsentSideFlow />
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
  return { queryClient, ...utils };
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("ParentalConsentSideFlow", () => {
  it("shows the reassuring copy and the resend CTA while the parent is undecided", async () => {
    vi.mocked(fetchCurrentUser).mockResolvedValue(BASE_USER);
    vi.mocked(resendParentalConsentEmail).mockResolvedValue({ detail: "ok" });
    renderFlow();

    expect(
      await screen.findByText(
        "Ton parent reçoit l'email — tu peux continuer pendant qu'on vérifie.",
      ),
    ).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Relancer mon parent" }));
    expect(await screen.findByText("Email renvoyé à ton parent.")).toBeInTheDocument();
    expect(resendParentalConsentEmail).toHaveBeenCalledOnce();
  });

  it("surfaces the hourly rate limit calmly on 429", async () => {
    vi.mocked(fetchCurrentUser).mockResolvedValue(BASE_USER);
    vi.mocked(resendParentalConsentEmail).mockRejectedValue(
      new ApiError(429, "rate limited", {
        type: "about:blank",
        title: "Trop de requêtes",
        status: 429,
        detail: "Réessaie dans une heure.",
      }),
    );
    renderFlow();

    await userEvent.click(await screen.findByRole("button", { name: "Relancer mon parent" }));
    expect(
      await screen.findByText("Email déjà renvoyé récemment — réessaie dans une heure."),
    ).toBeInTheDocument();
  });

  it("switches to email-verification copy without resend when the parent already granted", async () => {
    vi.mocked(fetchCurrentUser).mockResolvedValue({
      ...BASE_USER,
      parental_consent_state: "granted",
    });
    renderFlow();

    expect(
      await screen.findByText(
        "Ton parent a validé ton inscription — il ne reste qu'à confirmer ton adresse email.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Relancer mon parent" })).not.toBeInTheDocument();
  });

  it("points to support when the consent window expired", async () => {
    vi.mocked(fetchCurrentUser).mockResolvedValue({
      ...BASE_USER,
      parental_consent_state: "expired",
    });
    renderFlow();

    await userEvent.click(await screen.findByRole("button", { name: "Contacter le support" }));
    expect(pushMock).toHaveBeenCalledWith("/support");
  });

  it("renders nothing for a fully active user", async () => {
    vi.mocked(fetchCurrentUser).mockResolvedValue({
      ...BASE_USER,
      status: "active",
      is_fully_active: true,
      parental_consent_state: null,
    });
    renderFlow();

    await waitFor(() => expect(fetchCurrentUser).toHaveBeenCalled());
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("hides the banner and confirms with a toast when the account becomes active", async () => {
    vi.mocked(fetchCurrentUser)
      .mockResolvedValueOnce(BASE_USER)
      .mockResolvedValue({
        ...BASE_USER,
        status: "active",
        is_fully_active: true,
        parental_consent_state: null,
      });
    const { queryClient } = renderFlow();

    expect(await screen.findByText(/Ton parent reçoit l'email/)).toBeInTheDocument();

    await queryClient.invalidateQueries({ queryKey: ["current-user"] });

    expect(
      await screen.findByText("Ton compte est entièrement actif maintenant."),
    ).toBeInTheDocument();
    expect(screen.queryByText(/Ton parent reçoit l'email/)).not.toBeInTheDocument();
  });
});
