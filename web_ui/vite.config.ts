import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // Separate vendor libraries for better caching
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom'],
          ui: ['@radix-ui/react-avatar', '@radix-ui/react-checkbox', '@radix-ui/react-dialog'],
          charts: ['recharts', '@tanstack/react-table'],
          icons: ['lucide-react', '@tabler/icons-react'],
        },
      },
    },
    // Increase chunk size warning limit or keep it for monitoring
    chunkSizeWarningLimit: 1000,
  },
});
