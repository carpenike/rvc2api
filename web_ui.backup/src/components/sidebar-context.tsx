import { createContext, useEffect, useState } from "react";

type SidebarCtx = { collapsed: boolean; toggle: () => void };

const SidebarContext = createContext<SidebarCtx | null>(null);

export function SidebarProvider({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState<boolean>(() =>
    localStorage.getItem("sidebar-collapsed") === "true"
  );

  useEffect(() => {
    localStorage.setItem("sidebar-collapsed", String(collapsed));
  }, [collapsed]);

  return (
    <SidebarContext.Provider
      value={{ collapsed, toggle: () => setCollapsed((c) => !c) }}
    >
      {children}
    </SidebarContext.Provider>
  );
}
