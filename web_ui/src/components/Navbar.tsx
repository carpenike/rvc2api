import { Button } from "@/components/ui/button";
import { NavigationMenu, NavigationMenuItem, NavigationMenuList } from "@/components/ui/navigation-menu";
import { cn } from "@/lib/utils";
import type { ReactNode } from "react";
import { useState } from "react";
import { Link, useLocation } from "react-router-dom";

/**
 * Props for the Navbar component
 */
interface NavbarProps {
  /** Optional current view identifier */
  currentView?: string;

  /** Optional children to render inside the component */
  children?: ReactNode;
}

/**
 * Navigation bar component for the application
 *
 * Provides navigation links to all main sections of the application
 * and handles responsive mobile navigation
 *
 * @param props - Component properties
 * @returns A React component
 */
export function Navbar(props: NavbarProps) {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();

  // Use provided currentView from props or get it from location path
  const currentView = props.currentView || location.pathname.split("/")[1] || "dashboard";

  const navItems = [
    { id: "dashboard", label: "Dashboard", path: "/dashboard" },
    { id: "lights", label: "Lights", path: "/lights" },
    { id: "mapping", label: "Device Mapping", path: "/mapping" },
    { id: "spec", label: "RVC Spec", path: "/spec" },
    { id: "documentation", label: "Documentation", path: "/documentation" },
    { id: "unmapped", label: "Unmapped Devices", path: "/unmapped" },
    { id: "unknownPgns", label: "Unknown PGNs", path: "/unknownPgns" },
    { id: "canSniffer", label: "CAN Sniffer", path: "/canSniffer" },
    { id: "networkMap", label: "Network Map", path: "/networkMap" }
  ];

  const toggleMenu = () => setIsOpen(!isOpen);

  return (
    <nav
      className="bg-card text-card-foreground px-4 py-3 rounded-xl mb-6 shadow-lg border transition-colors duration-200"
      aria-label="Main navigation"
      role="navigation"
      data-testid="navbar"
    >
      <div className="container mx-auto flex justify-between items-center">
        <div className="flex items-center">
          <span className="text-xl font-bold mr-8 text-foreground">RVC2API</span>

          {/* Desktop menu */}
          <NavigationMenu className="hidden md:flex">
            <NavigationMenuList className="space-x-2">
              {navItems.map((item) => (
                <NavigationMenuItem key={item.id}>
                  <Link
                    to={item.path}
                    className={cn(
                      "px-3 py-2 rounded-lg font-medium transition-colors duration-150 inline-flex items-center justify-center",
                      currentView === item.id
                        ? "bg-accent text-accent-foreground"
                        : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
                    )}
                    aria-current={currentView === item.id ? "page" : undefined}
                  >
                    {item.label}
                  </Link>
                </NavigationMenuItem>
              ))}
            </NavigationMenuList>
          </NavigationMenu>
        </div>

        {/* Mobile menu button */}
        <Button
          variant="ghost"
          size="sm"
          className="md:hidden p-2"
          onClick={toggleMenu}
          aria-label={isOpen ? "Close navigation menu" : "Open navigation menu"}
          aria-expanded={isOpen}
          aria-controls="mobile-nav-menu"
        >
          <svg
            className="h-6 w-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
          >
            {isOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </Button>
      </div>

      {/* Mobile menu */}
      {isOpen && (
        <div
          id="mobile-nav-menu"
          className="md:hidden mt-2 bg-card border rounded-lg shadow-lg p-4"
          role="menu"
        >
          {navItems.map((item) => (
            <Link
              key={item.id}
              to={item.path}
              className={cn(
                "block px-3 py-2 rounded-lg font-medium mb-1 transition-colors duration-150",
                currentView === item.id
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
              )}
              aria-current={currentView === item.id ? "page" : undefined}
              role="menuitem"
              tabIndex={0}
              onClick={() => setIsOpen(false)}
            >
              {item.label}
            </Link>
          ))}
        </div>
      )}
      {props.children}
    </nav>
  );
}
