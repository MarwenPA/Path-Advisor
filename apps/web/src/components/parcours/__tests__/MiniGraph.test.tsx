import { describe, it, expect } from "vitest";
import { render, container } from "@testing-library/react";
import { MiniGraph } from "../MiniGraph";
import type { ParcoursNode, ParcoursEdge } from "../types";

const nodes3: ParcoursNode[] = [
  { id: "n1", label: "Lycée", type: "start" },
  { id: "n2", label: "BTS", type: "intermediate" },
  { id: "n3", label: "IESEG", type: "target" },
];

const edges2: ParcoursEdge[] = [
  { source: "n1", target: "n2" },
  { source: "n2", target: "n3" },
];

describe("MiniGraph", () => {
  it("renders SVG with correct viewBox", () => {
    const { container } = render(<MiniGraph nodes={nodes3} edges={edges2} />);
    const svg = container.querySelector("svg");
    expect(svg).not.toBeNull();
    expect(svg?.getAttribute("viewBox")).toBe("0 0 200 60");
    expect(svg?.getAttribute("width")).toBe("200");
    expect(svg?.getAttribute("height")).toBe("60");
    expect(svg?.getAttribute("role")).toBe("img");
    expect(svg?.getAttribute("aria-label")).toContain("3");
  });

  it("renders circles for each node", () => {
    const { container } = render(<MiniGraph nodes={nodes3} edges={edges2} />);
    const circles = container.querySelectorAll("circle");
    expect(circles.length).toBe(3);
  });

  it("renders lines for each edge", () => {
    const { container } = render(<MiniGraph nodes={nodes3} edges={edges2} />);
    const lines = container.querySelectorAll("line");
    expect(lines.length).toBe(2);
  });

  it("target node has larger radius than other nodes", () => {
    const { container } = render(<MiniGraph nodes={nodes3} edges={edges2} />);
    const circles = container.querySelectorAll("circle");
    // nodes: start=6, intermediate=6, target=10
    const radii = Array.from(circles).map((c) => Number(c.getAttribute("r")));
    const targetRadius = radii[2]; // last node is target
    const otherRadii = radii.slice(0, 2);
    expect(targetRadius).toBe(10);
    otherRadii.forEach((r) => expect(r).toBe(6));
  });

  it("returns null when nodes empty", () => {
    const { container } = render(<MiniGraph nodes={[]} edges={[]} />);
    expect(container.querySelector("svg")).toBeNull();
  });
});
