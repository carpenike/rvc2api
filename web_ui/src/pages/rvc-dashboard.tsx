import { AppLayout } from "@/components/app-layout"
import { EntityOverviewCard, LightControlCard, SystemStatusCard } from "@/components/entity-status"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useWebSocketManager } from "@/hooks"

export default function RVCDashboard() {
  // Enable real-time updates via WebSocket
  const { hasAnyError } = useWebSocketManager({
    enableEntityUpdates: true,
    enableSystemStatus: true,
    enableCANScan: false, // Not needed for dashboard
  });

  return (
    <AppLayout pageTitle="RV-C Control" sidebarVariant="inset">
      <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
        <div className="px-4 lg:px-6">
          {/* WebSocket Status Indicator */}
          {hasAnyError && (
            <div className="mb-4">
              <Card className="border-yellow-200 bg-yellow-50">
                <CardContent className="pt-4">
                  <p className="text-sm text-yellow-800">
                    ⚠️ Real-time updates may be limited. Check your connection.
                  </p>
                </CardContent>
              </Card>
            </div>
          )}

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {/* Real-time Light Control */}
            <LightControlCard />

            {/* System Status with real data */}
            <SystemStatusCard />

            {/* Entity Overview with real data */}
            <EntityOverviewCard />

            {/* Static Cards (to be migrated later) */}
            <Card>
              <CardHeader>
                <CardTitle>Power Management</CardTitle>
                <CardDescription>Monitor and control power systems</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col gap-2">
                  <Button variant="outline">Battery Status</Button>
                  <Button variant="outline">Inverter Control</Button>
                  <Button variant="outline">Shore Power</Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Climate Control</CardTitle>
                <CardDescription>Temperature and ventilation control</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col gap-2">
                  <Button variant="outline">Air Conditioning</Button>
                  <Button variant="outline">Heating</Button>
                  <Button variant="outline">Ventilation</Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Water System</CardTitle>
                <CardDescription>Fresh water and waste management</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col gap-2">
                  <Button variant="outline">Fresh Water</Button>
                  <Button variant="outline">Gray Water</Button>
                  <Button variant="outline">Black Water</Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Slide Outs</CardTitle>
                <CardDescription>Extend and retract slide out rooms</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col gap-2">
                  <Button variant="outline">Main Slide</Button>
                  <Button variant="outline">Bedroom Slide</Button>
                  <Button variant="outline">Kitchen Slide</Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Awnings & Steps</CardTitle>
                <CardDescription>Deploy awnings and entry steps</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col gap-2">
                  <Button variant="outline">Main Awning</Button>
                  <Button variant="outline">Door Awning</Button>
                  <Button variant="outline">Entry Steps</Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        <div className="px-4 lg:px-6">
          <Card>
            <CardHeader>
              <CardTitle>System Status</CardTitle>
              <CardDescription>Real-time RV-C network status and diagnostics</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-3">
                <div className="space-y-2">
                  <h4 className="text-sm font-medium">Network Status</h4>
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 rounded-full bg-green-500"></div>
                    <span className="text-sm text-muted-foreground">Connected</span>
                  </div>
                </div>
                <div className="space-y-2">
                  <h4 className="text-sm font-medium">Active Devices</h4>
                  <div className="text-sm text-muted-foreground">24 devices online</div>
                </div>
                <div className="space-y-2">
                  <h4 className="text-sm font-medium">Message Rate</h4>
                  <div className="text-sm text-muted-foreground">127 msg/sec</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </AppLayout>
  )
}
