/**
 * Simple integration test component for multi-protocol features
 */

import { MultiProtocolSelector, ProtocolEntityCard, type ProtocolType } from "./"
import { useState } from "react"
import type { Entity } from "@/api/types"

// Mock entity data for testing
const mockEntities = [
  {
    entity_id: "rvc.light.kitchen",
    friendly_name: "Kitchen Light",
    device_type: "light",
    suggested_area: "Kitchen",
    state: "on",
    brightness: 75,
    capabilities: ["brightness", "toggle"],
    timestamp: Date.now(),
    value: {},
    groups: [],
    raw: {}
  },
  {
    entity_id: "j1939.engine.cummins",
    friendly_name: "Cummins Engine",
    device_type: "engine",
    suggested_area: "Engine Bay",
    state: "running",
    protocol: "j1939",
    system_type: "engine",
    manufacturer: "cummins",
    engine_data: {
      rpm: 1800,
      coolant_temp: 180,
      oil_pressure: 40
    },
    capabilities: ["monitor"],
    timestamp: Date.now(),
    value: {},
    groups: [],
    raw: {}
  },
  {
    entity_id: "firefly.scene.living_room",
    friendly_name: "Living Room Scene",
    device_type: "light",
    suggested_area: "Living Room",
    state: "active",
    protocol: "firefly",
    multiplexed: true,
    safety_interlocks: ["motion_sensor"],
    zone_controls: {
      scene_id: "evening_mood",
      fade_time: 2000
    },
    capabilities: ["scene_control"],
    timestamp: Date.now(),
    value: {},
    groups: [],
    raw: {}
  }
] as (Entity & { protocol?: string })[]

const mockProtocolStats = {
  all: { count: 45, health: 0.95, status: "active" },
  rvc: { count: 32, health: 0.98, status: "active" },
  j1939: { count: 8, health: 0.92, status: "active" },
  firefly: { count: 3, health: 0.89, status: "warning" },
  spartan_k2: { count: 2, health: 0.96, status: "active" }
}

export function ProtocolIntegrationTest() {
  const [selectedProtocol, setSelectedProtocol] = useState<ProtocolType>("all")

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Multi-Protocol Integration Test</h1>

      <MultiProtocolSelector
        selectedProtocol={selectedProtocol}
        onProtocolChange={setSelectedProtocol}
        protocolStats={mockProtocolStats}
      />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {mockEntities.map(entity => (
          <ProtocolEntityCard
            key={entity.entity_id}
            entity={entity}
            showProtocolInfo={selectedProtocol === "all"}
          />
        ))}
      </div>
    </div>
  )
}

export default ProtocolIntegrationTest
