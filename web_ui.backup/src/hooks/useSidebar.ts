import { useContext } from "react";
import { SidebarContext } from "@/contexts/sidebar-context";

export const useSidebar = () => {
  const ctx = useContext(SidebarContext);
  if (!ctx) throw new Error("useSidebar must be inside <SidebarProvider>");
  return ctx;
};
