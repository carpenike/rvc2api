# CAN API Reference

The CAN API provides access to the CAN bus interface and message history. This allows you to directly interact with the RV-C network.

## CAN Status

```
GET /api/can/status
```

Returns the current status of the CAN bus interface.

### Response

```json
{
  "can0": {
    "state": "active",
    "bitrate": "250000",
    "message_count": 15293,
    "error_count": 0,
    "last_message_timestamp": "2023-05-18T15:30:45"
  }
}
```

## CAN Sniffer

```
GET /api/can/sniffer
```

Returns recent CAN messages that have been captured on the bus.

### Query Parameters

| Parameter   | Type    | Description                                                  |
| ----------- | ------- | ------------------------------------------------------------ |
| limit       | integer | Optional. Maximum number of messages to return (default 100) |
| since       | string  | Optional. Only return messages after this timestamp          |
| pgn         | string  | Optional. Filter by PGN (Parameter Group Number)             |
| source      | string  | Optional. Filter by source address                           |
| include_raw | boolean | Optional. Include raw message data in the response           |

### Example

Get the last 10 messages:

```
GET /api/can/sniffer?limit=10
```

Get messages with a specific PGN:

```
GET /api/can/sniffer?pgn=FEF1
```

### Response

```json
[
  {
    "timestamp": "2023-05-18T15:30:45",
    "arbitration_id": "18FEF121",
    "data": "FFFF0000FFFF0000",
    "interface": "can0",
    "pgn": "FEF1",
    "source_addr": "21",
    "priority": "6",
    "dgn_hex": "FEF1",
    "name": "DC Dimmer Command",
    "decoded": {
      "instance": 1,
      "command": "On",
      "level": 100
    },
    "direction": "rx"
  },
  {
    "timestamp": "2023-05-18T15:30:40",
    "arbitration_id": "18EAFF00",
    "data": "FF000000FF000000",
    "interface": "can0",
    "pgn": "EAFF",
    "source_addr": "00",
    "priority": "6",
    "dgn_hex": "EAFF",
    "name": "Address Claimed",
    "decoded": {
      "industry_group": "RV",
      "device_instance": 0,
      "device_function": "Bridge",
      "device_class": "System"
    },
    "direction": "rx"
  }
]
```

## Send CAN Message

```
POST /api/can/send
```

Sends a raw CAN message to the bus.

### Request Body

| Field          | Type   | Description                                    |
| -------------- | ------ | ---------------------------------------------- |
| arbitration_id | string | Arbitration ID in hex format                   |
| data           | string | Data bytes in hex format                       |
| interface      | string | Optional. Interface to send on (default: can0) |

### Example

```json
{
  "arbitration_id": "18FEF121",
  "data": "FFFF0000FFFF0000",
  "interface": "can0"
}
```

### Response

```json
{
  "success": true,
  "message": "Message sent successfully",
  "timestamp": "2023-05-18T15:31:00"
}
```

## Unknown PGNs

```
GET /api/can/unknown_pgns
```

Returns a list of Parameter Group Numbers (PGNs) that have been seen on the bus but are not recognized by the system.

### Response

```json
[
  {
    "pgn": "FD01",
    "count": 127,
    "last_seen": "2023-05-18T15:30:45",
    "data_samples": ["FFFF0000FFFF0000", "00FF0000FF000000"]
  },
  {
    "pgn": "FDA1",
    "count": 43,
    "last_seen": "2023-05-18T15:29:10",
    "data_samples": ["FFFFFFFFFF000000"]
  }
]
```

## Unmapped Entries

```
GET /api/can/unmapped
```

Returns a list of DGN/instance pairs that have been seen on the bus but are not mapped to entities in the system.

### Response

```json
[
  {
    "dgn": "1FEFF",
    "dgn_hex": "1FEFF",
    "instance": 3,
    "count": 15,
    "last_seen": "2023-05-18T15:30:30",
    "name": "Generic Sensor",
    "decoded_sample": {
      "instance": 3,
      "value": 75.5,
      "unit": "Percent"
    }
  },
  {
    "dgn": "1FEF6",
    "dgn_hex": "1FEF6",
    "instance": 2,
    "count": 8,
    "last_seen": "2023-05-18T15:29:45",
    "name": "DC Source Status",
    "decoded_sample": {
      "instance": 2,
      "voltage": 12.87,
      "current": 1.5
    }
  }
]
```
