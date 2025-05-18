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
    sm: "h-6 w-6 border-2",
    md: "h-10 w-10 border-2",
    lg: "h-16 w-16 border-3"
  };

  const spinner = (
    <div className={`animate-spin rounded-full ${sizeClasses[size]} border-t-rv-primary border-b-rv-primary border-r-transparent border-l-transparent`}></div>
  );

  // For small loading spinners without messages, just return the spinner
  if (size === "sm" && !message && !children) {
    return <span className={className}>{spinner}</span>;
  }

  // For full page loading state
  if (fullPage) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-rv-background/80 backdrop-blur-sm z-50">
        <div className="flex flex-col items-center p-8 rounded-xl">
          {spinner}
          {message && <p className="mt-4 text-rv-text/90 text-lg">{message}</p>}
          {children}
        </div>
      </div>
    );
  }

  // Default loading component
  return (
    <div className={`flex flex-col items-center justify-center p-6 ${className}`}>
      {spinner}
      {message && <p className="mt-2 text-rv-text/70">{message}</p>}
      {children}
    </div>
  );
}
