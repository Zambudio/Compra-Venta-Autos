import { type InputHTMLAttributes, forwardRef } from "react";

import { cn } from "@/lib/cn";

export const Input = forwardRef<
  HTMLInputElement,
  InputHTMLAttributes<HTMLInputElement>
>(({ className, ...props }, ref) => (
  <input
    ref={ref}
    className={cn(
      "min-h-11 w-full rounded-[var(--radius)] border border-[var(--border)] bg-white px-3.5 text-[0.9375rem] text-[var(--foreground)] shadow-none transition-colors outline-none placeholder:text-[#858b90] hover:border-[#aeb3b7] focus:border-[var(--accent)] disabled:cursor-not-allowed disabled:bg-[#f4f5f5]",
      className,
    )}
    {...props}
  />
));
Input.displayName = "Input";
