import clsx from "clsx";
import React from "react";

interface ToggleProps {
  isOn: boolean;
  onToggle: (isOn: boolean) => void;
  disabled?: boolean;
  label?: string;
  className?: string;
  size?: "sm" | "md" | "lg";
  id?: string;
}

export function Toggle({
  isOn,
  onToggle,
  disabled = false,
  label,
  className = "",
  size = "md",
  id
}: ToggleProps) {
  // Size classes
  const sizeClasses = {
    sm: {
      toggle: "w-7 h-4",
      circle: "w-3 h-3",
      translate: "translate-x-3"
    },
    md: {
      toggle: "w-10 h-5",
      circle: "w-4 h-4",
      translate: "translate-x-5"
    },
    lg: {
      toggle: "w-12 h-6",
      circle: "w-5 h-5",
      translate: "translate-x-6"
    }
  };
  const currentSize = sizeClasses[size];

  // Keyboard accessibility
  const handleKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>) => {
    if (disabled) return;
    if (e.key === " " || e.key === "Enter") {
      e.preventDefault();
      onToggle(!isOn);
    }
  };

  // Visually hidden utility
  const srOnly = "sr-only";

  return (
    <div className={clsx("flex items-center", className)}>
      {label ? (
        <label htmlFor={id || "toggle-switch"} className="mr-2 text-rv-text font-medium">
          {label}
        </label>
      ) : (
        <span className={srOnly} id={id ? `${id}-label` : "toggle-switch-label"}>
          Toggle
        </span>
      )}
      <button
        type="button"
        id={id || "toggle-switch"}
        role="switch"
        aria-checked={isOn}
        aria-disabled={disabled}
        aria-label={label || "Toggle"}
        aria-labelledby={label ? undefined : id ? `${id}-label` : "toggle-switch-label"}
        tabIndex={disabled ? -1 : 0}
        disabled={disabled}
        onClick={() => !disabled && onToggle(!isOn)}
        onKeyDown={handleKeyDown}
        className={clsx(
          "relative inline-flex items-center transition-colors duration-200 focus:outline-none",
          currentSize.toggle,
          isOn
            ? "bg-rv-primary border-rv-primary"
            : "bg-rv-surface border border-rv-border",
          disabled
            ? "opacity-50 cursor-not-allowed"
            : "cursor-pointer focus:ring-2 focus:ring-rv-primary",
          "rounded-full",
          "p-0"
        )}
        data-testid="toggle-switch"
      >
        <span
          className={clsx(
            "inline-block rounded-full bg-white shadow transform transition-transform",
            currentSize.circle,
            isOn ? currentSize.translate : "translate-x-0",
            disabled ? "bg-rv-border" : "bg-rv-surface"
          )}
          aria-hidden="true"
        />
      </button>
    </div>
  );
}
