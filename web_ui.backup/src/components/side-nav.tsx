import { useSidebar } from "@/hooks/useSidebar";
import { UserNav } from "@/components/user-nav";
import { mainLinks } from "@/lib/navigation";
import { ChevronLeft, ChevronRight, Package2 } from "lucide-react";
import { Link, useLocation } from "react-router-dom";

function CollapseToggle() {
  const { collapsed, toggle } = useSidebar();
  return (
    <button
      onClick={toggle}
      className="flex h-8 w-8 items-center justify-center rounded-md hover:bg-muted/50"
    >
      {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
    </button>
  );
}

/* --- Brand row now includes toggle --------------- */
export function SidebarBrand() {
  const { collapsed } = useSidebar();
  return (
    <div className="flex items-center justify-between p-4">
      <Link to="/" className="flex items-center gap-2 text-lg font-semibold">
        <Package2 className="h-5 w-5" />
        {!collapsed && <span>My&nbsp;App</span>}
      </Link>
      <CollapseToggle />
    </div>
  );
}

/* ─── LINKS ─────────────────────────────────────────────────── */
export function NavLinks() {
  const { collapsed } = useSidebar();
  const location = useLocation();
  return (
    <nav className="flex flex-col gap-2 p-4 pt-0"> {/* pt-0 so brand controls top padding */}
      {mainLinks.map((link) => (
        <Link
          key={link.href}
          to={link.href}
          className={`flex items-center gap-3 rounded-md p-2 text-sm font-medium ${
            location.pathname === link.href ? "bg-muted" : "hover:bg-muted/50"
          }`}
        >
          {link.icon && <link.icon className="h-4 w-4" />}
          {!collapsed && link.title}
        </Link>
      ))}
    </nav>
  );
}

/* ─── USER PANEL ────────────────────────────────────────────── */
export function UserFooter() {
  return (
    <div className="mt-auto p-2">
      <UserNav />
    </div>
  );
}

/* ─── DESKTOP SIDEBAR ───────────────────────────────────────── */
export function SideNav() {
  const { collapsed } = useSidebar();
  return (
    <aside
      className={`hidden h-full flex-col border-r transition-all duration-200 md:flex
        ${collapsed ? "w-14" : "w-56"}`}
    >
      <SidebarBrand />
      <NavLinks />
      <UserFooter />
    </aside>
  );
}
