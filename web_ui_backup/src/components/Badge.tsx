import { Badge as ShadcnBadge } from "@/components/ui/badge";
import type { ReactNode } from "react";

interface BadgeProps {
  variant?: "default" | "secondary" | "destructive" | "outline" | "primary";
  children: ReactNode;
  className?: string;
  title?: string;
  ariaLabel?: string;
}

export function Badge({
  variant = "default",
  children,
  className = "",
  title,
  ariaLabel
}: BadgeProps) {
  // Map legacy variants to shadcn/UI variants
  const mappedVariant = variant === "primary" ? "default" : variant;

  // If ariaLabel is not provided, use children as fallback (visually hidden for screen readers)
  const computedAriaLabel = ariaLabel || (typeof children === "string" ? children : undefined);

  return (
    <ShadcnBadge
      variant={mappedVariant}
      className={className}
      data-testid="badge"
      title={title}
      aria-label={computedAriaLabel}
      role={computedAriaLabel ? "status" : "presentation"}
    >
      {children}
      {/* Visually hidden fallback for accessibility if ariaLabel is not provided and children is not string */}
      {(!ariaLabel && typeof children !== "string") && (
        <span className="sr-only">Badge</span>
      )}
    </ShadcnBadge>
  );
}
