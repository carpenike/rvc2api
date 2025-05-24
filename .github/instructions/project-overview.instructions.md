---
applyTo: "**"
---

# Project Overview

`rvc2api`: Python API/WebSocket service for RV-C CANbus systems:

- FastAPI backend with WebSocket support
- React frontend with TypeScript and Vite
- Console client
- RV-C decoder

## Current Structure

- `src/common/`: Shared models and utilities (Pydantic models, type definitions)
- `src/rvc_decoder/`: DGN decoding, mappings, instance management
- `backend/`: FastAPI app, API routes, services, and business logic
  - `backend/main.py`: FastAPI application entry point
  - `backend/core/`: Core application components (config, state, dependencies)
  - `backend/services/`: Business logic services (entity, CAN, RV-C)
  - `backend/api/routers/`: API endpoint routers
  - `backend/websocket/`: WebSocket management
  - `backend/integrations/`: Protocol integrations
  - `backend/models/`: Domain models
- `web_ui/`: React frontend with TypeScript, Vite, and Tailwind CSS

## Migration Complete

The migration from `src/core_daemon/` to `backend/` has been completed. The new structure provides:
- Service-oriented architecture with clear separation of concerns
- Improved maintainability and testability
- Better organization for future integrations (e.g., Victron Modbus)
- Production-ready backend structure

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
