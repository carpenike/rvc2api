// src/components/Layout.tsx

import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger
} from "@/components/ui/sidebar";
import { useState } from "react";
import { AppSidebar } from "../components/AppSidebar";
import { ThemeSelector } from "../components/ThemeSelector";

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <SidebarProvider>
      <LayoutContent>{children}</LayoutContent>
    </SidebarProvider>
  );
}

function LayoutContent({ children }: { children: React.ReactNode }) {
  const [wsStatus] = useState("Connected");

  return (
    <>
      {/* Sidebar (variant="inset" inside AppSidebar will handle offset) */}
      <AppSidebar wsStatus={wsStatus} />

      {/* Content area auto-offset by sidebar width */}
      <SidebarInset className="flex flex-col h-screen overflow-hidden">
        {/* Header */}
        <header className="flex h-14 items-center gap-2 border-b border-border bg-background px-4">
          <SidebarTrigger />
          <h1 className="text-lg font-semibold">RV-C API</h1>
          <div className="ml-auto">
            <ThemeSelector />
          </div>
        </header>

        {/* Main: scrollable */}
        <main className="flex-1 overflow-auto">
          {children}
        </main>

        {/* Footer */}
        <footer className="border-t border-border bg-background px-4 py-2">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>WebSocket: {wsStatus}</span>
            <span>© 2024 RV-C API</span>
          </div>
        </footer>
      </SidebarInset>
    </>
  );
}

export default Layout;
