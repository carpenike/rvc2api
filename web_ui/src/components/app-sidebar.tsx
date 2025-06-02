import {
    IconBulb,
    IconChartBar,
    IconCircuitSwitchOpen,
    IconCpu,
    IconDashboard,
    IconFileDescription,
    IconFileWord,
    IconHelp,
    IconInnerShadowTop,
    IconListDetails,
    IconMapPin,
    IconQuestionMark,
    IconSettings,
    IconWifi,
} from "@tabler/icons-react"
import * as React from "react"

import { NavDocuments } from "@/components/nav-documents"
import { NavMain } from "@/components/nav-main"
import { NavSecondary } from "@/components/nav-secondary"
import { NavSection } from "@/components/nav-section"
import { NavUser } from "@/components/nav-user"
import {
    Sidebar,
    SidebarContent,
    SidebarFooter,
    SidebarHeader,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
} from "@/components/ui/sidebar"

const data = {
  user: {
    name: "RV-C User",
    email: "user@rvc2api.local",
    avatar: "/avatars/shadcn.jpg",
  },
  navMain: [
    {
      title: "Dashboard",
      url: "/dashboard",
      icon: IconDashboard,
    },
    {
      title: "Demo Dashboard",
      url: "/demo-dashboard",
      icon: IconChartBar,
    },
    {
      title: "Lights",
      url: "/lights",
      icon: IconBulb,
    },
    {
      title: "Device Mapping",
      url: "/device-mapping",
      icon: IconCpu,
    },
  ],
  navMonitoring: [
    {
      title: "CAN Sniffer",
      url: "/can-sniffer",
      icon: IconWifi,
    },
    {
      title: "Network Map",
      url: "/network-map",
      icon: IconMapPin,
    },
  ],
  navDiagnostics: [
    {
      title: "Unknown PGNs",
      url: "/unknown-pgns",
      icon: IconQuestionMark,
    },
    {
      title: "Unmapped Entries",
      url: "/unmapped-entries",
      icon: IconCircuitSwitchOpen,
    },
  ],
  navSecondary: [
    {
      title: "Documentation",
      url: "/documentation",
      icon: IconFileDescription,
    },
    {
      title: "RV-C Spec",
      url: "/rvc-spec",
      icon: IconFileWord,
    },
    {
      title: "Theme Test",
      url: "/theme-test",
      icon: IconSettings,
    },
  ],
  documents: [
    {
      name: "System Status",
      url: "#",
      icon: IconListDetails,
    },
    {
      name: "Configuration",
      url: "#",
      icon: IconSettings,
    },
    {
      name: "Help",
      url: "#",
      icon: IconHelp,
    },
  ],
}

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  return (
    <Sidebar collapsible="offcanvas" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              className="data-[slot=sidebar-menu-button]:!p-1.5"
            >
              <IconInnerShadowTop className="!size-5" />
              <span className="text-base font-semibold">RV-C2API</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={data.navMain} />
        <NavSection
          title="Monitoring"
          items={data.navMonitoring}
          className="mt-4"
        />
        <NavSection
          title="Diagnostics"
          items={data.navDiagnostics}
          className="mt-4"
        />
        <NavDocuments items={data.documents} />
        <NavSecondary items={data.navSecondary} className="mt-auto" />
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={data.user} />
      </SidebarFooter>
    </Sidebar>
  )
}
