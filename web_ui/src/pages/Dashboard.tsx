import { useEffect, useState } from "react";
import { fetchAppHealth, fetchCanStatus } from "../api";
import { Button, Card } from "../components";

/**
 * Dashboard page component
 *
 * Displays system health information, CAN bus status, and quick actions.
 * Provides an overview of the system's current state and serves as the
 * primary landing page for the application.
 *
 * @returns The Dashboard page component
 */
export function Dashboard() {
  /** Application health status information */
  const [appHealth, setAppHealth] = useState<any>(null);

  /** CAN bus connection status information */
  const [canStatus, setCanStatus] = useState<any>(null);

  /** Loading state for the API calls */
  const [loading, setLoading] = useState(false);

  /** Error state for failed API calls */
  const [error, setError] = useState<string | null>(null);

  /** WebSocket connection status */
  const [wsStatus, setWsStatus] = useState<string>("unknown");

  /**
   * Fetch app health and CAN status data on component mount
   */
  useEffect(() => {
    setLoading(true);
    setError(null);

    // Fetch both app health and CAN status in parallel
    Promise.all([fetchAppHealth(), fetchCanStatus()])
      .then(([health, can]) => {
        setAppHealth(health);
        setCanStatus(can);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  // This will be updated via a prop from the parent to show real WebSocket status
  useEffect(() => {
    // WebSocket status will be provided by the parent App component
    const eventHandler = (e: CustomEvent) => {
      setWsStatus(e.detail.status);
    };

    window.addEventListener("ws-status-change", eventHandler as EventListener);
    return () => {
      window.removeEventListener("ws-status-change", eventHandler as EventListener);
    };
  }, []);

  return (
    <section className="space-y-6">
      <h1 className="text-3xl font-bold">Dashboard</h1>

      <Card title="Quick Light Controls" className="mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Button variant="primary">All Lights On</Button>
          <Button variant="ghost">All Lights Off</Button>
          <Button variant="accent">Exterior On</Button>
          <Button variant="ghost">Exterior Off</Button>
          <Button variant="secondary">Interior On</Button>
          <Button variant="ghost">Interior Off</Button>
        </div>
      </Card>

      <Card title="Scenes">
        <p className="text-rv-text/70 mb-4">Scene management and definition coming soon.</p>
        <Button variant="primary">Create New Scene</Button>
      </Card>

      <div className="mt-8 space-y-6">
        <h2 className="text-2xl font-semibold">System Status</h2>
        {loading && <p className="text-rv-text/70">Loading...</p>}
        {error && <p className="text-rv-error">{error}</p>}

        <Card title="Application Health">
          {appHealth ? (
            <pre className="text-rv-text/90 text-sm whitespace-pre-wrap overflow-x-auto rounded-lg">{JSON.stringify(appHealth, null, 2)}</pre>
          ) : (
            <p className="text-rv-text/50">Loading application health...</p>
          )}
        </Card>

        <Card title="CAN Bus Interfaces">
          {canStatus ? (
            <pre className="text-rv-text/90 text-sm whitespace-pre-wrap overflow-x-auto rounded-lg">{JSON.stringify(canStatus, null, 2)}</pre>
          ) : (
            <p className="text-rv-text/50">Loading CAN status...</p>
          )}
        </Card>

        <Card title="WebSocket Status">
          <div className="flex items-center space-x-2">
            <span>Status:</span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
              wsStatus === "open"
                ? "bg-rv-success/20 text-rv-success"
                : wsStatus === "connecting"
                  ? "bg-rv-warning/20 text-rv-warning"
                  : "bg-rv-error/20 text-rv-error"
            }`}>
              {wsStatus}
            </span>
          </div>
        </Card>
      </div>
    </section>
  );
}
