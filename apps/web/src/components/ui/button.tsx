import { type ButtonHTMLAttributes, forwardRef } from "react";

import { cn } from "@/lib/cn";

export const Button = forwardRef<
  HTMLButtonElement,
  ButtonHTMLAttributes<HTMLButtonElement>
>(({ className, type = "button", ...props }, ref) => (
  <button
    ref={ref}
    type={type}
    className={cn(
      "inline-flex min-h-11 items-center justify-center rounded-[var(--radius)] bg-[var(--accent)] px-5 text-[0.9375rem] font-semibold text-white transition-colors hover:bg-[var(--accent-hover)] disabled:cursor-not-allowed disabled:opacity-60",
      className,
    )}
    {...props}
  />
));
Button.displayName = "Button";
