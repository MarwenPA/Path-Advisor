/**
 * /desinscription/[token] page tests — Story 8.2 §AC3.
 *
 * The first test pins the page's core safety property: NO unsubscribe POST
 * on page load/mount — email-client prefetchers follow links, so rendering
 * the page must never mutate. The POST fires only on the confirm click.
 */
import { fireEvent, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api/client";
import { renderWithIntl } from "@/test/render-with-intl";

vi.mock("next-intl/server", () => import("@/test/next-intl-server-mock"));

const unsubscribeMock = vi.fn();
vi.mock("@/lib/api/notifications", () => ({
  unsubscribeByToken: (token: string) => unsubscribeMock(token),
}));

import DesinscriptionPage from "./page";

async function renderPage(token = "tok-123") {
  return renderWithIntl(await DesinscriptionPage({ params: Promise.resolve({ token }) }));
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("DesinscriptionPage", () => {
  it("never fires the unsubscribe POST on mount — it only explains and offers a button", async () => {
    await renderPage();

    expect(
      screen.getByRole("heading", { level: 1, name: "Se désinscrire de ces emails" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/en confirmant, tu ne recevras plus/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Confirmer la désinscription" })).toBeInTheDocument();
    // The safety property itself: rendering ≠ unsubscribing.
    expect(unsubscribeMock).not.toHaveBeenCalled();
  });

  it("POSTs the token on confirm click and shows the success state with the category label", async () => {
    unsubscribeMock.mockResolvedValue({ category: "new_schools", label: "Nouvelles écoles" });
    await renderPage("tok-abc");

    fireEvent.click(screen.getByRole("button", { name: "Confirmer la désinscription" }));

    expect(unsubscribeMock).toHaveBeenCalledTimes(1);
    expect(unsubscribeMock).toHaveBeenCalledWith("tok-abc");

    await waitFor(() => expect(screen.getByRole("status")).toBeInTheDocument());
    // Success shows the API-provided category label…
    expect(screen.getByRole("status")).toHaveTextContent("Nouvelles écoles");
    // …and the link to the settings page, mentioning login is needed.
    expect(screen.getByRole("link", { name: "tes paramètres de notifications" })).toHaveAttribute(
      "href",
      "/parametres/notifications",
    );
    expect(screen.getByText(/connexion requise/i)).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("shows a clear terminal error state on a 400 (invalid/tampered token)", async () => {
    unsubscribeMock.mockRejectedValue(new ApiError(400, "Lien de désinscription invalide."));
    await renderPage();

    fireEvent.click(screen.getByRole("button", { name: "Confirmer la désinscription" }));

    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
    expect(screen.getByRole("alert")).toHaveTextContent("Lien de désinscription invalide");
    // Terminal state: no button left to re-POST a bad token.
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("keeps the confirm button retryable on a transient failure (non-400)", async () => {
    unsubscribeMock.mockRejectedValue(new ApiError(503, "Service indisponible"));
    await renderPage();

    fireEvent.click(screen.getByRole("button", { name: "Confirmer la désinscription" }));

    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
    expect(screen.getByRole("alert")).toHaveTextContent(/réessaie/i);
    expect(screen.getByRole("button", { name: "Confirmer la désinscription" })).toBeEnabled();
  });
});
