import { type InputHTMLAttributes, forwardRef } from "react";

import { cn } from "@/lib/cn";

export const Input = forwardRef<
  HTMLInputElement,
  InputHTMLAttributes<HTMLInputElement>
>(({ className, ...props }, ref) => (
  <input
    ref={ref}
    className={cn(
      "min-h-11 w-full rounded-[var(--radius-control)] border border-[var(--control-border)] bg-[var(--control-bg)] px-3.5 text-sm text-[var(--foreground)] shadow-[inset_0_1px_1px_rgba(23,32,29,0.035)] transition-[background-color,border-color,box-shadow] duration-150 outline-none placeholder:text-[var(--muted-soft)] hover:border-[var(--border-strong)] focus:border-[var(--accent)] focus:bg-[var(--surface-raised)] focus:ring-4 focus:ring-[var(--focus-ring)] disabled:cursor-not-allowed disabled:opacity-55",
      className,
    )}
    {...props}
  />
));
Input.displayName = "Input";
