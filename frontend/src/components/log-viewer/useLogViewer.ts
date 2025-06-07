import { createContext, useContext } from "react";
import type { LogViewerContextType } from "./log-viewer-context";

export const LogViewerContext = createContext<LogViewerContextType | undefined>(undefined);

export function useLogViewer() {
  const context = useContext(LogViewerContext);
  if (!context) {
    throw new Error("useLogViewer must be used within a LogViewerProvider");
  }
  return context;
}
