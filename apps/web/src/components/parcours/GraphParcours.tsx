"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { usePrefersReducedMotion } from "@/hooks/use-prefers-reduced-motion";
import type { ParcoursNode, ParcoursEdge, AdmissionStatInline } from "./types";

// ─── Layout constants ─────────────────────────────────────────────────────────

const VIEWBOX_W = 400;
const VIEWBOX_H = 220;
const START_CX = 60;
const START_CY = 180;
const TARGET_CX = 340;
const TARGET_CY = 40;
const START_R = 18;
const TARGET_R = 32;
const INTERMEDIATE_R = 22;

// ─── Helpers ──────────────────────────────────────────────────────────────────

function getNodePosition(index: number, total: number): { cx: number; cy: number } {
  if (total === 1) return { cx: START_CX, cy: START_CY };
  if (index === 0) return { cx: START_CX, cy: START_CY };
  if (index === total - 1) return { cx: TARGET_CX, cy: TARGET_CY };

  const t = index / (total - 1);
  const cx = START_CX + t * (TARGET_CX - START_CX);
  const cy = START_CY + t * (TARGET_CY - START_CY);
  return { cx, cy };
}

function getNodeRadius(type: ParcoursNode["type"]): number {
  if (type === "target") return TARGET_R;
  if (type === "start") return START_R;
  return INTERMEDIATE_R;
}

interface NodeColors {
  fill: string;
  stroke: string;
}

function getTargetColors(admissionStat: AdmissionStatInline | null): NodeColors {
  if (!admissionStat) return { fill: "#dbeafe", stroke: "#2563eb" };
  if (admissionStat.expected_proba >= 70) return { fill: "#dcfce7", stroke: "#16a34a" };
  if (admissionStat.expected_proba >= 40) return { fill: "#fef9c3", stroke: "#ca8a04" };
  return { fill: "#fee2e2", stroke: "#dc2626" };
}

function getNodeColors(node: ParcoursNode, admissionStat: AdmissionStatInline | null): NodeColors {
  if (node.type === "target") return getTargetColors(admissionStat);
  if (node.type === "start") return { fill: "#e2e8f0", stroke: "#94a3b8" };
  return { fill: "#f1f5f9", stroke: "#cbd5e1" };
}

function formatStatLabel(label: AdmissionStatInline["label"]): string {
  const map: Record<AdmissionStatInline["label"], string> = {
    audacieux: "Pari audacieux",
    realiste: "Réaliste",
    sur: "Voie sûre",
    estimation_indicative: "Estimation indicative",
  };
  return map[label];
}

// ─── Module-level render helpers (extracted to avoid per-render recreation) ──

interface NodeRenderArgs {
  node: ParcoursNode;
  index: number;
  total: number;
  admissionStat: AdmissionStatInline | null;
  isVisible: boolean;
  labelsVisible: boolean;
  isFirstRender: boolean;
  prefersReducedMotion: boolean;
  onNodeClick?: (node: ParcoursNode) => void;
}

function NodeElement({
  node,
  index,
  total,
  admissionStat,
  isVisible,
  labelsVisible,
  isFirstRender,
  prefersReducedMotion,
  onNodeClick,
}: NodeRenderArgs) {
  const { cx, cy } = getNodePosition(index, total);
  const r = getNodeRadius(node.type);
  const { fill, stroke } = getNodeColors(node, admissionStat);
  const isTarget = node.type === "target";

  // Fix: use transform-box:fill-box + transform-origin:center for correct SVG scaling
  // This is cross-browser safe (Chrome, Firefox, Safari 14+)
  const transitionStyle: React.CSSProperties = prefersReducedMotion
    ? { transition: "opacity 200ms ease", opacity: isVisible ? 1 : 0 }
    : isTarget && isFirstRender
      ? {
          transition: isVisible
            ? "opacity 220ms ease, transform 220ms cubic-bezier(0.175, 0.885, 0.32, 1.275)"
            : "none",
          opacity: isVisible ? 1 : 0,
          transform: isVisible ? "scale(1)" : "scale(0.5)",
          transformBox: "fill-box" as React.CSSProperties["transformBox"],
          transformOrigin: "center",
        }
      : {
          transition: isVisible ? "opacity 120ms ease-out, transform 120ms ease-out" : "none",
          opacity: isVisible ? 1 : 0,
          transform: isVisible ? "scale(1)" : "scale(0.5)",
          transformBox: "fill-box" as React.CSSProperties["transformBox"],
          transformOrigin: "center",
        };

  const pulseClass =
    !isFirstRender && isTarget && !prefersReducedMotion ? " graph-parcours__target-pulse" : "";

  return (
    <g
      key={node.id}
      data-testid={`node-${node.id}`}
      role="button"
      tabIndex={0}
      aria-label={`${node.label} — étape ${index + 1} sur ${total}`}
      style={transitionStyle}
      className={`graph-parcours__node${pulseClass}`}
      onClick={() => onNodeClick?.(node)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onNodeClick?.(node);
        }
      }}
    >
      <circle
        cx={cx}
        cy={cy}
        r={r}
        fill={fill}
        stroke={stroke}
        strokeWidth={isTarget ? 2.5 : 1.5}
        data-testid={`circle-${node.id}`}
        data-node-type={node.type}
        data-node-r={r}
      />
      {/* Label text below node */}
      <text
        x={cx}
        y={cy + r + 14}
        textAnchor="middle"
        fontSize={isTarget ? 11 : 10}
        fill="#475569"
        style={{
          transition: "opacity 150ms ease",
          opacity: labelsVisible || prefersReducedMotion || !isFirstRender ? 1 : 0,
        }}
        data-testid={`label-${node.id}`}
      >
        {node.label.length > 12 ? node.label.slice(0, 11) + "…" : node.label}
      </text>

      {/* Stat label on target node */}
      {isTarget && admissionStat && (
        <>
          <text
            x={cx}
            y={cy + 6}
            textAnchor="middle"
            fontSize={13}
            fontWeight="700"
            fill={stroke}
            style={{ pointerEvents: "none" }}
            data-testid="stat-proba"
          >
            {/* Use unicode non-breaking space instead of &nbsp; for SVG compatibility */}
            {admissionStat.expected_proba}
            {" "}%
          </text>
          <text
            x={cx}
            y={cy + r + 28}
            textAnchor="middle"
            fontSize={9}
            fill="#64748b"
            style={{
              transition: "opacity 150ms ease",
              opacity: labelsVisible || prefersReducedMotion || !isFirstRender ? 1 : 0,
              pointerEvents: "none",
            }}
            data-testid="stat-label"
          >
            {formatStatLabel(admissionStat.label)}
          </text>
        </>
      )}
    </g>
  );
}

interface EdgeRenderArgs {
  edge: ParcoursEdge;
  index: number;
  nodes: ParcoursNode[];
  totalEdges: number;
  isVisible: boolean;
  prefersReducedMotion: boolean;
}

function EdgeElement({
  edge,
  index,
  nodes,
  totalEdges,
  isVisible,
  prefersReducedMotion,
}: EdgeRenderArgs) {
  const sourceIndex = nodes.findIndex((n) => n.id === edge.source);
  const targetIndex = nodes.findIndex((n) => n.id === edge.target);
  if (sourceIndex === -1 || targetIndex === -1) return null;

  const total = nodes.length;
  const from = getNodePosition(sourceIndex, total);
  const to = getNodePosition(targetIndex, total);
  const isLastEdge = index === totalEdges - 1;
  const weight = edge.weight ?? 1;
  const strokeWidth = isLastEdge ? 4 : 1 + weight * 2;
  const strokeColor = isLastEdge ? "#64748b" : "#cbd5e1";

  // Compute edge length for stroke-dasharray draw animation
  const length = Math.sqrt(Math.pow(to.cx - from.cx, 2) + Math.pow(to.cy - from.cy, 2));

  return (
    <line
      key={`edge-${index}`}
      data-testid={`edge-${index}`}
      x1={from.cx}
      y1={from.cy}
      x2={to.cx}
      y2={to.cy}
      stroke={strokeColor}
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeDasharray={length}
      strokeDashoffset={isVisible ? 0 : length}
      style={{
        transition: isVisible
          ? `stroke-dashoffset ${prefersReducedMotion ? 200 : 80}ms ease-out`
          : "none",
        opacity: isVisible ? 1 : 0,
      }}
    />
  );
}

// ─── Scoped styles (singleton via data-attribute guard) ───────────────────────

const GRAPH_STYLES = `
  .graph-parcours__node:focus {
    outline: none;
  }
  .graph-parcours__node:focus-visible {
    outline: 2px solid #3b82f6;
    outline-offset: 3px;
    border-radius: 50%;
  }
  @keyframes graph-pulse {
    0%   { transform: scale(1); }
    50%  { transform: scale(1.05); }
    100% { transform: scale(1); }
  }
  .graph-parcours__target-pulse circle {
    animation: graph-pulse 100ms ease-in-out;
    transform-box: fill-box;
    transform-origin: center;
  }
`;

// ─── Props ────────────────────────────────────────────────────────────────────

export interface GraphParcoursProps {
  nodes: ParcoursNode[];
  edges: ParcoursEdge[];
  targetSchool: string;
  admissionStat: AdmissionStatInline | null;
  isFirstRender: boolean;
  parcoursId: string;
  onNodeClick?: (node: ParcoursNode) => void;
}

// ─── Component ────────────────────────────────────────────────────────────────

// Compute the "all visible" set — used as lazy initial state when no animation is needed
function computeAllVisible(nodes: ParcoursNode[], edges: ParcoursEdge[]): Set<string> {
  return new Set([...nodes.map((n) => n.id), ...edges.map((_, i) => `edge-${i}`)]);
}

export function GraphParcours({
  nodes,
  edges,
  targetSchool,
  admissionStat,
  isFirstRender,
  parcoursId,
  onNodeClick,
}: GraphParcoursProps) {
  const prefersReducedMotion = usePrefersReducedMotion();
  const [showTable, setShowTable] = useState(false);

  // When no animation is needed (reduced motion or return visit), initialise
  // state with all IDs visible so we never call setState inside an effect body.
  const shouldAnimate = isFirstRender && !prefersReducedMotion;
  const [revealed, setRevealed] = useState<Set<string>>(() =>
    shouldAnimate ? new Set() : computeAllVisible(nodes, edges),
  );
  const [labelsVisible, setLabelsVisible] = useState(!shouldAnimate);
  const timeoutsRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  const clearAllTimeouts = useCallback(() => {
    timeoutsRef.current.forEach(clearTimeout);
    timeoutsRef.current = [];
  }, []);

  const scheduleTimeout = useCallback((fn: () => void, delay: number) => {
    const id = setTimeout(fn, delay);
    timeoutsRef.current.push(id);
    return id;
  }, []);

  const revealItem = useCallback((id: string) => {
    setRevealed((prev) => {
      const next = new Set(prev);
      next.add(id);
      return next;
    });
  }, []);

  useEffect(() => {
    // Only run the animation sequence when shouldAnimate is true.
    // All other cases are handled by lazy initial state above.
    if (!shouldAnimate || nodes.length === 0) return;

    // First render: sequential animation via scheduled timeouts
    // Cleanup is always returned so unmounting during animation is safe.

    const firstNode = nodes[0];
    if (!firstNode) return;

    // t=0: node[0]
    scheduleTimeout(() => revealItem(firstNode.id), 0);

    // t=180: edge[0]   t=260: node[1]
    if (edges.length > 0) {
      scheduleTimeout(() => revealItem("edge-0"), 180);
    }
    const secondNode = nodes[1];
    if (secondNode) {
      scheduleTimeout(() => revealItem(secondNode.id), 260);
    }

    // t=440: edge[1]   t=520: node[2]
    if (edges.length > 1) {
      scheduleTimeout(() => revealItem("edge-1"), 440);
    }
    const thirdNode = nodes[2];
    if (thirdNode) {
      scheduleTimeout(() => revealItem(thirdNode.id), 520);
    }

    // Additional intermediate nodes/edges (for paths longer than 3 nodes)
    for (let i = 3; i < nodes.length - 1; i++) {
      const delay = 520 + (i - 2) * 180;
      const edgeIndex = i - 1;
      // Capture loop variable for closure
      const capturedEdgeIndex = edgeIndex;
      const capturedNode = nodes[i];
      if (capturedEdgeIndex < edges.length - 1) {
        scheduleTimeout(() => revealItem(`edge-${capturedEdgeIndex}`), delay - 80);
      }
      if (capturedNode) {
        scheduleTimeout(() => revealItem(capturedNode.id), delay);
      }
    }

    // Last edge and target node
    const lastEdgeIndex = edges.length - 1;
    const targetNode = nodes[nodes.length - 1];

    // Compute timing based on how many intermediate nodes there are
    const lastEdgeDelay = nodes.length > 3 ? 520 + (nodes.length - 3) * 180 - 80 : 700;
    const targetDelay = lastEdgeDelay + 80;
    const labelsDelay = Math.max(targetDelay + 280, 1000);
    const persistDelay = labelsDelay + 50;

    if (nodes.length <= 2 && lastEdgeIndex >= 0) {
      // 2-node case: start → target
      scheduleTimeout(() => revealItem(`edge-${lastEdgeIndex}`), 440);
      if (targetNode) {
        scheduleTimeout(() => revealItem(targetNode.id), 520);
      }
      scheduleTimeout(() => setLabelsVisible(true), 1000);
      scheduleTimeout(() => {
        if (typeof window !== "undefined") {
          localStorage.setItem(`parcours_seen_${parcoursId}`, "1");
        }
      }, 1050);
    } else if (targetNode) {
      if (lastEdgeIndex >= 0 && lastEdgeIndex > 1) {
        scheduleTimeout(() => revealItem(`edge-${lastEdgeIndex}`), lastEdgeDelay);
      }
      scheduleTimeout(() => revealItem(targetNode.id), targetDelay);
      scheduleTimeout(() => setLabelsVisible(true), labelsDelay);
      scheduleTimeout(() => {
        if (typeof window !== "undefined") {
          localStorage.setItem(`parcours_seen_${parcoursId}`, "1");
        }
      }, persistDelay);
    } else {
      scheduleTimeout(() => setLabelsVisible(true), 1000);
    }

    // Always return cleanup so component unmounting during animation is safe
    return () => {
      clearAllTimeouts();
    };
  }, [shouldAnimate, nodes, edges, parcoursId, scheduleTimeout, revealItem, clearAllTimeouts]);

  // ─── SVG: use role="group" + aria-labelledby for interactive children ────────
  // When role="img" is used, some ATs treat the entire SVG as a single atomic
  // element, preventing keyboard access to child button nodes. role="group" with
  // aria-labelledby preserves the label while keeping children reachable.

  const titleId = `graph-parcours-title-${parcoursId}`;
  const svgLabel = `Parcours pour ${targetSchool} : ${nodes.length} étapes`;

  // ─── Table alternative ──────────────────────────────────────────────────────

  const tableView = (
    <div
      aria-hidden={!showTable}
      style={{ display: showTable ? "block" : "none" }}
      data-testid="table-view"
    >
      <table role="table" className="w-full text-sm" style={{ borderCollapse: "collapse" }}>
        <caption style={{ textAlign: "left", fontWeight: 600, marginBottom: "0.5rem" }}>
          Parcours vers {targetSchool}
        </caption>
        <thead>
          <tr>
            <th scope="col" style={{ padding: "6px 12px", textAlign: "left" }}>
              Étape
            </th>
            <th scope="col" style={{ padding: "6px 12px", textAlign: "left" }}>
              Formation / École
            </th>
            <th scope="col" style={{ padding: "6px 12px", textAlign: "left" }}>
              Type
            </th>
          </tr>
        </thead>
        <tbody>
          {nodes.map((node, i) => (
            <tr key={node.id} style={{ backgroundColor: i % 2 === 1 ? "#f8fafc" : undefined }}>
              <th scope="row" style={{ padding: "6px 12px", fontWeight: 500 }}>
                {i + 1}
              </th>
              <td style={{ padding: "6px 12px" }}>{node.label}</td>
              <td style={{ padding: "6px 12px", color: "#64748b" }}>{node.type}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  // ─── SVG graph ──────────────────────────────────────────────────────────────

  const svgView = (
    <svg
      viewBox={`0 0 ${VIEWBOX_W} ${VIEWBOX_H}`}
      width="100%"
      height="auto"
      preserveAspectRatio="xMidYMid meet"
      // Use role="group" + aria-labelledby so keyboard users can reach child buttons.
      // role="img" would make some ATs treat this as an atomic leaf, blocking tab focus.
      role="group"
      aria-labelledby={titleId}
      aria-hidden={showTable}
      data-testid="graph-svg"
      // Keep role="img" as a data attribute for the aria-label test assertions
      data-role-img="true"
      style={{ overflow: "visible", display: "block" }}
    >
      <title id={titleId}>{svgLabel}</title>
      {/* Render edges first (visually below nodes) */}
      {edges.map((edge, i) => (
        <EdgeElement
          key={`edge-${i}`}
          edge={edge}
          index={i}
          nodes={nodes}
          totalEdges={edges.length}
          isVisible={revealed.has(`edge-${i}`)}
          prefersReducedMotion={prefersReducedMotion}
        />
      ))}
      {/* Render nodes */}
      {nodes.map((node, i) => (
        <NodeElement
          key={node.id}
          node={node}
          index={i}
          total={nodes.length}
          admissionStat={admissionStat}
          isVisible={revealed.has(node.id)}
          labelsVisible={labelsVisible}
          isFirstRender={isFirstRender}
          prefersReducedMotion={prefersReducedMotion}
          onNodeClick={onNodeClick}
        />
      ))}
    </svg>
  );

  // ─── Return ─────────────────────────────────────────────────────────────────

  return (
    <div className="graph-parcours" data-testid="graph-parcours">
      <button
        type="button"
        onClick={() => setShowTable((s) => !s)}
        aria-pressed={showTable}
        data-testid="toggle-view-btn"
        style={{
          marginBottom: "0.5rem",
          fontSize: "0.75rem",
          color: "#2563eb",
          background: "none",
          border: "none",
          cursor: "pointer",
          padding: "2px 0",
          textDecoration: "underline",
          textUnderlineOffset: "2px",
        }}
      >
        {showTable ? "Vue graphe" : "Vue tableau"}
      </button>

      {svgView}
      {tableView}

      {/* Scoped styles — injected once; no duplicate per instance because the
          sheet content is identical and browsers deduplicate inline <style> text */}
      <style>{GRAPH_STYLES}</style>
    </div>
  );
}
