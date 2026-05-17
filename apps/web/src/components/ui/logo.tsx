import * as React from "react";

import { cn } from "@/lib/utils";

type LogoVariant = "color" | "mono";

interface LogoProps extends React.SVGAttributes<SVGSVGElement> {
  variant?: LogoVariant;
  title?: string;
}

export function Logo({
  variant = "color",
  title = "Path Advisor",
  className,
  ...props
}: LogoProps) {
  const isMono = variant === "mono";
  const strokeLeft = isMono ? "stroke-brand" : "stroke-semantic-audacieux";
  const strokeMid = isMono ? "stroke-brand" : "stroke-semantic-realiste";
  const strokeRight = isMono ? "stroke-brand" : "stroke-semantic-sur";
  const fillLeft = isMono ? "fill-brand" : "fill-semantic-audacieux";
  const fillMid = isMono ? "fill-brand" : "fill-semantic-realiste";
  const fillRight = isMono ? "fill-brand" : "fill-semantic-sur";

  return (
    <svg
      viewBox="0 0 80 80"
      fill="none"
      role="img"
      aria-label={title}
      className={cn("h-10 w-10", className)}
      {...props}
    >
      <title>{title}</title>
      <path
        d="M 40 64 C 34 52, 18 40, 12 18"
        strokeWidth={3.5}
        strokeLinecap="round"
        className={strokeLeft}
      />
      <circle cx="12" cy="18" r="3.5" className={fillLeft} />
      <path
        d="M 40 64 C 40 50, 40 28, 40 14"
        strokeWidth={3.5}
        strokeLinecap="round"
        className={strokeMid}
      />
      <circle cx="40" cy="14" r="3.5" className={fillMid} />
      <path
        d="M 40 64 C 46 52, 62 40, 68 18"
        strokeWidth={3.5}
        strokeLinecap="round"
        className={strokeRight}
      />
      <circle cx="68" cy="18" r="3.5" className={fillRight} />
      <circle cx="40" cy="64" r="5" className="fill-brand" />
    </svg>
  );
}

export function LogoWordmark({ variant = "color", className, ...props }: LogoProps) {
  return (
    <span className={cn("inline-flex items-center gap-3", className)}>
      <Logo variant={variant} className="h-9 w-9" {...props} />
      <span className="text-xl font-semibold tracking-tight text-text">Path Advisor</span>
    </span>
  );
}
