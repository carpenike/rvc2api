import { type Icon } from "@tabler/icons-react"
import * as React from "react"
import { Link } from "react-router-dom"

import { LogDrawer } from "@/components/log-viewer/LogDrawer"
import {
    SidebarGroup,
    SidebarGroupContent,
    SidebarGroupLabel,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
} from "@/components/ui/sidebar"

interface DiagnosticsItem {
  title: string
  url: string
  icon: Icon
  drawer?: boolean
  badge?: boolean
}

interface NavDiagnosticsProps {
  title: string
  items: DiagnosticsItem[]
  className?: string
}

export function NavDiagnostics({ title, items, className, ...props }: NavDiagnosticsProps & React.ComponentPropsWithoutRef<typeof SidebarGroup>) {
  return (
    <SidebarGroup className={className} {...props}>
      <SidebarGroupLabel>{title}</SidebarGroupLabel>
      <SidebarGroupContent>
        <SidebarMenu>
          {items.map((item) => (
            <SidebarMenuItem key={item.title}>
              {item.drawer ? (
                // Live Logs: Render LogDrawer as a sidebar button
                <LogDrawer
                  websocketUrl="/ws/logs"
                  apiEndpoint="/api/logs"
                  asChild
                  trigger={
                    <SidebarMenuButton tooltip={item.title} className="w-full justify-start">
                      <item.icon />
                      <span>{item.title}</span>
                    </SidebarMenuButton>
                  }
                />
              ) : (
                // Regular navigation items
                <SidebarMenuButton tooltip={item.title} asChild>
                  <Link to={item.url}>
                    <item.icon />
                    <span>{item.title}</span>
                    {item.badge && (
                      <span className="ml-auto inline-flex items-center rounded bg-destructive px-2 py-0.5 text-xs font-semibold text-destructive-foreground">
                        Err
                      </span>
                    )}
                  </Link>
                </SidebarMenuButton>
              )}
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  )
}
