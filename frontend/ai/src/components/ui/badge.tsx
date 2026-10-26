import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold font-mono transition-colors focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-cyan-500/20 text-cyan-300 border border-cyan-500/40",
        secondary: "border-transparent bg-slate-800 text-slate-300",
        destructive:
          "border-transparent bg-red-500/20 text-red-300 border-red-500/40",
        outline: "text-slate-200 border-slate-700",
        emerald: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
        amber: "bg-amber-500/15 text-amber-300 border-amber-500/30",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export interface BadgeProps
  extends
    React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
