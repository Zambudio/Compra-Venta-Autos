import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

type BadgeProps = {
  tone?: "neutral" | "success" | "warning" | "danger";
  children: ReactNode;
};

const TONES: Record<NonNullable<BadgeProps["tone"]>, string> = {
  neutral:
    "border-[var(--border)] bg-[var(--surface-hover)] text-[var(--foreground-secondary)]",
  success:
    "border-[color-mix(in_srgb,var(--success)_22%,transparent)] bg-[var(--success-soft)] text-[var(--success)]",
  warning:
    "border-[color-mix(in_srgb,var(--warning)_22%,transparent)] bg-[var(--warning-soft)] text-[var(--warning)]",
  danger:
    "border-[color-mix(in_srgb,var(--danger)_22%,transparent)] bg-[var(--danger-soft)] text-[var(--danger)]",
};

export function Badge({ tone = "neutral", children }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex min-h-6 items-center rounded-full border px-2 py-0.5 text-[0.6875rem] leading-none font-semibold whitespace-nowrap",
        TONES[tone],
      )}
    >
      {children}
    </span>
  );
}
