import { Suspense, lazy, useCallback, useEffect, useMemo, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import "./App.css";
import { ErrorBoundary, LoadingSpinner } from "./components";
import { ThemeDebugger } from "./components/dev/ThemeDebugger";
import { useWebSocket } from "./hooks";
import "./index.css";
import Layout from "./layout/Layout";
import { getWebSocketUrl } from "./utils/config";

// Lazy load pages for better performance
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Lights = lazy(() => import("./pages/Lights"));
const DeviceMapping = lazy(() => import("./pages/DeviceMapping"));
const RvcSpec = lazy(() => import("./pages/RvcSpec"));
const DocumentationPage = lazy(() => import("./pages/DocumentationPage"));
const UnmappedEntries = lazy(() => import("./pages/UnmappedEntries"));
const UnknownPgns = lazy(() => import("./pages/UnknownPgns"));
const CanSniffer = lazy(() => import("./pages/CanSniffer"));
const NetworkMap = lazy(() => import("./pages/NetworkMap"));
const ThemeTest = lazy(() => import("./pages/ThemeTest"));

/**
 * Main application component
 *
 * Provides the primary application layout with:
 * - Navigation bar
 * - Main content area with route-based views
 * - WebSocket connection status monitoring
 * - Event distribution system for real-time updates
 *
 * @returns The main application component
 */
function App() {
  /**
   * Store for WebSocket messages that can be used by components needing
   * access to the full history of messages
   */
  const [_wsMessages, setWsMessages] = useState<unknown[]>([]);

  /**
   * Loading state for initial application setup
   */
  const [isInitializing, setIsInitializing] = useState(true);

  /**
   * Helper function to dispatch custom events for cross-component communication
   *
   * @param eventName - The name of the custom event to dispatch
   * @param detail - The data to include with the event
   */
  const dispatchCustomEvent = useCallback((
    eventName: string,
    detail: Record<string, unknown>
  ): void => {
    const event = new CustomEvent(eventName, { detail });
    window.dispatchEvent(event);
  }, []);

  // Memoize WebSocket options to prevent unnecessary re-renders
  const wsOptions = useMemo(
    () => ({
      onMessage: (data: unknown) => {
        console.log("WebSocket message:", data);
        try {
          // Try to parse the data if it's a string
          const parsedData = typeof data === "string" ? JSON.parse(data) : data;

          // Handle different message types
          if (parsedData.type === "can_message") {
            // Update relevant state based on message type
            dispatchCustomEvent("can-message-received", parsedData);
          } else if (parsedData.type === "light_status") {
            // Dispatch light status update event
            dispatchCustomEvent("light-status-update", parsedData);
          }
        } catch (err) {
          console.error("Error parsing WebSocket message:", err);
        }
      },
      onOpen: () => {
        console.log("WebSocket connection opened successfully!");
      },
      onClose: () => {
        console.log("WebSocket connection closed");
      },
      onError: (error: unknown) => {
        console.error("WebSocket error:", error);
        console.error("WebSocket URL:", getWebSocketUrl("/api/ws"));
      },
      reconnectInterval: 2000,
      reconnectAttempts: 10
    }),
    [dispatchCustomEvent]
  );

  /**
   * WebSocket connection setup with status monitoring and message handling
   */
  const {
    status: wsStatus,
    messages,
    // Keep sendMessage available for future custom commands implementation
    sendMessage: _sendMessage
  } = useWebSocket("/api/ws", wsOptions);

  /**
   * Handle WebSocket message storage and dispatch WebSocket status events
   */
  useEffect(() => {
    // Store messages in state for debugging and potential later use by components
    setWsMessages(messages);

    // Dispatch WebSocket status change event
    dispatchCustomEvent("ws-status-change", { status: wsStatus });
  }, [messages, wsStatus, dispatchCustomEvent]);

  /**
   * Handle initial application setup and loading state
   */
  useEffect(() => {
    // Mark app as initialized once WebSocket connection is established or after timeout
    const initTimer = setTimeout(() => {
      setIsInitializing(false);
    }, 1000); // Short timeout to show initial loading state

    // Initialize immediately if WebSocket is connected
    if (wsStatus === "open") {
      setIsInitializing(false);
      clearTimeout(initTimer);
    }

    return () => clearTimeout(initTimer);
  }, [wsStatus]);

  return (
    <ErrorBoundary>
      {isInitializing ? (
        <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900">
          <div className="text-center">
            <LoadingSpinner label="Initializing application..." />
            <p className="mt-2 text-xs text-gray-500 dark:text-gray-500">
              WebSocket status: {wsStatus}
            </p>
          </div>
        </div>
      ) : (
        <>
          <Layout wsStatus={wsStatus}>
            <Suspense fallback={<LoadingSpinner label="Loading page..." />}>
              <Routes>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/lights" element={<Lights />} />
                <Route path="/mapping" element={<DeviceMapping />} />
                <Route path="/spec" element={<RvcSpec />} />
                <Route path="/documentation" element={<DocumentationPage />} />
                <Route path="/unmapped" element={<UnmappedEntries />} />
                <Route path="/unknownPgns" element={<UnknownPgns />} />
                <Route path="/canSniffer" element={<CanSniffer />} />
                <Route path="/networkMap" element={<NetworkMap />} />
                <Route path="/themeTest" element={<ThemeTest />} />
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </Suspense>
          </Layout>
          {/* Development-only theme debugger */}
          <ThemeDebugger />
        </>
      )}
    </ErrorBoundary>
  );
}

export default App;
