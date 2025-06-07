import { type Icon } from "@tabler/icons-react"
import * as React from "react"
import { Link } from "react-router-dom"

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
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  )
}
