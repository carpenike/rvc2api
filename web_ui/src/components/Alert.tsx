import type { ReactNode } from "react";

interface AlertProps {
  title?: string;
  variant?: "info" | "success" | "warning" | "error";
  children: ReactNode;
  className?: string;
  onDismiss?: () => void;
}

export function Alert({
  title,
  variant = "info",
  children,
  className = "",
  onDismiss
}: AlertProps) {
  const variantClasses = {
    info: {
      wrapper: "bg-rv-primary/10 border border-rv-primary/30 text-rv-primary",
      icon: "text-rv-primary"
    },
    success: {
      wrapper: "bg-rv-success/10 border border-rv-success/30 text-rv-success",
      icon: "text-rv-success"
    },
    warning: {
      wrapper: "bg-rv-warning/10 border border-rv-warning/30 text-rv-warning",
      icon: "text-rv-warning"
    },
    error: {
      wrapper: "bg-rv-error/10 border border-rv-error/30 text-rv-error",
      icon: "text-rv-error"
    }
  };

  const icons = {
    info: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    success: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    warning: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    ),
    error: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
      </svg>
    )
  };

  const wrapperClass = [
    "flex items-start gap-2 p-3 rounded-md relative",
    variantClasses[variant]?.wrapper,
    className
  ].filter(Boolean).join(" ");

  return (
    <div
      role="alert"
      aria-live="polite"
      className={wrapperClass}
      data-testid="alert"
    >
      <span className={"mt-0.5 " + variantClasses[variant]?.icon} aria-hidden="true">
        {icons[variant]}
      </span>
      <div className="flex-1 min-w-0">
        {title && <div className="font-semibold mb-0.5">{title}</div>}
        <div>{children}</div>
      </div>
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="ml-2 p-1 rounded hover:bg-black/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-rv-primary"
          aria-label="Dismiss alert"
          data-testid="alert-dismiss"
        >
          <span className="sr-only">Dismiss</span>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </div>
  );
}
