import { ThemeProvider } from "@/components/theme-provider";
import { StrictMode } from "react";
import ReactDOM from "react-dom/client";
import { AppRouter } from "./app-router";
import "./global.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ThemeProvider>
      <AppRouter />
    </ThemeProvider>
  </StrictMode>
);
