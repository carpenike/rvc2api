import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarSeparator
} from "@/components/ui/sidebar";
import {
  AlertCircle,
  Database,
  FileText,
  HelpCircle,
  LayoutDashboard,
  Lightbulb,
  Map,
  Network,
  User
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
const navMain: NavItem[] = [
  { id: "dashboard", label: "Dashboard", path: "/dashboard", icon: <LayoutDashboard size={20} /> },
  { id: "lights", label: "Lights", path: "/lights", icon: <Lightbulb size={20} /> },
  { id: "mapping", label: "Device Mapping", path: "/mapping", icon: <Map size={20} /> },
  { id: "networkMap", label: "Network Map", path: "/networkMap", icon: <Map size={20} /> }
];

const navSecondary: NavItem[] = [
  { id: "spec", label: "RVC Spec", path: "/spec", icon: <FileText size={20} /> },
  { id: "documentation", label: "Documentation", path: "/documentation", icon: <HelpCircle size={20} /> }
];

const navDeveloper: NavItem[] = [
  { id: "unmapped", label: "Unmapped Devices", path: "/unmapped", icon: <AlertCircle size={20} /> },
  { id: "unknownPgns", label: "Unknown PGNs", path: "/unknownPgns", icon: <Database size={20} /> },
  { id: "canSniffer", label: "CAN Sniffer", path: "/canSniffer", icon: <Network size={20} /> }
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
 * - Organized navigation groups following v4 patterns
 */
export function AppSidebar({ wsStatus }: AppSidebarProps) {
  const location = useLocation();
  const navigate = useNavigate();

  // Get current active route
  const currentPath = location.pathname;

  /**
   * Handle navigation to a route
   */
  const handleNavigation = (path: string) => {
    navigate(path);
  };

  /**
   * Render navigation menu from items array
   */
  const renderNavMenu = (items: NavItem[]) => (
    <SidebarMenu>
      {items.map((item) => {
        const isActive = currentPath === item.path;
        return (
          <SidebarMenuItem key={item.id}>
            <SidebarMenuButton
              onClick={() => handleNavigation(item.path)}
              isActive={isActive}
              tooltip={item.label}
            >
              {item.icon}
              <span>{item.label}</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        );
      })}
    </SidebarMenu>
  );

  return (
    <Sidebar collapsible="icon" className="!border-0">
      {/* Header with app branding */}
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <div className="flex items-center">
                <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                  <LayoutDashboard className="size-4" />
                </div>
                <div className="flex flex-col gap-0.5 leading-none">
                  <span className="font-semibold">RVC2API</span>
                  <span className="text-xs">Control System</span>
                </div>
              </div>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      {/* Main content with navigation groups */}
      <SidebarContent className="!px-0 overflow-y-auto overflow-x-hidden">
        {/* Main navigation */}
        <SidebarGroup>
          <SidebarGroupLabel>Main</SidebarGroupLabel>
          <SidebarGroupContent>
            {renderNavMenu(navMain)}
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarSeparator />

        {/* Secondary navigation */}
        <SidebarGroup>
          <SidebarGroupLabel>Resources</SidebarGroupLabel>
          <SidebarGroupContent>
            {renderNavMenu(navSecondary)}
          </SidebarGroupContent>
        </SidebarGroup>

        {/* Developer tools - using mt-auto to push to bottom */}
        <SidebarGroup className="mt-auto">
          <SidebarGroupLabel>Developer Tools</SidebarGroupLabel>
          <SidebarGroupContent>
            {renderNavMenu(navDeveloper)}
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      {/* Footer with status and user info */}
      <SidebarFooter>
        <SidebarMenu>
          {wsStatus && (
            <SidebarMenuItem>
              <div className="flex items-center gap-2 px-2 py-1.5">
                <div className="size-2 rounded-full bg-green-500" />
                <span className="text-sm text-muted-foreground">
                  {wsStatus}
                </span>
              </div>
            </SidebarMenuItem>
          )}
          <SidebarMenuItem>
            <SidebarMenuButton>
              <User />
              <span>Settings</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
