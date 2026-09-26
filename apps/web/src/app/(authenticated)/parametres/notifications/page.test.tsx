/**
 * /parametres/notifications page tests — Story 8.2 §AC1.
 *
 * Category labels in the fixture stand in for the backend's French labels
 * (`NotificationCategory.choices`) — the page displays them as-is, they are
 * NOT keys in `messages/fr.json`.
 */
import { fireEvent, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { renderWithIntl } from "@/test/render-with-intl";

vi.mock("next-intl/server", () => import("@/test/next-intl-server-mock"));

const fetchPreferencesMock = vi.fn();
const updatePreferenceMock = vi.fn();
vi.mock("@/lib/api/notifications", () => ({
  fetchNotificationPreferences: () => fetchPreferencesMock(),
  updateNotificationPreference: (category: string, enabled: boolean) =>
    updatePreferenceMock(category, enabled),
}));

import NotificationsPage from "./page";

const PREFERENCES = [
  { category: "parcoursup_calendar", label: "Calendrier Parcoursup", enabled: true },
  { category: "school_responses", label: "Réponses des écoles", enabled: true },
  { category: "new_schools", label: "Nouvelles écoles", enabled: false },
  { category: "profile_completion", label: "Complétion du profil", enabled: true },
];

beforeEach(() => {
  vi.clearAllMocks();
  fetchPreferencesMock.mockResolvedValue({ preferences: PREFERENCES });
});

describe("NotificationsPage", () => {
  it("renders one labelled toggle per category from the GET payload", async () => {
    renderWithIntl(await NotificationsPage());

    expect(screen.getByRole("heading", { level: 1, name: "Notifications" })).toBeInTheDocument();
    expect(screen.getAllByRole("switch")).toHaveLength(4);
    // Real <label htmlFor> association — the accessible name IS the API label.
    expect(screen.getByRole("switch", { name: "Calendrier Parcoursup" })).toBeChecked();
    expect(screen.getByRole("switch", { name: "Réponses des écoles" })).toBeChecked();
    expect(screen.getByRole("switch", { name: "Nouvelles écoles" })).not.toBeChecked();
    expect(screen.getByRole("switch", { name: "Complétion du profil" })).toBeChecked();
    // RGAA — state is also carried by visible text, not colour alone.
    expect(screen.getAllByText("Activé")).toHaveLength(3);
    expect(screen.getAllByText("Désactivé")).toHaveLength(1);
  });

  it("fires the PUT on toggle (immediate save, no save button) and keeps the new state", async () => {
    updatePreferenceMock.mockResolvedValue({ category: "parcoursup_calendar", enabled: false });
    renderWithIntl(await NotificationsPage());

    const toggle = screen.getByRole("switch", { name: "Calendrier Parcoursup" });
    fireEvent.click(toggle);

    // Optimistic flip + per-row pending state while the PUT is in flight.
    expect(toggle).not.toBeChecked();
    expect(toggle).toBeDisabled();
    expect(screen.getByText("Enregistrement…")).toBeInTheDocument();

    expect(updatePreferenceMock).toHaveBeenCalledTimes(1);
    expect(updatePreferenceMock).toHaveBeenCalledWith("parcoursup_calendar", false);

    await waitFor(() => expect(toggle).toBeEnabled());
    expect(toggle).not.toBeChecked();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    // No page-wide save button anywhere (AC1 — saves per change).
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("reverts the toggle and says so when the PUT fails", async () => {
    updatePreferenceMock.mockRejectedValue(new Error("network down"));
    renderWithIntl(await NotificationsPage());

    const toggle = screen.getByRole("switch", { name: "Réponses des écoles" });
    fireEvent.click(toggle);
    expect(toggle).not.toBeChecked(); // optimistic flip…

    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
    expect(toggle).toBeChecked(); // …reverted after the failure
    expect(toggle).toBeEnabled();
    expect(screen.getByRole("alert")).toHaveTextContent(/n'a pas pu être enregistré/);
    // The failing row's switch points at the error message (screen readers).
    expect(toggle).toHaveAttribute("aria-describedby", "notification-school_responses-error");
  });
});
