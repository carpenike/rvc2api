import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { defineConfig } from "vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src")
    }
  },
  server: {
    proxy: {
      // Proxy API requests to the FastAPI backend
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        secure: false,
        ws: true // proxy WebSockets
      }
    }
  }
});
