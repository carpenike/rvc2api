import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { cn } from "@/lib/utils";

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
  // Size variants for the switch
  const sizeVariants = {
    sm: "h-4 w-7 [&>span]:h-3 [&>span]:w-3 [&[data-state=checked]>span]:translate-x-3",
    md: "h-5 w-9 [&>span]:h-4 [&>span]:w-4 [&[data-state=checked]>span]:translate-x-4", // default
    lg: "h-6 w-12 [&>span]:h-5 [&>span]:w-5 [&[data-state=checked]>span]:translate-x-6"
  };

  const switchId = id || "toggle-switch";

  return (
    <div className={cn("flex items-center space-x-2", className)}>
      {label && (
        <Label htmlFor={switchId} className="text-sm font-medium">
          {label}
        </Label>
      )}
      <Switch
        id={switchId}
        checked={isOn}
        onCheckedChange={onToggle}
        disabled={disabled}
        className={cn(size !== "md" && sizeVariants[size])}
        data-testid="toggle-switch"
        aria-label={label || "Toggle"}
      />
    </div>
  );
}
