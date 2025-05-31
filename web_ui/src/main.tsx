import { ThemeProvider } from "@/components/theme-provider";
import DemoDashboard from "@/pages/demo-dashboard";
import RVCDashboard from "@/pages/rvc-dashboard";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import "./global.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ThemeProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
    >
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/rvc-dashboard" replace />} />
          <Route path="/demo-dashboard" element={<DemoDashboard />} />
          <Route path="/rvc-dashboard" element={<RVCDashboard />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  </StrictMode>
);
