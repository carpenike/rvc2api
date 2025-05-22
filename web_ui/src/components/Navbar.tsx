import clsx from "clsx";
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
      className="bg-rv-surface text-rv-text px-4 py-3 rounded-xl mb-6 shadow-lg border border-rv-border transition-colors duration-200"
      aria-label="Main navigation"
      role="navigation"
      data-testid="navbar"
    >
      <div className="container mx-auto flex justify-between items-center">
        <div className="flex items-center">
          <span className="text-xl font-bold mr-8 text-rv-heading">RVC2API</span>

          {/* Desktop menu */}
          <div className="hidden md:flex space-x-4" role="menubar">
            {navItems.map((item) => (
              <Link
                key={item.id}
                to={item.path}
                className={clsx(
                  "px-3 py-2 rounded-lg font-medium focus:outline-none focus:ring-2 focus:ring-rv-primary transition-colors duration-150",
                  currentView === item.id
                    ? "bg-rv-primary/20 text-rv-primary"
                    : "hover:bg-rv-primary/10 hover:text-rv-primary text-rv-text"
                )}
                aria-current={currentView === item.id ? "page" : undefined}
                role="menuitem"
                tabIndex={0}
              >
                {item.label}
              </Link>
            ))}
          </div>
        </div>

        {/* Mobile menu button */}
        <button
          className="md:hidden p-2 rounded focus:outline-none focus:ring-2 focus:ring-rv-primary text-rv-text"
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
        </button>
      </div>

      {/* Mobile menu */}
      {isOpen && (
        <div
          id="mobile-nav-menu"
          className="md:hidden mt-2 bg-rv-surface border border-rv-border rounded-lg shadow-lg p-4"
          role="menu"
        >
          {navItems.map((item) => (
            <Link
              key={item.id}
              to={item.path}
              className={clsx(
                "block px-3 py-2 rounded-lg font-medium mb-1 focus:outline-none focus:ring-2 focus:ring-rv-primary transition-colors duration-150",
                currentView === item.id
                  ? "bg-rv-primary/20 text-rv-primary"
                  : "hover:bg-rv-primary/10 hover:text-rv-primary text-rv-text"
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
