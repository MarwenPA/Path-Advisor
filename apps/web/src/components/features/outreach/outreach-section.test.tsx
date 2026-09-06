/**
 * <OutreachSection> tests — Story 5.4 §AC1/AC3.
 */
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

const fetchCurrentUserMock = vi.fn();
vi.mock("@/lib/api/auth", () => ({
  fetchCurrentUser: () => fetchCurrentUserMock(),
}));

const fetchQuotaMock = vi.fn();
vi.mock("@/lib/api/outreach", () => ({
  fetchOutreachQuota: () => fetchQuotaMock(),
}));

const fetchRecommendationsMock = vi.fn();
vi.mock("@/lib/api/recommendations", () => ({
  fetchRecommendations: () => fetchRecommendationsMock(),
}));

vi.mock("./send-outreach-button", () => ({
  SendOutreachButton: ({ schoolName }: { schoolName: string }) => (
    <button type="button">Envoyer à {schoolName}</button>
  ),
}));

import { OutreachSection } from "./outreach-section";

beforeEach(() => {
  fetchCurrentUserMock.mockReset();
  fetchQuotaMock.mockReset();
  fetchRecommendationsMock.mockReset();
});

describe("OutreachSection", () => {
  it("shows the PaywallContextuel trigger for a freemium student", async () => {
    fetchCurrentUserMock.mockResolvedValue({ id: "u1", is_premium: false });

    render(<OutreachSection schoolSlug="ecole-test" schoolName="École Test" />);

    expect(await screen.findByRole("button", { name: /passe en premium/i })).toBeInTheDocument();
  });

  it("shows the send button for a premium student with quota remaining and recommendations", async () => {
    fetchCurrentUserMock.mockResolvedValue({ id: "u1", is_premium: true });
    fetchQuotaMock.mockResolvedValue({ used: 1, limit: 5, remaining: 4 });
    fetchRecommendationsMock.mockResolvedValue({
      results: [{ id: "prof_01", name: "Infirmier" }],
      computed_at: "",
    });

    render(<OutreachSection schoolSlug="ecole-test" schoolName="École Test" />);

    expect(
      await screen.findByRole("button", { name: /envoyer à école test/i }),
    ).toBeInTheDocument();
  });

  it("shows the non-scary quota-exhausted message instead of the button", async () => {
    fetchCurrentUserMock.mockResolvedValue({ id: "u1", is_premium: true });
    fetchQuotaMock.mockResolvedValue({ used: 5, limit: 5, remaining: 0 });
    fetchRecommendationsMock.mockResolvedValue({ results: [], computed_at: "" });

    render(<OutreachSection schoolSlug="ecole-test" schoolName="École Test" />);

    await waitFor(() =>
      expect(screen.getByText(/tu as utilisé tes 5 envois ce mois/i)).toBeInTheDocument(),
    );
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("renders nothing while loading or on fetch failure", async () => {
    fetchCurrentUserMock.mockRejectedValue(new Error("network down"));

    const { container } = render(
      <OutreachSection schoolSlug="ecole-test" schoolName="École Test" />,
    );

    await waitFor(() => expect(container).toBeEmptyDOMElement());
  });
});
