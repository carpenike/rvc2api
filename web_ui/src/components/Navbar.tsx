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
    <nav className="bg-rv-surface text-rv-text px-4 py-3 rounded-xl mb-6 shadow-lg">
      <div className="container mx-auto flex justify-between items-center">
        <div className="flex items-center">
          <span className="text-xl font-bold mr-8">RVC2API</span>

          {/* Desktop menu */}
          <div className="hidden md:flex space-x-4">
            {navItems.map((item) => (
              <Link
                key={item.id}
                to={item.path}
                className={`px-3 py-2 rounded-lg transition-colors ${
                  currentView === item.id
                    ? "bg-rv-primary text-white"
                    : "hover:bg-rv-surface/80"
                }`}
              >
                {item.label}
              </Link>
            ))}
          </div>
        </div>

        {/* Mobile menu button */}
        <div className="md:hidden">
          <button
            onClick={toggleMenu}
            className="focus:outline-none"
            aria-label="Toggle menu"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              {isOpen ? (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              ) : (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {isOpen && (
        <div className="md:hidden mt-3 pt-3 border-t border-rv-surface/20">
          <div className="flex flex-col space-y-2">
            {navItems.map((item) => (
              <Link
                key={item.id}
                to={item.path}
                onClick={() => setIsOpen(false)}
                className={`px-3 py-2 rounded-lg transition-colors ${
                  currentView === item.id
                    ? "bg-rv-primary text-white"
                    : "hover:bg-rv-surface/80"
                }`}
              >
                {item.label}
              </Link>
            ))}
          </div>
        </div>
      )}
    </nav>
  );
}
