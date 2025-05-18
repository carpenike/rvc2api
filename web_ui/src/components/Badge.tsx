import type { ReactNode } from "react";

interface BadgeProps {
  variant?: "primary" | "secondary" | "success" | "warning" | "error";
  children: ReactNode;
  className?: string;
}

export function Badge({ variant = "primary", children, className = "" }: BadgeProps) {
  const variantClasses = {
    primary: "bg-rv-primary/20 text-rv-primary",
    secondary: "bg-rv-secondary/20 text-rv-secondary",
    success: "bg-rv-success/20 text-rv-success",
    warning: "bg-rv-warning/20 text-rv-warning",
    error: "bg-rv-error/20 text-rv-error"
  };

  return (
    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${variantClasses[variant]} ${className}`}>
      {children}
    </span>
  );
}
