import { useTheme } from "@/hooks/use-theme"
import type { ToasterProps } from "sonner"
import { Toaster as Sonner } from "sonner"

const Toaster = ({ ...props }: ToasterProps) => {
  const { theme = "system" } = useTheme()

  const { theme: propsTheme, ...restProps } = props

  const sonnerProps: ToasterProps = {
    className: "toaster group",
    style: {
      "--normal-bg": "var(--popover)",
      "--normal-text": "var(--popover-foreground)",
      "--normal-border": "var(--border)",
    } as React.CSSProperties,
    ...restProps,
  }

  // Use props theme if provided, otherwise use theme hook
  const effectiveTheme = propsTheme || theme
  if (effectiveTheme && effectiveTheme !== "system" && effectiveTheme !== undefined) {
    sonnerProps.theme = effectiveTheme
  } else if (effectiveTheme === "system") {
    sonnerProps.theme = "system"
  }

  return <Sonner {...sonnerProps} />
}

export { Toaster }
