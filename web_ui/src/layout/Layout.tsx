import { Badge } from "@/components/ui/badge";
import { SidebarProvider } from "@/components/ui/sidebar";
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
  const getWsStatusBadge = () => {
    if (!wsStatus) return null;
    const variant = wsStatus === "Connected" ? "default" : "destructive";
    return <Badge variant={variant} className="text-xs">{wsStatus}</Badge>;
  };

  return (
    <SidebarProvider>
      {/* full-bleed root, one divider between sidebar & main */}
      <div className="flex h-screen w-full overflow-hidden divide-x divide-border bg-background">
        {/* Sidebar */}
        <aside className="w-64 flex-shrink-0 hidden md:flex md:flex-col bg-background overflow-x-hidden">
          <AppSidebar wsStatus={wsStatus} />
        </aside>

        {/* Main column */}
        <div className="flex flex-col flex-1 w-full min-w-0 overflow-hidden bg-background">
          {/* Header */}
          <header className="flex h-16 items-center justify-between border-b border-border px-4">
            <h1 className="text-xl font-bold">RVC2API</h1>
            <div className="flex items-center space-x-4">
              {wsStatus && (
                <div
                  className="flex items-center space-x-2"
                  aria-live="polite"
                  aria-label={`WebSocket status: ${wsStatus}`}
                >
                  {getWsStatusBadge()}
                </div>
              )}
              <ThemeSelector />
            </div>
          </header>

          {/* Scrollable content */}
          <main className="flex-1 w-full min-w-0 overflow-y-auto p-4 md:p-6">
            {children}
          </main>

          {/* Footer */}
          <div className="w-full">
            <Footer />
          </div>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default Layout;
