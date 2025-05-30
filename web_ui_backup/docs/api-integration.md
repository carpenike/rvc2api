# API Integration Guide

This document provides details about how the React frontend interacts with the FastAPI backend in the rvc2api project.

## REST API Endpoints

The frontend uses standardized API endpoints for all entity types.

### Entity Endpoints

All entity interactions (including lights) use the `/api/entities` endpoints:

```typescript
// Fetch all lights
// GET /api/entities?device_type=light
const lights = await fetchLights();

// Control a light (turn on/off)
// POST /api/entities/{id}/control
const updatedLight = await setLightState(lightId, true);
// Sends command payload: { command: "set", state: "on" }
```

### Entity Control Commands

The `/api/entities/{id}/control` endpoint accepts the following commands:

| Command           | Parameters                                        | Description                |
| ----------------- | ------------------------------------------------- | -------------------------- |
| `set`             | `state: "on"/"off"`, optional `brightness: 0-100` | Set light state/brightness |
| `toggle`          | none                                              | Toggle current light state |
| `brightness_up`   | none                                              | Increase brightness by 10% |
| `brightness_down` | none                                              | Decrease brightness by 10% |

Example payloads:

```json
// Turn light on
{ "command": "set", "state": "on" }

// Turn light off
{ "command": "set", "state": "off" }

// Set brightness to 75%
{ "command": "set", "state": "on", "brightness": 75 }

// Toggle light state
{ "command": "toggle" }

// Increase brightness by 10%
{ "command": "brightness_up" }

// Decrease brightness by 10%
{ "command": "brightness_down" }
```

### Health and Status Endpoints

```typescript
// Application health check
// GET /api/health
const health = await fetchAppHealth();

// CAN interface status
// GET /api/can/status
const canStatus = await fetchCanStatus();
```

### Additional Endpoints

```typescript
// Device mappings
// GET /api/mappings/devices
const mappings = await fetchDeviceMappings();

// Recent CAN messages
// GET /api/can/recent?limit=100
const messages = await fetchRecentCanMessages(100);

// Unmapped entries
// GET /api/mappings/unmapped
const unmapped = await fetchUnmappedEntries();

// Unknown PGNs
// GET /api/mappings/unknown-pgns
const unknownPgns = await fetchUnknownPgns();

// RV-C Specification
// GET /api/spec
const spec = await fetchRvcSpec();

// Network map data
// GET /api/network/map
const networkMap = await fetchNetworkMap();
```

## WebSocket Integration

Real-time updates use the WebSocket protocol:

```typescript
// Connect to the entity events WebSocket
const wsUrl = `${protocol}//${window.location.host}/api/ws/entities`;
const ws = new WebSocket(wsUrl);

// Handle incoming messages
ws.addEventListener("message", (event) => {
  const data = JSON.parse(event.data);
  // Handle entity updates
  if (data.entity_id && data.state) {
    // Update UI with new entity state
    updateEntityState(data);
  }
});

// Handle connection events
ws.addEventListener("open", () => {
  console.log("WebSocket connection established");
});

ws.addEventListener("close", () => {
  console.log("WebSocket connection closed");
  // Implement reconnection logic
  setTimeout(reconnect, 3000);
});
```

## Error Handling

The frontend API functions use a common error handling pattern:

```typescript
export async function handleApiResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `API error: ${response.status}`);
  }
  return (await response.json()) as T;
}
```

## Type Definitions

The frontend defines TypeScript interfaces that match the backend Pydantic models. For example:

```typescript
export interface LightStatus {
  id: string;
  name: string;
  instance: number;
  zone: number;
  state: boolean;
  type: string;
  location?: string;
  last_updated: string;
}
```

## Best Practices

1. Always use the standard entity endpoints (`/api/entities`) for entity operations.
2. Handle API errors and provide feedback to the user.
3. Use the WebSocket connection for real-time updates.
4. Maintain TypeScript interfaces that match the backend models.
5. Consider optimistic UI updates for better user experience.
