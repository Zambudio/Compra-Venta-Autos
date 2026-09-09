import { cva, type VariantProps } from "class-variance-authority";
import { type ButtonHTMLAttributes, forwardRef } from "react";

import { cn } from "@/lib/cn";

const buttonVariants = cva(
  "inline-flex min-h-11 items-center justify-center gap-2 rounded-[var(--radius-control)] px-4 text-sm font-semibold transition-[background-color,color,border-color,box-shadow,transform] duration-150 ease-[cubic-bezier(0.23,1,0.32,1)] active:scale-[0.98] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[var(--focus-ring)] disabled:pointer-events-none disabled:opacity-45",
  {
    variants: {
      variant: {
        primary:
          "bg-[var(--accent)] text-white shadow-[0_1px_2px_rgba(6,49,42,0.18)] hover:bg-[var(--accent-hover)]",
        secondary:
          "border border-[var(--border-strong)] bg-[var(--surface-raised)] text-[var(--foreground)] shadow-[0_1px_2px_rgba(23,32,29,0.03)] hover:bg-[var(--surface-hover)]",
        ghost:
          "text-[var(--foreground-secondary)] hover:bg-[var(--surface-hover)] hover:text-[var(--foreground)]",
        danger: "bg-[var(--danger)] text-white hover:bg-[#87352f]",
      },
      size: {
        default: "min-h-11 px-4",
        compact: "min-h-10 px-3 text-xs",
        icon: "h-11 w-11 px-0",
      },
    },
    defaultVariants: { variant: "primary", size: "default" },
  },
);

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof buttonVariants>;

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, type = "button", variant, size, ...props }, ref) => (
    <button
      ref={ref}
      type={type}
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    />
  ),
);
Button.displayName = "Button";
