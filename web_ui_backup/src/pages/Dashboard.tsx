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
    <div className="flex flex-1 flex-col gap-4 p-4 pt-0">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
      </div>

      {/* Quick actions grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card title="Quick Light Controls" className="md:col-span-2 lg:col-span-4">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            <Button variant="primary" className="w-full" aria-label="Turn all lights on">
              All On
            </Button>
            <Button variant="ghost" className="w-full" aria-label="Turn all lights off">
              All Off
            </Button>
            <Button variant="accent" className="w-full" aria-label="Turn exterior lights on">
              Exterior On
            </Button>
            <Button variant="ghost" className="w-full" aria-label="Turn exterior lights off">
              Exterior Off
            </Button>
            <Button variant="secondary" className="w-full" aria-label="Turn interior lights on">
              Interior On
            </Button>
            <Button variant="ghost" className="w-full" aria-label="Turn interior lights off">
              Interior Off
            </Button>
          </div>
        </Card>
      </div>

      {/* Secondary actions */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card title="Scenes" className="md:col-span-2">
          <p className="text-sm text-muted-foreground mb-4">
            Scene management and definition coming soon.
          </p>
          <Button variant="primary" aria-label="Create new scene">
            Create New Scene
          </Button>
        </Card>

        <Card title="Quick Stats" className="md:col-span-2">
          <div className="grid grid-cols-2 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-primary">8</div>
              <div className="text-xs text-muted-foreground">Active Lights</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-primary">12</div>
              <div className="text-xs text-muted-foreground">Total Devices</div>
            </div>
          </div>
        </Card>
      </div>

      {/* System status section */}
      <div className="mt-6">
        <h2 className="text-xl font-semibold mb-4">System Status</h2>

        {loading && (
          <p className="text-sm text-muted-foreground">Loading system status...</p>
        )}

        {error && (
          <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4">
            <p className="text-sm text-destructive" role="alert">
              Error loading system status: {error}
            </p>
          </div>
        )}

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <Card title="Application Health">
            {appHealth ? (
              <div className="rounded-md bg-muted p-3">
                <pre className="text-xs text-foreground whitespace-pre-wrap overflow-auto">
                  {JSON.stringify(appHealth, null, 2)}
                </pre>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Loading...</p>
            )}
          </Card>

          <Card title="CAN Bus Status">
            {canStatus && canStatus.interfaces ? (
              <CanBusStatusPanel interfaces={canStatus.interfaces} />
            ) : loading ? (
              <p className="text-sm text-muted-foreground">Loading CAN status...</p>
            ) : error ? (
              <p className="text-sm text-destructive" role="alert">Failed to load</p>
            ) : (
              <p className="text-sm text-muted-foreground">No CAN status available</p>
            )}
          </Card>

          <Card title="Network Status">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm">WebSocket</span>
                <div className="flex items-center gap-2">
                  <div className="size-2 rounded-full bg-green-500" />
                  <span className="text-xs text-muted-foreground">Connected</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">API Server</span>
                <div className="flex items-center gap-2">
                  <div className="size-2 rounded-full bg-green-500" />
                  <span className="text-xs text-muted-foreground">Online</span>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
