import { ThemeProvider } from "@/components/theme-provider";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AuthGuard } from "@/components/auth-guard";
import { AuthProvider } from "@/contexts/auth-context";
import { QueryProvider } from "@/contexts/query-provider";
import { WebSocketProvider } from "@/contexts/websocket-provider";
import AnalyticsDashboardPage from "@/pages/analytics-dashboard";
import CanSniffer from "@/pages/can-sniffer";
import ConfigurationPage from "@/pages/config";
import Dashboard from "@/pages/dashboard";
import DemoDashboard from "@/pages/demo-dashboard";
import DeviceMapping from "@/pages/device-mapping";
import DiagnosticsPage from "@/pages/diagnostics";
import Documentation from "@/pages/documentation";
import EntitiesPage from "@/pages/entities";
import Lights from "@/pages/lights";
import LoginPage from "@/pages/login";
import LogsPage from "@/pages/logs";
import NetworkMap from "@/pages/network-map";
import PerformancePage from "@/pages/performance";
import ProfilePage from "@/pages/profile";
import AdminSettingsPage from "@/pages/admin-settings";
import SettingsPage from "@/pages/settings";

import { Toaster } from "@/components/ui/sonner";
import RVCSpec from "@/pages/rvc-spec";
import SystemStatus from "@/pages/system-status";
import ThemeTest from "@/pages/theme-test";
import UnknownPGNs from "@/pages/unknown-pgns";
import UnmappedEntries from "@/pages/unmapped-entries";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import "./global.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryProvider>
      <AuthProvider>
        <WebSocketProvider enableEntityUpdates enableSystemStatus enableCANScan={false}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <TooltipProvider>
            <Toaster />
            <BrowserRouter
            future={{
              v7_startTransition: true,
              v7_relativeSplatPath: true,
            }}
          >
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<LoginPage />} />

              {/* Protected routes */}
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<AuthGuard><Dashboard /></AuthGuard>} />
              <Route path="/demo-dashboard" element={<AuthGuard><DemoDashboard /></AuthGuard>} />
              <Route path="/entities" element={<AuthGuard><EntitiesPage /></AuthGuard>} />
              <Route path="/lights" element={<AuthGuard><Lights /></AuthGuard>} />
              <Route path="/device-mapping" element={<AuthGuard><DeviceMapping /></AuthGuard>} />
              <Route path="/can-sniffer" element={<AuthGuard><CanSniffer /></AuthGuard>} />
              <Route path="/network-map" element={<AuthGuard><NetworkMap /></AuthGuard>} />
              <Route path="/diagnostics" element={<AuthGuard><DiagnosticsPage /></AuthGuard>} />
              <Route path="/unknown-pgns" element={<AuthGuard><UnknownPGNs /></AuthGuard>} />
              <Route path="/unmapped-entries" element={<AuthGuard><UnmappedEntries /></AuthGuard>} />
              <Route path="/config" element={<AuthGuard><ConfigurationPage /></AuthGuard>} />
              <Route path="/documentation" element={<AuthGuard><Documentation /></AuthGuard>} />
              <Route path="/rvc-spec" element={<AuthGuard><RVCSpec /></AuthGuard>} />
              <Route path="/system-status" element={<AuthGuard><SystemStatus /></AuthGuard>} />
              <Route path="/performance" element={<AuthGuard><PerformancePage /></AuthGuard>} />
              <Route path="/analytics-dashboard" element={<AuthGuard><AnalyticsDashboardPage /></AuthGuard>} />
              <Route path="/settings" element={<AuthGuard><SettingsPage /></AuthGuard>} />
              <Route path="/profile" element={<AuthGuard><ProfilePage /></AuthGuard>} />
              <Route path="/admin-settings" element={<AuthGuard><AdminSettingsPage /></AuthGuard>} />
              <Route path="/theme-test" element={<AuthGuard><ThemeTest /></AuthGuard>} />
              <Route path="/logs" element={<AuthGuard><LogsPage /></AuthGuard>} />
            </Routes>
          </BrowserRouter>
          </TooltipProvider>
        </ThemeProvider>
        </WebSocketProvider>
      </AuthProvider>
    </QueryProvider>
  </StrictMode>
);
