import { Badge } from "@/components/ui/badge";
import {
    Sidebar,
    SidebarContent,
    SidebarHeader,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
    useSidebar
} from "@/components/ui/sidebar";
import {
    AlertCircle,
    Database,
    FileText,
    HelpCircle,
    LayoutDashboard,
    Lightbulb,
    Map,
    Network
} from "lucide-react";
import type { ReactNode } from "react";
import { useLocation, useNavigate } from "react-router-dom";

/**
 * Navigation item structure
 */
interface NavItem {
  id: string;
  label: string;
  path: string;
  icon: ReactNode;
}

/**
 * Navigation items configuration
 */
const navItems: NavItem[] = [
  { id: "dashboard", label: "Dashboard", path: "/dashboard", icon: <LayoutDashboard size={20} /> },
  { id: "lights", label: "Lights", path: "/lights", icon: <Lightbulb size={20} /> },
  { id: "mapping", label: "Device Mapping", path: "/mapping", icon: <Map size={20} /> },
  { id: "spec", label: "RVC Spec", path: "/spec", icon: <FileText size={20} /> },
  { id: "documentation", label: "Documentation", path: "/documentation", icon: <HelpCircle size={20} /> },
  { id: "unmapped", label: "Unmapped Devices", path: "/unmapped", icon: <AlertCircle size={20} /> },
  { id: "unknownPgns", label: "Unknown PGNs", path: "/unknownPgns", icon: <Database size={20} /> },
  { id: "canSniffer", label: "CAN Sniffer", path: "/canSniffer", icon: <Network size={20} /> },
  { id: "networkMap", label: "Network Map", path: "/networkMap", icon: <Map size={20} /> }
];

/**
 * Props for the AppSidebar component
 */
interface AppSidebarProps {
  /** WebSocket status indicator */
  wsStatus?: string;
}

/**
 * Main application sidebar using shadcn/ui v4 sidebar components
 *
 * Features:
 * - Responsive design with mobile support
 * - Collapsible functionality via SidebarProvider context
 * - Icon-based navigation with labels
 * - Active state management
 * - Built-in accessibility and keyboard navigation
 */
export function AppSidebar({ wsStatus }: AppSidebarProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const { state } = useSidebar();

  // Get current active route
  const currentPath = location.pathname;

  /**
   * Handle navigation to a route
   */
  const handleNavigation = (path: string) => {
    navigate(path);
  };

  /**
   * Get WebSocket status display
   */
  const getWsStatusBadge = () => {
    if (!wsStatus) return null;

    const variant = wsStatus === "Connected" ? "default" : "destructive";
    return <Badge variant={variant} className="text-xs">{wsStatus}</Badge>;
  };

  return (
    <Sidebar>
      <SidebarHeader className="border-b border-sidebar-border">
        <div className="flex items-center gap-2 px-2 py-3">
          <div className="flex items-center gap-2 font-semibold">
            <LayoutDashboard size={20} className="text-sidebar-primary" />
            {state === "expanded" && (
              <span className="text-sidebar-foreground">RVC2API</span>
            )}
          </div>
          {state === "expanded" && wsStatus && (
            <div className="ml-auto">
              {getWsStatusBadge()}
            </div>
          )}
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarMenu>
          {navItems.map((item) => {
            const isActive = currentPath === item.path;

            return (
              <SidebarMenuItem key={item.id}>
                <SidebarMenuButton
                  onClick={() => handleNavigation(item.path)}
                  isActive={isActive}
                  tooltip={state === "collapsed" ? item.label : undefined}
                  className="w-full"
                >
                  <div className="flex items-center gap-3 w-full">
                    <span className="flex-shrink-0">{item.icon}</span>
                    {state === "expanded" && (
                      <span className="flex-1 text-left">{item.label}</span>
                    )}
                  </div>
                </SidebarMenuButton>
              </SidebarMenuItem>
            );
          })}
        </SidebarMenu>
      </SidebarContent>
    </Sidebar>
  );
}
