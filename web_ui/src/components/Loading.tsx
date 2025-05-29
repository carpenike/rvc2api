import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";
import type { ReactNode } from "react";

interface LoadingProps {
  size?: "sm" | "md" | "lg";
  message?: string;
  fullPage?: boolean;
  className?: string;
  children?: ReactNode;
}

export function Loading({
  size = "md",
  message = "Loading...",
  fullPage = false,
  className = "",
  children
}: LoadingProps) {
  const sizeClasses = {
    sm: "h-4 w-4",
    md: "h-6 w-6",
    lg: "h-8 w-8"
  };

  const spinner = (
    <Loader2
      className={cn("animate-spin", sizeClasses[size])}
      role="status"
      aria-label="Loading"
      data-testid="loading-spinner"
    />
  );

  // For small loading spinners without messages, just return the spinner
  if (size === "sm" && !message && !children) {
    return <span className={className}>{spinner}</span>;
  }

  // For full page loading state
  if (fullPage) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-background/80 backdrop-blur-sm z-50">
        <Card className="max-w-sm">
          <CardContent className="flex flex-col items-center p-6">
            {spinner}
            {message && <p className="mt-4 text-foreground text-lg" aria-live="polite">{message}</p>}
            {children}
          </CardContent>
        </Card>
      </div>
    );
  }

  // Default loading component
  return (
    <div className={cn("flex flex-col items-center justify-center p-6", className)}>
      {spinner}
      {message && <p className="mt-2 text-muted-foreground" aria-live="polite">{message}</p>}
      {children}
    </div>
  );
}
