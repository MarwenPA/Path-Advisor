import { useTranslations } from "next-intl";

import { cn } from "@/lib/utils";

// Illustrative percentages for anonymous visitors — the real graph
// (components/parcours/GraphParcours) needs a scored profile.
const BRANCHES = [
  {
    id: "but",
    y: 28,
    pct: 82,
    edge: "M96 75 C150 75, 150 28, 196 28",
    stroke: "stroke-semantic-sur",
    fill: "fill-semantic-sur",
  },
  {
    id: "licence",
    y: 75,
    pct: 61,
    edge: "M96 75 L196 75",
    stroke: "stroke-semantic-realiste",
    fill: "fill-semantic-realiste",
  },
  {
    id: "cpge",
    y: 122,
    pct: 23,
    edge: "M96 75 C150 75, 150 122, 196 122",
    stroke: "stroke-semantic-audacieux",
    fill: "fill-semantic-audacieux",
  },
] as const;

const END_EDGES = [
  "M340 28 C364 28, 364 75, 388 75",
  "M340 75 L388 75",
  "M340 122 C364 122, 364 75, 388 75",
];

const NODE_CLASS = "fill-bg stroke-border-strong stroke-[1.2px]";

export function ParcoursExampleGraph() {
  const t = useTranslations("homepage.ahaMoments.parcours.graph");

  return (
    <svg
      viewBox="0 0 440 150"
      role="img"
      aria-label={t("ariaLabel")}
      className="mt-1 h-auto w-full max-w-full text-[11px]"
    >
      {BRANCHES.map((branch) => (
        <path
          key={branch.id}
          d={branch.edge}
          className={cn("fill-none stroke-[1.5px]", branch.stroke)}
        />
      ))}
      {END_EDGES.map((d) => (
        <path key={d} d={d} className="fill-none stroke-border-strong stroke-[1.5px]" />
      ))}

      <rect x="8" y="60" width="88" height="30" rx="6" className="fill-brand" />
      <text x="52" y="79" textAnchor="middle" className="fill-bg font-medium">
        {t("start")}
      </text>
      <text x="52" y="108" textAnchor="middle" className="fill-text-subtle text-[10px]">
        {t("startCaption")}
      </text>

      {BRANCHES.map((branch) => (
        <g key={branch.id}>
          <rect x="196" y={branch.y - 15} width="144" height="30" rx="6" className={NODE_CLASS} />
          <text x="206" y={branch.y + 4} className="fill-text">
            {t(`nodes.${branch.id}`)}
          </text>
          <text
            x="332"
            y={branch.y + 4}
            textAnchor="end"
            className={cn("font-semibold font-tabular", branch.fill)}
          >
            {`${branch.pct} %`}
          </text>
        </g>
      ))}

      <rect x="388" y="60" width="44" height="30" rx="6" className={NODE_CLASS} />
      <text x="410" y="79" textAnchor="middle" className="fill-text">
        {t("end")}
      </text>
    </svg>
  );
}
