import "@testing-library/jest-dom";
import { vi } from "vitest";

// Mock theme hooks
vi.mock("@/hooks/use-theme", () => ({
  useTheme: () => ({
    theme: "light",
    setTheme: vi.fn(),
    systemTheme: "light",
    resolvedTheme: "light",
  }),
}));

vi.mock("@/components/theme-provider", () => ({
  ThemeProvider: ({ children }: { children: React.ReactNode }) => children,
}));
