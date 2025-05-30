import { Button as ShadcnButton, type ButtonProps as ShadcnButtonProps } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import type { ButtonHTMLAttributes, ReactNode } from "react";
import { memo } from "react";

type ButtonVariant = "default" | "destructive" | "outline" | "secondary" | "ghost" | "link" | "primary" | "accent";

type ButtonProps = {
  variant?: ButtonVariant;
  isLoading?: boolean;
  children: ReactNode;
  className?: string;
  "aria-label"?: string;
  title?: string;
  type?: "button" | "submit" | "reset";
  size?: ShadcnButtonProps["size"];
} & Omit<ButtonHTMLAttributes<HTMLButtonElement>, "type">;

export const Button = memo(function Button({
  variant = "default",
  isLoading = false,
  children,
  className = "",
  "aria-label": ariaLabel,
  title,
  type = "button",
  size = "default",
  ...props
}: ButtonProps) {
  // Map legacy variants to shadcn/UI variants
  const mappedVariant = variant === "primary" ? "default" :
                       variant === "accent" ? "default" : variant;

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
    <ShadcnButton
      className={className}
      disabled={isLoading || props.disabled}
      aria-busy={isLoading ? "true" : undefined}
      data-testid="button"
      aria-label={ariaLabel}
      title={title}
      type={type}
      variant={mappedVariant}
      size={size}
      {...props}
    >
      {isLoading ? (
        <>
          <Loader2 className="h-4 w-4 animate-spin" />
          <span className="sr-only">Loading...</span>
          Loading...
        </>
      ) : (
        children
      )}
    </ShadcnButton>
  );
});
