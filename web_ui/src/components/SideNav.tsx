import {
  AlertCircle,
  ChevronRight,
  Database,
  FileText,
  HelpCircle,
  LayoutDashboard,
  Lightbulb,
  Map,
  Menu,
  Network,
  X
} from "lucide-react";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";

/**
 * Props for the SideNav component
 */
interface SideNavProps {
  /** Optional current view identifier */
  currentView?: string;

  /** WebSocket status indicator */
  wsStatus?: string;
}

/**
 * Navigation item structure
 */
interface NavItem {
  id: string;
  label: string;
  path: string;
  icon: ReactNode;
}

/**
 * Sidebar navigation component for the application with responsive design
 *
 * Desktop: Shows as a sidebar that can be collapsed to icons only
 * Mobile: Hidden by default, shows as a slide-in menu when toggled
 *
 * @param props - Component properties
 * @returns A React component
 */
export function SideNav({ currentView: propCurrentView, wsStatus }: SideNavProps) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const location = useLocation();

  // Use provided currentView from props or get it from location path
  const currentView = propCurrentView || location.pathname.split("/")[1] || "dashboard";

  // Navigation items with icons
  const navItems: NavItem[] = [
    { id: "dashboard", label: "Dashboard", path: "/dashboard", icon: <LayoutDashboard size={20} /> },
    { id: "lights", label: "Lights", path: "/lights", icon: <Lightbulb size={20} /> },
    { id: "mapping", label: "Device Mapping", path: "/mapping", icon: <Map size={20} /> },
    { id: "spec", label: "RVC Spec", path: "/spec", icon: <FileText size={20} /> },
    { id: "documentation", label: "Documentation", path: "/documentation", icon: <HelpCircle size={20} /> },
    { id: "unmapped", label: "Unmapped Devices", path: "/unmapped", icon: <AlertCircle size={20} /> },
    { id: "unknownPgns", label: "Unknown PGNs", path: "/unknownPgns", icon: <Database size={20} /> },
    { id: "canSniffer", label: "CAN Sniffer", path: "/canSniffer", icon: <Network size={20} /> },
    { id: "networkMap", label: "Network Map", path: "/networkMap", icon: <Map size={20} /> }
  ];

  // Close mobile menu when location changes
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [location]);

  // Check if we're on mobile based on window width
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 1024) {
        setIsCollapsed(true);
      }
    };

    handleResize(); // Initial check
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return (
    <>
      {/* Mobile header with menu button */}
      <div className="lg:hidden flex items-center justify-between bg-rv-surface text-rv-text p-4 rounded-xl mb-4 shadow-lg">
        <div className="flex items-center">
          <span className="text-xl font-bold">RVC2API</span>
        </div>
        <div className="flex items-center space-x-3">
          {/* WebSocket status indicator - mobile only */}
          {wsStatus && (
            <div className="flex items-center space-x-2">
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                wsStatus === "open"
                  ? "bg-rv-success/20 text-rv-success"
                  : wsStatus === "connecting"
                  ? "bg-rv-warning/20 text-rv-warning"
                  : "bg-rv-error/20 text-rv-error"
              }`}>
                {wsStatus}
              </span>
            </div>
          )}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="p-2 rounded-lg hover:bg-rv-surface/80"
            aria-label="Toggle menu"
          >
            {isMobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* Mobile menu overlay */}
      {isMobileMenuOpen && (
        <div className="lg:hidden fixed inset-0 bg-rv-background/80 backdrop-blur-sm z-40" onClick={() => setIsMobileMenuOpen(false)}></div>
      )}

      {/* Sidebar navigation - hidden on mobile unless menu is open */}
      <div
        className={`
          fixed lg:sticky top-0 lg:top-4 z-50 lg:z-auto
          h-screen lg:h-[calc(100vh-2rem)]
          transition-all duration-300 ease-in-out
          ${isMobileMenuOpen ? "left-0" : "-left-64 lg:left-0"}
          ${isCollapsed ? "lg:w-16" : "lg:w-64"} w-64
        `}
      >
        <div className="bg-rv-surface text-rv-text h-full rounded-r-3xl lg:rounded-3xl p-4 shadow-lg flex flex-col">
          {/* Logo section - hidden on desktop as it's in the main header */}
          <div className="flex lg:hidden items-center justify-between mb-6 pb-4 border-b border-rv-surface/20">
            <span className="text-xl font-bold">RVC2API</span>
            <button
              onClick={() => setIsMobileMenuOpen(false)}
              className="p-2 rounded-lg hover:bg-rv-surface/80"
              aria-label="Close menu"
            >
              <X size={20} />
            </button>
          </div>

          {/* Navigation items */}
          <div className="flex flex-col space-y-2 overflow-y-auto flex-1">
            {navItems.map((item) => (
              <Link
                key={item.id}
                to={item.path}
                className={`
                  flex items-center space-x-3 px-4 py-3 rounded-xl transition-all
                  ${currentView === item.id
                    ? "bg-rv-primary text-white"
                    : "hover:bg-rv-surface/80"
                  }
                  ${isCollapsed && !isMobileMenuOpen ? "justify-center" : ""}
                `}
                title={isCollapsed ? item.label : undefined}
              >
                <span className="flex-shrink-0">{item.icon}</span>
                {(!isCollapsed || isMobileMenuOpen) && (
                  <span className="flex-1">{item.label}</span>
                )}
                {currentView === item.id && !isCollapsed && !isMobileMenuOpen && (
                  <ChevronRight size={16} />
                )}
              </Link>
            ))}
          </div>

          {/* Collapse/Expand button - desktop only */}
          <div className="hidden lg:flex justify-center mt-4 pt-4 border-t border-rv-surface/20">
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="p-2 rounded-full hover:bg-rv-surface/80"
              aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
              <ChevronRight className={`transform transition-transform ${isCollapsed ? "rotate-0" : "rotate-180"}`} size={20} />
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
