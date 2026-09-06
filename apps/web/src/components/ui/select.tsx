import { type SelectHTMLAttributes, forwardRef } from "react";

import { cn } from "@/lib/cn";

export const Select = forwardRef<
  HTMLSelectElement,
  SelectHTMLAttributes<HTMLSelectElement>
>(({ className, children, ...props }, ref) => (
  <select
    ref={ref}
    className={cn(
      "min-h-11 w-full rounded-[var(--radius)] border border-[var(--border)] bg-white px-3 text-[0.9375rem] text-[var(--foreground)] transition-colors outline-none hover:border-[#aeb3b7] focus:border-[var(--accent)] disabled:cursor-not-allowed disabled:bg-[#f4f5f5]",
      className,
    )}
    {...props}
  >
    {children}
  </select>
));
Select.displayName = "Select";
