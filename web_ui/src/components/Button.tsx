import clsx from "clsx";
import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "accent" | "danger" | "ghost";

type ButtonProps = {
  variant?: ButtonVariant;
  isLoading?: boolean;
  children: ReactNode;
  className?: string;
  "aria-label"?: string;
  title?: string;
  type?: "button" | "submit" | "reset";
} & ButtonHTMLAttributes<HTMLButtonElement>;

export function Button({
  variant = "primary",
  isLoading = false,
  children,
  className = "",
  "aria-label": ariaLabel,
  title,
  type = "button",
  ...props
}: ButtonProps) {
  // Base classes for all buttons
  const baseClasses = "btn";

  // Variant-specific classes
  const variantClasses = {
    primary: "btn-primary",
    secondary: "btn-secondary",
    accent: "btn-accent",
    danger: "bg-rv-error hover:bg-rv-error/80 text-white",
    ghost: "bg-transparent hover:bg-rv-surface text-rv-text border border-rv-surface"
  };

  // Spinner color adapts to variant
  const spinnerColor =
    variant === "danger" || variant === "primary" || variant === "accent"
      ? "text-white"
      : variant === "secondary"
        ? "text-rv-secondary"
        : "text-rv-text";

  // Accessibility: warn if children is not a string and no aria-label is provided
  if (
    process.env.NODE_ENV !== "production" &&
    typeof children !== "string" &&
    !ariaLabel
  ) {
    console.warn(
      "[Button] Accessible label missing: Provide aria-label prop when children is not a string."
    );
  }

  return (
    <button
      className={clsx(baseClasses, variantClasses[variant], className)}
      disabled={isLoading || props.disabled}
      aria-busy={isLoading ? "true" : undefined}
      data-testid="button"
      aria-label={ariaLabel}
      title={title}
      type={type}
      {...props}
    >
      {isLoading ? (
        <span className="flex items-center justify-center">
          <svg className={clsx("animate-spin -ml-1 mr-2 h-4 w-4", spinnerColor)} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" aria-hidden="true">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span className="sr-only">Loading...</span>
          <span aria-hidden="true">Loading...</span>
        </span>
      ) : (
        children
      )}
    </button>
  );
}
