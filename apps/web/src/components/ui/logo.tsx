import * as React from "react";

import { cn } from "@/lib/utils";

type LogoVariant = "light" | "dark";

interface LogoProps extends React.SVGAttributes<SVGSVGElement> {
  variant?: LogoVariant;
  title?: string;
  decorative?: boolean;
}

export function Logo({
  variant = "light",
  title = "Path-Advisor",
  decorative = false,
  className,
  ...props
}: LogoProps) {
  const stroke = variant === "dark" ? "stroke-bg" : "stroke-text";
  const a11y = decorative
    ? ({ "aria-hidden": true } as const)
    : ({ role: "img", "aria-label": title } as const);

  return (
    <svg
      viewBox="0 0 64 64"
      fill="none"
      className={cn("h-10 w-10", className)}
      {...a11y}
      {...props}
    >
      {decorative ? null : <title>{title}</title>}
      <path
        d="M10 45.9A26 26 0 1 1 26 57.3"
        strokeWidth={4}
        strokeLinecap="round"
        strokeLinejoin="round"
        className={stroke}
      />
      <circle cx="32" cy="32" r="14" strokeWidth={4} className={stroke} />
      <path d="M18 32V61" strokeWidth={4} strokeLinecap="round" className={stroke} />
      <circle cx="32" cy="32" r="6" className="fill-brand" />
    </svg>
  );
}

export function LogoWordmark({ variant = "light", className, ...props }: LogoProps) {
  return (
    <span className={cn("inline-flex items-center gap-3", className)}>
      <Logo variant={variant} decorative className="h-9 w-9" {...props} />
      <span
        className={cn(
          "text-xl font-semibold tracking-tight",
          variant === "dark" ? "text-bg" : "text-text",
        )}
      >
        Path-Advisor
      </span>
    </span>
  );
}
