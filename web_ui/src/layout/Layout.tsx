import { Badge } from "@/components/ui/badge";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import type { ReactNode } from "react";
import React from "react";
import { AppSidebar } from "../components/AppSidebar";
import Footer from "../components/Footer";
import { ThemeSelector } from "../components/ThemeSelector";

interface LayoutProps {
  children: ReactNode;
  wsStatus?: string;
}

const Layout: React.FC<LayoutProps> = ({ children, wsStatus }) => {
  /**
   * Get WebSocket status display
   */
  const getWsStatusBadge = () => {
    if (!wsStatus) return null;

    const variant = wsStatus === "Connected" ? "default" : "destructive";
    return <Badge variant={variant} className="text-xs">{wsStatus}</Badge>;
  };

  return (
    <SidebarProvider>
      <AppSidebar wsStatus={wsStatus} />
      <SidebarInset>
        {/* Header with integrated sidebar trigger */}
        <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="-ml-1" />
          <div className="flex flex-1 items-center justify-between">
            <div className="flex items-center">
              <span className="text-xl font-bold">RVC2API</span>
            </div>
            <div className="flex items-center space-x-4">
              {wsStatus && (
                <div className="flex items-center space-x-3" aria-live="polite">
                  <span className="sr-only" id="ws-status-label">WebSocket status:</span>
                  {getWsStatusBadge()}
                </div>
              )}
              <ThemeSelector />
            </div>
          </div>
        </header>

        {/* Main content area */}
        <main className="flex flex-1 flex-col gap-4 p-4 lg:gap-6 lg:p-6">
          {children}
        </main>

        {/* Footer */}
        <Footer />
      </SidebarInset>
    </SidebarProvider>
  );
};

export default Layout;
