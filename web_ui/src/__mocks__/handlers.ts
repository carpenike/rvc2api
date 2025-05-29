import { http, HttpResponse } from "msw";

// Mock API handlers for testing
export const handlers = [
  // Mock entities endpoint
  http.get("http://localhost:8000/api/entities", () => {
    return HttpResponse.json({
      "light.kitchen": {
        entity_id: "light.kitchen",
        state: "on",
        device_type: "light",
        suggested_area: "Kitchen",
        friendly_name: "Kitchen Light",
        capabilities: ["brightness", "switch"],
        groups: [],
        brightness: 80,
        last_updated: "2025-05-28T10:00:00Z"
      },
      "light.living_room": {
        entity_id: "light.living_room",
        state: "off",
        device_type: "light",
        suggested_area: "Living Room",
        friendly_name: "Living Room Light",
        capabilities: ["brightness", "switch"],
        groups: [],
        brightness: 0,
        last_updated: "2025-05-28T09:30:00Z"
      }
    });
  }),

  // Mock individual entity endpoint
  http.get("http://localhost:8000/api/entities/:entityId", ({ params }) => {
    const { entityId } = params;

    if (entityId === "light.kitchen") {
      return HttpResponse.json({
        entity_id: "light.kitchen",
        state: "on",
        device_type: "light",
        suggested_area: "Kitchen",
        friendly_name: "Kitchen Light",
        capabilities: ["brightness", "switch"],
        groups: [],
        brightness: 80,
        last_updated: "2025-05-28T10:00:00Z"
      });
    }

    return new HttpResponse(null, { status: 404 });
  }),

  // Mock entity control endpoint
  http.post("http://localhost:8000/api/entities/:entityId/control", async ({ params, request }) => {
    const { entityId } = params;
    const command = await request.json() as { command: string; state?: string; brightness?: number };

    return HttpResponse.json({
      status: "success",
      entity_id: entityId,
      command: command.command,
      state: command.state || "on",
      brightness: command.brightness || 100,
      action: `${command.command} command executed successfully`
    });
  }),

  // Mock entity history endpoint
  http.get("http://localhost:8000/api/entities/:entityId/history", () => {
    return HttpResponse.json([
      {
        entity_id: "light.kitchen",
        timestamp: Date.now() - 300000, // 5 minutes ago
        state: "on",
        brightness: 80
      },
      {
        entity_id: "light.kitchen",
        timestamp: Date.now() - 600000, // 10 minutes ago
        state: "off",
        brightness: 0
      }
    ]);
  })
];

export { http };
