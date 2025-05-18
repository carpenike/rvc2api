import { useState } from "react";

interface ToggleProps {
  isOn: boolean;
  onToggle: (isOn: boolean) => void;
  disabled?: boolean;
  label?: string;
  className?: string;
  size?: "sm" | "md" | "lg";
}

export function Toggle({
  isOn,
  onToggle,
  disabled = false,
  label,
  className = "",
  size = "md"
}: ToggleProps) {
  const [isChecked, setIsChecked] = useState(isOn);

  const handleToggle = () => {
    if (disabled) return;

    const newState = !isChecked;
    setIsChecked(newState);
    onToggle(newState);
  };

  // Size classes
  const sizeClasses = {
    sm: {
      toggle: "w-9 h-5",
      circle: "w-3.5 h-3.5",
      translate: "translate-x-4"
    },
    md: {
      toggle: "w-12 h-6",
      circle: "w-5 h-5",
      translate: "translate-x-6"
    },
    lg: {
      toggle: "w-14 h-7",
      circle: "w-6 h-6",
      translate: "translate-x-7"
    }
  };

  const currentSize = sizeClasses[size];

  return (
    <div className={`flex items-center ${className}`}>
      {label && (
        <span className="mr-2 text-rv-text font-medium">{label}</span>
      )}
      <button
        type="button"
        className={`${currentSize.toggle} rounded-full relative inline-flex flex-shrink-0 cursor-pointer items-center
        ${isChecked ? "bg-rv-primary" : "bg-rv-surface/70"}
        ${disabled ? "opacity-50 cursor-not-allowed" : ""}
        transition-colors ease-in-out duration-200 focus:outline-none focus:ring-2 focus:ring-rv-primary focus:ring-offset-2`}
        onClick={handleToggle}
        disabled={disabled}
        aria-pressed={isChecked}
      >
        <span
          className={`${currentSize.circle} ${isChecked ? currentSize.translate : "translate-x-0.5"}
          bg-white rounded-full shadow-lg transform transition ease-in-out duration-200`}
        />
      </button>
    </div>
  );
}
