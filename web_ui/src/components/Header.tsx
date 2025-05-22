import React from "react";
import { ThemeSelector } from "./ThemeSelector";

/**
 * Header component for the application
 * - Semantic <header> with ARIA role
 * - Responsive, theme-adaptive, accessible
 * - Integrates ThemeSelector and app branding
 */
const Header: React.FC<{ wsStatus?: string }> = ({ wsStatus }) => {
  return (
    <header
      className="hidden lg:flex bg-[var(--color-surface)] text-[var(--color-text)] px-6 py-4 items-center justify-between shadow-md border-b border-[var(--color-border)]"
      role="banner"
    >
      <div className="flex items-center">
        <span className="text-xl font-bold">RVC2API</span>
      </div>
      <div className="flex items-center space-x-4">
        {wsStatus && (
          <div className="flex items-center space-x-3" aria-live="polite">
            <span className="sr-only" id="ws-status-label">WebSocket status:</span>
            <span
              aria-labelledby="ws-status-label"
              className={`px-2 py-1 rounded-full text-sm font-medium transition-colors duration-200
                ${wsStatus === "open"
                  ? "bg-[var(--color-success,theme(colors.green.100)/.2)] text-[var(--color-success,theme(colors.green.600))]"
                  : wsStatus === "connecting"
                  ? "bg-[var(--color-warning,theme(colors.yellow.100)/.2)] text-[var(--color-warning,theme(colors.yellow.700))]"
                  : "bg-[var(--color-error,theme(colors.red.100)/.2)] text-[var(--color-error,theme(colors.red.700))]"}
              `}
            >
              {wsStatus.charAt(0).toUpperCase() + wsStatus.slice(1)}
            </span>
          </div>
        )}
        <ThemeSelector />
      </div>
    </header>
  );
};

export default Header;
