import { useEffect, useState } from "react";
import { fetchAppHealth, fetchCanStatus } from "../api";
import type { AllCanStats } from "../api/types";
import { Button, Card } from "../components";
import { CanBusStatusPanel } from "../components/CanBusStatusPanel";

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
  const [appHealth, setAppHealth] = useState<unknown>(null);

  /** CAN bus connection status information */
  const [canStatus, setCanStatus] = useState<AllCanStats | null>(null);

  /** Loading state for the API calls */
  const [loading, setLoading] = useState(false);

  /** Error state for failed API calls */
  const [error, setError] = useState<string | null>(null);

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

  return (
    <section className="space-y-8 bg-background text-foreground min-h-screen p-4 md:p-8">
      <h1 className="text-3xl font-bold text-primary">Dashboard</h1>

      <Card title="Quick Light Controls" className="mb-8 bg-card text-card-foreground">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <Button variant="primary" className="w-full" aria-label="Turn all lights on">All Lights On</Button>
          <Button variant="ghost" className="w-full" aria-label="Turn all lights off">All Lights Off</Button>
          <Button variant="accent" className="w-full" aria-label="Turn exterior lights on">Exterior On</Button>
          <Button variant="ghost" className="w-full" aria-label="Turn exterior lights off">Exterior Off</Button>
          <Button variant="secondary" className="w-full" aria-label="Turn interior lights on">Interior On</Button>
          <Button variant="ghost" className="w-full" aria-label="Turn interior lights off">Interior Off</Button>
        </div>
      </Card>

      <Card title="Scenes" className="bg-card text-card-foreground">
        <p className="text-muted-foreground mb-6">Scene management and definition coming soon.</p>
        <Button variant="primary" aria-label="Create new scene">Create New Scene</Button>
      </Card>

      <div className="mt-8 space-y-6">
        <h2 className="text-xl font-semibold text-primary">System Status</h2>
        {loading && <p className="text-muted-foreground">Loading...</p>}
        {error && <p className="text-error" role="alert">{error}</p>}

        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          <Card title="Application Health" className="bg-card text-card-foreground">
            {appHealth ? (
              <pre className="text-foreground text-sm whitespace-pre-wrap overflow-x-auto rounded-lg bg-muted p-3">
                {JSON.stringify(appHealth, null, 2)}
              </pre>
            ) : (
              <p className="text-muted-foreground">Loading application health...</p>
            )}
          </Card>

          <Card title="CAN Bus Interfaces" className="bg-card text-card-foreground">
            {canStatus && canStatus.interfaces ? (
              <CanBusStatusPanel interfaces={canStatus.interfaces} />
            ) : loading ? (
              <p className="text-muted-foreground">Loading CAN status...</p>
            ) : error ? (
              <p className="text-error" role="alert">{error}</p>
            ) : (
              <p className="text-muted-foreground">No CAN status available.</p>
            )}
          </Card>

          <Card title="WebSocket Status" className="bg-card text-card-foreground">
            <span className="text-muted-foreground">WebSocket status coming soon.</span>
          </Card>
        </div>
      </div>
    </section>
  );
}
