// src/components/AppSidebar.tsx

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
import { cn } from "@/lib/utils";
import {
  AlertCircle,
  Database,
  FileText,
  HelpCircle,
  LayoutDashboard,
  Lightbulb,
  Map,
  Network,
  Palette,
  User
} from "lucide-react";
import type { ReactNode } from "react";
import { useLocation, useNavigate } from "react-router-dom";

interface NavItem {
  id: string;
  label: string;
  path: string;
  icon: ReactNode;
}

const navMain: NavItem[] = [
  { id: "dashboard", label: "Dashboard", path: "/dashboard", icon: <LayoutDashboard size={20} /> },
  { id: "lights",    label: "Lights",    path: "/lights",    icon: <Lightbulb size={20} /> },
  { id: "mapping",   label: "Device Mapping", path: "/mapping",   icon: <Map size={20} /> },
  { id: "networkMap",label: "Network Map",   path: "/networkMap",icon: <Map size={20} /> }
];

const navSecondary: NavItem[] = [
  { id: "spec",           label: "RVC Spec",     path: "/spec",           icon: <FileText size={20} /> },
  { id: "documentation",  label: "Documentation",path: "/documentation", icon: <HelpCircle size={20} /> }
];

const navDeveloper: NavItem[] = [
  { id: "unmapped",    label: "Unmapped Devices", path: "/unmapped",    icon: <AlertCircle size={20} /> },
  { id: "unknownPgns", label: "Unknown PGNs",     path: "/unknownPgns", icon: <Database size={20} /> },
  { id: "canSniffer",  label: "CAN Sniffer",      path: "/canSniffer",  icon: <Network size={20} /> },
  { id: "themeTest",   label: "Theme Test",       path: "/themeTest",   icon: <Palette size={20} /> }
];

interface AppSidebarProps {
  wsStatus?: string;
  className?: string;
}

export function AppSidebar({ wsStatus, className }: AppSidebarProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const currentPath = location.pathname;

  const renderNavMenu = (items: NavItem[]) => (
    <SidebarMenu>
      {items.map((item) => {
        const isActive = currentPath === item.path;
        return (
          <SidebarMenuItem key={item.id}>
            <SidebarMenuButton
              onClick={() => navigate(item.path)}
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
    <Sidebar
      variant="inset"             // ⟵ tells SidebarInset to auto-offset
      collapsible="icon"
      openWidth="16rem"            // ⟵ expanded width
      collapsedWidth="4rem"        // ⟵ collapsed width
      className={cn(
        "bg-background border-r border-border !border-0",
        className
      )}
    >
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <div className="flex items-center">
                <div className="flex aspect-square w-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                  <LayoutDashboard className="w-4 h-4" />
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

      <SidebarContent className="!px-0 overflow-y-auto overflow-x-hidden">
        <SidebarGroup>
          <SidebarGroupLabel>Main</SidebarGroupLabel>
          <SidebarGroupContent>
            {renderNavMenu(navMain)}
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarSeparator />

        <SidebarGroup>
          <SidebarGroupLabel>Resources</SidebarGroupLabel>
          <SidebarGroupContent>
            {renderNavMenu(navSecondary)}
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup className="mt-auto">
          <SidebarGroupLabel>Developer Tools</SidebarGroupLabel>
          <SidebarGroupContent>
            {renderNavMenu(navDeveloper)}
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <SidebarMenu>
          {wsStatus && (
            <SidebarMenuItem>
              <div className="flex items-center gap-2 px-2 py-1.5">
                <div className="w-2 h-2 rounded-full bg-green-500" />
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
