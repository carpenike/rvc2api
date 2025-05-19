# Entity API Reference

Entities represent the devices and systems in your RV, such as lights, tanks, and temperature sensors. The Entity API allows you to interact with these devices.

## Entity Model

Each entity has the following structure:

```json
{
  "id": "light_1",
  "name": "Living Room Light",
  "device_type": "light",
  "suggested_area": "living_room",
  "state": "on",
  "raw": {
    "operating_status": 100
  },
  "capabilities": ["toggle", "brightness"],
  "last_updated": "2023-05-18T15:30:45",
  "source_type": "rv-c"
}
```

## List Entities

```
GET /api/entities
```

Returns all entities, with optional filtering by device type or area.

### Query Parameters

| Parameter   | Type   | Description                                     |
| ----------- | ------ | ----------------------------------------------- |
| device_type | string | Optional. Filter by device type (e.g., "light") |
| area        | string | Optional. Filter by area (e.g., "living_room")  |

### Example

Get all lights:

```
GET /api/entities?device_type=light
```

Get all entities in the bedroom:

```
GET /api/entities?area=bedroom
```

### Response

```json
{
  "light_1": {
    "id": "light_1",
    "name": "Living Room Light",
    "device_type": "light",
    "suggested_area": "living_room",
    "state": "on",
    "raw": {
      "operating_status": 100
    },
    "capabilities": ["toggle", "brightness"],
    "last_updated": "2023-05-18T15:30:45",
    "source_type": "rv-c"
  },
  "light_2": {
    "id": "light_2",
    "name": "Bedroom Light",
    "device_type": "light",
    "suggested_area": "bedroom",
    "state": "off",
    "raw": {
      "operating_status": 0
    },
    "capabilities": ["toggle", "brightness"],
    "last_updated": "2023-05-18T15:25:30",
    "source_type": "rv-c"
  }
}
```

## Get Entity by ID

```
GET /api/entities/{entity_id}
```

Returns a specific entity by ID.

### Path Parameters

| Parameter | Type   | Description                 |
| --------- | ------ | --------------------------- |
| entity_id | string | The ID of the entity to get |

### Response

```json
{
  "id": "light_1",
  "name": "Living Room Light",
  "device_type": "light",
  "suggested_area": "living_room",
  "state": "on",
  "raw": {
    "operating_status": 100
  },
  "capabilities": ["toggle", "brightness"],
  "last_updated": "2023-05-18T15:30:45",
  "source_type": "rv-c"
}
```

## Control Entity

```
POST /api/entities/{entity_id}/control
```

Controls an entity by sending commands.

### Path Parameters

| Parameter | Type   | Description                     |
| --------- | ------ | ------------------------------- |
| entity_id | string | The ID of the entity to control |

### Request Body

The request body contains a command object with the following structure:

| Field      | Type    | Description                                                                 |
| ---------- | ------- | --------------------------------------------------------------------------- |
| command    | string  | The command to execute: "set", "toggle", "brightness_up", "brightness_down" |
| state      | string  | Optional. The desired state: "on" or "off" (used with "set" command)        |
| brightness | integer | Optional. The desired brightness: 0-100 (used with "set" command)           |

### Command Examples

Turn a light on:

```json
{
  "command": "set",
  "state": "on"
}
```

Turn a light off:

```json
{
  "command": "set",
  "state": "off"
}
```

Set brightness to 75%:

```json
{
  "command": "set",
  "state": "on",
  "brightness": 75
}
```

Toggle a light:

```json
{
  "command": "toggle"
}
```

Increase brightness by 10%:

```json
{
  "command": "brightness_up"
}
```

Decrease brightness by 10%:

```json
{
  "command": "brightness_down"
}
```

### Response

```json
{
  "command": "set",
  "state": "on",
  "brightness": 75,
  "description": "Light turned on and set to 75% brightness"
}
```

## Get Entity History

```
GET /api/entities/{entity_id}/history
```

Returns the history of an entity's state changes.

### Path Parameters

| Parameter | Type   | Description                             |
| --------- | ------ | --------------------------------------- |
| entity_id | string | The ID of the entity to get history for |

### Response

```json
[
  {
    "timestamp": "2023-05-18T15:30:45",
    "state": "on",
    "raw": {
      "operating_status": 100
    }
  },
  {
    "timestamp": "2023-05-18T15:25:30",
    "state": "off",
    "raw": {
      "operating_status": 0
    }
  }
]
```
