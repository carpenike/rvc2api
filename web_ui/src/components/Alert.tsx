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
      wrapper: "bg-rv-primary/10 border-rv-primary/30 text-rv-primary",
      icon: "text-rv-primary"
    },
    success: {
      wrapper: "bg-rv-success/10 border-rv-success/30 text-rv-success",
      icon: "text-rv-success"
    },
    warning: {
      wrapper: "bg-rv-warning/10 border-rv-warning/30 text-rv-warning",
      icon: "text-rv-warning"
    },
    error: {
      wrapper: "bg-rv-error/10 border-rv-error/30 text-rv-error",
      icon: "text-rv-error"
    }
  };

  // Icons for different alert types
  const icons = {
    info: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    success: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    warning: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    ),
    error: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    )
  };

  return (
    <div className={`p-4 rounded-lg border ${variantClasses[variant].wrapper} ${className}`}>
      <div className="flex">
        <div className={`flex-shrink-0 ${variantClasses[variant].icon}`}>
          {icons[variant]}
        </div>
        <div className="ml-3 flex-grow">
          {title && <h3 className="text-sm font-medium">{title}</h3>}
          <div className="text-sm mt-2">{children}</div>
        </div>
        {onDismiss && (
          <button
            type="button"
            className={`ml-auto -mx-1.5 -my-1.5 rounded-lg focus:ring-2 p-1.5 inline-flex h-8 w-8 ${variantClasses[variant].wrapper}`}
            onClick={onDismiss}
            aria-label="Dismiss"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}
