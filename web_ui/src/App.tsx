import { useCallback, useEffect, useMemo, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import "./App.css";
import { SideNav } from "./components";
import { useWebSocket } from "./hooks";
import "./index.css";
import Layout from "./layout/Layout";
import {
  CanSniffer,
  Dashboard,
  DeviceMapping,
  DocumentationPage,
  Lights,
  NetworkMap,
  RvcSpec,
  UnknownPgns,
  UnmappedEntries
} from "./pages";
import "./styles/themes.css";
import { getWebSocketUrl } from "./utils/config";

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
   * Gets the current view identifier from the route path
   *
   * @returns The current view identifier (defaults to 'dashboard' if none found)
   */
  const getCurrentView = (): string => {
    const path = location.pathname.split("/")[1] || "dashboard";
    return path;
  };

  return (
    <Layout wsStatus={wsStatus}>
      <div className="flex flex-1 min-h-0">
        {/* Sidebar Navigation */}
        <div className="z-40">
          <SideNav currentView={getCurrentView()} wsStatus={wsStatus} />
        </div>
        {/* Main Content */}
        <main className="flex-1 p-4 lg:p-6 overflow-y-auto min-h-0">
          <div className="overflow-y-auto h-full">
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
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </div>
        </main>
      </div>
    </Layout>
  );
}

export default App;
