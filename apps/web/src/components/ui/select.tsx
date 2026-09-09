import { type SelectHTMLAttributes, forwardRef } from "react";

import { cn } from "@/lib/cn";

export const Select = forwardRef<
  HTMLSelectElement,
  SelectHTMLAttributes<HTMLSelectElement>
>(({ className, children, ...props }, ref) => (
  <select
    ref={ref}
    className={cn(
      "min-h-11 w-full rounded-[var(--radius-control)] border border-[var(--control-border)] bg-[var(--control-bg)] px-3 text-sm text-[var(--foreground)] shadow-[inset_0_1px_1px_rgba(23,32,29,0.035)] transition-[background-color,border-color,box-shadow] duration-150 outline-none hover:border-[var(--border-strong)] focus:border-[var(--accent)] focus:bg-[var(--surface-raised)] focus:ring-4 focus:ring-[var(--focus-ring)] disabled:cursor-not-allowed disabled:opacity-55",
      className,
    )}
    {...props}
  >
    {children}
  </select>
));
Select.displayName = "Select";
