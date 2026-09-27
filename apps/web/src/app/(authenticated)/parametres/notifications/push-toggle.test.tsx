/**
 * PushToggle — Story 10.2 contracts.
 *
 * Contracts: hidden when the browser can't push OR the server has no VAPID
 * key (graceful degradation — never an error state for an absent feature);
 * off→on subscribes; a denied permission lands back on off with calm copy;
 * on→off revokes; a failure reverts with a visible alert.
 */
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { beforeEach, describe, expect, it, vi } from "vitest";

import messages from "../../../../../messages/fr.json";

vi.mock("@/lib/api/notifications", async () => ({
  ...(await vi.importActual<typeof import("@/lib/api/notifications")>("@/lib/api/notifications")),
  fetchVapidPublicKey: vi.fn(),
}));
vi.mock("@/lib/push", () => ({
  isPushSupported: vi.fn(),
  getPushSubscription: vi.fn(),
  enablePush: vi.fn(),
  disablePush: vi.fn(),
}));

import { fetchVapidPublicKey } from "@/lib/api/notifications";
import { disablePush, enablePush, getPushSubscription, isPushSupported } from "@/lib/push";

import { PushToggle } from "./push-toggle";

function renderToggle() {
  return render(
    <NextIntlClientProvider locale="fr" messages={messages}>
      <PushToggle />
    </NextIntlClientProvider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(isPushSupported).mockReturnValue(true);
  vi.mocked(fetchVapidPublicKey).mockResolvedValue("BFakeKey");
  vi.mocked(getPushSubscription).mockResolvedValue(null);
});

describe("PushToggle", () => {
  it("renders nothing when the browser does not support push", async () => {
    vi.mocked(isPushSupported).mockReturnValue(false);
    const { container } = renderToggle();
    await waitFor(() => expect(container).toBeEmptyDOMElement());
  });

  it("renders nothing when the server has no VAPID config", async () => {
    vi.mocked(fetchVapidPublicKey).mockResolvedValue(null);
    const { container } = renderToggle();
    await waitFor(() => expect(fetchVapidPublicKey).toHaveBeenCalled());
    expect(container).toBeEmptyDOMElement();
  });

  it("subscribes on toggle-on and shows the enabled state", async () => {
    vi.mocked(enablePush).mockResolvedValue("subscribed");
    renderToggle();

    const toggle = await screen.findByRole("switch", {
      name: "Notifications push sur cet appareil",
    });
    expect(toggle).not.toBeChecked();
    await userEvent.click(toggle);

    await waitFor(() => expect(enablePush).toHaveBeenCalledOnce());
    expect(toggle).toBeChecked();
  });

  it("lands back on off with calm copy when permission is denied", async () => {
    vi.mocked(enablePush).mockResolvedValue("denied");
    renderToggle();

    await userEvent.click(
      await screen.findByRole("switch", { name: "Notifications push sur cet appareil" }),
    );

    expect(await screen.findByText(/Ton navigateur bloque les notifications/)).toBeInTheDocument();
    expect(
      screen.getByRole("switch", { name: "Notifications push sur cet appareil" }),
    ).not.toBeChecked();
  });

  it("revokes on toggle-off", async () => {
    vi.mocked(getPushSubscription).mockResolvedValue({} as PushSubscription);
    vi.mocked(disablePush).mockResolvedValue();
    renderToggle();

    const toggle = await screen.findByRole("switch", {
      name: "Notifications push sur cet appareil",
    });
    expect(toggle).toBeChecked();
    await userEvent.click(toggle);

    await waitFor(() => expect(disablePush).toHaveBeenCalledOnce());
    expect(toggle).not.toBeChecked();
  });

  it("reverts with a visible alert when the call fails", async () => {
    vi.mocked(enablePush).mockRejectedValue(new Error("réseau"));
    renderToggle();

    await userEvent.click(
      await screen.findByRole("switch", { name: "Notifications push sur cet appareil" }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(/n'a pas abouti/);
    expect(
      screen.getByRole("switch", { name: "Notifications push sur cet appareil" }),
    ).not.toBeChecked();
  });
});
