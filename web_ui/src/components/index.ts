// All exports are for theme-adaptive, accessible components only

// Application-specific Button (with legacy variant support)
export { Button } from "./Button";

// shadcn/ui New York v4 Components (excluding Button to avoid conflicts)
export * from "./ui/alert";
export * from "./ui/badge";
export * from "./ui/breadcrumb";
export * from "./ui/calendar";
export * from "./ui/card";
export * from "./ui/chart";
export * from "./ui/checkbox";
export * from "./ui/collapsible";
export * from "./ui/command";
export * from "./ui/context-menu";
export * from "./ui/dialog";
export * from "./ui/drawer";
export * from "./ui/form";
export * from "./ui/hover-card";
export * from "./ui/input";
export * from "./ui/input-otp";
export * from "./ui/label";
export * from "./ui/menubar";
export * from "./ui/navigation-menu";
export * from "./ui/pagination";
export * from "./ui/radio-group";
export * from "./ui/resizable";
export * from "./ui/scroll-area";
export * from "./ui/select";
export * from "./ui/separator";
export * from "./ui/sheet";
export * from "./ui/sidebar";
export * from "./ui/skeleton";
export * from "./ui/sonner";
export * from "./ui/switch";
export * from "./ui/table";
export * from "./ui/textarea";
export * from "./ui/toggle";
export * from "./ui/toggle-group";
export * from "./ui/tooltip";

// Application-specific components (avoiding naming conflicts with ui components)
export { default as ErrorBoundary } from "./ErrorBoundary";
export { default as Footer } from "./Footer";
export { default as Header } from "./Header";
export * from "./Loading";
export { default as LoadingSpinner } from "./LoadingSpinner";
export * from "./Navbar";
export * from "./SideNav"; // Legacy - will be removed after migration
export { default as SkeletonLoader } from "./SkeletonLoader";
export * from "./ThemeSelector";

// Application-specific components with ui naming conflicts
export * from "./AppSidebar";
export * from "./CanBusStatusPanel";

// Legacy components - use specific names to avoid conflicts with shadcn/ui
export { Alert as LegacyAlert } from "./Alert";
export { Badge as LegacyBadge } from "./Badge";
export { Card as LegacyCard } from "./Card";
export { Toggle as LegacyToggle } from "./Toggle";
