import clsx from "clsx";
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
import React, {
  cloneElement,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
  type ReactElement,
  type ReactNode
} from "react";
import { useLocation, useNavigate } from "react-router-dom";

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
const navItems: Array<{
  id: string;
  label: string;
  path: string;
  icon: ReactNode;
}> = [
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

/**
 * Sidebar navigation component for the application with responsive design
 *
 * Desktop: Shows as a sidebar that can be collapsed to icons only
 * Mobile: Hidden by default, shows as a slide-in menu when toggled
 *
 * @returns A React component
 */
export function SideNav({ currentView: propCurrentView, wsStatus }: SideNavProps) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const menuButtonRef = useRef<HTMLButtonElement | null>(null);
  const sidebarRef = useRef<HTMLDivElement | null>(null);
  const lastFocusedElement = useRef<HTMLElement | null>(null);
  const menuItemRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const location = useLocation();
  const navigate = useNavigate();

  // Use provided currentView from props or get it from location path
  const currentView = propCurrentView || location.pathname.split("/")[1] || "dashboard";

  // Memoize nav items for performance
  const memoizedNavItems = useMemo(() => navItems, []);

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

  // Trap focus in mobile menu
  useEffect(() => {
    if (!isMobileMenuOpen) return;
    const focusableSelectors = [
      "button", "a[href]", "input", "select", "textarea", "[tabindex]:not([tabindex='-1'])"
    ];
    const sidebar = sidebarRef.current;
    if (!sidebar) return;
    lastFocusedElement.current = document.activeElement as HTMLElement;
    const focusableEls = sidebar.querySelectorAll<HTMLElement>(focusableSelectors.join(","));
    if (focusableEls.length) focusableEls[0].focus();
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = "";
      if (lastFocusedElement.current) {
        lastFocusedElement.current.focus();
      }
    };
  }, [isMobileMenuOpen]);

  // Focus first menu item when mobile menu opens
  useEffect(() => {
    if (isMobileMenuOpen && menuItemRefs.current[0]) {
      menuItemRefs.current[0].focus();
    }
  }, [isMobileMenuOpen]);

  // Keyboard navigation for focus trap
  const handleKeyDown = useCallback((e: KeyboardEvent<HTMLDivElement>) => {
    if (!isMobileMenuOpen || !sidebarRef.current) return;
    if (e.key === "Escape") {
      setIsMobileMenuOpen(false);
    } else if (e.key === "Tab") {
      const focusableEls = sidebarRef.current.querySelectorAll<HTMLElement>(
        "button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])"
      );
      const first = focusableEls[0];
      const last = focusableEls[focusableEls.length - 1];
      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    }
  }, [isMobileMenuOpen]);

  // Keyboard navigation for menu items
  function handleMenuItemKeyDown(e: React.KeyboardEvent<HTMLButtonElement>, idx: number) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      const next = (idx + 1) % memoizedNavItems.length;
      menuItemRefs.current[next]?.focus();
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      const prev = (idx - 1 + memoizedNavItems.length) % memoizedNavItems.length;
      menuItemRefs.current[prev]?.focus();
    } else if (e.key === "Home") {
      e.preventDefault();
      menuItemRefs.current[0]?.focus();
    } else if (e.key === "End") {
      e.preventDefault();
      menuItemRefs.current[memoizedNavItems.length - 1]?.focus();
    }
  }

  // Restore focus to menu button when closing mobile menu
  useEffect(() => {
    if (!isMobileMenuOpen && menuButtonRef.current) {
      menuButtonRef.current.focus();
    }
  }, [isMobileMenuOpen]);

  const handleMenuToggle = useCallback(() => setIsMobileMenuOpen((v) => !v), []);
  const handleMenuClose = useCallback(() => setIsMobileMenuOpen(false), []);

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
            ref={menuButtonRef}
            onClick={handleMenuToggle}
            className="p-2 rounded-lg hover:bg-rv-surface/80"
            aria-label="Toggle menu"
            aria-controls="side-nav-menu"
            aria-expanded={isMobileMenuOpen}
          >
            {isMobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* Mobile menu overlay */}
      {isMobileMenuOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-rv-background/80 backdrop-blur-sm z-40"
          role="dialog"
          aria-modal="true"
          tabIndex={-1}
          onClick={handleMenuClose}
        ></div>
      )}

      {/* Sidebar navigation - hidden on mobile unless menu is open */}
      <div
        ref={sidebarRef}
        id="side-nav-menu"
        tabIndex={-1}
        className={clsx(
          "fixed lg:sticky top-0 lg:top-0 z-50 lg:z-auto h-screen lg:h-full transition-all duration-300 ease-in-out",
          isMobileMenuOpen ? "left-0" : "-left-64 lg:left-0",
          isCollapsed ? "lg:w-16" : "lg:w-64",
          "w-64"
        )}
        aria-hidden={!isMobileMenuOpen && window.innerWidth < 1024}
        onKeyDown={handleKeyDown}
        aria-label="Sidebar navigation"
        role="navigation"
        data-testid="side-nav"
      >
        <div className="bg-rv-surface text-rv-text h-full rounded-r-3xl lg:rounded-none p-4 shadow-md flex flex-col border-l border-rv-border transition-colors duration-200">
          {/* Logo section - hidden on desktop as it's in the main header */}
          <div className="flex lg:hidden items-center justify-between mb-4 pb-3 border-b border-rv-surface/20">
            <span className="text-lg font-bold text-rv-heading">RVC2API</span>
            <button
              onClick={handleMenuClose}
              className="p-2 rounded-lg hover:bg-rv-surface/80 focus:outline-none focus:ring-2 focus:ring-rv-primary"
              aria-label="Close menu"
            >
              <X size={20} />
            </button>
          </div>

          {/* Navigation items - scrollable if needed */}
          <div className="flex flex-col space-y-1.5 overflow-y-auto flex-1" role="menubar" aria-orientation="vertical">
            {memoizedNavItems.map((item, idx) => (
              <button
                key={item.path}
                ref={el => { menuItemRefs.current[idx] = el; }}
                className={clsx(
                  "flex items-center w-full px-3 py-2 rounded-lg text-left transition-colors focus:outline-none focus:ring-2 focus:ring-rv-primary",
                  "hover:bg-rv-primary/10 focus:bg-rv-primary/20",
                  currentView === item.id ? "bg-rv-primary/20 text-rv-primary" : "text-rv-text"
                )}
                onClick={() => {
                  navigate(item.path);
                  setIsMobileMenuOpen(false);
                }}
                aria-label={item.label}
                aria-current={currentView === item.id ? "page" : undefined}
                role="menuitem"
                tabIndex={0}
                onKeyDown={e => handleMenuItemKeyDown(e, idx)}
              >
                {React.isValidElement(item.icon)
                  ? cloneElement(item.icon as ReactElement<{ className?: string; "aria-hidden"?: boolean }>, {
                      className: "mr-3 w-5 h-5 shrink-0",
                      "aria-hidden": true
                    })
                  : item.icon}
                <span className="truncate">{item.label}</span>
              </button>
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
