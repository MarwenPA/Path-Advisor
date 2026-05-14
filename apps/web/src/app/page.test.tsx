import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import Home from "./page";

describe("Home page", () => {
  it("renders the foundation seed greeting", () => {
    render(<Home />);
    expect(screen.getByRole("heading", { name: /hello path-advisor/i })).toBeInTheDocument();
  });
});
