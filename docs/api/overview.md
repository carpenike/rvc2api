# API Overview

The rvc2api server provides a RESTful API for interacting with RV-C devices and systems. This page provides an overview of the API structure and common patterns.

## API Base URL

All API endpoints are located under `/api`.

## Authentication

Currently, the API doesn't require authentication. This may change in future versions.

## Response Format

Most API endpoints return JSON responses with the following general structure:

```json
{
  "key1": "value1",
  "key2": "value2",
  ...
}
```

List endpoints typically return an array of objects:

```json
[
  { "id": "light_1", ... },
  { "id": "light_2", ... },
  ...
]
```

## Error Handling

The API uses standard HTTP status codes to indicate the success or failure of requests:

- `200 OK`: The request was successful
- `400 Bad Request`: The request was invalid or cannot be served
- `404 Not Found`: The requested resource was not found
- `500 Internal Server Error`: An error occurred on the server

Error responses include a JSON body with details about the error:

```json
{
  "detail": "Error message"
}
```

## API Categories

The API is organized into the following categories:

### Entity API

Endpoints for managing and controlling entities (devices like lights, temperature sensors, etc.) in the RV.

- `GET /api/entities` - List all entities with optional filtering by device type and area
- `GET /api/entities/{id}` - Get details for a specific entity
- `POST /api/entities/{id}/control` - Control an entity (e.g., turn a light on/off)

### CAN Bus API

Endpoints for interacting with the CAN bus directly.

- `GET /api/can/status` - Get status of the CAN bus interface
- `GET /api/can/sniffer` - Get recent CAN messages

### Configuration API

Endpoints for retrieving and modifying system configuration.

- `GET /api/config` - Get current configuration

### WebSocket API

The server also provides WebSocket endpoints for real-time updates.

- `WS /api/ws` - WebSocket connection for entity state updates
