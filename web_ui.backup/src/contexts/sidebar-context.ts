import { createContext } from "react";

export type SidebarContextProps = {
  state: "expanded" | "collapsed"
  open: boolean
  setOpen: (open: boolean) => void
  openMobile: boolean
  setOpenMobile: (open: boolean) => void
  isMobile: boolean
  toggleSidebar: () => void
  // Legacy properties for backward compatibility
  collapsed: boolean
  toggle: () => void
}

export const SidebarContext = createContext<SidebarContextProps | null>(null);
