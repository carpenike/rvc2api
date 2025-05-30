import { SidebarProvider } from "@/components/ui/sidebar";
import { Outlet } from "react-router-dom";
import { MainNav } from "./main-nav";
import { SideNav } from "./side-nav";

export default function RootLayout() {
  return (
    <SidebarProvider>
      <div className="flex h-screen w-full overflow-hidden divide-x divide-border">
        <SideNav />

        {/* main column */}
        <div className="flex flex-1 flex-col">
          <MainNav />
          <main className="flex-1 overflow-auto bg-background p-6">
            <Outlet />
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}
