import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

type BadgeProps = {
  tone?: "neutral" | "success" | "warning" | "danger";
  children: ReactNode;
};

const TONES: Record<NonNullable<BadgeProps["tone"]>, string> = {
  neutral: "border-[var(--border)] text-[var(--muted)]",
  success: "border-[var(--success)] text-[var(--success)]",
  warning: "border-[#b7791f] text-[#b7791f]",
  danger: "border-[var(--danger)] text-[var(--danger)]",
};

export function Badge({ tone = "neutral", children }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium",
        TONES[tone],
      )}
    >
      {children}
    </span>
  );
}
