/**
 * Tests for FavoriteButton component — Story 4.8.
 *
 * The useFavoriteSchool hook is mocked so tests don't fire real HTTP requests.
 * We test the rendered output and ARIA attributes in both favorited and
 * unfavorited states.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { FavoriteButton } from "../FavoriteButton";

// ---------------------------------------------------------------------------
// Mock the hook so tests stay synchronous and don't call the API
// ---------------------------------------------------------------------------

const mockToggle = vi.fn();
let mockFavorited = false;
let mockIsPending = false;

vi.mock("@/hooks/use-favorite-school", () => ({
  useFavoriteSchool: (_slug: string, initialFavorited = false) => {
    return {
      favorited: mockFavorited !== false ? mockFavorited : initialFavorited,
      toggle: mockToggle,
      isPending: mockIsPending,
    };
  },
}));

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("FavoriteButton", () => {
  beforeEach(() => {
    mockToggle.mockClear();
    mockFavorited = false;
    mockIsPending = false;
  });

  it("renders heart icon in unfavorited state", () => {
    render(<FavoriteButton schoolSlug="ifsi-paris" initialFavorited={false} />);
    // Unfavorited uses the outline heart character
    expect(screen.getByRole("button")).toHaveTextContent("♡");
  });

  it("has aria-pressed=false initially", () => {
    render(<FavoriteButton schoolSlug="ifsi-paris" initialFavorited={false} />);
    expect(screen.getByRole("button")).toHaveAttribute("aria-pressed", "false");
  });

  it("has aria-label 'Ajouter a mes paris' when unfavorited", () => {
    render(<FavoriteButton schoolSlug="ifsi-paris" initialFavorited={false} />);
    expect(screen.getByRole("button")).toHaveAttribute("aria-label", "Ajouter a mes paris");
  });

  it("renders filled heart and aria-pressed=true when favorited", () => {
    mockFavorited = true;
    render(<FavoriteButton schoolSlug="ifsi-paris" initialFavorited={true} />);
    const btn = screen.getByRole("button");
    expect(btn).toHaveTextContent("♥");
    expect(btn).toHaveAttribute("aria-pressed", "true");
  });

  it("has aria-label 'Retirer de mes paris' when favorited", () => {
    mockFavorited = true;
    render(<FavoriteButton schoolSlug="ifsi-paris" initialFavorited={true} />);
    expect(screen.getByRole("button")).toHaveAttribute("aria-label", "Retirer de mes paris");
  });

  it("calls toggle on click", () => {
    render(<FavoriteButton schoolSlug="ifsi-paris" />);
    fireEvent.click(screen.getByRole("button"));
    expect(mockToggle).toHaveBeenCalledOnce();
  });

  it("is disabled when isPending=true", () => {
    mockIsPending = true;
    render(<FavoriteButton schoolSlug="ifsi-paris" />);
    expect(screen.getByRole("button")).toBeDisabled();
  });
});
