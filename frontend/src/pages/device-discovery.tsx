/**
 * Enhanced Device Discovery Page
 *
 * Comprehensive device discovery with auto-detection wizard, network topology,
 * device profiling, and configuration assistance.
 */

import type { DiscoveredDevice } from "@/api/types"
import { AppLayout } from "@/components/app-layout"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useDeviceDiscovery } from "@/hooks/useDeviceDiscovery"
import { useState } from "react"
// Reserved for future features: DeviceProfile, NetworkTopology
import {
    IconAlertCircle,
    IconClock,
    IconDeviceDesktop,
    IconInfoCircle,
    IconNetwork,
    IconRefresh,
    IconSearch,
    IconSettings,
    IconShield,
    IconTarget,
    IconWand,
    IconWifi
} from "@tabler/icons-react"

/**
 * Device Status Badge
 */
function DeviceStatusBadge({ status }: { status: string }) {
  const variants = {
    online: { variant: "default" as const, icon: IconShield, label: "Online", color: "text-green-500" },
    discovered: { variant: "secondary" as const, icon: IconTarget, label: "Discovered", color: "text-blue-500" },
    offline: { variant: "secondary" as const, icon: IconClock, label: "Offline", color: "text-gray-500" },
    error: { variant: "destructive" as const, icon: IconAlertCircle, label: "Error", color: "text-red-500" },
  }

  const config = variants[status as keyof typeof variants] || variants.offline
  const Icon = config.icon

  return (
    <Badge variant={config.variant} className="gap-1">
      <Icon className="h-3 w-3" />
      {config.label}
    </Badge>
  )
}

/**
 * Auto-Discovery Wizard Component
 */
function AutoDiscoveryWizard({ onDiscoveryComplete }: { onDiscoveryComplete: () => void }) {
  const [isOpen, setIsOpen] = useState(false)
  const [isScanning, setIsScanning] = useState(false)
  const [scanProgress, setScanProgress] = useState(0)
  const [selectedProtocols, setSelectedProtocols] = useState<string[]>(["rvc"])
  const [deepScan, setDeepScan] = useState(false)
  const [scanDuration, setScanDuration] = useState(30)

  const { startAutoDiscovery } = useDeviceDiscovery()

  const handleStartScan = async () => {
    setIsScanning(true)
    setScanProgress(0)

    try {
      // Simulate progress during scan
      const progressInterval = setInterval(() => {
        setScanProgress((prev) => {
          const newProgress = prev + (100 / scanDuration)
          if (newProgress >= 100) {
            clearInterval(progressInterval)
            return 100
          }
          return newProgress
        })
      }, 1000)

      await startAutoDiscovery.mutateAsync({
        protocols: selectedProtocols,
        scan_duration_seconds: scanDuration,
        deep_scan: deepScan,
        save_results: true,
      })

      clearInterval(progressInterval)
      setScanProgress(100)

      setTimeout(() => {
        setIsScanning(false)
        setIsOpen(false)
        onDiscoveryComplete()
      }, 1000)

    } catch (error) {
      setIsScanning(false)
      console.error("Discovery failed:", error)
    }
  }

  return (
    <>
      <Button onClick={() => setIsOpen(true)} className="gap-2">
        <IconWand className="h-4 w-4" />
        Start Auto-Discovery
      </Button>

      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <IconWand className="h-5 w-5" />
              Auto-Discovery Wizard
            </DialogTitle>
            <DialogDescription>
              Automatically discover and profile devices on your CAN network
            </DialogDescription>
          </DialogHeader>

          {!isScanning ? (
            <div className="space-y-4">
              <div>
                <Label htmlFor="protocols">Protocols to Scan</Label>
                <div className="flex gap-2 mt-2">
                  {["rvc", "j1939", "firefly", "spartan_k2"].map((protocol) => (
                    <div key={protocol} className="flex items-center space-x-2">
                      <Checkbox
                        id={protocol}
                        checked={selectedProtocols.includes(protocol)}
                        onCheckedChange={(checked) => {
                          if (checked) {
                            setSelectedProtocols([...selectedProtocols, protocol])
                          } else {
                            setSelectedProtocols(selectedProtocols.filter(p => p !== protocol))
                          }
                        }}
                      />
                      <Label htmlFor={protocol} className="text-sm font-medium">
                        {protocol.toUpperCase()}
                      </Label>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <Label htmlFor="duration">Scan Duration (seconds)</Label>
                <Input
                  id="duration"
                  type="number"
                  value={scanDuration}
                  onChange={(e) => setScanDuration(Number(e.target.value))}
                  min={10}
                  max={300}
                  className="mt-1"
                />
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="deep-scan"
                  checked={deepScan}
                  onCheckedChange={(checked) => setDeepScan(checked === true)}
                />
                <Label htmlFor="deep-scan" className="text-sm">
                  Deep Scan (detailed capability profiling)
                </Label>
              </div>

              <div className="flex gap-2">
                <Button
                  onClick={() => void handleStartScan()}
                  disabled={selectedProtocols.length === 0}
                  className="flex-1"
                >
                  Start Discovery
                </Button>
                <Button variant="outline" onClick={() => setIsOpen(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="text-center">
                <IconSearch className="h-12 w-12 mx-auto mb-4 text-blue-500 animate-pulse" />
                <h3 className="text-lg font-semibold mb-2">Scanning Network...</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Discovering devices on {selectedProtocols.join(", ").toUpperCase()} protocol{selectedProtocols.length > 1 ? "s" : ""}
                </p>
                <Progress value={scanProgress} className="w-full" />
                <p className="text-xs text-muted-foreground mt-2">
                  {Math.round(scanProgress)}% complete
                </p>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  )
}

/**
 * Device Profile Dialog
 */
function DeviceProfileDialog({
  device,
  isOpen,
  onClose,
  onSetup
}: {
  device: DiscoveredDevice | null
  isOpen: boolean
  onClose: () => void
  onSetup: (device: DiscoveredDevice) => void
}) {
  // Device profile can be fetched via useDeviceProfile hook if needed

  if (!device) return null

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <IconDeviceDesktop className="h-5 w-5" />
            Device Profile - {device.device_type || "Unknown Device"}
          </DialogTitle>
          <DialogDescription>
            Address: {device.address.toString(16).toUpperCase().padStart(2, '0')} • Protocol: {device.protocol.toUpperCase()}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-sm font-medium">Status</Label>
              <div className="mt-1">
                <DeviceStatusBadge status={device.status} />
              </div>
            </div>
            <div>
              <Label className="text-sm font-medium">Response Count</Label>
              <p className="text-sm">{device.response_count}</p>
            </div>
          </div>

          <div>
            <Label className="text-sm font-medium">Capabilities</Label>
            <div className="flex flex-wrap gap-1 mt-1">
              {device.capabilities.map((cap) => (
                <Badge key={cap} variant="outline" className="text-xs">
                  {cap}
                </Badge>
              ))}
              {device.capabilities.length === 0 && (
                <p className="text-sm text-muted-foreground">No capabilities detected</p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-sm font-medium">First Seen</Label>
              <p className="text-sm">{new Date(device.first_seen * 1000).toLocaleString()}</p>
            </div>
            <div>
              <Label className="text-sm font-medium">Last Seen</Label>
              <p className="text-sm">{new Date(device.last_seen * 1000).toLocaleString()}</p>
            </div>
          </div>

          <div className="flex gap-2">
            <Button onClick={() => onSetup(device)} className="flex-1">
              <IconSettings className="h-4 w-4 mr-2" />
              Setup Device
            </Button>
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

/**
 * Device Setup Dialog
 */
function DeviceSetupDialog({
  device,
  isOpen,
  onClose,
  onComplete
}: {
  device: DiscoveredDevice | null
  isOpen: boolean
  onClose: () => void
  onComplete: () => void
}) {
  const [deviceName, setDeviceName] = useState("")
  const [deviceType, setDeviceType] = useState("")
  const [area, setArea] = useState("")
  const [selectedCapabilities] = useState<string[]>([])

  const { setupDevice } = useDeviceDiscovery()

  const handleSetup = async () => {
    if (!device) return

    try {
      await setupDevice.mutateAsync({
        device_address: device.address,
        device_name: deviceName,
        device_type: deviceType,
        area,
        capabilities: selectedCapabilities,
        configuration: {}
      })

      onComplete()
      onClose()
    } catch (error) {
      console.error("Device setup failed:", error)
    }
  }

  if (!device) return null

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Setup Device</DialogTitle>
          <DialogDescription>
            Configure device at address {device.address.toString(16).toUpperCase().padStart(2, '0')}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <Label htmlFor="device-name">Device Name</Label>
            <Input
              id="device-name"
              value={deviceName}
              onChange={(e) => setDeviceName(e.target.value)}
              placeholder="Enter a descriptive name"
              className="mt-1"
            />
          </div>

          <div>
            <Label htmlFor="device-type">Device Type</Label>
            <Select value={deviceType} onValueChange={setDeviceType}>
              <SelectTrigger className="mt-1">
                <SelectValue placeholder="Select device type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="light">Light</SelectItem>
                <SelectItem value="lock">Lock</SelectItem>
                <SelectItem value="tank">Tank Sensor</SelectItem>
                <SelectItem value="temperature">Temperature Sensor</SelectItem>
                <SelectItem value="pump">Pump</SelectItem>
                <SelectItem value="generator">Generator</SelectItem>
                <SelectItem value="hvac">HVAC</SelectItem>
                <SelectItem value="slide">Slide Out</SelectItem>
                <SelectItem value="unknown">Unknown</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="area">Area</Label>
            <Select value={area} onValueChange={setArea}>
              <SelectTrigger className="mt-1">
                <SelectValue placeholder="Select area" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="living_room">Living Room</SelectItem>
                <SelectItem value="bedroom">Bedroom</SelectItem>
                <SelectItem value="kitchen">Kitchen</SelectItem>
                <SelectItem value="bathroom">Bathroom</SelectItem>
                <SelectItem value="utility">Utility</SelectItem>
                <SelectItem value="entry">Entry</SelectItem>
                <SelectItem value="exterior">Exterior</SelectItem>
                <SelectItem value="climate">Climate</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex gap-2">
            <Button
              onClick={() => void handleSetup()}
              disabled={!deviceName || !deviceType || !area}
              className="flex-1"
            >
              Setup Device
            </Button>
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

/**
 * Discovered Devices List
 */
function DiscoveredDevicesList() {
  const { topology, isLoading, error } = useDeviceDiscovery()
  const [selectedDevice, setSelectedDevice] = useState<DiscoveredDevice | null>(null)
  const [showProfile, setShowProfile] = useState(false)
  const [showSetup, setShowSetup] = useState(false)

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex items-center gap-3 p-4 border rounded-lg">
            <Skeleton className="h-10 w-10 rounded-full" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-3 w-1/2" />
            </div>
            <Skeleton className="h-8 w-20" />
          </div>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <IconAlertCircle className="h-4 w-4" />
        <AlertTitle>Error Loading Devices</AlertTitle>
        <AlertDescription>
          Unable to load discovered devices. Please check your connection and try again.
        </AlertDescription>
      </Alert>
    )
  }

  if (!topology?.devices || Object.keys(topology.devices).length === 0) {
    return (
      <Card>
        <CardContent className="p-6 text-center">
          <IconSearch className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <h3 className="text-lg font-semibold mb-2">No Devices Discovered</h3>
          <p className="text-muted-foreground mb-4">
            Start the auto-discovery wizard to find devices on your network.
          </p>
        </CardContent>
      </Card>
    )
  }

  const devices = Object.entries(topology.devices).flatMap(([protocol, protocolDevices]) =>
    protocolDevices.map(device => ({ ...device, protocol }))
  )

  return (
    <>
      <div className="space-y-3">
        {devices.map((device) => (
          <Card key={`${device.protocol}_${device.source_address}`}>
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 mt-1">
                  <IconDeviceDesktop className="h-5 w-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-sm leading-5 mb-1">
                        {device.device_type || "Unknown Device"}
                        <span className="text-muted-foreground ml-2">
                          ({device.source_address.toString(16).toUpperCase().padStart(2, '0')})
                        </span>
                      </h4>
                      <div className="flex items-center gap-2 mb-2">
                        <DeviceStatusBadge status={device.status} />
                        <Badge variant="outline" className="text-xs">
                          {device.protocol.toUpperCase()}
                        </Badge>
                      </div>
                      <div className="text-xs text-muted-foreground space-y-1">
                        <div>Responses: {device.response_count}</div>
                        <div>Last seen: {new Date(device.last_seen * 1000).toLocaleString()}</div>
                        {device.capabilities.length > 0 && (
                          <div>Capabilities: {device.capabilities.join(", ")}</div>
                        )}
                      </div>
                    </div>
                    <div className="flex-shrink-0 flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          const discoveredDevice: DiscoveredDevice = {
                            address: device.source_address,
                            protocol: device.protocol,
                            capabilities: device.capabilities,
                            last_seen: device.last_seen,
                            first_seen: device.first_seen,
                            response_count: device.response_count,
                            response_times: [],
                            status: device.status
                          };

                          if (device.device_type !== undefined) {
                            discoveredDevice.device_type = device.device_type;
                          }

                          setSelectedDevice(discoveredDevice)
                          setShowProfile(true)
                        }}
                      >
                        <IconInfoCircle className="h-3 w-3 mr-1" />
                        Profile
                      </Button>
                      <Button
                        size="sm"
                        onClick={() => {
                          const discoveredDevice: DiscoveredDevice = {
                            address: device.source_address,
                            protocol: device.protocol,
                            capabilities: device.capabilities,
                            last_seen: device.last_seen,
                            first_seen: device.first_seen,
                            response_count: device.response_count,
                            response_times: [],
                            status: device.status
                          };

                          if (device.device_type !== undefined) {
                            discoveredDevice.device_type = device.device_type;
                          }

                          setSelectedDevice(discoveredDevice)
                          setShowSetup(true)
                        }}
                      >
                        <IconSettings className="h-3 w-3 mr-1" />
                        Setup
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <DeviceProfileDialog
        device={selectedDevice}
        isOpen={showProfile}
        onClose={() => {
          setShowProfile(false)
          setSelectedDevice(null)
        }}
        onSetup={(device) => {
          setShowProfile(false)
          setSelectedDevice(device)
          setShowSetup(true)
        }}
      />

      <DeviceSetupDialog
        device={selectedDevice}
        isOpen={showSetup}
        onClose={() => {
          setShowSetup(false)
          setSelectedDevice(null)
        }}
        onComplete={() => {
          // Refresh the devices list
          window.location.reload()
        }}
      />
    </>
  )
}

/**
 * Network Topology Overview
 */
function NetworkTopologyCard() {
  const { networkMap, isLoading, error } = useDeviceDiscovery()

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Network Topology</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-32 w-full" />
        </CardContent>
      </Card>
    )
  }

  if (error || !networkMap) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-destructive">
            <IconAlertCircle className="h-5 w-5" />
            Network Topology
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Unable to load network topology</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <IconNetwork className="h-5 w-5" />
          Network Topology
        </CardTitle>
        <CardDescription>Current network status and device distribution</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-3 bg-background/50 rounded-lg">
              <div className="text-2xl font-semibold text-green-500">
                {networkMap.online_devices}
              </div>
              <div className="text-xs text-muted-foreground">Online</div>
            </div>
            <div className="text-center p-3 bg-background/50 rounded-lg">
              <div className="text-2xl font-semibold text-gray-500">
                {networkMap.offline_devices}
              </div>
              <div className="text-xs text-muted-foreground">Offline</div>
            </div>
            <div className="text-center p-3 bg-background/50 rounded-lg">
              <div className="text-2xl font-semibold text-blue-500">
                {networkMap.total_devices}
              </div>
              <div className="text-xs text-muted-foreground">Total</div>
            </div>
          </div>

          <div>
            <h4 className="text-sm font-medium mb-2">Protocol Distribution</h4>
            <div className="space-y-2">
              {Object.entries(networkMap.protocol_distribution).map(([protocol, count]) => (
                <div key={protocol} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <IconWifi className="h-4 w-4" />
                    <span className="text-sm font-medium">{protocol.toUpperCase()}</span>
                  </div>
                  <Badge variant="outline">{count}</Badge>
                </div>
              ))}
            </div>
          </div>

          {networkMap.network_health && (
            <div>
              <h4 className="text-sm font-medium mb-2">Network Health</h4>
              <div className="flex items-center gap-2">
                <Progress value={networkMap.network_health.score * 100} className="flex-1" />
                <span className="text-sm font-medium">
                  {Math.round(networkMap.network_health.score * 100)}%
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-1 capitalize">
                {networkMap.network_health.status}
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Main Device Discovery Page
 */
export default function DeviceDiscoveryPage() {
  const { refresh, isLoading } = useDeviceDiscovery()

  const handleDiscoveryComplete = () => {
    refresh()
  }

  return (
    <AppLayout pageTitle="Device Discovery">
      <div className="flex-1 space-y-6 p-4 pt-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Device Discovery</h1>
            <p className="text-muted-foreground">
              Discover, profile, and configure devices on your CAN network
            </p>
          </div>
          <div className="flex gap-2">
            <AutoDiscoveryWizard onDiscoveryComplete={handleDiscoveryComplete} />
            <Button onClick={refresh} variant="outline" className="gap-2" disabled={isLoading}>
              <IconRefresh className="h-4 w-4" />
              Refresh
            </Button>
          </div>
        </div>

        {/* Overview Card */}
        <NetworkTopologyCard />

        {/* Main Content Tabs */}
        <Tabs defaultValue="devices" className="space-y-4">
          <TabsList>
            <TabsTrigger value="devices" className="gap-2">
              <IconDeviceDesktop className="h-4 w-4" />
              Discovered Devices
            </TabsTrigger>
            <TabsTrigger value="topology" className="gap-2">
              <IconNetwork className="h-4 w-4" />
              Network Map
            </TabsTrigger>
            <TabsTrigger value="recommendations" className="gap-2">
              <IconTarget className="h-4 w-4" />
              Setup Recommendations
            </TabsTrigger>
          </TabsList>

          <TabsContent value="devices" className="space-y-4">
            <h2 className="text-lg font-semibold">Discovered Devices</h2>
            <DiscoveredDevicesList />
          </TabsContent>

          <TabsContent value="topology" className="space-y-4">
            <h2 className="text-lg font-semibold">Network Topology</h2>
            <Card>
              <CardContent className="p-6 text-center">
                <IconNetwork className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-semibold mb-2">Enhanced Network Visualization</h3>
                <p className="text-muted-foreground">
                  Interactive network topology visualization coming soon. Use the topology overview card above for current network status.
                </p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="recommendations" className="space-y-4">
            <h2 className="text-lg font-semibold">Setup Recommendations</h2>
            <Card>
              <CardContent className="p-6 text-center">
                <IconTarget className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-semibold mb-2">Intelligent Setup Recommendations</h3>
                <p className="text-muted-foreground">
                  AI-powered setup recommendations will appear here after device discovery.
                </p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </AppLayout>
  )
}
