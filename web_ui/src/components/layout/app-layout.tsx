import * as React from "react"

import { cn } from "@/lib/utils"

export interface AppLayoutProps {
  children: React.ReactNode
  className?: string
}

const AppLayout = React.forwardRef<HTMLDivElement, AppLayoutProps>(
  ({ children, className, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "min-h-screen bg-background font-sans antialiased",
          className
        )}
        {...props}
      >
        {children}
      </div>
    )
  }
)
AppLayout.displayName = "AppLayout"

export { AppLayout }
