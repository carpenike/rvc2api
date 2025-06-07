import { ThemeProvider } from "@/components/theme-provider";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryProvider } from "@/contexts/query-provider";
import { WebSocketProvider } from "@/contexts/websocket-provider";
import CanSniffer from "@/pages/can-sniffer";
import Dashboard from "@/pages/dashboard";
import DemoDashboard from "@/pages/demo-dashboard";
import DeviceMapping from "@/pages/device-mapping";
import Documentation from "@/pages/documentation";
import EntitiesPage from "@/pages/entities";
import Lights from "@/pages/lights";
import LogsPage from "@/pages/logs";
import NetworkMap from "@/pages/network-map";

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
      <WebSocketProvider enableEntityUpdates={true} enableSystemStatus={true} enableCANScan={false}>
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
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/demo-dashboard" element={<DemoDashboard />} />
            <Route path="/entities" element={<EntitiesPage />} />
            <Route path="/lights" element={<Lights />} />
            <Route path="/device-mapping" element={<DeviceMapping />} />
            <Route path="/can-sniffer" element={<CanSniffer />} />
            <Route path="/network-map" element={<NetworkMap />} />
            <Route path="/unknown-pgns" element={<UnknownPGNs />} />
            <Route path="/unmapped-entries" element={<UnmappedEntries />} />
            <Route path="/documentation" element={<Documentation />} />
            <Route path="/rvc-spec" element={<RVCSpec />} />
            <Route path="/system-status" element={<SystemStatus />} />
            <Route path="/theme-test" element={<ThemeTest />} />
            <Route path="/logs" element={<LogsPage />} />
          </Routes>
          </BrowserRouter>
          </TooltipProvider>
        </ThemeProvider>
      </WebSocketProvider>
    </QueryProvider>
  </StrictMode>
);
