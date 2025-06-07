import { AppSidebar } from "@/components/app-sidebar"
import { SiteHeader } from "@/components/site-header"
import {
  SidebarInset,
  SidebarProvider,
} from "@/components/ui/sidebar"
import * as React from "react"

interface AppLayoutProps {
  children: React.ReactNode
  pageTitle?: string
  sidebarVariant?: "inset" | "sidebar" | "floating"
}

function AppFooter() {
  return (
    <footer className="border-t bg-background px-6 py-4">
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <p>&copy; 2025 RV-C2API. All rights reserved.</p>
        <p>Version 1.0.0</p>
      </div>
    </footer>
  )
}

export function AppLayout({
  children,
  pageTitle = "Application",
  sidebarVariant = "inset"
}: AppLayoutProps) {
  return (
    <SidebarProvider
      style={
        {
          "--sidebar-width": "calc(var(--spacing) * 72)",
          "--header-height": "calc(var(--spacing) * 12)",
        } as React.CSSProperties
      }
    >
      <AppSidebar variant={sidebarVariant} />
      <SidebarInset>
        <SiteHeader pageTitle={pageTitle} />
        <div className="flex flex-1 flex-col min-h-[calc(100vh-var(--header-height))]">
          <main className="@container/main flex flex-1 flex-col gap-2">
            {children}
          </main>
          <AppFooter />
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}
