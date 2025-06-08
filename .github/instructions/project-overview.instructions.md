---
applyTo: "**"
---

# Project Overview

`CoachIQ`: Intelligent RV-C network management system with advanced analytics and control:

- FastAPI backend with WebSocket support and feature management
- React frontend with TypeScript, Vite, and shadcn/ui
- RV-C protocol decoder with comprehensive message processing
- Real-time CAN bus monitoring and control

## Current Structure

- `backend/`: FastAPI app, API routes, services, and business logic
  - `backend/main.py`: FastAPI application entry point
  - `backend/core/`: Core application components (config, state, dependencies)
  - `backend/services/`: Business logic services (entity, CAN, RV-C)
  - `backend/api/routers/`: API endpoint routers
  - `backend/websocket/`: WebSocket management
  - `backend/integrations/`: Protocol integrations
  - `backend/models/`: Domain models
- `frontend/`: React frontend with TypeScript, Vite, and Tailwind CSS

## Architecture Features

The current backend structure provides:
- Service-oriented architecture with clear separation of concerns
- YAML-driven feature flag system with dependency resolution
- Multi-interface CAN bus support with automatic reconnection
- Real-time WebSocket updates for entity state changes
- Optional SQLite persistence with repository pattern
- Comprehensive OpenAPI documentation with type generation

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
