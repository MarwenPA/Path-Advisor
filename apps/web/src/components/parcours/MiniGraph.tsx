import type { ParcoursNode, ParcoursEdge } from "./types";

interface MiniGraphProps {
  nodes: ParcoursNode[];
  edges: ParcoursEdge[];
}

export function MiniGraph({ nodes, edges }: MiniGraphProps) {
  if (nodes.length === 0) return null;

  const WIDTH = 200;
  const HEIGHT = 60;
  const nodeCount = nodes.length;
  const spacing = WIDTH / (nodeCount + 1);

  return (
    <svg
      viewBox={"0 0 " + WIDTH + " " + HEIGHT}
      width={WIDTH}
      height={HEIGHT}
      role="img"
      aria-label={"Parcours en " + nodeCount + " étapes"}
      className="overflow-visible"
    >
      {edges.map((edge, i) => {
        const sourceIdx = nodes.findIndex((n) => n.id === edge.source);
        const targetIdx = nodes.findIndex((n) => n.id === edge.target);
        if (sourceIdx === -1 || targetIdx === -1) return null;
        const x1 = spacing * (sourceIdx + 1);
        const x2 = spacing * (targetIdx + 1);
        const y = HEIGHT / 2;
        return <line key={i} x1={x1} y1={y} x2={x2} y2={y} stroke="#cbd5e1" strokeWidth={2} />;
      })}
      {nodes.map((node, i) => {
        const cx = spacing * (i + 1);
        const cy = HEIGHT / 2;
        const r = node.type === "target" ? 10 : 6;
        const fill =
          node.type === "start" ? "#e2e8f0" : node.type === "target" ? "#dbeafe" : "#f1f5f9";
        const stroke = node.type === "target" ? "#2563eb" : "#94a3b8";
        return (
          <circle
            key={node.id}
            cx={cx}
            cy={cy}
            r={r}
            fill={fill}
            stroke={stroke}
            strokeWidth={1.5}
          />
        );
      })}
    </svg>
  );
}
