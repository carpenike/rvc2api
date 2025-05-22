import type { ReactNode } from "react";

interface BadgeProps {
  variant?: "primary" | "secondary" | "success" | "warning" | "error";
  children: ReactNode;
  className?: string;
  title?: string;
  ariaLabel?: string;
}

export function Badge({
  variant = "primary",
  children,
  className = "",
  title,
  ariaLabel
}: BadgeProps) {
  const variantClasses = {
    primary: "bg-rv-primary/20 text-rv-primary",
    secondary: "bg-rv-secondary/20 text-rv-secondary",
    success: "bg-rv-success/20 text-rv-success",
    warning: "bg-rv-warning/20 text-rv-warning",
    error: "bg-rv-error/20 text-rv-error"
  };
  const badgeClass = [
    "inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium select-none",
    variantClasses[variant] || variantClasses.primary,
    className
  ].filter(Boolean).join(" ");

  // If ariaLabel is not provided, use children as fallback (visually hidden for screen readers)
  const computedAriaLabel = ariaLabel || (typeof children === "string" ? children : undefined);

  return (
    <span
      role={computedAriaLabel ? "status" : "presentation"}
      className={badgeClass}
      data-testid="badge"
      title={title}
      aria-label={computedAriaLabel}
      tabIndex={-1}
    >
      {children}
      {/* Visually hidden fallback for accessibility if ariaLabel is not provided and children is not string */}
      {(!ariaLabel && typeof children !== "string") && (
        <span className="sr-only">Badge</span>
      )}
    </span>
  );
}
