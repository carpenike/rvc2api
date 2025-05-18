---
applyTo: "**"
---

# Project Overview

`rvc2api`: Python API/WebSocket service for RV-C CANbus systems:

- FastAPI backend daemon with WebSocket support
- React frontend with TypeScript and Vite
- Console client
- RV-C decoder

## Structure

- `src/common/`: Models, utilities
- `src/console_client/`: CLI
- `src/core_daemon/`: FastAPI, frontend, settings
- `src/rvc_decoder/`: DGN decoding, mappings

## Future Structure

- `src/core_daemon/` → `backend/` (FastAPI, API routes)
- `src/rvc_decoder/` → `backend/integrations/rvc/`
- Business logic → `backend/services/`
- Config → `backend/settings/`
- Prepares for Victron Modbus integration

# API Endpoint Design Decision

All light-related API operations are consolidated under `/api/entities` endpoints (e.g., `/api/entities?device_type=light`). The legacy `/api/lights` endpoint is not used. This ensures a unified, type-safe, and extensible API surface for all entity types.

## Entity Control Command Structure

When controlling entities via the `/api/entities/{id}/control` endpoint, the request body must use the standardized command format:

```json
// Turn light on
{ "command": "set", "state": "on" }

// Set light brightness
{ "command": "set", "state": "on", "brightness": 75 }

// Toggle light state
{ "command": "toggle" }

// Adjust brightness
{ "command": "brightness_up" }
{ "command": "brightness_down" }
```

All frontend code must use this command structure rather than simplified formats like `{ state: true }` which don't match the backend API expectations.
