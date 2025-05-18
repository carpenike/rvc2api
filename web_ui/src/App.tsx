import { useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import "./App.css";
import { Navbar } from "./components";
import { useWebSocket } from "./hooks";
import "./index.css";
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
import { WS_URL } from "./utils/config";

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
   * WebSocket connection setup with status monitoring and message handling
   */
  const {
    status: wsStatus,
    messages,
    // Keep sendMessage available for future custom commands implementation
    sendMessage: _sendMessage
  } = useWebSocket(WS_URL, {
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
    onError: (error) => {
      console.error("WebSocket error:", error);
    }
  });

  /**
   * Handle WebSocket message storage and dispatch WebSocket status events
   */
  useEffect(() => {
    // Store messages in state for debugging and potential later use by components
    setWsMessages(messages);

    // Dispatch WebSocket status change event
    dispatchCustomEvent("ws-status-change", { status: wsStatus });
  }, [messages, wsStatus]);

  /**
   * Helper function to dispatch custom events for cross-component communication
   *
   * @param eventName - The name of the custom event to dispatch
   * @param detail - The data to include with the event
   */
  const dispatchCustomEvent = (
    eventName: string,
    detail: Record<string, unknown>
  ): void => {
    const event = new CustomEvent(eventName, { detail });
    window.dispatchEvent(event);
  };

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
    <div className="min-h-screen flex flex-col bg-rv-background text-rv-text">
      {/* Navigation */}
      <Navbar currentView={getCurrentView()} />

      <div className="flex flex-1 overflow-hidden min-h-0">
        {/* Main Content */}
        <main className="flex-1 container mx-auto p-6">
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
        </main>
      </div>

      {/* Footer */}
      <footer className="bg-rv-surface text-rv-text/60 text-xs p-4 flex justify-between items-center">
        <span>rvc2api React UI</span>
        <div className="flex items-center space-x-2">
          <span>WebSocket:</span>
          <span
            className={`px-2 py-1 rounded-full text-xs font-medium ${
              wsStatus === "open"
                ? "bg-rv-success/20 text-rv-success"
                : wsStatus === "connecting"
                ? "bg-rv-warning/20 text-rv-warning"
                : "bg-rv-error/20 text-rv-error"
            }`}
          >
            {wsStatus}
          </span>
        </div>
      </footer>
    </div>
  );
}

export default App;
