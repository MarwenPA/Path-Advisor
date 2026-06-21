import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { GraphParcours } from "../GraphParcours";
import type { ParcoursNode, ParcoursEdge, AdmissionStatInline } from "../types";

// ─── Mock usePrefersReducedMotion ─────────────────────────────────────────────

vi.mock("@/hooks/use-prefers-reduced-motion", () => ({
  usePrefersReducedMotion: () => true,
}));

// ─── Fixtures ─────────────────────────────────────────────────────────────────

const nodes3: ParcoursNode[] = [
  { id: "n1", label: "Lycée Général", type: "start" },
  { id: "n2", label: "BTS NRC", type: "intermediate" },
  { id: "n3", label: "IESEG", type: "target" },
];

const edges2: ParcoursEdge[] = [
  { source: "n1", target: "n2", weight: 0.5 },
  { source: "n2", target: "n3", weight: 1 },
];

const admissionStat: AdmissionStatInline = {
  expected_proba: 62,
  label: "realiste",
};

const baseProps = {
  nodes: nodes3,
  edges: edges2,
  targetSchool: "IESEG",
  admissionStat,
  isFirstRender: false,
  parcoursId: "test-parcours-123",
};

// ─── Setup / teardown ─────────────────────────────────────────────────────────

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

// ─── Tests ────────────────────────────────────────────────────────────────────

describe("GraphParcours", () => {
  it("renders all nodes as SVG elements", () => {
    render(<GraphParcours {...baseProps} />);
    expect(screen.getByTestId("node-n1")).toBeDefined();
    expect(screen.getByTestId("node-n2")).toBeDefined();
    expect(screen.getByTestId("node-n3")).toBeDefined();
  });

  it("renders edges between nodes", () => {
    render(<GraphParcours {...baseProps} />);
    expect(screen.getByTestId("edge-0")).toBeDefined();
    expect(screen.getByTestId("edge-1")).toBeDefined();
  });

  it("shows table alternative when toggle clicked", () => {
    render(<GraphParcours {...baseProps} />);
    const btn = screen.getByTestId("toggle-view-btn");
    expect(btn.textContent).toBe("Vue tableau");
    fireEvent.click(btn);
    expect(screen.getByTestId("table-view").style.display).toBe("block");
    expect(btn.textContent).toBe("Vue graphe");
  });

  it("hides table and shows graph when toggle clicked again", () => {
    render(<GraphParcours {...baseProps} />);
    const btn = screen.getByTestId("toggle-view-btn");
    fireEvent.click(btn);
    fireEvent.click(btn);
    expect(screen.getByTestId("table-view").style.display).toBe("none");
    expect(screen.getByTestId("graph-svg").getAttribute("aria-hidden")).toBe("false");
    expect(btn.textContent).toBe("Vue tableau");
  });

  it("SVG has role=group and aria-labelledby pointing to title with school name", () => {
    render(<GraphParcours {...baseProps} />);
    const svg = screen.getByTestId("graph-svg");
    // role="group" (not "img") so keyboard users can reach child button nodes
    expect(svg.getAttribute("role")).toBe("group");
    const titleId = svg.getAttribute("aria-labelledby");
    expect(titleId).toBeTruthy();
    // The <title> element with that id should contain the school name and step count
    const titleEl = document.getElementById(titleId!);
    expect(titleEl?.textContent).toContain("IESEG");
    expect(titleEl?.textContent).toContain("3 étapes");
  });

  it("target node has larger radius than intermediate nodes", () => {
    render(<GraphParcours {...baseProps} />);
    const targetCircle = screen.getByTestId("circle-n3");
    const intermediateCircle = screen.getByTestId("circle-n2");
    const targetR = Number(targetCircle.getAttribute("data-node-r"));
    const intermediateR = Number(intermediateCircle.getAttribute("data-node-r"));
    expect(targetR).toBeGreaterThan(intermediateR);
  });

  it("nodes have tabIndex and aria-label", () => {
    render(<GraphParcours {...baseProps} />);
    const node1 = screen.getByTestId("node-n1");
    const node2 = screen.getByTestId("node-n2");
    const node3 = screen.getByTestId("node-n3");

    expect(node1.getAttribute("tabindex")).toBe("0");
    expect(node1.getAttribute("aria-label")).toBe("Lycée Général — étape 1 sur 3");

    expect(node2.getAttribute("tabindex")).toBe("0");
    expect(node2.getAttribute("aria-label")).toBe("BTS NRC — étape 2 sur 3");

    expect(node3.getAttribute("tabindex")).toBe("0");
    expect(node3.getAttribute("aria-label")).toBe("IESEG — étape 3 sur 3");
  });

  it("does not animate when isFirstRender=false", () => {
    render(<GraphParcours {...baseProps} isFirstRender={false} />);
    // With prefersReducedMotion=true (mocked) and isFirstRender=false,
    // all nodes are immediately visible (lazy initial state, no setTimeout)
    const node1 = screen.getByTestId("node-n1");
    expect(node1.style.opacity).toBe("1");
  });

  it("does not animate when prefers-reduced-motion is true", () => {
    // usePrefersReducedMotion is globally mocked to return true in this file
    render(<GraphParcours {...baseProps} isFirstRender={true} />);
    // All nodes should be immediately visible (no animation)
    const node1 = screen.getByTestId("node-n1");
    const node3 = screen.getByTestId("node-n3");
    expect(node1.style.opacity).toBe("1");
    expect(node3.style.opacity).toBe("1");
  });

  it("shows admission stat on target node when admissionStat provided", () => {
    render(<GraphParcours {...baseProps} admissionStat={admissionStat} />);
    expect(screen.getByTestId("stat-proba")).toBeDefined();
    expect(screen.getByTestId("stat-label")).toBeDefined();
    expect(screen.getByTestId("stat-label").textContent).toBe("Réaliste");
  });

  it("does not crash when admissionStat is null", () => {
    expect(() => render(<GraphParcours {...baseProps} admissionStat={null} />)).not.toThrow();
    expect(screen.queryByTestId("stat-proba")).toBeNull();
    expect(screen.queryByTestId("stat-label")).toBeNull();
  });
});
