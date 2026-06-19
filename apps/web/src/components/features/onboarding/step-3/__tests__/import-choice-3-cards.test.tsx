import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ImportChoice3Cards } from "../import-choice-3-cards";

describe("ImportChoice3Cards — AC1", () => {
  it("renders exactly 3 cards", () => {
    render(<ImportChoice3Cards onSelect={vi.fn()} />);
    const cards = screen.getAllByRole("button");
    expect(cards).toHaveLength(3);
  });

  it("no ribbon / no recommended badge on any card", () => {
    render(<ImportChoice3Cards onSelect={vi.fn()} />);
    expect(screen.queryByText(/recommand/i)).toBeNull();
    expect(screen.queryByText(/badge/i)).toBeNull();
  });

  it("calls onSelect with 'scan' when camera card clicked", async () => {
    const onSelect = vi.fn();
    render(<ImportChoice3Cards onSelect={onSelect} />);
    await userEvent.click(screen.getAllByRole("button")[0]);
    expect(onSelect).toHaveBeenCalledWith("scan");
  });

  it("calls onSelect with 'manual' when pen card clicked", async () => {
    const onSelect = vi.fn();
    render(<ImportChoice3Cards onSelect={onSelect} />);
    await userEvent.click(screen.getAllByRole("button")[1]);
    expect(onSelect).toHaveBeenCalledWith("manual");
  });

  it("calls onSelect with 'later' when arrow card clicked", async () => {
    const onSelect = vi.fn();
    render(<ImportChoice3Cards onSelect={onSelect} />);
    await userEvent.click(screen.getAllByRole("button")[2]);
    expect(onSelect).toHaveBeenCalledWith("later");
  });

  it("snapshot: 3 visually identical cards", () => {
    const { container } = render(<ImportChoice3Cards onSelect={vi.fn()} />);
    expect(container.firstChild).toMatchSnapshot();
  });
});
