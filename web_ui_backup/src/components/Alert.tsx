import { AlertDescription, AlertTitle, Alert as ShadcnAlert } from "@/components/ui/alert";
import { AlertTriangle, CheckCircle, Info, X, XCircle } from "lucide-react";
import type { ReactNode } from "react";

interface AlertProps {
  title?: string;
  variant?: "default" | "destructive" | "success" | "warning" | "error" | "info";
  children: ReactNode;
  className?: string;
  onDismiss?: () => void;
}

export function Alert({
  title,
  variant = "default",
  children,
  className = "",
  onDismiss
}: AlertProps) {
  // Map our custom variants to shadcn variants
  const shadcnVariant = variant === "destructive" ? "destructive" :
                        variant === "error" ? "destructive" : "default";

  const icons = {
    default: <Info className="h-4 w-4" />,
    success: <CheckCircle className="h-4 w-4" />,
    warning: <AlertTriangle className="h-4 w-4" />,
    destructive: <XCircle className="h-4 w-4" />,
    error: <XCircle className="h-4 w-4" />,
    info: <Info className="h-4 w-4" />
  };

  return (
    <ShadcnAlert
      variant={shadcnVariant}
      className={`${className} ${variant === "success" ? "border-green-500/50 text-green-700 dark:text-green-400" : ""} ${variant === "warning" ? "border-yellow-500/50 text-yellow-700 dark:text-yellow-400" : ""}`}
      data-testid="alert"
    >
      {icons[variant as keyof typeof icons]}
      <div className="flex-1">
        {title && <AlertTitle>{title}</AlertTitle>}
        <AlertDescription>{children}</AlertDescription>
      </div>
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="absolute right-2 top-2 p-1 rounded hover:bg-black/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2"
          aria-label="Dismiss alert"
          data-testid="alert-dismiss"
        >
          <span className="sr-only">Dismiss</span>
          <X className="h-4 w-4" />
        </button>
      )}
    </ShadcnAlert>
  );
}
