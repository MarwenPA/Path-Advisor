import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { GracefulFallback, type GracefulFallbackProps } from "./graceful-fallback";
import { setAnalyticsTracker, type AnalyticsEvent } from "@/lib/analytics/events";

const baseProps: GracefulFallbackProps = {
  title: "Ton bulletin a un format qu'on connaît pas encore",
  description:
    "Pas grave. Saisis-le à la main — 5 champs et c'est bon. Tu pourras retenter avec une photo plus nette si tu veux.",
  context: "ocr",
  primaryAction: { label: "Saisir à la main", onClick: vi.fn(), icon: "arrow-right" },
  secondaryAction: { label: "Réessayer avec une autre photo", onClick: vi.fn(), icon: "rotate" },
};

describe("GracefulFallback", () => {
  let events: AnalyticsEvent[];

  beforeEach(() => {
    events = [];
    setAnalyticsTracker((event) => events.push(event));
  });

  afterEach(() => {
    setAnalyticsTracker(null);
  });

  it("renders title, description and both CTAs with their labels", () => {
    render(<GracefulFallback {...baseProps} />);
    expect(screen.getByRole("heading", { name: baseProps.title })).toBeInTheDocument();
    expect(screen.getByText(baseProps.description)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Saisir à la main/ })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Réessayer avec une autre photo/ }),
    ).toBeInTheDocument();
  });

  it("wires the title to the region via aria-labelledby", () => {
    render(<GracefulFallback {...baseProps} />);
    const region = screen.getByRole("region");
    const heading = screen.getByRole("heading", { name: baseProps.title });
    expect(region.getAttribute("aria-labelledby")).toBe(heading.id);
  });

  it("groups the CTAs and exposes the right SR label", () => {
    render(<GracefulFallback {...baseProps} />);
    const group = screen.getByRole("group", { name: "Options disponibles" });
    expect(group).toBeInTheDocument();
  });

  it("renders the context-specific illustration icon", () => {
    render(<GracefulFallback {...baseProps} context="network" />);
    expect(screen.getByTestId("fallback-icon-network")).toBeInTheDocument();
  });

  it("enforces strict shape equivalence between primary and secondary buttons (anti-dark-pattern)", () => {
    render(<GracefulFallback {...baseProps} />);
    const primary = document.querySelector<HTMLButtonElement>('[data-action="primary"]')!;
    const secondary = document.querySelector<HTMLButtonElement>('[data-action="secondary"]')!;
    for (const klass of ["h-12", "px-4", "font-medium", "text-base", "rounded-md"]) {
      expect(primary.className).toContain(klass);
      expect(secondary.className).toContain(klass);
    }
  });

  it("omits the tertiary slot entirely when `tertiaryLink` is undefined", () => {
    render(<GracefulFallback {...baseProps} />);
    expect(document.querySelector('[data-action="tertiary"]')).toBeNull();
    expect(screen.getAllByRole("button")).toHaveLength(2);
  });

  it("renders the tertiary link when provided and emits its analytics event on click", () => {
    const tertiaryOnClick = vi.fn();
    render(
      <GracefulFallback
        {...baseProps}
        tertiaryLink={{ label: "Plus tard", onClick: tertiaryOnClick }}
      />,
    );
    const tertiary = screen.getByRole("button", { name: "Plus tard" });
    fireEvent.click(tertiary);
    expect(tertiaryOnClick).toHaveBeenCalledOnce();
    const tertiaryEvents = events.filter(
      (e) => e.name === "graceful_fallback_tertiary_clicked",
    );
    expect(tertiaryEvents).toHaveLength(1);
    expect(tertiaryEvents[0]).toMatchObject({ context: "ocr", tertiary_label: "Plus tard" });
  });

  it("emits `graceful_fallback_shown` once on mount with the correct has_tertiary flag", () => {
    render(<GracefulFallback {...baseProps} />);
    const shown = events.filter((e) => e.name === "graceful_fallback_shown");
    expect(shown).toHaveLength(1);
    expect(shown[0]).toMatchObject({ context: "ocr", has_tertiary: false });
  });

  it("emits primary and secondary click events with the right labels", () => {
    const primaryClick = vi.fn();
    const secondaryClick = vi.fn();
    render(
      <GracefulFallback
        {...baseProps}
        primaryAction={{ ...baseProps.primaryAction, onClick: primaryClick }}
        secondaryAction={{ ...baseProps.secondaryAction, onClick: secondaryClick }}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /Saisir à la main/ }));
    expect(primaryClick).toHaveBeenCalledOnce();
    fireEvent.click(screen.getByRole("button", { name: /Réessayer avec une autre photo/ }));
    expect(secondaryClick).toHaveBeenCalledOnce();

    const names = events.map((e) => e.name);
    expect(names).toContain("graceful_fallback_primary_clicked");
    expect(names).toContain("graceful_fallback_secondary_clicked");
  });

  it("replaces the icon with a spinner and ignores the click when isSubmitting is true", () => {
    const primaryClick = vi.fn();
    render(
      <GracefulFallback
        {...baseProps}
        primaryAction={{ ...baseProps.primaryAction, onClick: primaryClick, isSubmitting: true }}
      />,
    );
    const primary = screen.getByRole("button", { name: /Saisir à la main/ });
    expect(primary).toHaveAttribute("aria-busy", "true");
    expect(primary.className).toContain("cursor-wait");
    fireEvent.click(primary);
    expect(primaryClick).not.toHaveBeenCalled();
    expect(
      events.filter((e) => e.name === "graceful_fallback_primary_clicked"),
    ).toHaveLength(0);
  });

  it("disables click and emits no event when isDisabled is true", () => {
    const primaryClick = vi.fn();
    render(
      <GracefulFallback
        {...baseProps}
        primaryAction={{ ...baseProps.primaryAction, onClick: primaryClick, isDisabled: true }}
      />,
    );
    const primary = screen.getByRole("button", { name: /Saisir à la main/ });
    expect(primary).toBeDisabled();
    fireEvent.click(primary);
    expect(primaryClick).not.toHaveBeenCalled();
  });

  it("warns in dev when the title starts with `Tu `", () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    render(<GracefulFallback {...baseProps} title="Tu as téléchargé un mauvais fichier" />);
    expect(warn).toHaveBeenCalled();
    expect(warn.mock.calls[0]?.[0]).toContain("agentivité utilisateur");
    warn.mockRestore();
  });

  it("warns in dev when the title contains a forbidden word", () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    render(<GracefulFallback {...baseProps} title="Une erreur est survenue" />);
    expect(warn).toHaveBeenCalled();
    expect(warn.mock.calls[0]?.[0]).toContain("mot proscrit");
    warn.mockRestore();
  });

  it("places initial focus on the primary button when the page has no other focus", () => {
    render(<GracefulFallback {...baseProps} />);
    expect(document.activeElement).toBe(
      screen.getByRole("button", { name: /Saisir à la main/ }),
    );
  });

  it("does not steal focus when the caller has already placed it elsewhere", () => {
    const input = document.createElement("input");
    document.body.appendChild(input);
    input.focus();
    render(<GracefulFallback {...baseProps} />);
    expect(document.activeElement).toBe(input);
    input.remove();
  });
});
